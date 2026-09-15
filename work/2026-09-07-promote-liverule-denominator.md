---
title: Decide what the board's recall cells describe — the artifacts we hold or the code we ship
capability: [triage, detection]
tractate: [ketubot, kiddushin]
blocked_by: []
awaiting: []
writes: [scripts/board.py, results/recall/, STATE.md, STATUS.md]
finding:
superseded_by:
---

# The board reports the artifacts; the code says something else

**Self-contained.** Read
[`2026-09-07-triage-live-rule-remeasured`](../docs/findings/2026-09-07-triage-live-rule-remeasured.md).
**Not a measurement — a decision, with the measurement already done.** **Cost: none.**

## The problem

Two true answers, and the board can only print one:

| | artifacts we hold | code we ship today |
|---|---|---|
| Ketubot Triage | 96.6% | 98.0% |
| Kiddushin Triage | 95.6% | 97.8% |

The shipped **runs** were produced under the previous keep-rule. The shipped **code** uses
`>=1 NARRATIVE_EVENT`. The live-rule figures are measured, on the current matcher, and
live in `results/recall/*_jeff2005_matches_liverule.json` — but they come from a *splice*
that says of itself *"MEASUREMENT ARTIFACT… not a ship candidate"*.

CLAUDE.md pins the unsuffixed file as the recall denominator, so this cannot be settled by
renaming something.

## The three options

1. **Board reads the artifacts** (today). Honest about what exists; describes a pipeline
   nobody would run again.
2. **Board reads the live-rule variants.** Honest about the code; the denominator becomes
   a splice, and every downstream cell inherits a counterfactual.
3. **Board prints both, per row.** Costs a column and ends the ambiguity permanently.
   The coverage matrix already carries italic sub-rows for exactly this.

**Recommended: 3**, and only because this project has now been bitten three times by a
number that was right for the question it was built for and wrong for the one it was
quoted against.

## Deciding it

Needs Simon, at integration on main, with STATUS — not on a branch. Whichever is chosen,
`board.py` must state the rule and the matcher **in the cell**, and
`test_board_reports_what_it_holds.py` gets a case pinning it.

## When done

`## Outcome` here, then `python3 scripts/board.py finish 2026-09-07-promote-liverule-denominator`.
