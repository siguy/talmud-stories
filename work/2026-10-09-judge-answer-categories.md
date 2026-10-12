---
title: Decide the judge's answer categories (confidence tiers?)
capability: [classification]
tractate: []
blocked_by: []
awaiting: []
writes: [src/prompts/judge_register_v1.md, scripts/judge_labelled_spans.py]
finding:
superseded_by:
---

# Decide the judge's answer categories

**Self-contained.** Read [`FRAMEWORK.md`](../FRAMEWORK.md) first, then this.

## The claim to test / the problem

The consensus judge (`src/prompts/judge_register_v1.md`) answers one of five:
`story`, `borderline`, `not`, `out_of_scope`, `unsure`. It gives **no confidence tier**,
while the detector and the goldens carry YES / HIGH_CONFIDENCE / LOW_CONFIDENCE /
BORDERLINE / NOT_A_STORY. Simon (2026-10-09): think about whether these are the right
answer possibilities — they may be right; not checked now.

Facts to start from:
- Jeff's 2005 lists are a plain yes — no tiers, no borderline. A judge `borderline` on a
  list story is not a contradiction.
- In early rounds Jeff used "low confidence" and "borderline" as one category (L-042);
  only `borderline` became his column (R-C2).
- Strict vs loose on the 2026-09-28 run (`full_v2_*`): 826 passages both judges agree
  with him when story≈borderline, 751 strictly. Of the 75: 41 list `yes` → a judge said
  `borderline` (not a real conflict); 23 his `borderline` → both said `story` (real).
- The sureness/confidence field is already an open question for him
  (`work/2026-10-02-jeff-feature-questions.md`).

## Method

1. Decide what a confidence tier would be *scored against* — without his tiers there is no
   ground truth for it.
2. Decide whether `borderline` vs `story` disagreement should count as a judge split in
   routing (phase 2) or only `not` vs the rest.
3. Any change to the categories makes the next run non-comparable with `full_v2`/`full_v3`;
   do it as a new prompt version with a same-code baseline.

## How you know it worked

A written decision, with the comparability cost stated.

## Guardrails

Do not change `judge_register_v1.md` in place — version it.

## When done

Write the finding to `docs/findings/<date>-<slug>.md`, add an `## Outcome` section
below, and `git mv` this file to `work/done/`. **Never delete it.**
