---
title: Two pre-flight fixes before a new tractate — validate proposed spans, and stop the Mishnah key from being silently invisible
capability: [detection, boundaries]
tractate: []
blocked_by: []
awaiting: []
finding: docs/findings/2026-08-31-span-bounds-and-mishnah-readers.md
superseded_by:
---

# Two pre-flight fixes before a new tractate

**Self-contained.** Read [`FRAMEWORK.md`](../../FRAMEWORK.md) first, then this.

Both defects are latent on Ketubot/Kiddushin and would land unmeasured on a virgin
tractate, where there is no prior run to diff against.

## The problem

**1. Nothing validates that a proposed span lies within its page.** Stage 2 proposed
`Ketubot 112b, start_segment -2, end_segment 0`. Reported 2026-08-31
([`triage-recall-price`](../../docs/findings/2026-08-31-triage-recall-price.md)), hit again
independently by the 2026-09-01 proposal screen, still unfixed. Every Stage 4
post-processor indexes `segments[start:end+1]`, where a negative index silently means
*from the end of the page*.

**2. `mishnah_stories[]` readers are partially fixed and the docs still say otherwise.**
The recall harness and the axis review UI read the key; `build_ruler.py` deliberately does
not fold it in. But `score_boundary_targets.py` reads only `stories`, so a withheld story
is an unscorable boundary that looks like a boundary we failed to produce — and
`new_tractate_workflow.md` Step 7 still asserts "no harness or UI reads it", which is now
false in a way that stops a reader checking.

## Method

1. `validate_story_spans()` in `src/story_detector_v11.py` (v11 only; v7–v10 stay frozen).
   Clamp a span that overlaps the page, drop one that does not, **count and name** every
   repair (Lesson 38), surface it in the run output.
2. Make `score_boundary_targets.py` read `mishnah_stories` explicitly and report the
   withheld separately — never pooled into the score.
3. Correct Step 7 of the workflow doc to say which readers see the key today.

## How you know it worked

Failure-injection tests: a page carrying `start_segment -2` must not reach Stage 4, and
must be *reported*, not dropped in silence. Boundary scores on both tractates unchanged
(no withheld story carries a target today) with the withheld line printed.

## Guardrails

`evaluate_golden.py` is immutable — the Mishnah delta stays with
`report_mishnah_filter_delta.py`. No detector prompt changes; no API calls needed.
Full suite before stopping.

## Outcome

**Both shipped. No API calls, no prompt change, no shipped score moved.** Finding:
[`span_bounds_and_mishnah_readers`](../../docs/findings/2026-08-31-span-bounds-and-mishnah-readers.md).

**1. Span bounds.** `validate_story_spans()` in `src/story_detector_v11.py`, called from
`detect_stories()` so both Stage 2 passes and `run_triage_recall_price.py` are covered.
Clamps what overlaps the page, drops what does not, and writes every repair to the run as
`span_repairs` (always present, `[]` included). 15 tests, written first and watched fail.

Two things came out differently from the brief:

- **A second malformed span, previously unknown.** Auditing every run on disk turned up
  `Ketubot 22a`, `10..0` on an 11-segment page — a reversed span with a real story behind
  it. The corpus holds exactly two malformed spans, not one.
- **The reversed case is not dropped.** The brief implied a uniform drop. Deleting 22a
  would spend a Detection miss to avoid a Boundaries error, which is the wrong trade here;
  it collapses to the valid start and is stamped `needs_review` instead. Documented as a
  judgment call, not folded in quietly.

**2. `mishnah_stories` readers.** `score_boundary_targets.py` now reports a `WITHHELD`
bucket, in neither the score nor `N/A`. **The brief's guess that no withheld story carries
a target today was wrong**: 2 of the 294 blind Ketubot targets move `N/A → WITHHELD`, both
on `Ketubot 54b`'s chapter-boundary mis-tag, which the current tagger no longer withholds
(`8fd68de`) — so the bucket named a stale artifact's known defect instead of burying it.
Kiddushin **85% / 91%** and Ketubot 61–112 **80% / 84%** are unchanged, as claimed.
`CLAUDE.md` and `new_tractate_workflow.md` Step 7 lose the now-false *"no harness or UI
reads that key"* and carry a per-reader table instead — including that
`evaluate_golden.py` is still blind and still immutable.

**Not done, deliberately:** Stage 4's own post-processors are not bounds-checked. Both
defects entered as model output at Stage 2, and widening the check to every mutation in
the pipeline is a different, larger piece of work.
