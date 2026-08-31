---
title: Gittin — detection
capability: [detection]
tractate: [gittin]
blocked_by: [2026-08-30-gittin-triage, 2026-08-30-two-amud-header-parser]
awaiting: []
writes: [results/detection/gittin.json, src/story_detector_v11.py]
finding:
superseded_by:
---

# Gittin — detection

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
