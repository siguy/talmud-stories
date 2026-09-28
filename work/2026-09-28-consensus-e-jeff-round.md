---
title: Consensus E — the first contested + audit page for Jeff
capability: [review]
tractate: [yevamot]
blocked_by: [2026-09-28-consensus-d-calibrate]
awaiting: []
writes: [scripts/route_consensus.py, validation/generators/generate_axis_review_ui.py, validation/ui/, comms/JEFF.md, tests/test_review_ui_symmetry.py]
finding:
superseded_by:
---

# Consensus E — the first round under consensus

**Self-contained.** Read the plan [`consensus-at-scale`](../docs/history/2026-09-28-PLAN-consensus-at-scale.md) §3d, the phase-D finding,
and [`comms/JEFF.md`](../comms/JEFF.md) ("Ask order").

## What to build and send

1. **Router** (`scripts/route_consensus.py`): tiers from D → a page of **≤25 contested**
   (ranked: unruled-rule splits first, then fewest-runs-found) **+ ~10 random consensus
   audit** items, shuffled together and **not labelled** as which is which (so the audit
   measures agreement, not deference).
2. **Review page** (`generate_axis_review_ui.py`, shared display core): add an
   **"a story, but out of scope"** answer (R-S1 — he had to say it in a note on
   2026-09-23), and fix the doubled Hebrew quote capture (Yevamot 105a,
   2026-09-23). Test in the browser: Hebrew + English, story highlighted (Critical Rule 1).
3. **The email** (draft in `comms/`, Simon sends): one line on what changed — *you now
   see only what two independent models disagree about, plus a random check* — and
   `jeff:review-error-rate` asked with the **measured** consensus agreement rate from D.
   Carry the free ask `jeff:scope-edges`.

## When his verdicts come back

- Into the golden as **his** labels (Yevamot: through the builder pattern of
  `build_gittin_golden.py`).
- Audit agreement recorded — this is the live consensus error rate.
- Each disagreement with a judge → a regression case; a reason no judge covers → a
  candidate rule in STORY_RULES, with his words.

## Guardrails

- Never tell him an item is "machine consensus" on the page — it biases the audit.
- The page is ≤35 items. If D produces more contested items, the rest wait for the next round.

## When done

Finding `docs/findings/<date>-first-consensus-round.md`, `## Outcome`,
`python3 scripts/board.py finish 2026-09-28-consensus-e-jeff-round`.
