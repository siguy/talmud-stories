---
title: Consensus 1b — re-run the phase 1 test on the corrected register (R-C0 restored, R-C5 gloss removed)
capability: [classification, review]
tractate: [ketubot, kiddushin, gittin, yevamot]
blocked_by: []
awaiting: []
writes: [results/consensus/phase1/full_v2_gemini.json, results/consensus/phase1/full_v2_claude.json, results/consensus/phase1/full_v2_gemini_repeat.json, results/consensus/phase1/full_v2_claude_repeat.json, docs/findings/2026-09-28-consensus-phase1.md]
finding: docs/findings/2026-09-28-consensus-phase1.md
superseded_by:
---

# Consensus 1b — the phase 1 test, on the corrected register

**Self-contained.** Read the finding [`consensus-phase1`](../docs/findings/2026-09-28-consensus-phase1.md) in full — §7 is why this
exists — then the plan (`docs/history/2026-09-28-PLAN-consensus-at-scale.md` §4, whose
go/no-go is unchanged). **Do not touch Eruvin.**

## Before you start — two things only Simon can do

- **Gemini:** the project hit its **monthly spend cap** on 2026-09-28 (AI Studio → spend).
- **Anthropic:** the account is **out of credit** (Console → billing). Phase 1 cost $8.94
  for 403 Claude calls (~$0.022 each at effort `medium`); this item needs ~2,000 → ~$45.
  Raise the item's cap: `BUDGET_USD` in `scripts/judge_labelled_spans.py` counts every
  earlier run's Claude spend against it.

## Method

The register changed on 2026-09-28 (R-C0 added, R-C5 corrected), so the prompt sha
changed and every answer must be new. Same code, same labels (`labels.json`).

1. Gemini, full set — **resumes** the stopped run (its 997 rows are `failed`, 429 cap):
   `python3 scripts/judge_labelled_spans.py run --set full --backend gemini --out results/consensus/phase1/full_v2_gemini.json`
2. Claude, full set: `--backend claude --out results/consensus/phase1/full_v2_claude.json`.
3. **A same-prompt repeat of each** (`*_repeat.json`) — Claude's spread has never been
   measured (finding §8); Opus 5 takes no temperature.
4. Report with `report`, and add to the finding: the §4 table; the 47 list misses and the
   10 agreed-`not`s of v1, one by one — which moved; his `no`s — did any flip to `story`
   (the cost of the correction); agreement **by stratum** (never pooled only).

## How you know it worked

The §4 table gives go or no-go. Label it **same-data**: the register was corrected after
seeing these failures, so a pass is *indicated*; the phase 2 audit is the real test.

## When done

Update the finding (§10), `## Outcome`, `python3 scripts/board.py finish 2026-09-28-consensus-1b-corrected-register`.
