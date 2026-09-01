---
title: Fix skip_triage so it bypasses Stage 1 instead of faking its output
capability: [triage]
tractate: []
blocked_by: []
awaiting: []
finding:
superseded_by:
---

# Fix `skip_triage` so it bypasses Stage 1 instead of faking its output

**Self-contained.** Read [`FRAMEWORK.md`](../FRAMEWORK.md), then
[`2026-09-01-contaminated-no-triage-ablation.md`](../docs/findings/2026-09-01-contaminated-no-triage-ablation.md),
then this. **Capability: 1 Triage.** **Depends on Jeff: no.** **Cost: minutes, no API
calls** — the measurement this would have unblocked is already done by
[`2026-08-31-triage-recall-price.md`](../docs/findings/2026-08-31-triage-recall-price.md),
which routed around the flag rather than fixing it. What is left is the trap itself.

## The problem

```python
# story_detector_v11.py:1058-1064 — identical in v7:658, v8:727, v9:845, v10:1014
elif skip_triage:
    # Generate default triage (all DELIBERATION) so detection still works
    triage_results[ref] = [EventType.DELIBERATION] * n_segs
```

The flag reads as "run without Stage 1". It instead **substitutes a false Stage 1 output**,
which two consumers then believe:

- Stage 2's prompt renders it per segment as `[DELIBERATION] Seg N:` (`:75`), under a
  header saying each segment "has been pre-classified by event type" — so every page is
  introduced to the model as containing nothing narrative.
- Post-processing `rule3_v6_ensemble` demotes proposals on pages with "0 NARRATIVE_EVENTs",
  true of every page under the stub.

Measured on the one archived run built with it: the arm examining 3x the pages found **5
fewer** of Jeff's stories, 3 of them on pages both arms examined, and `NOT_A_STORY` went
2 → 44 of 74 → 91 proposals.

It is a live trap, not just history: `2026-08-31-triage-recall-price.md` had to work around
it, and `CLAUDE.md` now warns about it, but nothing stops the next use.

## Method

1. **Guard first.** A test that fails on today's behaviour: call the pipeline with
   `skip_triage=True` and real cached labels available, and assert the labels reaching the
   Stage 2 prompt builder are the cached ones — not all-`DELIBERATION`. Write it, watch it
   fail (Lesson 31), then fix.
2. **Fix in `src/story_detector_v11.py` only.** Every lower version is a frozen ship point
   — never edit those in place (CLAUDE.md). The flag should gate **only** the
   `pages_to_process` branch; labels come from cache or from a real Stage 1 run. Stage 1 is
   the cheap stage — the saving was never in skipping the labelling.
3. **Rename it `examine_all_pages`** so the name stops promising a bypass, keeping
   `skip_triage` as a deprecated alias if anything still passes it.
4. **Leave `results/v7/ablation_v7_no_triage.json` in place.** It is contaminated as a
   measurement and is now the *evidence* for the retraction. Do not regenerate or delete it.
5. **Optionally re-run the ablation properly.** `scripts/run_triage_recall_price.py`
   already implements the corrected shape (real labels, skip decision the only variable),
   so this is a re-use, not new machinery. Only then can the retracted 2026-02-13 claim be
   replaced with a measured one.

## How you know it worked

- The guard test fails on `main` and passes after the fix.
- With `skip_triage=True`, a spot-checked page's prompt carries its real mixed labels.
- If step 5 is run: a with/without table where the no-triage arm **never** loses a story on
  a page both arms examined — the impossible result that exposed the original.

## Guardrails

- **Do not change the shipped keep-condition here.** That is `N>=1` as of 2026-08-31 and
  was measured; this item is about the bypass, not the rule.
- Write any new output to `results/v11/ablation_fixed/`; never overwrite the v7 files.
- Run `evaluate_golden.py` only with `--output <scratch path>` (CLAUDE.md rule 4).

## When done

Finding → `docs/findings/<date>-<slug>.md`. Update
[`docs/capabilities/1_triage.md`](../docs/capabilities/1_triage.md) — capability **1
Triage** — including, if step 5 was run, what replaces the retracted 2026-02-13 row.
