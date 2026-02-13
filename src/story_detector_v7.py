#!/usr/bin/env python3
"""
Talmud Story Detection v7: Hybrid Pipeline — Decomposed Detection + Adversarial Validation

Architecture:
  Stage 1: Event Triage (event_triage.py) — classify segments, skip legal pages
  Stage 2: Constrained Story Detection — event-annotated prompt, anti-legal few-shots
  Stage 3: Adversarial Validation — three-call pattern for borderline stories
  Stage 4: Boundary Refinement + Improved Merge — deterministic post-processing

Key changes from v6:
- Event type annotations on each segment (from Stage 1)
- Explicit "legal is not a story" instruction with Jeff's examples
- Self-check can only DEMOTE or CONFIRM, never promote
- Few-shot examples from Ground Truth DB (Jeff's actual corrections)
- Adversarial validation for borderline cases
- Deterministic boundary trimming using event tags
"""

import json
import os
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

from src.ground_truth import GroundTruthDB, EventType, ErrorType
from src.event_triage import EventTriager

try:
    from google import genai
    from google.genai import types
    GOOGLE_AI_AVAILABLE = True
except ImportError:
    GOOGLE_AI_AVAILABLE = False


class V7StoryDetector:
    """
    v7 story detection with event-annotated constrained prompt.
    Uses Ground Truth DB for few-shot examples.
    """

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

    def build_detection_prompt(self, ref: str, segments: List[Dict],
                                event_types: List[EventType],
                                prev_page_context: Optional[str] = None,
                                next_page_context: Optional[str] = None) -> str:
        """
        Build constrained detection prompt with event annotations.
        ~15K chars with few-shot examples from Ground Truth DB.
        """
        # Build annotated segment display
        segment_lines = []
        for i, seg in enumerate(segments):
            eng = seg.get('english', '')
            eng = re.sub(r'<[^>]+>', '', eng)
            if len(eng) > 300:
                eng = eng[:300] + "..."
            heb = seg.get('hebrew', '')
            if len(heb) > 200:
                heb = heb[:200] + "..."

            et = event_types[i].value if i < len(event_types) else "UNKNOWN"
            segment_lines.append(
                f"[{et}] Seg {seg['index']}:\n  English: {eng}\n  Hebrew: {heb}"
            )

        segments_text = '\n\n'.join(segment_lines)

        # Build few-shot examples from Ground Truth DB
        few_shot_section = ""
        if self.ground_truth_db:
            examples = self.ground_truth_db.generate_few_shot_examples(
                'story_detection', error_type=ErrorType.LEGAL_MISIDENTIFICATION, n=3
            )
            if examples:
                few_shot_section = (
                    "\n\n=== EXAMPLES FROM EXPERT VALIDATION ===\n\n"
                    + '\n\n'.join(examples)
                    + "\n\n=== END EXAMPLES ===\n"
                )

        # Cross-page context
        cross_page = ""
        if prev_page_context:
            cross_page += f"\n--- CONTEXT: Last segments from PREVIOUS page ---\n{prev_page_context}\n---\n"
        if next_page_context:
            cross_page += f"\n--- CONTEXT: First segments from NEXT page ---\n{next_page_context}\n---\n"

        prompt = f"""Analyze this Talmud page for narrative stories. Each segment has been pre-classified
by event type: NARRATIVE_EVENT, VERBAL_ACT, DELIBERATION, or HABITUAL.

## CRITICAL RULE: LEGAL DISCUSSIONS ARE NOT STORIES

A legal discussion is NOT a story even if:
- It mentions a specific rabbi, place, or time
- A rabbi travels to another academy for a debate
- One sage "sits before" another sage
- Named rabbis make legal arguments to each other
- Place names appear (academies debating is NOT a story)
- A rabbi experiences "difficulty" with a legal issue
- Someone "thought about acting" according to a legal opinion

A passage IS a story only if SPECIFIC PEOPLE perform PHYSICAL ACTIONS that create
a CAUSAL CHAIN of EVENTS with TEMPORAL PROGRESSION resulting in CHANGE.

## CLASSIFICATION SYSTEM

1. **YES** — Definitively a story: ≥5 criteria met, no disqualifiers
2. **HIGH_CONFIDENCE** — Likely a story: 4-5 criteria met, minor weakeners
3. **LOW_CONFIDENCE** — Borderline story: 1 real event + discussion, or 3-4 criteria
4. **NOT_A_STORY** — Rejected: legal discussion, hypothetical, or <3 criteria

## THE 6 CRITERIA

1. **IDENTIFIABLE_CHARACTERS**: Specific people (named or anonymous like "a certain man")
   who ACT in the narrative (not just state legal opinions)
2. **MULTIPLE_EVENTS**: ≥2 NARRATIVE events (physical actions, not talk/deliberation)
3. **CAUSAL_CHAIN**: Events connected by cause→effect
4. **TEMPORAL_PROGRESSION**: Time markers or clear sequence
5. **DESCRIPTIVE**: Describes what DID happen (not what SHOULD happen)
6. **CHANGE_OUTCOME**: Situation transformed from beginning to end

## AUTOMATIC DISQUALIFIERS → NOT_A_STORY

- Mishna section (מתני׳)
- Hypothetical case ("If X were to...")
- Habitual action (היה רגיל)
- Pure legal ruling without narrative
- Rabbi stating legal opinion (not acting in narrative)
- Legal deliberation (thinking, considering, difficulty resolving)
- Legal debate with setting (sitting before another = just a debate)
- A legal debate between academies (place names ≠ characters)

## BORDERLINE → LOW_CONFIDENCE (not NOT_A_STORY)

One real event + discussion about it → LOW_CONFIDENCE
Mainly dialogue but with some real events → LOW_CONFIDENCE
Weak causality but some change → LOW_CONFIDENCE

## BOUNDARY RULES

- Story STARTS at first NARRATIVE event, not preceding legal ruling
- Story ENDS at final narrative action, not following Talmudic commentary
- Talmudic questions (beginning with וְהָא) are NOT part of story
- Exception: Rabbi directly referencing story events IS part of story
- Do NOT split one continuous story into two

{cross_page}
{few_shot_section}

## PAGE TO ANALYZE: {ref}

{segments_text}

## OUTPUT

Return JSON:
{{
  "page_ref": "{ref}",
  "stories": [
    {{
      "start_segment": <int>,
      "end_segment": <int>,
      "classification": "YES | HIGH_CONFIDENCE | LOW_CONFIDENCE | NOT_A_STORY",
      "criteria": {{
        "identifiable_characters": {{"met": true/false, "evidence": "...", "anonymous": true/false}},
        "multiple_events": {{"met": true/false, "count": <int>, "events": ["...", "..."]}},
        "causal_chain": {{"met": true/false, "chain": "A → B → C"}},
        "temporal_progression": {{"met": true/false, "markers": ["..."]}},
        "descriptive": {{"met": true/false, "evidence": "..."}},
        "change_outcome": {{"met": true/false, "before": "...", "after": "..."}}
      }},
      "criteria_met_count": <0-6>,
      "disqualifiers_found": ["..." or empty],
      "weakeners_found": ["..." or empty],
      "one_sentence_summary": "...",
      "classification_reasoning": "...",
      "continuation": {{
        "continues_from_previous_page": true/false,
        "continues_to_next_page": true/false,
        "note": "..."
      }}
    }}
  ]
}}

If no stories found: {{"page_ref": "{ref}", "stories": []}}
"""
        return prompt

    def _call_google(self, prompt: str, max_tokens: int = 8192,
                     json_mode: bool = False) -> str:
        """Call Google Gemini API.

        Args:
            json_mode: If True, use response_mime_type='application/json' and
                       disable thinking (required for Gemini 3+ models).
        """
        try:
            config_kwargs = {
                'max_output_tokens': max_tokens,
                'temperature': 0.1,
            }
            if json_mode:
                config_kwargs['response_mime_type'] = 'application/json'
                # Gemini 3 models use "thinking" tokens that count against
                # max_output_tokens, causing truncated JSON. Disable thinking
                # for structured output.
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
                # Repair common issues from newer Gemini models:
                # 1. Trailing commas before } or ]
                repaired = re.sub(r',\s*([}\]])', r'\1', json_str)
                try:
                    return json.loads(repaired)
                except json.JSONDecodeError as e:
                    print(f"  JSON parse error (after repair): {e}")
                    return None
        return None

    @property
    def _use_json_mode(self) -> bool:
        """Use JSON mode for Gemini 3+ models to avoid thinking token issues."""
        return 'gemini-3' in self.model_name or 'gemini-2.5' in self.model_name

    def detect_stories(self, ref: str, segments: List[Dict],
                       event_types: List[EventType],
                       prev_page_context: Optional[str] = None,
                       next_page_context: Optional[str] = None) -> List[Dict]:
        """
        Detect stories on a single page using constrained prompt.
        Returns list of story dicts. Retries once on JSON parse failure.
        """
        if not self.client:
            raise RuntimeError("Gemini API not configured")

        prompt = self.build_detection_prompt(
            ref, segments, event_types,
            prev_page_context, next_page_context
        )
        use_json = self._use_json_mode

        for attempt in range(2):
            content = self._call_google(prompt, json_mode=use_json)
            if use_json:
                # JSON mode returns clean JSON, parse directly
                try:
                    result = json.loads(content) if content else None
                except json.JSONDecodeError:
                    result = self._parse_json_response(content)
            else:
                result = self._parse_json_response(content)
            if result is not None:
                return result.get('stories', [])
            if attempt == 0:
                print(f"    Retrying {ref} (JSON parse failed)...")
                time.sleep(1)

        return []

    def run_pipeline(self, pages: List[Dict],
                     triage_results: Optional[Dict[str, List[EventType]]] = None,
                     delay: float = 1.0,
                     skip_triage: bool = False,
                     enable_adversarial: bool = False) -> Dict:
        """
        Full v7 pipeline: triage → detect → (adversarial) → (boundary refine)

        Args:
            pages: List of page dicts with 'ref' and 'segments'
            triage_results: Pre-computed triage results (or None to compute)
            delay: Delay between API calls
            skip_triage: If True, process all pages (no triage filtering)
        """
        # Stage 1: Event Triage
        if triage_results is None and not skip_triage:
            print("\n--- Stage 1: Event Triage ---")
            triager = EventTriager(
                api_key=self.api_key,
                ground_truth_db=self.ground_truth_db,
                model_name=self.model_name,
            )
            triage_results = triager.triage_all_pages(pages, delay=delay)
        elif skip_triage:
            # Generate default triage (all DELIBERATION) so detection still works
            triage_results = {}
            for page in pages:
                ref = page.get('ref', '')
                n_segs = len(page.get('segments', []))
                triage_results[ref] = [EventType.DELIBERATION] * n_segs

        # Determine which pages to process
        pages_to_process = []
        skipped_pages = []
        for page in pages:
            ref = page.get('ref', '')
            events = triage_results.get(ref, [])
            if skip_triage or not EventTriager.should_skip_page(events):
                pages_to_process.append(page)
            else:
                skipped_pages.append(ref)

        print(f"\n--- Stage 2: Constrained Story Detection ---")
        print(f"  Processing {len(pages_to_process)} pages "
              f"(skipped {len(skipped_pages)})")

        # Stage 2: Constrained Detection
        all_results = []
        for i, page in enumerate(pages_to_process):
            ref = page.get('ref', '')
            segments = page.get('segments', [])
            events = triage_results.get(ref, [EventType.DELIBERATION] * len(segments))

            # Build cross-page context
            prev_ctx = None
            next_ctx = None
            page_idx = next((j for j, p in enumerate(pages)
                             if p.get('ref') == ref), None)
            if page_idx is not None:
                if page_idx > 0:
                    prev_segs = pages[page_idx - 1].get('segments', [])
                    if prev_segs:
                        prev_ctx = '\n'.join(
                            f"[Prev Seg {s['index']}] {re.sub(r'<[^>]+>', '', s.get('english', ''))[:150]}"
                            for s in prev_segs[-3:]
                        )
                if page_idx < len(pages) - 1:
                    next_segs = pages[page_idx + 1].get('segments', [])
                    if next_segs:
                        next_ctx = '\n'.join(
                            f"[Next Seg {s['index']}] {re.sub(r'<[^>]+>', '', s.get('english', ''))[:150]}"
                            for s in next_segs[:3]
                        )

            print(f"  [{i+1}/{len(pages_to_process)}] Detecting on {ref}...")
            stories = self.detect_stories(ref, segments, events, prev_ctx, next_ctx)

            # Build page result
            page_result = {
                'ref': ref,
                'segments': segments,
                'stories': stories,
            }
            all_results.append(page_result)

            story_count = sum(1 for s in stories
                              if s.get('classification') != 'NOT_A_STORY')
            print(f"    → {len(stories)} candidates, {story_count} stories")

            if delay > 0 and i < len(pages_to_process) - 1:
                time.sleep(delay)

        # Add skipped pages with empty stories
        for page in pages:
            ref = page.get('ref', '')
            if ref in skipped_pages:
                all_results.append({
                    'ref': ref,
                    'segments': page.get('segments', []),
                    'stories': [],
                    'skipped_by_triage': True,
                })

        # Sort by page order
        page_order = {p.get('ref', ''): i for i, p in enumerate(pages)}
        all_results.sort(key=lambda r: page_order.get(r['ref'], 999))

        # Stage 3: Adversarial Validation (disabled by default — net negative in testing)
        if enable_adversarial:
            print(f"\n--- Stage 3: Adversarial Validation ---")
            validator = AdversarialValidator(
                api_key=self.api_key,
                ground_truth_db=self.ground_truth_db,
                model_name=self.model_name,
            )
            if validator.client:
                changes = validator.validate_all_stories(all_results, delay=delay)
            else:
                print("  Skipped (no API configured)")
                changes = []
        else:
            print(f"\n--- Stage 3: Adversarial Validation (disabled) ---")
            changes = []

        # Stage 4: Boundary Refinement + Cross-page Merge
        print(f"\n--- Stage 4: Boundary Refinement + Cross-page Merge ---")

        # 4a: Refine boundaries using event tags
        boundary_changes = refine_boundaries_with_event_tags(all_results, triage_results)
        print(f"  Boundary refinement: {boundary_changes} stories trimmed")

        # 4b: Cross-page merge (improved — uses triage event types)
        all_results = merge_cross_page_stories_v7(all_results, triage_results)

        # 4c: Legacy cross-page merge for continuation flags
        all_results = merge_cross_page_stories(all_results)

        # Detect duplicates
        all_results = detect_duplicate_stories(all_results)

        return {
            'tractate': 'Ketubot',
            'version': 'v7',
            'pages': all_results,
            'triage_summary': EventTriager.summarize_triage(triage_results),
        }


