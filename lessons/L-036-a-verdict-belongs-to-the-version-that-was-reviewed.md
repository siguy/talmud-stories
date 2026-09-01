# L-036 — A verdict belongs to the version that was reviewed

**Date:** 2026-08-31
**Found in:** Phase A of `review-verdict-axes`
→ [`2026-08-31-unclassified-notes-resolved.md`](../docs/findings/2026-08-31-unclassified-notes-resolved.md)

## The rule

**An expert verdict is a judgement about a specific version's output. Store the version
with the verdict, and never quote a round's precision as a current capability number
without checking that the current detector still makes the same calls.**

Corollary for reading old feedback: **read a note against what the reviewer saw**, which
is the reviewed version's classification — not against whatever the current run says
about the same passage.

## What happened

`build_ruler.py` joins historical verdicts onto today's proposals. Its
`detector_classification` column is therefore *today's* call, while the note beside it
was written about v5.1's, v7's or v8's. On 12 of 34 notes those differ.

Read against today's column, the notes look absurd — Jeff clicking `incorrect` while
writing *"This is definitely a story"* about an entry we currently classify `YES`. An
early pass through this set duly sorted that as "Jeff agreeing with us, miscoded as a
rejection". It is the exact opposite: v5.1 said `NOT_A_STORY`, he corrected it, and we
have since fixed it.

Of the 8 notes where the detector disagreed with a plainly-stated position at review
time, **today it agrees with 7**. Those are corrected defects still sitting in the pool
quoted as Classification precision.

## Why it is the same failure as L-030 and L-035, one axis over

Each is a metric pooled across a dimension it should have been split by, and each sends
the fix to the wrong place:

| lesson | pooled across | symptom |
|---|---|---|
| L-030 | **reasons for a rejection** | boundary failures reported as classification errors |
| L-035 | **stages of a pipeline** | Triage's losses charged to Detection as well |
| **L-036** | **detector versions** | fixed defects charged to the current detector |

The tell is the same in all three: a single number standing for several distinct things,
where improving the thing the number names would not move it.

## How to apply

- **Write the version into every verdict record.** One field. This is now a requirement
  on Phase B of `review-verdict-axes`; without it Phase C's point estimate inherits the
  defect in a new vocabulary.
- **When reading a banked round**, resolve each verdict against the run that round was
  generated from. `ROUND_SOURCES` in `scripts/resolve_unclassified_notes.py` is the
  mapping; extend it rather than re-deriving it.
- **Match spans by OVERLAP, never by exact key.** A verdict key names the extent the
  reviewed version proposed. A later version proposing the same passage with a different
  extent is a boundary change; keyed exactly it reads as *the story is gone*. This was got
  wrong first time and reported Ketubot 10b_3-3 as a regression when the current run in
  fact proposes 10b 3–5 at `HIGH_CONFIDENCE`.
- **Then, having matched properly, do not let "no proposal today" mean "no opinion".**
  For a *not-a-story* objection it is agreement by omission; for a *this-is-a-story*
  objection the passage has genuinely vanished, which is a Detection loss.
- **A round's precision is a historical fact about that version.** It is legitimate to
  report and must be labelled. It is not the current capability's number.

## The general form

Ground truth ages against a moving system. A judgement about output is only meaningful
paired with the output it judged — so the artifact identifier travels with the judgement,
always. This is the same discipline the project already applies to BLIND vs CIRCULAR and
to same-day baselines (L-011): **provenance is part of the measurement, not metadata
about it.**
