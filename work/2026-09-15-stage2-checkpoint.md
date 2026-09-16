---
title: Stage 2 has no checkpoint — a 503 at page 32 discards 31 pages of detection
capability: [detection]
tractate: []
blocked_by: []
awaiting: []
writes: [scripts/run_new_tractate.py, src/story_detector_v11.py, tests/test_stage2_checkpoint.py]
finding:
superseded_by:
---

# Stage 2 has no checkpoint

**Self-contained.** Read [`FRAMEWORK.md`](../FRAMEWORK.md), then this.
**Cost: small.** **Depends on Jeff: no.**

## The problem

Stage 1 checkpoints every 10 pages (added 2026-09-03 after a crash ate 18 minutes). Stage
2 does not. It has now thrown away a run three times: twice on 2026-09-03 (unhandled
response shapes), once on 2026-09-15 (a Google `503 UNAVAILABLE` at Kiddushin page 32 of
66). Each time the fix was to run the whole arm again. Transient server errors are not
going to stop.

## Method

1. Write `results[]` to `<output>.partial.json` every N pages, with the page index.
2. On start, if the partial exists for the same output path and the same page list,
   resume from it — and **say so in the log and in `run_meta`** (`resumed_from_page`).
3. Retry a `5xx` from the API up to 3 times with backoff before it becomes fatal; a
   `4xx` stays fatal.
4. A page whose Stage 2 call failed after retries is recorded with `stage2_error`, not as
   "no stories" (Lesson 21), and the run continues.

## How you know it worked

- Failure-injection test: kill the run at page K, restart, `run_meta.resumed_from_page == K`,
  and the output is byte-identical to an uninterrupted run (the runs are deterministic).
- A page with an injected persistent failure appears with `stage2_error` and the outcome
  buckets sum to pages processed.

## Guardrails

- Never resume across a code or prompt change: store a hash of the detection prompt in
  the partial and refuse to resume if it differs.
- Never silently resume: the log line and the `run_meta` field are the point.

## When done

Finding, `## Outcome`, `python3 scripts/board.py finish 2026-09-15-stage2-checkpoint`.
