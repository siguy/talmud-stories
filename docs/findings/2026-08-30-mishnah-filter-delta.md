# The Mishnah filter contradicts the golden — measured

**2026-08-30.** Found while executing `tasks/NEXT/02`; the seed case is written up in
[`docs/history/2026-08-29-PLAN-wave6-story-criteria.md`](../history/2026-08-29-PLAN-wave6-story-criteria.md) under "Seed case — Ketubot 77a",
adjacent defect #1. This file is the measurement and the scope question it raises.

## What the filter does

`filter_mishnah_only_stories()` (`src/story_detector_v11.py`, Wave 1 Issue #7) moves any
story lying entirely inside a Mishnah block out of `stories` and into `mishnah_stories`.
Its docstring says such stories "should be tallied separately, not as Talmud (Gemara)
stories."

Nothing tallies them. Neither `scripts/measure_recall_vs_expert_list.py` nor
`scripts/evaluate_golden.py` reads `mishnah_stories`, and neither does the review UI
generator. A withheld story therefore lands in the golden evaluation as a **false
negative** and in recall as a **miss**, indistinguishable from a story we never found.

## Measured — `results/v10/wave4_notrim/`, 2026-08-30

The filter moves **5 stories corpus-wide**: 4 on Ketubot, 1 on Kiddushin.

| | detector | golden | genuinely in a Mishnah? |
|---|---|---|---|
| Ketubot 14b seg 11 | HIGH_CONFIDENCE | **accepted** (LOW_CONFIDENCE) | yes |
| Ketubot 54b segs 1-3 | YES | **accepted** (YES, segs 1-2) | **no — tagger bug** |
| Ketubot 77a seg 8 | HIGH_CONFIDENCE | **accepted** (LOW_CONFIDENCE) | yes |
| Ketubot 95b seg 0 | LOW_CONFIDENCE | **accepted** (LOW_CONFIDENCE) | **no — tagger bug** |
| Kiddushin 50b seg 10 | HIGH_CONFIDENCE | NOT_A_STORY | yes |

Reproduce, both tractates:

```bash
python3 scripts/report_mishnah_filter_delta.py --detected results/v10/wave4_notrim/ketubot_v10_2-60_notrim.json results/v10/wave4_notrim/ketubot_v10_61-112_notrim.json
```

### The delta against the golden

Scored twice by the **immutable** `evaluate_golden.py` — imported read-only, never
modified, never written through — once as the runs stand, once with `mishnah_stories`
folded back into `stories`.

**Ketubot** (golden 187 entries):

| metric | as-is | folded back | delta |
|---|---|---|---|
| classification recall | 0.9085 | 0.9329 | **+0.0244** |
| classification F1 | 0.9003 | 0.9134 | +0.0131 |
| true positives | 149 | 153 | **+4** |
| false negatives | **15** | 11 | **−4** |
| false positives | 18 | 18 | 0 |
| composite | 0.9115 | 0.9125 | +0.0010 |

**The filter alone accounts for 4 of Ketubot's 15 golden false negatives — 27%.**

> Corrects an earlier figure. `PLAN_wave6.md` and `STATUS.md` said "31% of the 13 golden
> false negatives." Both numbers moved when brief 10 grew the golden 182 → 187: the
> denominator is now 15. The 4 is unchanged.

**Kiddushin** (golden 96 entries): the one withheld story is `NOT_A_STORY` in the golden,
so the filter is **right** there — folding it back costs a false positive
(precision 0.8526 → 0.8438). The filter is not uniformly wrong; it is uncalibrated.

### The delta against recall — none

Recall is **unchanged at 143/149 = 96.0%**. Jeff's blind 2005 Ketubot list contains no
Mishnah-only story, so the filter costs no *measured* recall. That is an absence of
evidence, not evidence the scope is right.

One expert story (Ketubot 77a) now reports `in_mishnah_filtered: true`, but that is the
**same locator artifact** documented in
[`recall_miss_diagnosis_2026-08-30.md`](2026-08-30-recall-miss-diagnosis.md):
the located window runs 77a segs 8..14 and so straddles both the withheld Mishnah
ma'aseh (seg 8) and Jeff's actual story (segs 13-14). An overlap is a lead, not a loss —
which is why the recall script prints it as `CHECK`, not as a miss.

## How the golden came to hold stories the detector now deletes

The filter arrived in Wave 1 (v8), **after** the golden had already accepted these
passages:

- `results/v7/ketubot_v7_2-60.json` — Ketubot 14b seg 11 present in `stories` as `YES`.
- `results/v9/wave3/ketubot_v9_61-112.json` — 77a seg 8 and 95b seg 0 already sitting in
  `mishnah_stories`, absent from `stories`.

So these entered the golden from pre-filter output and expert review, and the filter now
makes them permanently unreachable. No harness, and no review page, can see the loss.

## This is a scope question, and both sides of it are Jeff's

The filter's premise is **his**, from the Kiddushin review (2026-04-23, entry #58,
Kiddushin 50b):

