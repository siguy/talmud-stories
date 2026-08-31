---
title: Add the 5 blind-list stories missing from the Ketubot golden
capability: [detection, classification]
tractate: [ketubot]
blocked_by: []
awaiting: []
finding:
superseded_by:
---

# Add the 5 blind-list stories missing from the Ketubot golden

**Self-contained.** Read `STATUS.md` and `FRAMEWORK.md` first.
**Capability: 2 Detection (ground truth).** **No LLM calls.** **Independent.**

## What is missing and why it matters

Five stories in Jeff's blind 2005 Ketubot list are **absent from our golden dataset**:
**20a, 53a, 67b, 72b, 82b.**

They are a *double* miss: the detector never found them **and** they were never in our
labels. That makes them invisible to every metric we have — `evaluate_golden.py` cannot
count a false negative for a story that is not in the golden. They only surfaced because
Jeff's list is blind.

Diagnosis of how each was lost is already written:
`docs/findings/2026-08-30-recall-miss-diagnosis.md` — three died in triage
(20a, 72b, 82b), two on pages that were examined but produced nothing.

## Method

1. Locate each story's text in the Sefaria Hebrew — `scripts/measure_recall_vs_expert_list.py`
   already resolves all five; reuse that alignment rather than re-deriving it.
2. Add each to `results/canonical/ketubot_canonical.json` with explicit provenance:
   `source: "jeff_2005_list"`, `blind: true`, and the note that it was never detected.
   **Do not silently merge them in as if they had always been there.**
3. Re-run `scripts/evaluate_golden.py` **with an explicit `--output`** (it defaults to
   overwriting `docs/golden/v7/baseline_ketubot.json`, a historical artifact) and report
   the before/after. Recall will drop, because we are adding stories we cannot find.
   **That drop is the point — the metric becomes honest, not worse.**
4. Say plainly in the writeup that the composite score falls and why.

## How you know it worked

The golden holds 187 stories, five of them flagged with expert-list provenance, and the
recorded Ketubot recall against the golden drops by roughly 3 points. If the score does
not move, the stories were not really added.

## Guardrails

- Never edit `scripts/evaluate_golden.py` — it is immutable.
- Always pass `--output`.
- A score that falls because the ground truth got more honest is a good outcome. Lesson
  13 already says this; do not let it look like a regression in any writeup.

## Outcome

**Done 2026-08-30 (`2e61035`).** Golden 182 -> 187. Recall fell 0.9371 -> 0.9085 and **the drop is the deliverable** — nothing about the detector changed; we added stories it cannot find so the harness can finally count them. Blind recall untouched at 96.0%. Golden coverage of Jeff's 149-story list 96.6% -> 100%. **Later corrected** by `6284070`: two of the five (20a segs 2-3, 53a seg 11) *were* proposed by earlier runs and classified `NOT_A_STORY`, so they are Classification rejections, not Detection misses. The generator's blanket 'never proposed' claim was checked against one run directory and asserted over all of them.
