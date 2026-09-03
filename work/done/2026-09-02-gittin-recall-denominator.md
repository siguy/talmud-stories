---
title: Correct the Gittin recall denominator — Jeff retracted one of his own entries
capability: [detection]
tractate: [gittin]
blocked_by: []
awaiting: []
writes: [results/expert_lists/gittin_2005.json, results/recall/gittin_strict.json, results/recall/gittin_strict_rc3.json, results/recall/gittin_jeff2005_matches.json, docs/capabilities/2_detection.md, docs/findings/2026-08-31-gittin-first-run.md, tests/test_new_tractate_expert_lists.py]
finding:
superseded_by:
---

# Correct the Gittin recall denominator

**Self-contained.** Read [`FRAMEWORK.md`](../../FRAMEWORK.md) first, then this.
**Capability: 2 Detection.** **Cost:** free, no API calls.

## The problem

On 2026-09-01 Jeff retracted an entry from his own 2005 Gittin list — `gittin_075`,
Gittin 57a, the Sadducee's exchange with R. Ḥanina about the land's fertility:

> *"I agree that this is not a story and should not have been included. The list was
> wrong. Great to have the AI correct it!"*

We proposed nothing there, so it scores today as one of our four strict misses. It is not
a miss; **it is a case where we were right and the ground truth was wrong.**

`results/expert_lists/gittin_2005.json` still carries all 112 entries at
`counts_for_recall: true`, and `results/recall/gittin_strict.json` still reports
`denominator: 112`. Strict recall is **108/111 = 97.3%**, not 108/112 = 96.4%.

## Method

1. Set `counts_for_recall: false` on `gittin_075` **and leave `blind: true` alone** — it
   was blind; it is simply not a story. Record the retraction in the entry itself: his
   words, the date, and a pointer to the reply. The rule in
   [`docs/STORY_RULES.md`](../../docs/STORY_RULES.md) is that his lists are evidence, so
   this is an **annotation, never a deletion** — the entry stays, with a flag.
2. Regenerate the recall artifacts:
   `python3 scripts/measure_recall_vs_expert_list.py --tractate gittin --expert-json results/expert_lists/gittin_2005.json --output <scratch>` then move into place. Keep the
   unsuffixed `results/recall/gittin_jeff2005_matches.json` as the denominator file — the
   board reads it (CLAUDE.md).
3. Update the Gittin row in [`docs/capabilities/2_detection.md`](../../docs/capabilities/2_detection.md)
   and any finding that quotes 108/112, **as a Correction, not a silent edit.**

## How you know it worked

- `gittin_strict.json` reports `denominator: 111`, `recall_strict: 0.973`.
- The remaining three strict misses are `gittin_043` (38b), `gittin_054` (46b),
  `gittin_078` (57a Beitar) — **57a fertility is no longer among them.**
- `python3 scripts/board.py` regenerates STATE.md with the Gittin ground-truth row
  reading `112 parsed · 112 blind · 111 count for recall`, and the suite is green.

## Guardrails

- **Filter on the flags, never on the raw length** (CLAUDE.md). Anything that takes
  `len(stories)` as the denominator will silently keep 112.
- **The board's count-for-recall must equal the harness filter and the ruler
  denominator** — `tests/test_board_reports_what_it_holds.py` pins this. If it fails,
  the three have diverged, which is the defect the test exists to catch.
- Do not touch the other 111 entries. One retraction is not a licence to re-audit a
  blind list.

## When done

Write the finding to `docs/findings/2026-09-02-gittin-recall-denominator.md`, add an
`## Outcome` below, and `python3 scripts/board.py finish 2026-09-02-gittin-recall-denominator`.

## Outcome

**Done, 2026-09-02.** Strict recall **108/112 = 96.4% → 108/111 = 97.3%**; the remaining
misses are three, not four — 38b, 46b, 57a Beitar, all passages he has confirmed *are*
stories, so the deficit is now entirely ours.
Finding: [`2026-09-02-gittin-recall-denominator.md`](../../docs/findings/2026-09-02-gittin-recall-denominator.md).

Regenerated: `gittin_strict.json`, `gittin_jeff2005_matches.json`, and
`gittin_strict_rc3.json` — the last was not in the plan and was done anyway, because a
sibling artifact left at 112 is a number someone quotes later without knowing it is stale.

### One test had to change, and it is the interesting part

`test_the_committed_json_matches_a_fresh_parse` asserted
`recall_denominator == parsed story count`. That was true of a pristine list and stopped
being true the moment an expert withdrew an entry.

**The trap:** the cheapest way to make it pass is to delete `gittin_075` from the file —
which is precisely the edit [`STORY_RULES.md`](../../docs/STORY_RULES.md) forbids. A test
can push you toward the wrong fix as firmly as the right one, so it now pins the property
that actually matters: **every gap between entries and denominator is accounted for by an
annotation carrying his words, and the entry keeps `blind: true`.**

Blindness and story-hood are different facts. `gittin_075` was detector-blind and still
is; it is simply not a story. Collapsing the two flags would leave neither question
answerable.

### What was deliberately not touched

- **The boundary set.** `tests/expert_boundary_targets_2005_gittin.json` still carries the
  57a targets. A passage that is not a story still has an extent he drew, and dropping it
  from a boundary exam would be discarding evidence to move a different number.
- **`comms/2026-09-01-email-jeff-gittin.md`** and the sent artifact HTML. Sent
  correspondence is a record of what he was told; it is not updated after the fact.
- **The other 111 entries.** One retraction is not a licence to re-audit a blind list.

### A note on `board.py finish`'s drift report, for whoever hits it next

It ran here and was **wrong**, and the reason is worth knowing. `declared_vs_actual()`
diffs `main..HEAD` on **committed** work. This item was developed on a branch stacked on
another open PR and finished before its own commit, so the report showed the *previous*
PR's files as under-declared and this item's real files as "declared but never touched" —
exactly inverted.

It then escalated to a lane collision that does not exist: the previous PR's feedback
file against `classification-point-estimate`, two items that never ran concurrently.

Nothing is wrong with the check. It is accurate for the workflow it assumes — one branch,
one item, commit before finish. **On a stacked branch, run `finish` after the commit and
read its report against `git diff <parent-pr-head>..HEAD`, not against main.** The
`writes:` above is corrected from that diff, by hand.
