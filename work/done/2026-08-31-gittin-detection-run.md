---
title: Gittin — the first full detection run on a tractate we have never detected on
capability: [triage, detection]
tractate: [gittin]
blocked_by: []
awaiting: []
writes: [results/triage/gittin.json, results/v11/gittin/gittin_v11.json, scripts/run_new_tractate.py, src/story_detector_v11.py]
finding: docs/findings/2026-08-31-gittin-first-run.md
superseded_by:
---

# Gittin — the first full detection run

**Self-contained.** Read [`FRAMEWORK.md`](../../FRAMEWORK.md) and
[`docs/technical/new_tractate_workflow.md`](../../docs/technical/new_tractate_workflow.md),
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

## Outcome

**Done.** Gittin detected end to end in **20 minutes**; finding:
[`gittin-first-run`](../../docs/findings/2026-08-31-gittin-first-run.md).

- **Stage 1:** 178 pages, 88 skipped, 90 kept — **49% skip rate**, in line with Ketubot
  (46%) and Kiddushin (41%) under the shipped `N>=1` rule. Cached to
  `results/triage/gittin.json`, so a re-run costs nothing.
- **Stage 2/4:** 158 proposals, **147 stories**, 11 `NOT_A_STORY`; 69 clause cuts,
  **0 mid-word, 100% clause-edge**, `--strict` gate passes.
- **Blind recall:** **100.0% loose / 96.4% strict** on Jeff's 112-story list. The loose
  figure is not the result — `scripts/measure_strict_recall.py` was written to say so,
  and it reproduces Kiddushin's banked 93.3%/83.3% exactly. Triage lost **0** of the 112.
- **The span validator fired on its first live run**: Gittin 38a proposed `16..0`,
  collapsed to `16..16` and marked `needs_review`. Same shape as `Ketubot 22a`.

Two things came out differently from the brief:

- **The pipeline could not have run at all.** Stage 4k called a Wave 4 method v11 does not
  have, so v11's `run_pipeline` raised `AttributeError` at the last step, after the full
  spend. v11 had only ever been driven by `run_wave5_clause_spans.py` on existing outputs.
  Fixed and pinned before any money was spent.
- **The board would have published a bare `100.0%`.** `board.py` fills its Detection cell
  from the loose harness, and no ruler exists for a tractate with no expert round. It now
  reads `results/recall/<t>_strict.json` when there is no ruler, so the matrix carries
  both figures.

**Not done:** Classification and Boundaries are unmeasurable until Jeff reviews Gittin —
both need verdicts, and `report_mishnah_filter_delta.py` needs a golden. The four
loose-only recall cases (38b, 46b, 57a x2) are named in `results/recall/gittin_strict.json`
and want checking by name.
