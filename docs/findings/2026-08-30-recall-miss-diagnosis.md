# Why we miss the 6 stories we miss — 2026-08-30

> **Corrected 2026-08-30.** This document's cause breakdown treats all five as
> Detection misses. Two of them are not. A text search across all 53 run files (this
> document checked only `results/v10/wave4_notrim/`) found **Ketubot 20a segs 2-3**
> proposed by `results/v5/pages_2-39.json` and **Ketubot 53a seg 11** proposed by
> `results/v7/ablation_v6_triage_merge.json`, both classified **NOT_A_STORY**, both at
> 100% Hebrew 4-gram coverage of Jeff's text. For those two the failure is
> **Classification, not Detection** — the same re-diagnosis `abdc4af` made for 77a.
> So the taxonomy is 3 Detection misses and 2 Classification rejections, not 5 misses.
> The golden's provenance is corrected by `scripts/correct_detector_status_2026-08-30.py`.


The 96% recall figure on Ketubot rests on 6 misses against Jeff's detector-blind 2005
list. They are the most valuable failures in the project — genuine negatives, found
without our own labels in the loop. Traced through the pipeline, they are not one
problem.

> ## CORRECTION — 2026-08-30 evening (brief `tasks/NEXT/02`)
>
> **The two-population split below is wrong. All six misses are absent from the golden.**
>
> The row for Ketubot 77a carried `in_golden: true`, and this document read that as "we
> labelled it ourselves and still miss it." It is a locator artifact. Jeff's blind 77a
> story and our golden's 77a story are **two different passages on one daf**:
>
> | | golden | Jeff's 2005 list |
> |---|---|---|
> | segments | **8** | **13-14** |
> | passage | Sidon tanner *ma'aseh* | `אכסוה שערי לאלעזר` |
> | layer | Mishnah | Gemara |
> | n-gram coverage of Jeff's text | 0.010 | **0.943** |
>
> The recall locator returns a deliberately coarse window (up to 14 segments) to
> maximise coverage, so it spanned both and made them look like one story.
>
> **What 77a actually is:** re-run 8 times on identical code, Stage 2 *does* propose
> segs 13-14 in **7 of 8** runs and classifies them `NOT_A_STORY` in 6 of those 7,
> every time citing the same three prompt disqualifiers. Production landed in the ~1/8
> tail where nothing was proposed. So it is a **Classification** problem sitting on
> proposal-level variance — not Detection. Capability reassigned 2 → 3.
> Seed case with the minimal pair: [`docs/history/2026-08-29-PLAN-wave6-story-criteria.md`](../history/2026-08-29-PLAN-wave6-story-criteria.md).
>
> **A separate, larger loss found while measuring the corpus rate:**
> `filter_mishnah_only_stories()` moves stories out of `stories` into `mishnah_stories`,
> and **neither `evaluate_golden.py` nor the recall script reads that key**. Of the 4
> Ketubot stories it moves, **3 are stories our own golden accepts** — removed from the
> output and invisible to every metric. Ketubot 77a seg 8, 95b seg 0, 14b seg 11.
>
> **Also:** `parse_expert_doc` only matches single-amud headers, so stories under
> two-amud headers (`מט ע"ב-נ ע"א`) are credited to the preceding daf — **15 such headers
> in the Ketubot document**. The **96% recall figure is unaffected**: `locate()` finds
> stories by n-gram matching across the whole corpus and never consults the parsed
> reference. What is unreliable is the per-story `ref` *label*, so any **per-daf**
> analysis needs the fix first.

## The two populations, which had been conflated

| | count | what it means |
|---|---|---|
| missed by the detector **and** absent from the golden | **5** (20a, 53a, 67b, 72b, 82b) | we never found them *and* never labelled them. Invisible to every metric we had. |
| missed by the detector but **present** in the golden | **1** (77a) | our own validated dataset says this is a story. No definitional argument is available. A plain bug. |

## Cause breakdown

```
3  Stage 1 (event triage) discarded every page the story sits on
2  page was processed, Stage 2 found nothing in that range
1  cross-page story, both halves processed, neither half flagged
```

## The dominant cause: Stage 1 throws away half the tractate

**Stage 1 triage discards 124 of 222 Ketubot pages — 56%.** Those pages are never shown
to the story detector at all. Of Jeff's 149 stories, 19 touch a discarded page; 16
survive only because the *other* page of the pair was kept. Three are lost outright:

- **Ketubot 20a** — both 19b and 20a discarded
- **Ketubot 72b** — both 72a and 72b discarded
- **Ketubot 82b** — both 82b and 83a discarded

This reframes the headline number: **we reach 96% recall while never looking at more
than half the tractate.** The cheapest recall work available is not a better Stage 2
prompt — it is re-running Stage 2 on the 124 discarded pages and measuring what comes
back. That is bounded, cheap, and has never been done.

## The clearest bug: Ketubot 77a

The page was processed. Stage 2 returned **zero stories for the whole page**. Our own
golden dataset has a story at segments 8-14, and Jeff's 2005 list has the same story
(58 words, 97% alignment). Both agree; the detector produces nothing. Worth reading the
passage against the Stage 2 prompt directly — a story both an expert and our own
labellers accept, that the prompt rejects, is the sharpest available signal about what
the prompt gets wrong. Feeds Wave 6.

## The weaker claim, stated as weak

4 of the 6 misses span two pages. But 53% of all 149 stories also *appear* to span two
pages by this measure, because the locator returns a coarse n-gram window that can
straddle a page break even when the story does not. **Cross-page is at most mildly
over-represented here (67% vs 53%), and the measurement is not clean enough to
support more.** Do not cite it as a cause without tightening the locator first.

## Next

1. Re-run Stage 2 on the 124 triage-discarded Ketubot pages. Bounded cost, unmeasured
   benefit, and it directly tests whether the 96% is really a ~96%-of-56% figure.
2. Read Ketubot 77a against the Stage 2 prompt.
3. Add the 5 absent stories to the golden with expert-list provenance.
