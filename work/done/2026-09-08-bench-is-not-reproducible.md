---
title: Two identical runs differ by 12.8 points — pin a model and measure the noise floor
capability: [detection, triage, boundaries, classification]
tractate: [yevamot]
blocked_by: []
awaiting: []
writes: [src/story_detector_v11.py, scripts/run_new_tractate.py, results/v11/noise_floor/, docs/capabilities/, .env.example]
finding: docs/findings/2026-09-09-broken-prompt-explains-everything.md
superseded_by: docs/findings/2026-09-09-broken-prompt-explains-everything.md
---

# The bench cannot currently tell a change from a re-run

**Self-contained.** Read [`series-rule-refuted`](../../docs/findings/2026-09-08-series-rule-refuted.md)
and [`model-swap-collapses-detection`](../../docs/findings/2026-09-08-model-swap-collapses-detection.md).
**Blocks every detector experiment.** **Cost: ~4 tractate arms.**

## The problem

Yevamot, 2026-09-08, same code path, same model name, same day:

| | recall | stories | span repairs |
|---|---|---|---|
| control A | 56.9% | 222 | 91 |
| control A2 | 44.1% | 216 | 90 |
| shipped artifact, 2026-09-03 | **89.2%** | 168 | **0** |

**12.8 points between two runs of the same code**, and neither reproduces the artifact the
board quotes. The prompt diff against 2026-09-03 is one blank line, verified against the
commit. `gemini-3-flash-preview` is a preview endpoint and Google updates those in place.

A floor that size is larger than every effect this project has ever chased: R-B1's
boundary gains, the triage rule's 1.4 points, the cluster clause's 29 stories.

## Method

1. **Four control arms**, one tractate, one day, same code — the floor is a distribution,
   not a difference between two runs. Report spread, not just mean.
2. **Try to reproduce 2026-09-03.** If a pinned non-preview model reproduces it, the
   diagnosis is drift and the fix is the pin. If nothing does, the artifact is
   unreproducible and every Yevamot cell on the board needs that caveat (Lesson 11).
3. **Pin a model in code, not in a dotfile.** `.env` carried
   `GEMINI_THINKING_LEVEL=high` for an unknown period; it made every call truncate. A
   value that changes results this much does not belong somewhere untracked.
4. **Add a per-run floor check** — examined pages yielding nothing, and span-repair count
   — asserted against the shipped rates. Both of this week's failures would have tripped
   it in the first minute; neither tripped anything.

## How you know it worked

- A stated noise floor, per capability, with its date and its model.
- Either a run that reproduces 89.2%, or that figure carrying an explicit
  not-reproducible caveat wherever it is quoted.
- A guard that fails a run whose empty-page or span-repair rate departs from the baseline.

## Guardrails

- Do not compare any two runs made on different days until this is done.
- `span_repairs` is the most sensitive instrument found so far — 0 / 90 / 237 separated
  three conditions that recall alone read as noise. Report it beside every score.

## When done

Finding to `docs/findings/<date>-noise-floor.md`, `## Outcome` here, then
`python3 scripts/board.py finish 2026-09-08-bench-is-not-reproducible`.

## Outcome

**Premise refuted, 2026-09-09.** The 12.8-point spread between two identical runs was
not the bench — it was a splice into the detection f-string that sent
`{few_shot_section}` to the model as literal text. With the prompt intact, three repeats
per arm give **identical story sets, spread 0.0**, and the pre-splice code reproduces the
shipped artifact to within one story. There is no noise floor to measure here; single
runs are comparable. Closed without doing the method above, because the method was
written to measure a problem that did not exist.
→ [`broken-prompt-explains-everything`](../../docs/findings/2026-09-09-broken-prompt-explains-everything.md)
