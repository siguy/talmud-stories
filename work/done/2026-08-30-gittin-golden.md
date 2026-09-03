---
title: Gittin — golden
capability: [classification]
tractate: [gittin]
blocked_by: [2026-08-30-gittin-expert-round]
awaiting: []
writes: [results/canonical/gittin_canonical.json, tests/test_bookkeeping.py, scripts/build_gittin_golden.py, comms/JEFF.md]
finding:
superseded_by:
---

# Gittin — golden

**Self-contained.** Read [`FRAMEWORK.md`](../../FRAMEWORK.md) and
[`docs/technical/new_tractate_workflow.md`](../../docs/technical/new_tractate_workflow.md),
which documents this sequence, then this.

## Method

See the workflow doc; this item is the handle and the ordering.

## Guardrails

- **Ask Jeff to keep his appendix separate BEFORE the first review round**, not
  after (Lesson 29). Once merged into his list it cannot be reconstructed, and the
  list stops being able to measure what we missed.
- Regenerate a same-day baseline before any comparison (Lesson 11).
- Report the corrections ruler and the neutral ruler separately (Lesson 24).

## When done

Finding to `docs/findings/`, add `## Outcome`, `git mv` to `work/done/`.

## Outcome

**Done, 2026-09-02.** `results/canonical/gittin_canonical.json` — 178 pages, **135
entries**, built by [`scripts/build_gittin_golden.py`](../../scripts/build_gittin_golden.py).
Finding: [`2026-09-02-gittin-golden.md`](../../docs/findings/2026-09-02-gittin-golden.md).

| | |
|---|---|
| `expert_verdict` (he judged our span) | 25 |
| `expert_blind_list` (his list names a story our span overlaps, strictly) | 110 |
| `YES` / `BORDERLINE` / `NOT_A_STORY` | 113 / 4 / **18** |
| proposals with no expert evidence, kept **out** | 23 |
| his stories no proposal covers strictly | 3 |

**Blind end to end** — the first golden of which that is true. No Gittin material was in
any prompt, the run predates his list being opened, and the verdicts came after the run.
The 18 negatives are what the other two goldens do not have: explicit expert rejections on
a tractate that was never in a prompt.

### The design decision, and why it is not cosmetic

Two kinds of evidence, never merged, `label_source` on every entry. A verdict judges the
passage **and the extent**; a 2005 list entry says only that a story is there, and was
written twenty years before the span existed. Merging them lets an unvalidated boundary be
quoted as expert-confirmed (Lesson 24's shape). A test fails if the split disappears.

Two consequences of the same principle:

- **Every entry carries an expert label.** 23 proposals with no expert evidence are named
  in `unlabelled_proposals` rather than written in with a null classification — a null in
  a file called *golden* is read as a label by the next reader and as a fact by the one
  after.
- **`BORDERLINE` is not rounded.** He asked for contested cases to be kept and flagged
  (2026-07-06); rounding them is the thing he declined.

### What building it strictly found — the part worth reading

Two `YES`-tier proposals turn out to have **no expert evidence at all**: Gittin 57b:0-4
(Nebuzaradan and Zechariah's blood) and 68a:7-12 (Solomon and Ashmedai). Both were counted
as list matches by the **loose** window, which credited a neighbouring story on the same
daf — the third and fourth known instance of that failure, and the first found by a
consumer instead of by hand-checking.

So a claim in the sent email — *"all 59 we called certain are on your list"* — **is false
for two of them.** Recorded in `comms/JEFF.md` under corrections owed;
→ [`gittin-two-unjudged-yes`](../2026-09-02-gittin-two-unjudged-yes.md).

They are very likely stories. They are recorded as `indicated` and kept out of the golden,
because this week has twice shown that only a ruling on a passage settles that passage.

### Guardrail that did not apply

The item's boilerplate says to regenerate a same-day baseline before comparing (Lesson 11).
Nothing is compared here — a golden is assembled, not scored — so there is no baseline to
regenerate. Recorded rather than silently skipped.

### On the drift report `finish` printed

It named nine under-declared paths. Eight belong to the two earlier PRs this branch is
stacked on — `declared_vs_actual()` diffs `main..HEAD`, so on a stack it attributes every
ancestor commit to the item being closed. The `writes:` above is corrected by hand from
`git diff <parent>..HEAD`. Same caveat as
[`gittin-recall-denominator`](2026-09-02-gittin-recall-denominator.md); the check is right
for one-branch-one-item and misleading for a stack.
