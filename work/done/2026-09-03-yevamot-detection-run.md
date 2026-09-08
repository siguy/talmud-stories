---
title: Yevamot — the full detection run, measured against the blind list the day it runs
capability: [triage, detection]
tractate: [yevamot]
blocked_by: []
awaiting: []
writes: [results/triage/yevamot.json, results/v11/yevamot/yevamot_v11.json, results/recall/yevamot_jeff2005_matches.json, results/recall/yevamot_strict.json]
finding: docs/findings/2026-09-03-yevamot-first-run.md
superseded_by:
---

# Yevamot — the full detection run

**Self-contained.** Read [`FRAMEWORK.md`](../../FRAMEWORK.md) and
[`docs/technical/new_tractate_workflow.md`](../../docs/technical/new_tractate_workflow.md),
then this. Executes `2026-08-30-yevamot-triage` and `2026-08-30-yevamot-detection`
together, because Stage 1 and Stage 2 are one pipeline call — exactly as
[`2026-08-31-gittin-detection-run`](2026-08-31-gittin-detection-run.md) did.

## Method

`scripts/run_new_tractate.py --tractate yevamot`. Reads the cached
`results/sefaria/yevamot.json` (fetched 2026-08-30, never re-fetched), caches Stage 1 to
`results/triage/yevamot.json`, writes `results/v11/yevamot/yevamot_v11.json`.
Ground truth for few-shots is **Ketubot only** — every example is cross-tractate, so no
page being scored can appear in its own prompt (Lesson 2).

242 dapim / 102 blind stories, against Gittin's 178 / 111.

## How you know it worked

Structural gate `audit_text_spans.py --strict` passes; then blind recall against
`results/expert_lists/yevamot_2005.json`, **loose and strict together**
(`measure_strict_recall.py`), quoted as Triage and Detection *given the page survived
triage*, never pooled. A run with no blind measurement against it is not a result.

## Guardrails

- Never re-fetch what is cached; never re-triage without `--retriage`.
- Report recall end-to-end **and** conditioned — they differ, and put the deficit in
  different columns.
- Ask Jeff to keep his appendix separate BEFORE any review round (Lesson 29).

## When done

Finding to `docs/findings/`, add `## Outcome`, `python3 scripts/board.py finish`.

## Outcome

**Done.** Yevamot detected end to end in **21 minutes**; finding:
[`yevamot-first-run`](../../docs/findings/2026-09-03-yevamot-first-run.md).

- **Stage 1:** 242 pages, 141 skipped, 101 kept — **58% skip rate**, the highest of the
  four tractates. Cached to `results/triage/yevamot.json`.
- **Stage 2/4:** 190 proposals, **168 stories**, 22 `NOT_A_STORY`, 8 withheld by the
  Mishnah filter; 126 clause cuts, **0 mid-word, 100% clause-edge**, `--strict` passes.
- **Blind recall:** **94.1% loose / 89.2% strict** on Jeff's 102-story list. Triage lost
  **0**, so every miss is Detection's. Three of the six misses are the speech-act class —
  evidence for `jeff:speech-act-policy`, not defects.
- **The Mishnah filter costs one story here** (122b, the innkeeper), where on Gittin it
  cost none. The scope question now has a price on it.

**Two crashes, neither a model failure, each of which discarded a whole stage:** a string
segment index killed Stage 1 at page 228/242, and a `PROHIBITED_CONTENT` response with
`parts=None` killed Stage 2 at page 35/106. Both fixed; the triage cache now checkpoints
every 10 pages so Stage 1 resumes. **Stage 2 still has no checkpoint** — the next crash
there throws the run away again, and that is worth fixing before Eruvin.

**Not done:** Classification and Boundaries are unmeasurable until Jeff reviews Yevamot.
The five loose-only credits are named in `results/recall/yevamot_strict.json` and want
checking by name. The Gittin confidence-tier test is not replicated — it needs a
per-proposal join the strict harness does not emit.
