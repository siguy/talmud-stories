---
title: Separate "alone on the daf" from "surrounded by halakhah" — the density finding named the check and did not run it
capability: [detection]
tractate: [ketubot, kiddushin]
blocked_by: []
awaiting: []
writes: [results/recall/detection_density.json, scripts/audit_detection_density.py]
finding:
superseded_by:
---

# Separate "alone on the daf" from "surrounded by halakhah"

**Self-contained.** Read
[`docs/findings/2026-09-03-detection-density.md`](../docs/findings/2026-09-03-detection-density.md)
first — this item is the check that finding explicitly declines to run.

## Where it stands

Detection recall against the blind lists, by how many of Jeff's stories share the daf:

| stories on the daf | recall |
|---|---|
| **1** | **83.3%** |
| 2 | 95.9% |
| 4+ | **90.7%** |

It is not story length — found stories median 46 words, missed 44 — and the gap survives
inside a single length band (84% vs 94% for stories over 25 words).

The reading offered was **salience**: *we find a story among its own kind and miss it
embedded in legal give-and-take.* The finding then says plainly what it cannot support:

> "Alone on the daf" and "surrounded by legal material" are the same dapim in this data —
> nothing here separates *isolation* from *context*, and the proposed mechanism is the
> second. Testing it needs a measure of how much of a daf is halakhic, **which the triage
> labels can probably supply and this does not use.**

And a second confound:

> A daf where he found one story may be one where stories are genuinely marginal — harder
> for anyone, not just for us. That would make the profile a fact about the material
> rather than about the detector.

**Neither is checked. Both are checkable with no API calls.** Until one of them is, we do
not know whether to fix the detector or accept that those passages are marginal — and any
Detection work aimed at this is aimed at a correlation.

## Method — no API calls

1. **Build a halakhic-density measure per daf** from the cached Stage 1 labels: the share
   of segments labelled `DELIBERATION` / `VERBAL_ACT` against `NARRATIVE_EVENT`. The labels
   exist for every page in `results/v7/event_triage_*.json`.
2. **Re-run the density table with both variables.** Recall by (stories-per-daf ×
   halakhic-density). If recall tracks **density** at fixed story-count, the mechanism is
   context and the finding's reading is right. If it tracks **story-count** at fixed
   density, the mechanism is something else and "salience" was a story we told ourselves.
3. **Test the material-difficulty confound.** For the isolated dapim, compare the stories
   we missed against the ones we found on the *same* density band. If the misses are not
   distinguishable, the profile is about the material.
4. **Report the cell counts.** The published table has bands as thin as n=11, already
   flagged as unreadable. **A cell under n=20 is reported and not interpreted.**

## How you know it worked

A statement of the form *"at fixed halakhic density, recall does / does not vary with
stories-per-daf"*, with cell counts, over both tractates measured the same day
(Lesson 11). Gittin carries no signal — 3 misses in the tractate — and must be excluded
rather than pooled.

**A null result is a real outcome** and redirects Detection work away from this seam
entirely. That is worth as much as a positive one and costs the same nothing.

## Guardrails

- Correlational either way. This item can **relocate** the mechanism; it cannot establish
  causation, and the finding must not claim it does.
- Do not build a fix in this item. Its whole value is telling the next Detection attempt
  where to aim.

## When done

Finding to `docs/findings/<date>-density-mechanism.md`, `## Outcome` here, then
`python3 scripts/board.py finish density-mechanism`.
