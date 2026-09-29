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

## Before you start

- **Money: done (Simon, 2026-09-29).** The Gemini monthly cap was raised and the Anthropic
  account has credit. `BUDGET_USD` in `scripts/judge_labelled_spans.py` is **75** — it
  counts every earlier run's Claude spend in `results/consensus/phase1/` ($8.94), and this
  item needs ~$44 (full + same-prompt repeat at ~$0.022/call). Always `--dry-run` first.
- **Labels: current.** `results/consensus/phase1/labels.json` was rebuilt on 2026-09-29
  after the register changed; only `cited_in_rules` moved (18 spans — the corrected R-C0 /
  R-C5 now quote those pages as cases). Report cited and not-cited separately, as before.
- **The reading of old verdicts** now lives in `scripts/verdict_reading.py` (shared with
  the rulers) — behaviour identical to phase 1.

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