# ============================================================
# ADVERSARIAL VALIDATION (Stage 3)
# ============================================================

class AdversarialValidator:
    """
    Three-call adversarial validation for borderline stories.

    Pattern:
    1. Detector Defense: "You classified this as a story. Defend your classification."
    2. Jeff's Advocate: "Argue why this is NOT a story."
    3. Adjudicator: "Given defense and challenge, what's the correct classification?"

    Only runs on borderline stories (~30-40 cases per tractate).
    """

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

    def _call_google(self, prompt: str) -> str:
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
            return ''.join(part.text for part in response.candidates[0].content.parts)
        except Exception as e:
            print(f"    Adversarial API error: {e}")
            raise

    def _parse_json_response(self, content: str) -> Optional[Dict]:
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
                repaired = re.sub(r',\s*([}\]])', r'\1', json_str)
                try:
                    return json.loads(repaired)
                except json.JSONDecodeError:
                    return None
        return None

    def should_validate(self, story: Dict) -> bool:
        """
        Determine if a story needs adversarial validation.

        Target cases most likely to be legal misidentifications:
        - HIGH_CONFIDENCE with legal-related weakeners or disqualifier flags
        - LOW_CONFIDENCE where events are mainly verbal/legal
        - Any story with ≤1 actual narrative event but HIGH+ classification
        """
        cls = story.get('classification', '')
        if cls == 'NOT_A_STORY':
            return False

        weakeners = story.get('weakeners_found', [])
        disqualifiers = story.get('disqualifiers_found', [])
        criteria = story.get('criteria', {})
        events = criteria.get('multiple_events', {})
        event_count = events.get('count', 0) if isinstance(events, dict) else 0

        # HIGH/YES with weakeners suggesting legal content
        if cls in ('HIGH_CONFIDENCE', 'YES'):
            legal_weakeners = [w for w in weakeners
                               if any(kw in str(w).lower()
                                      for kw in ['legal', 'embedded', 'speech', 'verbal'])]
            if legal_weakeners or len(weakeners) >= 2:
                return True
            if event_count <= 1:
                return True

        # LOW_CONFIDENCE: only validate if events seem questionable
        if cls == 'LOW_CONFIDENCE':
            if event_count <= 1:
                return True
            if any(kw in str(weakeners).lower() for kw in ['legal', 'speech', 'verbal']):
                return True

        return False

    def _get_story_text(self, story: Dict, segments: List[Dict]) -> str:
        """Get the text of a story from its segments."""
        start = story.get('start_segment', 0)
        end = story.get('end_segment', 0)
        texts = []
        for seg in segments:
            if start <= seg.get('index', -1) <= end:
                eng = re.sub(r'<[^>]+>', '', seg.get('english', ''))
                texts.append(f"Seg {seg['index']}: {eng[:200]}")
        return '\n'.join(texts)

    def build_detector_defense_prompt(self, story: Dict, story_text: str) -> str:
        """Call 1: Ask the detector to defend its classification."""
        cls = story.get('classification', 'UNKNOWN')
        reasoning = story.get('classification_reasoning', 'N/A')
        summary = story.get('one_sentence_summary', 'N/A')
        criteria = json.dumps(story.get('criteria', {}), indent=2)

        return f"""You classified the following Talmudic passage as {cls}.

Summary: {summary}
Reasoning: {reasoning}

Criteria evaluation:
{criteria}

Text:
{story_text}

DEFEND your classification. Explain specifically:
1. What are the NARRATIVE events (not verbal statements or legal arguments)?
2. What is the CAUSAL chain between events?
3. What CHANGES from beginning to end?
4. Why is this NOT just a legal discussion with a narrative setting?

Be specific and cite the text. If your defense is weak, acknowledge it.

Respond in plain text (no JSON)."""

    def build_advocate_prompt(self, story: Dict, story_text: str,
                              defense: str) -> str:
        """Call 2: Jeff's advocate challenges the classification."""
        cls = story.get('classification', 'UNKNOWN')

        # Get adversarial examples from ground truth
        examples = ""
        if self.ground_truth_db:
            adv_examples = self.ground_truth_db.generate_few_shot_examples('adversarial', n=2)
            if adv_examples:
                examples = "\n\nRelevant expert corrections:\n" + '\n'.join(adv_examples)

        return f"""You are Jeff Rubenstein's advocate — an expert in Talmudic narrative who holds a HIGH BAR
for what counts as a "story." A passage was classified as {cls} and the detector defended it.

TEXT:
{story_text}

DETECTOR'S DEFENSE:
{defense}

{examples}

YOUR TASK: Argue why this passage should be classified as NOT_A_STORY. Be aggressive:

1. Are the "events" really just VERBAL ACTS (statements, arguments, rulings)?
   - "Rabbi X said to Rabbi Y" is NOT a narrative event
   - "He ruled that..." is NOT a narrative event
   - Legal difficulty/resolution is NOT a narrative event

2. Is there a REAL causal chain, or just sequential statements?
   - One thing being mentioned after another ≠ causality
   - Legal reasoning chain ≠ narrative causality

3. Is the "change" just a legal ruling being issued?
   - A rabbi ruling on a case is NOT a story outcome
   - Resolution of a legal difficulty is NOT narrative change

4. Is this a legal discussion with a SETTING (not a story)?
   - A rabbi going somewhere to discuss law ≠ narrative event
   - A sage sitting before another sage ≠ story

If you genuinely believe it IS a story, say so. But err on the side of NOT_A_STORY.

Respond in plain text (no JSON)."""

    def build_adjudicator_prompt(self, story: Dict, story_text: str,
                                  defense: str, challenge: str) -> str:
        """Call 3: Adjudicator makes final decision."""
        cls = story.get('classification', 'UNKNOWN')

        return f"""You are an impartial adjudicator reviewing a Talmudic passage classification dispute.

ORIGINAL CLASSIFICATION: {cls}

TEXT:
{story_text}

DEFENDER'S ARGUMENT (for {cls}):
{defense}

CHALLENGER'S ARGUMENT (for NOT_A_STORY):
{challenge}

## CLASSIFICATION RULES

DEMOTE to NOT_A_STORY if:
1. The "events" are purely verbal (legal arguments, rulings, traditions) with no physical action
2. A rabbi "going somewhere" or "sitting before" someone is ONLY a setting for legal debate
3. "Experiencing difficulty" with a legal issue is NOT a narrative event
4. All characters are just stating legal opinions, not acting in a narrative

KEEP as LOW_CONFIDENCE if:
1. A specific person PHYSICALLY does something (comes with a real case, performs an action)
2. There is genuine temporal progression around a real-world event
3. Even one REAL event (not legal/verbal) embedded in discussion = borderline story

KEEP as HIGH_CONFIDENCE or higher if:
1. Multiple physical events in causal chain
2. Clear temporal progression with change

## KEY TEST
Ask: "If I remove all the legal discussion, is there still a PHYSICAL EVENT that happened
to a specific person?" If YES → keep (at least LOW_CONFIDENCE). If NO → NOT_A_STORY.

YOUR DECISION:

Return JSON:
{{
  "final_classification": "YES | HIGH_CONFIDENCE | LOW_CONFIDENCE | NOT_A_STORY",
  "reasoning": "...",
  "defender_strongest_point": "...",
  "challenger_strongest_point": "...",
  "decision_basis": "..."
}}"""

    def validate_story(self, story: Dict, segments: List[Dict],
                       delay: float = 0.5) -> Dict:
        """
        Run three-call adversarial validation on a single story.
        Returns validation result with final classification.
        """
        if not self.client:
            raise RuntimeError("Gemini API not configured")

        story_text = self._get_story_text(story, segments)
        original_cls = story.get('classification', 'UNKNOWN')

        # Call 1: Defense
        defense_prompt = self.build_detector_defense_prompt(story, story_text)
        defense = self._call_google(defense_prompt)
        time.sleep(delay)

        # Call 2: Challenge
        advocate_prompt = self.build_advocate_prompt(story, story_text, defense)
        challenge = self._call_google(advocate_prompt)
        time.sleep(delay)

        # Call 3: Adjudication
        adjudicator_prompt = self.build_adjudicator_prompt(
            story, story_text, defense, challenge
        )
        adjudication_raw = self._call_google(adjudicator_prompt)
        adjudication = self._parse_json_response(adjudication_raw)

        if not adjudication:
            return {
                'original_classification': original_cls,
                'final_classification': original_cls,
                'error': 'Failed to parse adjudication',
            }

        final_cls = adjudication.get('final_classification', original_cls)

        return {
            'original_classification': original_cls,
            'final_classification': final_cls,
            'reasoning': adjudication.get('reasoning', ''),
            'defense_summary': defense[:300],
            'challenge_summary': challenge[:300],
            'changed': original_cls != final_cls,
        }

    def validate_all_stories(self, pages: List[Dict],
                              delay: float = 0.5) -> List[Dict]:
        """
        Run adversarial validation on all borderline stories across pages.
        Modifies story classifications in-place and returns log of changes.
        """
        changes = []
        total_validated = 0

        for page in pages:
            ref = page.get('ref', '')
            segments = page.get('segments', [])
            stories = page.get('stories', [])

            for i, story in enumerate(stories):
                if not self.should_validate(story):
                    continue

                total_validated += 1
                cls = story.get('classification', '')
                segs = f"{story.get('start_segment', '?')}-{story.get('end_segment', '?')}"
                print(f"    Validating {ref} segs {segs} ({cls})...")

                result = self.validate_story(story, segments, delay=delay)

                if result.get('changed'):
                    old_cls = result['original_classification']
                    new_cls = result['final_classification']
                    story['classification'] = new_cls
                    story['adversarial_validation'] = result
                    print(f"      → CHANGED: {old_cls} → {new_cls}")
                    print(f"        Reason: {result.get('reasoning', '')[:100]}")
                    changes.append({
                        'page_ref': ref,
                        'segments': segs,
                        'old': old_cls,
                        'new': new_cls,
                        'reasoning': result.get('reasoning', '')[:200],
                    })
                else:
                    story['adversarial_validation'] = {'confirmed': True}
                    print(f"      → CONFIRMED: {cls}")

        print(f"\n  Adversarial validation complete: {total_validated} stories validated, "
              f"{len(changes)} changed")
        return changes


