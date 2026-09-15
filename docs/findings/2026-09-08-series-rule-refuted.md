# The parallel-series clause is refuted — and the bench it was measured on is broken

> **SUPERSEDED 2026-09-09 — the runs behind this finding used a broken prompt.** A splice
> into the detection f-string sent `{cross_page}` and `{few_shot_section}` to the model as
> literal text, so every call lost its few-shot examples and cross-page context: 83.3% ->
> 50.7% on a fixed slice. No conclusion here survives.
> See [`broken-prompt-explains-everything`](2026-09-09-broken-prompt-explains-everything.md).

**2026-09-08.** Status: **indicated, not measured** — and the reason for that word is the
finding's second half. Artifacts: `results/v11/series_rule_experiment/`,
scored to `results/recall/series_rule/`. Item:
[`formulaic-cluster-splitting`](../../work/2026-09-07-formulaic-cluster-splitting.md).

## The experiment

Three whole-tractate Yevamot arms, `gemini-3-flash-preview`, no thinking level, run
back-to-back in one hour. The clause is gated `SERIES_RULE`, so the control arms are the
**same code path** with the clause string empty — not a different revision.

| arm | recall vs Jeff's 102 | stories | span repairs |
|---|---|---|---|
| **A** control | **56.9%** | 222 | 91 |
| **A2** control, same code, same day | **44.1%** | 216 | 90 |
| **B** series clause | **24.5%** | 155 | **237** |

**The clause makes it worse**, by 19.6 points against the nearer control. And it has a
mechanism that is not recall noise: span repairs nearly triple, **237 against ~90**, all
of the same kind — *"span lies outside the page"*. Told to split a run into its members,
the model returns segment indices the page does not have. It does not find more stories;
it invents more places.

**Read `indicated`, not `measured`.** The two controls differ by **12.8 points**. B sits
outside that band and its repair count is a separate signal pointing the same way, which
is why the direction is worth acting on. The size is not.

**The clause stays `SERIES_RULE` default off**, where it already was. Nothing shipped.

## The bench is broken, and that is the larger result

**Neither control reproduces the shipped Yevamot run.**

| | recall | stories | span repairs |
|---|---|---|---|
| shipped artifact, 2026-09-03 | **89.2%** | 168 | **0** |
| control today | 56.9% / 44.1% | 222 / 216 | 91 / 90 |

Same model name, same code, same prompt — the diff between today's control prompt and the
2026-09-03 one is **one blank line**, verified against the commit. Five days apart.

Three things follow, and the third is the one that matters:

1. **A 12.8-point spread between two identical runs.** Every detector result this project
   has published on Yevamot rests on a single run. This is the first time two were done
   the same day.
2. **`gemini-3-flash-preview` is a preview endpoint** — Google updates those in place.
   That is the most likely explanation, and it means the shipped artifact is **not
   reproducible**: Lesson 11, arriving through the model rather than through a lost
   command line.
3. **No detector experiment is trustworthy on this bench right now.** A 12.8-point floor
   swallows every effect this project has ever chased. R-B1's boundary gains, the
   triage rule's 1.4 points, the cluster clause's 29 stories — all smaller than the noise
   between two runs of the same code.

## The night's model results, for the record

| model | pages returning nothing | recall |
|---|---|---|
| `gemini-3-flash-preview`, `thinking_level` unset | 4 of 106 | 44–57% |
| `gemini-3-flash-preview`, `thinking_level=low` | few | 35.3%, **135 dropped spans** |
| `gemini-3-flash-preview`, `thinking_level=high` | most | truncated, unusable |
| `gemini-3.7-flash` | **66 of 106** | **7.8%** |
| `gemini-3.8-flash` | every page probed | 0 stories, never completed a run |

`.env` carried `GEMINI_THINKING_LEVEL=high`, which alone made every call truncate — 120s
per call returning a JSON object cut off mid-string. It is now unset, matching the shipped
run's `thinking_level: null`. **A truncated response is now reported and recorded**
(`TRUNCATED RESPONSE`, `self.truncated_responses`) instead of falling through the parser
into "no stories" — Lesson 21 at the layer where it was still possible.

## What to do next, in order

1. **Establish the noise floor properly.** Two arms is a spread, not a floor. Three or
   four controls, one tractate, one day, before any further detector work.
2. **Pin a stable model.** A preview endpoint cannot carry a baseline. This is a decision,
   and it is now blocking.
3. **Then, and only then**, re-ask whether the cluster defect is reachable by prompt.
   The defect is real and measured
   ([`miss-anatomy`](2026-09-07-miss-anatomy.md)); only this attempt at it is refuted.
