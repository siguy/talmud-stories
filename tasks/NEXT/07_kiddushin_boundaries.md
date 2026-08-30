# NEXT 07 — A blind boundary set for Kiddushin

**`NEXT/05` is DONE** — ground truth is
[`results/expert_lists/kiddushin_2005.json`](../../results/expert_lists/kiddushin_2005.json).
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
