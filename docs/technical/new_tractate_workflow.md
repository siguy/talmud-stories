# New Tractate Workflow

Step-by-step guide for running the story detector on a tractate beyond Ketubot and validating the results. This workflow was developed from the Ketubot experience (v5 through v10, 4 rounds of expert review).

---

## Prerequisites

- `.env` file with `GOOGLE_API_KEY` (Gemini Flash)
- Sefaria API access (public, no key needed)
- Python 3.11+ with `google-genai`, `requests`, `python-dotenv`
- Expert reviewer available to validate ~30 stories
- Read `docs/history/2026-03-27-PLAN-false-positive-learning.md` — contains checklists for before/after each tractate run

## Step 1: Fetch Pages from Sefaria

```bash
# The run script handles fetching automatically via Sefaria API.
# Pages are cached locally after first fetch.
# Talmud page refs follow the pattern: "Kiddushin 2a", "Kiddushin 2b", etc.
```

**What you get:** A JSON file with pages, each containing segments with English and Hebrew text.

## Step 2: Run Event Triage (Stage 1)

The triage stage classifies each segment as NARRATIVE_EVENT, VERBAL_ACT, DELIBERATION, or HABITUAL. **A page is examined if it has ≥1 NARRATIVE_EVENT**, or if a triage call failed (fail-open), or if it contains a canonical story introducer. Everything else is skipped — roughly 55-60% of pages.

*Changed 2026-08-31: the rule used to require a narrative event to be corroborated (`N>=2`, or `N>=1 and V>=2`). That clause was discarding pages at a ~75% story rate. See [`2026-08-31-triage-single-narrative.md`](../findings/2026-08-31-triage-single-narrative.md).*

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

## Step 4: Post-Processing (Stage 4)

Deterministic refinement + targeted LLM calls:
- **4a:** Boundary trimming using event types
- **4b-4c:** Cross-page merge detection (stories spanning page boundaries)
- **4d:** Cross-page stitching (targeted LLM for unmerged boundary stories with continuation flags)
- **4f:** Continuation check (targeted LLM for stories near page boundaries WITHOUT continuation flags — asks "does THIS story continue?" not "find a story"). ~$0.03 per tractate. Added for Kiddushin run, caught 3 additional cross-page stories.
- Duplicate story detection

**Reference implementation:** `scripts/run_kiddushin.py` demonstrates the full workflow.

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

> **Two traps in this step, both of which this document used to walk you into.**
>
> 1. **Never pass `--output docs/golden/v7/baseline_ketubot.json`** (and never omit
>    `--output`, which defaults there). It overwrites an unreproducible baseline —
>    a permanent loss, Lesson 11. That file's hash is pinned by
>    `tests/test_bookkeeping.py` and the pre-commit hook; if the guard fires,
>    `git checkout --` the file. **Always write to a scratch path.**
> 2. **Never verify with the composite score.** It is built from ratios over pages
>    already in the golden, so *deleting* expert validations makes it go **up** — it is
>    anti-correlated with the risk it is supposed to measure. Verify with **counts**
>    and `git hash-object`.

```bash
python3 scripts/evaluate_golden.py \
  --detected results/<run>/<tractate>_output.json \
  --golden results/canonical/<tractate>_canonical.json \
  --output /tmp/scratch_<tractate>_score.json      # scratch path, always
```

**Metrics:**
- **Classification F1:** story vs not-story
- **Boundary IoU:** segment overlap for correct stories
- **Merge F1:** cross-page detection
- **Composite:** reported by the harness; **do not use it as a gate** (see above)

For live gate values per capability read [`FRAMEWORK.md`](../../FRAMEWORK.md) and the
generated [`STATE.md`](../../STATE.md). This document deliberately carries no current
score — every stale entry found in the 2026-08-30 audit was a count, a score, or an
"active version" claim.

## Step 7b: Measure TRUE recall against a blind list — do this before believing anything

The golden is **circular**: it contains only stories the detector itself proposed, so it
cannot see a systematic miss. If an expert list exists for this tractate that predates our
output, it is the only thing that can measure recall.

