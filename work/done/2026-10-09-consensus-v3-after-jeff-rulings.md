---
title: Re-run both consensus judges on the register with Jeff's 2026-10-07 rulings
capability: [classification]
tractate: [ketubot, kiddushin, gittin, yevamot]
blocked_by: []
awaiting: []
writes: [results/consensus/phase1/full_v3_gemini.json, results/consensus/phase1/full_v3_claude.json, results/consensus/phase1/subagent/full_v3_claude/, results/consensus/phase1/compare_v3.json, scripts/compare_consensus_v3.py, src/story_detector_v12.py, work/2026-10-09-judge-answer-categories.md]
finding: docs/findings/2026-10-09-consensus-v3.md
superseded_by:
---

# Re-run both consensus judges after Jeff's 2026-10-07 rulings

**Self-contained.** Read [`FRAMEWORK.md`](../../FRAMEWORK.md) first, then this.

## The claim to test / the problem

His seven answers went into `docs/STORY_RULES.md`, which the judge carries as its whole
instruction. Did the two judges move toward him, and on what?

## Method

Same as `full_v2_*` in every respect but the register: `judge_register_v1.md`, the same
`labels.json`, `gemini-3-flash-preview` at T 0.1 thinking off, Claude as Opus 5.5 Claude Code
subagents, seed 1, batches of 25 (so each subagent saw the same batch-mates as v2). One run
each (Simon, 2026-10-09: full set, no sample, no repeat). Score with
`scripts/compare_consensus_v3.py`, twice: labels as run, and with his 2026-10-07 verdicts.

Also here: `src/story_detector_v12.py` — his rulings as abstract prompt wording. Written,
**not run**.

## How you know it worked

Read the §4 criteria and the tally side by side; v2's run-to-run spread (Claude 5.8% of
review spans moved on a same-prompt repeat) is the noise floor.

## Outcome

Done 2026-10-09 — see the finding. §4 still fails: agreement 80.2% → 75.5% (the judges drifted
apart, Claude much stricter), his-no→story 3 → 1, list stories rejected by both 8 → 14. The 8
ruled passages all answered his way. Eight newly rejected list stories are the open question
(over-reach of the R-C0 limit, or correct under his recent thinking?).

## Guardrails

The passages he ruled on are quoted in the register now — report criteria without them too.
