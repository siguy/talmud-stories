---
title: Gittin — the first full detection run on a tractate we have never detected on
capability: [triage, detection]
tractate: [gittin]
blocked_by: []
awaiting: []
writes: [results/triage/gittin.json, results/v11/gittin/gittin_v11.json, scripts/run_new_tractate.py, src/story_detector_v11.py]
finding:
superseded_by:
---

# Gittin — the first full detection run

**Self-contained.** Read [`FRAMEWORK.md`](../FRAMEWORK.md) and
[`docs/technical/new_tractate_workflow.md`](../docs/technical/new_tractate_workflow.md),
then this. Executes `2026-08-30-gittin-triage` and `2026-08-30-gittin-detection`
together, because Stage 1 and Stage 2 are one pipeline call.

## Why Gittin

All three fetched tractates are candidates. Gittin is the smallest (**178 dapim**,
2,990 segments) and carries the **largest blind list** (**112 stories**, every entry
blind, checked against the appendix) — the most ground truth per API call. Yevamot (242
dapim / 102 stories) and Eruvin (207 / 74) follow.

## The blocker found on the way

`run_pipeline()` Stage 4k called `self.extract_text_spans_via_llm(...)` — **Wave 4's
char-offset mechanism, which v11 does not have.** With a client attached the pipeline
raised `AttributeError` at the last step, after the whole Stage 1/2/4 spend. v11 had only
ever been driven by `run_wave5_clause_spans.py` on existing outputs, so nothing had run it
end to end. Fixed to call the clause mechanism, and pinned by
`tests/test_pipeline_stage4k_wiring.py`.

## Method

`scripts/run_new_tractate.py --tractate gittin`, parameterized over the three fetched
tractates. Reads `results/sefaria/gittin.json`, caches Stage 1 to
`results/triage/gittin.json`, writes `results/v11/gittin/gittin_v11.json`.

Ground truth for few-shots is **Ketubot only** — every example is cross-tractate, so no
page being scored can appear in its own prompt (Lesson 2).

## How you know it worked

Structural gate `audit_text_spans.py --strict` passes; then **Step 7b of the workflow —
blind recall against `results/expert_lists/gittin_2005.json`**, quoted as Triage and
Detection *given the page survived triage*, never pooled. A run with no blind measurement
against it is not a result.

## Guardrails

- Never re-fetch what is cached; never re-triage without `--retriage`.
- Report recall end-to-end **and** conditioned — they differ, and put the deficit in
  different columns.
- Ask Jeff to keep his appendix separate BEFORE any review round (Lesson 29).
