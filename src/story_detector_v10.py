#!/usr/bin/env python3
"""
Talmud Story Detection v10: v9 baseline + Wave 4 LLM-side text-span emission.

v10 = v9 (Wave 1+2+3) PLUS:
  - Wave 4: extract_text_spans_via_llm replaces edit_text_internal_boundaries
    (regex) as the production pipeline path. Per-story Gemini call emits
    {start_offset, end_offset}. Regex retained only as fallback on LLM
    error. See tasks/PLAN_wave4.md.

Requires GEMINI_MODEL=gemini-2.5-flash or newer — the legacy
gemini-2.0-flash default was deprecated by Google in mid-2026.

At end of Phase 1 the file is byte-identical to v9 EXCEPT version metadata.
The class name V7StoryDetector is retained on purpose so existing call
sites only need to swap the import path. v9 stays frozen as the Wave 3
baseline.

Wave 2 fixes (mechanical, deterministic post-processors):

  Issue #3 — Story-START boundary snap (snap_start_to_introducer)
    Scan the first few segments of each detected multi-segment story for a
    canonical Hebrew introducer (מַעֲשֶׂה ב…, כִּי הָא ד…, הַהוּא ד…,
    הָנְהוּ בֵּי תְרֵי, כִּדְתַנְיָא, תַּנְיָא). If found at index >
    start, snap start forward. If found in the segment immediately BEFORE
    start, extend start back. Single-segment stories are not touched (their
    boundary issues are text-internal — see wave2_results.md).

  Issue #4 — Story-END boundary trim (trim_trailing_stam_segments)
    Walk the detected story from the end inward. Drop trailing segments
    that open with stam-Talmud markers (שְׁמַע מִינַּהּ, מַאי טַעְמָא,
    אִי הָכִי, וְאִי, שָׁאנֵי, הָכִי קָאָמַר, אֶלָּא) as long as at
    least one segment remains. Single-segment stories are not touched.

  Issue #6(b) — Biblical-actor filter (filter_biblical_actor_stories)
    If a story's identifiable_characters.evidence names only biblical
    actors (Moses, David, Nebuchadnezzar, "Jewish people" collective,
    etc.), demote to NOT_A_STORY. We are cataloguing rabbinic stories;
    biblical narratives belong in a different corpus.

Wave 1 fixes (mechanical, no model change):

  Issue #1 — Cross-page first-segment skip ("the glitch")
    merge_cross_page_stories_v7 gains Case 5: when both sides flag continuation
    and page2's first story starts at seg 1, override start_segment_page2 = 0
    to capture the seg-0 orphan. Distinct from Case 4 (which requires seg==0).

  Issue #2 — Gap-aware continuation
    stitch_cross_page_continuation and continuation_check reject any bridge
    that has intervening segments between the story end and the page boundary
    on page1. Empirically all 3 false-bridge cases with gap>0 (#11, #21, #26)
    were rejected without removing the 9 valid bridges (all of which have
    gap=0).

  Issue #5 — Triage lexical override
    Pages containing canonical story introducers (מַעֲשֶׂה ב…, הָנְהוּ בֵּי
    תְרֵי, ההוא ד…, כִּי הָא ד…) force Stage 2 to run even when Stage 1
    triage would skip them. On Kiddushin: 9 pages shifted from skipped→processed.

  Issue #7 — Mishnah-only story filter
    Stories whose segments lie entirely within a Mishnah block (between
    מַתְנִי׳ and the next גְּמָ׳ marker) are moved out of `stories` and into
    `mishnah_stories`. Detection uses Sefaria HTML markers and handles
    mid-page mishnah continuation from the prior daf.

v7 (canonical) is left untouched. Revert = swap import back.
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
- A passage whose entire activity is verbal exchange (אֲמַר לוֹ … אֲמַר לוֹ)
  with NO physical action. Speech alone is not a story.
- Biblical narrative (named actors are only biblical figures like Moses, David,
  Nebuchadnezzar, "the Jewish people" as a collective). We catalog rabbinic stories.
- Fewer than 2 distinct actions, OR no change/conflict between start and end.
  A story requires AT LEAST two distinct actions and some transformation.

## BORDERLINE → LOW_CONFIDENCE (not NOT_A_STORY)

One real event + discussion about it → LOW_CONFIDENCE
Mainly dialogue but with some real events → LOW_CONFIDENCE
Weak causality but some change → LOW_CONFIDENCE

## MULTIPLE STORIES PER PAGE

A page often contains MORE than one distinct story. Detect EVERY story on
the page — not only the most prominent one. Two stories are distinct when
they have different protagonists, different settings, or are separated by
halakhic discussion (even a single intervening segment). Do not stop after
finding the first story; scan all segments.

## EMBEDDED STORIES — DETECT THESE TOO

Stories often appear INSIDE other Talmudic structures (baraitot, objections).
Do not skip them. The framing formula does NOT disqualify the story body.

Pattern 1 — BARAITA-EMBEDDED (תניא / דתניא + narrative)
  Example (Ketubot 111b seg 13):
    "תניא, אמר רב יוסי: מעשה בשיחין באחד שהניח לו אביו שלשה בדי חרדל
    ונפשח אחד מהן ונמצאו בו תשעה קבין חרדל..."
  → Classification: HIGH_CONFIDENCE. The תניא citation introduces a real
    incident (מעשה ב) with character, action, and outcome.

Pattern 2 — OBJECTION-EMBEDDED (תא שמע / מיתיבי / איתיביה + narrative)
  Example (Ketubot 91a segs 19-20):
    "תא שמע: דניכסי דבי בר צרצור מועטין ונתרבו הוו, ואתו לקמיה דרב עמרם.
    אמר להו: זילו פייסינהו. לא אשגחו..."
  → Classification: YES. The תא שמע objection frame doesn't disqualify
    the narrative — there are characters who act (came before Rav Amram,
    he ruled, they refused, etc.) with a real outcome.

Rule: when a baraita citation or objection formula PRECEDES a narrative
with characters and physical events, the narrative IS a story — include it
(start_segment at the formula or at the narrative open, per BOUNDARY RULES).

## BOUNDARY RULES

- Story STARTS at first NARRATIVE event, not preceding legal ruling
- Story ENDS when its narrative arc resolves — this includes:
  - The final narrative action
  - A rabbi's ruling that RESOLVES the narrative case (this IS the story's conclusion)
  - The consequence or outcome of the events
- Story does NOT include Talmudic commentary that ANALYZES the story from outside
- Talmudic questions (beginning with וְהָא) challenging the story are NOT part of it
- Exception: Rabbi directly referencing story events IS part of story
- Do NOT split one continuous story into two
- An abrupt ending is NOT a reason to weaken a story — some stories end abruptly for literary effect
- "Beyond the letter of the law" (לפנים משורת הדין) is NOT a weakener — it describes legal
  precedent status, not whether the passage is a story

## CROSS-PAGE CONTINUATION

Stories frequently span Talmud page boundaries. Pagination is a printing artifact, not a narrative boundary.

Set continues_from_previous_page = true when:
- The FIRST segments of THIS page continue a narrative from the previous page
- The previous page context shows the same characters/situation
- This page begins mid-narrative without a new story introduction

Set continues_to_next_page = true when:
- A story reaches the LAST segments without narrative resolution
- The next page context shows continuation of the same characters/situation

When continuation is detected, include ALL story segments on THIS page — do not leave
continuation segments undetected.

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

    # Models that require thinking mode (can't set thinking_budget=0)
    THINKING_REQUIRED_MODELS = {'gemini-3-pro-preview', 'gemini-2.5-pro'}

    def _call_google(self, prompt: str, max_tokens: int = 8192,
                     json_mode: bool = False) -> str:
        """Call Google Gemini API.

        Args:
            json_mode: If True, use response_mime_type='application/json'.
                       For Flash models, also disables thinking to prevent
                       token exhaustion. For Pro models (which require thinking),
                       increases max_output_tokens instead.
        """
        try:
            config_kwargs = {
                'max_output_tokens': max_tokens,
                'temperature': 0.1,
            }
            if json_mode:
                config_kwargs['response_mime_type'] = 'application/json'
                if self.model_name in self.THINKING_REQUIRED_MODELS:
                    # Pro models require thinking — give enough tokens for
                    # thinking + structured JSON output
                    config_kwargs['max_output_tokens'] = max(max_tokens, 32768)
                else:
                    # Flash models: disable thinking for structured output
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
                    continue  # Skip thinking tokens, keep only output
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

    # -- Wave 4: LLM-side text-span emission --------------------------

    _TEXT_SPAN_PROMPT_TEMPLATE = (
        "You are reading a Talmud passage to determine the EXACT character "
        "boundaries of a narrative story embedded inside one or two segments.\n\n"
        "Story summary: {summary}\n\n"
        "Start segment text (Hebrew, no vowel pointing):\n"
        "<<<\n{start_text}\n>>>\n\n"
        "End segment text (Hebrew, no vowel pointing):\n"
        "<<<\n{end_text}\n>>>\n\n"
        "Return start_offset: the character offset in the start segment where "
        "the STORY content begins. Return -1 if the story starts at the very "
        "beginning of the start segment.\n\n"
        "Return end_offset: the character offset in the end segment where the "
        "STORY content ends (exclusive). Return -1 if the story extends to the "
        "end of the end segment.\n\n"
        "Rules:\n"
        "- Editorial framing BEFORE the story (e.g. a stam-Talmud setup line, "
        "  a legal question that introduces the case) is NOT story content — "
        "  set start_offset past it.\n"
        "- A stam-Talmud aside AFTER the story body is NOT story content — "
        "  set end_offset to where it begins. Common closing patterns to cut:\n"
        "    * \"שמע מינה...\" (legal inference)\n"
        "    * \"אי הכי...\" (legal objection)\n"
        "    * \"שאני...\" (legal distinguishing)\n"
        "    * \"ולאו משום ד... אלא משום ד...\" (stam re-explains the story's "
        "      reasoning — cut from ולאו onward)\n"
        "    * a final \"אלא\" that introduces a competing stam-Talmud "
        "      explanation rather than a character's speech\n"
        "- Phrases like \"אלא\" or rabbi names INSIDE the story body (e.g. a "
        "  character speaking in the narrative) ARE story content — do not cut.\n"
        "- For the start side: if the segment opens with a stam-Talmud "
        "  legal question or framing that introduces the case (e.g. \"לא, "
        "  לעולם ד...\", \"כי הא ד...\" used as setup), trim it; if the "
        "  segment opens directly with the story (\"ההוא גברא\", \"מעשה ב\", "
        "  rabbi-narrative), keep it whole.\n"
        "- If any doubt about whether to cut, return -1 for that side. "
        "  But do NOT return -1 if you can identify a clear stam-Talmud "
        "  closing pattern above — those MUST be cut.\n\n"
        "Return ONLY valid JSON: {{\"start_offset\": <int>, \"end_offset\": <int>}}"
    )

    def _llm_text_span_for_story(self, story: Dict,
                                  start_seg_text: str,
                                  end_seg_text: str) -> Optional[Dict]:
        """Single Gemini call. Returns {'start_offset': int, 'end_offset': int}
        in nikud-STRIPPED coordinates, or None on any error."""
        if not self.client:
            return None
        summary = story.get('summary') or story.get('text', '') or ''
        if not summary:
            # Derive from criteria.multiple_events.events if available
            crit = story.get('criteria', {}) or {}
            events = (crit.get('multiple_events', {}) or {}).get('events', [])
            if events:
                summary = '; '.join(events)
        summary = (summary or '(no summary available)')[:400]
        prompt = self._TEXT_SPAN_PROMPT_TEMPLATE.format(
            summary=summary,
            start_text=start_seg_text,
            end_text=end_seg_text,
        )
        try:
            raw = self._call_google(prompt, max_tokens=512, json_mode=True)
        except Exception:
            return None
        parsed = self._parse_json_response(raw)
        if not parsed:
            return None
        try:
            so = int(parsed.get('start_offset', -1))
            eo = int(parsed.get('end_offset', -1))
        except (TypeError, ValueError):
            return None
        return {'start_offset': so, 'end_offset': eo}

    def extract_text_spans_via_llm(self, pages: List[Dict]) -> Dict[str, int]:
        """
        Wave 4 replacement for edit_text_internal_boundaries.

        For each non-NOT_A_STORY story, ask Gemini for the character offsets
        where the story begins/ends inside its first/last segment. Offsets
        are returned in nikud-stripped coordinates and mapped back to the
        original (with-nikud) text before being recorded.

        Per-story outcomes (text_span_source):
          - 'llm'           : LLM ran and set at least one span offset.
          - 'llm_kept_full' : LLM ran, returned -1/-1 ("no trim needed").
          - 'skipped'       : LLM call errored. NO regex fallback — the
                              regex over-trims (Jeff 2026-06-03), so
                              silent substitution would re-introduce the
                              bug Wave 4 exists to fix. We fail loud:
                              warn to stdout, leave spans absent.

        Note: regex IS used when self.client is None (offline/test path);
        that branch lives in the Stage 4 wiring, not here.

        Returns counts: {'llm': N, 'llm_kept_full': N, 'skipped': N}.
        """
        counts = {'llm': 0, 'llm_kept_full': 0, 'skipped': 0}
        for page in pages:
            segments = page.get('segments', [])
            seg_by_idx = {s.get('index', i): s for i, s in enumerate(segments)}
            for story in page.get('stories', []):
                if story.get('classification') == 'NOT_A_STORY':
                    continue
                start = story.get('start_segment')
                end = story.get('end_segment')
                if start is None or end is None:
                    continue
                start_seg = seg_by_idx.get(start)
                end_seg = seg_by_idx.get(end)
                if not start_seg or not end_seg:
                    continue

                start_heb = start_seg.get('hebrew', '') or ''
                end_heb = end_seg.get('hebrew', '') or ''
                start_stripped, start_map = _strip_nikud_with_map(start_heb)
                end_stripped, end_map = _strip_nikud_with_map(end_heb)

                llm = self._llm_text_span_for_story(
                    story, start_stripped, end_stripped
                )

                if llm is None:
                    # LLM error — do NOT fall back to regex. Regex
                    # over-trims (Jeff 2026-06-03); silent substitution
                    # would re-introduce the bug. Fail loud.
                    page_ref = page.get('ref', '?')
                    print(
                        f"  WARN text_span LLM error on {page_ref} "
                        f"story {start}-{end}: leaving spans absent"
                    )
                    story['text_span_source'] = 'skipped'
                    counts['skipped'] += 1
                    continue

                # Valid LLM response (incl. -1/-1 meaning "keep full")
                so, eo = llm['start_offset'], llm['end_offset']
                emitted = False
                if so is not None and so > 0 and so < len(start_stripped):
                    story['text_span_start'] = {
                        'segment': start,
                        'char_offset': start_map[so],
                        'source': 'llm',
                    }
                    emitted = True
                if eo is not None and eo > 0 and eo < len(end_stripped):
                    if start == end and so not in (None, -1) and eo <= so:
                        pass  # bad LLM output — ignore the end side
                    else:
                        story['text_span_end'] = {
                            'segment': end,
                            'char_offset': end_map[eo],
                            'source': 'llm',
                        }
                        emitted = True

                if emitted:
                    story['text_span_source'] = 'llm'
                    counts['llm'] += 1
                else:
                    story['text_span_source'] = 'llm_kept_full'
                    counts['llm_kept_full'] += 1
        return counts

    def detect_stories(self, ref: str, segments: List[Dict],
                       event_types: List[EventType],
                       prev_page_context: Optional[str] = None,
                       next_page_context: Optional[str] = None) -> List[Dict]:
        """
        Detect stories on a single page using constrained prompt.

        Wave 3 Item 1 (Option A fallback): when Stage 2 returns ≥1 real
        story but the page may have more, make ONE additional "find more
        stories" pass listing the already-detected ranges and asking
        Stage 2 for any others. New non-overlapping stories are appended.
        Bounded to a single extra call per page to cap cost.

        Returns list of story dicts. Retries once on JSON parse failure.
        """
        if not self.client:
            raise RuntimeError("Gemini API not configured")

        prompt = self.build_detection_prompt(
            ref, segments, event_types,
            prev_page_context, next_page_context
        )
        stories = self._call_stage2(ref, prompt)

        # Iterative multi-story pass (item 1 fallback). Only run if the
        # first pass found at least one real story — pages with zero
        # stories don't benefit from "find more."
        real_stories = [s for s in stories
                        if s.get('classification') not in ('NOT_A_STORY', None)]
        if real_stories:
            extra = self._find_additional_stories(
                ref, segments, event_types, real_stories,
                prev_page_context, next_page_context,
            )
            if extra:
                merged = self._merge_nonoverlapping(stories, extra)
                added = len(merged) - len(stories)
                if added:
                    print(f"    Iterative Stage 2: +{added} additional stories")
                stories = merged

        return stories

    def _call_stage2(self, ref: str, prompt: str) -> List[Dict]:
        """Single Stage 2 LLM call with JSON-parse retry. Returns story list."""
        use_json = self._use_json_mode
        for attempt in range(2):
            content = self._call_google(prompt, json_mode=use_json)
            if use_json:
                try:
                    result = json.loads(content) if content else None
                except json.JSONDecodeError:
                    result = self._parse_json_response(content)
            else:
                result = self._parse_json_response(content)
            if result is not None:
                if isinstance(result, list):
                    if (len(result) == 1 and isinstance(result[0], dict)
                            and 'stories' in result[0]):
                        return result[0]['stories']
                    return result
                return result.get('stories', [])
            if attempt == 0:
                print(f"    Retrying {ref} (JSON parse failed)...")
                time.sleep(1)
        return []

    def _find_additional_stories(self, ref: str, segments: List[Dict],
                                  event_types: List[EventType],
                                  detected: List[Dict],
                                  prev_page_context: Optional[str],
                                  next_page_context: Optional[str]) -> List[Dict]:
        """One additional Stage 2 call asking for stories NOT already in
        `detected`. Returns the new story list (caller dedupes by overlap)."""
        already = '; '.join(
            f"seg {s.get('start_segment')}-{s.get('end_segment')} "
            f"({s.get('classification','?')})"
            for s in detected
        )
        base_prompt = self.build_detection_prompt(
            ref, segments, event_types,
            prev_page_context, next_page_context,
        )
        extra_instr = (
            "\n\n## ADDITIONAL DETECTION PASS\n\n"
            f"On this page we have ALREADY detected these stories: {already}.\n"
            "Re-scan the page for any OTHER distinct stories that you did "
            "not include in the prior pass. A second story is distinct if it "
            "has different protagonists, a different setting, or is separated "
            "from the prior stories by halakhic discussion (even one segment).\n"
            "Return ONLY stories that do NOT overlap the already-detected "
            "segment ranges. If there are no additional stories, return "
            '{"page_ref": "' + ref + '", "stories": []}.\n'
        )
        return self._call_stage2(ref, base_prompt + extra_instr)

    @staticmethod
    def _merge_nonoverlapping(orig: List[Dict],
                              extra: List[Dict]) -> List[Dict]:
        """Append stories from `extra` whose [start,end] does not overlap
        any range already in `orig`. Skips malformed entries."""
        def rng(s):
            a, b = s.get('start_segment'), s.get('end_segment')
            return (a, b) if a is not None and b is not None else None
        used = [rng(s) for s in orig if rng(s)]
        out = list(orig)
        for s in extra:
            r = rng(s)
            if not r:
                continue
            if any(r[0] <= u[1] and r[1] >= u[0] for u in used):
                continue
            out.append(s)
            used.append(r)
        return out

    @staticmethod
    def _has_intervening_gap_on_page1(story: Dict, segments: List[Dict]) -> bool:
        """
        Wave 1 Issue #2: Gap-aware continuation check.
        Returns True if there are non-empty segments between the story's end
        and the page boundary on page1. Empirically, any intervening segment
        (even DELIBERATION) breaks narrative continuity for cross-page bridges
        — Jeff's 3 gap>0 false-bridge cases (#11 12b→13a, #21 29b→30a,
        #26 31a→31b) all had intervening DELIBERATION/NARRATIVE content.
        """
        if not segments:
            return False
        last_seg_idx = max(s.get('index', 0) for s in segments)
        story_end = story.get('end_segment', 0)
        return story_end < last_seg_idx

    def stitch_cross_page_continuation(self, all_results: List[Dict],
                                        pages: List[Dict],
                                        triage_results: Dict[str, List[EventType]],
                                        delay: float = 0.5) -> int:
        """
        Post-detection stitching for stories with continues_to_next_page=true
        that were NOT merged by the merge passes (no story detected on next page start).

        Makes a targeted LLM call: story text + first 8 segments of next page →
        "Where does this story end on page N+1?"

        Returns count of stories stitched.
        """
        if not self.client:
            return 0

        stitched = 0
        # Build ref→page lookup for all_results
        result_by_ref = {r.get('ref', ''): r for r in all_results}
        # Build ref→page lookup for original pages (for segment data)
        page_by_ref = {p.get('ref', ''): p for p in pages}
        # Build ordered ref list
        ref_order = [p.get('ref', '') for p in pages]

        for page_result in all_results:
            ref = page_result.get('ref', '')
            stories = page_result.get('stories', [])
            if not stories:
                continue

            for story in stories:
                if story.get('classification') == 'NOT_A_STORY':
                    continue
                if story.get('spans_pages'):
                    continue  # Already merged
                cont = story.get('continuation', {})
                if not cont.get('continues_to_next_page'):
                    continue

                # Find next page
                try:
                    idx = ref_order.index(ref)
                except ValueError:
                    continue
                if idx >= len(ref_order) - 1:
                    continue
                next_ref = ref_order[idx + 1]
                next_page = page_by_ref.get(next_ref)
                if not next_page:
                    continue

                # Wave 1 Issue #2: reject if there's intervening material on page1
                # between the story end and the page boundary.
                segments_p1 = page_result.get('segments', [])
                if self._has_intervening_gap_on_page1(story, segments_p1):
                    continue

                # Check that no merge happened — the next page's first story
                # should NOT already be part of this story
                next_result = result_by_ref.get(next_ref)
                next_stories = next_result.get('stories', []) if next_result else []
                if next_stories and next_stories[0].get('continuation', {}).get('continues_from_previous_page'):
                    continue  # Already handled by merge logic

                # Build story text from current page
                segments = page_result.get('segments', [])
                start = story.get('start_segment', 0)
                end = story.get('end_segment', 0)
                story_lines = []
                for seg in segments:
                    if start <= seg.get('index', -1) <= end:
                        eng = re.sub(r'<[^>]+>', '', seg.get('english', ''))[:300]
                        story_lines.append(f"Seg {seg['index']}: {eng}")
                story_text = '\n'.join(story_lines)

                # Build next page segments (first 8)
                next_segs = next_page.get('segments', [])[:8]
                next_events = triage_results.get(next_ref, [])
                next_lines = []
                for seg in next_segs:
                    idx_s = seg.get('index', 0)
                    eng = re.sub(r'<[^>]+>', '', seg.get('english', ''))[:300]
                    et = next_events[idx_s].value if idx_s < len(next_events) else "UNKNOWN"
                    next_lines.append(f"[{et}] Seg {idx_s}: {eng}")
                next_text = '\n'.join(next_lines)

                prompt = f"""A story on {ref} was detected as continuing to the next page ({next_ref}).
