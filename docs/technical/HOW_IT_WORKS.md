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

**Skip Decision (changed 2026-08-31):** a page is examined if it has **≥1 NARRATIVE_EVENT**,
or if any segment's triage call failed (fail-open — we could not look, so we do not get to
decide), or if it contains a canonical story introducer (the Stage 2 lexical override).
Everything else is skipped.

The rule previously demanded that a narrative event be *corroborated* — `≥2 NARRATIVE_EVENT`,
or `≥1 NARRATIVE_EVENT and ≥2 VERBAL_ACT`. Measured against both blind expert lists, that
clause was the single richest seam of missed stories in the corpus: the 8 pages it discarded
across Ketubot and Kiddushin contain **6 real stories** (~75%, against 14.3% for discarded
pages as a whole), Ketubot 51a among them. Removing it costs 8 extra Stage 2 calls across
both tractates and raises triage recall from 98.0% → **98.7%** (Ketubot) and 95.6% →
**97.8%** (Kiddushin).

**Verbal acts alone never keep a page.** A `V >= 4` clause would recover one further story
(Kiddushin 10b) but buys nothing on Ketubot for 70 extra calls; it is a threshold fitted to a
single case and is deliberately not adopted.
→ [`2026-08-31-triage-single-narrative.md`](../findings/2026-08-31-triage-single-narrative.md)

Result: ~54% of Ketubot pages skipped and ~59% of Kiddushin, down from 56% / 62%.

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

The goldens add two labels the detector does not emit (2026-09-25): **BORDERLINE**
(Jeff's own column — speech with conflict, R-C2) and **OUT_OF_SCOPE** (a story, but of
biblical characters, R-S1).

**Automatic Disqualifiers → NOT_A_STORY:**
Mishna sections, hypothetical cases, habitual actions, pure legal rulings, legal deliberation, legal debate settings

### Stage 2b: Twin Pass (v11, on by default since 2026-09-25)

The Talmud often tells the same shape of anecdote two or three times in a row. Stage 2
tends to return one and stop. So after Stage 2, for each free segment beside a found
story, one narrow call: *here is story A, here is the segment next to it — separate
incident, same story, or not a story?* Adds only; never moves or drops a story.

- Code: `_find_adjacent_twins()` / `_twin_prompt()` in `src/story_detector_v11.py`
- Flags: `TWIN_PASS` (default `1`; `0` = off), `TWIN_TRIGGER` (default `all`;
  `labelled` asks only beside NARRATIVE_EVENT / VERBAL_ACT segments), `TWIN_REACH` (1)
- Its `not_a_story` option names Jeff's rejections: Gemara commentary on A, a bare
  report of what someone did or used to do with no one responding, a seating
  description, a biblical episode (`docs/STORY_RULES.md` R-B4, R-C5, R-S1) — and, since
  2026-09-29, says an incident followed by a ruling IS a story (R-C0)
- A failed call adds nothing and is counted on `twin_failures`
- Findings: `docs/findings/2026-09-14-twin-pass.md`, `2026-09-25-jeff-verdicts-scope-commentary-reports.md`

### Stage 3: Adversarial Validation (disabled)

