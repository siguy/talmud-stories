# How It Works

## Overview

This system detects narrative stories in Talmud text using AI-powered semantic analysis with expert-validated criteria. Version 7 uses a decomposed 4-stage pipeline with Gemini 3 Flash, achieving 92.1% accuracy on Jeff Rubenstein's 128 expert-labeled passages.

```
Sefaria API → Fetch pages → Event Triage (skip 66% of pages) →
Constrained Detection (event-annotated) → Boundary Refinement →
Cross-page Merge → Duplicate Detection → [Post-Processing] → Output
```

## v7 Pipeline Stages

### Stage 0: Fetch Text from Sefaria

```python
# Preserves aligned segment structure
{
  "ref": "Ketubot 8b",
  "segments": [
    {"index": 0, "english": "...", "hebrew": "..."},
    {"index": 1, "english": "...", "hebrew": "..."},
    # text[] and he[] are 1:1 aligned
  ]
}
```

### Stage 1: Event Triage (`src/event_triage.py`)

Every segment on every page is classified into one of 4 event types using Gemini Flash:

| Event Type | Description | Example |
|-----------|-------------|---------|
| NARRATIVE_EVENT | Physical action happens to a specific person | "A certain man came before Rabbi X" |
| VERBAL_ACT | Speech act as main content (ruling, question) | "Rabbi X said..." |
| DELIBERATION | Legal reasoning, hypotheticals, abstract principles | "What is the law if..." |
| HABITUAL | Recurring practice or custom | "He was accustomed to..." |

**Skip Decision:** Pages with <2 NARRATIVE_EVENT (or <1 NARRATIVE + <2 VERBAL_ACT) are skipped.
Result: ~66% of pages skipped on pages 2-60, ~50% on pages 61-112.

**Hebrew markers used:** `מעשה` (incident), `ההוא/ההיא` (that certain person), `אתא לקמיה` (came before), `הוה עובדא` (there was an incident)

### Stage 2: Constrained Story Detection (`src/story_detector_v7.py`)