No story was detected on the start of {next_ref} to merge with.

STORY TEXT (from {ref}):
{story_text}

SUMMARY: {story.get('one_sentence_summary', 'N/A')}

FIRST SEGMENTS OF {next_ref} (with event types):
{next_text}

QUESTION: Does this story continue on {next_ref}? If yes, at which segment does it end?

IMPORTANT GUIDELINES:
- The continuation is at the VERY TOP of {next_ref} (typically the first 1-3 segments).
- Look for where the Talmud shifts to a new topic or introduces a new sage — that marks the END of the continuation.
- Do NOT skip past the top segments to find a different story further down the page.
- If the top segments don't clearly continue the story from {ref}, set continues_on_page to false.

Return JSON:
{{
  "continues_on_page": true/false,
  "end_segment": <int or null>,
  "reasoning": "..."
}}"""

                try:
                    use_json = self._use_json_mode
                    content = self._call_google(prompt, max_tokens=2048, json_mode=use_json)
                    if use_json:
                        try:
                            result = json.loads(content) if content else None
                        except json.JSONDecodeError:
                            result = self._parse_json_response(content)
                    else:
                        result = self._parse_json_response(content)

                    if result and result.get('continues_on_page'):
                        end_seg = result.get('end_segment')
                        if end_seg is not None:
                            story['spans_pages'] = [ref, next_ref]
                            story['start_segment_page2'] = 0
                            story['end_segment_page2'] = end_seg
                            story['cross_page_stitched'] = True
                            stitched += 1
                            print(f"  Stitched: {ref} → {next_ref} (ends at seg {end_seg})")

                    if delay > 0:
                        time.sleep(delay)

                except Exception as e:
                    print(f"  Stitch error for {ref}: {e}")

        return stitched

    def continuation_check(self, all_results: List[Dict],
                           pages: List[Dict],
                           triage_results: Dict[str, List[EventType]],
                           delay: float = 0.5) -> int:
        """
        Stage 4f: Continuation check for stories near page boundaries.

        Unlike stitch (4d) which only fires when continues_to_next_page is already set,
        this checks stories that are the LAST story on their page AND end near the
        page boundary, but were NOT flagged as continuing.

        Asks: "Does THIS specific story continue on the next page?"
        Binary yes/no — NOT "find a story."

        Returns count of stories extended.
        """
        if not self.client:
            return 0

        extended = 0
        page_by_ref = {p.get('ref', ''): p for p in pages}
        ref_order = [p.get('ref', '') for p in pages]

        for page_result in all_results:
            ref = page_result.get('ref', '')
            stories = page_result.get('stories', [])
            if not stories:
                continue

            # Find the last real story on this page
            real_stories = [s for s in stories
                           if s.get('classification') != 'NOT_A_STORY'
                           and not s.get('spans_pages')]
            if not real_stories:
                continue

            last_story = max(real_stories, key=lambda s: s.get('end_segment', 0))

            # Skip if already has continuation flag or is already merged
            cont = last_story.get('continuation', {})
            if cont.get('continues_to_next_page'):
                continue  # Already handled by stitch pass (4d)

            # Check if story ends near the page boundary (within last 3 segments)
            segments = page_result.get('segments', [])
            if not segments:
                continue
            last_seg_idx = max(s.get('index', 0) for s in segments)
            story_end = last_story.get('end_segment', 0)
            if story_end < last_seg_idx - 3:
                continue  # Story ends too far from page boundary

            # Wave 1 Issue #2: gap-aware — story MUST end at the page boundary.
            # Any intervening segment breaks continuity (empirically confirmed
            # on Jeff's false-bridge cases #21 29b→30a, #26 31a→31b).
            if story_end < last_seg_idx:
                continue

            # Find next page
            try:
                idx = ref_order.index(ref)
            except ValueError:
                continue
            if idx >= len(ref_order) - 1:
                continue
            next_ref = ref_order[idx + 1]
            next_page = page_by_ref.get(next_ref)
            if not next_page:
                continue

            # Build story text
            start = last_story.get('start_segment', 0)
            end = last_story.get('end_segment', 0)
            story_lines = []
            for seg in segments:
                if start <= seg.get('index', -1) <= end:
                    eng = re.sub(r'<[^>]+>', '', seg.get('english', ''))[:300]
                    heb = seg.get('hebrew', '')[:200]
                    story_lines.append(f"Seg {seg['index']}:\n  English: {eng}\n  Hebrew: {heb}")
            story_text = '\n'.join(story_lines)

            # Build next page segments (first 8)
            next_segs = next_page.get('segments', [])[:8]
            next_events = triage_results.get(next_ref, [])
            next_lines = []
            for seg in next_segs:
                idx_s = seg.get('index', 0)
                eng = re.sub(r'<[^>]+>', '', seg.get('english', ''))[:300]
                heb = seg.get('hebrew', '')[:200]
                et = next_events[idx_s].value if idx_s < len(next_events) else "UNKNOWN"
                next_lines.append(f"[{et}] Seg {idx_s}:\n  English: {eng}\n  Hebrew: {heb}")
            next_text = '\n'.join(next_lines)

            summary = last_story.get('one_sentence_summary', 'N/A')

            prompt = f"""You are checking whether a specific Talmudic story continues across a page boundary.

