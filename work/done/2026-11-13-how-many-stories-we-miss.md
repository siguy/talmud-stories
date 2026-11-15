---
title: How many real stories are missing from the Septimus site?
capability: [triage, detection, classification, publication]
tractate: [ketubot, kiddushin, gittin, yevamot, eruvin]
blocked_by: []
awaiting: [jeff:miss-rate]
writes: [CLAUDE.md, scripts/measure_site_misses.py, scripts/measure_shas_accuracy.py, results/shas_run/accuracy/site_misses.json, results/shas_run/accuracy/shas_accuracy.json, docs/findings/2026-11-13-how-many-stories-we-miss.md, docs/findings/2026-11-10-shas-accuracy.md, comms/JEFF.md, work/2026-11-13-how-many-stories-we-miss.md]
finding: docs/findings/2026-11-13-how-many-stories-we-miss.md
superseded_by:
---

# How many real stories are missing from the Septimus site?

**Self-contained.** A fresh session executes this with no other context.
Read [`FRAMEWORK.md`](../../FRAMEWORK.md) first, then this.

## The claim to test / the problem

Simon, 2026-11-13: *"the BIGGER issue is how many stories did we miss?!"* The site ships 1,784
definite stories across 37 tractates. "Proposed by the detector" (Eruvin 55/55 after Jeff's
2026-11-12 verdicts) is not "on the site": the definite-in-both-runs rule, the Mishnah filter,
biblical scope and Jeff's removals all sit between them. Nobody has split a site miss by where it
was lost, or put a number on misses across all 37 tractates.

## Method

No model calls. A new read-only script, `scripts/measure_site_misses.py`, which runs the recall
harness (`measure_recall_vs_expert_list.py`, exact matcher, `--standard current`) as a subprocess
and joins by span overlap:

1. every counted story on the five lists → the stage where it was lost, for the site and for the
   detector alone (either run);
2. a bootstrap extrapolation of site recall (Eruvin + Yevamot, the v14 tractates with lists) and
   the 2026-11-12 precision sample to the 34 unreviewed tractates; reviewed tractates counted directly;
3. the recoverable pool from `results/consensus/<t>/units.json` (spans proposed as a story but not
   shipped), with three candidate ship rules priced in buy (stories) and cost (precision).

Then rerun `measure_shas_accuracy.py`, add a dated Update to the 11-10 finding, and a dated line
under `jeff:miss-rate`.

## How you know it worked

Every list story is assigned to exactly one stage (the stage counts sum to the denominator); the
denominators equal the harness's `counts_for_recall`; the script refuses if a list story has no
located window.

## Guardrails

Proposals only: no change to the site, the filter, or its decisions file (Simon rejected judge
promotion and a both-judges gate on 2026-11-09). Never quote a list's raw length as a denominator.
Mark every figure measured / indicated / suspected.

## When done

Write the finding to `docs/findings/<date>-<slug>.md`, add an `## Outcome` section
below, and `git mv` this file to `work/done/`. **Never delete it.**

## Outcome

Done 2026-11-13. Finding: [`2026-11-13-how-many-stories-we-miss.md`](../../docs/findings/2026-11-13-how-many-stories-we-miss.md).

- **At least ~700 real stories (indicated, ~520–940) are missing from the site.** That is ~607 on the 34
  unreviewed tractates (bootstrap 420–842) plus 99 listed misses on the reviewed three. It is a floor, because
  the lists are not comprehensive and probably list the clearer stories.
- **The site filter, not the detector, is the loss.** On Eruvin + Yevamot (154 stories) the detector proposes
  149 (96.8%) and the site shows 107 (69.5%). 36 are lost at the definite-only filter, 7 to NOT_A_STORY, and 4
  never proposed or Mishnah-withheld (measured).
- **Recoverable pool:** 95 one-run-definite spans, 26 definite-in-one-run-only spans, and 1,049 LOW-in-both. Four
  rules are priced (0, A, B, C), and none is applied: the site is Simon's (L-045). Rule 0 ships the 60 golden-LOW
  stories on Jeff's own Ketubot/Kiddushin lists at no precision cost by his evidence.
- `measure_shas_accuracy.py` was re-run. Its blind precision lower bound now ignores list entries Jeff has ruled
  `not` (an overcount of up to 6 on the 11-10 Eruvin site). The 11-10 finding has a dated Update, and
  `jeff:miss-rate` has the numbers to ask it beside.
- Still open: whether a looser rule ships (Simon), and the miss rate itself (Jeff).
