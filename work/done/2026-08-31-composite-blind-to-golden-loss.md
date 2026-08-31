---
title: Can the composite score detect silent loss from the golden?
capability: [classification]
tractate: [ketubot]
blocked_by: []
awaiting: []
finding: docs/findings/2026-08-31-composite-blind-to-golden-loss.md
superseded_by:
---

# Can the composite score detect silent loss from the golden?

**Self-contained.** A fresh session executes this with no other context.
Read [`FRAMEWORK.md`](../../FRAMEWORK.md) first, then this.

## The claim to test / the problem

A plan to reorganize this repo proposed using `scripts/evaluate_golden.py` as its safety
check: re-run it after each merge, and if the composite is unchanged, nothing was lost.

The claim to test is whether that check can see the failure it exists to catch — a merge
resolution that silently drops entries from `results/canonical/ketubot_canonical.json`.

## Method

Import the immutable harness READ-ONLY. Score the real corpus, then progressively remove
golden pages that carry accepted stories and re-score. Never pass a bare invocation: with
no `--output` the harness overwrites `docs/golden/v7/baseline_ketubot.json`.

## How you know it worked

A measured table of composite against accepted stories lost, and a statement of which
direction the metric moves.

## Guardrails

- `evaluate_golden.py` is immutable — import it, never edit it (CLAUDE.md).
- Assert `git diff --exit-code` on the harness and on the v7 baseline afterwards.

## When done

Write the finding, add `## Outcome`, `git mv` to `work/done/`.

## Outcome

**Measured 2026-08-31. The composite cannot detect golden loss, and can move the wrong
way.** Scored through the immutable harness at its default `--detected` paths
(`DEFAULT_DETECTED_V7` + `DEFAULT_DETECTED_V9`):

```
golden pages  accepted  composite      F1    TP   FN   delta
         222       164     0.9256  0.9075   157    7   (baseline)
         219       161     0.9258  0.9086   154    7   +0.0002   (3 lost)
         215       149     0.9247  0.9079   143    6   -0.0009   (15 lost)
         203       129     0.9264  0.9084   124    5   +0.0008   (35 lost)
         184        91     0.8993  0.9026    88    3   -0.0263   (73 lost)
```

Losing **35 expert-validated stories moved the score up**. Losing 15 moved it 0.0009 —
two orders of magnitude inside this project's own stated noise floor. `FN` *falls* as data
is lost, which is the mechanism in one column: a deleted golden entry does not become a
wrong answer, it stops being a question.

The reorganization plan was amended before execution to verify with counts and file
hashes instead. Four lessons landed with this item: L-031 (the general rule), and L-032 /
L-033 / L-034 from the same design review.

Harness and v7 baseline confirmed byte-identical afterwards.
