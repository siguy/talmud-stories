---
title: Consensus A — freeze the calibration set before any judge is written
capability: [classification, review]
tractate: []
blocked_by: []
awaiting: []
writes: [results/consensus/calibration_set.json, scripts/build_calibration_set.py, tests/test_calibration_set.py]
finding:
superseded_by:
---

# Consensus A — freeze the calibration set

**Self-contained.** Read [`FRAMEWORK.md`](../FRAMEWORK.md), then the plan
[`consensus-at-scale`](../docs/history/2026-09-28-PLAN-consensus-at-scale.md) §4. This item is the exam; it is written **before** the
judges so the judges cannot be fitted to it.

## The problem

Phase D will measure how often a unanimous machine verdict agrees with Jeff. That number
is only honest if the labels were fixed first and no page the judges were shown is also
a page they are scored on (Lesson 2).

## Method

1. Collect every expert label on disk into one file, one row per labelled span:
   - verdict rounds via `scripts/map_verdict_vocabularies.py` (605 banked), plus
     `validation/feedback/gittin_axes_review_2026-09-02.json` and
     `validation/feedback/review_2026-09-16_bundle_jeff_2026-09-23.json` if not already
     mapped. **Every file read must be counted and named** — an unrecognised shape is an
     error, not a skip (Lesson 38);
   - the five 2005 lists (`results/expert_lists/*_2005.json`, filtered on
     `counts_for_recall`) as **positives only**;
   - Simon's pre-screen as a **separate, non-expert** source.
2. Per row: tractate, ref, segments (as located by the exact matcher for list entries),
   label (`story` / `borderline` / `not` / `out_of_scope`), source file, date,
   `applies_to` and detector version, BLIND or CIRCULAR.
3. **Precedent exclusion.** Build the list of every page cited as a case in
   `docs/STORY_RULES.md` — these are the judges' precedents. Mark each row on those pages
   `held_out: false`. Everything else is `held_out: true`.
4. Report counts: positives / negatives / borderline per tractate, BLIND vs CIRCULAR,
   held out vs not. **Negatives are the constraint** — state n.
5. Write `results/consensus/calibration_set.json` with its own sha256 in a sidecar; the
   test pins the hash, so a later edit is visible.

## How you know it worked

- Row counts reconcile to the sources (e.g. 605 mapped verdicts accounted for, dropped
  rows named with reasons).
- No held-out row sits on a precedent page (test).
- The hash is pinned.

## Guardrails

- Labels are copied, never edited. A disagreement between his 2005 list and a later
  verdict is kept as two rows (STORY_RULES: annotate, never move).
- No model calls in this item.

## When done

Finding to `docs/findings/<date>-calibration-set.md` (the counts), `## Outcome`, then
`python3 scripts/board.py finish 2026-09-28-consensus-a-calibration-set`.
