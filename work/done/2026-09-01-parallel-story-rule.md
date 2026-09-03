---
title: Stop the parallel-practice rule deleting a second story
capability: [boundaries]
tractate: [ketubot, kiddushin]
blocked_by: []
awaiting: []
writes: [src/story_detector_v11.py, scripts/screen_end_trim_depth.py, scripts/run_parallel_rule_experiment.py, scripts/score_boundary_targets.py, tests/test_parallel_story_rule.py, docs/capabilities/4_boundaries.md, docs/findings/2026-09-01-parallel-story-rule.md, results/v11/]
finding: docs/findings/2026-09-01-parallel-story-rule.md
superseded_by:
---

# Stop the parallel-practice rule deleting a second story

**Self-contained.** Read [`FRAMEWORK.md`](../../FRAMEWORK.md) and
[`docs/capabilities/4_boundaries.md`](../../docs/capabilities/4_boundaries.md) first.
**Capability: 4 Boundaries.** **Cost: one prompt rule, plus one measured run.**

## The claim to test

One rule in the Wave 5 clause-span prompt conflates two different things:

> `- A clause that merely states a PARALLEL practice by a different person after the
>   story has ended is not part of this story.`

It is meant for a footnote — *"and Rav Pappa did the same"*. It also fires on a
**second complete story** that the Talmud introduces with a parallel marker, and
because nothing downstream picks up the discarded clauses, the passage leaves the
corpus entirely.

Two confirmed cases, both at depth 6:

- **Ketubot 105b seg 9** — kept through clause 7 (Ameimar and the feather), dropped
  8-13: Mar Ukva, the spittle, the man who covers it, their exchange, and
  `פְּסִילְנָא לָךְ לְדִינָא`. English: *"The Gemara likewise relates:"*
- **Ketubot 62a seg 7** — kept through clause 2 (R. Abbahu and the bathhouse),
  dropped 3-8: R. Yochanan on the stair, the Sages' question, and his answer
  *"what will I leave for my old age?"*. English: *"Similarly,"*

**This is the same defect as `work/2026-08-30-second-story-guard.md`, reached from the prompt rather than from a new labelling pass.** That item proposes
~40 lines of clause-role labeller used as a veto on the trim. This is the cheaper
first attempt at the same outcome. If it fails, that item is the answer and will
have earned it.

## What the corpus-wide screen says — do not skip this

Lesson 18: an expert sample locates a defect and never sizes it. Sized before the
change, with `scripts/screen_end_trim_depth.py` (structural, no API calls):

| | |
|---|---|
| end-trims across the three shipped v11 runs | **50** |
| depth >= 4 (candidates) | **13 (26%)** |
| **judged by eye to be a second story** | **2 (4%)** — 62a, 105b |

**Depth over-selects by roughly 6x, and the false candidates are the dangerous
kind.** Four of the 13 — Ketubot 67b seg 3, 77b seg 11, Kiddushin 72a seg 3, and in
part 60b seg 9 — are **amoraic legal debate**: `אָמַר אַבָּיֵי ... אֲמַר לֵיהּ רַב אַדָּא בַּר מַתְנָא`,
chains of attributions, a question and its answer. They carry **names and dialogue**
and the prompt trims them correctly today.

So the rule must key on **events**, not on names or speech. A first draft of this
change said *"its own characters and its own events or dialogue"* and would have
kept all four. That is Jeff's own complaint about Wave 3 — *"crude criteria, such as
the word אלא or a rabbi's name automatically signalling the story's end"* — in
mirror image. The shipped wording adds an explicit second line naming amoraic debate
as the confusable case.

## Method

**Steps 2-5 are one command.** `scripts/run_parallel_rule_experiment.py` runs the
arms, the same-code repeats, both blind rulers split by direction, the corrections
ruler apart, the two motivating cases and the three lookalikes, and re-screens — so
the parts that make the result trustworthy cannot be skipped by whoever has the key.
It refuses without a `GOOGLE_API_KEY` and `--dry-run` verifies the plan with no calls.

1. `src/story_detector_v11.py` — split the parallel rule in two: a bare mention is
   trimmed; a full incident is kept; **judge on events, never on names or speech**.