# ============================================================
# STAGE 4: BOUNDARY REFINEMENT + IMPROVED MERGE
# ============================================================

def refine_boundaries_with_event_tags(pages: List[Dict],
                                       triage_results: Dict[str, List[EventType]]) -> int:
    """
    Trim DELIBERATION segments from story edges using triage event types.

    If a story starts or ends with segments that are DELIBERATION in the triage,
    shrink the boundary inward. This prevents including legal commentary at the
    edges of stories.

    Returns count of stories modified.
    """
    changes = 0

    for page in pages:
        ref = page.get('ref', '')
        events = triage_results.get(ref, [])
        if not events:
            continue

        for story in page.get('stories', []):
            cls = story.get('classification', 'NOT_A_STORY')
            if cls == 'NOT_A_STORY':
                continue

            start = story.get('start_segment', 0)
            end = story.get('end_segment', 0)
            orig_start = start
            orig_end = end

            # Trim DELIBERATION from the start
            while start < end and start < len(events):
                if events[start] == EventType.DELIBERATION:
                    start += 1
                else:
                    break

            # Trim DELIBERATION from the end
            while end > start and end < len(events):
                if events[end] == EventType.DELIBERATION:
                    end -= 1
                else:
                    break

            # Only apply if we still have at least 1 segment with narrative content
            if start != orig_start or end != orig_end:
                # Verify the trimmed range still has narrative events
                remaining_narrative = any(
                    events[i] == EventType.NARRATIVE_EVENT
                    for i in range(start, min(end + 1, len(events)))
                )
                if remaining_narrative and start <= end:
                    story['start_segment'] = start
                    story['end_segment'] = end
                    story['boundary_refined'] = True
                    changes += 1

    return changes


