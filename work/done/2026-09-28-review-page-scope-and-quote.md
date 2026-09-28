---
title: Review page — an "out of scope" answer, and the doubled Hebrew quote
capability: [review]
tractate: []
blocked_by: []
awaiting: []
writes: [validation/generators/generate_axis_review_ui.py, validation/generators/review_ui_core.py, scripts/build_ruler.py, scripts/build_gittin_golden.py, tests/test_review_ui_symmetry.py, tests/test_axis_review_ui.py]
finding:
superseded_by:
---

# Review page — out-of-scope answer, doubled quote

**Self-contained.** Read [`docs/capabilities/5_review.md`](../../docs/capabilities/5_review.md)
and [`2026-09-25-jeff-verdicts`](../../docs/findings/2026-09-25-jeff-verdicts-scope-commentary-reports.md)
§"Two defects in the review page".

## The problems (both hit by Jeff, 2026-09-23)

1. **No "a story, but not our kind" answer.** On Gittin 57b / 68a he had to answer
   `is_story: no`, `confidence: right` and explain in a note. R-S1 makes out-of-scope
   its own answer (Lesson 42: an answer with no column gets rounded).
2. **The start quote came back doubled** on Yevamot 105a — the highlight capture appended
   the selection twice.

## Method

- Add `out_of_scope` to the `is_story` answers (yes / borderline / no / out of scope),
  exported verbatim; bump `schema_version` to `axes-3`. Readers of `is_story`
  (`build_ruler.py` `AXES_TO_VERDICT`, `build_gittin_golden.py`
  `VERDICT_TO_CLASSIFICATION`) must map it explicitly — an unknown value already raises
  or is counted; add `out_of_scope` to both, with a test.
- Reproduce the doubled capture in the browser first, then fix it in the shared core.
- Verify in the browser: Hebrew + English, story highlighted, quote captured once.

## When done

`## Outcome`, `python3 scripts/board.py finish 2026-09-28-review-page-scope-and-quote`.

## Outcome

**Done, 2026-09-28.**

- **Out of scope is an answer.** `is_story` gains `out_of_scope` ("A story, but out of
  scope"), exported verbatim; `schema_version` → `axes-3`. `build_ruler.py` counts it in
  neither ACCEPTED nor REJECTED; `build_gittin_golden.py` routes it to `out_of_scope`
  (its output is byte-identical after the change). Tests: `test_out_of_scope_is_its_own_answer`,
  `test_out_of_scope_is_neither_accepted_nor_rejected`.
- **The doubled quote was not a capture bug.** Reproduced in the browser on the real
  2026-09-16 page: the grab button writes the selection once and a second grab replaces
  it. Jeff's value is one grab (no comma) followed by a paste of the same phrase (with
  the comma) — the paste appended. Fix: a grab now leaves the box's text selected, so a
  paste replaces it. His text is never altered afterwards. Test:
  `test_a_grab_leaves_the_box_selected_so_a_paste_replaces_it`. The preview pane has no
  keyboard focus, so the paste itself could not be driven end to end; the selection
  (0–41 of 41 characters) was confirmed.
- **Browser-checked** on a freshly generated page: Hebrew + English side by side, the
  story segment highlighted, context segments dimmed, the new button selects and exports.
- **Found in passing, not fixed here:** the committed `results/rulers/*_ruler.json` are
  stale against current `main` — regenerating them with main's own code changes all
  three. This change has no effect on them (verified by building on a clean `main`
  checkout).
