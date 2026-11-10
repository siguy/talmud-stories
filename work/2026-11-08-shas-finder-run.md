---
title: Run the story finder across all of Shas and build story list v1
capability: [triage, detection, classification, publication]
tractate: [eruvin]
blocked_by: []
awaiting: []
writes: [scripts/run_new_tractate.py, scripts/run_shas.py, scripts/check_tractate_run.py, scripts/tractates.py, scripts/fetch_tractate_pages.py, scripts/judge_detector_spans.py, scripts/build_site_data.py, site/, results/sefaria/, results/triage/, results/v14/, results/consensus/, results/shas_run/, tests/]
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

**Current plan: [`docs/history/2026-11-09-PLAN-shas-run.md`](../docs/history/2026-11-09-PLAN-shas-run.md)**: v14, two runs
per tractate, standard Gemini tier, deadline Sunday 2026-11-15. It supersedes the v11 / one-run method below.
Pre-flight code (plan §4 items 1-7) is built: `scripts/run_shas.py` (driver), `scripts/check_tractate_run.py` (gates G1-G6),
`scripts/tractates.py` (the one tractate table). `site/` is in `writes:` because the sign-up work also writes it
(`board.py lanes` shows that conflict).

*Older method, kept for the record:*

Plan §4: pre-flight (runner generalised, token logging, no API calls) → Berakhot as the cost calibration → the other
31 in plan order, one per commit → build list v1. Eruvin was run on Simon's machine and is held for Jeff.

## How you know it worked

- Every tractate's output covers every Sefaria page, with zero `stage2_error` pages.
- When Jeff releases Eruvin: its recall reported end-to-end and given-triage, on the BLIND list, with denominators.
- Real cost per page measured from Berakhot's token log, and the rest re-quoted before it is spent.

## Guardrails

- No API calls until Simon approves the plan and cost. Gemini key via the credential form only.
- Never edit `scripts/evaluate_golden.py` or `results/canonical/*`. No detector or prompt change rides on this run.
- Same-code repeat before attributing any score movement (Lessons 22, 43). Recall on BLIND data only.
- Unreviewed tractates ship labelled "not yet reviewed".

## When done

Write the finding to `docs/findings/<date>-shas-finder-run.md`, add an `## Outcome` section
below, then `python3 scripts/board.py finish 2026-11-08-shas-finder-run`. **Never delete it.**
