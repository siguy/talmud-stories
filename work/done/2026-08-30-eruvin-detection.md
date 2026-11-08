---
title: Eruvin — detection
capability: [detection]
tractate: [eruvin]
blocked_by: [2026-08-30-eruvin-triage, 2026-08-30-two-amud-header-parser]
awaiting: []
writes: [results/triage/eruvin.json, results/v11/eruvin/eruvin_v11.json, results/v11/eruvin/eruvin_v11_r2.json, results/recall/eruvin_jeff2005_matches.json, results/recall/eruvin_jeff2005_matches_r2.json, results/recall/eruvin_strict.json, results/recall/eruvin_strict_r2.json]
finding: docs/findings/2026-11-08-eruvin-v11-run.md
superseded_by:
---

# Eruvin — detection

**Self-contained.** Read [`FRAMEWORK.md`](../../FRAMEWORK.md) and
[`docs/technical/new_tractate_workflow.md`](../../docs/technical/new_tractate_workflow.md),
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

## Outcome

**DONE 2026-11-08** (shipped detector v11, two runs). Triage cached in `results/triage/eruvin.json`; runs in
`results/v11/eruvin/`. Recall vs Jeff's BLIND 74: 91.9% end-to-end, Triage 97.3%, Detection given
page survived 94.4%, identical in both runs (indicated, n=2). 6 misses, same both runs: 2 triage-lost
(14b, 32b), 4 examined-nothing-proposed (13b, 53b x2, 60a). Run 2 reused run 1's triage cache, so triage is one
draw. See [the finding](../../docs/findings/2026-11-08-eruvin-v11-run.md).
