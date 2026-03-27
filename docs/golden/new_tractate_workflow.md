# New Tractate Workflow

Step-by-step guide for running the story detector on a tractate beyond Ketubot and validating the results. This workflow was developed from the Ketubot experience (v5 through v10, 4 rounds of expert review).

---

## Prerequisites

- `.env` file with `GOOGLE_API_KEY` (Gemini Flash)
- Sefaria API access (public, no key needed)
- Python 3.11+ with `google-genai`, `requests`, `python-dotenv`
- Expert reviewer available to validate ~30 stories

## Step 1: Fetch Pages from Sefaria

```bash
# The run script handles fetching automatically via Sefaria API.
# Pages are cached locally after first fetch.
# Talmud page refs follow the pattern: "Kiddushin 2a", "Kiddushin 2b", etc.
```

**What you get:** A JSON file with pages, each containing segments with English and Hebrew text.

## Step 2: Run Event Triage (Stage 1)

The triage stage classifies each segment as NARRATIVE_EVENT, VERBAL_ACT, DELIBERATION, or HABITUAL. Pages with fewer than 2 NARRATIVE_EVENT segments are skipped (~60% of pages).

**Cost:** ~$0.08 per 100 pages (Gemini Flash input tokens)
**Time:** ~2 min per 100 pages (with 0.5s rate limiting)

## Step 3: Run Story Detection (Stage 2)

The detector analyzes kept pages using:
- Event-annotated segments from Stage 1
- 6-criteria classification system (IDENTIFIABLE_CHARACTERS, MULTIPLE_EVENTS, CAUSAL_CHAIN, TEMPORAL_PROGRESSION, DESCRIPTIVE, CHANGE_OUTCOME)
- Legal discussion disqualifiers
- Few-shot examples from Ground Truth DB
- Cross-page context (last 5 segments of previous page, first 5 of next)

**Cost:** ~$0.12 per 100 pages (only ~40% of pages make it past triage)
**Time:** ~3 min per 100 pages

## Step 4: Post-Processing (Stage 4, no API calls)

Deterministic refinement:
- Boundary trimming using event types
- Cross-page merge detection (stories spanning page boundaries)
- Duplicate story detection

## Step 5: Generate Review UI

```bash
python3 validation/generators/generate_review_ui.py --input results/v7/tractate_output.json --output validation/ui/tractate_review.html
```

The review UI shows each detected story with:
- English and Hebrew text side by side
- Story text highlighted in context
- Classification and confidence level
- Verdict buttons (correct / incorrect / approve / adjust)
- Notes field for boundary and merge corrections

## Step 6: Expert Review

**Target:** ~30 stories across representative pages.

**What to tell the reviewer:**
- The detector finds story candidates. About 85% are correct; ~15% are false positives.
- False positives are typically legal discussions with narrative framing — a rabbi goes somewhere, sits before another rabbi, then the passage is entirely legal debate.
- The most useful feedback is: (1) is this a story or not, and (2) if the boundaries are wrong, where should the story start/end.
- See `docs/golden/error_taxonomy.md` for the 6 known error patterns.

**What the reviewer produces:** A feedback JSON file with verdicts and notes per story.

## Step 7: Score Against Expert Labels

```bash
python3 scripts/evaluate_golden.py \
  --detected results/v7/tractate_output.json \
  --golden results/canonical/tractate_golden.json \
  --output docs/golden/baseline_tractate.json
```

**Metrics:**
- **Classification F1:** Story vs not-story (target: >0.85)
- **Boundary IoU:** Segment overlap for correct stories (target: >0.90)
- **Merge F1:** Cross-page detection (target: >0.70)
- **Composite:** 0.4 × F1 + 0.4 × IoU + 0.2 × Merge

**Ketubot baseline for comparison:** Composite = 0.93

## Step 8: Build Golden Dataset (if proceeding to full tractate)

If the expert reviews all stories (not just a sample):

```bash
python3 scripts/build_canonical.py  # Adapt for new tractate
python3 scripts/apply_boundary_corrections.py  # Adapt for new tractate
```

---

## What to Expect

Based on Ketubot experience:

| Metric | Typical Range | Notes |
|---|---|---|
| Pages with stories | ~40% of total | Triage skips ~60% |
| Stories per page | 0-3 | Average ~0.8 for pages with stories |
| False positive rate | ~15% | Legal discussions with narrative framing |
| Boundary accuracy | >95% | Most boundaries are segment-level accurate |
| Cross-page merges | ~10% of stories | Detector catches ~85% of these |

## Known False Positive Patterns

From Ketubot error taxonomy (see `docs/golden/error_taxonomy.md`):

1. **LEGAL_FALSE_POSITIVE** (most common): Legal debate with narrative setting
2. **CONFIDENCE_MISCALIBRATION**: Habitual actions or events without causality rated too high
3. **BOUNDARY_OVEREXTENSION**: Talmud analytical commentary included in story
4. **BOUNDARY_UNDEREXTENSION**: Story starts earlier or ends later than detected
5. **MERGE_NEEDED**: Adjacent entries that are one story
6. **MERGE_INCORRECT**: Cross-page merge with wrong segments

These patterns are expected to appear in any tractate. The expert should watch for them.

## Cost Summary

| Tractate Size | Triage | Detection | Total | Time |
|---|---|---|---|---|
| 80 pages | $0.06 | $0.10 | **~$0.16** | ~4 min |
| 160 pages | $0.12 | $0.18 | **~$0.30** | ~8 min |
| 200 pages | $0.15 | $0.22 | **~$0.37** | ~10 min |

## Important Lessons from Ketubot

1. **Don't add the expert's corrections as few-shot examples for the same tractate.** This causes overfitting — the model memorizes specific passages instead of learning patterns. Use corrections from OTHER tractates as few-shots.

2. **The detector is a candidate finder, not a final classifier.** 98.7% recall means it finds almost everything. The ~15% false positive rate is the cost of high recall. The expert review is the final decision-maker.

3. **Prompt engineering has a ceiling (~0.93 composite on Ketubot).** The remaining errors are genuine judgment calls requiring domain expertise. Don't spend time tweaking prompts — spend it on expert review.

4. **Process all feedback types in one pass.** Don't split feedback into "easy" and "hard" buckets. The hard ones (boundary/merge corrections) get forgotten.
