# Code review of the axis review UI, before Eruvin's first round

**Date:** 2026-11-07 · **Item:** `work/2026-11-07-review-ui-fixes.md` · **Evidence:** generator run
on `results/v11/yevamot/yevamot_v11.json` into a scratch path, every card rendered through the
page's own JS under Node, 26/26 review-UI tests pass; no API calls. Companion to
[`2026-11-07-pre-eruvin-code-review.md`](2026-11-07-pre-eruvin-code-review.md), which covered
the run path; this covers what Jeff sees and what comes back.

**Verdict.** Critical Rule 1 holds on real data: 154 Yevamot cards, every one bilingual, story
rows highlighted, all 12 cross-page stories drawn on both pages, all 8 Mishnah-withheld shown
and badged, nothing undefined leaks. The export shape is what `build_ruler.py` and
`verdict_reading.py` read. **But two defects would cost a round:** the page shows a boundary we
do not claim, and it forgets every answer on reload.

## P1 — would cost Jeff's round

1. **The page hides the detector's clause-level boundary and highlights the whole segment, so
   Jeff corrects boundaries the scored output does not have.** `generate_axis_review_ui.py:347`
   passes `spanRangeFn = null`; `text_span_start/end` is never read, while
   `scripts/score_boundary_targets.py:69` *does* score them. **Measured, already happened:** all
   5 Gittin boundary notes (10b:6, 19b:6, 20a:9, 43b:4, 70a:22) quote text to cut that the run's
   `text_span_*` already excluded, character for character. Lesson 25's shape: the display
   manufactured five corrections, and an `extent: ends_wrong` on such a card is banked against
   a boundary we never claimed. 96 of Yevamot's 168 stories carry spans. The docstring's reason
   (L331–333, "55% cut mid-word") describes the reverted Wave 4 char offsets, not v11's clause
   spans (0 mid-word). *Fix:* pass a `spanRangeFn` returning the clause offsets as a `<mark>`
   (`review_ui_core.py:24–26, :64` already support it) and say in the how-to that the highlight
   is our claimed extent. **The UI and the scorer must agree on which boundary is ours.**
2. **Verdicts live only in memory.** `const verdicts = {}` (L306); no `localStorage` in this
   generator or `review_ui_core.py` (the four older generators had it). A reload, a crash or a
   closed tab loses every answer; the only persistence is Save → download → email.
   `docs/capabilities/5_review.md:120` describes the old UIs. *Fix:* persist on every
   `setAxis/setNotes/setField`, keyed by tractate + `detector_version`; restore in `init()`;
   show "N saved locally".

## P2 — wrong or lossy

3. **Pages whose Stage 2 call failed look like pages with no stories.** `build_data` (L93–148)
   never reads `stage2_error`; such a page emits no card and no count. An Eruvin run with 6
   failed pages ships a page Jeff "confirms" where nobody examined. *Fix:* count them, show
   "N pages not examined (call failed): refs" in the header, refuse to build unless
   `--allow-failed`.
4. **The structured boundary quotes have no consumer.** `quote_start/quote_end/quote_polarity`
   are exported (L632–638); nothing in `scripts/` reads them — `build_boundary_testset.py:78`
   regex-mines `notes`. The 2026-09-23 round returned 4 `quote_start` and 3 `quote_end`, the
   first structured boundaries Jeff ever gave, and they were never scored. *Fix:* read them
   in `build_boundary_testset.py` before mining notes; match by overlap (Lesson 36).
5. **A card with a note, extent or quote but no `is_story` click is silently absent from the
   export** (`isComplete` L356, `buildExport` L613); `saveResults` reports no dropped count.
   No loss in either axes round so far. *Fix:* warn with refs before export.
6. **`NOT_A_STORY` proposals are dropped with no stated decision** (L106–107): 22 of Yevamot's
   168. The recall scorer names "proposed-then-NOT_A_STORY" as a miss cause — the one Jeff
   could rescue. *Fix:* a comment stating the decision, or include them badged "we rejected
   this" behind a default-off filter.

## P3

- `--out` outside `validation/ui/` writes the file then crashes on `out.relative_to(ROOT)` (L750).
- Dead listed/unlisted filter: buttons never rendered (L281–288), branches unreachable
  (L380–381), `test_C11` pins the dead string.
- Neighbouring-daf context carries 3 segments, draws 2 (`review_ui_core.py:115–116`).
- `verdict_reading.label_axes` has no case for the axes-3 token `out_of_scope`; `read_as`
  is wrong on every such verdict (counting unaffected).
- `new_tractate_workflow.md` Step 5 sends an operator to the retired `generate_review_ui.py`;
  the `--only`/`--listed` input (`results/recall/<t>_listed_keys.json`) has no script that
  writes it. For Eruvin that is a manual, undocumented step.
- `schema_version` is file-level only, no per-verdict timestamp, so verdicts per hour cannot be
  measured from the file (5_review's gate is "days, not weeks").
- Card key `ref_start-end` does not distinguish `stories[]` from `mishnah_stories[]` (no
  collision in Yevamot).
- 5.3 MB for Yevamot, half of it `page_segments` duplicated per story; loads offline with zero
  external references. Fine for a file Jeff opens.

## Throughput inventory (FRAMEWORK §5 gate: days, not weeks)

**Exists:** one-click Yes; filters all / unreviewed / cross-page / in-a-Mishnah; progress bar;
reviewed cards fade; `--only` to shrink to the unlisted ask; `--listed` badges; grab-highlighted-
Hebrew into the quote boxes; one-sentence summary per card; neighbouring daf for edge boundaries.

**Missing:** persistence and resume (P1 #2); keyboard shortcuts (none in any generator since
`batch_review.html`); numeric progress and jump-to-next-unreviewed; sort or filter by
classification/confidence; reviewer name; per-verdict timestamps; an "add a story we missed"
control (his three Gittin additions arrived as prose on other cards); any statement of pages not
examined (P2 #3); pagination — one page of 154 cards re-rendered on every filter click.

## What is fine

The "is it a story" question is the only completion requirement and the extent / confidence /
grouping disclosure is independent of it, both pinned. Gittin's empty structured fields were a
layout defect, fixed; the 2026-09-23 round returned 9 populated extent axes — the instrument
works, nothing downstream reads what it captures (P2 #4). The docstring at
`generate_axis_review_ui.py:44–46` names the wrong symmetry test; pairing on this page is
covered by `test_hebrew_leads_and_still_pairs_with_the_english`.
