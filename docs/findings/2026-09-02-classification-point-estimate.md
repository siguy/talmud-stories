# Classification on Gittin: 83.7–86.7% on what is labelled, and the number the ruler prints is not it

**2026-09-02.** Phase C of
[`review-verdict-axes`](../../work/done/2026-08-30-review-verdict-axes.md). The acceptance
test was that `unclassified_notes` reaches 0 and the precision range **converges to a
point**. Both happened on the first round that speaks the axis vocabulary — and the number
that converged is not the one to quote.

## The acceptance test passed

```
CLASSIFICATION (CIRCULAR)  25 of 158 proposals carry a verdict
   gittin_axes_review_2026-09-02.json   n=21   precision 0.143..0.143   {'classification': 18}
```

`0.143..0.143`. All-causes and classification-only are **identical**, because every one of
the 18 rejections names its own axis instead of burying it in prose. For a year
Classification could only be quoted as a range — Ketubot 87.9–94.8%, Kiddushin 67.4–92.1%
— and the width was unreadable notes. The width is now zero. That is the instrument
working exactly as designed.

## And the number is not the tractate's precision

**14.3% is precision on the residue.** The Gittin round covered *only* the 25 proposals his
2005 list does not name — deliberately, because the other 133 were already corroborated by
the list. So the ruler's denominator is the hardest subset that exists: everything we
proposed that twenty years of his own scholarship did not.

Quoting it as Gittin's Classification precision understates it by about **seventy points**.

This is not a bug in the ruler. It reports precision over proposals carrying a verdict,
which is right, and on Ketubot and Kiddushin that was most of them because those rounds
walked the tractate story by story. **The round changed shape and the figure changed
meaning, silently.** That is the thing to carry forward: a metric is only comparable across
tractates while the rounds behind it ask the same question.

## The tractate figure

`scripts/report_classification_precision.py --golden results/canonical/gittin_canonical.json`

Denominator: the **147** proposals the detector asserts are stories. A span it labelled
`NOT_A_STORY` itself is not a claim and cannot be a false positive.

| | |
|---|---|
| corroborated by his 2005 list | 110 |
| judged `YES` | 3 |
| judged `BORDERLINE` | 4 |
| judged `NOT_A_STORY` | **18** |
| **no expert evidence at all** | **12** |

| reading | precision |
|---|---|
| everything unproven counted against us | **76.9%** |
| everything unproven counted for us | **87.8%** |
| over the 135 labelled spans, borderline against us | **83.7%** |
| over the 135 labelled spans, borderline for us | **86.7%** |

**83.7–86.7% is the honest headline**, with the caveat below. The 76.9–87.8% band is the
same measurement with 12 unjudged spans left in the denominator, and its width *is* those
12 — reported as a width rather than distributed, because a single number over a
denominator containing unjudged spans is a guess wearing a decimal point.

### The caveat that must travel with it

**110 of the 113 correct entries are corroborated, not judged.** His list says a story is
*there*. It does not say our extent is right — that is capability 4, measured separately
and reported at 84% / 88% on Gittin. A reader who takes 86.7% as "86.7% of what we output
is right" is reading a boundary claim into a classification number.

Only **25** of the 147 have been judged as spans. That is the real limit here, and it is a
review-throughput limit, not a measurement one.

## Corrects a figure quoted earlier today

An earlier reading of this round gave **81.6–84.4%**, computed as `(117 listed + 3
yes) / 147`. The 117 came from `results/recall/gittin_listed_keys.json`, which was built on
the **loose** window and mis-credits two proposals
([`gittin_golden`](2026-09-02-gittin-golden.md)). The strict count is 110, and 12 spans
that figure treated as corroborated are in fact unjudged. **83.7–86.7%, over 135 labelled
spans, supersedes it.**

## What this does not settle

- **The gate.** `jeff:review-error-rate` is still unanswered, so there is no threshold to
  compare 86.7% against. The number is now a number; whether it is good enough is his call
  and remains Email 2, item 7.
- **Ketubot and Kiddushin.** Their ranges do not narrow retroactively. 129 banked verdicts
  are marked `lossy` for a reason, and re-deriving them in the new vocabulary would be
  manufacturing a measurement (the guardrail this item was opened with). The range narrows
  going forward.
- **A comparison across tractates.** Gittin's 86.7% and Ketubot's 87.9–94.8% are not
  like-for-like: different rounds, different denominators, and one of them mostly
  corroborated rather than judged.
