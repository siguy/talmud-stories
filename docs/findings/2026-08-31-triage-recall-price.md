# The price of the triage trade — measured on both tractates

**Date:** 2026-08-31
**Capability:** 1 Triage (primary), 2 Detection
**Datasets:** Jeff's 2005 Ketubot list (149, BLIND) and Kiddushin list (90, BLIND)
**Status:** measured
**Item:** [`work/2026-08-30-triage-recall-price.md`](../../work/done/2026-08-30-triage-recall-price.md)

---

## What was asked

`docs/capabilities/1_triage.md` names this the single highest-value untried item in
the capability and says it had **never been attempted**: Stage 1 discards more than
half of each tractate, so "96% recall" is really *96% of the fraction we look at*.
Nobody had measured the rest.

The item asks for an **exchange rate** — extra Stage 2 calls spent per additional
story recovered — not for a pipeline change. That constraint is kept: nothing about
the shipped pipeline moved.

## Method

Stage 2 was run on every page Stage 1 discarded, with **the skip decision as the only
variable**:

- Pages and their full text came from `results/v10/wave4_notrim/`, whose skipped pages
  carry `skipped_by_triage: true` together with their segments. No refetch.
- Event-type labels came from the shipped triage caches (`results/v7/event_triage_*.json`),
  **not** from a re-run and **not** from the all-DELIBERATION default that the existing
  `--skip-triage` flag substitutes. Stage 2 therefore saw the prompt it would have seen
  had the page not been skipped. Using the flag's default would have changed the prompt
  and confounded the result.
- Cross-page context was built from the **full** page list, so a discarded page still
  saw its real neighbours.
- Model `gemini-2.5-flash`, matching the provenance recorded in the shipped run's
  `wave4_stats.model`. A different model would have made this a model comparison
  (Lesson 22).

Before any API call, all 224 discarded pages were verified against the cache: entry
present, length matching the segment count, and `should_skip_page()` reproducing the
shipped decision. **All 224 reproduced exactly**, in four asserted buckets with zero
in any failure bucket.

Baselines were regenerated the same day rather than quoted from disk (Lesson 11), and
reproduced the published figures exactly.

Scripts: [`run_triage_recall_price.py`](../../scripts/run_triage_recall_price.py),
[`merge_triage_recall_run.py`](../../scripts/merge_triage_recall_run.py).
Artifacts: `results/v11/triage_recall/`.

## The result

**224 Stage 2 calls, 0 errors, 28 story proposals, 4 of them stories on Jeff's lists.**

| | Ketubot | Kiddushin |
|---|---|---|
| pages discarded by Stage 1 | 124 of 222 (56%) | 100 of 162 (62%) |
| segments never examined | 1,535 | 1,459 |
| recall, shipped (BLIND) | 96.0% (143/149) | 93.3% (84/90) |
| recall, every page examined | **96.6% (144/149)** | **96.7% (87/90)** |
| stories recovered | **1** — 72b | **3** — 10b, 14a, 69a |
| stories lost | 0 | 0 |
| extra Stage 2 calls | 124 | 100 |
| **exchange rate** | **124 calls per story** | **33 calls per story** |
| recall gained | +0.6 points | +3.4 points |

**The exchange rate differs by ~4x between the two tractates**, in the direction the
2026-08-31 recall finding predicted: Kiddushin skips more of the corpus and pays for it,
and the pages it skips are the ones with stories still on them.

## The two things worth acting on

**1. The Ketubot/Kiddushin recall gap is entirely the triage threshold, and it closes.**
Examined end to end, the two tractates land at **96.6% and 96.7%** — 0.1 points apart,
against 2.7 points apart as shipped. Detection was already known to be the same on both
(97.9% / 97.7%). This is the second, independent confirmation that the deficit sits in
Triage and nowhere else, and the first evidence that it is **recoverable rather than
structural**.