STORY ON {ref} (segments {start}-{end}):
{story_text}

SUMMARY: {summary}

FIRST SEGMENTS OF NEXT PAGE ({next_ref}):
{next_text}

QUESTION: Is the text at the top of {next_ref} a direct continuation of this specific story?

To answer YES, ALL of these must be true:
- The SAME characters or rabbis from the story appear at the top of {next_ref}
- The SAME situation or narrative event continues (not a new topic)
- The narrative flows directly — removing the page break would read as one story

To answer NO (most cases):
- The next page starts a new topic, new discussion, or new story
- Different characters appear
- The connection is only thematic (same legal topic) but not the same narrative

This is a CONSERVATIVE check. When in doubt, answer NO.

Return JSON:
{{
  "continues": true/false,
  "end_segment": <int — last segment of continuation on {next_ref}, or null if false>,
  "reasoning": "brief explanation"
}}"""

            try:
                use_json = self._use_json_mode
                content = self._call_google(prompt, max_tokens=2048, json_mode=use_json)
                if use_json:
                    try:
                        result = json.loads(content) if content else None
                    except json.JSONDecodeError:
                        result = self._parse_json_response(content)
                else:
                    result = self._parse_json_response(content)

                if result and result.get('continues'):
                    end_seg = result.get('end_segment')
                    if end_seg is not None:
                        last_story['spans_pages'] = [ref, next_ref]
                        last_story['start_segment_page2'] = 0
                        last_story['end_segment_page2'] = end_seg
                        last_story['continuation_check_extended'] = True
                        extended += 1
                        print(f"  Continuation check: {ref} → {next_ref} (ends seg {end_seg})")
                        print(f"    Reasoning: {result.get('reasoning', '')[:100]}")

                if delay > 0:
                    time.sleep(delay)

            except Exception as e:
                print(f"  Continuation check error for {ref}: {e}")

        return extended

    def run_pipeline(self, pages: List[Dict],
                     triage_results: Optional[Dict[str, List[EventType]]] = None,
                     delay: float = 1.0,
                     skip_triage: bool = False,
                     enable_adversarial: bool = False,
                     tractate: str = 'Ketubot') -> Dict:
        """
        Full v7 pipeline: triage → detect → (adversarial) → (boundary refine)

        Args:
            pages: List of page dicts with 'ref' and 'segments'
            triage_results: Pre-computed triage results (or None to compute)
            delay: Delay between API calls
            skip_triage: If True, process all pages (no triage filtering)
            tractate: Tractate name for output metadata
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
            # Wave 1 Issue #5: lexical override — if the page contains a canonical
            # story introducer (מַעֲשֶׂה ב…, הָנְהוּ בֵּי תְרֵי, הַהוּא ד…,
            # כִּי הָא ד…), force Stage 2 to run regardless of triage skip.
            if skip_triage or not EventTriager.should_skip_page(events) \
                    or _page_has_story_introducer(page):
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
                    prev_page = pages[page_idx - 1]
                    prev_segs = prev_page.get('segments', [])
                    prev_ref = prev_page.get('ref', '')
                    prev_events = triage_results.get(prev_ref, []) if triage_results else []
                    if prev_segs:
                        lines = []
                        for s in prev_segs[-5:]:
                            eng = re.sub(r'<[^>]+>', '', s.get('english', ''))[:300]
                            heb = s.get('hebrew', '')[:200]
                            idx = s.get('index', 0)
                            et = prev_events[idx].value if idx < len(prev_events) else "UNKNOWN"
                            lines.append(f"[{et}] Prev Seg {idx}:\n  English: {eng}\n  Hebrew: {heb}")
                        prev_ctx = '\n'.join(lines)
                if page_idx < len(pages) - 1:
                    next_page = pages[page_idx + 1]
                    next_segs = next_page.get('segments', [])
                    next_ref = next_page.get('ref', '')
                    next_events = triage_results.get(next_ref, []) if triage_results else []
                    if next_segs:
                        lines = []
                        for s in next_segs[:5]:
                            eng = re.sub(r'<[^>]+>', '', s.get('english', ''))[:300]
                            heb = s.get('hebrew', '')[:200]
                            idx = s.get('index', 0)
                            et = next_events[idx].value if idx < len(next_events) else "UNKNOWN"
                            lines.append(f"[{et}] Next Seg {idx}:\n  English: {eng}\n  Hebrew: {heb}")
                        next_ctx = '\n'.join(lines)

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

        # 4d: Stitch unmerged boundary stories via targeted LLM calls
        stitch_count = self.stitch_cross_page_continuation(
            all_results, pages, triage_results, delay=delay
        )
        if stitch_count:
            print(f"  Cross-page stitching: {stitch_count} stories extended")

        # 4f: Continuation check — for stories near page boundaries without continuation flags
        continuation_count = self.continuation_check(
            all_results, pages, triage_results, delay=delay
        )
        if continuation_count:
            print(f"  Continuation check: {continuation_count} stories extended")

        # 4g (Wave 1 Issue #7): Filter Mishnah-only stories
        mishnah_filtered = filter_mishnah_only_stories(all_results)
        if mishnah_filtered:
            print(f"  Mishnah filter: {mishnah_filtered} stories moved to mishnah_stories")

        # 4h (Wave 2 Issue #3): snap story start to canonical introducer
        snapped = snap_start_to_introducer(all_results)
        if snapped:
            print(f"  Start-boundary snap: {snapped} stories adjusted")

        # 4i (Wave 2 Issue #4): trim trailing stam-Talmud segments
        trimmed = trim_trailing_stam_segments(all_results)
        if trimmed:
            print(f"  End-boundary trim: {trimmed} stories trimmed")

        # 4j (Wave 2 Issue #6b): demote biblical-actor-only stories
        biblical = filter_biblical_actor_stories(all_results)
        if biblical:
            print(f"  Biblical-actor filter: {biblical} stories demoted")

        # 4k (Wave 4): LLM-side text-span emission. No regex fallback on
        # LLM error — see extract_text_spans_via_llm docstring.
        if self.client:
            span_counts = self.extract_text_spans_via_llm(all_results)
            print(
                "  Text-span (Wave 4): "
                f"llm={span_counts['llm']} "
                f"kept_full={span_counts['llm_kept_full']} "
                f"skipped={span_counts['skipped']}"
            )
        else:
            # No API client (e.g. offline tests) — pure regex pass.
            text_edited = edit_text_internal_boundaries(all_results)
            print(
                "  Text-span (regex-only, no client): "
                f"{text_edited} stories got sub-segment spans"
            )

        # Detect duplicates
        all_results = detect_duplicate_stories(all_results)

        return {
            'tractate': tractate,
            'version': 'v10',
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

def _segment_has_ruling(seg: Dict, story: Dict) -> bool:
    """
    Check if a DELIBERATION segment contains a ruling that resolves the story.

    A ruling segment has ruling verbs AND mentions a character from the story.
    These should NOT be trimmed from story boundaries.
    """
    eng = re.sub(r'<[^>]+>', '', seg.get('english', '')).lower()

    ruling_verbs = [
        'ruled', 'said to him', 'said to them', 'said to her',
        'permitted', 'forbade', 'decreed', 'excommunicated',
        'ordered', 'instructed', 'declared', 'pronounced',
    ]
    has_ruling = any(verb in eng for verb in ruling_verbs)
    if not has_ruling:
        return False

    # Check if segment mentions a character from the story
    # Use the story's criteria for character evidence, or check for rabbi names
    criteria = story.get('criteria', {})
    chars = criteria.get('identifiable_characters', {})
    char_evidence = str(chars.get('evidence', '')).lower()

    # Extract potential names from the character evidence
    # Also check common rabbi name patterns in the segment
    rabbi_pattern = r'\b(?:rabbi|rav|r\.|mar|rab)\s+\w+'
    story_names = set(re.findall(rabbi_pattern, char_evidence))
    seg_names = set(re.findall(rabbi_pattern, eng))

    # If any character name from the story appears in this segment, it's a ruling
    if story_names and seg_names and story_names & seg_names:
        return True

    # Fallback: if the segment has a ruling verb, be conservative — keep it
    # if the story summary mentions similar characters
    summary = story.get('one_sentence_summary', '').lower()
    if summary:
        summary_names = set(re.findall(rabbi_pattern, summary))
        if summary_names and seg_names and summary_names & seg_names:
            return True

    return False


def refine_boundaries_with_event_tags(pages: List[Dict],
                                       triage_results: Dict[str, List[EventType]]) -> int:
    """
    Trim DELIBERATION segments from story edges using triage event types.

    If a story starts or ends with segments that are DELIBERATION in the triage,
    shrink the boundary inward. This prevents including legal commentary at the
    edges of stories.

    Guard: DELIBERATION segments containing ruling verbs that resolve the story's
    narrative case are NOT trimmed (they are the story's conclusion).

    Returns count of stories modified.
    """
    changes = 0

    for page in pages:
        ref = page.get('ref', '')
        events = triage_results.get(ref, [])
        segments = page.get('segments', [])
        if not events:
            continue

        # Build index→segment lookup
        seg_by_idx = {s.get('index', i): s for i, s in enumerate(segments)}

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

            # Trim DELIBERATION from the end — but guard ruling segments
            while end > start and end < len(events):
                if events[end] == EventType.DELIBERATION:
                    seg = seg_by_idx.get(end)
                    if seg and _segment_has_ruling(seg, story):
                        break  # This is a ruling that resolves the story — keep it
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

        # Case 4: Both sides are REAL stories at the boundary with continuation flags
        # This is the key gap — previously only handled NOT_A_STORY combinations
        # Fix C: Tightened from <= 1 to == 0. Seg 1 stories are often independent
        # (e.g. 61a→61b where the seg 1 story is different).
        if (last_story_n and first_story_n1 and
            last_story_n.get('classification') not in ('NOT_A_STORY', None) and
            first_story_n1.get('classification') not in ('NOT_A_STORY', None) and
            last_story_n.get('end_segment', -1) >= last_seg_idx - 1 and
            first_story_n1.get('start_segment', 999) == 0):

            # Check continuation flags — at least one side must signal continuation
            last_cont = last_story_n.get('continuation', {})
            first_cont = first_story_n1.get('continuation', {})
            has_continuation = (
                last_cont.get('continues_to_next_page') or
                first_cont.get('continues_from_previous_page')
            )

            if has_continuation:
                merged_cls = _pick_higher_classification(
                    last_story_n.get('classification', 'LOW_CONFIDENCE'),
                    first_story_n1.get('classification', 'LOW_CONFIDENCE')
                )

                last_story_n['classification'] = merged_cls
                last_story_n['spans_pages'] = [ref_n, ref_n1]
                last_story_n['start_segment_page2'] = first_story_n1.get('start_segment')
                last_story_n['end_segment_page2'] = first_story_n1.get('end_segment')
                last_story_n['cross_page_merge_v7'] = True

                # Merge summaries
                summary_n = last_story_n.get('one_sentence_summary', '')
                summary_n1 = first_story_n1.get('one_sentence_summary', '')
                if summary_n and summary_n1:
                    last_story_n['one_sentence_summary'] = f"{summary_n} {summary_n1}"
                elif summary_n1:
                    last_story_n['one_sentence_summary'] = summary_n1

                stories_n1.pop(0)
                page_n1['stories'] = stories_n1

                print(f"  Cross-page merge (v7): {ref_n} → {ref_n1} ({merged_cls}) "
                      f"[both real stories merged via continuation flags]")
                continue

        # Case 5 (Wave 1 Issue #1): "First-segment skip glitch" — fires when BOTH
        # sides flag continuation but the next-page story starts at seg 1 (not 0),
        # leaving seg 0 of page2 orphaned. Distinct from Case 4 (which requires
        # start==0) and from the seg-1-independent risk (61a→61b) because here
        # BOTH continuation flags are set (high confidence the merge is real).
        # Override start_segment_page2 = 0 to capture the missed leading segment.
        if (last_story_n and first_story_n1 and
            last_story_n.get('classification') not in ('NOT_A_STORY', None) and
            first_story_n1.get('classification') not in ('NOT_A_STORY', None) and
            last_story_n.get('end_segment', -1) >= last_seg_idx and
            first_story_n1.get('start_segment', 999) == 1):

            last_cont = last_story_n.get('continuation', {})
            first_cont = first_story_n1.get('continuation', {})
            both_flag = (
                last_cont.get('continues_to_next_page') and
                first_cont.get('continues_from_previous_page')
            )

            if both_flag:
                merged_cls = _pick_higher_classification(
                    last_story_n.get('classification', 'LOW_CONFIDENCE'),
                    first_story_n1.get('classification', 'LOW_CONFIDENCE')
                )

                last_story_n['classification'] = merged_cls
                last_story_n['spans_pages'] = [ref_n, ref_n1]
                last_story_n['start_segment_page2'] = 0  # override: include seg 0
                last_story_n['end_segment_page2'] = first_story_n1.get('end_segment')
                last_story_n['cross_page_merge_v7'] = True
                last_story_n['first_segment_skip_fix'] = True

                summary_n = last_story_n.get('one_sentence_summary', '')
                summary_n1 = first_story_n1.get('one_sentence_summary', '')
                if summary_n and summary_n1:
                    last_story_n['one_sentence_summary'] = f"{summary_n} {summary_n1}"
                elif summary_n1:
                    last_story_n['one_sentence_summary'] = summary_n1

                stories_n1.pop(0)
                page_n1['stories'] = stories_n1

                print(f"  Cross-page merge (v7) [seg0 fix]: {ref_n} → {ref_n1} "
                      f"({merged_cls}) [both flag continuation, page2 started at seg 1]")
                continue

    return pages


# ============================================================
# CROSS-PAGE MERGING (from v6, adapted for v7)
# ============================================================

def merge_cross_page_stories(pages: List[Dict]) -> List[Dict]:
    """
    Merge stories that span page boundaries.
    Merge if at least one side has a continuation flag (relaxed from requiring both).
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

        # Fix A: Skip if already merged by a previous pass (e.g. 4b)
        if last_story.get('spans_pages'):
            continue

        last_cont = last_story.get('continuation', {})
        first_cont = first_story.get('continuation', {})

        if (last_cont.get('continues_to_next_page') or
            first_cont.get('continues_from_previous_page')):

            # Both sides agree there's a continuation
            if last_story.get('classification') == 'NOT_A_STORY':
                continue
            if first_story.get('classification') == 'NOT_A_STORY':
                continue

            # Fix B: If first story on N+1 starts at seg >= 1, there's likely
            # a gap of undetected continuation text. Defer to stitch pass (4d).
            if first_story.get('start_segment', 0) >= 1:
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


# Hebrew story introducer markers — used to override triage skip (Wave 1 Issue #5).
# Match on the unvocalized consonantal skeleton (Sefaria adds nikud which would
# otherwise prevent literal substring matches). Spaces between letters are
# expected in the source text.
_STRIP_NIKUD_RE = re.compile(r'[\u0591-\u05C7]')


def _strip_nikud(s: str) -> str:
    """Remove Hebrew vowel/cantillation marks for substring matching."""
    return _STRIP_NIKUD_RE.sub('', s)


# Canonical introducers in consonantal form. These all reliably introduce stories.
_STORY_INTRODUCERS = (
    'מעשה ב',         # "An incident with…"
    'הנהו בי תרי',    # "Those two…"
    'ההוא ד',         # "A certain one who…"
    'ההוא גברא',      # "A certain man"
    'כי הא ד',        # "Like this one who…" / "as in the case where…"
)


def _page_has_story_introducer(page: Dict) -> bool:
    """
    Wave 1 Issue #5: detect canonical story introducers in a page's Hebrew text.
    Used as a recall safety net when Stage 1 triage marks the page skip-able.
    """
    for seg in page.get('segments', []):
        heb = _strip_nikud(seg.get('hebrew', ''))
        if any(marker in heb for marker in _STORY_INTRODUCERS):
            return True
    return False


def _tag_mishnah_segments(segments: List[Dict]) -> Dict[int, bool]:
    """
    Wave 1 Issue #7: tag which segments are in Mishnah vs Gemara.

    Detection uses Sefaria's HTML markers: `<big><strong>מַתְנִי׳</strong></big>`
    starts a Mishnah block, `<big><strong>גְּמָ׳</strong></big>` starts Gemara.
    A page may begin mid-Mishnah (continuation from previous page) — detected
    by the first marker on the page being גְּמָ׳ rather than מַתְנִי׳.

    Returns dict: segment_index -> is_mishnah (bool).
    """
    if not segments:
        return {}

    # Nikud byte order in Sefaria differs from naive literals, so match against
    # the unvocalized consonantal skeleton.
    GEMARA = 'גמ׳'
    MISHNAH = 'מתני׳'

    # Find first marker to determine initial state
    first_marker = None
    for seg in segments:
        heb = _strip_nikud(seg.get('hebrew', ''))
        if GEMARA in heb:
            first_marker = 'gemara'
            break
        if MISHNAH in heb:
            first_marker = 'mishnah'
            break

    # If first marker is גמ׳, the page started in mishnah (continuation).
    # If first marker is מתני׳, segments before it are gemara. Default: gemara.
    in_mishnah = (first_marker == 'gemara')

    result = {}
    for seg in segments:
        heb = _strip_nikud(seg.get('hebrew', ''))
        if MISHNAH in heb:
            in_mishnah = True
        elif GEMARA in heb:
            in_mishnah = False
        result[seg.get('index', -1)] = in_mishnah
    return result


def filter_mishnah_only_stories(pages: List[Dict]) -> int:
    """
    Wave 1 Issue #7: move stories that are entirely within a Mishnah block
    out of the main `stories` list and into `mishnah_stories`. These should
    be tallied separately, not as Talmud (Gemara) stories.

    Returns count of stories filtered.
    """
    moved = 0
    for page in pages:
        segments = page.get('segments', [])
        if not segments:
            continue
        is_mishnah_by_index = _tag_mishnah_segments(segments)
        kept = []
        mishnah = page.setdefault('mishnah_stories', [])
        for story in page.get('stories', []):
            if story.get('classification') == 'NOT_A_STORY':
                kept.append(story)
                continue
            start = story.get('start_segment', 0)
            end = story.get('end_segment', start)
            indices = list(range(start, end + 1))
            # Only filter if every segment in the story lies in Mishnah
            if indices and all(is_mishnah_by_index.get(i, False) for i in indices):
                story['filtered_as_mishnah'] = True
                mishnah.append(story)
                moved += 1
            else:
                kept.append(story)
        page['stories'] = kept
    return moved


# ============================================================
# WAVE 2 POST-PROCESSORS — deterministic, no model calls
# ============================================================

# Issue #3 (Wave 2). Story introducers (consonantal forms, no nikud).
# Order matters: longer prefixes first so substring search picks them up.
_START_INTRODUCERS = (
    'מעשה ב',         # "An incident with…"
    'הנהו בי תרי',    # "Those two…"
    'הנהו תרי',       # variant
    'ההוא גברא',      # "A certain man"
    'ההוא ד',         # "A certain one who…"
    'ההיא',           # "That [feminine]…" (used for ההיא איתתא)
    'כי הא ד',        # "Like this one who…"
    'כדתניא',         # "As it was taught"
    'תניא',           # "It was taught" (baraita)
)


def _segment_starts_with_introducer(seg_hebrew: str) -> bool:
    """True if the segment's Hebrew text starts with a canonical introducer
    (after stripping nikud and leading punctuation/whitespace)."""
    if not seg_hebrew:
        return False
    txt = _strip_nikud(seg_hebrew).lstrip(' :,.!?"\u201c\u201d״׳')
    return any(txt.startswith(m) for m in _START_INTRODUCERS)


def _segment_contains_introducer(seg_hebrew: str) -> bool:
    """True if the segment contains an introducer anywhere (loose check)."""
    if not seg_hebrew:
        return False
    txt = _strip_nikud(seg_hebrew)
    return any(m in txt for m in _START_INTRODUCERS)


def snap_start_to_introducer(pages: List[Dict]) -> int:
    """
    Wave 2 Issue #3: snap story start to canonical introducer segment.

    For each multi-segment real story:
      1. If a segment in [start+1 .. start+3] STARTS WITH an introducer,
         snap start to that segment (skip preceding halakhic framing).
      2. If the segment immediately BEFORE start (start-1) starts with an
         introducer, extend start back to include it (missed preamble).

    Single-segment stories are not modified — their boundary issues are
    text-internal and require Hebrew-text trimming (out of scope).

    Returns count of stories modified.
    """
    modified = 0
    for page in pages:
        segments = page.get('segments', [])
        seg_by_idx = {s.get('index', i): s for i, s in enumerate(segments)}
        for story in page.get('stories', []):
            if story.get('classification') == 'NOT_A_STORY':
                continue
            start = story.get('start_segment')
            end = story.get('end_segment')
            if start is None or end is None or end <= start:
                continue  # skip single-segment

            # (1) snap forward within the first few segments
            new_start = None
            for cand in range(start + 1, min(end, start + 4)):
                seg = seg_by_idx.get(cand)
                if seg and _segment_starts_with_introducer(seg.get('hebrew', '')):
                    new_start = cand
                    break

            # (2) extend back if introducer is in segment immediately before
            extend = False
            if new_start is None and start > 0:
                prev = seg_by_idx.get(start - 1)
                if prev and _segment_starts_with_introducer(prev.get('hebrew', '')):
                    new_start = start - 1
                    extend = True

            if new_start is not None and new_start != start:
                story['start_segment_pre_snap'] = start
                story['start_segment'] = new_start
                story['start_snap_kind'] = 'extend_back' if extend else 'snap_forward'
                modified += 1
    return modified


# Issue #4 (Wave 2). Stam-Talmud / dialectical markers that signal the
# voice has shifted from narrative to anonymous commentary. A trailing
# segment is trimmable only if it opens with one of these.
_TRAILING_MARKERS = (
    'שמע מינה',       # "infer from this"
    'מאי טעמא',       # "what is the reason"
    'אי הכי',         # "if so"
    'הכי קאמר',       # "this is what he means"
    'שאני',           # "it is different"
    'תא שמע',         # "come and hear" (objection introducer)
    'איתיביה',        # "they raised an objection"
    'מיתיבי',         # variant
    'אלא',            # "rather"
    'ואי',            # "and if"
    'מתקיף',          # "X challenges"
    'תניא נמי הכי',   # "this too was taught"
    'תנו רבנן',       # "the Sages taught" (often shifts to new baraita)
)


def _segment_starts_with_trailing_marker(seg_hebrew: str) -> bool:
    if not seg_hebrew:
        return False
    txt = _strip_nikud(seg_hebrew).lstrip(' :,.!?"\u201c\u201d״׳')
    return any(txt.startswith(m) for m in _TRAILING_MARKERS)


def trim_trailing_stam_segments(pages: List[Dict]) -> int:
    """
    Wave 2 Issue #4: trim trailing dialectical segments from a story.

    For each multi-segment real story, walk from the end inward. Drop the
    last segment if it opens with a stam-Talmud marker, as long as at
    least 2 segments would remain (we never reduce to a single segment
    via trim; that would be aggressive and risks deletion of real story
    body).

    Single-segment stories are untouched (their boundary issues are
    text-internal — out of scope for a segment-level trim).

    Returns count of stories modified.
    """
    modified = 0
    for page in pages:
        segments = page.get('segments', [])
        seg_by_idx = {s.get('index', i): s for i, s in enumerate(segments)}
        for story in page.get('stories', []):
            if story.get('classification') == 'NOT_A_STORY':
                continue
            start = story.get('start_segment')
            end = story.get('end_segment')
            if start is None or end is None or end <= start:
                continue

            orig_end = end
            cur_end = end
            while cur_end > start + 1:
                seg = seg_by_idx.get(cur_end)
                if seg and _segment_starts_with_trailing_marker(seg.get('hebrew', '')):
                    cur_end -= 1
                else:
                    break

            if cur_end != orig_end:
                story['end_segment_pre_trim'] = orig_end
                story['end_segment'] = cur_end
                story['end_trim_segments_removed'] = orig_end - cur_end
                modified += 1
    return modified


# Issue #6(b) (Wave 2). Biblical-actor names that signal a story is a
# biblical narrative, not a rabbinic one. We compare against the
# `criteria.identifiable_characters.evidence` field, which the Stage 2
# prompt populates with a short comma-separated list of named actors.

# Surface form is checked case-insensitively as a substring of `evidence`.
_BIBLICAL_ACTORS = frozenset({
    # Patriarchs and matriarchs
    'adam', 'eve', 'noah', 'abraham', 'sarah', 'isaac', 'rebecca',
    'jacob', 'leah', 'rachel', 'joseph', 'benjamin',
    # Exodus / wilderness
    'moses', 'aaron', 'miriam', 'pharaoh', 'jethro', 'tzipporah',
    # Conquest and judges
    'joshua', 'caleb', 'gideon', 'samson', 'deborah', 'barak',
    'samuel', 'eli',
    # United monarchy and prophets
    'saul', 'david', 'solomon', 'jonathan', 'bathsheba', 'nathan',
    'absalom', 'goliath',
    # Divided kingdoms and later kings
    'rehoboam', 'jeroboam', 'ahab', 'jezebel', 'hezekiah', 'manasseh',
    'josiah', 'ahaz', 'jehu', 'uzziah', 'amaziah',
    # Latter prophets
    'elijah', 'elisha', 'isaiah', 'jeremiah', 'ezekiel', 'hosea',
    'amos', 'obadiah', 'jonah', 'micah', 'nahum', 'habakkuk',
    'zephaniah', 'haggai', 'zechariah', 'malachi',
    # Exile / return / late biblical
    'daniel', 'esther', 'mordechai', 'mordecai', 'haman', 'ahasuerus',
    'nebuchadnezzar', 'sennacherib', 'cyrus', 'darius', 'ezra',
    'nehemiah', 'pelatiah',
    # Collective biblical actors
    'jewish people', 'children of israel', 'israelites',
    'people of israel',
})

# A handful of common rabbinic actor names; if any appear, the story is
# NOT biblical-only.
_RABBINIC_SIGNAL = (
    'rabbi ', 'rav ', 'rabban ', 'reish lakish', 'resh lakish',
    'mar ', 'abaye', 'rava', 'shmuel', 'samuel',  # 'samuel' overlaps
    'hillel', 'shammai', 'akiva', 'akiba', 'meir', 'judah hanasi',
    'yehuda hanasi', 'tanna', 'amora',
)


def _actors_are_biblical_only(evidence: str) -> bool:
    """True if the actor evidence string names ONLY biblical figures."""
    if not evidence:
        return False
    low = evidence.lower()

    # Quick reject: if any rabbinic signal is present, not biblical-only.
    # "Samuel" alone is ambiguous (prophet vs amora). Treat as biblical
    # unless explicitly "Rav Samuel" / "Rabbi Samuel".
    if any(sig in low for sig in _RABBINIC_SIGNAL):
        # 'samuel' in _RABBINIC_SIGNAL — guard
        # Only count as rabbinic if the rabbi prefix is present, not bare
        # mentions of an ambiguous name.
        rabbinic_strong = any(s in low for s in [
            'rabbi ', 'rav ', 'rabban ', 'reish lakish', 'resh lakish',
            'mar ', 'abaye', 'rava ', 'rava\n', 'hillel', 'shammai',
            'akiva', 'akiba', 'rabbi meir', 'judah hanasi', 'yehuda hanasi',
            'tanna', 'amora',
        ])
        if rabbinic_strong:
            return False

    # Hit if any biblical name is mentioned.
    has_biblical = any(name in low for name in _BIBLICAL_ACTORS)
    if not has_biblical:
        return False

    # Additional check: tokenize by commas/and and see whether ANY token
    # contains no biblical name and is not a generic descriptor.
    parts = re.split(r'[,;]| and ', low)
    generic_descriptors = (
        'collective character', 'character', 'narrator',
        'agent', 'agents', 'man', 'woman', 'child', 'children',
    )
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if any(name in p for name in _BIBLICAL_ACTORS):
            continue
        if any(g in p for g in generic_descriptors):
            continue
        # An actor token with no biblical name and not a generic descriptor
        # → likely rabbinic. Reject biblical-only.
        return False
    return True


def filter_biblical_actor_stories(pages: List[Dict]) -> int:
    """
    Wave 2 Issue #6(b): demote stories whose only named actors are biblical
    figures. We want rabbinic stories in the catalog; biblical narratives
    belong elsewhere.

    The actor names are read from `criteria.identifiable_characters.evidence`
    which is a comma-separated string the Stage 2 prompt produces. Stories
    are demoted to NOT_A_STORY (kept in the page record with a flag, so the
    decision is auditable).

    Returns count of stories demoted.
    """
    demoted = 0
    for page in pages:
        for story in page.get('stories', []):
            if story.get('classification') == 'NOT_A_STORY':
                continue
            evidence = (story.get('criteria', {})
                            .get('identifiable_characters', {})
                            .get('evidence', ''))
            if _actors_are_biblical_only(evidence):
                story['filtered_as_biblical'] = True
                story['classification_pre_biblical_filter'] = story.get('classification')
                story['classification'] = 'NOT_A_STORY'
                demoted += 1
    return demoted


# ============================================================
# Wave 3 Item 4: text-internal boundary editing
# ============================================================
#
# Many of Jeff's 2026-04-23 Kiddushin boundary complaints are TEXT-INTERNAL:
# the canonical introducer he wants the story to start at, or the
# stam-Talmud marker he wants trimmed, falls INSIDE the first/last segment
# rather than at a segment boundary. Wave 2's snap_start_to_introducer and
# trim_trailing_stam_segments operate on segment indices, so they cannot
# reach these. Re-segmenting the corpus would invalidate the golden labels
# (Lesson 12).
#
# Item 4 records sub-segment text spans without changing segment indices.
# The score harness reads only start_segment/end_segment, so text_span_*
# is invisible to scoring (review-debt repayment, not score-improvement).
# The validation UI reads these fields to render the trimmed text.


def _strip_nikud_with_map(s: str):
    """Return (stripped_text, idx_map). stripped[i] = s[idx_map[i]].
    idx_map has one extra entry mapping len(stripped) → len(s)."""
    stripped = []
    idx_map = []
    for i, ch in enumerate(s):
        if not _STRIP_NIKUD_RE.match(ch):
            stripped.append(ch)
            idx_map.append(i)
    idx_map.append(len(s))
    return ''.join(stripped), idx_map


# Token boundary chars: anything that's not a Hebrew letter.
_HEBREW_LETTER_RE = re.compile(r'[\u05D0-\u05EA]')


def _has_word_boundary_before(stripped: str, pos: int) -> bool:
    """True if char before pos is start-of-string or non-Hebrew-letter."""
    if pos == 0:
        return True
    return not _HEBREW_LETTER_RE.match(stripped[pos - 1])


def _has_word_boundary_after(stripped: str, pos: int) -> bool:
    """True if char at pos is end-of-string or non-Hebrew-letter."""
    if pos >= len(stripped):
        return True
    return not _HEBREW_LETTER_RE.match(stripped[pos])


def _find_first_introducer(stripped: str):
    """Earliest introducer occurrence at a word-start boundary.

    Introducers like 'מעשה ב' end with the prefix-letter ב which attaches
    to the following word, so we do NOT require an end-word-boundary. We
    only require the introducer's first letter to start a new word.
    """
    best_pos = None
    best_intro = None
    for intro in _START_INTRODUCERS:
        for m in re.finditer(re.escape(intro), stripped):
            pos = m.start()
            if pos == 0:
                continue  # already at segment start — nothing to snap
            if not _has_word_boundary_before(stripped, pos):
                continue
            if best_pos is None or pos < best_pos:
                best_pos = pos
                best_intro = intro
            break
    return best_pos, best_intro


def _find_last_trailing_marker(stripped: str, lower_bound: int = 0):
    """Latest trailing-marker occurrence at a full-word boundary, strictly
    after lower_bound. Stam markers are discrete words/phrases, so we
    require BOTH leading and trailing word boundaries to avoid matching
    'ואי' inside 'ואיקפד'.
    """
    best_pos = None
    best_marker = None
    for marker in _TRAILING_MARKERS:
        for m in re.finditer(re.escape(marker), stripped):
            pos = m.start()
            if pos <= lower_bound:
                continue
            if not _has_word_boundary_before(stripped, pos):
                continue
            if not _has_word_boundary_after(stripped, pos + len(marker)):
                continue
            if best_pos is None or pos > best_pos:
                best_pos = pos
                best_marker = marker
    return best_pos, best_marker


def _apply_regex_text_span_to_story(story: Dict,
                                     seg_by_idx: Dict[int, Dict]) -> bool:
    """Per-story regex text-span pass (Wave 3 Item 4 logic, extracted).
    Returns True if any text_span_* field was set.
    """
    start = story.get('start_segment')
    end = story.get('end_segment')
    if start is None or end is None:
        return False

    edited = False
    end_search_lower_bound = 0  # in stripped coords

    seg = seg_by_idx.get(start)
    if seg:
        orig = seg.get('hebrew', '') or ''
        stripped, idx_map = _strip_nikud_with_map(orig)
        pos, intro = _find_first_introducer(stripped)
        if pos is not None:
            story['text_span_start'] = {
                'segment': start,
                'char_offset': idx_map[pos],
                'introducer': intro,
                'source': 'regex',
            }
            edited = True
            if start == end:
                end_search_lower_bound = pos

    seg = seg_by_idx.get(end)
    if seg:
        orig = seg.get('hebrew', '') or ''
        stripped, idx_map = _strip_nikud_with_map(orig)
        pos, marker = _find_last_trailing_marker(
            stripped, end_search_lower_bound)
        if pos is not None:
            story['text_span_end'] = {
                'segment': end,
                'char_offset': idx_map[pos],
                'marker': marker,
                'source': 'regex',
            }
            edited = True

    return edited


def edit_text_internal_boundaries(pages: List[Dict]) -> int:
    """
    Wave 3 Item 4: record sub-segment text spans when the canonical Hebrew
    introducer or trailing-stam marker falls mid-segment.

    Wave 4 keeps this function as the regex-only path for tests/comparison.
    The production pipeline (v10) calls extract_text_spans_via_llm instead,
    which falls back to _apply_regex_text_span_to_story per story.

    Returns count of stories with at least one text-span field.
    """
    modified = 0
    for page in pages:
        segments = page.get('segments', [])
        seg_by_idx = {s.get('index', i): s for i, s in enumerate(segments)}
        for story in page.get('stories', []):
            if story.get('classification') == 'NOT_A_STORY':
                continue
            if _apply_regex_text_span_to_story(story, seg_by_idx):
                modified += 1
    return modified


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
