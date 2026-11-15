---
title: The narrate test — can writing a summary tell a story from a non-story, and find its borders?
capability: [classification, boundaries]
tractate: [ketubot, kiddushin, gittin, eruvin, yevamot]
blocked_by: []
awaiting: []
writes: [results/shas_run/narrate_test/, scripts/narrate_test.py, tests/test_narrate_test.py]
finding:
superseded_by:
---

# The narrate test

**Self-contained.** A fresh session executes this with no other context.
Read [`FRAMEWORK.md`](../FRAMEWORK.md) first, then this.

## The claim to test / the problem

On 2026-11-14 a writer filled 85 empty card summaries (`results/shas_run/site_summaries_written.json`) and, unprompted,
flagged ~20 of them as not reading like stories (no events, legal dialogue, habits). Writing a summary of the
Taanit 5b card also exposed that it stops before its punchline. **Indicated, from one batch:** the act of
*narrating* a passage is a judge of story-ness and of extent, independent of the rule register.

Two claims, each measurable against Jeff:
1. **Classification.** Whether a passage can be narrated as *someone did something, something turned, it ended
   somehow* predicts Jeff's yes/no — and in particular recovers the Jeff-yes stories the rule-based grader called
   `borderline` (calibration: grader recall 32/141, `docs/findings/2026-11-13-low-pool-grader-calibration.md`).
2. **Boundaries.** The segments a narrator *needs* to tell the story (including ones outside the card) locate its
   start and end better than the detector's span.

## Method

A narrator prompt, deliberately **blind to `STORY_RULES.md`** (so it is an independent signal, not the grader again).
Input: the card's segments, marked, plus 3 segments of context either side. Output, per passage:
`{can_narrate: yes|partial|no, actor, event, turn, outcome, needed_segments: [...], summary, missing: "what the
summary needed that the window lacked"}`. Claude Code subagents, batches of 20, two passes (Lesson 22), ids hidden,
same harness pattern as `scripts/calibrate_low_pool_grader.py`.

- **Classification set:** the 300-span calibration manifest (`results/shas_run/low_pool/calibration/manifest.json`).
  Score `can_narrate` against Jeff (borderline = not a story, the site rule); cross-tab against the grader's verdicts.
- **Boundary set:** the blind targets `tests/expert_boundary_targets_2005.json` (Ketubot, 294) and
  `..._kiddushin.json` (176). Window = detector span ± 3. Predicted start/end = min/max of `needed_segments`.
  Score with `scripts/score_boundary_targets.py --by-direction`, beside the detector's own spans.

## How you know it worked

- Classification: `can_narrate == yes` precision vs Jeff ≥ the grader's 0.95 **and** recall clearly above 32/141;
  or, as a second judge, `grader story OR (narrate yes AND grader borderline)` keeps precision ≥ 0.90 (Wilson LB ≥ 0.80).
- Boundaries: beats the detector on ends (Ketubot's whole deficit is ends) without losing starts, both passes.
- Report BLIND (Eruvin/Yevamot C2, the 2005 boundary sets) and CIRCULAR (C1) separately. Measured, not indicated.

## Guardrails

- Never run `evaluate_golden.py`. The narrator never reads `STORY_RULES.md`, `keys/` or the manifest.
- Nothing ships from this item. A site or detector change is a separate decision by Simon.
- Never ask for character offsets (Lesson 16): `needed_segments` are whole segments.

## When done

Write the finding to `docs/findings/<date>-<slug>.md`, add an `## Outcome` section
below, and `git mv` this file to `work/done/`. **Never delete it.**