**2. Two of the three stories blamed on Ketubot triage are not triage's fault.**
Ketubot 20a and 82b are still missed with **every page examined** — Stage 2 does not
find them when handed the text. They are Detection failures wearing Triage's label, and
`1_triage.md` and the 2026-08-30 miss diagnosis both attribute all three to Stage 1.
Only 72b was genuinely recoverable by looking. Kiddushin is the opposite: **3 of its 4**
triage-lost stories come back, and only 21b resists.

Corrected attribution of the six known Ketubot misses: **1 triage-recoverable
(72b), 2 lost on discarded pages that Stage 2 cannot find anyway (20a, 82b)**, the rest
unchanged.

## The cost side, stated plainly

Precision on discarded pages is **4 of 28 proposals = 14.3%**, against ~89% on the pages
triage keeps. Stage 1 is therefore doing close to what it is meant to do: the pages it
throws away really are mostly storyless, and reading them all would add 24 false
proposals to buy 4 real stories — each of which then costs reviewer time, which is the
project's actual bottleneck.

**This is why the item asked for a rate and not a fix.** The naive reading of "we
discard 56% of the tractate" is that triage is broken. Measured, it is not: it is a
priced trade, and on Ketubot the price is bad (124 calls and 17 spurious proposals for
one story). On Kiddushin it is arguably worth paying (33 calls per story, and it closes
the tractate's entire gap).

## What this does NOT license

- **No pipeline change is proposed here**, per the item's guardrail. Loosening Stage 1
  costs calls on every future run and on every future tractate, and the review cost of
  24 extra false proposals per tractate is not yet priced — it lands on the one
  capability that is already the bottleneck.
- **The 96.6% / 96.7% figures are not a new headline recall.** They describe a
  configuration we do not ship. The shipped numbers remain 96.0% / 93.3%.
- **The proposals were checked against Jeff's list, not spot-read for quality.** The
  item asks for a sample read before treating a rise in "detected" as a win; the
  list-check is the stronger test and it is what is reported. The 24 non-matching
  proposals have **not** been read, so nothing here says whether they are hallucinations
  or unlisted-but-real stories. That distinction matters and is untested.

## Defects found on the way

- **`measure_recall_vs_expert_list.py` prints cause buckets that need not sum to the
  miss count.** The total is derived from the current run's proposals; the two buckets
  are derived from `skipped_by_triage` flags baked into the detected file. On the merged
  run it printed *"CAUSE of the 3 misses: 4 triage discarded, 2 examined"*. Latent in
  normal use, and never asserted — the Lesson 21 shape again. Reported, not fixed here.
- **A negative segment index in shipped-adjacent output.** Stage 2 proposed
  `Ketubot 112b, start_segment -2, end_segment 0`. Nothing validates that a proposed
  span lies within the page. This one is on a discarded page so it reaches no published
  number, but the absence of the check is general.

## Reproduce

```bash
python3 scripts/run_triage_recall_price.py --tractate kiddushin --dry-run   # partition only, no API
python3 scripts/run_triage_recall_price.py --tractate kiddushin             # ~100 calls
python3 scripts/merge_triage_recall_run.py --tractate kiddushin
python3 scripts/measure_recall_vs_expert_list.py \
  --expert-json results/expert_lists/kiddushin_2005.json --expert-filter recall \
  --detected results/v11/triage_recall/kiddushin_v10_notrim_plus_skipped.json \
  --golden results/canonical/kiddushin_canonical.json --tractate Kiddushin \
  --out results/v11/triage_recall/kiddushin_allpages.json
```

## Open question this hands to Simon

FRAMEWORK §2b's end-to-end target now has a price attached on both tractates. The
question is no longer "is 98% the right triage bar" but:

> Is +3.4 points of Kiddushin recall worth 100 extra Stage 2 calls **and 7 extra false
> proposals landing in front of the reviewer**, when reviewer throughput is the binding
> constraint on the whole project?

That is a product decision, and the review-cost half of it is still unpriced.
