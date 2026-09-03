---
title: Stage 2 checkpointing — a crashed detection run must resume, not restart
capability: [detection]
tractate: []
blocked_by: []
awaiting: []
writes: [src/story_detector_v11.py, scripts/run_new_tractate.py, tests/test_stage2_checkpoint.py, docs/capabilities/2_detection.md, results/stage2/]
finding:
superseded_by:
---

# Stage 2 checkpointing

**Self-contained.** Read [`FRAMEWORK.md`](../../FRAMEWORK.md), then
[`docs/findings/2026-09-03-yevamot-first-run.md`](../../docs/findings/2026-09-03-yevamot-first-run.md),
then this.

## The problem

`V7StoryDetector.run_pipeline()` loops over every examined page making Stage 2 LLM calls
and holds the results in memory until the whole tractate is done. Any raise inside that
loop discards every page detected so far. It did, twice on 2026-09-03 during the Yevamot
run — the second time at page 35 of 106, on a `PROHIBITED_CONTENT` response with
`parts=None`.

Stage 1 got the durable fix that day: `scripts/run_new_tractate.py` writes
`results/triage/<t>.json` every `CHECKPOINT=10` pages, so a re-run resumes. Stage 2 has
no equivalent. The next unhandled response shape throws the run away again, and there
will be a next one.

## Method

Persist Stage 2 per page, resume from it, and change nothing else about the run.

The constraint that decides the design: **Stage 4 must see exactly the inputs it would
have seen.** It runs over the whole tractate after Stage 2 — cross-page merge, stitching,
the Mishnah filter, snap/trim, Wave 5 clause spans — and reads neighbouring pages'
results. A resume that perturbs any Stage 4 input silently changes the output.

## How you know it worked

A resumed run must produce **byte-identical** output to an uninterrupted one, on the same
fixture with the same fake client. Plus a failure-injection test in the style of
`tests/test_wave5b_runner_outcomes.py` and `tests/test_examine_all_pages.py`: a page whose
call fails must never be persisted as a page where nothing was found (Lesson 21).

## Guardrails

- No API calls. Fixtures and a fake client only.
- `scripts/evaluate_golden.py` is immutable; nothing here touches it.
- v7–v10 are frozen ship points; only `src/story_detector_v11.py` may be edited.
- Never delete anything under `results/`.

## When done

`## Outcome` below, `python3 scripts/board.py finish 2026-09-03-stage2-checkpoint`.

## Outcome

**Done and shipped.** `src/story_detector_v11.py` (the active detector) + one caller,
`scripts/run_new_tractate.py`, guarded by `tests/test_stage2_checkpoint.py` (10 tests, no
API calls). No finding document: this is infrastructure, not a measurement — the history
row is in [`docs/capabilities/2_detection.md`](../../docs/capabilities/2_detection.md).

**The design.** `run_pipeline()` gains two optional arguments and no file handles.
`on_page_detected(ref, digest, stories, span_repairs)` fires after each page Stage 2
**successfully** completes; `resume_stories` is what a previous run persisted. The runner
owns the file: `results/stage2/<tractate>.json`, written every `CHECKPOINT=10` pages and
once more on the way out of an exception — the same shape as the Stage 1 fix beside it.

**Why a resume reproduces the run exactly.** Stage 2 per page is a pure function of the
page, its triage labels, and its two neighbours' segments and labels. None of those is
read back from Stage 2's own output, so a resumed page contributes precisely what the
original call contributed and Stage 4 — merge, stitch, Mishnah filter, snap/trim, clause
spans — sees inputs it cannot distinguish. Pinned:
`test_resume_after_crash_is_byte_identical_except_the_field_that_says_it_resumed`.

**Staleness.** The per-page digest is a SHA-256 of the **built prompt**, plus model and
thinking level. Exact by construction, and it needs no version bump ever: a prompt edit, a
few-shot change, a re-fetched daf or a changed triage label on the page *or either
neighbour* moves it, and the page is re-asked. The file also carries a coarse header
(schema, tractate, model, thinking level, detector module); a mismatch **raises** rather
than blending two detectors' output into one file, and deletes nothing.

**A failure is never cached.** `_call_stage2` returns `[]` when neither attempt parses,
and an empty response returns `""` — both indistinguishable from a page holding no
stories. Both are now counted (`parse_failures`, `empty_responses`), and a page whose
counters moved is kept in the run but **withheld from the cache**, so a resume re-asks
instead of inheriting a silence (Lesson 21). Verified by disabling the guard and watching
two tests fail (Lesson 31). `stage2_summary` buckets are asserted exclusive and to sum to
the pages walked.

### Rejected, and why

- **A cache written by the detector itself.** Simpler by a few lines, but it puts file
  I/O, atomic-write and staleness policy into a class that has none, and it would have to
  invent a path convention the runner already owns. The callback keeps the detector a
  pure function of its arguments, which is also what makes the byte-identity test cheap.
- **The runner driving Stage 2 page by page.** It would have to rebuild the
  pages-to-examine set (triage rule + story-introducer override) and the prev/next context
  blocks, which live in `run_pipeline`. Two copies of that logic is exactly how a resume
  starts changing Stage 4's inputs without anyone noticing.
- **Keying the cache on a detector version string.** Someone has to remember to bump it,
  and nobody will. Hashing the prompt is strictly stronger and self-maintaining.
- **Checkpointing Stage 4's LLM steps too** (4d stitch, 4f continuation, 4k clause spans).
  Out of scope and left undone deliberately: they run after the whole corpus, so a crash
  there loses minutes rather than the tractate, and they mutate `all_results` in place —
  resuming them needs a different unit than "a page". **Stated as a limitation, not
  solved.**

### Known limitations

- A crash inside Stage 4 still discards Stage 4; Stage 2 survives it, which is the
  expensive half.
- The cache persists after a successful run. Re-running the same tractate therefore
  reuses Stage 2 unless `--fresh-stage2` is passed — a real hazard for anyone wanting a
  second sample of a nondeterministic model (Lesson 22). Mitigated, not removed: the run
  says so in `stage2_summary` and `run_meta.stage2_resumed_pages`, and the load is logged.
- Nothing has run against a live API. Every test uses fixtures and a fake client.
