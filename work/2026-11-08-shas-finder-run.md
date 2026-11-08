---
title: Run the story finder across all of Shas and build story list v1
capability: [triage, detection, classification, publication]
tractate: [eruvin]
blocked_by: []
awaiting: []
writes: [scripts/run_new_tractate.py, results/sefaria/, results/triage/, results/v11/, results/recall/, site/data/, scripts/build_site_data.py, tests/]
finding:
superseded_by:
---

# Run the story finder across all of Shas and build story list v1

**Self-contained.** Read [`FRAMEWORK.md`](../FRAMEWORK.md) first, then this. **Full plan:
[`docs/technical/shas-finder-plan.md`](../docs/technical/shas-finder-plan.md)**: the 37 tractates, page counts,
cost and time estimates, order, quality gates, and what Simon must do.

## The problem

The Septimus sign-up (`work/2026-11-08-septimus-signup.md`) needs every story in Shas. Four tractates have runs;
33 (4,610 pages) have none. List v1 = high-probability stories (YES + HIGH_CONFIDENCE; BORDERLINE separate;
LOW_CONFIDENCE excluded), dated.

## Method

Plan §4: pre-flight (runner generalised, token logging, no API calls) → Eruvin, scored once on its BLIND list →
the other 32 in plan order, one per commit → build list v1.

## How you know it worked

- Every tractate's output covers every Sefaria page, with zero `stage2_error` pages.
- Eruvin recall reported end-to-end and given-the-page-survived-triage, on the BLIND list, with denominators.
- Real cost per page measured from Eruvin's token log, and the rest re-quoted before it is spent.

## Guardrails

- No API calls until Simon approves the plan and cost. Gemini key via the credential form only.
- Never edit `scripts/evaluate_golden.py` or `results/canonical/*`. No detector or prompt change rides on this run.
- Same-code repeat before attributing any score movement (Lessons 22, 43). Recall on BLIND data only.
- Unreviewed tractates ship labelled "not yet reviewed".

## When done

Write the finding to `docs/findings/<date>-shas-finder-run.md`, add an `## Outcome` section
below, then `python3 scripts/board.py finish 2026-11-08-shas-finder-run`. **Never delete it.**
