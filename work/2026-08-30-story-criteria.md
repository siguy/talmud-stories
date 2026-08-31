---
title: Encode Jeff's story criteria (was Wave 6)
capability: [classification]
tractate: []
blocked_by: []
awaiting: [jeff:speech-act-policy]
finding:
superseded_by:
---

# Encode Jeff's story criteria (was Wave 6)

**Self-contained.** Read [`FRAMEWORK.md`](../FRAMEWORK.md) §1.3, then this. Full design,
including the measured seed case and the gate table, is in
[`docs/history/2026-08-29-PLAN-wave6-story-criteria.md`](../docs/history/2026-08-29-PLAN-wave6-story-criteria.md)
— that file moved to `docs/history/` in the 2026-08-30 restructure because it is a plan,
**not because it is dead.** This item is the live handle on it.

## Why it is split three ways

Encoding [Jeff's 2026-07-06 rubric](../docs/findings/2026-07-06-jeff-story-definition-criteria.md)
looks like a prompt change. It is not — it is a question about what the dataset *means*,
and we cannot answer it for him.

**His 2026-07-06 criteria contradict his own 2026-03-17 rulings**, and the bucket they
point at is **110 of the 249 accepted golden entries** (Ketubot 77, Kiddushin 33 —
verified 2026-08-30). Applying the new rule mechanically would redefine 44% of the golden.

## The three phases

- **6a — measure the blast radius.** Classify each of the 110 LOW_CONFIDENCE golden
  entries on one axis: *does anything non-speech happen?* ~$0.10, needs nobody, changes
  nothing. **Never run.**
- **6b — ask Jeff.** Present the contradiction in his own words with 6a's count and 3–4
  examples: should those entries become NOT_A_STORY, stay LOW_CONFIDENCE, or take a new
  **borderline** status? Drafted, not sent.
- **6c — implement.** **BLOCKED on 6b by design**, not by circumstance.

## Guardrails

- Conformance set is **TEST-ONLY, never few-shot** (Lessons 2, 8).
- Hard abort if either composite drops >0.02 below a same-day baseline (Lessons 5, 11).
- A post-hoc FP classifier is a *separate* job — it can never create a false negative, and
  can never recover one, which is what this item is for. Do not bundle them.

## When done

Finding to `docs/findings/`, add `## Outcome`, `git mv` to `work/done/`.