def merge_cross_page_stories_v7(pages: List[Dict],
                                 triage_results: Dict[str, List[EventType]]) -> List[Dict]:
    """
    Improved cross-page merge using triage event types.

    Handles cases where a story at a page boundary is classified as NOT_A_STORY
    because it doesn't have enough context on its own, but the adjacent page
    has a detected story that this fragment belongs to.

    Key improvement over merge_cross_page_stories:
    - Uses triage NARRATIVE_EVENT types to identify story fragments at boundaries
    - Promotes NOT_A_STORY fragments to LOW_CONFIDENCE when they have narrative
      events and merge with an adjacent story
    """
    for i in range(len(pages) - 1):
        page_n = pages[i]
        page_n1 = pages[i + 1]

        ref_n = page_n.get('ref', '')
        ref_n1 = page_n1.get('ref', '')

        events_n = triage_results.get(ref_n, [])
        events_n1 = triage_results.get(ref_n1, [])

        stories_n = page_n.get('stories', [])
        stories_n1 = page_n1.get('stories', [])

        if not events_n or not events_n1:
            continue

        # Check if last segment(s) of page N have NARRATIVE_EVENT
        last_seg_idx = len(events_n) - 1
        n_has_narrative_at_end = (
            last_seg_idx >= 0 and
            events_n[last_seg_idx] == EventType.NARRATIVE_EVENT
        )

        # Check if first segment(s) of page N+1 have NARRATIVE_EVENT
        n1_has_narrative_at_start = (
            len(events_n1) > 0 and
            (events_n1[0] == EventType.NARRATIVE_EVENT or
             (len(events_n1) > 1 and events_n1[1] == EventType.NARRATIVE_EVENT))
        )

        if not (n_has_narrative_at_end and n1_has_narrative_at_start):
            continue

        # Find boundary stories
        last_story_n = stories_n[-1] if stories_n else None
        first_story_n1 = stories_n1[0] if stories_n1 else None

        # Case: Page N has NOT_A_STORY at boundary, Page N+1 has real story at start
        if (last_story_n and first_story_n1 and
            last_story_n.get('classification') == 'NOT_A_STORY' and
            first_story_n1.get('classification') not in ('NOT_A_STORY', None) and
            last_story_n.get('end_segment', -1) >= last_seg_idx - 1 and
            first_story_n1.get('start_segment', 999) <= 1):

            # Promote the NOT_A_STORY fragment and merge
            merged_cls = first_story_n1.get('classification', 'LOW_CONFIDENCE')
            last_story_n['classification'] = merged_cls
            last_story_n['spans_pages'] = [ref_n, ref_n1]
            last_story_n['start_segment_page2'] = first_story_n1.get('start_segment')
            last_story_n['end_segment_page2'] = first_story_n1.get('end_segment')
            last_story_n['cross_page_merge_v7'] = True

            # Merge summaries
            summary_n = last_story_n.get('one_sentence_summary', '')
            summary_n1 = first_story_n1.get('one_sentence_summary', '')
            if summary_n1 and not summary_n:
                last_story_n['one_sentence_summary'] = summary_n1
            elif summary_n and summary_n1:
                last_story_n['one_sentence_summary'] = f"{summary_n} {summary_n1}"

            # Remove from page N+1
            stories_n1.pop(0)
            page_n1['stories'] = stories_n1

            print(f"  Cross-page merge (v7): {ref_n} → {ref_n1} ({merged_cls}) "
                  f"[promoted NOT_A_STORY + story]")
            continue

        # Case: Page N has real story at end, Page N+1 has NOT_A_STORY at boundary
        if (last_story_n and first_story_n1 and
            last_story_n.get('classification') not in ('NOT_A_STORY', None) and
            first_story_n1.get('classification') == 'NOT_A_STORY' and
            last_story_n.get('end_segment', -1) >= last_seg_idx - 1 and
            first_story_n1.get('start_segment', 999) <= 1):

            # Merge the NOT_A_STORY fragment into the page N story
            merged_cls = last_story_n.get('classification', 'LOW_CONFIDENCE')
            last_story_n['spans_pages'] = [ref_n, ref_n1]
            last_story_n['start_segment_page2'] = first_story_n1.get('start_segment')
            last_story_n['end_segment_page2'] = first_story_n1.get('end_segment')
            last_story_n['cross_page_merge_v7'] = True

            # Remove from page N+1
            stories_n1.pop(0)
            page_n1['stories'] = stories_n1

            print(f"  Cross-page merge (v7): {ref_n} → {ref_n1} ({merged_cls}) "
                  f"[story + promoted NOT_A_STORY]")
            continue

        # Case: Both sides are NOT_A_STORY but boundary has NARRATIVE_EVENT
        # Create a LOW_CONFIDENCE cross-page story
        if (last_story_n and first_story_n1 and
            last_story_n.get('classification') == 'NOT_A_STORY' and
            first_story_n1.get('classification') == 'NOT_A_STORY' and
            last_story_n.get('end_segment', -1) >= last_seg_idx - 1 and
            first_story_n1.get('start_segment', 999) <= 1):

            last_story_n['classification'] = 'LOW_CONFIDENCE'
            last_story_n['spans_pages'] = [ref_n, ref_n1]
            last_story_n['start_segment_page2'] = first_story_n1.get('start_segment')
            last_story_n['end_segment_page2'] = first_story_n1.get('end_segment')
            last_story_n['cross_page_merge_v7'] = True

            stories_n1.pop(0)
            page_n1['stories'] = stories_n1

            print(f"  Cross-page merge (v7): {ref_n} → {ref_n1} (LOW_CONFIDENCE) "
                  f"[both NOT_A_STORY promoted]")
            continue

    return pages


