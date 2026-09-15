# Swapping the model collapses Detection to 7.8% — and the run reports success

> **CORRECTED 2026-09-08 — this finding's conclusion does not hold.** Every run below
> was made with `GEMINI_THINKING_LEVEL=high` in `.env`, which alone truncates the model's
> JSON. With it unset, `gemini-3.8-flash` finds the most stories of the three models
> tested. See [`model-verdicts-were-config-not-model`](2026-09-08-model-verdicts-were-config-not-model.md).

> **SUPERSEDED 2026-09-09 — the runs behind this finding used a broken prompt.** A splice
> into the detection f-string sent `{cross_page}` and `{few_shot_section}` to the model as
> literal text, so every call lost its few-shot examples and cross-page context: 83.3% ->
> 50.7% on a fixed slice. No conclusion here survives.
> See [`broken-prompt-explains-everything`](2026-09-09-broken-prompt-explains-everything.md).

**2026-09-08.** Status: **measured** (one arm, one tractate). Artifact:
`results/v11/yevamot_model_probe/yevamot_3.7flash.json`, scored to
`results/recall/yevamot_3.7flash_matches.json`. Follows
[`model-default-returns-nothing`](2026-09-07-model-default-returns-nothing.md).

Yevamot, whole tractate, **the only change being the model name**:

| | pages examined | pages returning **nothing** | proposals | Detection recall, BLIND |
|---|---|---|---|---|
| `gemini-3-flash-preview` (shipped run) | 106 | **3** | 176 | **89.2%** |
| `gemini-3.7-flash` | 106 | **66** | 112 | **7.8%** |
| `gemini-3.8-flash` (the `.env` default) | — | every page probed | 0 | not run |

**62% of examined pages came back with no stories at all**, and the run reported
`DONE in 79 min · 104 stories`. Nothing failed. The artifact is well-formed, the
structural gate passes, Stage 4 does its work on what little arrives. Only a scored
recall measurement against a blind list shows it.

**The single-page probe that motivated this was wrong.** On Yevamot 121b, 3.7-flash
returned 4 proposals against the shipped run's 1, which read as the newer model being
better at exactly the clustering defect we were chasing. Over the tractate it is the
same silent-empty failure as 3.8, one notch less severe. **One page is not a
measurement**, and the direction of the error on that page was the flattering one.

## What this means beyond the model

The pipeline is currently **pinned, by accident rather than by decision, to one model**.
`.env` names a different one. A run started today with the committed default produces an
artifact that looks complete and is empty.

The guard this needs does not exist: `tests/test_wave5b_runner_outcomes.py` pins that a
failed *call* is never stamped as a judgment, and a page returning valid JSON with an
empty story list is not a failed call at that layer. **A per-run floor — "examined pages
that yielded nothing" against the rate the shipped runs show — would have caught all
three of these in the first minute.** That is the fix worth making; choosing a model is
not.

## Why the two-arm cluster test still has not run

Sequenced three arms on the preview model (treatment, control, same-code repeat). Two
process-level mistakes of mine cost the first attempt — a `pkill` that missed the parent
shell, so two runs competed for one quota — and after that the API throttled hard:

| | median gap between calls |
|---|---|
| 00:00–01:00 | **14s** |
| 02:10 onward, single process | **105s** |

At 105s a call, one arm is ~6 hours and the three-arm design is ~18. No 429s are logged —
the SDK absorbs them and only successful responses reach the log, which is its own small
blindness. **Stopped rather than left running overnight**: the remaining cost is quota,
and that is not a measurement decision.

The clause itself is written, gated `SERIES_RULE`, **default off**, and still unmeasured.
Nothing in this finding bears on whether it works.
