---
title: STATE.md reports the superseded triage rule — re-run the recall harness, or stamp the artifact
capability: [triage, detection]
tractate: [ketubot, kiddushin]
blocked_by: []
awaiting: []
finding: docs/findings/2026-09-01-board-guards-verify-the-wrong-property.md
superseded_by:
---

# STATE.md reports the superseded triage rule

**Self-contained.** A fresh session executes this with no other context.
Read [`FRAMEWORK.md`](../FRAMEWORK.md) first, then this.

## The claim to test / the problem

`should_skip_page()` keeps any page with `>=1 NARRATIVE_EVENT` as of 2026-08-31
([`triage-single-narrative`](../docs/findings/2026-08-31-triage-single-narrative.md)).
The board still reports the rule it replaced:

```
STATE.md      Ketubot 98.0%   Kiddushin 95.6%     <- previous corroboration rule
shipped code  Ketubot 98.7%   Kiddushin 97.8%     <- measured, in the finding, in STATUS.md
```

`board.py recalls()` derives both cells from
`results/recall/<t>_jeff2005_matches.json`, whose `survived_triage` flag came from the
shipped run's examined-page set — produced under the old rule. The generator is faithful;
the artifact is stale. `board.py --check` passes, because it compares the generator
against itself.

**Two reasons this is worth doing properly rather than quickly:**

1. It is Triage — FRAMEWORK §2 calls its errors invisible and permanent, and it holds the
   strictest gate on the board. It was also, under the old rule, the **only cell below its
   gate**, so the stale number is the one most likely to be acted on.
2. The **Detection** cells inherit it. `detection_given_triage` divides by the same
   `survived_triage` set, so all four cells on the coverage matrix are conditioned on a
   partition the detector no longer uses.

**This is a measurement decision, not a cleanup.** Re-running rewrites the file CLAUDE.md
calls *"always the recall denominator"*, which changes what every recall cell means. Hence
an item rather than a patch.

## Method

**Option A — re-run the harness under the live rule (preferred).** No API calls: the
triage labels are cached and `merge_triage_recall_run.py --live-rule` exists precisely for
this.

1. Confirm the partition first, with no writes:
   `python3 scripts/run_triage_recall_price.py --dry-run`
2. Splice the discarded-page Stage 2 output into the shipped run under the **current**
   `should_skip_page()`:
   `python3 scripts/merge_triage_recall_run.py --live-rule ...`
3. Score through the recall harness, writing to a **scratch path first**:
   `python3 scripts/measure_recall_vs_expert_list.py ... --output <scratch>/ketubot_live.json`
4. Diff against the committed artifact and check the story-level deltas by name before
   promoting. Expect Ketubot +1 (**51a**) and Kiddushin +2, per the finding.
5. Only then overwrite `results/recall/<t>_jeff2005_matches.json`, and regenerate the
   board.

**Option B — if A is deferred, make the staleness visible.** Cheaper and strictly better
than the status quo: stamp the rule into the artifact and have the board check it.

- `measure_recall_vs_expert_list.py` writes a `triage_rule` field — the source of
  `should_skip_page()`, hashed, or a version string it owns.
- `board.py` compares that against the live function and renders the cell as
  **`98.0% (STALE — computed under a different triage rule)`** when they differ.
- A test asserts the two agree, so the next rule change fails the suite instead of
  silently ageing the board.

Option B is the durable half either way: A fixes today's numbers, B stops it recurring.
**Do B even if you do A.**

## How you know it worked

- `STATE.md` Triage reads **98.7% / 97.8%**, matching `STATUS.md` and the finding.
- The Detection cells are recomputed against the new surviving set, and the change is
  *stated* — they will move, and a silent move is what created this item.
- `python3 scripts/board.py --check` passes, and now means something.
- The new provenance test fails if `should_skip_page()` is edited without regenerating.
- **Counts, not the composite** (CLAUDE.md rule 5): verify with `n=`, the per-story
  `survived_triage` deltas, and `git hash-object`.

## Guardrails

- **`scripts/evaluate_golden.py` is IMMUTABLE**, and always run it with `--output <scratch>`.
- **Never `git stash`** — commit to the branch.
- The unsuffixed `<t>_jeff2005_matches.json` **is** the recall denominator; sensitivity
  variants take a suffix. Do not rename one to dodge the overwrite (CLAUDE.md, Key Files).
- Do not promote a scratch run without checking the added stories **by name**. The loose
  recall window credits a different passage on the same daf in 2 of 6 cases tested
  (Lesson 37's neighbour;
  [`kiddushin-comments-harvest`](../docs/findings/2026-08-31-kiddushin-comments-harvest.md)).
- Quote every figure as end-to-end **or** given-the-page-survived-triage, never bare
  (Lesson 35).
- The **strict** end-to-end column has not been re-measured since the rule changed. If you
  re-run anyway, re-measure it too rather than leaving a second stale number behind.

## When done

Write the finding to `docs/findings/<date>-<slug>.md`, add an `## Outcome` section
below, and `python3 scripts/board.py finish <slug>`. **Never delete it.**
