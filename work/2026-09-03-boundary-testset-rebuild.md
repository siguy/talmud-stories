---
title: Rebuild the blind boundary sets on the exact matcher without dropping their annotations
capability: [boundaries]
tractate: [ketubot, kiddushin]
blocked_by: []
awaiting: []
writes: [tests/expert_boundary_targets_2005.json,
         tests/expert_boundary_targets_2005_kiddushin.json,
         scripts/build_boundary_testset_2005.py, scripts/parse_kiddushin_list.py,
         results/expert_lists/, docs/capabilities/4_boundaries.md,
         docs/findings/2026-09-03-boundary-testset-rebuild.md]
finding:
superseded_by:
---

# Rebuild the blind boundary sets on the exact matcher, without dropping their annotations

**Self-contained.** Read [`FRAMEWORK.md`](../FRAMEWORK.md), then
[the cutover finding](../docs/findings/2026-09-03-exact-matcher-cutover.md).

## The problem

`build_boundary_testset_2005.py` locates each expert story and then **sequence-aligns
inside that window**, so the window is not just an index: text offered to the aligner that
is not the story's is text it can align to. On the exact matcher it aligns **148/149**
Ketubot (was 147) and **89/89** Kiddushin (was 88), and 19 Ketubot / 1 Kiddushin existing
targets move — 16 of them the `ref` label only.

**The banked sets cannot simply be regenerated.** A fresh *4-gram* build does not reproduce
them either:

- **23 Ketubot targets carry `rule`, `rule_clause`, `rule_relation`** — fields the builder
  does not produce. They were annotated afterwards against
  [`docs/STORY_RULES.md`](../docs/STORY_RULES.md). A rebuild drops them silently.
- **16 more differ in `ref`**, because the two-amud daf attribution fix (2026-09-01)
  landed after the file was written.

So the file on disk is a build plus two later edits nobody can replay. That is the real
work here; the matcher is the easy part.

## Method

1. **Reproduce the annotations first, and prove it** — read the 23 `rule*` values, find
   what wrote them (or that a human did), and either regenerate them or carry them across
   on `(review_key, direction)` with a test that fails if any is lost.
2. Rebuild both sets with `--matcher exact` (already the default) and diff **every**
   moved target by name, as the recall reconciliation did.
3. Re-score the boundary numbers in `docs/capabilities/4_boundaries.md` — 80%/84% Ketubot
   and 85%/91% Kiddushin were measured on the old targets, so they are not comparable
   until re-scored the same day (Lesson 11).
4. Decide separately about `anchor_span_refs` and `parse_kiddushin_list.py`, which still
   locate with 4-grams. They assign an entry's **daf label**, not a measurement — but they
   write `results/expert_lists/*.json`, which is ground truth, so a change there is a data
   change and gets its own before/after count.

## How you know it worked

The rebuilt files contain **every** annotation the old ones did — asserted, not eyeballed —
and every moved target is named with its old and new value and a reason.

## Guardrails

- **Do not rebuild first and reconcile later.** The annotations are unrecoverable once
  overwritten; `git show HEAD:` is the only copy and a second rebuild will not bring them
  back.
- The 2005 sets are **blind ground truth**. Nothing about our output may influence a
  boundary in them (Lesson 29).
- The Kiddushin set is built with `--expert-filter blind` (89), **not** the recall filter
  (90): a boundary target must be an extent Jeff chose.

## When done

Write the finding, add an `## Outcome`, and
`python3 scripts/board.py finish 2026-09-03-boundary-testset-rebuild`.
