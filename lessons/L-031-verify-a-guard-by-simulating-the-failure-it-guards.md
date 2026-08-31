# Lesson 31 — Verify a guard by simulating the failure it guards against

**2026-08-31**

A plan to reorganize this repo proposed one safety check: re-run
`scripts/evaluate_golden.py` after each merge, and if the composite is unchanged, nothing
was lost. It sounded like the most conservative check available.

Measured instead of assumed — golden pages carrying accepted stories removed, corpus
re-scored through the immutable harness:

```
golden pages  accepted  composite    TP   FN   delta
         222       164     0.9256   157    7   (baseline)
         215       149     0.9247   143    6   -0.0009   (15 accepted lost)
         203       129     0.9264   124    5   +0.0008   (35 accepted lost)
         184        91     0.8993    88    3   -0.0263   (73 accepted lost)
```

**Losing 35 expert-validated stories moved the score up.** Losing 15 moved it by 0.0009 —
two orders of magnitude inside our own measured noise floor (Lesson 22).

The mechanism is in the `FN` column, which *falls* as data disappears. Composite is
`0.4·F1 + 0.4·IoU + 0.2·merge_F1` — three ratios, no count — and the scorers open with
`for page_ref in golden`. Removing a golden entry removes it from the numerator **and**
the denominator. A deleted answer does not produce a wrong answer; it produces one fewer
question.

So the check was not weak. It was **pointing the wrong way**: the more damage the
migration did, the better it could read.

**Rule:** before trusting a metric as the guard on an operation, simulate that operation's
failure and check which way the metric moves. If it can stay flat or improve, it is not a
guard — whatever else it is good for.

**Why:** we were one approval away from executing a migration on irreplaceable expert data
behind a check that was blind to its worst outcome. A check that cannot fail is worse than
no check, because no check leaves you careful and a false one makes you confident.

**How to apply:**
(a) **Guard with counts and hashes, not ratios.** A ratio cannot detect a change in its
own denominator. `tests/test_bookkeeping.py::test_golden_still_measures_what_it_should`
pins 222 pages / 187 stories / 164 accepted for exactly this reason.
(b) **An unchanged score beside a changed count is the signature of silent loss** — check
both, and treat agreement between them as the actual pass condition.
(c) **The simulation is cheap.** This one was twenty lines and five minutes, against a
migration that would have taken a day and could not be undone.
(d) Related to Lesson 27 and Lesson 23, but distinct: those are about records leaving the
measured population. This is about the arithmetic of the metric itself, and it applies to
every composite comparison this project has ever made where the golden was in question.
Full measurement: `docs/findings/2026-08-31-composite-blind-to-golden-loss.md`.
