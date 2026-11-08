---
title: Review UI — show the boundary we claim, keep the verdicts, name the pages not examined
capability: [review, boundaries]
tractate: [eruvin]
blocked_by: []
awaiting: []
writes: [validation/generators/generate_axis_review_ui.py, validation/generators/review_ui_core.py, scripts/build_boundary_testset.py, scripts/verdict_reading.py, scripts/measure_recall_vs_expert_list.py, docs/technical/new_tractate_workflow.md, tests/]
finding: docs/findings/2026-11-07-review-ui-review.md
superseded_by:
---

# Review UI fixes before Eruvin's first round

**Self-contained.** Read [`FRAMEWORK.md`](../FRAMEWORK.md) §5, then the finding this item
carries: [`2026-11-07-review-ui-review.md`](../docs/findings/2026-11-07-review-ui-review.md).
Every numbered item below is a finding there, with file and line.

## The problem

The axis page is correct on what it shows (Critical Rule 1 holds on 154 real cards) and wrong
on two things that cost a round: it highlights the whole segment while the scored output
claims a clause-level span — so five of Gittin's five boundary corrections were corrections to a
boundary we never claimed — and it keeps every verdict only in memory. Eruvin is ~150 cards
across several evenings; either defect alone makes the round unreliable.

## Must land before Eruvin's review page is built

- [ ] **1** Render `text_span_start/end` as a `<mark>` inside the highlighted segment via
      `spanRangeFn` (`review_ui_core.py` already supports it); the how-to says the mark is our
      claimed extent and the segment is context. Test: a story with spans renders the mark at
      the right offsets; a story without spans renders as today; a cross-page story renders
      no end mark (`text_span_end_skipped` after PR #71).
- [ ] **2** Persist `verdicts` to `localStorage` keyed by tractate + `detector_version` on
      every change; restore in `init()`; header shows "N saved locally"; Save still downloads
      the JSON. Test under Node with a `localStorage` stub.
- [ ] **3** Count pages carrying `stage2_error` in `build_data`; header line "N pages not
      examined (call failed): refs"; refuse to build if any unless `--allow-failed`. Test with
      a fixture page carrying `stage2_error`.
- [ ] **4** `build_boundary_testset.py` reads `quote_start` / `quote_end` / `quote_polarity`
      from axes exports before regex-mining `notes`; match by overlap (Lesson 36). Re-run on
      the 2026-09-23 export and count what it now yields that notes-mining did not.
- [ ] **5** `saveResults` counts cards with any field set but no `is_story` and warns with refs.
- [ ] **6** State the `NOT_A_STORY` decision in a comment, or show them badged "we rejected
      this" behind a default-off filter. Decide which; either is fine, silence is not.

## Should land (cheap)

- [ ] `--out` anywhere: print `out`, not `out.relative_to(ROOT)`.
- [ ] Delete the dead listed/unlisted filter branches and `test_C11`'s dead assertion, or
      render the buttons.
- [ ] `verdict_reading.label_axes`: `out_of_scope` → `('out_of_scope', 'is_story=out_of_scope (R-S1)')`.
- [ ] Per-verdict `schema_version` and `answered_at`.
- [ ] `measure_recall_vs_expert_list.py --write-listed-keys` writes `results/recall/<t>_listed_keys.json`
      so `--only` / `--listed` stop being a manual step; `new_tractate_workflow.md` Step 5
      points at the axis generator with the full command.
- [ ] Throughput: numeric progress ("37 of 154"), keyboard `y` / `b` / `n` / `j` for yes /
      borderline / no / next-unreviewed, a classification filter. Each one is a few lines; none
      changes the export shape.

## How you know it worked

- `python3 -m pytest tests/test_review_ui_axes.py tests/test_review_ui_symmetry.py -q` green.
- Generate the Yevamot page into a scratch path and open it in a browser (Critical Rule 1:
  test in the browser, not only in Node): spans marked, reload keeps a test verdict, header
  names failed pages when a fixture has one.
- The five Gittin boundary notes, re-read against the marked span, are now "agrees" rather
  than corrections.

## Guardrails

- The export shape (`is_story` / `extent` / `confidence` / `grouping` / `display_problem` /
  `detector_version` / `applies_to`) does not change; `build_ruler.py` and `verdict_reading.py`
  read it. New fields are additions.
- "Is it a story" stays the only required question; the axes stay independent of it (pinned).
- No golden, no detector, no scorer denominator is touched.

## When done

Finding update, `## Outcome` here, `python3 scripts/board.py finish review-ui-fixes`.