# ============================================================
# CROSS-PAGE MERGING (from v6, adapted for v7)
# ============================================================

def merge_cross_page_stories(pages: List[Dict]) -> List[Dict]:
    """
    Merge stories that span page boundaries.
    Only merge if both sides have continuation flags.
    """
    for i in range(len(pages) - 1):
        page_n = pages[i]
        page_n1 = pages[i + 1]

        stories_n = page_n.get('stories', [])
        stories_n1 = page_n1.get('stories', [])

        if not stories_n or not stories_n1:
            continue

        # Check if last story on page N continues to page N+1
        last_story = stories_n[-1]
        first_story = stories_n1[0]

        last_cont = last_story.get('continuation', {})
        first_cont = first_story.get('continuation', {})

        if (last_cont.get('continues_to_next_page') and
            first_cont.get('continues_from_previous_page')):

            # Both sides agree there's a continuation
            if last_story.get('classification') == 'NOT_A_STORY':
                continue
            if first_story.get('classification') == 'NOT_A_STORY':
                continue

            # Merge: keep higher classification
            merged_cls = _pick_higher_classification(
                last_story.get('classification', 'NOT_A_STORY'),
                first_story.get('classification', 'NOT_A_STORY')
            )

            last_story['classification'] = merged_cls
            last_story['spans_pages'] = [page_n['ref'], page_n1['ref']]
            last_story['start_segment_page2'] = first_story.get('start_segment')
            last_story['end_segment_page2'] = first_story.get('end_segment')

            # Remove the first story from page N+1 (it's merged into page N)
            stories_n1.pop(0)
            page_n1['stories'] = stories_n1

            print(f"  Merged cross-page story: {page_n['ref']} → {page_n1['ref']} ({merged_cls})")

    return pages


