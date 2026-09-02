---
title: Include the introducing formula in the story start — Jeff ruled, so build it
capability: [boundaries]
tractate: []
blocked_by: []
awaiting: []
writes: [src/story_detector_v11.py, scripts/apply_opening_formula.py, scripts/annotate_boundary_rules.py, scripts/score_boundary_targets.py, tests/test_opening_formula.py, tests/expert_boundary_targets_2005.json, tests/expert_boundary_targets_2005_kiddushin.json, tests/expert_boundary_targets_2005_gittin.json, docs/STORY_RULES.md, docs/capabilities/4_boundaries.md, CLAUDE.md]
finding: docs/findings/2026-09-02-jeff-answers-gittin.md
superseded_by:
---

# Include the introducing formula in the story start

**Self-contained.** Read [`FRAMEWORK.md`](../../FRAMEWORK.md), then
[`2026-09-01-gittin-boundary-analysis`](../../docs/findings/2026-09-01-gittin-boundary-analysis.md)
— which **rejected** this rule — and then
[`2026-09-02-jeff-answers-gittin`](../../docs/findings/2026-09-02-jeff-answers-gittin.md),
which is why it is back.

## The claim to test

Jeff, 2026-09-01: the formulae *"are not technically part of the stories. But they are
important, as, for example, `תניא` indicates the Talmud thinks the story is Tannaitic…
If not too much trouble, we should include them."*

We measured this rule the day before at **9 targets fixed, 8 broken**, and dropped it as a
wash. His answer re-reads the 8: they are targets where *his own* start sits after the
formula, and *"the lists were sloppy and preliminary, and we had not worked this out."*
Re-measured across all four blind sets: **10 fixed, 10 ruler corrections, 17 late starts
that the formula does not explain.**

## Method

1. A deterministic pass over a finished run: if the clause immediately before a story's
   start clause, in the same segment, is a citation or attribution formula, extend the
   start to it. **Only one clause, and only backwards.**
2. The formula list is drawn from the cases he named plus the ones the blind sets show:
   `תניא` · `תנו רבנן` · `תא שמע` · `מיתיבי` · `גופא` · `אמר רב…` · `אמר ר׳…` ·
   `כי אתא רב דימי` · `בעו מיניה` · `שאלו` · `משתעי` · `דרש`. **Count how many of his
   *other* boundaries each token touches before adding it** (Lesson 27).
3. Score before and after on all four blind sets, reported per set (Lesson 24).
4. **Annotate the 2005 target files**: a start target that begins after an introducing
   formula no longer defines the right answer. Add the flag, do not silently move the
   target — a boundary target must remain an extent *Jeff* chose.

## How you know it worked

Starts improve by ~10 across the four sets, ends unchanged, and the 17 unexplained late
starts are still reported as unexplained rather than absorbed.

## Guardrails

- This is a **deterministic post-processor on a text-internal decision**, the shape
  Lesson 15 forbids — the difference is that the expert stated the rule in words, so it is
  principled and not fitted. Say so in the finding, and keep the scope to one clause.
- Do not re-baseline the golden. Score with `score_boundary_targets.py` only.

## Outcome

**Shipped 2026-09-02.** `extend_start_over_opening_formula()` runs as Stage 4l, and
`scripts/apply_opening_formula.py` applies it to a finished run for nothing.

**Measured, both standards, because the two disagree and that is the point:**

| | as his 2005 list is written | under the rule he stated in 2026 |
|---|---|---|
| Gittin | 84% → 84% | **82% → 86%** |
| Kiddushin | 85% → 85% | **84% → 88%** |
| Ketubot 61-112 | 80% → 79% | **77% → 82%** |

Against the lists as written the change is **+10 / −11**, and **every one of the 11
losses is a target whose own start excludes a formula** — the population he called
"sloppy and preliminary". That is not a regression; it is the ruler and the rule
disagreeing, which is Lesson 24 in a new place.

**Nothing in his data was moved.** `scripts/annotate_boundary_rules.py` marks 30 start
targets across the three blind sets as `included` or `excluded`, and
`score_boundary_targets.py --standard jeff-2026` reads the annotation. Both numbers come
from one file and both are reproducible.

Two things came out differently from the brief:

- **The formula list needed a verb-final case.** `רב חנין משתעי:` puts the verb last, so a
  prefix test alone missed the whole "X related:" family — 2 of the 10 corrected starts.
- **A length guard does the real work.** `אמר רב יהודה אמר רב:` introduces; the same words
  followed by `מעשה ב…` are the story. Without the ≤8-word guard the rule swallows
  narrative, which is exactly how the 2026-06-03 regex trimmer failed.

**Not fixed:** 17 late starts across the four sets that the formula does not explain, and
the segment-level misses (Gittin 55b, 56a, 56b, 57a) where our story starts on a different
*segment* than his — a clause rule cannot reach those.
