---
title: Review the boundaries of every story on the Septimus site (display only)
capability: [boundaries, publication]
tractate: []
blocked_by: []
awaiting: [jeff:boundary-end-rule]
writes: [scripts/review_site_boundaries.py, site/data/, results/shas_run/septimus_site_decisions.json, results/shas_run/site_summaries_written.json, results/site_notes/, tests/test_review_site_boundaries.py, tests/test_site_data.py, tests/test_site_notes.py, tests/expert_boundary_targets_2005_yevamot.json, docs/technical/septimus-signup-plan.md]
finding: docs/findings/2026-11-16-full-boundary-review.md
superseded_by:
---

# Review the boundaries of every story on the Septimus site

**Self-contained.** A fresh session executes this with no other context.
Read [`FRAMEWORK.md`](../../FRAMEWORK.md) first, then this, then the plan
[`docs/history/2026-11-15-PLAN-full-boundary-review.md`](../../docs/history/2026-11-15-PLAN-full-boundary-review.md).

## The claim to test / the problem

Many site stories carry the Gemara's legal argument before or after the events, and some are cut off or split across
two cards (Simon 2026-11-15: "we don't need the legal argument"; "if this is actually 1 story, then make it 1"). Run
`bfix1` fixed the 154 the note-drafters flagged. This reviews the rest the same way. Display only: it writes
`site/data/boundary_extensions.json` and the merge list in `results/shas_run/septimus_site_decisions.json`, never a
golden, a run, `evaluate_golden.py` or a story id.

## Decisions (Simon, 2026-11-15, all as recommended)

1. Jeff-validated tractates (Ketubot, Kiddushin, Gittin) may be trimmed, display only; cuts of a segment Jeff listed
   go to the second reader, and Simon sees the list before apply.
2. A ruling that ends the story: keep it when it is the outcome of the events, cut the Gemara's discussion of it.
3. The 148 stories `bfix1` decided are not re-reviewed (`export --after bfix1`).
4. Gates as written in the plan, step 3 and step 5.
5. Cut ends in calibration are sorted by a different model from the reviewer; Simon reads the "narrative lost" pile.
6. Redrafted notes: approved if the checks pass and the drafter raised no flag.
7. Simon reads ~20 before/after pairs (`sample-html`) after the second reader, before the main apply.

## Method

The plan, in order: script changes with tests; calibration on Ketubot, then Kiddushin + Gittin + Yevamot on a frozen
prompt, gated (stop and report to Simon on a fail); the main run; second reader; Simon's sample; apply; note redrafts;
tests; finding.

## How you know it worked

Every site story reviewed or skipped by name (`skipped.json` per run); the calibration gates pass; the second-reader
gate passes; `python3 -m pytest tests/ -q --deselect tests/test_wave4_text_spans.py::test_wave4_ship_gate` green.

## Guardrails

- The reader-feedback plan writes several of the same files: the two do not run in parallel on them.
- A merge cannot be fully undone (story ids never revive); trims and extensions can, from `applied.json`.
- Never publish between apply and note approval: a changed story has no approved note until redrafted.

## When done

Write the finding to `docs/findings/<date>-<slug>.md`, add an `## Outcome` section
below, and `python3 scripts/board.py finish 2026-11-15-full-boundary-review`. **Never delete it.**

## Outcome

Done 2026-11-16 (finding `docs/findings/2026-11-16-full-boundary-review.md`). Every site story reviewed or skipped by
name. Calibration gate passed on a frozen prompt: 0 narrative lost of 190 CIRCULAR and 54 BLIND (Yevamot) measurable
stories, 207/208 good boundaries left alone, no merge of two of Jeff's stories. Second reader: 5.6% disagreement on
random adjusts (gate 10%), 9 changes held. Simon read 20 pairs and approved. Applied: 110 stories changed (6 merges);
site 1,786 stories, 0 segments in two cards; 104 notes redrafted, 102 approved. One applied change undone by hand
(Taanit 23b:9 widened over a removed passage) and the script now refuses that case.

**Why the change rate was low, and what is left:** the reviewer prefers the smallest change and must keep a segment
that mixes story with argument. The second reader still saw legal argument in 30% of random keeps. Trimming further
at segment level, or cutting inside a segment, is a separate decision for Simon.
