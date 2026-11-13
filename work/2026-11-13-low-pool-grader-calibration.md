---
title: Calibrate the Claude grader before it promotes LOW proposals to the Septimus site
capability: [classification, publication]
tractate: [ketubot, kiddushin, gittin, yevamot, eruvin]
blocked_by: []
awaiting: []
writes: [scripts/calibrate_low_pool_grader.py, results/shas_run/low_pool/calibration/]
finding:
superseded_by:
---

# Calibrate the Claude grader before it promotes LOW proposals to the Septimus site

**Self-contained.** A fresh session executes this with no other context.
Read [`FRAMEWORK.md`](../FRAMEWORK.md) first, then this.

## The claim to test / the problem

About three in four stories missing from the site were found and graded LOW
([finding](../docs/findings/2026-11-13-how-many-stories-we-miss.md)). The proposal: let the Claude
grader (the consensus judge, [`judge_register_v2.md`](../src/prompts/judge_register_v2.md) at the sha
pinned as `JUDGE_PROMPT_SHA` in `scripts/check_tractate_run.py`, `88e8fff62716`) promote a LOW span it
calls `story`. That prompt has never been scored against Jeff. **Claim: on spans Jeff has ruled on,
when the grader says `story`, Jeff says yes often enough for a definite-only site.**

Truth rule: Jeff `borderline` counts as **not** a story (the site ships definite stories only, L-045).

## Method

`scripts/calibrate_low_pool_grader.py` (no model calls) builds the set and the grader prompts:

- **C1, CIRCULAR** (158 spans): every Ketubot / Kiddushin / Gittin passage the detector showed Jeff as
  LOW_CONFIDENCE, truth = his last verdict on it (149 spans; the finding's 153 counts 4 duplicate
  ruler rows on 3 shared spans). Plus golden LOW stories that carry a counted 2005-list story the
  site misses at that grade (61 list stories; the finding says 60); 49 of those spans are already
  in the first group and get the tag. The 9 new ones take the list as truth. Tag: `golden_low_on_list`.
- **C2, BLIND** (142 spans): Eruvin + Yevamot v14 units that are LOW in at least one run or split
  between runs (pools P1-P4), not already on the site. Truth comes from his 2005 list, read through
  `superseded_by_rule.json`: overlapping a counted story = yes, a story he has since ruled
  borderline = borderline, one he ruled not = no, no list story = `unknown` (counted only as a lower bound).
- Two independent exports (`pass1` seed 1, `pass2` seed 2, batches of 20, ids hidden). Graders
  answer each pass separately. `import` validates every answer with the judge's own `ask()`, and a failed or
  invalid answer is counted, never scored (Lesson 21). `score` reports precision and Wilson 95% per group and per pass,
  for "both passes say story", and how stable the verdicts are between passes.

## How you know it worked

**Ship bar:** on the spans the grader calls `story` with known truth, precision >= **0.90** and Wilson
95% lower bound >= **0.80**, held in **both passes** (and on the both-passes-story rule). Report C1
and C2 separately: C1 is circular, because the register was written from these verdicts. C2's `unknown` spans
are a lower bound only. Report `golden_low_on_list` separately too.

## Guardrails

- Never run `evaluate_golden.py`. Never edit the judge prompt or `STORY_RULES.md` during the test:
  `import` refuses if the prompt sha moved since export.
- Graders read only `<pass>/system_prompt.md` and `<pass>/batches/NNN/*.txt`. They never read `keys/`
  or `manifest.json`, because those hold the ids and the truth.
- A pass is one grader per batch, and the two passes use different graders.

## When done

Write the finding to `docs/findings/<date>-<slug>.md`, add an `## Outcome` section
below, and `git mv` this file to `work/done/`. **Never delete it.**

## Results (2026-11-13, calibration step — item stays open for the pool grading)

Both passes graded, 300/300 valid each. "Both passes say story": 32/33 = 0.97 (Wilson 0.85–1.00), **meets the bar**.
Recall of Jeff's yes is only 32/141: the grader is strict. Finding: `docs/findings/2026-11-13-low-pool-grader-calibration.md`.