> "This story is in the Mishnah, so it should be catalogued with Mishnah stories, not
> Talmud stories."

But he also affirmed, in review, every one of the four Ketubot stories the filter now
deletes:

| | his verdict | date | his note |
|---|---|---|---|
| Ketubot 77a seg 8 | **correct** | 2026-03-17 | — |
| Ketubot 95b seg 0 | **correct** | 2026-03-17 | — |
| Ketubot 54b segs 1-2 | **correct** | 2026-03-13 | — |
| Ketubot 14b seg 11 | *incorrect* | 2026-03-13 | *"It should be 'low confidence,' a borderline story. There are two events but no causality."* |

The 14b verdict is about the **confidence label, not storyhood** — he demoted it and kept
it, which is exactly how the golden holds it.

**These are not in conflict — our implementation is.** He asked for Mishnah stories to be
*catalogued separately*. We built a *deletion* that nothing catalogues, nothing scores and
nothing displays. Under his literal words, a Mishnah story belongs in the database in a
different bucket, and there is no contradiction to resolve at all.

**Two of the four aren't even Mishnah.** Ketubot 54b and 95b are plain Gemara mis-tagged
at a chapter boundary — a separate defect, owned by the companion task on chapter-boundary
mis-tagging (`PLAN_wave6.md`, adjacent defect #2; 7 pages affected). The genuine scope
question rests on **two** passages, both classic `מעשה` precedent stories cited inside a
Mishnah:

- Ketubot 14b seg 11 — `מעשה בתינוקת שירדה למלאות מים מן העין, ונאנסה`
- Ketubot 77a seg 8 — `מעשה בצידון בבורסי אחד שמת, והיה לו אח בורסי`

Question drafted for the next email:
[`JEFF.md`](../../comms/JEFF.md).

## What changed in the repo today

Regardless of his answer, the loss should stop being invisible.

- **`scripts/report_mishnah_filter_delta.py`** — NEW. Inventories every withheld story with
  its standing in the golden, then reports the delta by scoring the runs twice through the
  immutable harness. `evaluate_golden.py` is imported read-only and is **not modified**
  (project rule), and nothing is written to its default output path.
- **`scripts/measure_recall_vs_expert_list.py`** — now reads `mishnah_stories` and reports
  it. The headline recall is **deliberately unchanged**: a withheld story was found and
  then dropped on a scope judgement, which is not the same as never finding it, and
  merging the two would trade one invisible number for another. Each row gains
  `in_mishnah_filtered`.

Not done here: `results/recall/ketubot_jeff2005_matches.json` was **not** regenerated, so
it lacks the new `in_mishnah_filtered` field — other sessions share this working tree. One
command when wanted; the `--out` line in the script's own docstring.

Also unfixed by design: the chapter-boundary tagger bug, and the review UI, which still
does not show `mishnah_stories` to the expert.
