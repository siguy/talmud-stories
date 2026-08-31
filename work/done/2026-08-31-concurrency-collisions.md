---
title: Make concurrent work items declare what they write
capability: []
tractate: []
blocked_by: []
awaiting: []
writes: [work/, scripts/board.py, tests/test_bookkeeping.py, .gitattributes, requirements.txt, CLAUDE.md]
finding: docs/findings/2026-08-31-concurrent-work-collisions.md
superseded_by:
---

# Make concurrent work items declare what they write

**Self-contained.** Read [`FRAMEWORK.md`](../../FRAMEWORK.md), then
[`lessons/L-032`](../../lessons/L-032-a-clean-merge-is-not-evidence-that-the-result-is.md)
and [`L-033`](../../lessons/L-033-when-a-mechanism-needs-a-third-guard-remove-the.md), then this.

## The claim to test / the problem

`work/` carries 30 open items and the repo runs several sessions at once as a matter of
course. Every item records `blocked_by` — **ordering**. Nothing records what an item
*writes* — **contention**. Those are different graphs, and only one of them exists.

Two items with no `blocked_by` relation are presented as concurrently runnable by
`STATE.md`, `WORK.md` and `STATUS.md` alike, whether or not they write the same file.
Six such pairs exist among the items runnable today, and the board recommends four of
them as the cheapest next steps.

## Method

1. Measure the collision rate on real history rather than asserting it.
2. Add `writes:` to the item frontmatter and to `_TEMPLATE.md`; populate all open items.
3. Teach `board.py` to compute the contention graph and emit disjoint lanes
   (`board.py lanes`), and surface it in `STATE.md` beside the coverage matrix.
4. Make the *guaranteed* collision impossible rather than detected: generated and
   session-scoped files are not branch artifacts, enforced by a test.
5. Make a fresh clone able to run the mandatory gate.

## How you know it worked

- `python3 scripts/board.py lanes` names every colliding pair among open items, and the
  pairs it names are the ones found by hand in the finding.
- `python3 -m pytest tests/ -q` passes from a clone with nothing but `requirements.txt`
  installed — it does not today.
- The three pairs that share `results/canonical/`, `src/story_detector_v11.py` and
  `scripts/measure_recall_vs_expert_list.py` land in the same lane, not parallel ones.

## Guardrails

- **Do not build a lock** (Lesson 33). The requirement is "two sessions must not
  corrupt each other", and a reservation protocol creates the problem it then defends.
  Prefer declaring the write-set and serializing the lane.
- **Over-declaring `writes:` costs a serialized lane; under-declaring costs a silent
  corruption.** They are not symmetric — declare generously.
- Do not touch `scripts/evaluate_golden.py` or `docs/golden/v7/baseline_ketubot.json`.
- A clean merge is not evidence (Lesson 32): the point of this item is the collisions
  git will *not* report.

## When done

Finding to `docs/findings/2026-08-31-concurrent-work-collisions.md`, add `## Outcome`,
then `python3 scripts/board.py finish 2026-08-31-concurrency-collisions`.

## Outcome

**Confirmed, and worse than the question assumed.** Full write-up in
[`docs/findings/2026-08-31-concurrent-work-collisions.md`](../../docs/findings/2026-08-31-concurrent-work-collisions.md).

Measured: 51% of recent commit pairs touch a common file; 31 open items resolve to **15**
lanes, not 31; and three worktrees carrying 30 uncommitted files sit on branches that
exist on no remote (`git ls-remote --heads origin` returns one ref).

Three things were not anticipated when this item was written:

1. **The guaranteed collision has nothing to do with the work.** Three sessions each
   opening one *unrelated* item produced two conflicting merges, five conflict markers
   committed into `WORK.md`, and a trunk on which `board.py --check` failed. Bookkeeping
   collided harder than data, and for no information.
2. **A merge driver alone is not enough, and the reason is worth keeping.** It runs while
   the merge is in progress, when `work/` on disk does not yet hold the other side's
   items — so it resolves the conflict but writes a *stale* board. Found by testing it,
   not by reasoning about it. The driver keeps conflict markers and a broken checksum out
   of a generated file; `.githooks/post-merge` produces the truth. Both are needed and
   they do different jobs.
3. **The suite had never been green on Linux** — `textutil` is macOS-only and a `node -e`
   argument exceeded `ARG_MAX`. `1 failed / 5 errors` → `100 passed, 2 skipped`. A cloud
   session could not previously satisfy the gate `CLAUDE.md` requires before stopping.

Verified by A/B in two identical repositories differing only in whether `board.py setup`
had been run: **2 of 3 merges conflicting → 0**, and `board.py --check` FAIL → PASS.

**Not done, deliberately.** `STATUS.md` remains a serial collision — it is hand-written
and no driver can merge it; the resolution is that rewriting it is an integration step,
now stated in `CLAUDE.md` but not enforced, since a test would fire on legitimate trunk
work. And `GOLDEN_COUNTS` still forces every golden-growing item into one lane; decoupling
it means changing a guard `CLAUDE.md` Rule 5 pins on purpose, which is Simon's call.