def _pick_higher_classification(cls1: str, cls2: str) -> str:
    """Pick the higher confidence classification."""
    order = {'YES': 4, 'HIGH_CONFIDENCE': 3, 'LOW_CONFIDENCE': 2, 'NOT_A_STORY': 1}
    if order.get(cls1, 0) >= order.get(cls2, 0):
        return cls1
    return cls2


def detect_duplicate_stories(pages: List[Dict]) -> List[Dict]:
    """Detect stories that appear on multiple pages (same passage quoted twice)."""
    fingerprints = {}

    for page_idx, page in enumerate(pages):
        segments = page.get('segments', [])
        for story_idx, story in enumerate(page.get('stories', [])):
            if story.get('classification') == 'NOT_A_STORY':
                continue

            start = story.get('start_segment', 0)
            end = story.get('end_segment', 0)

            text = ""
            for seg in segments:
                if start <= seg.get('index', -1) <= end:
                    text += re.sub(r'<[^>]+>', '', seg.get('english', ''))

            fp = ' '.join(text.split())[:150].strip().lower()
            if len(fp) < 20:
                continue

            if fp in fingerprints:
                orig_ref = fingerprints[fp]
                story['possible_duplicate_of'] = orig_ref
            else:
                fingerprints[fp] = page['ref']

    return pages


