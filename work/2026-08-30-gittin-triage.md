---
title: Gittin — triage
capability: [triage]
tractate: [gittin]
blocked_by: []
awaiting: []
writes: [results/triage/gittin.json]
finding:
superseded_by: work/done/2026-08-31-gittin-detection-run.md
---

# Gittin — triage

**Superseded, found 2026-09-03 while checking board coverage.** Triage actually ran as part of the 2026-08-31 first blind run (`results/triage/gittin.json`, commit d40411e), never under this item. The generic per-capability workflow (this file, plus -detection/-classification/-review-ui) was superseded by an ad-hoc single-run item before any of the four were started. Left open rather than deleted (CLAUDE.md: never delete a work item) but the work described here is done elsewhere.


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
