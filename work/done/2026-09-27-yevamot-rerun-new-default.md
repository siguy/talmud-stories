---
title: Re-run Yevamot under the new default (twin pass on, 2026-09-25 wording)
capability: [detection]
tractate: [yevamot]
blocked_by: []
awaiting: []
writes: [results/v11/twin_pass/, results/recall/yevamot_jeff2005_matches_twin2.json]
finding: docs/findings/2026-09-27-yevamot-rerun-new-default.md
superseded_by:
---

# Re-run Yevamot under the new default

**Self-contained.** Read [`FRAMEWORK.md`](../../FRAMEWORK.md) first, then
[`2026-09-25-jeff-verdicts`](../../docs/findings/2026-09-25-jeff-verdicts-scope-commentary-reports.md).

## The claim to test / the problem

The twin pass went on by default on 2026-09-25 with a new question. That was measured
only by re-asking the 21 additions already on disk, which sees what the new wording
DROPS and not what it ADDS. A full run measures both, and gives an artifact under the
shipped default.

## Method

`scripts/run_new_tractate.py --tractate yevamot` with defaults (TWIN_PASS=1,
TWIN_TRIGGER=all, gemini-3-flash-preview, thinking off), cached triage, output to
`results/v11/twin_pass/yevamot_full_twin2.json` — NOT the shipped `yevamot_v11.json`.
Score with `measure_recall_vs_expert_list.py` (exact matcher) into a suffixed recall
file, beside the old twin run (`_twinall`) and the control (`yevamot_v11`).

## How you know it worked

- Recall vs the 2005 list (end-to-end and given-triage), story by story against `_twinall`.
- Twin additions by name: which of the 12 old additions survive, and any new ones.
- The 5 verdicts from 2026-09-23 checked against the new proposals.

## Guardrails

- Do not overwrite `yevamot_v11.json` or the unsuffixed recall file (the board reads it).
- Deterministic config (spread 0.0, 2026-09-09) — one run per arm.

## Outcome

**Done, 2026-09-27.** Detection 93.1% (95/102) under the new default, vs 94.1% old wording
and 89.2% with the pass off. The single loss is `yevamot_050` (78a:13), as predicted.
Extras off his list 8 → 6. Seven page-level Stage 2 proposals moved between runs —
suspected variation or code drift, unmeasured. Not promoted to the shipped artifact.
→ [finding](../../docs/findings/2026-09-27-yevamot-rerun-new-default.md)
