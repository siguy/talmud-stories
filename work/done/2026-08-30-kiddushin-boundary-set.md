---
title: Build a blind Kiddushin boundary set
capability: [boundaries]
tractate: [kiddushin]
blocked_by: []
awaiting: []
finding: docs/findings/2026-08-31-kiddushin-boundary-set.md
superseded_by:
---

# Build a blind Kiddushin boundary set

**`NEXT/05` is DONE** — ground truth is
[`results/expert_lists/kiddushin_2005.json`](../results/expert_lists/kiddushin_2005.json).
Read `STATUS.md` and `FRAMEWORK.md`.
**Capability: 4 Boundaries.** **No API calls.**

## What this fixes

Kiddushin's boundary score today is **60% / 73% on 15 targets, all of them corrections**
— cases we already got wrong — with a **±7 point** run-to-run noise band. One target is
worth 6.7 points. That gate cannot adjudicate anything.

Ketubot solved this exact problem on 2026-08-30: aligning Jeff's verbatim story text
against the Sefaria Hebrew produced **294 blind boundary targets** and dropped the noise
floor to **zero**. Same method, same tooling, different tractate.

## Method

1. Run `scripts/build_boundary_testset_2005.py` against the Kiddushin stories filtered
   to `blind == true` and `duplicate_of == null` — **89 stories**, `--tractate Kiddushin`.
   The five `in_appendix` entries are excluded: their text came from our own runs, so a
   boundary target built from them would be graded against a boundary we chose.
2. Expect roughly 2 targets per story, so ~180. Report `align_fraction` and `bracket_ratio`
   distributions; Ketubot aligned 147 of 149 at a median 99% of letters matched.
3. Measure `exact_clause_edge`. On Ketubot **87%** of Jeff's boundaries fall on a clause
   edge, which set the ceiling for clause-anchored spans. If Kiddushin differs, the
   ceiling differs.
4. Cross-check against the existing 15 correction targets, broken out by direction. On
   Ketubot the two sources agreed on starts and split on ends.
5. Re-measure the noise floor: run the same code twice and report the spread (Lesson 22).

## How you know it worked

A Kiddushin boundary score on a blind set, with its noise floor stated. The old
15-target number is retired, not averaged with the new one.

## Guardrails

- Report corrections and blind sets **separately, never pooled** (Lesson 24). They
  answer different questions.
- Watch the clause-edge measurement: a first attempt on Ketubot said 61% fell mid-clause
  and that was an artifact — clause ranges run past the closing full stop while Jeff's
  text ends on a letter. The honest test is whether any Hebrew *letter* is left outside.
- Kiddushin's end boundaries inherit the open question with Jeff. Do not tune ends
  against this set until he answers.

## Outcome

**Done 2026-08-31.** →
[`docs/findings/2026-08-31-kiddushin-boundary-set.md`](../docs/findings/2026-08-31-kiddushin-boundary-set.md)
· set: `tests/expert_boundary_targets_2005_kiddushin.json`

**176 targets** from 88 of 89 blind stories (median 99.3% of Jeff's letters aligned;
1 rejected, 33a `weak_alignment`). 130 scorable.

| | old: corrections, n=15 | new: blind, n=130 |
|---|---|---|
| Wave 5 clause spans | 60% / 73% | **85% / 91%** |
| shipped (untrimmed) | 13% / 47% | **77% / 85%** |
| noise floor, same code twice | **±7 pts** | **0.77 pt on hit, 0 on hit+near** |

**The noise floor collapsed for the reason predicted, and the demonstration is exact:**
across the two identical runs **one target** changes verdict — Kiddushin 66b seg 0,
NEAR→HIT. On 15 targets that flip is 6.7 points and reads as a result; on 130 it is 0.77.
Same noise, same single target, different denominator. The gate can now adjudicate.

**Kiddushin is the better tractate for boundaries, not the worse one** — 85% / 91%
against Ketubot's 80% / 84%, and above the gate on the *shipped untrimmed* output alone.
Every document in this repo said the opposite; all of them were quoting the 15-target
exam. The old number is retired, not averaged.

**The clause-edge ceiling generalizes: 88% Kiddushin against 87% Ketubot** — and split by
direction, ends are 95%/96% clause-aligned while starts are 80%/79%. **The residual 12-13%
is a start problem**, which is new and tells a finer splitter where it would pay.

**Cross-check (item 4) came back thinner than Ketubot's** and is reported as such: only 14
boundaries overlap the corrections set against Ketubot's 32; agreement 2/3 starts, 8/11
ends. Ketubot's clean "agree on starts, split on ends" does not reproduce, and 3 start
boundaries cannot decide it. Two of the three end disagreements run the direction
Lesson 24 predicts; that is recorded as a count of three, not as evidence.

**Guardrails, as followed.** Corrections and blind reported separately, never pooled
(Lesson 24) — and a latent violation was found and fixed: `score_boundary_targets.py`
classified sources by the literal filename `expert_boundary_targets_2005.json`, so the new
set would have been *labelled a corrections set*. Clause-edge measured with the letter
test, not string equality. Ends were **measured, not tuned**, pending Jeff — scored as an
upper bound under the standard Simon settled, where trimming halves the definite
overshoots (13 → 6) while also raising exact matches (48 → 51), and *later than his 2005
boundary* is wrong under either answer he gives. The Ketubot build was verified
**byte-identical** before any Kiddushin number was read (Lesson 11).
