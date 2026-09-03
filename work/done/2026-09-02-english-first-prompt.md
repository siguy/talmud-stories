---
title: The detector reads more translation than source — price it
capability: [detection, classification]
tractate: []
blocked_by: []
awaiting: []
writes: [scripts/audit_language_exposure.py, docs/capabilities/2_detection.md, docs/findings/]
finding:
superseded_by:
---

# The detector reads more translation than source — price it

**Self-contained.** Read [`FRAMEWORK.md`](../../FRAMEWORK.md) first, then this.
**Capabilities: 2 Detection (primary), 3 Classification.**
**Cost:** the audit is free. The ablation is one Gittin run.

## The claim to test

Jeff rejected Gittin 46a — a passage we proposed at `HIGH_CONFIDENCE` — with:

> *"If you look at the Aramaic/Hebrew, there is no story. It is filled in by the
> translator. Not enough to go on here."*

And then 74b: *"the same as 46a above."* Two of our five `HIGH_CONFIDENCE` extras, killed
by the same cause.

**The mechanism is real and it is in the prompt.** `build_detection_prompt`
([`src/story_detector_v11.py:204`](../../src/story_detector_v11.py)) renders each segment as
English truncated at **300** characters, then Hebrew truncated at **200** — so on any
segment long enough to truncate, the model sees *more translation than source*. Boundary
refinement, cross-page merge and the continuation check send **English only** (lines 913,
923, 1059, 1070, 1237, 1251).

Steinsaltz interpolates: it supplies subjects, connectives and narrative sequencing that
the Aramaic leaves implicit. A detector reading it as if it were the source will find
event structure that is not in the text.

**Claim: a measurable share of our false positives are the translator's narrative, not
the Talmud's.** Status: **suspected**. One expert case is not a rate (Lesson 18).

## Method

**Step 1 — the audit, free, do this first.** `scripts/audit_language_exposure.py`:
for every proposal in `results/v11/gittin/gittin_v11.json`, report what the model actually
saw — how many of its segments truncated, the English:Hebrew character ratio, and whether
any downstream stage that touched it was English-only. Cross it with the 25 verdicts in
`validation/feedback/gittin_axes_review_2026-09-02.json`.

**This is the step that decides whether the ablation is worth running.** If the 18
rejections do not sit at a higher exposure than the 3 accepted stories, the mechanism is
real but not the explanation, and it stops here.

**Step 2 — the ablation, only if step 1 says go.** One Gittin arm with the Hebrew first
and the truncation budgets reversed (Hebrew 300 / English 200), everything else identical.
Score against the same blind list.

## How you know it worked

- Step 1 reports exposure per proposal, and the rejected/accepted split is either
  separated or it is not — **both are publishable answers**, and the negative one is the
  cheaper finding.
- Step 2, if run: recall must not fall. It is a precision experiment; a precision gain
  bought with recall is not a win on this project (`feedback_recall_over_precision`).

## Guardrails

- **A same-code repeat run before attributing any score change to the prompt change**
  (Lesson 22). Wave 5 measured this project's noise floor and it is not small.
- **Report blind and corrections sets separately** (Lesson 24), and split boundaries by
  direction (Lesson 15/`--by-direction`) — a language change plausibly moves ends and
  starts differently.
- Do **not** drop English. It is what the few-shot examples and the whole ground-truth DB
  are written against, and Jeff's own objection was that the Aramaic should be *consulted*,
  not that the translation should be *absent*.
- The frozen v7-v10 detectors are ship points; edit v11 or open v12 (CLAUDE.md).

## When done

Write the finding to `docs/findings/<date>-english-first-prompt.md`, update the
**2 Detection** row in [`docs/capabilities/2_detection.md`](../../docs/capabilities/2_detection.md),
add an `## Outcome` below, and `python3 scripts/board.py finish 2026-09-02-english-first-prompt`.

## Outcome

**Step 1 done, 2026-09-02. Step 2 not run, and should not be.**
Finding: [`2026-09-02-english-first-prompt.md`](../../docs/findings/2026-09-02-english-first-prompt.md).

**The mechanism is confirmed and larger than expected.** Hebrew is truncated on **197 of
301** proposal segments — 65%. On two thirds of the segments in a proposal the model has
not seen the whole source. That was not known before today.

**His two cases are exactly as he described.** Untruncated English:Hebrew, corpus median
2.05: Gittin 46a:12 is **4.51**, 74b:4 is **5.89**. Both single short segments where the
translator supplies four to six times the Aramaic. He read them right.

**And the hypothesis fails anyway.** The passages he rejects sit *lower* on expansion than
the ones he accepts — medians 2.42 against 2.59, gap **−0.17** — and the split test agrees:
of the judged proposals above ratio 2.5, 62% are rejected; below it, 83%. The
heavily-expanded group is rejected **less**. Expansion is not what separates his yes from
his no.

So the ablation is not run. That is the gate working: it existed so a real-sounding
mechanism could not spend a run on its own plausibility (Lesson 18).

### What makes this worth having written

The cause an expert names for two passages is evidence about **those two passages**. It
became a corpus-wide theory in the space of one paragraph while the finding was being
drafted, and only the screen stopped it — the same shape as Lesson 27, and the second time
in two days that his prose about specific cases nearly became a rule.

The negative result is also the cheaper half of the item by a wide margin: no API calls,
no same-code repeat needed, and it closes a live hypothesis rather than parking it.

### The honest limit

3 accepted against 18 rejected, and the entire judged set is the adversarial residue — the
proposals his 2005 list does not name. The medians move on one passage. **This points
away; it does not refute.** If a later round judges a broad sample of ordinary proposals,
re-run the audit against it before treating the question as closed.

### Where the next attempt should aim

Detection's **coverage of a page** — the find-more-stories pass — not the criteria and not
the language mix. Two independent results now point there: R-C3/R-C4 measured no effect on
the wording, and Beitar is not proposed at all, not even as `NOT_A_STORY`.
