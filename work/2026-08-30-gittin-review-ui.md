---
title: Gittin — review ui
capability: [review]
tractate: [gittin]
blocked_by: [2026-08-30-gittin-classification]
awaiting: []
writes: [validation/ui/gittin_review.html, validation/generators/]
finding:
superseded_by: work/done/2026-08-30-gittin-expert-round.md
---

# Gittin — review ui

**Superseded, found 2026-09-03 while checking board coverage.** The review UI Jeff actually used was the axis-review page (`validation/ui/axis_gittin_unlisted.html`, from `validation/generators/generate_axis_review_ui.py`), not `validation/ui/gittin_review.html` as this item declared — that path never materialized either. See `work/done/2026-08-30-gittin-expert-round.md`.


**Self-contained.** Read [`FRAMEWORK.md`](../FRAMEWORK.md) and
[`docs/technical/new_tractate_workflow.md`](../docs/technical/new_tractate_workflow.md),
which documents this sequence, then this.

## Method

See the workflow doc; this item is the handle and the ordering.

## Guardrails

- **Ask Jeff to keep his appendix separate BEFORE the first review round**, not
  after (Lesson 29). Once merged into his list it cannot be reconstructed, and the
  list stops being able to measure what we missed.
- Regenerate a same-day baseline before any comparison (Lesson 11).
- Report the corrections ruler and the neutral ruler separately (Lesson 24).

## When done

Finding to `docs/findings/`, add `## Outcome`, `git mv` to `work/done/`.
