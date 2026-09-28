---
title: Consensus 2 — the first Yevamot round under consensus (contested + audit)
capability: [review, classification]
tractate: [yevamot]
blocked_by: [2026-09-28-consensus-1-test-the-bet, 2026-09-28-review-page-scope-and-quote]
awaiting: []
writes: [scripts/pool_runs.py, scripts/route_consensus.py, tests/test_pool_runs.py, results/consensus/phase2/, validation/ui/, comms/, comms/JEFF.md, scripts/build_yevamot_golden.py, results/canonical/yevamot_canonical.json, tests/test_bookkeeping.py]
finding:
superseded_by:
---

# Consensus 2 — the Yevamot round

**Self-contained.** Read the plan [`consensus-at-scale`](../docs/history/2026-09-28-PLAN-consensus-at-scale.md) §5, the phase 1 finding,
and [`comms/JEFF.md`](../comms/JEFF.md). **Only on a phase 1 go.**

## Method

1. **Pool** (`scripts/pool_runs.py`) the three same-code Yevamot runs on disk:
   `results/v11/twin_pass/yevamot_full_twinall.json`, `yevamot_full_twin2.json`,
   `yevamot_full_twin2_r2.json`. Union by segment overlap, **not transitively** (test the
   A∩B, B∩C chain). Each candidate: `found_in`, each run's class and span.
   `mishnah_stories[]` is read and kept as its own tier, with a comment saying so.
2. **Judge** every candidate with phase 1's prompt on both models.
3. **Route** (`scripts/route_consensus.py`): consensus = both agree, neither unsure;
   contested = the rest. Page = **≤25 contested** (ranked: splits citing a rule he has
   never ruled on, then fewest `found_in`) **+ ~5 consensus-story + ~5 consensus-not**
   drawn at random, shuffled together, audit items not marked. Build it with the axis
   review UI (after `review-page-scope-and-quote`); check it in the browser — Hebrew +
   English, story highlighted.
4. **Email draft** in `comms/` (Simon sends): what changed, in one line;
   `jeff:review-error-rate` asked with phase 1's indicated figure; `jeff:scope-edges`.
5. **When he answers:** build `yevamot_canonical.json` with a builder on the
   `build_gittin_golden.py` pattern (verdicts first, then his list, `label_source`
   on every entry — **never** a machine verdict); record audit agreement per tier; each
   disagreement with the judge → a regression case; a reason STORY_RULES lacks → a
   candidate rule in his words. Update `GOLDEN_COUNTS`.

## Guardrails

- Never tell him which items are audit.
- ≤35 items on the page; the rest wait.
- Blind lists untouched; Eruvin untouched.

## When done

Finding `docs/findings/<date>-consensus-yevamot-round.md`, `## Outcome`,
`python3 scripts/board.py finish 2026-09-28-consensus-2-yevamot-round`.
