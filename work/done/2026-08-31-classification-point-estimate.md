---
title: Turn Classification from a range into a number
capability: [classification, review]
tractate: []
blocked_by: []
awaiting: [jeff:axes-round]
writes: [validation/ui/, validation/feedback/, results/rulers/, scripts/build_ruler.py, scripts/report_classification_precision.py, scripts/board.py, tests/test_board_reports_what_it_holds.py, docs/capabilities/3_classification.md]
finding:
superseded_by:
---

# Turn Classification from a range into a number

**Self-contained.** Read [`FRAMEWORK.md`](../../FRAMEWORK.md) first, then this.
**Capabilities: 3 Classification (primary), 5 Review.**
**Depends on Jeff: yes — one review round on the new UI. No code is blocked.**
**Cost:** free once the round returns. No API calls.

This is **Phase C** of
[`review-verdict-axes`](../../work/done/2026-08-30-review-verdict-axes.md), which closed on
2026-08-31 with Phases A and B done. It is a separate item because what remains is not
work we can do — it is a round, and a round is weeks.

## The problem

Classification can only be quoted as a **range** — Ketubot 87.9–94.8%, Kiddushin
67.4–92.1% — because the reviewer never recorded *which thing* he was rejecting. The
width of that range is unreadable notes plus boundary/merge/confidence rejections pooled
into one figure.

The instrument that fixes it now exists. What is missing is a reading from it.

## Method

1. Generate the page: `python3 validation/generators/generate_axis_review_ui.py`
   (writes `validation/ui/axis_kiddushin_review.html` and `axis_ketubot_review.html`).
2. **Open it in a browser before sending it.** CLAUDE.md critical rule 1, and the rule
   Lesson 25 records us breaking. A display bug does not merely waste his time, it
   manufactures expert feedback we then have to disbelieve.
3. Send one tractate. Bundle the two asks that cost him nothing extra:
   - the **Mishnah-withheld** passages are already displayed and filterable on the page
     (`in a Mishnah`) — ask whether they belong in the database (`jeff:mishnah-scope`);
   - ask him to keep his appendix of "stories you and Claude found" a **separate file**
     (`jeff:appendix-separate`) — it cannot be reconstructed afterwards, and the window
     closes the moment we send Gittin / Yevamot / Eruvin results (Lesson 29).
4. Drop the returned JSON into `validation/feedback/` and rebuild:
   `python3 scripts/build_ruler.py --tractate Kiddushin`.

## How you know it worked

**The acceptance test for the whole three-phase item:** the round reports
`unclassified_notes: 0`, and `precision_all_causes` and
`precision_classification_only` **converge** — the range becomes a point.

Also check, because they are new and have never seen real data:
- every verdict carries a `detector_version` (Lesson 36);
- any `borderline` verdicts are counted as neither accepted nor rejected;
- any `display_problem` flags are charged to the renderer, not to a judgement
  capability (Lesson 25) — and then **fixed**, because that is what they are for;
- **any `quote` carries a `quote_polarity`.** For those entries
  `scripts/build_boundary_testset.py` can read the field instead of inferring direction
  from the note with `quote_polarity()` — which is what leaves 16 of the banked 70
  targets `mixed` or `unclear`. Do not retrofit the old 70; the mining was the only way
  to get them and it does not become better in hindsight.

## Guardrails

- **Quote the new round's precision as a property of the version it judged.** It is a
  fact about `v10-notrim`, not about whatever runs next (Lesson 36).
- **Do not fold the new round into the old per-round figures.** `applies_to` exists to
  keep base and corrected data apart (Lesson 3).
- **Do not re-derive the banked rounds in the new vocabulary and call it a measurement.**
  129 of them are marked `lossy` for a reason; the range narrows going forward, not
  backward.

## When done

Write the finding to `docs/findings/<date>-classification-point-estimate.md`, update the
**3 Classification** row in `STATUS.md` and
[`docs/capabilities/3_classification.md`](../../docs/capabilities/3_classification.md),
add an `## Outcome` here, and `python3 scripts/board.py finish 2026-08-31-classification-point-estimate`.

## Outcome

**Done, 2026-09-02, and the acceptance test passed.**
Finding: [`2026-09-02-classification-point-estimate.md`](../../docs/findings/2026-09-02-classification-point-estimate.md).

The test was: `unclassified_notes` reaches 0, and `precision_all_causes` and
`precision_classification_only` **converge**. On the first round in the axis vocabulary
they are **identical** — `0.143..0.143`, 18 rejections, every one naming its own axis. The
width that made Classification a range for a year was unreadable notes, and it is gone.

### The converged number is not the tractate's precision, and that is the finding

**14.3% is precision on the residue.** The Gittin round covered *only* the proposals his
2005 list does not name — deliberately, because the rest were already corroborated. So the
ruler's denominator is the hardest subset that exists. Quoting it as Gittin's
Classification precision understates it by about seventy points.

Nothing is wrong with the ruler: it reports precision over proposals carrying a verdict,
which is correct, and on Ketubot and Kiddushin that was most of them because those rounds
walked the tractate story by story. **The round changed shape and the figure quietly
changed meaning.** A metric is comparable across tractates only while the rounds behind it
ask the same question — which is not a property any code can check, so it is written into
the finding and into `docs/capabilities/3_classification.md` beside the number.

The tractate figure, from the new `scripts/report_classification_precision.py`:
**83.7–86.7%** over the 135 of 147 asserted proposals that carry a label; **76.9–87.8%**
with the 12 unjudged spans left in. The width *is* those 12, reported as a width rather
than distributed.

**The caveat that must travel with it:** 110 of the 113 correct entries are *corroborated*
by his blind list, not judged. His list says a story is there; it says nothing about our
extent. Only 25 of 147 have been judged as spans, and that is a review-throughput limit,
not a measurement one.

### Two things this item did not expect to find

1. **An earlier figure quoted today — 81.6–84.4% — was wrong.** It used
   `gittin_listed_keys.json`, built on the loose window, which mis-credits two proposals.
   Corrected in the finding rather than overwritten.
2. **`board.py` could not see the new golden or the new ruler.** `goldens()` and
   `rulers()` looped over a hardcoded `("ketubot", "kiddushin")` while `TRACTATES` held
   five, so the Gittin Classification cell printed `⬜` — *never measured* — for a file on
   disk. Fixed, and pinned by a test: **every golden and every ruler on disk must be
   readable by the board.** This is the third defect of the shape
   [`board-guards-verify-the-wrong-property`](../../docs/findings/2026-09-01-board-guards-verify-the-wrong-property.md)
   describes, and the same one as Lesson 38 — a missing file and an unlooped tractate
   produce the identical blank.

### Guardrails observed

- **Not folded into the old per-round figures.** Ketubot and Kiddushin keep their ranges;
  129 banked verdicts are `lossy` and re-deriving them in the new vocabulary would be
  manufacturing a measurement. The range narrows going forward, not backward.
- **Quoted as a property of the version judged** (Lesson 36) — `v11`, `applies_to: base`,
  carried on every verdict.
- **`borderline` counted as neither.** 4 of them, and they stay their own answer.
- `display_problem` was false on all 25, so nothing is charged to the renderer.

### What it still does not settle

`jeff:review-error-rate` is unanswered, so there is no threshold to compare 86.7% against.
The number is now a number; whether it is good enough is his call, and it stays Email 2.

*(`writes:` corrected by hand at close. `finish`'s drift report diffs `main..HEAD`, and
this branch is stacked on three earlier PRs, so it attributed all of their files to this
item. Same caveat as the two items closed before it.)*
