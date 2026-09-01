---
title: Two board.py loaders report absence instead of what the artifact holds
capability: [classification, review]
tractate: [ketubot, kiddushin]
blocked_by: []
awaiting: []
finding: docs/findings/2026-09-01-board-guards-verify-the-wrong-property.md
superseded_by:
---

# Two board.py loaders report absence instead of what the artifact holds

**Self-contained.** A fresh session executes this with no other context.
Read [`FRAMEWORK.md`](../../FRAMEWORK.md) first, then this.

## The claim to test / the problem

Two loaders in `scripts/board.py` print a smaller number than the file holds, and both
print it as an ordinary value rather than as a failure to read:

1. **`expert_lists()`** keys rows `f.stem.split("_")[0]`, so `kiddushin_2005.json` and
   `kiddushin_comments_harvested.json` both key to `'kiddushin'` and the second overwrites
   the first. It then sizes whatever survived with the story-list formula. Net effect: the
   **Ground truth on hand** table never showed the Kiddushin blind list — the denominator
   behind every Kiddushin number on the board — and showed
   `0 parsed · 0 blind · 0 count for recall` in its place.
2. **`_verdict_count()`** counts list entries with a *truthy* `feedback_type`, so the
   2026-01-08 round reads **24** where the file states `"reviewed_count": 25`. The dropped
   entry has `feedback_type: null` and a note in which Jeff states a display defect and
   **quotes the Hebrew of the story the excerpt contains** — the most informative verdict
   in the round.

Both sat behind a passing `board.py --check` and a passing `test_bookkeeping.py`.

## Method

- Key `expert_lists()` rows by **full stem**; dispatch on shape (`stories` → story list,
  `remarks` → comment harvest, else **unrecognised**) and size each in its own units.
  An unrecognised file is named with its top-level keys and marked `**UNKNOWN**`, never
  sized at zero — zero-because-empty and zero-because-unrecognised must not share a
  representation (Lesson 38).
- Adopt `measure_recall_vs_expert_list.load_expert()`'s filter exactly: drop
  `duplicate_of` entries **before** counting flags, and print the duplicate that was
  dropped. Counting over the raw list gives 91 where the harness denominator is 90.
- Count a verdict by whether it carries a judgement **field**, not a truthy one.

## How you know it worked

Every assertion watched fail against `git show HEAD:scripts/board.py` first (Lesson 31).

## Guardrails

- Do not "fix" the 91/90 gap by editing `kiddushin_2005.json`. The flags are correct; the
  board was applying them wrongly. The list is expert provenance and is not ours to edit.
- Do not widen `_is_verdict` until it counts blank rows — a round must not inflate.
- This item touches presentation only. **No measured value may move.** If one does, stop:
  that is [`board-reads-stale-triage`](../2026-09-01-board-reads-stale-triage.md)'s territory.

## Outcome

**DONE, 2026-09-01. Both fixed; one turned out to be substantially worse than filed.**
→ [`board-guards-verify-the-wrong-property`](../../docs/findings/2026-09-01-board-guards-verify-the-wrong-property.md)

**The comment-harvest row was the symptom, not the defect.** It was filed as "a file
renders as three zeros". Running the pre-fix loader with `ROOT` patched showed the real
behaviour: two files on disk, **one row returned**, and the row was the harvest. The
Kiddushin blind list was not mis-sized — it was **absent**, silently replaced. The zeros
that made the table look merely untidy were what a reader saw *instead of* the 89-blind /
90-for-recall denominator behind every Kiddushin recall figure the project quotes. Filing
it by its appearance understated it; the collision was found only by running the old code
rather than reading it.

**The verdict counter reproduced the shape of the lesson it was written for.** L-038 was
bought by this exact round being skipped for eight months on an `isinstance` guard. The fix
recovered the round and then miscounted it, dropping the one entry where Jeff declined the
dropdown and answered in prose. A guard against silent dropping is not the same as not
silently dropping.

**One thing deliberately not done.** The `counts_for_recall` flag reads 91 over the raw
list against a harness denominator of 90. Chased and resolved as **correct**: the harness
drops the duplicate before applying the flag. No defect — but the board had to adopt the
same order, or this fix would have shipped a fresh 91-vs-90 disagreement while claiming to
remove one. That is why `duplicates_dropped` is now printed rather than merely subtracted.

**No measured value moved**, as the guardrail required: `STATE.md`'s only changes are the
ground-truth table (a row restored, a row re-sized) and the January round 24 → 25.

**12 tests** in `tests/test_board_reports_what_it_holds.py`, each watched fail against the
pre-fix module. Left for [`board-reads-stale-triage`](../2026-09-01-board-reads-stale-triage.md):
the third and largest defect, which no test here can reach, because the generator is honest
about an artifact that is stale about the code.
