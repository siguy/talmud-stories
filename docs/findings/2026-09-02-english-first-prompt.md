# "It is filled in by the translator" — the mechanism is real, and it does not explain the rejections

**2026-09-02.** Step 1 of
[`english-first-prompt`](../../work/done/2026-09-02-english-first-prompt.md): the free
audit that decides whether the ablation is worth running. **It says no**, and the reason
is more useful than a yes would have been.

Reproduce:

```bash
python3 scripts/audit_language_exposure.py --run results/v11/gittin/gittin_v11.json --verdicts validation/feedback/gittin_axes_review_2026-09-02.json
```

## The mechanism, confirmed

`build_detection_prompt` ([`src/story_detector_v11.py:204`](../../src/story_detector_v11.py))
renders each segment as English truncated at **300** characters, then Hebrew truncated at
**200**. Boundary refinement, cross-page merge and the continuation check send **English
only**. So the model reads more Steinsaltz than Aramaic, and Steinsaltz interpolates.

Measured on the shipped Gittin run: **Hebrew is truncated on 197 of 301 proposal segments
— 65%.** On two thirds of the segments in a proposal the model has not seen the whole
source. That is a real property of the pipeline, it was not known before today, and it is
worth knowing whatever else is true.

The audit script asserts the two budgets against the detector's own code, so if the
prompt changes and this file does not, it says so instead of silently describing a prompt
that no longer exists.

## And his two cases are exactly as he described them

Expansion ratio — the passage's own English:Hebrew, untruncated — corpus median **2.05**:

| | ratio | detector | his verdict |
|---|---|---|---|
| **Gittin 46a:12** | **4.51** | `HIGH_CONFIDENCE` | no |
| **Gittin 74b:4** | **5.89** | `HIGH_CONFIDENCE` | no |

Both are single short segments where the translator supplies four to six times the
Aramaic. *"There is no story. It is filled in by the translator"* is a precise description
of these two passages, and he read them right.

## The hypothesis still fails

If translator expansion were what makes us over-propose, the passages he rejects would sit
higher on it than the passages he accepts. **They sit lower.**

| | n | median untruncated ratio |
|---|---|---|
| judged a story | 3 | **2.59** |
| judged borderline | 4 | 3.46 |
| judged NOT a story | 18 | **2.42** |

Gap, rejected minus accepted: **−0.17**. And a median can hide a threshold, so the split
test too:

| | judged | rejected |
|---|---|---|
| ratio ≥ 2.5 | 13 | 8 (**62%**) |
| ratio < 2.5 | 12 | 10 (**83%**) |

The heavily-expanded group is rejected **less**. Whatever separates his yes from his no,
this is not it.

## What to conclude, and what not to

**Do not run the ablation.** It was gated on this screen precisely so a real-sounding
mechanism could not spend a run on its own plausibility (Lesson 18: measure the rate
before planning the fix).

**Do not conclude the mechanism is harmless.** It is real, it is large — 65% of segments
truncated on the Hebrew — and it is a live explanation for the *two* cases where the
expert named it. What this rules out is expansion as the **general** cause of our
false positives on Gittin.

**Read the power honestly.** 3 accepted against 18 rejected, and the whole judged set is
the adversarial residue: proposals his 2005 list does not name. The medians move on one
passage. This is a screen that points away, not a refutation — but a screen that points
away is exactly what it was built to produce, and acting as though it pointed toward
would be the more expensive mistake.

**The generalisation trap, avoided.** He named a cause for two passages. Turning that into
a corpus-wide theory without counting how many of his *other* verdicts it touches is
Lesson 27's shape, and it is the second time in two days that his prose about specific
cases nearly became a rule
([lesson](../../lessons/_a-policy-answer-does-not-certify-a-case.md)).

## Where the next attempt should aim

Not at the criteria and not at the language mix. The 2026-09-02 R-C3/R-C4 attempt already
showed the wording is not the constraint, and **Beitar is not proposed at all — not even
as `NOT_A_STORY`.** Both point at the same place: Detection's *coverage* of a page — the
find-more-stories pass — rather than at how a found candidate is described or judged.
