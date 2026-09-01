---
title: Turn Classification from a range into a number
capability: [classification, review]
tractate: []
blocked_by: []
awaiting: [jeff:axes-round]
finding:
superseded_by:
---

# Turn Classification from a range into a number

**Self-contained.** Read [`FRAMEWORK.md`](../FRAMEWORK.md) first, then this.
**Capabilities: 3 Classification (primary), 5 Review.**
**Depends on Jeff: yes — one review round on the new UI. No code is blocked.**
**Cost:** free once the round returns. No API calls.

This is **Phase C** of
[`review-verdict-axes`](../work/done/2026-08-30-review-verdict-axes.md), which closed on
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
  capability (Lesson 25) — and then **fixed**, because that is what they are for.

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
[`docs/capabilities/3_classification.md`](../docs/capabilities/3_classification.md),
add an `## Outcome` here, and `python3 scripts/board.py finish 2026-08-31-classification-point-estimate`.
