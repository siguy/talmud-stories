---
title: Rank the unlisted proposals — separate real discoveries from junk in the LOW band
capability: [classification]
tractate: []
blocked_by: []
awaiting: []
writes: [results/discovery/, scripts/build_unlisted_labelled.py, scripts/rank_unlisted_proposals.py]
finding:
superseded_by:
---

# Rank the unlisted proposals — separate real discoveries from junk in the LOW band

**Self-contained.** Read [`FRAMEWORK.md`](../FRAMEWORK.md) §1.3 and §3, then this.

## The problem, stated as a fact rather than a worry

Gittin is the first tractate where Jeff labelled proposals **his own list does not
contain**. 30 unlisted proposals, 25 sent to him, and the verdicts came back:

| our tier | shown | → yes | → borderline | → no |
|---|---|---|---|---|
| `YES` | **0** | — | — | — |
| `HIGH_CONFIDENCE` | 5 | **0** | 3 | 2 |
| `LOW_CONFIDENCE` | 20 | **3** | 1 | 16 |

**Every one of our 59 `YES`-tier proposals was already on his list.** The top band has
perfect precision and contributes **zero** new stories. The middle band produced five
extras and zero acceptances. **All three genuine discoveries came from the bottom band**,
where they sat alongside 16 rejections.

So the confidence tier we emit is a good predictor of *agreement with Jeff's 2005 list*
and a **useless** predictor of *whether an unlisted passage is a story*. For the half of
this project that is discovery — finding what the 2005 list missed — our ranking signal
is not weak, it is absent.

**This is the item that makes discovery cheap.** Nothing here improves the detector. It
improves which 25 of the unlisted proposals we put in front of Jeff, and in what order.

## The claim to test

*Features the detector already emits, plus surface features of the passage, separate
Jeff's `yes`/`borderline` from his `no` among unlisted proposals — better than the
confidence tier does, which is not at all.*

## What labels exist (count them before designing anything)

| source | positives | negatives | blind? |
|---|---|---|---|
| Gittin 25 verdicts, 2026-09-02 | 3 yes + 4 borderline | **18 no** | **BLIND** — the tractate was never in a prompt |
| Ketubot canonical | 164 accepted | 23 `NOT_A_STORY` | CIRCULAR |
| Kiddushin canonical | 85 accepted | 11 `NOT_A_STORY` | CIRCULAR, and on **v7** output |
| Gittin self-screened | — | 5 duplicates / standing practice | ours, not his |

**The Gittin 25 are the only rows that answer the actual question** — the others are
verdicts on proposals mostly *on* his list, which is a different population. Design for
n≈25 with 18 negatives. That is small, and the method must be chosen for that size.

## Method

1. **Assemble the population, do not model yet.** One row per unlisted proposal with a
   Jeff verdict. Emit `results/discovery/unlisted_labelled.json`. Columns: everything the
   detector already writes (`criteria_met_count`, `disqualifiers_found`,
   `weakeners_found`, tier, segment count, `one_sentence_summary`) plus cheap surface
   features: word count, Hebrew:English expansion ratio, presence of each
   `_STORY_INTRODUCERS` opener, and the `src/speech_act_lexicon.py` tier flags. **No API
   calls in this step.**

2. **Look at the 3 accepted before fitting anything.** Jeff's note on 19a — *"A very
   minimal story, but qualifies as a story"* — suggests the accepted extras are *thin*
   rather than different in kind. If all three are short and many rejections are long,
   that is a one-feature answer and no model is needed. **Report this by hand first**
   (Lesson 18 — measure at the granularity the mechanism operates on).

3. **Only then, a ranker.** With 25 rows, a fitted classifier will memorize. Two
   admissible options, in order of preference:
   - **A hand-built score from at most 3 features**, chosen in step 2, with the threshold
     set by leave-one-out over the 25. Interpretable, and it can be explained to Jeff.
   - **Logistic regression on ≤4 features**, leave-one-out, reporting the LOO AUC *and*
     the spread across folds. If the spread is wide, say so and stop.
   Anything with more parameters than rows is out (Lesson 9).

4. **Baseline it against the tier.** The bar is not "does it work" but "does it beat the
   confidence tier". The tier's discovery AUC on this set is near chance by construction —
   0 of 5 `HIGH` accepted, 3 of 20 `LOW` accepted. **A ranker that cannot beat that is a
   negative result worth writing down.**

5. **Ship it as an ordering, not a filter.** Output is the order in which unlisted
   proposals go into the review UI. **It must never suppress a proposal** — Jeff sees all
   of them; the ranker only decides what he sees first. This is the whole reason this item
   is safe to build where a false-positive *filter* was twice deferred (Lesson 7):
   a filter can silently lose a story, an ordering cannot.

## How you know it worked

- LOO AUC over the Gittin 25, reported with fold spread, **beating the tier baseline**.
- Applied to a tractate's unlisted proposals, the accepted ones sit in the top half of the
  order. On Gittin this is checkable directly: do 19a:16, 43b:4 and 70a:22 rank above the
  18 rejections?
- **A negative result closes this item too.** "Nothing in what we emit predicts Jeff's
  acceptance of an unlisted passage" is a finding, and it argues for a different round
  design instead — send him more extras, not better-ordered ones.

## Guardrails

- **The Gittin 25 are TEST-ONLY. Never few-shot, never in a prompt** (Lessons 2, 8).
  They are the project's only blind negatives; burning them into a prompt destroys the
  one dataset that can answer this.
- **Do not pool Gittin with the Ketubot/Kiddushin `NOT_A_STORY` rows** without reporting
  both separately. Different populations, one blind and two circular, and Kiddushin's are
  v7-era.
- n=25. **Report the confidence interval or do not report the number.**
- No change to the detector, no change to any golden, in this item.

## When done

Write the finding to `docs/findings/<date>-extra-story-discriminator.md`, add an
`## Outcome` section here, and `python3 scripts/board.py finish extra-story-discriminator`.
