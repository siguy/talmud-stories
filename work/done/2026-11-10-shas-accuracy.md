---
title: Did we find the stories across Shas? Definition of done, stats, reading-list review
capability: [triage, detection, classification, publication]
tractate: []
blocked_by: []
awaiting: []
writes: [scripts/measure_shas_accuracy.py, tests/test_shas_accuracy.py, results/shas_run/accuracy/, docs/findings/2026-11-10-shas-accuracy.md, CLAUDE.md]
finding: docs/findings/2026-11-10-shas-accuracy.md
superseded_by:
---

# Did we find the stories across Shas?

**Self-contained.** A fresh session executes this with no other context.
Read [`FRAMEWORK.md`](../../FRAMEWORK.md) first, then this.

## The claim to test / the problem

Simon asked for an independent, numbers-backed answer: did the 2026-11 Shas run find the stories accurately,
how was that validated, and what are the stats. Review the reading lists too.

## Method

Define "done and verified" first (recall, precision, coverage, generalisation; BLIND vs CIRCULAR), then measure with
one re-runnable script, no model calls: `python3 scripts/measure_shas_accuracy.py --out results/shas_run/accuracy/shas_accuracy.json`.

## How you know it worked

Every number in the finding is in that JSON; the script refuses if a shipped unlisted story is ungraded.

## Guardrails

No Claude API, no Gemini calls, no edits to `src/`, `evaluate_golden.py` untouched, site build untouched.

## When done

Write the finding, add an Outcome, `board.py finish`.

## Outcome

**Not verified; partly measured.** Eruvin (held out, blind): detector proposes 90.5% of Jeff's 74 stories in each
run (Triage 97.3%, Detection given triage 93.1%) — under the provisional 95% gate. **The site shows 49/74 (66%)**;
Yevamot 64/100. The loss is grading (42 of 61 site-misses were proposed as stories but not definite in both runs).
Precision ~85% is indicated, not measured: circular 87.4% on older versions, blind lower bound 68–73%, Claude-graded
81–89%. Coverage measured complete: 4,787 pages, 0 failed calls. Biblical drops 45/45 correct; 5 shipped
non-stories are all Gemini-OOS + Claude-not, which the site rule ignores. **Why not verified:** no expert sample of
shipped v14 stories exists, and 32 of 37 tractates have no list. Also found: the recall harness raises on the Ketubot
.doc under `--standard current`; the run finding's 93.7% does not reproduce (93.1%).
