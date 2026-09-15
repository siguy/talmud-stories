# Correction: the model verdicts measured a bad config, not the models

**2026-09-08.** Status: **corrects two findings from the same 24 hours** —
[`model-default-returns-nothing`](2026-09-07-model-default-returns-nothing.md) and
[`model-swap-collapses-detection`](2026-09-08-model-swap-collapses-detection.md). Both are
kept as written; this supersedes their conclusions.

## What was claimed, and why it was wrong

Claimed: `gemini-3.8-flash` returns no stories at all, and `gemini-3.7-flash` collapses
Detection to 7.8%. **Every one of those runs was made with `GEMINI_THINKING_LEVEL=high`
set in `.env`.** That single setting makes the model spend its output budget thinking and
return JSON cut off mid-object — the failure documented in the first of those findings and
then, inexcusably, used as the baseline for the second.

The confound was named in the first finding and carried into the second anyway.

Re-probed with the thinking level unset, six Yevamot dapim, everything else identical:

| model | pages returning nothing | stories | truncations | time |
|---|---|---|---|---|
| **gemini-3.8-flash** | **0 of 6** | **15** | 4 (retried) | 77s |
| gemini-3.7-flash | 2 of 6 | 9 | 2 | 56s |
| gemini-3-flash-preview | 1 of 6 | 9 | 0 | 51s |

**3.8-flash is not broken. On this probe it is the strongest of the three.** The single
real defect was the config, and it is fixed: `.env` no longer sets a thinking level,
matching the `thinking_level: null` in every shipped run's `run_meta`.

**Six pages is a probe, not a measurement** — the same mistake in the other direction is
what produced the 3.7 verdict, so no model ranking is claimed here. What is established
is only that the earlier verdicts do not survive their confound.

## What was over-claimed about drift

Also claimed: the preview endpoint has drifted and the 2026-09-03 Yevamot artifact is
"not reproducible". **Not supported.** The evidence is two same-day runs at 56.9% and
44.1% against the artifact's 89.2%. Two samples cannot separate *the model changed* from
*the artifact was a favourable draw from a very wide distribution*, and the 12.8 points
between the two controls says the distribution is wide.

The honest statement: **run-to-run variance is large, both of today's runs sit well below
the artifact, and nothing here distinguishes the two explanations.** That is what the
successor item exists to settle
([`bench-is-not-reproducible`](../../work/done/2026-09-08-bench-is-not-reproducible.md)).

## What is unaffected

Both arms of the series-rule experiment ran with the thinking level unset, back to back,
same day. Nothing in this correction touches
[`series-rule-refuted`](2026-09-08-series-rule-refuted.md): control 56.9% / 44.1%,
treatment 24.5%, span repairs 91 / 90 / 237. The clause is still refuted and still off.

The truncation guard added yesterday also stands, and earned itself in this probe — 3.8
truncated 4 times in 6 pages and the retries carried it. Before the guard those were
invisible.

## The lesson, which is this project's oldest one

A configuration value living in an untracked dotfile changed every result on the bench,
and was then used as the control for the next experiment. `run_meta` records
`thinking_level` and would have shown it in one line — **it was read only after two
findings had been written.** Read the run's own metadata before writing anything down
about why a run differs.
