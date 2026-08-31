# NEXT 00 — Write the history of each capability

**Self-contained.** Read [`FRAMEWORK.md`](../../FRAMEWORK.md) first, then this.
**Depends on Jeff: no.** **No API calls.** **Cost: reading time, a few hours.**

## Before you start — state as of 2026-08-30

Steps 0–6 of the reorg plan (`~/.claude/plans/fuzzy-yawning-hinton.md`) are **done**:
four branches merged, lessons de-duplicated to a clean 1–30, trunk and
`claude/repo-reorganization-execution-bed72b` both pushed. This brief is **step 7**, and
the plan calls it the highest-value item because it decays fastest. Steps 8–13
(restructuring) come after and are reversible.

**Three corrections landed today that this brief must reflect.** Each was a confident
claim whose scope did not match the scope of the check behind it, so do not carry the
old versions forward from any doc that predates them:

1. **Ketubot 20a segs 2-3 and 53a seg 11 are Classification rejections, not Detection
   misses.** Both were proposed by earlier runs (`results/v5/pages_2-39.json` and
   `results/v7/ablation_v6_triage_merge.json`) and classified `NOT_A_STORY`, at 100%
   Hebrew 4-gram coverage. The taxonomy in
   `docs/golden/workflow/recall_miss_diagnosis_2026-08-30.md` is 3 Detection misses and
   2 Classification rejections, not 5 misses. Same re-diagnosis `abdc4af` made for 77a.

2. **The Kiddushin appendix is three signals, not one** —
   `docs/golden/v11/appendix_provenance_correction_2026-08-30.md`. 33a/45a are Detection
   successes; 53a/71a are Detection hits with the wrong extent, which belong to
   **Boundaries**; 81b is a genuine Detection miss. Recall denominator 89 → **90**;
   strict Kiddushin recall 84.3% → **83.3%**.

3. **The loose recall window demonstrably over-credits.** Jeff's 81b story is at
   segment 9; every run proposed segments 1-3 and 14 and nothing at 9 — 9% text overlap
   — and the loose test credits it anyway. Pinned by
   `tests/test_build_ruler.py::test_the_loose_window_credits_a_story_we_never_proposed`.
   This is the first case that proves the loose/strict gap without relying on the
   aligner, and Detection's record should quote the strict number beside the loose one.

**Hazards, verified — read before running anything:**

- **Never run `scripts/evaluate_golden.py` without `--output`.** It defaults to
  overwriting `docs/golden/v7/baseline_ketubot.json`, an irreplaceable historical record.
- **Never verify with the composite score.** It is built from ratios over pages already
  in the golden, so deleting expert validations makes it go **up**. Verify with counts
  (`ketubot` 222 pages / 187 stories / 164 accepted; `kiddushin` 162 / 96 / 85) and
  `git hash-object`.
- **Never `git stash` / `stash pop`.** `refs/stash` is shared across all worktrees.
  Commit to your branch instead. (`git stash create` also silently drops untracked files.)

## What this produces

Six files, `docs/capabilities/1_triage.md` … `6_publication.md`. One per capability in
FRAMEWORK §1. Each answers, for that capability alone:

1. **What have we tried?** — every attempt, in order, with its outcome.
2. **What did we revert, and why?** — this project has several; they are the most
   instructive entries and the easiest to lose.
3. **What is our current best?** — the exact configuration, its number, and the dataset
   that number came from.
4. **How far from the gate?** — and whether that distance is inside the noise.
5. **Is there a ceiling?** — a limit no amount of tuning passes.
6. **What is untried?** — the honest list, including things we decided against.

This is the missing layer. `STATUS.md` says where we are, `FRAMEWORK.md` says how we
measure, `tasks/NEXT/` says what to do — **nothing says what we already tried**, so every
session risks re-running a dead end. That has already happened once: Ein Yaakov was
proposed to Jeff, rejected by him, recorded in the ledger, and then re-proposed months
later by someone who had not read it.

## The required shape

Use this exact skeleton in every file, so the six can be read side by side.

```markdown
# Capability N — <name>

**Definition:** one line, and a link to FRAMEWORK §1.N. Do not restate it.
**Gate:** <value> (PROVISIONAL / DERIVED — copy the marker from FRAMEWORK)
**Current:** <value> on <dataset> (BLIND / CIRCULAR), measured <date>

## What we tried
| when | what | outcome | evidence |
|---|---|---|---|
| 2026-xx-xx | … | improved / no change / reverted | `docs/golden/...` or commit sha |

## What we reverted, and why
…the reasoning, not just the fact. A revert we cannot explain will be re-tried.

## Current best — the exact configuration
Files, flags, model, prompt version. Enough that someone could reproduce the number.

## Distance to gate
Current vs gate, and whether the difference exceeds the run-to-run noise for this
capability. If the noise is unknown, say so — do not imply precision we do not have.

## Ceiling
Any measured structural limit, with its evidence. "None known" is a valid answer.

## Untried
Including things deliberately declined, with the reason and who declined them.
```

## Where the history actually lives

Read these; do not reconstruct from memory.

| source | what it holds |
|---|---|
| `git log --oneline` | the spine. Every wave and revert is a commit with reasoning in its body. |
| `docs/golden/v7/ … v11/` | dated findings per detector era. v11 is 2026-08-30. |
| `tasks/PLAN_wave*.md` | what each wave *intended* — compare against what shipped. |
| `tasks/lessons.md` | 24 lessons; most were bought by a failure worth recording. |
| `validation/feedback/jeff_*_ledger.md` | everything Jeff said and its disposition. |
| `archive/todo_history_pre_2026-08-30.md` | the old 539-line todo, for provenance only. |

**Waves map onto capabilities, they are not capabilities.** Wave 4 was Boundaries. Wave 5
and 5b were Boundaries. Wave 6 is Classification. Wave 1-3 touched Detection and
Classification together. Sort each wave into the capability it actually changed — that
re-sorting is most of the work, and most of the value.

## Discipline — non-negotiable

- **Every number names its dataset and says BLIND or CIRCULAR** (FRAMEWORK §3). A
  circular number is not an accuracy claim.
- **Every finding is labelled measured / indicated / suspected.** If you cannot tell
  which, it is `suspected`.
- **Every claim cites a dated doc or a commit.** No claim from memory.
- **Do not restate status.** Status lives in `STATUS.md`. If you find yourself writing
  "we are currently…", stop — that belongs in the Current line and nowhere else.
- **Record failures at the same weight as successes.** Wave 4's char-offset spans were
  wrong in 9 of 9 reviewed cases; the boundary record is not honest without that.

## How you know it worked

Someone who has never seen this project can read one file and answer: what has been
tried here, what is the best we have, and what would be a waste of time to re-attempt.

## When done

Add the six links to `STATUS.md` under each capability. Delete this brief.
