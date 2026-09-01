---
title: Fix the triage bypass, then price the review cost of examining more pages
capability: [triage, detection]
tractate: [ketubot, kiddushin]
blocked_by: []
awaiting: []
finding:
superseded_by:
---

# Fix the triage bypass, then price the review cost of examining more pages

**Self-contained.** Read [`FRAMEWORK.md`](../FRAMEWORK.md), then
[`2026-09-01-triage-recall-price.md`](../docs/findings/2026-09-01-triage-recall-price.md),
then this. **Capability: 1 Triage.** **Depends on Jeff: no.**
**Cost: one code fix, then ~224 Stage 2 calls — pennies.**

Successor to [`triage-recall-price`](../work/done/2026-08-30-triage-recall-price.md), which priced
the **recall** side of the trade from artifacts on disk and found that the archived
ablation cannot price the other side.

## The problem

`skip_triage=True` does not bypass Stage 1. It stamps every segment `DELIBERATION`:

```python
# story_detector_v11.py:1058-1064 — identical in v7:658, v8:727, v9:845, v10:1014
elif skip_triage:
    # Generate default triage (all DELIBERATION) so detection still works
    triage_results[ref] = [EventType.DELIBERATION] * n_segs
```

Stage 2 renders that into its prompt as `[DELIBERATION] Seg N:` under a header saying each
segment "has been pre-classified by event type" (`:75`), and post-processing's
`rule3_v6_ensemble` demotes proposals for sitting on a page with "0 NARRATIVE_EVENTs" —
true of every page under the stub. Measured on the one archived run: **6 stories lost on
pages both arms examined**, and `NOT_A_STORY` 2 → 44 of 74 → 91 proposals.

So the flag answers a different question — *does Stage 2 need labels?* — and any experiment
using it to mean "no triage" is contaminated, including
`results/v7/ablation_v7_no_triage.json` and the 2026-02-13 conclusion drawn from it.

## Method

1. **Fix the bypass.** `skip_triage` must override the *skip decision only*, keeping real
   labels: compute or load `triage_results` as normal, and gate solely on the
   `pages_to_process` branch. Where no cached labels exist, that means running Stage 1
   anyway and ignoring its verdict — Stage 1 is the cheap stage; the saving was never
   there. Fix in `src/story_detector_v11.py` only; **never edit the frozen lower versions**
   (CLAUDE.md). Consider renaming to `examine_all_pages` so the flag stops implying it
   skips Stage 1.
2. **Guard it.** A test that fails on the old behaviour: with `skip_triage=True` and real
   cached labels supplied, assert the labels reaching `build_prompt` are the cached ones,
   not all-DELIBERATION. Write it, watch it fail, then fix (Lesson 31).
3. **Re-run the ablation properly** on Ketubot 2a–60b, the range where a triaged v7 twin
   exists, using the cached labels in `results/v7/event_triage_2-60.json`.
4. **Then price the review cost.** Run the corrected bypass over the 124 discarded Ketubot
   and 100 discarded Kiddushin pages and count **proposals per story recovered** — the
   number §5 of the finding says is still missing. Review throughput is the project's
   binding constraint, so a rule that recovers 3 stories and adds 60 items to Jeff's queue
   is a worse trade than the recall table alone suggests.
5. **Regenerate today's baseline before comparing** (Lesson 11) and **repeat one arm with
   unchanged code** to get a noise floor before attributing anything (Lesson 22).

## How you know it worked

- The guard test fails on `main` and passes after the fix.
- A corrected with/without table where turning triage off **never loses a story on a page
  both arms examined** — the impossible result that exposed the original.
- Proposals per story recovered, stated for both tractates, alongside the recall ceilings
  already measured (1 per 41 Ketubot, 1 per 25 Kiddushin).

## Guardrails

- **Experiment, not a ship.** Do not change the shipped keep-condition in this item. The
  2026-09-01 finding already measured that no threshold relaxation recovers anything, so a
  loosening here would be both unpriced and known not to work.
- Write to `results/v11/triage_bypass/`; never overwrite `wave4_notrim` or the v7 files.
  `results/v7/ablation_v7_no_triage.json` is contaminated but is **evidence** — keep it.
- Run `evaluate_golden.py` only with `--output <scratch path>` (CLAUDE.md rule 4).
- Every outcome bucket must be a partition and must be asserted (Lesson 21).

## When done

Finding → `docs/findings/<date>-triage-bypass-and-precision.md`. Update `STATUS.md` and
[`docs/capabilities/1_triage.md`](../docs/capabilities/1_triage.md) — capability **1
Triage** — including whether the 2026-02-13 "single largest accuracy driver" claim survives
a clean re-run.
