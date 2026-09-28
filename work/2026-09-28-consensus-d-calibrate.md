---
title: Consensus D — measure consensus against Jeff; set the tiers
capability: [classification, review]
tractate: [yevamot, gittin, ketubot, kiddushin]
blocked_by: [2026-09-28-consensus-a-calibration-set, 2026-09-28-consensus-b-pooled-recall, 2026-09-28-consensus-c-rule-panel]
awaiting: []
writes: [scripts/calibrate_consensus.py, results/consensus/calibration/, tests/test_calibrate_consensus.py]
finding:
superseded_by:
---

# Consensus D — calibrate

**Self-contained.** Read the plan [`consensus-at-scale`](../docs/history/2026-09-28-PLAN-consensus-at-scale.md) §3c, §4 and §5 — the gates
there were fixed on 2026-09-28, before this measurement. Do not move them to pass.

## Method

1. Join panel output (C) on the pools (B) to the calibration set (A) **by overlap**;
   report every calibration row that matched no candidate, and why (Lesson 36).
2. For each candidate compute: `found_in` k/N, Gemini decision, Claude decision, any
   `unsure`. Fix the tier rule (plan §3c) — **write the k threshold down before step 3**.
3. On **held-out BLIND** rows (headline) and CIRCULAR rows (separately):
   - agreement of the consensus-story tier with his labels, with a 95% interval;
   - stories on his lists that land in consensus-not (the costly error);
   - Gemini vs Claude agreement, and which one agrees with him more where they split;
   - per judge: agreement with his reasons where his notes name one;
   - contested-queue size per tractate.
4. Answer the open item
   [`extra-story-discriminator`](2026-09-03-extra-story-discriminator.md)'s claim with
   this: does the panel separate his yes/borderline from his no among **unlisted**
   Gittin proposals better than the confidence tier (which does not at all)? Record it
   there.

## How you know it worked

Plan §5 gate D, both rows. If the quality row fails, the panel is used only to rank the
queue and nothing is published as consensus — say so in the finding.

## Guardrails

- Thresholds are principled or they are reported as tuned (Lesson 37).
- Nothing enters a golden.

## When done

Finding `docs/findings/<date>-consensus-calibration.md`, `## Outcome`,
`python3 scripts/board.py finish 2026-09-28-consensus-d-calibrate`.
