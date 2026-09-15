# `gemini-3.8-flash` returns no stories, and the failure is silent

> **CORRECTED 2026-09-08 — this finding's conclusion does not hold.** Every run below
> was made with `GEMINI_THINKING_LEVEL=high` in `.env`, which alone truncates the model's
> JSON. With it unset, `gemini-3.8-flash` finds the most stories of the three models
> tested. See [`model-verdicts-were-config-not-model`](2026-09-08-model-verdicts-were-config-not-model.md).

> **SUPERSEDED 2026-09-09 — the runs behind this finding used a broken prompt.** A splice
> into the detection f-string sent `{cross_page}` and `{few_shot_section}` to the model as
> literal text, so every call lost its few-shot examples and cross-page context: 83.3% ->
> 50.7% on a fixed slice. No conclusion here survives.
> See [`broken-prompt-explains-everything`](2026-09-09-broken-prompt-explains-everything.md).

**2026-09-07.** Status: **measured, unresolved.** Found while trying to run the
two-arm test for [`formulaic-cluster-splitting`](../../work/2026-09-07-formulaic-cluster-splitting.md).

`.env` sets `GEMINI_MODEL=gemini-3.8-flash`, `GEMINI_THINKING_LEVEL=high`. One page,
Yevamot 121b, same code, same prompt, `SERIES_RULE=0`:

| model | stories proposed on Yevamot 121b |
|---|---|
| `gemini-3.8-flash` | **0**, three runs |
| `gemini-3-flash-preview` (produced the shipped Yevamot run) | 1 |
| `gemini-3.7-flash` | **4** |

**Two distinct defects.**

**1. Truncation, fixed.** At `thinking_level=HIGH` the 3.x branch capped
`max_output_tokens` at 8192; thinking consumed it and the JSON came back cut off
mid-object — the log shows a parse error and the page scores *"0 candidates, 0 stories"*.
This is the **same failure as 2026-08-29**, when the cap was raised 512 → 8192 for
`gemini-3.7-flash`; one model later the same budget is short again. Raised to 32768, the
floor the Pro branch already uses, so it is not re-tuned per model. `gemini-3-flash-preview`
still truncates on its **first** attempt and succeeds on the retry, so the shipped runs
have been living on that retry.

**2. Empty responses, unresolved.** With truncation fixed, `gemini-3.8-flash` returns
valid JSON containing **no stories at all** — in 4 seconds, which is too fast for
`thinking_level=HIGH`. Not diagnosed. One earlier truncated response answered about
**Sanhedrin 25b**, a page not in the prompt, which suggests the model is responding to
something other than the target page.

## Why this matters more than the model choice

**A page that returns nothing is indistinguishable from a page with no stories.** The run
completes, the summary prints `0 stories`, the artifact is well-formed, and the only trace
is a line in a log nobody reads. That is [Lesson 21](../../lessons/) — a failed call must
never be stamped as a judgment — reaching Stage 2 through the model layer rather than the
runner, which is where the existing guard
(`tests/test_wave5b_runner_outcomes.py`) does not look.

**Nothing here was scored**, so no published number is affected. But the default in `.env`
is a model that finds nothing, and any run started today inherits it.

## What is not established

- **Whether 3.7-flash's 4 proposals are better.** It proposes segments 1, 2, 13, 17 where
  the shipped preview run has 2, 5-6, 15-16, 17. Neither includes Yevamot 121b **segment
  14**, where both of Jeff's entries sit. More proposals is not the same as the right ones,
  and one page is not a measurement.
- **Whether the cluster clause helps.** Its two-arm test never ran. With the clause on,
  3.7-flash returned 0 stories on this page — one page, one call, and not distinguishable
  from the variance above.

## Next

Pin the experiment to a **single** model so the cluster clause is the only variable, and
run it over a whole tractate rather than named dapim. Model choice is a separate question
and wants its own scored comparison, not a default in a dotfile.
