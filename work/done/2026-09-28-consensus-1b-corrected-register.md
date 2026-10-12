---
title: Consensus 1b — re-run the phase 1 test on the corrected register (R-C0 restored, R-C5 gloss removed)
capability: [classification, review]
tractate: [ketubot, kiddushin, gittin, yevamot]
blocked_by: []
awaiting: []
writes: [results/consensus/phase1/full_v2_gemini.json, results/consensus/phase1/full_v2_claude.json, results/consensus/phase1/full_v2_gemini_repeat.json, results/consensus/phase1/full_v2_claude_repeat.json, results/consensus/phase1/subagent/, results/consensus/phase1/compare_1b.json, scripts/judge_labelled_spans.py, scripts/judge_via_subagents.py, scripts/compare_consensus_1b.py, docs/findings/2026-09-28-consensus-phase1.md, work/2026-09-28-consensus-2-yevamot-round.md]
finding: docs/findings/2026-09-28-consensus-phase1.md
superseded_by:
---

# Consensus 1b — the phase 1 test, on the corrected register

**Self-contained.** Read the finding [`consensus-phase1`](../../docs/findings/2026-09-28-consensus-phase1.md) in full — §7 is why this
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

## Outcome

**2026-10-01. No-go again: same-data / indicated** (finding §10). Phase 2 stays blocked.

| §4 criterion | limit | run 1 | repeat |
|---|---|---|---|
| models agree (review spans) | ≥ 80% | 291/363 = 80.2% [75.8–83.9] | 295/364 = 81.0% [76.7–84.7] |
| agreed `story` on his `no` | ≤ 2 | **4** | **5** |
| list stories both call `not` | ≤ 2 | **9** of 444 | **8** of 445 |

- **What ran.** Gemini full (resumed) + repeat via the API, as specified. **The Claude arm was
  not run through the API:** on 2026-10-01 the account still refused every call (*"credit
  balance is too low"*, 997/997, $0), and Simon declined to fund API calls and chose Claude
  Code subagents instead. `scripts/judge_via_subagents.py` gives each subagent the exact
  system and per-span prompts and validates its answers with the same `ask()`. Differences,
  all recorded in §10a: Opus 5.5 not Opus 5, 25 spans per context (seeded shuffle; the
  repeat re-shuffles), no structured output. Span ids were hidden (a `list:` id is the
  label), and 5 spans an agent had not seen in full were found by auditing transcripts and
  re-judged.
- **What moved.** R-C0 fixed the miss it was aimed at: Gemini's `not` on his list stories fell
  47 → 10, and 20 of the 47 are now `story` under both models in both runs. It overshot on the
  other side: Gemini's `story` on his 130 `no`s rose 10 → 32 (13 of 18 on Gittin). Of the 10
  agreed `not`s on his `yes`es, 5 are now agreed `story`, 4 split, 1 unchanged.
- **Why it failed** (§10g). Every remaining error sits on a line the register does not settle.
  (1) Agreed `story` on his `no`: R-C0 has no line between an incident brought to a rabbi and
  *"a legal problem and answer"* (his words on Gittin 88a). That is `jeff:report-vs-incident`,
  and his Gittin 88a and Ketubot 50b notes are cases for it. (2) The 9 list `not`s: 4 rejected
  by his R-C2 (scholarly speech), 1 by his R-B4, and 4 by **our** wording (R-C5's
  "alluded-to incident" line; "a custom stays a custom"). His 2005 lists keep all 9.
- **Claude's spread, measured for the first time:** 6–8% of verdicts move between re-shuffled
  runs, about 20× Gemini the judge's. Both runs fail by more than that.
- **Not done, on purpose:** no change to STORY_RULES.md, the judge prompt or §4. Phase 2 not
  started; its `awaiting:` now names `jeff:report-vs-incident`, because closing this item
  cleared its `blocked_by`.
- Also fixed: the Claude budget tally crashed on `list_misses.json` (a list) before any call.

