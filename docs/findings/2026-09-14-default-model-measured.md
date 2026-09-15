# The default model, measured — and it was the one that loses two-thirds of the stories

**2026-09-14.** Status: **measured.** Reproduce:
`python3 scripts/score_noise_floor_slice.py results/thinking` (the scorer ships in #48;
the artifacts are here). Closes
[`thinking-level-experiment`](../../work/done/2026-09-03-thinking-level-experiment.md).

PR #42 (2026-09-07) unified four drifting model literals into `src/model_config.py` —
the right change — and, in the same commit, set the default to `gemini-3.8-flash` at
`thinking_level=high`. Its own comment called `high` *"a choice made without evidence"*
and named the experiment that would justify it as unrun. This is that experiment.

## The measurement

Twenty Yevamot dapim carrying 36 of Jeff's blind stories — chosen by daf, not by outcome.
The detection prompt verified byte-identical to the 2026-09-03 shipped run. No rate
limiting. One run per config: at this temperature the runs are deterministic (three
repeats, identical story sets, measured 2026-09-09).

| config | recall | pages returning nothing | truncated responses |
|---|---|---|---|
| **`gemini-3-flash-preview`, thinking off** | **83.3%** (30/36) | 1 of 20 | 0 |
| `gemini-3.8-flash`, thinking off | 75.0% (27/36) | 0 | 4 (recovered on retry) |
| `gemini-3.8-flash`, thinking high — **the default** | **27.8%** (10/36) | **9 of 20** | 14 |

**Two different failures, and only one is about the model.**

**`high` fails on budget.** Thinking tokens and output tokens draw on one
`max_output_tokens`; the detection output is a large JSON object per story, so thinking
starves it and the JSON is cut mid-string. `finish_reason` says `MAX_TOKENS`, the parser
fails, the retry fails the same way, and the page records *"0 candidates, 0 stories"*.
**The run completes and reports success.** Raising the cap to 32768 — which #42 did —
does not prevent it; the model thinks longer.

**3.8 with thinking off is simply stricter.** The three stories it drops were all
`LOW_CONFIDENCE` under preview: a legal question put to a rabbi, Rav addressing sheaves,
a teacher's one-line reminiscence. Jeff lists them. A higher bar costs recall against his
list; it may buy precision, which is unmeasured.

**Every number the board quotes was produced by the first row.** The 2026-09-03 Yevamot
run's `run_meta` records `thinking_level: null`, as does every shipped run before it.

## What changed

`DEFAULT_MODEL = "gemini-3-flash-preview"`, `DEFAULT_THINKING_LEVEL = None`, and
`default_thinking_level()` now treats a **set-but-empty** `GEMINI_THINKING_LEVEL` as off
rather than as "use the default" — a dotfile with `GEMINI_THINKING_LEVEL=` was silently
becoming `high`. `GEMINI_MODEL` still wins when set. Tests pin all of it.

## What this does not settle

- **Whether thinking helps at a budget it cannot exhaust.** Untested above 32768. The
  task is extraction plus exact index reporting, and one earlier run at `low` produced
  135 out-of-range spans — on a broken prompt, so it is not evidence, only a reason to
  expect little.
- **Whether 3.8's strictness is worth its precision.** If review throughput ever wants a
  stricter first pass, that is the model to measure for it.
- **Anything about 3.7.** Not run clean.
