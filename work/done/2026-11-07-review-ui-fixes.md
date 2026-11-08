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

**Self-contained.** Read [`FRAMEWORK.md`](../../FRAMEWORK.md) §5, then the finding this item
carries: [`2026-11-07-review-ui-review.md`](../../docs/findings/2026-11-07-review-ui-review.md).
Every numbered item below is a finding there, with file and line.

## The problem

The axis page is correct on what it shows (Critical Rule 1 holds on 154 real cards) and wrong
on two things that cost a round: it highlights the whole segment while the scored output
claims a clause-level span — so five of Gittin's five boundary corrections were corrections to a
boundary we never claimed — and it keeps every verdict only in memory. Eruvin is ~150 cards
across several evenings; either defect alone makes the round unreliable.

## Must land before Eruvin's review page is built

- [x] **1** Render `text_span_start/end` as a `<mark>` inside the highlighted segment via
      `spanRangeFn` (`review_ui_core.py` already supports it); the how-to says the mark is our
      claimed extent and the segment is context. Test: a story with spans renders the mark at
      the right offsets; a story without spans renders as today; a cross-page story renders
      no end mark (`text_span_end_skipped` after PR #71).
- [x] **2** Persist `verdicts` to `localStorage` keyed by tractate + `detector_version` on
      every change; restore in `init()`; header shows "N saved locally"; Save still downloads
      the JSON. Test under Node with a `localStorage` stub.
- [x] **3** Count pages carrying `stage2_error` in `build_data`; header line "N pages not
      examined (call failed): refs"; refuse to build if any unless `--allow-failed`. Test with
      a fixture page carrying `stage2_error`.
- [x] **4** `build_boundary_testset.py` reads `quote_start` / `quote_end` / `quote_polarity`
      from axes exports before regex-mining `notes`; match by overlap (Lesson 36). Re-run on
      the 2026-09-23 export and count what it now yields that notes-mining did not.
- [x] **5** `saveResults` counts cards with any field set but no `is_story` and warns with refs.
- [x] **6** State the `NOT_A_STORY` decision in a comment, or show them badged "we rejected
      this" behind a default-off filter. Decide which; either is fine, silence is not.

## Should land (cheap)

- [x] `--out` anywhere: print `out`, not `out.relative_to(ROOT)`.
- [x] Delete the dead listed/unlisted filter branches and `test_C11`'s dead assertion, or
      render the buttons.
- [x] `verdict_reading.label_axes`: `out_of_scope` → `('out_of_scope', 'is_story=out_of_scope (R-S1)')`.
- [x] Per-verdict `schema_version` and `answered_at`.
- [ ] `measure_recall_vs_expert_list.py --write-listed-keys` writes `results/recall/<t>_listed_keys.json`
      so `--only` / `--listed` stop being a manual step; `new_tractate_workflow.md` Step 5
      points at the axis generator with the full command.
- [x] Throughput: numeric progress ("37 of 154"), keyboard `y` / `b` / `n` / `j` for yes /
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

## Outcome

Done 2026-11-07 on `fix/review-ui-spans-persistence`, one commit per item, each with a
test written first and watched fail. Tests: `tests/test_review_ui_fixes.py` (UI, run
through the page's own JS under Node) and `tests/test_boundary_testset_structured.py`.
Export shape unchanged: two per-verdict additions (`schema_version`, `answered_at`).

1. **Claimed span marked.** `claimedSpan()` passed as `spanRangeFn`; `build_data` carries
   `text_span_start/end/_end_skipped`. Cross-page stories draw no end mark even when a
   pre-PR-#71 run carries a stale `text_span_end`. The how-to says the mark is our claimed
   extent. *Measured on Gittin v11:* of the five boundary notes, 10b, 19b, 20a and 43b now
   ask to cut text that is already outside the mark — they agree with us. **70a does not
   fully:** the start agrees (the mark opens on his quote), but the mark runs to the end of
   segment 22 and he ends the story at וּמִית! — a real end correction, so the finding's
   "all 5" is 4 and a half.
2. **Verdicts persist** in localStorage under `axis-review:<tractate>:<detector_version>`,
   written on every change (notes as typed), restored in `init()`, "N saved locally" in the
   header; works with storage blocked. Save Review unchanged.
3. **Failed pages** (`stage2_error`) are named in the header; the build refuses unless
   `--allow-failed`.
4. **Structured quotes read.** `build_boundary_testset.py` reads `quote_start` /
   `quote_end` (polarity `include` by construction) and `quote` + `quote_polarity` (direction
   from `extent`) before mining notes; a direction stated in a field is not mined again.
   Located by text, never by verdict key. Loads Gittin and Yevamot segments. Scratch
   rebuild: 70 → 78 targets, none lost. Of the 7 quotes in the 2026-09-23 export, **5 now
   become targets**; 2 do not resolve — Gittin 68a's `quote_start` is English, and Yevamot
   105a's start was doubled by grab-then-paste (the defect fixed on the page since). +3
   Gittin note targets resolve only because Gittin segments are now loaded. **No banked
   targets file was regenerated.**
5. **Save warns** with refs for cards with input but no `is_story`; they stay absent from
   the export (property F).
6. **NOT_A_STORY: decided, not shown, counted.** Comment in `build_data`; header shows "we
   rejected ourselves (not shown): N".

Should-land done: `--out` anywhere; listed/unlisted filter buttons rendered (hidden until
`--listed`), so the branches and `test_C11` are live rather than deleted;
`label_axes('out_of_scope')`; per-verdict `schema_version` + `answered_at`; "N of M
reviewed", keys j / y / b / n (set, never toggle; inert in text boxes), classification
filter; `new_tractate_workflow.md` Step 5 points at the axis generator.

**Not done:** `measure_recall_vs_expert_list.py --write-listed-keys`. Not a few lines done
safely: the recall window credits neighbouring stories (`audit_proposal_credit.py`, Gittin
57b/68a), so a listed-keys writer needs the strict-overlap rule, and a wrong file tells
Jeff his list has stories it does not. Step 5 of the workflow now says so.

Browser (Critical Rule 1, built-in browser, Yevamot v11 page, 154 cards): 15a seg 7 shows
the mark inside the highlighted row; a Borderline click survived a reload (selected, card
faded, "1 saved locally", "1 of 154 reviewed"); `j` then `y` answered card 0; a 30-page
Yevamot fixture with `stage2_error` on 3b refused without `--allow-failed` and, with it,
showed "1 page not examined (call failed): Yevamot 3b". No console errors.
