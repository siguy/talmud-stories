# The composite score cannot see loss from the golden — 2026-08-31

**MEASURED.** Scored through `scripts/evaluate_golden.py`, imported read-only, at its
default `--detected` paths (`DEFAULT_DETECTED_V7` + `DEFAULT_DETECTED_V9`) against
`results/canonical/ketubot_canonical.json`.

## Why this was asked

A plan to reorganize this repo proposed a safety check: re-run the harness after each
merge, and if the composite is unchanged, the migration lost nothing. The question is
whether that check can see the failure it exists to catch — a merge that silently drops
golden entries.

## The measurement

Golden pages carrying accepted stories were progressively removed and the corpus
re-scored:

```
golden pages  accepted  composite      F1    TP   FN   delta
         222       164     0.9256  0.9075   157    7   (baseline)
         219       161     0.9258  0.9086   154    7   +0.0002   (3 accepted lost)
         215       149     0.9247  0.9079   143    6   -0.0009   (15 accepted lost)
         203       129     0.9264  0.9084   124    5   +0.0008   (35 accepted lost)
         184        91     0.8993  0.9026    88    3   -0.0263   (73 accepted lost)
```

**Losing 35 expert-validated stories — 21% of the accepted golden — moved the composite
UP by 0.0008.** Losing 15 moved it 0.0009, two orders of magnitude inside the ±7pt noise
floor this project measured for itself (Lesson 22). You have to destroy 45% of the corpus
before the number moves further than run-to-run variance.

## Why it behaves this way

Two properties, both in the harness as written:

```
composite = 0.4 * classification_f1 + 0.4 * mean_iou + 0.2 * merge_f1
```

Every term is a **ratio**; none is a count. And `compute_classification_scores` and
`compute_boundary_iou` both open with `for page_ref in golden` — a page absent from the
golden is never visited, so it cannot contribute an error.

Together: removing a golden entry removes it from the numerator *and* the denominator. It
does not become a false negative; it stops being scored at all. That is visible in the
`FN` column, which **falls from 7 to 3 as 73 stories vanish**.

> A deleted answer does not produce a wrong answer. It produces one fewer question.

## Scope — this is not only about the migration

The plan was amended to verify with counts and `git hash-object` instead, so that specific
risk is closed. But the property is a property of the metric, not of the migration:
**no composite comparison in this project's history could have detected golden loss**, and
none can in future. Any use of the composite to argue "nothing was lost" is unsupported.

The composite remains valid for what it was built for — comparing two detector runs
against a *fixed* golden. The failure is only when the golden itself is the thing that
might have changed.

## What to do instead

Assert on counts and hashes, which are the things that move when data is lost:

- `ketubot_canonical.json` = 222 pages / 187 stories / 164 accepted
- `kiddushin_canonical.json` = 162 / 96 / 85
- `git hash-object` unchanged on the harness, both canonicals,
  `tests/expert_boundary_targets_2005.json`, and `jeff comms/*.doc`

`tests/test_bookkeeping.py::test_golden_still_measures_what_it_should` already pins the
first of these. This finding is the reason that test is worth more than it looks.

**An unchanged composite beside a changed count is the signature of silent loss.**

## Related

Same family as [Lesson 27](../../lessons/L-027-a-step-that-moves-records-out-of-the-measured-path.md)
(a step that moves records out of the measured path) and
[Lesson 23](../../lessons/L-023-an-exam-built-only-from-corrections-cannot-see-a.md)
(an exam built only from corrections), but a distinct mechanism: those are about data
leaving the measured population, this is about the metric's own arithmetic. Generalised as
[Lesson 31](../../lessons/L-031-verify-a-guard-by-simulating-the-failure-it-guards.md).
