---
title: Price the triage trade over the 124 discarded Ketubot pages
capability: [triage]
tractate: [ketubot, kiddushin]
blocked_by: []
awaiting: []
finding: docs/findings/2026-09-01-triage-recall-price.md
superseded_by:
---

# Price the triage trade over the 124 discarded Ketubot pages

**Self-contained.** Read `STATUS.md` and `FRAMEWORK.md` first, then this.
**Capability: 1 Triage.** Gate: >=98% survival, provisional. No other context needed.
**Depends on Jeff: no.** **Cost: minutes, pennies.** **Owner: unassigned.**

## The claim to test

Stage 1 (event triage) discards **124 of 222 Ketubot pages — 56%** — before the story
detector ever sees them. **1,535 segments have never been examined.** Three of our six
known recall misses (Ketubot 20a, 72b, 82b) died there: both pages of each pair were
thrown out.

So "96% recall" is really *96% of the 44% we look at*. Nobody has ever measured the
other 56%.

This is not a Ketubot problem. If Stage 1 is over-aggressive it is costing us on every
tractate, and it compounds at Talmud scale.

## Inputs, all already on disk

- `results/v10/wave4_notrim/ketubot_v10_2-60_notrim.json`
- `results/v10/wave4_notrim/ketubot_v10_61-112_notrim.json`
  Skipped pages carry `skipped_by_triage: true` **and their full segment text** — no
  re-fetch needed.
- `jeff comms/b.ketubot (1).doc` — the blind 149-story list
- `scripts/measure_recall_vs_expert_list.py` — the recall harness

## Method

1. Extract the 124 skipped pages into a working file.
2. Run **Stage 2 only** on them (`src/story_detector_v11.py`, `detect_stories`) — do not
   re-run triage, do not re-fetch.
3. Re-measure recall against Jeff's list with the pages included.
4. Compute the **exchange rate**: extra Stage 2 calls spent per additional story
   recovered. This decides whether the pipeline changes, not just whether stories exist.
5. Spot-read a sample of anything new — Stage 1 may be filtering correctly and Stage 2
   may simply hallucinate stories on legal pages. **A rise in "detected" is not a win
   until the new items are checked against Jeff's list, not just counted.**

## How you know it worked

- A recall number **for the whole tractate**, not for the examined subset.
- The 3 known misses (20a, 72b, 82b) either recovered or explained.
- A stated exchange rate, so the pipeline decision is evidence-based.

## Guardrails

- **Experiment, not a ship.** Loosening triage costs calls on every future run. Do not
  change the pipeline in this task; produce the number that justifies the change.
- Write to `results/v11/triage_recall/`; never overwrite `wave4_notrim`.
- Regenerate today's baseline before comparing (Lesson 11).
- Every outcome bucket must be a partition and must be asserted (Lesson 21).

## When done

Findings → `docs/findings/<date>-triage-recall.md`. Update `STATUS.md` — capability: **1 Triage**.
If it changes what we would tell Jeff, note it — a reply is pending.

## Outcome

**Done 2026-09-01.** The recall side is priced on both tractates; the review-cost side is
not, because the artifact that looked like it had already answered it turned out to be
contaminated. Successor: [`2026-09-01-triage-bypass-and-precision`](../2026-09-01-triage-bypass-and-precision.md).
Finding: [`2026-09-01-triage-recall-price.md`](../../docs/findings/2026-09-01-triage-recall-price.md).
No API calls were spent; everything came from artifacts already on disk.

**What was measured.**

- **The exchange rate, both tractates.** Ketubot: at most 3 stories for 124 extra Stage 2
  calls — **1 per 41**, +2.0 pts. Kiddushin: at most 4 for 100 — **1 per 25**, +4.4 pts.
  This item was scoped to Ketubot's 124 discarded pages; Kiddushin's 100 were priced too,
  which `STATUS.md` had flagged as the missing half.
- **The three known misses are explained, and the explanation kills the obvious fix.**
  10 of the 13 pages that killed a story carry **zero** narrative events, not one below
  the bar. Relaxing to `narrative>=1` costs 4 calls and recovers **0 stories on both
  tractates**. Stage 1's misses are labelling failures, so they belong to the opener
  lexicon or a different Stage 1 model — not to the threshold.
- **A structural fix, proposed and killed in the same session.** 6 of 7 killed stories
  span a daf boundary, so "examine the daf either side of every kept page" looked
  compelling. Priced from the cache: **+60 Ketubot calls, +34 Kiddushin, 0 stories** — the
  killed pages sit inside runs of discarded pages, never on the edge of a kept one.
  Recorded so it is not proposed again.

**Why the rest is a new item rather than more of this one.** The method this brief
specified — *"run Stage 2 only on them"* — is booby-trapped. `skip_triage=True` does not
bypass Stage 1; it stamps every segment `DELIBERATION` and feeds that to Stage 2, in every
detector version v7 through **v11**. `results/v7/ablation_v7_no_triage.json` is that flag's
output, and scoring it exposed the contamination: it **loses 6 stories on pages both arms
examined**, which no change to the page set can cause. The 2026-02-13 "triage is the single
largest accuracy driver" conclusion rests on that file and does not follow from it —
corrected in [`docs/capabilities/1_triage.md`](../../docs/capabilities/1_triage.md) rather
than edited away. Fixing the bypass is a code change with its own guard test, so it gets
its own item.
