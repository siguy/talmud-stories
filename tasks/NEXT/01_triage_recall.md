# NEXT 01 — Does Stage 1 throw away real stories?

**Self-contained.** Read `STATUS.md` first, then this. No other context needed.
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

Findings → `docs/golden/workflow/triage_recall_<date>.md`. Update `STATUS.md` axis 1.
If it changes what we would tell Jeff, note it — a reply is pending.
