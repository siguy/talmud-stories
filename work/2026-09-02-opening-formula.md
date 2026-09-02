---
title: Include the introducing formula in the story start — Jeff ruled, so build it
capability: [boundaries]
tractate: []
blocked_by: []
awaiting: []
writes: [src/story_detector_v11.py, tests/expert_boundary_targets_2005.json, tests/expert_boundary_targets_2005_kiddushin.json, tests/expert_boundary_targets_2005_gittin.json]
finding: docs/findings/2026-09-02-jeff-answers-gittin.md
superseded_by:
---

# Include the introducing formula in the story start

**Self-contained.** Read [`FRAMEWORK.md`](../FRAMEWORK.md), then
[`2026-09-01-gittin-boundary-analysis`](../docs/findings/2026-09-01-gittin-boundary-analysis.md)
— which **rejected** this rule — and then
[`2026-09-02-jeff-answers-gittin`](../docs/findings/2026-09-02-jeff-answers-gittin.md),
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
