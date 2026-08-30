# Wave 5 Steps 1–2: tripling the evidence base, and finding the gate's noise floor

**Date:** 2026-08-30 · **Model:** gemini-3.7-flash, thinking=high · **Detector:** v11

Two things were planned here: run Wave 5's clause spans on Ketubot so the expert
boundary test set is more than a third usable (Step 1), and fix the span prompt's
broken summary fallback (Step 2). Both are done. The third thing — the one worth
remembering — was not planned: **the gate cannot resolve a change of this size.**

---

## 1. The handicap was total, not partial

`_llm_clause_span_for_story` read `story['summary']`, then `story['text']`, then fell
back to joining the detected event list. Measured across all three `wave4_notrim`
files:

| file | stories | has `summary` | has `one_sentence_summary` | fell back to events |
|---|---|---|---|---|
| ketubot 2-60 | 56 | 0 | 56 | 55 |
| ketubot 61-112 | 111 | 0 | 105 | 105 |
| kiddushin | 95 | 0 | 95 | 95 |
| **total** | **262** | **0** | **256** | **255** (+7 with nothing) |

Not "0 of 95" as the plan estimated — **0 of 262**. Every single story ran on the
fallback. What that costs, on Ketubot 61a 12-12:

```
NOW   (events join):  They brought Shmuel a dish of mushrooms; Shmuel gave some to Rav Anan
FIXED (one_sentence): Rav Anan bar Tahalifa and Rav Ashi recount personal incidents where they
                      were served food while attending to their teachers and would have been
                      endangered by their cravings if not given a portion.
```

The events join stops mid-story. **35 of the 52 expert targets are END boundaries**,
so the model was being asked where a story ends while shown a description that stops
before the ending.

Fixed by putting `one_sentence_summary` first. The chain now lives in one place —
`story_summary()` in `src/story_detector_v11.py`, imported by
`scripts/run_clause_labeling.py`, which had independently written the same fix and
would otherwise have drifted.

## 2. Step 1 — Ketubot, run for the first time

Wave 5 had only ever run on Kiddushin, so 36 of 52 targets scored `N/A`. With
Ketubot 2-60 and 61-112 run today, **scorable targets go 16 → 35**.

And clause-anchored spans are worth a lot more than the earlier Kiddushin-only
number suggested. All three files pooled, 35 targets:

| run | scored | HIT | NEAR | MISS | hit% | hit+near% |
|---|---|---|---|---|---|---|
| no-trim (segment boundaries) | 35 | 4 | 6 | 25 | 11% | 29% |
| Wave 5 clause spans | 35 | 14 | 8 | 13 | **40%** | **63%** |

Per file, clause spans vs no-trim: ketubot 2-60 20%→30% HIT (30%→60% HIT+NEAR),
ketubot 61-112 11%→33% (11%→56%), kiddushin 6%→50% (38%→69%).

## 3. Step 2 — the fix is real, and the gate cannot see it

The fix changed **14 of 262 boundaries (5%)** corpus-wide. On the 35 expert targets
it changed **nothing**:

| run | scored | HIT | NEAR | MISS | hit% | hit+near% |
|---|---|---|---|---|---|---|
| baseline (handicapped prompt) | 35 | 14 | 8 | 13 | 40% | 63% |
| summary fix | 35 | 14 | 8 | 13 | 40% | 63% |

Identical on every target in all three files.

## 4. The noise floor — the finding that matters

Before calling that a null result, we measured what two runs of **identical code**
do. Kiddushin, same input, same model, same thinking level, run twice:

```
Kiddushin, 95 stories
  baseline vs fixed      (different code) :   6 (6%)
  fixed  vs fixed-repeat (SAME code)      :   3 (3%)   <- noise floor
  baseline vs fixed-repeat                :   7 (7%)
```

And on the scoreboard, the two identical-code runs do not agree:

| run | scored | HIT | NEAR | MISS | hit% | hit+near% |
|---|---|---|---|---|---|---|
| fix_kid | 16 | 8 | 3 | 5 | 50% | 69% |
| fix_kid **repeat, same code** | 16 | **9** | **2** | 5 | **56%** | 69% |

One target flipped NEAR→HIT from nondeterminism alone, and moved the headline six
points. On Kiddushin's 16 scorable targets **one target is 6.25 percentage points**;
the noise is about one target per run.

**So a single-run comparison at this sample size cannot distinguish a real
improvement from noise.** Every prompt-tuning number this project has quoted from one
run each side — including this one — carries an uncertainty band wider than most of
the effects being chased.

## 5. What follows

- **Keep the summary fix.** It is a strict information improvement — the model was
  being shown a truncated description of the thing it was asked to bound. It should
  not be *claimed* as a boundary improvement; the gate says nothing either way.
- **Step 4's precondition is now answered.** "Only revive Wave 5b if a properly-fed
  one-shot still stalls near 50%" — it does: 40% HIT / 63% HIT+NEAR on 35 targets,
  unmoved by proper feeding. But see the next point before acting on that.
- **Step 3 got bigger and more urgent.** It is no longer just the 2 contradictions
  and 3 duplicates (which cap a perfect run at 50/52). The gate needs either
  repeated runs averaged, or many more targets, before it can adjudicate any prompt
  change. Deciding Wave 5b on a one-run 50%-vs-56% swing would be deciding on noise.
- **A live instance of review §2.3:** the baseline ketubot 61-112 run had
  `skipped: 1` — one story whose boundary the model never produced. The scorer folded
  it into the metric as a "kept full" boundary without a word. It happened not to be
  a target this time.

## Artifacts

```
results/v11/wave5/ketubot_2-60_v11_g37high.json          baseline (handicapped)
results/v11/wave5/ketubot_61-112_v11_g37high.json        baseline (handicapped)
results/v11/wave5/kiddushin_v11_g37high_2026-08-30.json  baseline, same-day (Lesson 11)
results/v11/wave5_summaryfix/ketubot_2-60_v11_g37high.json
results/v11/wave5_summaryfix/ketubot_61-112_v11_g37high.json
results/v11/wave5_summaryfix/kiddushin_v11_g37high.json
results/v11/wave5_summaryfix/kiddushin_v11_g37high_repeat.json   the noise floor
```

`results/v11/wave5/kiddushin_v11_g37high.json` (2026-08-29) is kept but superseded by
the same-day baseline.
