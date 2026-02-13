#!/usr/bin/env python3
"""
Event Triage (Stage 1): Classify every segment into event types.
Skip pages with <2 narrative events (~60% of pages).

Increment 2 of v7 hybrid pipeline.
"""

import json
import os
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
        self.model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
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

    def _call_google(self, prompt: str) -> str:
        """Call Google Gemini API."""
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=4096,
                    temperature=0.1,
                )
            )
            if not response.candidates:
                return ""
            full_text = ""
            for part in response.candidates[0].content.parts:
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
            try:
                return json.loads(cleaned[json_start:json_end])
            except json.JSONDecodeError as e:
                print(f"  JSON parse error: {e}")
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
            # Default: all DELIBERATION (safest — won't skip pages incorrectly)
            return [EventType.DELIBERATION] * len(segments)

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
        - ≥2 NARRATIVE_EVENT segments, OR
        - ≥1 NARRATIVE_EVENT + ≥2 VERBAL_ACT (story with dialogue)

        This catches Talmudic stories which often have 1 narrative setup
        followed by dialogue between characters.
        """
        narrative_count = sum(1 for et in event_types
                              if et == EventType.NARRATIVE_EVENT)
        verbal_count = sum(1 for et in event_types
                           if et == EventType.VERBAL_ACT)

        if narrative_count >= 2:
            return False
        if narrative_count >= 1 and verbal_count >= 2:
            return False
        return True

    @staticmethod
    def summarize_triage(triage_results: Dict[str, List[EventType]]) -> Dict:
        """Summarize triage results."""
        total_pages = len(triage_results)
        skipped = sum(1 for events in triage_results.values()
                      if EventTriager.should_skip_page(events))
        kept = total_pages - skipped

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
            'total_segments': total_segments,
            'event_type_counts': type_counts,
        }
