---
title: Split runs of formulaically parallel stories — we return one representative
capability: [detection]
tractate: [ketubot, kiddushin, gittin, yevamot]
blocked_by: []
awaiting: []
writes: [src/story_detector_v11.py, src/prompts/, results/v11/series_rule_experiment/, results/recall/series_rule/, tests/test_cluster_splitting.py]
finding: docs/findings/2026-09-09-broken-prompt-explains-everything.md
superseded_by:
---

# Split runs of formulaically parallel stories

**Self-contained.** Read [`FRAMEWORK.md`](../FRAMEWORK.md), then
[`2026-09-07-miss-anatomy`](../docs/findings/2026-09-07-miss-anatomy.md), then
[`docs/capabilities/2_detection.md`](../docs/capabilities/2_detection.md).
**Capability: 2 Detection.** **Depends on Jeff: no.** **Cost: prompt work + one measured
run per tractate.**

## The claim to test

Given a run of formulaically parallel anecdotes on one daf, the detector proposes **one
representative and stops**. Measured 2026-09-07: 18 of 38 Detection misses have a proposal
**one segment away**, and in 18 of 18 that proposal is a *different* story — nearly always
the missed story's twin. Kiddushin 40a: we return Rav Kahana and the noblewoman, Jeff's
entry is R. Zadok and the noblewoman, immediately before it. Yevamot 121b: we return
*"Ḥasa has drowned"*, his two entries are *"Ḥiwai has drowned"* and the horseman of
Pumbedita, the same crier formula three times. A further 11 misses sit 2–6 segments away,
mostly on dapim where the run produced exactly one proposal against two to six of his
stories.

**Ceiling if fully recovered: 29 stories, ~6 points of Detection recall across four
tractates.** Nobody has yet recovered one, which is what this item is for.

## Method

1. **Fix the population first.** `results/recall/miss_anatomy.json` names all 29 with
   their nearest proposal. Read them. Any case where the neighbour is *not* a sibling is
   a different bug and leaves this item — say so in the Outcome rather than absorbing it.
2. **Instrument before changing anything.** Count, per daf, proposals produced against
   expert stories present. That table is in the finding and is the thing that must move.
3. **Try the cheapest mechanism first, and only one at a time.** Candidates, in order of
   how little they assume:
   a. an explicit instruction that a series of parallel incidents is **N stories, not
      one**, with a worked Hebrew example of a `ההוא דהוה קאמר ואזיל` run;
   b. a second-pass sweep restricted to segments adjacent to an accepted proposal,
      asking only *"is this a further, separate incident?"*;
   c. nothing structural until (a) and (b) are measured — a splitter that operates on
      formula matching is a lexical rule and must be evidence, never a filter
      (Lesson 15).
4. **Score on the blind recall harness and the neutral boundary rulers, both directions**
   (`--by-direction`). Splitting a cluster can only be a gain if precision and boundaries
   hold; a rise in proposals with a fall on the ruler is over-splitting, and is the
   failure mode to look for.
5. **Same-code repeat before attributing anything** (Lesson 22). The noise floor on these
   runs is ~7 points on boundary metrics and is not optional here — the effect being
   chased is ~6.

## How you know it worked

- Named cases recovered by ref: Kiddushin 40a R. Zadok, Yevamot 121b **both** criers,
  Yevamot 63a R. Elazar, Ketubot 67b Hillel, Ketubot 61a both, Ketubot 112a the Sadducee.
- Blind Detection recall (given the page survived triage) rises from
  **Ketubot 90.3 / Kiddushin 88.4 / Gittin 97.3 / Yevamot 89.2**, all four re-measured
  through `--matcher exact` and no other way.
- Mean proposals per daf at 3+ expert stories moves toward the expert count **without**
  the boundary rulers falling.
- A same-code repeat is reported beside the result.

## Guardrails

- **Never a filter on an opening formula.** Parallel markers are evidence (Lesson 15);
  a rule that *requires* one will find the twins and lose everything else.
- **Watch precision on the residue.** More proposals per daf is the mechanism *and* the
  risk: every extra proposal costs the reviewer, and review throughput is the project's
  bottleneck. Report the change in proposals-not-on-his-list beside the recall change.
- Report blind and corrections rulers apart (Lesson 24).
- A failed call must never be stamped as a judgment (Lesson 21).
- Re-measure with the exact-anchor matcher only. The 4-gram window **cannot see this
  defect at all** — it credited every member of a cluster from one proposal, which is why
  the bug survived to 2026-09-07.

## When done

Write the finding to `docs/findings/<date>-cluster-splitting.md`, add `## Outcome`
here — including why, if reverted — and `python3 scripts/board.py finish
2026-09-07-formulaic-cluster-splitting`.


## Where this stands, 2026-09-09 — reopened

**The 2026-09-08 "refuted" result is void**: it was measured through a prompt that had
lost its few-shot examples
([`broken-prompt`](../docs/findings/2026-09-09-broken-prompt-explains-everything.md)).

Re-measured on an intact prompt, 20-page Yevamot slice, 3 repeats per arm, spread **0.0**:

| arm | recall | proposals |
|---|---|---|
| control | 83.3% (30/36) | 38.0 |
| **series clause** | **86.1% (31/36)** | 42.3 |

**+1 story, none lost, reproducible 3/3 — and it recovers none of the four cluster cases
on the slice.** The story it gains is Yevamot 78b, not a formulaic twin. The gain looks
like "proposes slightly more", not like the mechanism the clause was written for.

**Still `SERIES_RULE` default off.** What is left to decide it:

1. **A whole tractate, both arms.** One slice is 36 stories; the cluster population across
   four tractates is 29. Yevamot full is ~25 min per arm and the runs are deterministic,
   so 2 arms suffice — the repeats were only needed to establish that.
2. **Score precision, not just recall.** +4.3 proposals per 20 pages is a reviewer cost,
   and review throughput is the project's bottleneck.
3. **Report on the ADJACENT cases by name.** If a full run still recovers none of the 18,
   the clause is a small unrelated gain and the cluster hypothesis needs a different
   attack — say that plainly rather than shipping the clause as though it worked.