```bash
python3 scripts/measure_recall_vs_expert_list.py \
  --expert-json results/expert_lists/<tractate>_2005.json --expert-filter recall \
  --tractate <Tractate> \
  --detected results/<run>/<tractate>_output.json \
  --golden results/canonical/<tractate>_canonical.json \
  --out results/recall/<tractate>_jeff2005_matches.json
```

Before trusting the list, **check it is actually blind**: `scripts/check_appendix_coverage.py`
(Lesson 29 — 5 of Jeff's 95 Kiddushin stories were our own output, merged in and unmarked).
Filter on the `blind` / `counts_for_recall` flags, never on the raw length and never on the
filename.

Quote **Triage** and **Detection given the page survived triage** separately. The
end-to-end figure charges Triage's losses to Detection as well (Lesson 35), and the two have
separate gates.

## Step 7c: Price what triage discarded — cheap, and it has moved a gate

Triage errors are invisible by construction: a page never examined leaves no record of what
was lost. With a blind list on hand this is measurable for pennies, and on both tractates so
far it found real stories.

```bash
python3 scripts/run_triage_recall_price.py --tractate <t> --dry-run   # partition, no API
python3 scripts/run_triage_recall_price.py --tractate <t>             # Stage 2 on skipped pages
python3 scripts/sweep_triage_rules.py --tractate <t>                  # candidate rules, no API
```

**Sweep the intermediate rules, do not act on the endpoints** (Lesson 37). On Ketubot the
first step inside the interval captured the entire gain available from reading the whole
tractate, at 1/31st the cost. Then ask of the winner: *principled boundary, or threshold
fitted to the data I just looked at?* Ship the first, reject the second and pin the
rejection with a test.

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
| Pages with stories | ~40% of total | Triage skips ~55-60% |
| Stories per page | 0-3 | Average ~0.8 for pages with stories |
| False positive rate | ~15% | Legal discussions with narrative framing |
| Boundary accuracy | see `STATE.md` | The >95% once quoted here was never measured against a blind set; the blind figure is lower (Lesson 23) |
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

2. **The detector is a candidate finder, not a final classifier.** Recall is high — read the current figure from [`STATE.md`](../../STATE.md), and note whether it is end-to-end or given-the-page-survived-triage, because those differ and put the deficit in different columns (Lesson 35). The ~15% false positive rate is the cost of high recall. The expert review is the final decision-maker.

3. **Prompt engineering has a ceiling.** The remaining errors are genuine judgment calls requiring domain expertise. Don't spend time tweaking prompts — spend it on expert review. *(This item used to name a composite score as the ceiling. Don't quote the composite: it rises when expert validations are deleted. The ceiling argument stands on its own — see `docs/findings/2026-03-25-overfitting-and-generalization-research.md`.)*

4. **Process all feedback types in one pass.** Don't split feedback into "easy" and "hard" buckets. The hard ones (boundary/merge corrections) get forgotten. *Eight months on, one whole round is still unread — and for a different reason: it stores verdicts in a shape the loader silently skips (Lesson 38).*

5. **Store the detector version with every verdict** (Lesson 36). A verdict judges the output of a specific version. Quoting a round's precision as the current capability's number charges today's detector for calls it no longer makes — of 8 notes where the detector disagreed at review time, 7 now agree.

6. **Ask the reviewer *which* thing is wrong.** Most rejections are not "this is not a story" — they are boundary, merge or confidence complaints pooled into one number (Lesson 30). Until the UI separates them, precision can only be quoted as a range.

7. **Count what the reviewer never saw.** Stage 4g moves Mishnah-internal stories to `mishnah_stories[]`. The recall harness, the boundary scorer and the axis review UI each read it and report it apart (see the table in `CLAUDE.md`); `evaluate_golden.py` is blind to it and immutable, so a withheld story still scores there as one we never found (Lesson 27). Run `scripts/report_mishnah_filter_delta.py` before trusting a golden number, and read the `WITHHELD` column on `score_boundary_targets.py` before reading its `N/A` one.

8. **Check a "blind" list is blind before using it as one** (Lesson 29). Run `scripts/check_appendix_coverage.py`. Filter on the `blind` / `counts_for_recall` flags, never on the filename and never on the raw length.

9. **Two runs of the same code differ.** Measure the noise floor before attributing a score change to a change you made (Lesson 22), and regenerate baselines the same day rather than quoting a stored number (Lesson 11).
