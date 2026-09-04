#!/usr/bin/env python3
"""
Event Triage (Stage 1): Classify every segment into event types.
Skip pages with no narrative event at all.

Increment 2 of v7 hybrid pipeline.
"""

import json
import os

from src.model_config import default_model
import re
import time
from typing import Dict, List, Optional

from src.ground_truth import EventType, GroundTruthDB

try:
    from google import genai
    from google.genai import types
    GOOGLE_AI_AVAILABLE = True
except ImportError:
    GOOGLE_AI_AVAILABLE = False


class EventTriager:
    """Classify every segment on a page into event types."""

    def __init__(self, api_key: Optional[str] = None,
                 ground_truth_db: Optional[GroundTruthDB] = None,
                 model_name: Optional[str] = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.model_name = model_name or default_model()
        self.ground_truth_db = ground_truth_db

        if self.api_key and GOOGLE_AI_AVAILABLE:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    def build_event_triage_prompt(self, ref: str, segments: List[Dict]) -> str:
        """
        Build prompt for segment-level event classification.
        ~10K chars (half of v6's 22K).
        """
        # Build segment display
        segment_lines = []
        for seg in segments:
            eng = seg.get('english', '')
            # Strip HTML
            eng = re.sub(r'<[^>]+>', '', eng)
            if len(eng) > 300:
                eng = eng[:300] + "..."
            heb = seg.get('hebrew', '')
            if len(heb) > 200:
                heb = heb[:200] + "..."
            segment_lines.append(f"Segment {seg['index']}:\n  English: {eng}\n  Hebrew: {heb}")

        segments_text = '\n\n'.join(segment_lines)

        # Build few-shot examples
        few_shot = ""
        if self.ground_truth_db:
            examples = self.ground_truth_db.generate_few_shot_examples('event_triage', n=3)
            if examples:
                few_shot = "\n\n--- FEW-SHOT EXAMPLES FROM EXPERT VALIDATION ---\n" + \
                    '\n\n'.join(examples) + "\n--- END EXAMPLES ---\n"

        prompt = f"""You are an expert in Talmudic literature. Your task is to classify each segment of this Talmud page
into one of four event types. This is a TRIAGE step to determine which pages might contain stories.

## Event Types

1. **NARRATIVE_EVENT**: Something actually happens to a specific person in the physical world.
   This includes:
   - Physical actions: someone goes somewhere, hits someone, dies, builds, destroys
   - Events happening TO someone: "a certain man came before Rabbi X", "his wife died",
     "he found her", "she was captured", "the roof collapsed"
   - A person physically coming before a court or rabbi with a SPECIFIC CASE (not hypothetical)
   - Someone performing a physical test or examination
   - Changes of state: someone became ill, recovered, was born, died
   Key markers in Hebrew: מעשה (incident), ההוא/ההיא (that certain person), אתא לקמיה (came before),
   הוה עובדא (there was an incident)

   IMPORTANT: If a segment describes a specific person doing a specific physical thing,
   it is NARRATIVE_EVENT even if dialogue follows in the same segment.

2. **VERBAL_ACT**: A speech act that IS the main content — someone states a legal tradition,
   asks a halakhic question, or issues a ruling. No physical action accompanies it.
   Examples: "Rabbi X said", "He asked him a legal question", "She told him the rule"

3. **DELIBERATION**: Legal reasoning, hypothetical scenarios, abstract principles, Talmudic
   give-and-take. Nobody is doing anything — it's intellectual discussion.
   Examples: "What is the law if...", "One might think...", "The halakha is...",
   "Due to what reason did they say...", "But isn't it taught in a baraita..."

4. **HABITUAL**: Describes a recurring practice, custom, or general rule rather than
   a specific event. Uses language like "was accustomed to", "would regularly".

## CRITICAL DISTINCTIONS

- A specific person bringing a SPECIFIC case before a rabbi = NARRATIVE_EVENT
  ("a certain man came before Rav Nachman" = NARRATIVE_EVENT)
- A rabbi "going to" another academy ONLY to participate in legal debate = DELIBERATION
- Sending a legal ruling or letter about law = VERBAL_ACT
- A hypothetical legal case ("if a man does X, then Y") = DELIBERATION
- The Talmud's questions and answers about a law = DELIBERATION
- Mishna text = DELIBERATION (it's a legal code, not narrative)
- "Rabbi X sat before Rabbi Y" ONLY as setting for legal discussion = DELIBERATION

## Page: {ref}

{segments_text}
{few_shot}

## Output Format

Return a JSON object with exactly one entry per segment:

```json
{{
  "page_ref": "{ref}",
  "segment_events": [
    {{"index": 0, "event_type": "DELIBERATION", "reason": "Mishna stating legal rule"}},
    {{"index": 1, "event_type": "VERBAL_ACT", "reason": "Rabbi X said to Rabbi Y"}},
    ...
  ]
}}
```

Classify EVERY segment. Be strict: when in doubt between NARRATIVE_EVENT and DELIBERATION,
choose DELIBERATION. Legal discussions with settings are DELIBERATION.
"""
        return prompt

    @property
    def _use_json_mode(self) -> bool:
        """Use JSON mode for Gemini 3+ models to avoid thinking token issues."""
        return 'gemini-3' in self.model_name or 'gemini-2.5' in self.model_name

    # Models that require thinking mode (can't set thinking_budget=0)
    THINKING_REQUIRED_MODELS = {'gemini-3-pro-preview', 'gemini-2.5-pro'}

    def _call_google(self, prompt: str) -> str:
        """Call Google Gemini API with Gemini 3 thinking mode support."""
        try:
            config_kwargs = {
                'max_output_tokens': 4096,
                'temperature': 0.1,
            }
            if self._use_json_mode:
                config_kwargs['response_mime_type'] = 'application/json'
                if self.model_name in self.THINKING_REQUIRED_MODELS:
                    config_kwargs['max_output_tokens'] = 32768
                else:
                    config_kwargs['thinking_config'] = types.ThinkingConfig(
                        thinking_budget=0
                    )

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(**config_kwargs),
            )
            if not response.candidates:
                return ""
            full_text = ""
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'thought') and part.thought:
                    continue  # Skip thinking tokens
                full_text += part.text
            return full_text
        except Exception as e:
            print(f"  Gemini API error: {e}")
            raise

    def _parse_json_response(self, content: str) -> Optional[Dict]:
        """Parse JSON from AI response, handling markdown code blocks."""
        cleaned = content
        if '```json' in cleaned:
            cleaned = cleaned.split('```json')[1].split('```')[0]
        elif '```' in cleaned:
            parts = cleaned.split('```')
            if len(parts) >= 2:
                cleaned = parts[1]

        json_start = cleaned.find('{')
        json_end = cleaned.rfind('}') + 1

        if json_start >= 0 and json_end > json_start:
            json_str = cleaned[json_start:json_end]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                # Repair trailing commas (common with Gemini 3 models)
                repaired = re.sub(r',\s*([}\]])', r'\1', json_str)
                try:
                    return json.loads(repaired)
                except json.JSONDecodeError as e:
                    print(f"  JSON parse error (after repair): {e}")
                    return None
        return None

    def triage_page(self, ref: str, segments: List[Dict]) -> List[EventType]:
        """
        Classify each segment on a page into event types.
        Returns a list of EventType, one per segment.
        """
        if not self.client:
            raise RuntimeError("Gemini API not configured")

        prompt = self.build_event_triage_prompt(ref, segments)
        content = self._call_google(prompt)
        result = self._parse_json_response(content)

        if not result:
            # The call failed or its response would not parse. We do NOT know what is on
            # this page, so we must not say DELIBERATION — that is a real verdict about a
            # legal passage, and should_skip_page() would then discard the page. Stage 1
            # discards leave no trace anywhere downstream, so that loss is permanent and
            # invisible (FRAMEWORK 1.1). Fail OPEN and say so. -> Lesson 21
            print(f"  TRIAGE FAILED on {ref}: response unparseable; keeping the page")
            return [EventType.TRIAGE_FAILED] * len(segments)

        # Parse event types
        event_types = [EventType.DELIBERATION] * len(segments)  # Default
        for item in result.get('segment_events', []):
            idx = item.get('index', -1)
            et_str = item.get('event_type', 'DELIBERATION')
            if 0 <= idx < len(segments):
                try:
                    event_types[idx] = EventType(et_str)
                except ValueError:
                    event_types[idx] = EventType.DELIBERATION

        return event_types

    def triage_all_pages(self, pages: List[Dict],
                         delay: float = 1.0) -> Dict[str, List[EventType]]:
        """
        Triage all pages. Returns dict of page_ref -> list of EventType.
        """
        results = {}
        for i, page in enumerate(pages):
            ref = page.get('ref', f'page_{i}')
            segments = page.get('segments', [])
            if not segments:
                results[ref] = []
                continue

            print(f"  Triaging {ref} ({len(segments)} segments)...")
            event_types = self.triage_page(ref, segments)
            results[ref] = event_types

            skip = self.should_skip_page(event_types)
            ne_count = sum(1 for et in event_types if et == EventType.NARRATIVE_EVENT)
            print(f"    → {ne_count} NARRATIVE_EVENT segments, skip={skip}")

            if delay > 0 and i < len(pages) - 1:
                time.sleep(delay)

        return results

    @staticmethod
    def should_skip_page(event_types: List[EventType]) -> bool:
        """
        Skip pages unlikely to contain stories.

        Keep pages with:
        - ≥1 NARRATIVE_EVENT segment, OR
        - any TRIAGE_FAILED segment — we could not look, so we do not get to decide

        This catches Talmudic stories which often have 1 narrative setup
        followed by dialogue between characters.

        **Changed 2026-08-31: a single NARRATIVE_EVENT is now enough.** The rule
        used to demand that a narrative event be *corroborated* — a second
        narrative event, or two verbal acts — and threw the page away otherwise.
        Measured against both blind lists, that clause was the single richest
        seam of missed stories in the corpus: 8 pages across Ketubot and
        Kiddushin were discarded by it and **6 of them carry a real story**
        (~75%, against 14.3% for discarded pages as a whole). One is Ketubot
        51a, the false skip found by hand on 2026-02-13 and never fixed.

        Priced before shipping: +1 Ketubot story and +2 Kiddushin stories for
        **8 extra Stage 2 calls** and 5 false proposals across both tractates.
        Keeping every discarded page instead costs 224 calls and 24 false
        proposals to gain just one story more.

        Verbal acts alone still never keep a page. Kiddushin 10b (N=0, V=5) is a
        real story that stays missed; recovering it needs a `V >= 4` clause,
        which buys nothing on Ketubot for 70 extra calls — a threshold fitted to
        a single story, deliberately not adopted (Lesson 18).
        → docs/findings/2026-08-31-triage-single-narrative.md
        """
        # A page whose triage failed is UNKNOWN, not empty. Examining it costs one Stage 2
        # call; discarding it costs a story we can never find again.
        if any(et == EventType.TRIAGE_FAILED for et in event_types):
            return False

        narrative_count = sum(1 for et in event_types
                              if et == EventType.NARRATIVE_EVENT)
        if narrative_count >= 1:
            return False
        return True

    @staticmethod
    def summarize_triage(triage_results: Dict[str, List[EventType]]) -> Dict:
        """Summarize triage results."""
        total_pages = len(triage_results)
        skipped = sum(1 for events in triage_results.values()
                      if EventTriager.should_skip_page(events))
        kept = total_pages - skipped

        # An error rate nobody counts is an error rate nobody notices. Name the pages
        # too: you cannot re-run what you cannot identify.
        failed_refs = sorted(ref for ref, events in triage_results.items()
                             if any(et == EventType.TRIAGE_FAILED for et in events))

        total_segments = sum(len(events) for events in triage_results.values())
        type_counts = {}
        for events in triage_results.values():
            for et in events:
                type_counts[et.value] = type_counts.get(et.value, 0) + 1

        return {
            'total_pages': total_pages,
            'skipped': skipped,
            'kept': kept,
            'skip_rate': f"{100*skipped/total_pages:.1f}%" if total_pages else "0%",
            'failed': len(failed_refs),
            'failed_refs': failed_refs,
            'total_segments': total_segments,
            'event_type_counts': type_counts,
        }
