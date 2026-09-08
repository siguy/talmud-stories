---
title: Cut every reader over to the exact-anchor matcher, so the board locates a story one way
capability: [detection, classification, boundaries]
tractate: [ketubot, kiddushin, gittin, yevamot]
blocked_by: []
awaiting: []
writes: [scripts/measure_recall_vs_expert_list.py, scripts/measure_strict_recall.py,
         scripts/build_ruler.py, scripts/audit_proposal_credit.py,
         scripts/audit_detection_density.py, scripts/build_gittin_golden.py,
         results/recall/, results/rulers/, docs/capabilities/, STATE.md, WORK.md,
         results/canonical/gittin_canonical.json, tests/test_bookkeeping.py,
         tests/test_build_ruler.py,
         docs/findings/2026-09-03-exact-matcher-cutover.md]
finding: docs/findings/2026-09-03-exact-matcher-cutover.md
superseded_by:
---

# Cut every reader over to the exact-anchor matcher

**Self-contained.** Read [`FRAMEWORK.md`](../../FRAMEWORK.md) first, then
[the matcher finding](../../docs/findings/2026-09-03-exact-anchor-matcher.md), which measured
this and shipped it behind a flag.

## The problem

`--matcher exact` is measured and better on all four tractates, but only two scripts can
use it. **Four others call `recall.locate` directly** — `build_ruler.py`,
`audit_proposal_credit.py`, `audit_detection_density.py`, `build_gittin_golden.py` — so
the board currently answers *"where is this story"* two different ways depending on which
script is asked. That is worse than either matcher alone: the recall row and the ruler
would disagree about the same story.

## Method

1. Make `exact` the default in both harnesses and route the other four through
   `recall.make_locator`, so there is **one** locating function and one place to change it.
2. Re-bank the **unsuffixed** `results/recall/*_jeff2005_matches.json` and the rulers.
3. Record the moved cells in `docs/capabilities/` as new dated rows. **Do not rewrite
   `STATUS.md`** — that is the integration step on main, not a branch's job.

## How you know it worked

- Every script that locates an expert story reports the **same span** for the same story;
  a spot check across the four scripts on one story per tractate says so.
- The two Ketubot cells that move are the two the matcher finding already named, and
  nothing else moves unexplained.
- `python3 -m pytest tests/ -q` is green, `board.py --check` passes, and the golden
  **counts** in `GOLDEN_COUNTS` are unchanged — verified by count and `git hash-object`,
  never by the composite score (Critical Rule 5).

## Guardrails

- **`scripts/evaluate_golden.py` is immutable** and is not in `writes:`.
- **`build_gittin_golden.py` writes a golden.** Rebuilding it is a data change: diff the
  output before replacing anything, and if the story count moves, stop and explain the
  move before writing. A golden is not a by-product of a matcher change.
- The exact matcher **falls back per story** when nothing anchors. Every script must
  count and name its fallbacks (Lesson 38) rather than fold them in silently.

## When done

Write the finding, add an `## Outcome`, and
`python3 scripts/board.py finish 2026-09-03-exact-matcher-cutover`.

## Outcome

**Done.** The finding is
[`docs/findings/2026-09-03-exact-matcher-cutover.md`](../../docs/findings/2026-09-03-exact-matcher-cutover.md).

`exact` is the default in both harnesses and the other four scripts route through
`recall.make_locator`, so there is one locating function for the board. The ruler and the
recall harness now report the **same** number per tractate — 130/149, 76/90, 108/111 —
which they did not before. Nothing fell back to the 4-gram aligner on any tractate.

**Cells that moved:** Ketubot detection 96.0 → **87.2**, triage 98.0 → **96.6**,
detection-given-triage 97.9 → **90.3**; Kiddushin loose 93.3 → **84.4** (strict unchanged
at 83.3); Gittin 100.0 → **97.3**; Yevamot 94.1 → **89.2**. Loose and strict now coincide
everywhere except Kiddushin, where they differ by one story. Recorded as dated rows in
`docs/capabilities/1_triage.md` and `2_detection.md`; **`STATUS.md` untouched**, as that
is the integration step on main.

**Three downstream consequences, all checked rather than assumed:**

1. The loose-credit population — 35 proposals, 11 of them top-confidence — drops to
   **Gittin 0, Ketubot 0, Kiddushin 1**.
   [`2026-09-03-loose-credited-proposals`](../2026-09-03-loose-credited-proposals.md) is now
   a one-case item, not an eleven-case one; its `results/recall/proposal_credit_audit.json`
   has been rewritten here.
2. **One entry left the Gittin golden**, and the guardrail was the reason it got looked at:
   `Gittin 34a:9` was in as `expert_blind_list`/`YES` because a 7-segment window credited
   it to Jeff's 34a:11 story. The two are formulaic near-twins — *did not marry* within
   thirty days versus *did not return* — one segment apart. Nobody labelled 34a:9. Golden
   is now **134 / 116**, repinned in `GOLDEN_COUNTS` with the reason beside it, verified by
   count and never by the composite. No other golden changes.
3. The density finding **survives** re-anchoring: same 350-story denominator, same shape
   (82% alone on the daf vs 90% at 4+).

**Two tests were pinning the old behaviour and were repinned, not deleted.**
`test_the_loose_window_credits_a_story_we_never_proposed` existed to *document the bug* —
Kiddushin 81b:9, credited by the window and by nothing else. It is now
`test_the_window_no_longer_credits_a_story_we_never_proposed` and pins the fix on the same
case.

**Left open, deliberately:** the live triage keep-rule figures (98.7% / 97.8%) were
measured with the 4-gram matcher on a different run and are **not** re-measured here —
flagged in the capability doc rather than silently mixed with the shipped-artifact
numbers. That belongs with
[`2026-09-01-board-reads-stale-triage`](../2026-09-01-board-reads-stale-triage.md).
