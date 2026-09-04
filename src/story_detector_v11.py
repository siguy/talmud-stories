#!/usr/bin/env python3
"""
Talmud Story Detection v10: v9 baseline + Wave 4 LLM-side text-span emission.

v10 = v9 (Wave 1+2+3) PLUS:
  - Wave 5 (v11): CLAUSE SELECTION replaces character offsets.
    The model never emits a number. It picks a punctuation-delimited
    clause index; we compute the offset from the real text. A mid-word
    cut is therefore structurally impossible (Lesson 16).
  - Wave 4 (v10, superseded): extract_text_spans_via_llm asked for char offsets;
    audit found 55% of cuts severed a word. See
    docs/findings/2026-08-28-wave4-span-failure-audit.md
  - Wave 4: extract_text_spans_via_llm replaces edit_text_internal_boundaries
    (regex) as the production pipeline path. Per-story Gemini call emits
    {start_offset, end_offset}. Regex retained only as fallback on LLM
    error. See docs/history/2026-06-15-PLAN-wave4.md.

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

from src.model_config import default_model
import re
import time
import warnings
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


def validate_story_spans(ref: str, stories: List[Dict], n_segments: int):
    """
    Every proposed span must lie inside its page. Returns `(kept, repairs)`.

    THE DEFECT this closes. Stage 2 proposed `Ketubot 112b, start_segment -2,
    end_segment 0` and nothing checked it. Python does not raise on a negative
    index — every Stage 4 post-processor slices `segments[start:end + 1]`, so
    `-2` silently means the second segment from the END of the page. The story
    is then built, snapped, trimmed and displayed from the wrong text, with no
    error anywhere. The one we caught sat on a triage-discarded page, so it
    reached no published number; that is luck, not a property of the code.

    Two rules, and the second matters as much as the first:

    - **Clamp what overlaps the page, drop what does not.** A span running from
      -2 to 0 is a real proposal with a wrong start; a span at 12..15 on a
      10-segment page is not about this page at all, and a non-integer one has
      no anchor to keep.
    - **Where one end survives, keep the proposal and refuse to invent the
      other.** `Ketubot 22a` proposes `10..0` on an 11-segment page: the start
      is real, the end is unusable, and the summary describes a genuine story.
      Deleting it would spend a Detection miss — the expensive kind — to avoid a
      Boundaries error. So it becomes `10..10`, the smallest claim consistent
      with the half the model got right, and the story is stamped
      `needs_review` so no downstream number reads that extent as a judgment
      (Lesson 21).
    - **Count and name every repair.** Returned in `repairs`, stamped on the
      story as `span_repair`, and accumulated on the detector so the run output
      carries it. A silent clamp turns a model defect into a boundary defect
      that scores as ours — and an unreported drop is Lesson 38's shape, where
      an `isinstance` guard swallowed a 25-verdict expert round for eight months.
    """
    kept, repairs = [], []
    last = n_segments - 1
    for story in stories:
        a, b = story.get('start_segment'), story.get('end_segment')

        def drop(reason):
            repairs.append({'ref': ref, 'action': 'dropped', 'reason': reason,
                            'original': [a, b]})

        # bool is an int in Python; a True start is a defect, not segment 1.
        if any(isinstance(v, bool) or not isinstance(v, int) for v in (a, b)):
            drop('span is not a pair of integers')
            continue
        if b < a:
            if 0 <= a <= last:
                repairs.append({'ref': ref, 'action': 'clamped',
                                'reason': 'end_segment before start_segment; '
                                          'collapsed to the start segment',
                                'original': [a, b], 'repaired': [a, a]})
                story['end_segment'] = a
                story['span_repair'] = {'original': [a, b], 'repaired': [a, a]}
                story['needs_review'] = True
                kept.append(story)
            else:
                drop('end_segment before start_segment, and start is off the page')
            continue
        lo, hi = max(a, 0), min(b, last)
        if n_segments <= 0 or hi < lo:
            drop(f'span lies outside the page (0..{last})')
            continue
        if (lo, hi) != (a, b):
            repairs.append({'ref': ref, 'action': 'clamped',
                            'reason': f'span clamped into the page (0..{last})',
                            'original': [a, b], 'repaired': [lo, hi]})
            story['start_segment'], story['end_segment'] = lo, hi
            story['span_repair'] = {'original': [a, b], 'repaired': [lo, hi]}
        kept.append(story)
    return kept, repairs


class V7StoryDetector:
    """
    v7 story detection with event-annotated constrained prompt.
    Uses Ground Truth DB for few-shot examples.
    """

    def __init__(self, api_key: Optional[str] = None,
                 ground_truth_db: Optional[GroundTruthDB] = None,
                 model_name: Optional[str] = None,
                 thinking_level: Optional[str] = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.model_name = model_name or default_model()
        # Wave 5: newer Gemini (3.x) exposes thinking_level; older flash models
        # need thinking disabled for structured output. Recorded per run so
        # results stay attributable (roadmap 5.3: pin and record model versions).
        self.thinking_level = thinking_level or os.getenv("GEMINI_THINKING_LEVEL")
        self.ground_truth_db = ground_truth_db
        # Every span repair Stage 2 needed, across the run. Written to the output
        # so a malformed proposal is a number someone can see, not a silence.
        self.span_repairs: List[Dict] = []

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
- Habitual action (היה רגיל) with NOTHING further — a standing practice, and then the
  passage moves on. But a custom is often the FRAME of a story rather than a
  disqualifier: if the habitual opening is followed by a single datable occurrence
  ("one day…", "מַעֲשֶׂה…", a named person doing something once), that is a STORY and
  the story STARTS at the custom. Jeff Rubenstein, 2026-09-01, on Gittin 57a: "clearly
  a story. After the custom you have the one time event — One day the emperor's
  daughter…" Do not stop reading at the frame.
- Pure legal ruling without narrative
- Rabbi stating legal opinion (not acting in narrative)
- Legal deliberation (thinking, considering, difficulty resolving)
- Legal debate with setting (sitting before another = just a debate)
- A legal debate between academies (place names ≠ characters)
- A passage whose entire activity is verbal exchange (אֲמַר לוֹ … אֲמַר לוֹ)
  with NO physical action. Speech alone is not a story — UNLESS a story is quoted
  INSIDE the speech. A dictum can contain one: Gittin 38b is a saying of Rabba, and
  inside it R. Yoḥanan reports two families who set their meals at the wrong times and
  were uprooted — two actions with a causal connection, which Jeff (2026-09-01) counts
  as a story. Judge what the speech CONTAINS, not only what the passage is.
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
                elif self.thinking_level and _supports_thinking_level(self.model_name):
                    # Gemini 3.x flash: thinking_level works alongside JSON output.
                    # Thinking tokens are drawn from max_output_tokens, so the
                    # budget MUST be raised or the model spends it all thinking
                    # and returns MAX_TOKENS with no JSON. Measured 2026-08-29:
                    # a 2,042-char clause prompt used 487 thinking tokens against
                    # a 512 budget -> 72 of 95 stories failed. Same fix the Pro
                    # branch above already applies.
                    config_kwargs['thinking_config'] = types.ThinkingConfig(
                        thinking_level=self.thinking_level.upper()
                    )
                    config_kwargs['max_output_tokens'] = max(max_tokens, 8192)
                else:
                    # Older flash models: disable thinking for structured output
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
        "The START segment, split into numbered clauses:\n"
        "{start_clauses}\n\n"
        "The END segment, split into numbered clauses:\n"
        "{end_clauses}\n\n"
        "Choose which clauses the STORY occupies.\n\n"
        "Return start_clause: the index of the FIRST clause of the start "
        "segment that is story content.\n"
        "Return end_clause: the index of the LAST clause of the end segment "
        "that is story content.\n\n"
        "Rules:\n"
        "- DEFAULT TO KEEPING EVERYTHING. Only exclude a clause when it is "
        "  clearly not part of the story. If in any doubt, include it.\n"
        "- Editorial framing BEFORE the story (a stam-Talmud setup line, a "
        "  legal question introducing the case) is not story content.\n"
        "- A stam-Talmud aside AFTER the story body is not story content: "
        "  \"שמע מינה\" (legal inference), \"אי הכי\" (objection), "
        "  \"שאני\" (distinguishing), \"ולאו משום ד... אלא משום ד...\" "
        "  (stam re-explaining the story), or a final \"אלא\" introducing a "
        "  competing stam explanation rather than a character speaking.\n"
        "- Words like \"אלא\" or rabbi names INSIDE the story body (a "
        "  character speaking, a rabbi acting) ARE story content. A rabbi's "
        "  concluding reflection on the events IS the story's closure.\n"
        "- A clause that merely NOTES a parallel practice by a different "
        "  person — a bare \"and so-and-so did the same\", with no events of "
        "  its own — is not part of this story. But when the parallel "
        "  material is itself a FULL INCIDENT — someone DOES something, "
        "  events happen to named people — it is a SECOND STORY, not an "
        "  aside: KEEP IT. Nothing downstream picks it up, so trimming it "
        "  deletes the passage outright, and a boundary that runs long is "
        "  recoverable by a reader while a deleted story is not.\n"
        "- Judge that on EVENTS, never on names or speech. Amoraic debate "
        "  about the story — \"אמר אביי... אמר ליה רב אדא בר מתנא...\", a "
        "  question and its answer, competing rulings — carries names and "
        "  dialogue and is still NOT a second incident. Trim it as usual.\n"
        "- Pick whole clauses only. Never split a clause.\n\n"
        "Return ONLY valid JSON: "
        "{{\"start_clause\": <int>, \"end_clause\": <int>}}"
    )

    def _llm_clause_span_for_story(self, story: Dict,
                                    start_clauses: List[str],
                                    end_clauses: List[str]) -> Optional[Dict]:
        """Single Gemini call. Returns {'start_clause': int, 'end_clause': int}
        as CLAUSE INDICES, or None on any error.

        The model never emits a character position — only an index into a list
        we built from real punctuation. This is the whole point of Wave 5.
        """
        if not self.client:
            return None
        summary = story_summary(story)

        def numbered(clauses):
            return '\n'.join(f'  [{i}] {c}' for i, c in enumerate(clauses))

        prompt = self._TEXT_SPAN_PROMPT_TEMPLATE.format(
            summary=summary,
            start_clauses=numbered(start_clauses),
            end_clauses=numbered(end_clauses),
        )
        try:
            raw = self._call_google(prompt, max_tokens=512, json_mode=True)
        except Exception:
            return None
        parsed = self._parse_json_response(raw)
        if not parsed:
            return None
        try:
            sc = int(parsed.get('start_clause', 0))
            ec = int(parsed.get('end_clause', len(end_clauses) - 1))
        except (TypeError, ValueError):
            return None
        # Clamp into range rather than trusting the model's arithmetic.
        sc = max(0, min(sc, len(start_clauses) - 1))
        ec = max(0, min(ec, len(end_clauses) - 1))
        return {'start_clause': sc, 'end_clause': ec}

    def extract_text_spans_via_clauses(self, pages: List[Dict]) -> Dict[str, int]:
        """
        Wave 5 (v11) replacement for Wave 4's extract_text_spans_via_llm.

        For each non-NOT_A_STORY story, split its first/last segment into
        punctuation-delimited clauses, ask the model WHICH CLAUSE the story
        starts and ends at, and snap the boundary to that clause's real
        position in the text.

        The model never emits a character position. We compute every offset
        from clause ranges we derived from the actual string, so a boundary
        can only ever land where a clause begins or ends — mid-word cuts are
        structurally impossible (Lesson 16, and the audit in
        docs/findings/2026-08-28-wave4-span-failure-audit.md).

        Per-story outcomes (text_span_source):
          - 'clause_llm'       : model selected a narrower clause range.
          - 'clause_kept_full' : model kept the whole segment(s).
          - 'no_clause_split'  : segment has no sentence punctuation, so it is
                                 one clause. Named, logged, never silent.
          - 'skipped'          : LLM error. NO regex fallback (it over-trims —
                                 Jeff 2026-06-03); fail loud.

        Returns counts keyed by those outcomes.
        """
        counts = {'clause_llm': 0, 'clause_kept_full': 0,
                  'no_clause_split': 0, 'skipped': 0}
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
                start_ranges = _split_into_clauses(start_heb)
                end_ranges = _split_into_clauses(end_heb)
                if not start_ranges or not end_ranges:
                    continue

                if len(start_ranges) == 1 and len(end_ranges) == 1:
                    # Nothing to choose between: the segment is one clause.
                    story['text_span_source'] = 'no_clause_split'
                    counts['no_clause_split'] += 1
                    continue

                llm = self._llm_clause_span_for_story(
                    story,
                    [_clause_text_for_display(start_heb, r) for r in start_ranges],
                    [_clause_text_for_display(end_heb, r) for r in end_ranges],
                )
                if llm is None:
                    print(f"  WARN clause-span LLM error on {page.get('ref', '?')} "
                          f"story {start}-{end}: leaving spans absent")
                    story['text_span_source'] = 'skipped'
                    counts['skipped'] += 1
                    continue

                sc, ec = llm['start_clause'], llm['end_clause']
                if start == end and ec < sc:
                    ec = len(end_ranges) - 1   # incoherent range -> keep full

                emitted = False
                if sc > 0:
                    offset = start_ranges[sc][0]
                    _assert_word_boundary(start_heb, offset, page.get('ref', '?'),
                                          start, 'start')
                    story['text_span_start'] = {
                        'segment': start,
                        'char_offset': offset,
                        'clause_index': sc,
                        'clause_count': len(start_ranges),
                        'source': 'clause_llm',
                    }
                    emitted = True
                # NOTE: an end-trim depth cap was tried on 2026-08-30 and
                # REVERTED once Simon settled which expert standard we build
                # for. It scored better only against Jeff's 2005 story INDEX,
                # which keeps the legal discussion after a story. We build for
                # his 2026 tool reviews, which say to cut it — and against
                # that standard the cap undoes the trims that remove real
                # overshoots (ends running past even the 2005 outer limit go
                # 10 -> 16 of 105). See docs/findings/2026-08-30-trim-asymmetry.md
                if ec < len(end_ranges) - 1:
                    offset = end_ranges[ec][1]
                    _assert_word_boundary(end_heb, offset, page.get('ref', '?'),
                                          end, 'end')
                    story['text_span_end'] = {
                        'segment': end,
                        'char_offset': offset,
                        'clause_index': ec,
                        'clause_count': len(end_ranges),
                        'source': 'clause_llm',
                    }
                    emitted = True

                if emitted:
                    story['text_span_source'] = 'clause_llm'
                    counts['clause_llm'] += 1
                else:
                    story['text_span_source'] = 'clause_kept_full'
                    counts['clause_kept_full'] += 1
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

        # Bounds check, both passes. Runs here rather than in run_pipeline so the
        # one other caller of this method — scripts/run_triage_recall_price.py,
        # which is where the Ketubot 112b span was found — is covered too.
        stories, repairs = validate_story_spans(ref, stories, len(segments))
        for r in repairs:
            print(f"    Span {r['action']}: {ref} "
                  f"{r['original'][0]}-{r['original'][1]} — {r['reason']}")
        if repairs:
            self.span_repairs = getattr(self, 'span_repairs', []) + repairs

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
                     examine_all_pages: bool = False,
                     enable_adversarial: bool = False,
                     tractate: str = 'Ketubot',
                     skip_triage: Optional[bool] = None) -> Dict:
        """
        Full v7 pipeline: triage → detect → (adversarial) → (boundary refine)

        Args:
            pages: List of page dicts with 'ref' and 'segments'
            triage_results: Pre-computed triage results (or None to compute)
            delay: Delay between API calls
            examine_all_pages: If True, run Stage 2 on every page — overriding Stage 1's
                skip verdict and ONLY that. The labels are still real.
            tractate: Tractate name for output metadata
            skip_triage: deprecated spelling of `examine_all_pages`
        """
        if skip_triage is not None:
            if examine_all_pages:
                raise TypeError(
                    'pass either examine_all_pages or skip_triage, not both — they are '
                    'the same argument and skip_triage is the deprecated spelling')
            warnings.warn(
                'skip_triage is deprecated and misnamed; use examine_all_pages. It never '
                'skipped Stage 1 — until 2026-09-01 it replaced Stage 1 output with '
                'all-DELIBERATION, a verdict Stage 2, the cross-page context, boundary '
                'refinement and post-processing all believed. See '
                'docs/findings/2026-09-01-contaminated-no-triage-ablation.md',
                DeprecationWarning, stacklevel=2)
            examine_all_pages = skip_triage

        # Stage 1: Event Triage.
        #
        # Runs whenever labels were not supplied — INCLUDING under examine_all_pages.
        # The flag decides which pages Stage 2 reads, and nothing else: Stage 1 is the
        # cheap stage, so there was never a saving in skipping the labelling, and the
        # labels are an input to how every examined page is read. Fabricating them is
        # what made results/v7/ablation_v7_no_triage.json unreadable — Stage 2's prompt
        # renders the label per segment, and rule3_v6_ensemble demotes on it, so an
        # invented DELIBERATION tells the model and the post-processor that nothing
        # happens on a page nobody looked at (EventType.TRIAGE_FAILED's docstring one
        # caller over; Lesson 21).
        if triage_results is None:
            print("\n--- Stage 1: Event Triage ---")
            triager = EventTriager(
                api_key=self.api_key,
                ground_truth_db=self.ground_truth_db,
                model_name=self.model_name,
            )
            triage_results = triager.triage_all_pages(pages, delay=delay)

        # Determine which pages to process
        pages_to_process = []
        skipped_pages = []
        for page in pages:
            ref = page.get('ref', '')
            events = triage_results.get(ref, [])
            # Wave 1 Issue #5: lexical override — if the page contains a canonical
            # story introducer (מַעֲשֶׂה ב…, הָנְהוּ בֵּי תְרֵי, הַהוּא ד…,
            # כִּי הָא ד…), force Stage 2 to run regardless of triage skip.
            if examine_all_pages or not EventTriager.should_skip_page(events) \
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
            # A page with no triage entry is UNKNOWN, not deliberative. `[]` renders as
            # "[UNKNOWN] Seg N" in the prompt (build_prompt's own fallback) and matches
            # what the cross-page context blocks below already do; the old
            # all-DELIBERATION default was the same fabrication as the removed stub, one
            # page at a time.
            events = triage_results.get(ref, [])

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

        # 4k (Wave 5): clause selection. The model picks a clause index and we
        # compute the offset, so a mid-word cut is structurally impossible.
        # No regex fallback on LLM error — see the method's docstring.
        #
        # This called `extract_text_spans_via_llm` until 2026-08-31 — Wave 4's
        # char-offset mechanism, which v11 does not have (removed when Wave 5
        # replaced it, per this module's docstring). With a client attached the
        # pipeline raised AttributeError here, after the whole Stage 1/2/4 spend.
        # Nothing caught it because v11 had only ever been driven by
        # run_wave5_clause_spans.py, which calls the method directly.
        span_counts = {'clause_llm': 0, 'clause_kept_full': 0,
                       'no_clause_split': 0, 'skipped': 0}
        if self.client:
            span_counts = self.extract_text_spans_via_clauses(all_results)
            print(
                "  Text-span (Wave 5 clause selection): "
                f"llm={span_counts['clause_llm']} "
                f"kept_full={span_counts['clause_kept_full']} "
                f"no_split={span_counts['no_clause_split']} "
                f"skipped={span_counts['skipped']}"
            )
        else:
            # No API client (e.g. offline tests) — pure regex pass.
            text_edited = edit_text_internal_boundaries(all_results)
            print(
                "  Text-span (regex-only, no client): "
                f"{text_edited} stories got sub-segment spans"
            )

        # 4l (2026-09-02): the story starts at the formula that introduces it.
        # Runs AFTER the spans exist, because it moves a clause index, not a segment.
        formula = extend_start_over_opening_formula(all_results)
        if formula['extended']:
            print(f"  Opening formula: {formula['extended']} starts extended over "
                  f"the formula that introduces them")

        # Detect duplicates
        all_results = detect_duplicate_stories(all_results)

        repairs = getattr(self, 'span_repairs', [])
        if repairs:
            clamped = sum(1 for r in repairs if r['action'] == 'clamped')
            print(f"  Span validation: {clamped} clamped, "
                  f"{len(repairs) - clamped} dropped — see `span_repairs`")

        return {
            'tractate': tractate,
            'version': 'v10',
            'pages': all_results,
            'triage_summary': EventTriager.summarize_triage(triage_results),
            'span_stats': span_counts,
            'opening_formula': formula,
            # Always written, including as `[]`. A key that appears only when
            # something went wrong reads as absence of the check itself.
            'span_repairs': repairs,
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
        self.model_name = model_name or default_model()
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


# Sefaria wraps every structural transition in `<big><strong>…</strong></big>`.
# Measured over the 384 fetched Ketubot/Kiddushin pages, exactly four kinds occur
# (and all four ONLY ever occur inside that markup — 0 bare occurrences):
#   מתני׳             a Mishnah block opens
#   גמ׳               the Gemara on it opens
#   הדרן עלך …       the chapter-end formula
#   the chapter name  a new chapter's FIRST Mishnah — Sefaria opens it with the
#                     chapter incipit INSTEAD of מתני׳ (e.g. אף על פי, Ketubot 54b seg 5)
_BIG_MARKER_RE = re.compile(r'<big>\s*<strong>(.*?)</strong>\s*</big>', re.DOTALL)

# Nikud byte order in Sefaria differs from naive literals, so match against
# the unvocalized consonantal skeleton.
_GEMARA = 'גמ׳'
_MISHNAH = 'מתני׳'
_HADRAN = 'הדרן'


def _segment_structural_marker(seg: Dict) -> Optional[str]:
    """
    Classify a segment's structural marker, or None if it carries none.

    Returns 'mishnah' | 'gemara' | 'chapter_end' | 'chapter_start'.

    The chapter incipit is only identifiable by its markup — it is the chapter's
    name, not a fixed formula — so the `<big><strong>` layer is read first. The
    bare-substring check afterwards preserves the pre-fix behaviour for מתני׳ and
    גמ׳ on any page whose markup differs from the corpus we measured.
    """
    heb = seg.get('hebrew', '')

    for raw in _BIG_MARKER_RE.findall(heb):
        marker = _strip_nikud(re.sub(r'<[^>]+>', '', raw)).strip()
        if _MISHNAH in marker:
            return 'mishnah'
        if _GEMARA in marker:
            return 'gemara'
        if _HADRAN in marker:
            return 'chapter_end'
        if marker:
            return 'chapter_start'

    plain = _strip_nikud(heb)
    if _MISHNAH in plain:
        return 'mishnah'
    if _GEMARA in plain:
        return 'gemara'
    return None


def _tag_mishnah_segments(segments: List[Dict]) -> Dict[int, bool]:
    """
    Wave 1 Issue #7: tag which segments are in Mishnah vs Gemara.

    Walks the page's structural markers (see `_segment_structural_marker`) as a
    state machine. A page may legitimately begin mid-Mishnah — the Mishnah opened
    on the previous page and the גמ׳ closing it is the page's first marker.

    That continuation rule used to read only מתני׳ and גמ׳, which made it misfire
    at every chapter boundary: the new chapter's opening Mishnah is marked with
    the chapter incipit rather than מתני׳, so גמ׳ looked like the page's first
    marker and everything before it — the PREVIOUS chapter's Gemara tail and the
    הדרן formula — was back-tagged as Mishnah. That silently fed
    `filter_mishnah_only_stories()` plain Gemara (e.g. Ketubot 95b seg 0,
    54b segs 1-3, both accepted stories in the golden). Reading all four markers
    fixes it: a chapter_end or chapter_start seen first means the page opened in
    Gemara, not Mishnah.

    Returns dict: segment_index -> is_mishnah (bool).
    """
    if not segments:
        return {}

    marked = [(seg, _segment_structural_marker(seg)) for seg in segments]

    first_marker = next((m for _, m in marked if m is not None), None)
    in_mishnah = (first_marker == 'gemara')

    result = {}
    for seg, marker in marked:
        if marker in ('mishnah', 'chapter_start'):
            in_mishnah = True
        elif marker in ('gemara', 'chapter_end'):
            # הדרן closes the chapter; the formula is not Mishnah, and neither is
            # the Gemara tail it follows. The next chapter's Mishnah opens after it.
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


def _supports_thinking_level(model_name: str) -> bool:
    """Gemini 3.x exposes thinking_level; 2.x only thinking_budget.

    Verified 2026-08-29 against the live model list: gemini-3.7-flash accepts
    thinking_level=HIGH together with response_mime_type='application/json'.
    """
    m = (model_name or '').lower()
    return any(tag in m for tag in ('gemini-3', 'gemini-4'))


CLAUSE_TERMINATORS = '.:?!'
_CLAUSE_BREAK = re.compile(r'(?<=[\.\:\?\!])\s+')


# Citation and attribution formulae that INTRODUCE a quoted story. Jeff, 2026-09-01:
# "not technically part of the stories. But they are important, as, for example,
# תניא indicates the Talmud thinks the story is Tannaitic... If not too much
# trouble, we should include them."
#
# Every token here was drawn from a case he named or from a boundary in one of the
# four blind sets, and each is counted against his OTHER boundaries before being
# added (Lesson 27). Matching is on the nikud-stripped text, because his edition and
# Sefaria's vocalise differently.
_OPENING_FORMULAE = (
    'תניא',            # this is Tannaitic - his own example
    'תנו רבנן',
    'תא שמע',
    'מיתיבי',
    'גופא',
    'אמר רב',           # covers אמר רב יהודה אמר רב - his second example
    'אמר רבי',
    'אמר ריש לקיש',
    'אמר רבה',
    'כי אתא',
    'בעו מיניה',
    'שאלו',
    'משתעי',
    'דרש',
)


def _strip_nikud(text: str) -> str:
    return re.sub(r'[\u0591-\u05C7]', '', text or '')


def _is_opening_formula(clause: str) -> bool:
    """True if this clause is a formula that introduces a story rather than telling it.

    Deliberately narrow: the clause must be SHORT. `אמר רב יהודה אמר רב:` introduces;
    `אמר רב יהודה: מעשה בבנו ובבתו של רבי ישמעאל...` is the story itself, and pulling a
    boundary over that would swallow narrative rather than frame it.
    """
    bare = _strip_nikud(clause).strip()
    if not bare:
        return False
    words = bare.split()
    if len(words) > 8:
        return False
    if any(bare.startswith(f) for f in _OPENING_FORMULAE):
        return True
    # `רב חנין משתעי:` puts the verb last, so a prefix test misses the whole
    # "X related:" family. Allowed only on a very short clause, where there is no
    # room for narrative around it.
    return len(words) <= 4 and any(f in bare for f in ('משתעי', 'מישתעי'))


def extend_start_over_opening_formula(pages: List[Dict]) -> Dict[str, int]:
    """Move a story's start back over the formula that introduces it (Jeff, 2026-09-01).

    ONE clause, backwards only, inside the start segment. A deterministic
    post-processor on a text-internal decision is the shape Lesson 15 forbids — the
    difference here is that the expert stated the rule in words, so it is principled
    rather than fitted to our own past errors, and it stays one clause wide.

    Measured before shipping, on all four blind 2005 sets: 10 of our late starts are
    fixed, and the 10 targets that move against us are ones where his own start sits
    after a formula — "the lists were sloppy and preliminary, and we had not worked
    this out."

    Returns counts. Never silent: a run records what moved.
    """
    counts = {'extended': 0, 'already_at_formula': 0, 'no_formula': 0}
    for page in pages:
        seg_by_idx = {s.get('index', i): s for i, s in enumerate(page.get('segments', []))}
        for story in page.get('stories', []):
            if story.get('classification') == 'NOT_A_STORY':
                continue
            span = story.get('text_span_start')
            if not span or span.get('clause_index') is None:
                counts['no_formula'] += 1
                continue
            idx = span['clause_index']
            if idx <= 0:
                counts['already_at_formula'] += 1
                continue
            seg = seg_by_idx.get(span.get('segment', story.get('start_segment')))
            heb = (seg or {}).get('hebrew', '')
            clauses = _split_into_clauses(heb)
            if idx >= len(clauses):
                counts['no_formula'] += 1
                continue
            prev = heb[clauses[idx - 1][0]:clauses[idx - 1][1]]
            if not _is_opening_formula(prev):
                counts['no_formula'] += 1
                continue
            span['clause_index'] = idx - 1
            span['char_offset'] = clauses[idx - 1][0]
            span['opening_formula'] = _strip_nikud(prev).strip()
            counts['extended'] += 1
    return counts


def _split_into_clauses(text: str):
    """Split `text` into sentence-level clause ranges [(start, end), ...].

    Splits ONLY on `. : ? !` — never on commas. The comma is the most frequent
    mark in this corpus (4,855 vs 3,959 periods) and Jeff's Kiddushin 12b seg 4
    correction is precisely a story continuing past one, so splitting there
    would recreate the bug Wave 5 exists to fix.

    Ranges are over the ORIGINAL string (nikud and HTML intact), so offsets map
    directly onto what the review UI renders. Verified safe: no HTML tag in the
    corpus contains a clause terminator.
    """
    if not text:
        return []
    ranges = []
    pos = 0
    for m in _CLAUSE_BREAK.finditer(text):
        ranges.append((pos, m.start()))
        pos = m.end()
    if pos < len(text):
        ranges.append((pos, len(text)))
    return [(a, b) for a, b in ranges if text[a:b].strip()]


def story_summary(story: Dict) -> str:
    """The story description shown to the boundary prompt.

    `one_sentence_summary` FIRST. The detector writes that field; `summary` is
    present on 0 of 262 stories in the corpus, so the old chain fell through to
    a joined events list on 100% of them — and that list stops before the
    story's resolution, while 35 of the 52 expert boundary targets are ENDS.
    Measured 2026-08-30 across all three wave4_notrim files.
    """
    for key in ('one_sentence_summary', 'summary', 'text'):
        val = story.get(key)
        if val:
            return str(val)[:400]
    crit = (story.get('criteria') or {}).get('multiple_events') or {}
    events = crit.get('events') or []
    return '; '.join(events)[:400] if events else '(no summary available)'


def _clause_text_for_display(text: str, rng) -> str:
    """Clause text as shown to the model: HTML stripped, whitespace collapsed."""
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', text[rng[0]:rng[1]])).strip()


def _assert_word_boundary(text: str, pos: int, ref: str, seg: int, side: str):
    """Fail loud if a boundary would land inside a word (Lesson 16).

    Clause ranges cannot produce one by construction; this makes that guarantee
    checkable rather than assumed, so any future refactor breaks the build
    instead of silently corrupting text.
    """
    if pos <= 0 or pos >= len(text):
        return
    before, after = text[pos - 1], text[pos]
    ok = (before.isspace() or after.isspace()
          or before in '.:?!,\u05f4\u05f3()[]\u2013\u2014'
          or after in '.:?!,\u05f4\u05f3()[]\u2013\u2014')
    if not ok:
        raise AssertionError(
            f"mid-word text span at {ref} seg {seg} ({side}) offset {pos}: "
            f"...{text[max(0, pos - 20):pos]}|{text[pos:pos + 20]}... "
            f"A boundary must sit on a real text unit (Lesson 16)."
        )


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
