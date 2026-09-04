---
title: The bookkeeping surface is the contended resource — shrink it
capability: []
tractate: []
blocked_by: []
awaiting: []
writes: [STATUS.md, scripts/board.py, docs/capabilities/, tests/test_bookkeeping.py]
finding:
superseded_by:
---

# The bookkeeping surface is the contended resource — shrink it

**Self-contained.** Read [`FRAMEWORK.md`](../FRAMEWORK.md), then
[`docs/findings/2026-08-31-concurrent-work-collisions.md`](../docs/findings/2026-08-31-concurrent-work-collisions.md),
then this.

**Raised, not scoped.** This is recorded so it is known and cannot be rediscovered from
scratch. Do not start it without agreeing the scope first — it changes conventions this
repo has deliberately chosen, and half of it may be the wrong trade.

## The claim to test / the problem

The 2026-08-31 audit fixed the *mechanics* of collision — the board regenerates instead of
merging, items declare `writes:`, lanes are computable. It did not touch the cause.

**The cause is that the same fact is stored in more than one place, so finishing any task
means editing every place it lives — and those places are therefore contended by
everyone, permanently, regardless of what the task was about.**

Measured on the commits preceding this item: bookkeeping is the *majority* of files
touched in most of them (`40eb568`: 5 of 7; `6ccc188`: 21 of 21). Two sessions working on
different tractates still both rewrite `STATUS.md`, regenerate the board, update a
capability history and move a work item. That is why the collision rate does not fall when
the work is separated — it is ~100% either way.

**This is not theoretical, and the direction of the error is the interesting part.**
`STATE.md` and `STATUS.md` both carry a section titled *"Ground truth on hand"* — one
generated, one typed. They disagreed: the generated cell said the Kiddushin recall
denominator was **91**, while `STATUS.md`, `results/rulers/kiddushin_ruler.json` and
`tests/test_kiddushin_list_parse.py` all said **90** (`kiddushin_050` is one story listed
twice). **The generated file was the wrong one** — fixed in `8771205`.

So the argument for generating a number is *not* that generators are trustworthy. It is
that one copy cannot drift, and when two copies disagree you cannot tell which one moved.
The only reason this was caught is that both happened to be read in one sitting.

> ## UPDATE 2026-09-03 — a live instance, and a merge obligation
>
> `STATUS.md` currently carries **retired** recall numbers: the 2026-09-03 matcher cutover
> moved Ketubot detection to 87.2%, its triage to 96.6%, Kiddushin loose to 84.4%, Gittin
> to 97.3% and Yevamot to 89.2%, and it moved two Ketubot stories from Detection's column
> to Triage's. `STATE.md` and `docs/capabilities/` were updated on the branch;
> **`STATUS.md` deliberately was not**, because it is hand-written and rewriting it in a
> branch is what makes every pair of concurrent branches conflict (CLAUDE.md, Concurrency).
>
> So the numbers are stale on main **by design**, and the design is exactly the problem
> this item names: the same fact lives in a generated file and a typed one, and the typed
> one can only be corrected by a human at merge time. **Whoever integrates the
> `feat/exact-anchor-matcher` branch must update `STATUS.md`'s scoreboard** — and that
> obligation existing at all is the evidence for doing this item.

## Method

`STATE.md` exists because "this repo has twice carried the same number in two places and
let them drift" (`board.py` docstring). That principle was applied to `STATE.md` and
`WORK.md` and then stopped. Finish applying it:

1. **Inventory `STATUS.md` by kind.** Which paragraphs are *judgment* (the strategic fork,
   the hazards, "treat this as indicated not measured") and which are *restatement* of
   something already on disk — the scoreboard, the next-items table, the ground-truth
   block, the waiting-on-Jeff list that the file itself says lives in `comms/JEFF.md`.
2. **Generate the restatement half**, leaving `STATUS.md` as prose only. Two sessions
   rarely rewrite the same paragraph; they always rewrite the same table.
3. **Close the `STATUS`-pointer cells in the coverage matrix** while there. `STATE.md`
   documents them as a known generator gap: Triage, Classification and Boundaries have no
   committed measurements file, so the honest cell is a pointer. A small
   `results/measurements/*.json` written by the scoring scripts would close it — and would
   also stop those numbers being typed into `STATUS.md`, which is the same problem.
4. **Consider the same for `docs/capabilities/`** — 10 open items point at
   `3_classification.md`, 8 at `2_detection.md`. Its "what was tried / what was reverted"
   log is derivable from the `## Outcome` of the items naming that capability.

## How you know it worked

- No number appears in both `STATUS.md` and a generated file.
- `python3 scripts/board.py lanes` shows fewer contended paths than it does today.
- The 91/90 class of defect becomes unrepresentable rather than caught by luck.

## Guardrails

- **Do not generate the judgment.** `STATUS.md`'s value is the part a script cannot write —
  the strategic fork, the two clocks, what is *indicated* rather than measured. A fully
  generated `STATUS.md` would be a worse file, not a less contended one.
- **`GOLDEN_COUNTS` is a separate question and probably a different answer.** It is
  contended by five items, but it is pinned *deliberately* (`CLAUDE.md` Rule 5) as the
  guard against silent golden loss, and a guard that derives its expectation from the
  thing it guards is not a guard. Moving the dict to its own small file would shrink the
  conflict without weakening it. Deriving it would weaken it. Do not conflate these.
- Lesson 33: if this starts needing a mechanism to protect the mechanism, stop.

## When done

Finding to `docs/findings/`, add `## Outcome`, then
`python3 scripts/board.py finish 2026-08-31-status-facts-are-typed-twice`.