Using Gemini 3 Flash (or configurable model), each non-skipped page is evaluated with:
- **Event annotations** on each segment: `[NARRATIVE_EVENT] Seg 3: "Rabbi Yochanan said..."`
- **Cross-page context** (last 3 segments of previous page, first 3 of next page)
- **Anti-legal few-shot examples** from Ground Truth DB (Jeff's actual corrections)
- **Explicit legal exclusion**: "A legal discussion is NOT a story even if it mentions a specific rabbi, place, or time"

Classification uses **6 criteria**:

| Criterion | Question | Example |
|-----------|----------|---------|
| identifiable_characters | Any specific actors? Anonymous characters count! | "a certain man", "Rabban Gamliel" |
| multiple_events | More than one NARRATIVE event? (not legal talk) | Physical actions, state changes |
| causal_chain | Event A CAUSED Event B CAUSED Outcome? | Not just sequential |
| temporal_progression | Before → during → after? | Time passes in narrative |
| descriptive | What DID happen (not hypothetical)? | Not "if X were to..." |
| change_outcome | Situation TRANSFORMED? | Not just action report |

**Key refinements from expert validation:**
- Anonymous characters ("a certain man/woman") are FULLY valid characters
- What is NOT a narrative event: verbal statements, legal arguments, deliberation, traveling to debate
- Rabbis who only state legal opinions are NOT characters in a story

**Classification:**
- **YES**: 6/6 criteria, no weakeners
- **HIGH_CONFIDENCE**: 5-6 criteria, minor weakeners
- **LOW_CONFIDENCE**: 3-4 criteria, OR 1 event + discussion (borderline stories)
- **NOT_A_STORY**: <3 criteria OR disqualifier

**Automatic Disqualifiers → NOT_A_STORY:**
Mishna sections, hypothetical cases, habitual actions, pure legal rulings, legal deliberation, legal debate settings

### Stage 3: Adversarial Validation (disabled)

Three-call LLM pattern for borderline stories. Currently disabled because testing showed net negative impact (-1 on Jeff's labels). The code is present for future tuning.

Pattern: Detector Defense → Jeff's Advocate → Adjudicator

### Stage 4: Boundary Refinement + Cross-Page Merge

**Boundary Refinement:** Trim DELIBERATION segments from story edges using triage event types. If a story starts/ends with segments classified as DELIBERATION in Stage 1, shrink the boundary inward. A guard prevents trimming segments that contain narrative rulings integral to the story.

**Cross-Page Merge (v8 improved):** Uses triage NARRATIVE_EVENT types at page boundaries to detect story fragments, even when one side is classified NOT_A_STORY:
1. Check if last segment of page N has NARRATIVE_EVENT in triage
2. Check if first segment of page N+1 has NARRATIVE_EVENT in triage
3. If both sides have narrative events and one side has a detected story, promote and merge
4. **(v8) Case 4 merge:** Detects real stories that span pages even when neither side was flagged as a continuation
5. **(v8) Relaxed legacy merge:** Uses OR logic (either side has narrative events) instead of requiring both
6. **(v8) Post-detection stitching:** A second pass after all merges catches stories that were split across pages but not caught by the initial boundary checks

Result: 16 cross-page stories on Ketubot 61-112 (up from 7 in v7). 12 cross-page stories on Kiddushin.

**Stage 4f: Continuation Check (new — added for Kiddushin run)**

After all merge passes, checks stories near page boundaries that were NOT flagged as continuing. Unlike stitch (4d) which only fires when `continues_to_next_page` is already set, this catches stories where the LLM didn't set the flag.

How it works:
1. Find the last story on each page that ends within 3 segments of the page boundary
2. Skip if already merged or already has continuation flags
3. Send LLM: story text + first 8 segments of next page
4. Ask: "Is the top of the next page a direct continuation of THIS specific story? Same characters, same situation?"
5. Conservative — requires same characters and narrative flow, not just thematic similarity

Why this works better than the sliding-window approach (which produced 28 false positives): it asks about a SPECIFIC story's continuation, not "find any story at this boundary." Binary yes/no, not open-ended detection.

Cost: ~$0.03 per tractate (20-30 small API calls).
Result on Kiddushin: 3 additional cross-page stories caught (including Dama ben Netina, 31a→31b).

**Stage 4g (v8 Wave 1): Mishnah-only filter** — `filter_mishnah_only_stories`. Moves stories entirely within a Mishnah block (Sefaria `מתני׳`/`גמ׳` markers) out of `stories` and into `mishnah_stories`. `NOT_A_STORY` entries are exempt. Each moved story is stamped `filtered_as_mishnah: true`.

> **A move is a deletion to every reader that doesn't know the key.** Nothing downstream reads `mishnah_stories` — not `scripts/evaluate_golden.py`, not `scripts/measure_recall_vs_expert_list.py`, not the review UI generators. So a story the detector found and this stage dropped scores identically to one it never found. **Measured 2026-08-30:** the filter accounts for **4 of Ketubot's 15 golden false negatives (27%)**, and all 4 are stories Jeff marked correct in review. On Kiddushin its one case is `NOT_A_STORY` in the golden, so there the filter is right.
>
> Report it before trusting any golden number: `python3 scripts/report_mishnah_filter_delta.py --detected <runs>`. The recall harness now prints what was withheld (without moving the headline number). **The scope premise is an open question for Jeff** — see [`docs/findings/2026-08-30-mishnah-filter-delta.md`](../findings/2026-08-30-mishnah-filter-delta.md) and Lesson 27.
>
> Known defect, separate from the scope question: `_tag_mishnah_segments()` mislabels Gemara as Mishnah at chapter boundaries, where Sefaria uses the chapter incipit in `<big><strong>` instead of `מתני׳`. 7 pages affected (Ketubot 54b, 65b, 70a, 95b, 101b; Kiddushin 41a, 58b).

**Stage 4h (v8 Wave 2): Start-boundary snap** — `snap_start_to_introducer`. For each multi-segment story: if a canonical Hebrew introducer (`ההוא ד`, `ההיא`, `מעשה ב`, `כי הא ד`, `כדתניא`) starts the segment immediately BEFORE detector's start, extend start back. If one starts a segment in `[start+1..start+3]`, snap start forward. Pure-Python, no LLM.

**Stage 4i (v8 Wave 2): End-boundary trim** — `trim_trailing_stam_segments`. Walks story from end inward, drops trailing segments that open with stam-Talmud markers (`שמע מינה`, `מאי טעמא`, `אי הכי`, `שאני`, `תא שמע`, `מיתיבי`, etc.) as long as ≥2 segments remain.

**Stage 4j (v8 Wave 2): Biblical-actor filter** — `filter_biblical_actor_stories`. Demotes stories whose `criteria.identifiable_characters.evidence` names only biblical figures (Moses, David, Ezra, Nebuchadnezzar, "Jewish people" collective, etc.) to NOT_A_STORY. The catalog is for rabbinic stories.

**Stage 4k (v9 Wave 3): Text-internal boundary edits** — `edit_text_internal_boundaries`. For each real story: search the first segment for the earliest canonical introducer at a word boundary, search the last segment for the latest stam-Talmud marker at a full word boundary. When found mid-segment, records `text_span_start = {segment, char_offset, introducer}` and/or `text_span_end = {segment, char_offset, marker}`. Char offsets are in the original (with-nikud) text. The evaluation harness reads only `start_segment` / `end_segment`, so these fields are score-neutral — the change shows up in the review UI (slice rendered with strikethrough + highlight) but not in the metric. Closes the segment-level gap from Lesson 12.

**Wave 3 Stage 2 prompt changes (v9):**
- "MULTIPLE STORIES PER PAGE" section — detect every distinct story; follow with iterative pass (one extra Stage 2 call listing already-detected ranges) when ≥1 story found.
- "EMBEDDED STORIES" section — two worked examples (Ketubot 111b baraita-embedded `תניא + מעשה ב`; Ketubot 91a objection-embedded `תא שמע + narrative`). Both sourced from Ketubot canonical (Lesson 2).
- Three new disqualifier rules: all-verbal exchanges, biblical-only narratives, requirement of ≥2 distinct actions + change/conflict. Per Lesson 8 these are abstract patterns only — no Kiddushin-specific examples.

**Duplicate Detection:** Flag stories that appear to be the same passage quoted on multiple pages.

### Stage 5: Post-Processing (`src/post_processing.py`)

Optional mechanical rules applied after LLM detection:

- **Rule 3 (v6 ensemble):** If v6 didn't find a story AND page has ≤1 NARRATIVE_EVENT → demote to NOT_A_STORY. Catches legal misidentifications on law-heavy pages.
- Rules 1 (single-event filter) and 2 (duplicate reclassification) are disabled — caused regressions in testing.

With gemini-2.0-flash, post-processing adds +2.4% (89.8% → from 87.4%). With gemini-3-flash, post-processing adds nothing (model already at 92.1%).

## Example Classification

**Ketubot 8b (Segments 3-5):**
```
When Rav Ḥisda and Rabba bar Rav Huna would go to console mourners in
the house of the Exilarch, they would say...
```

**Criteria Met:**
- ✓ named_characters: Rav Ḥisda, Rabba bar Rav Huna
- ✓ multiple_events: Going, consoling, speaking
- ✓ causal_chain: Go → Console → Say blessing
- ✓ temporal_progression: Before visit → during → after
- ✓ descriptive: What they DID do
- ✓ change_outcome: Mourners consoled

**Result:** YES (6/6, no weakeners)

---

**Ketubot 14b (Sequential, not causal):**
```
A girl went out to draw water. She was raped.
```

**Criteria Analysis:**
- ✓ named_characters: No specific name (weak)
- ✓ multiple_events: Went out, was raped
- ✗ causal_chain: Going out didn't CAUSE rape (sequential)
- ✓ temporal_progression: Before → after
- ✓ descriptive: What happened
- ✗ change_outcome: No transformation shown

**Self-Check:** "Are events CAUSAL or just SEQUENTIAL?" → SEQUENTIAL

**Result:** NOT_A_STORY (failed causality, self-check flagged)

## Output Format

```json
{
  "tractate": "Ketubot",
  "pages": [
    {
      "ref": "Ketubot 8b",
      "segments": [
        {"index": 0, "english": "...", "hebrew": "..."}
      ],
      "stories": [
        {
          "start_segment": 3,
          "end_segment": 5,
          "classification": "YES",
          "criteria": {
            "named_characters": {"met": true, "evidence": "Rav Ḥisda..."},
            "causal_chain": {"met": true, "chain": "Go → Console → Bless"}
          },
          "criteria_met_count": 6,
          "disqualifiers_found": [],
          "weakeners_found": [],
          "one_sentence_summary": "Rav Ḥisda and Rabba bar Rav Huna..."
        }
      ],
      "mishnah_stories": [
        {
          "start_segment": 8,
          "end_segment": 8,
          "classification": "HIGH_CONFIDENCE",
          "filtered_as_mishnah": true
        }
      ]
    }
  ]
}
```

**`mishnah_stories`** holds what Stage 4g withheld — same shape as a `stories` entry, plus `filtered_as_mishnah`. Anything reading a run for scoring or display must decide explicitly whether to include it; treating `stories` as the whole output silently drops these. Empty on most pages (5 stories corpus-wide across `results/v10/wave4_notrim/`).

## Why This Works

**vs Keyword Matching:**
- Keywords find "once" in legal discussions → false positive
- AI understands narrative STRUCTURE, not just words

**vs Simple AI Prompts:**
- v1-v3 had 50%+ false positive rate
- Expert validation identified specific patterns
- v5.1 addresses each pattern with explicit criteria

**Key Insights from Expert Validation:**

> v4.1: "The AI confuses attribution with characters. When it sees 'Rabbi X said that Rabbi Y said...', it thinks there's a story with characters, but it's just legal attribution."
> → Led to `rabbi_legal_opinion` disqualifier (53 false positives caught)

> v5.1: "Stories can be about unnamed people. The anonymous character does not weaken the confidence."
> → Renamed criterion to `identifiable_characters`, anonymous chars count fully

> v5.1: "The events here are rabbis making legal arguments... that is not really an event that makes for a story."
> → Refined what constitutes a "narrative event" vs legal/intellectual activity

> v5.1: "The page is a totally arbitrary marker and should be ignored when identifying the boundaries of stories."
> → Added cross-page merging and context in v6

> v5.1: "Passages with one event and then discussion should be identified as borderline stories."
> → Calibrated LOW_CONFIDENCE for borderline stories in v6

## Technical Details

**Model:** Gemini 3 Flash (`gemini-3-flash-preview`)
- Configurable via `model_name` param or `GEMINI_MODEL` env var
- 0.5 second delay between requests
- ~3 minutes for 40 pages detection
- Thinking mode disabled for Flash (JSON mode); increased token budget for Pro

**API:** Sefaria REST API
- No authentication required
- 15 second timeout
- Preserves segment alignment

**Cost (Gemini 3 Flash):** ~$0.31 per 40 pages (detection only)

## Running Detection

```bash
export GOOGLE_API_KEY='your-key'

# v7 (current) — pages 2-60, uses pre-computed triage
# NOT `python3 src/story_detector_v7.py`. Every detector's main() writes
# results/v7/ketubot_v7_2-60.json unconditionally, with no --output to redirect it,
# and that file is the frozen baseline the regression tests score against.
# The runner below writes to results/v7_fresh/ instead (Lesson 11).
PYTHONPATH=. python3 scripts/run_ketubot_v7_fresh.py
# Output: results/v7_fresh/ketubot_v7_2-60.json

# Pages 61-112 (generalization test)
python3 scripts/run_ketubot_61_112.py              # Full run
python3 scripts/run_ketubot_61_112.py --triage-only # Triage only
python3 scripts/run_ketubot_61_112.py --resume      # Resume from saved triage
# Output: results/v7/ketubot_v7_61-112.json

# Kiddushin (new tractate)
python3 scripts/run_kiddushin.py                    # Full run
python3 scripts/run_kiddushin.py --triage-only      # Triage only
python3 scripts/run_kiddushin.py --resume            # Resume from saved triage
# Output: results/kiddushin/kiddushin_v7.json

# Model comparison
PYTHONPATH=. python3 tests/model_comparison.py --model gemini-3-flash-preview

# Regression test (compare v6 vs v7 vs Jeff's labels)
PYTHONPATH=. python3 tests/v7_regression_test.py
```

## Validation UI

Results are reviewed using HTML interfaces:
- Side-by-side English/Hebrew
- Story segments highlighted (±1 context)
- Criteria breakdown visible
- Expert can mark correct/incorrect
- Feedback exported as JSON

See `validation/ui/` for interfaces.
