# L-037 — The endpoints bracket a trade; they do not locate it

**Date:** 2026-08-31
**Found in:** `triage-recall-price` → the rule sweep that followed it
→ [`2026-08-31-triage-single-narrative.md`](../docs/findings/2026-08-31-triage-single-narrative.md)

## The rule

**When you measure a filter by turning it off, you have measured two points. Before you
act on either, sweep the rules in between — the good deal is usually not at either end,
and the sweep is almost always free.**

## What happened

Stage 1 discards more than half of each tractate. To price it, Stage 2 was re-run on every
discarded page and scored against the blind expert lists. The result was clean:

```
current filter   ->  0 extra calls,   0 extra stories
no filter        ->  224 extra calls, 4 extra stories, 24 false proposals
```

A defensible trade, and the natural next move is to ask whoever owns the budget whether
24-for-4 is worth paying. That question was in fact asked and answered *yes*.

**It was the wrong question.** The intermediate rules had not been measured. Sweeping them
cost nothing — the Stage 2 output was already paid for, so each candidate only needed
re-asking which pages it would have kept:

```
N >= 1           ->  8 extra calls,   3 extra stories, 5 false proposals
```

Same idea, **28× cheaper**, and on Ketubot it captured *100% of the gain available from
reading the entire tractate* for 4 calls instead of 124.

The two endpoints were both real measurements and neither was wrong. They simply could not
show that almost the whole benefit sat at the first step inside the interval.

## Why the sweep is nearly always cheap

The expensive part of an ablation is **generating the counterfactual output**. Once you
have run the downstream stage on the excluded population, every intermediate rule is a
*re-partition of results you already hold* — no new calls, no new model time. The sweep
costs a loop.

This generalises past triage: any threshold, filter, or gate you can turn off can be swept
for free once the "off" run exists.

## How to apply

- **Ablate to establish that a trade exists. Sweep to decide what to do about it.** Never
  ship, and never escalate to a human for a budget decision, on the endpoints alone.
- **Report the whole curve**, not the point you chose. The rejected rows are what make the
  chosen one defensible, and they are what stop the next person re-running the sweep.
- **Distinguish a boundary from a tuned threshold, and say which you picked.** `N >= 1`
  is "any evidence at all" — a boundary; `V >= 4` came out of the sweep and fit one story
  in one tractate. The first was shipped, the second rejected and pinned by a test with the
  reason attached. Reaching for the best row in the sweep is how you overfit (Lesson 18).
- **Sanity-check the winner against something that predates the sweep.** `N >= 1` recovers
  Ketubot 51a, a false skip found by hand on 2026-02-13 and never fixed. A rule fitted to
  today's data has no business also fixing a six-month-old documented case; that
  coincidence is evidence the rule is real.

## The general form

An ablation answers *"does this component matter?"*. It does not answer *"what should this
component be?"* — and it is tempting to treat the second as settled because the first was
expensive. The interval between "as-is" and "off" is where the actual design decision
lives, and it is the cheapest part of the experiment to explore.

Related: Lesson 18 (do not generalise from the sample the expert happened to send),
Lesson 22 (a one-run difference is not a result without a noise floor).