Three-call LLM pattern for borderline stories. Currently disabled because testing showed net negative impact (-1 on Jeff's labels). The code is present for future tuning.

Pattern: Detector Defense → Jeff's Advocate → Adjudicator

### Stage 4: Boundary Refinement + Cross-Page Merge

The order `run_pipeline` in `src/story_detector_v11.py` executes (2026-11-07 review). There is no 4e and no separate post-processing stage: `run_pipeline` carries its own Stage 4. `src/clause_roles.py` is not on this path.

- **4a** `refine_boundaries_with_event_tags` — trims DELIBERATION segments off story edges using the Stage 1 labels, with a guard for narrative rulings.
- **4b** `merge_cross_page_stories_v7` — merges the page-N story reaching the page break with the page-N+1 story nearest its top, using triage NARRATIVE_EVENT labels at the boundary.
- **4c** `merge_cross_page_stories` (legacy) — merges on a continuation flag, only when the page-N story ends at the page's last segment; stamps `cross_page_merge_legacy`.
- **4d** `stitch_cross_page_continuation` (LLM) — for a flagged story nothing merged, asks where it ends on the next page; failures go to `stage4_call_failures`.
- **4f** `continuation_check` (LLM) — for an unflagged story ending at the page's last segment, asks whether the next page continues it; failures go to `stage4_call_failures`.
- **4g** `filter_mishnah_only_stories` — moves stories wholly inside a Mishnah block to `mishnah_stories` (see the warning below).
- **4h** `snap_start_to_introducer` — moves a multi-segment story's page-1 start to a canonical introducer (`ההוא ד`, `מעשה ב`, …) within reach.
- **4i** `trim_trailing_stam_segments` — drops trailing segments that open with a stam-Talmud marker, keeping ≥2; skips stories with `spans_pages`.
- **4j** `filter_biblical_actor_stories` — demotes a story whose named actors are only biblical (whole-name match) to `NOT_A_STORY`, with `out_of_scope` / `scope_reason: biblical_actors`.
- **4k** `extract_text_spans_via_clauses` (LLM, one call per story, paced by `delay`) — the model picks a clause index in the first/last segment and we compute the offset; no end span on a story with `spans_pages`.
- **4l** `extend_start_over_opening_formula` (R-B1) — extends a start back over the formula that introduces the story; runs after 4k because it moves a clause index.
- **dedup** `detect_duplicate_stories` — flags stories that duplicate another.

4h–4l and dedup read `stories[]` only; `mishnah_stories` is deliberately left as 4g wrote it.

> **A move is a deletion to every reader that doesn't know the key.** Nothing downstream reads `mishnah_stories` — not `scripts/evaluate_golden.py`, not `scripts/measure_recall_vs_expert_list.py`, not the review UI generators. So a story the detector found and this stage dropped scores identically to one it never found. **Measured 2026-08-30:** the filter accounts for **4 of Ketubot's 15 golden false negatives (27%)**, and all 4 are stories Jeff marked correct in review. On Kiddushin its one case is `NOT_A_STORY` in the golden, so there the filter is right.
>
> Report it before trusting any golden number: `python3 scripts/report_mishnah_filter_delta.py --detected <runs>`. The recall harness now prints what was withheld (without moving the headline number). **The scope premise is an open question for Jeff** — see [`docs/findings/2026-08-30-mishnah-filter-delta.md`](../findings/2026-08-30-mishnah-filter-delta.md) and Lesson 27.
>
> Known defect, separate from the scope question: `_tag_mishnah_segments()` mislabels Gemara as Mishnah at chapter boundaries, where Sefaria uses the chapter incipit in `<big><strong>` instead of `מתני׳`. 7 pages affected (Ketubot 54b, 65b, 70a, 95b, 101b; Kiddushin 41a, 58b).

**Wave 3 Stage 2 prompt changes (v9):**
- "MULTIPLE STORIES PER PAGE" section — detect every distinct story; follow with iterative pass (one extra Stage 2 call listing already-detected ranges) when ≥1 story found.
- "EMBEDDED STORIES" section — two worked examples (Ketubot 111b baraita-embedded `תניא + מעשה ב`; Ketubot 91a objection-embedded `תא שמע + narrative`). Both sourced from Ketubot canonical (Lesson 2).
- Three new disqualifier rules: all-verbal exchanges, biblical-only narratives, requirement of ≥2 distinct actions + change/conflict. Per Lesson 8 these are abstract patterns only — no Kiddushin-specific examples.

**Duplicate Detection:** Flag stories that appear to be the same passage quoted on multiple pages.

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
PYTHONPATH=. python3 src/story_detector_v7.py
# Output: results/v7/ketubot_v7_2-60.json

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
