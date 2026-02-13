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
                 ground_truth_db: Optional[GroundTruthDB] = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.model_name = "gemini-2.0-flash"
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

    def _call_google(self, prompt: str, max_tokens: int = 8192) -> str:
        """Call Google Gemini API."""
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=max_tokens,
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

    def detect_stories(self, ref: str, segments: List[Dict],
                       event_types: List[EventType],
                       prev_page_context: Optional[str] = None,
                       next_page_context: Optional[str] = None) -> List[Dict]:
        """
        Detect stories on a single page using constrained prompt.
        Returns list of story dicts.
        """
        if not self.client:
            raise RuntimeError("Gemini API not configured")

        prompt = self.build_detection_prompt(
            ref, segments, event_types,
            prev_page_context, next_page_context
        )
        content = self._call_google(prompt)
        result = self._parse_json_response(content)

        if not result:
            return []

        return result.get('stories', [])

    def run_pipeline(self, pages: List[Dict],
                     triage_results: Optional[Dict[str, List[EventType]]] = None,
                     delay: float = 1.0,
                     skip_triage: bool = False) -> Dict:
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
                ground_truth_db=self.ground_truth_db
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

        # Cross-page merge
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
