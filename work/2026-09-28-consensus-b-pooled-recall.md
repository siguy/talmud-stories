---
title: Consensus B — pooled recall: N runs, no page skipped, found-in-k-of-N
capability: [detection, triage]
tractate: [yevamot, gittin]
blocked_by: []
awaiting: []
writes: [scripts/run_new_tractate.py, scripts/pool_runs.py, results/consensus/runs/, results/consensus/pools/, results/recall/, tests/test_pool_runs.py]
finding:
superseded_by:
---

# Consensus B — pooled recall

**Self-contained.** Read [`FRAMEWORK.md`](../FRAMEWORK.md), the plan
[`consensus-at-scale`](../docs/history/2026-09-28-PLAN-consensus-at-scale.md) §3a, and
[`detector-is-not-deterministic`](../docs/findings/2026-09-27-detector-is-not-deterministic.md).

## The claim to test

Pooling N independent runs, with no page skipped by triage, finds measurably more of
Jeff's stories than one run — and the gain per extra run tells us what N to ship.

## Method

1. **Wire the flag.** `scripts/run_new_tractate.py`'s docstring promises
   `--examine-all-pages`; the argument does not exist. Add it, passing through to v11's
   `examine_all_pages` (which only ever ADDS pages — `tests/test_examine_all_pages.py`).
2. **Run** Yevamot and Gittin, 5 runs each, twin pass on (the default), examine-all-pages
   on, to `results/consensus/runs/<tractate>_r{1..5}.json`. Do not touch the shipped
   `results/v11/<tractate>/*.json`.
3. **Pool** (`scripts/pool_runs.py`): union proposals by segment overlap (Lesson 36 —
   never exact keys); each pooled candidate records `found_in` (which runs), each run's
   classification and span, and the widest/narrowest extent. Write
   `results/consensus/pools/<tractate>_pool.json`. Unit-test the union on synthetic runs.
4. **Measure** with `measure_recall_vs_expert_list.py` (exact matcher) into suffixed
   recall files: each single run (report min / max / spread), and the pool at N = 1…5
   (every subset size, mean). Report **Triage and Detection separately**, and the
   candidate count at each N.
5. Per story on his lists: found in how many of 5. Name the fragile ones.

## How you know it worked

Plan §5 gate B: pooled-5 recall ≥ best single run + 2 stories on at least one tractate,
with the single-run spread reported beside it. The curve of recall and candidate count
against N is the deliverable either way.

## Guardrails

- Same code for all runs (record the commit and `run_fingerprint` per run).
- A failed page is marked, not emptied (the checkpoint code already does this) — count them.
- Do not promote anything to the board's unsuffixed recall files.

## When done

Finding `docs/findings/<date>-pooled-recall.md`, `## Outcome`,
`python3 scripts/board.py finish 2026-09-28-consensus-b-pooled-recall`.
