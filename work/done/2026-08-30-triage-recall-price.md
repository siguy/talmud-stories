---
title: Price the triage trade over the 124 discarded Ketubot pages
capability: [triage]
tractate: [ketubot]
blocked_by: []
awaiting: []
finding:
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

**Done 2026-08-31, and widened from the 124 Ketubot pages in the title to all 224
discarded pages across both tractates** — Kiddushin's 100 had their text on disk too, and
after 2026-08-31 made Kiddushin Triage the board's only failing cell, scoping this to
Ketubot alone would have measured the wrong tractate.

→ [`docs/findings/2026-08-31-triage-recall-price.md`](../../docs/findings/2026-08-31-triage-recall-price.md)

**The exchange rate, which is what was asked for:**

| | Ketubot | Kiddushin |
|---|---|---|
| recall shipped -> all pages examined | 96.0% -> **96.6%** | 93.3% -> **96.7%** |
| stories recovered / extra Stage 2 calls | 1 / 124 | 3 / 100 |
| **calls per story** | **124** | **33** |

224 calls, **0 errors**, 28 proposals, 4 of them on Jeff's blind lists. Precision on
discarded pages **14.3%** against ~89% on kept pages.

**Three results, two of them not what the brief expected:**

1. **The Ketubot/Kiddushin recall gap is the triage threshold, and it closes.** Examined
   end to end the two land 0.1 points apart (96.6% / 96.7%) against 2.7 apart as shipped.
   Second independent confirmation that the deficit is Triage's, and the first evidence it
   is **recoverable, not structural**.
2. **Two of the three stories blamed on Ketubot triage are not triage's fault.** 20a and
   82b are still missed with every page examined — Detection failures wearing Triage's
   label. `1_triage.md` and the 2026-08-30 miss diagnosis both attributed all three to
   Stage 1; that attribution is now corrected. Only 72b was recoverable by looking.
   Kiddushin is the mirror image: 3 of its 4 come back, only 21b resists.
3. **The brief's success criterion "the 3 known misses recovered or explained" is met** —
   1 recovered, 2 explained as Detection misses.

**Why no pipeline change**, per the item's own guardrail: precision on discarded pages is
14.3%, so reading everything buys 4 real stories at the cost of 24 spurious proposals
landing in front of the reviewer — and reviewer throughput is the project's binding
constraint. The review-cost half of the trade is **still unpriced**, and that is what
would decide it. **Do not loosen Stage 1 until it is.**

**Untested, and it matters:** the 24 non-matching proposals were checked against Jeff's
list but never read. They are either hallucinations on legal pages or real stories absent
from his list, and those two answers point opposite ways. Recorded in
[`1_triage.md`](../../docs/capabilities/1_triage.md) Untried.

**Two defects found on the way**, neither fixed here (experiment, not a ship):
`measure_recall_vs_expert_list.py` prints miss-cause buckets that need not sum to the miss
count and never asserts that they do (Lesson 21's shape, latent in normal use); and Stage 2
proposed a **negative segment index** (Ketubot 112b, `-2..0`) with nothing validating that
a span lies within its page.