2. Re-run Wave 5 clause spans on Ketubot 2-60, Ketubot 61-112 and Kiddushin
   (`gemini-3.7-flash`, `thinking_level=HIGH` — the configuration in
   `docs/capabilities/4_boundaries.md`), writing to a scratch path.
3. Score against **both blind rulers**, reported apart from the corrections ruler
   (Lesson 24), and **split by direction** — the aggregate hides the effect.
4. Same-code repeat before attributing any movement (Lesson 22).
5. Re-run the screen and check 62a / 105b by eye.

## How you know it worked

- **Ketubot 62a and 105b keep their second story.** This is the point of the change.
- **Blind hit+near does not fall**, on either tractate, beyond the measured noise
  (0 points Ketubot, 0.8 Kiddushin).
- The four amoraic-debate candidates above **stay trimmed**. If they flip, the rule
  is keying on speech and the wording has failed.
- The screen's depth>=4 candidate count does not balloon.

## The prediction, stated before the run

**This change will probably cost points on the Ketubot end ruler**, and that may not
mean it is wrong. Keeping a second story makes the entry end *later* than Jeff's 2005
boundary for story one, and `docs/findings/2026-08-30-trim-asymmetry.md` scores
"later" as wrong under both standards. Ketubot ends are already the weak axis —
measured 2026-09-01 at **74% HIT / 77% HIT+NEAR**, against untrimmed's 74% / **80%**.

If hit+near falls *only* through the two second-story cases, that is the ruler
disagreeing with a fix that is right — record it and keep the change. If it falls
more widely, the rule is over-keeping and should be reverted rather than tuned.

## Guardrails

- **Never verify with the composite score** (Critical Rule 5). Counts and the blind
  rulers.
- `scripts/evaluate_golden.py` is immutable; always run it with `--output <scratch>`.
- Report the blind rulers and the corrections ruler separately (Lesson 24).
- No lexical rule for "parallel" in code. Markers appear in the screen as evidence
  only (Lesson 15).
- This fix produces a **merged entry**, not two separate stories — the text becomes
  visible again inside story one. Correct separation needs two stories to share one
  segment, which the segment-indexed detector cannot represent today. Same family as
  `work/2026-08-30-kiddushin-12a-dedup.md`, and the screen puts
  **Kiddushin 12a seg 13** in the candidate list independently.

## When done

Write the finding to `docs/findings/2026-09-01-parallel-story-rule.md`, add an
`## Outcome` section below, then `python3 scripts/board.py finish 2026-09-01-parallel-story-rule`.

## Outcome

**Measured 2026-09-03, and kept.**
Finding: [`2026-09-03-parallel-rule-measured.md`](../../docs/findings/2026-09-03-parallel-rule-measured.md).
Full log: `results/v11/parallel_rule/REPORT.txt`.

**Base and new are identical on every blind ruler row** — Ketubot 2-60 80%/85%, Ketubot
61-112 80%/84%, Kiddushin 85%/91%, and the same on the corrections set. The same-code
repeats move by one target on two of three sets, so the noise floor is ±1 and the change
is 0. **All five case checks pass**: 62a and 105b keep their second story, 67b, 77b and
72a stay trimmed.

### The prediction was wrong, and understanding why matters more than the result

The item predicted a cost on the Ketubot end ruler, on the reasoning that keeping a second
story makes an entry end later than Jeff's 2005 boundary. It cost nothing — **because the
two passages the rule rescues are not scorable targets in the blind sets.** The ruler is
blind to the thing the rule fixes.

So what the rulers establish is only that the rule **breaks nothing elsewhere**. That was
the real risk and it is now retired. What establishes that the rule *works* is five hand
checks, and it should be quoted that way and not as a ruler result.

### Why this ran now

It shipped **unmeasured** on 2026-09-01 — no API key in that session — and stayed live in
the detector for two days. A new tractate run would have confounded it with R-B1, the one
change since Gittin that does have a measured effect. **An unmeasured live change is a
confound with a countdown**, and the cost of clearing it was one command.

### Item 3 folded in

The end axis was ranked separately and is not opened as its own item. It is not
under-measured — Ketubot ends 72-75% against starts 84-88%, Kiddushin ends 84% against
starts 86%, measured again here. The Ketubot-only concentration argues against a general
end rule. It is one unanswered question (`jeff:boundary-end-rule`), and more measurement
will not answer it.
