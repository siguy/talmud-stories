# One splice into an f-string produced two nights of false findings

**2026-09-09.** Status: **root cause found, measured, fixed, guarded.** **Supersedes**
[`series-rule-refuted`](2026-09-08-series-rule-refuted.md),
[`model-swap-collapses-detection`](2026-09-08-model-swap-collapses-detection.md) and
[`model-default-returns-nothing`](2026-09-07-model-default-returns-nothing.md). All three
are kept; none of their conclusions survive.

## The bug

The clause added on 2026-09-07 was spliced into the middle of the detection prompt:

```python
prompt = f"""...
""" + _SERIES_RULE + """      # <- everything after this point is a PLAIN string
...
{cross_page}
{few_shot_section}
"""
```

The prompt is one f-string. Concatenating in the middle ends it, and **the tail became a
plain string**, so `{cross_page}` and `{few_shot_section}` were sent to the model as
literal text. Every call lost its **few-shot examples** and its **cross-page context**.

Nothing raised. The prompt was still a prompt; the model still answered; the artifact was
still well-formed and passed the structural gate.

## What it cost, measured on a fixed 20-page Yevamot slice (36 expert stories)

| | recall | span repairs | apparent spread over repeats |
|---|---|---|---|
| pre-splice detector (`5f09446`) | **83.3%** | **0** | **0.0** (2 runs) |
| with the splice | **50.7%** | 22 | 11.1 (4 runs) |

**32.6 points**, and it manufactured the variance that was then reported as a finding.

## Every conclusion it produced was wrong

**"The bench cannot tell a change from a re-run."** The noise floor was reported as
**12.8 points**. With the prompt intact, three repeats of each arm give **identical story
sets** — spread **0.0**, twice over. At temperature 0.1 this detector is effectively
deterministic, and a single run *is* comparable to another single run. The floor was the
bug.

**"The preview endpoint drifted; the shipped artifact is not reproducible."** Withdrawn.
The pre-splice code reproduces the artifact to within one story (83.3% against the
artifact's 86.1% on the same slice, same scorer).

**"gemini-3.7-flash collapses to 7.8%; 3.8-flash returns nothing."** Void — those runs
carried **both** `GEMINI_THINKING_LEVEL=high` **and** the broken prompt. No model
comparison from 2026-09-07/08 means anything. (The thinking-level defect was real and is
separately fixed; `.env` no longer sets one.)

**"The series clause is refuted."** The opposite, below.

## The series clause, measured on an intact prompt

Three repeats per arm, same slice, `gemini-3-flash-preview`, thinking off. The gate is now
guaranteed byte-identical when off — a test asserts it.

| arm | recall | proposals | span repairs | spread |
|---|---|---|---|---|
| control | 83.3% (30/36) | 38.0 | 0 | **0.0** |
| **series clause** | **86.1% (31/36)** | 42.3 | 0 | **0.0** |

**+1 story, none lost, reproducible in 3 of 3 runs.** It also lands exactly on the shipped
artifact's slice score.

**But it does not do what it was written to do.** The story it gains is Yevamot 78b —
a question put to R. Eliezer, not a formulaic twin. Of the **four** ADJACENT-class cluster
misses on this slice — both Yevamot 121b criers, 63a, 34b — the clause recovers
**none**. The gain is consistent with simply proposing more (+4.3 per 20 pages), not with
splitting runs of parallel incidents.

So: **a small real gain, and the hypothesis still unproven.** Not shipped on one slice of
one tractate; that is what the item now asks for.

## Guarded

`tests/test_prompt_is_fully_substituted.py`:

- no `{placeholder}` may survive into a built prompt, with the gate on **or** off;
- the gate must change the prompt by exactly the clause and nothing else, whitespace
  included.

The second test failed while being written — the gate was also eating a blank line.

## The lesson

**A prompt that loses its examples is still a valid prompt.** Every layer downstream was
healthy: valid JSON, well-formed artifact, passing structural gate, plausible story counts.
The only instrument that saw it was a scored measurement against ground truth, and the
first three explanations offered for that score — model drift, thinking levels, run-to-run
variance — were all external, all plausible, and all wrong.

**The cheap check that would have ended it on the first night: diff the rendered prompt
against the last known-good one.** It cost one command and was run on the third night.
