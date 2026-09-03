---
title: Encode Jeff's story criteria (was Wave 6)
capability: [classification]
tractate: []
blocked_by: []
awaiting: []
writes: [src/prompts/]
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

**His 2026-07-06 criteria contradict his own 2026-03-17 rulings.** The bucket they *point
at* is 110 of the 249 accepted golden entries (Ketubot 77, Kiddushin 33). The bucket they
**hit** is **6** — measured 2026-09-03, and the difference is the whole reason 6a exists.

> **Corrected 2026-09-03.** This section read *"applying the new rule mechanically would
> redefine 44% of the golden"* for five weeks, and it was the sentence that made this item
> look like the project's largest open question. 44% is the size of the bucket we had to
> *search*, not of the set that turns out to be affected. **A candidate count is not a
> blast radius**, and quoting one as the other is how an item gets ranked first on a
> number nobody measured.

## The three phases

- **6a — measure the blast radius.** ~~Never run.~~ **DONE 2026-09-03: the answer is 6,
  not 110** ([finding](../docs/findings/2026-09-03-speech-act-blast-radius.md)). 110 was
  the candidate bucket; 6 of them are speech-only, 2.4% of the accepted golden. And on
  reading those 6, **three are spans that stop before the action happens** — a Boundaries
  defect wearing a criteria costume. The criteria question is about **three entries**.
- **6b — ask Jeff.** Present the contradiction in his own words with 6a's count and 3–4
  examples: should those entries become NOT_A_STORY, stay LOW_CONFIDENCE, or take a new
  **borderline** status? Drafted, not sent. **Only 3 of the 6 are actually a 6b
  question** — 7a:1, 15a:0, 112a:11, all genuinely speech-only. The other three (17a:10,
  54a:22, 85a:13-14) are boundary bugs, not criteria cases, and go straight to a fix
  rather than a question.
  **Bundled into [`loose-credited-proposals`](2026-09-03-loose-credited-proposals.md)**
  as part of the single next review page, alongside the 11 loose-window cases and the
  Gittin extras — three separate asks would waste three of Jeff's replies on one round.
- **6c — implement.** **BLOCKED on 6b by design**, not by circumstance.

## Guardrails

- Conformance set is **TEST-ONLY, never few-shot** (Lessons 2, 8).
- Hard abort if either composite drops >0.02 below a same-day baseline (Lessons 5, 11).
- A post-hoc FP classifier is a *separate* job — it can never create a false negative, and
  can never recover one, which is what this item is for. Do not bundle them.

## When done

Finding to `docs/findings/`, add `## Outcome`, `git mv` to `work/done/`.