# ============================================================
# MAIN EXECUTION
# ============================================================

def load_pages_from_results(v5_paths: List[str]) -> List[Dict]:
    """Load pages from v5.1 result files."""
    all_pages = []
    for path in v5_paths:
        with open(path) as f:
            data = json.load(f)
            all_pages.extend(data.get('pages', []))
    return all_pages


def load_triage_results(triage_path: str) -> Dict[str, List[EventType]]:
    """Load pre-computed triage results."""
    with open(triage_path) as f:
        data = json.load(f)

    results = {}
    for ref, event_strs in data.get('triage_results', {}).items():
        results[ref] = [EventType(s) for s in event_strs]
    return results


def main():
    """Run v7 pipeline on Ketubot pages 2-60."""
    project_root = Path(__file__).parent.parent

    # Load ground truth
    feedback_path = str(project_root / 'validation' / 'feedback' /
                        'v5_1_feedback_anonymous_2026-02-05 (1).json')
    v5_paths = [
        str(project_root / 'results' / 'ketubot' / 'v5' / 'pages_2-39.json'),
        str(project_root / 'results' / 'ketubot' / 'v5' / 'pages_40-60.json'),
    ]

    db = GroundTruthDB()
    db.load_from_feedback(feedback_path, v5_paths)

    # Load pages
    pages = load_pages_from_results(v5_paths)
    print(f"Loaded {len(pages)} pages")

    # Load pre-computed triage (if available)
    triage_path = project_root / 'results' / 'v7' / 'event_triage_2-60.json'
    triage_results = None
    if triage_path.exists():
        print(f"Loading pre-computed triage from {triage_path}")
        triage_results = load_triage_results(str(triage_path))

    # Run pipeline
    detector = V7StoryDetector(ground_truth_db=db)
    results = detector.run_pipeline(pages, triage_results=triage_results, delay=0.5)

    # Save results
    output_path = project_root / 'results' / 'v7' / 'ketubot_v7_2-60.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {output_path}")

    # Count stories
    total_stories = 0
    for page in results.get('pages', []):
        for story in page.get('stories', []):
            if story.get('classification') != 'NOT_A_STORY':
                total_stories += 1
    print(f"Total stories found: {total_stories}")


if __name__ == '__main__':
    main()
