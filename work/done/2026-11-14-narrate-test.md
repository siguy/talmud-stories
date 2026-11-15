---
title: The narrate test — can writing a summary tell a story from a non-story, and find its borders?
capability: [classification, boundaries]
tractate: [ketubot, kiddushin, gittin, eruvin, yevamot]
blocked_by: []
awaiting: []
writes: [results/shas_run/narrate_test/, scripts/narrate_test.py, tests/test_narrate_test.py]
finding: docs/findings/2026-11-14-narrate-test.md
superseded_by:
---

# The narrate test

**Self-contained.** A fresh session executes this with no other context.
Read [`FRAMEWORK.md`](../../FRAMEWORK.md) first, then this.

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

## Outcome

Run 2026-11-14 with Sonnet narrators (two passes, 493 units each, all answers valid). Finding:
[`docs/findings/2026-11-14-narrate-test.md`](../../docs/findings/2026-11-14-narrate-test.md).

- **Classification: fails the bar.** `can_narrate == yes` recovers 80/141 and 84/141 of Jeff's yes (grader: 32/141) but at
  precision 0.81 / 0.80 (grader 0.97); the combined second-judge rule gets 0.83-0.84 (Wilson LB 0.74-0.76), below the 0.90 / 0.80 bar.
  BLIND (C2) precision 0.91 / 0.85 on n=22 / 26. Useful as a recall aid for the review queue, not for shipping.
- **Boundaries: no gain.** The narrator's needed-segments span equals the detector's in ~89% of units (it is anchored by the PASSAGE
  marker); Ketubot ends move by 2 targets (two MISS->HIT, one HIT->MISS), starts are level, both passes agree. The Ketubot end
  deficit is not recovered. Not an independent border judge as prompted.
- **Why / confounds:** the grader ran on Opus with the rules and a +-1 window; the narrator on Sonnet, no rules, +-3 window, so the
  comparison is model + prompt + context together and not attributable to narrating alone. Untried: Opus narrator; an unmarked window.
- Nothing ships; site and detector untouched. Reproduce: `python3 scripts/narrate_test.py build|export|import|score`.

### Addendum (same day, at Simon's request)

- **Opus on the grader's view (+-1, marked, no rules):** the same precision as Sonnet (0.80), recall 0.61-0.65. So the first run's gap to the grader was not
  the model or the context: it is the rules.
- **Narrate-then-rules (hybrid, Opus):** `story` precision 0.93-0.95 (Wilson LB 0.82-0.85), recall 0.26-0.30 -- it meets the second-judge bar
  but only by becoming the grader; the combined rule adds ~10 of Jeff's 141 yes (recall 0.23 -> 0.30). Hybrid stability 96% yes-or-not.
- **Unmarked-window border test (Opus):** the narrator's story equals the detector's span in 83-86% of windows without any marker (not an
  echo: independent agreement), and net movement against Jeff's blind targets is 1-2 per direction. The Ketubot end deficit is not a
  narration problem. Findings: `docs/findings/2026-11-14-narrate-test.md`, Addendum 2.
