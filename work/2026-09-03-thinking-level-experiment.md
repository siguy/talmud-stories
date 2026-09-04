---
title: Does thinking=high actually help? Screen on the known misses before paying for arms
capability: [detection, triage]
tractate: [kiddushin]
blocked_by: []
awaiting: []
writes: [scripts/run_thinking_experiment.py, results/thinking/, docs/findings/]
finding:
superseded_by:
---

# Does `thinking=high` actually help?

**Self-contained.** Read [`FRAMEWORK.md`](../FRAMEWORK.md) §2–3, then
[`src/model_config.py`](../src/model_config.py), then this.

## Why this exists

The 2026-09-03 default change set `thinking_level=high` **on no evidence that it helps**.
It was chosen because unset silently meant *off*, and off was clearly not a decision anyone
had made — but "not-a-decision" is not the same as "high is right". The cost is now known
and is not small: one detection call spent **7,867 thinking tokens against 321 tokens of
output**, and pages took **14–70s** against a few seconds before.

**This item is the evidence the default is currently missing.** It runs before any full
re-run, because the re-run should use whichever setting wins.

## Stage 1 — the enriched screen (~50 calls)

Run **only the pages holding the 12 blind-list stories we never propose**, at `low` and at
`high`, **twice each**.

| tractate | miss |
|---|---|
| Ketubot | 20a, 53a, 67b, 72b, 77a, 82b |
| Kiddushin | 10b, 14a, 21b, 26a, 69a, 81b |

Thinking can only help by changing a judgement call, so the misses are the enriched sample.
A whole tractate holds 12 such events in 350 stories; this holds 12 in 12.

**Decision rule, stated before the run:** if `high` recovers **zero** misses across both
repeats, stop and write the finding. That is a cheap, strong negative on the axis that
matters — finding stories — and Stage 2 is not worth its hours. If it recovers two or more,
proceed.

**Note what this stage cannot show.** It is blind to precision: every page in it contains a
story, so nothing here says whether `high` proposes *less junk*. A null result closes the
recall question only, and Stage 2 may still be worth running for precision alone. Say which
question is being closed.

## Stage 2 — one tractate, two arms, with the repeat

**Kiddushin** — smallest corpus, and its recall deficit is already characterised.

| | |
|---|---|
| arms | `thinking=low`, `thinking=high` |
| runs per arm | **2** (Lesson 22) |
| model | `gemini-3.8-flash`, pinned in all four |
| triage | **cached labels, held fixed** |

**The triage constraint is the one that makes this a valid experiment.** If Stage 1 is
re-triaged per arm, the page set differs between arms and detection thinking is no longer
the only variable — you would be measuring two changes and could attribute neither. Triage
thinking is a **separate** question and gets its own item if this one says thinking matters.

**The bar, set before the run:** if `|high − low|` is smaller than the **within-arm** spread
between the two repeats, the answer is **"no detectable effect"** — not "slightly better".
This is the most likely way the result gets misread, so the finding must print the
within-arm spread *first*, above the between-arm difference.

## Report three numbers, never pooled

| metric | provenance | answers |
|---|---|---|
| recall vs Jeff's 2005 list | **BLIND** | does it find more stories |
| classification precision vs golden | CIRCULAR | does it propose less junk |
| boundary hit / near | BLIND | does it read the extent better |

Pooling blind and circular rulers is how this project once produced a Kiddushin figure
wrong by 18 points and in the wrong order between tractates (Lesson 24).

**Stated prediction, before the run** — record it so the result cannot be rationalised
afterwards: *the effect, if any, will be on precision rather than recall.* Reasoning:
thinking plausibly helps a model **reject** a legal passage that looks narrative more than
it helps it **notice** a story it did not surface. If that is what comes back, `high` is
worth keeping for detection and wasteful for triage, and the two should be set independently
rather than sharing one default — which is what `src/model_config.py` currently does.

## Guardrails

- **Both arms run the same day** (Lesson 11). Nothing on the current scoreboard is a valid
  baseline: those numbers are `gemini-3-flash-preview` with thinking off, so comparing
  against them confounds the model change with this one.
- No golden is rebuilt. No prompt is changed. Thinking level is the only variable.
- Report calls, wall-clock and thinking-token counts per arm. A tie on quality is a **win
  for `low`**, and that only reads as a win if the cost side is on the page.

## How you know it worked

A sentence of the form *"at fixed model and fixed triage, thinking=high moves
<metric> by X, against a within-arm spread of Y"* — for all three metrics, both stages.
A null is a complete outcome and closes the item.

## When done

Finding to `docs/findings/<date>-thinking-level-experiment.md`, `## Outcome` here, then
`python3 scripts/board.py finish thinking-level-experiment`.
