# Two pre-flight fixes: spans that leave the page, and the Mishnah key the boundary scorer could not see

**2026-08-31.** Both defects were latent on Ketubot and Kiddushin and would have landed
unmeasured on a virgin tractate, where there is no prior run to diff against. Neither
needed an API call. Work item:
[`2026-08-31-span-bounds-and-mishnah-readers`](../../work/done/2026-08-31-span-bounds-and-mishnah-readers.md).

## 1. A proposed span must lie inside its page

Stage 2 proposed `Ketubot 112b, start_segment -2, end_segment 0`. Nothing checked it —
reported 2026-08-31 in [`triage-recall-price`](2026-08-31-triage-recall-price.md), hit
again by the [proposal screen](2026-09-01-unread-proposals-screened.md), unfixed both
times.

**Why it is worse than a bad number.** Python does not raise on a negative index. Every
Stage 4 post-processor slices `segments[start:end + 1]`, so `-2` means *the second
segment from the end of the page*. The story is then snapped, trimmed, span-extracted and
displayed from the wrong text, with no error and no trace. The one we caught sat on a
triage-discarded page and so reached no published number. That is luck.

`validate_story_spans()` (`src/story_detector_v11.py`, v11 only — v7–v10 stay frozen) runs
inside `detect_stories()`, which covers both Stage 2 passes and the one other caller,
`scripts/run_triage_recall_price.py` — the script the 112b span came out of.

| input | what happens | why |
|---|---|---|
| `-2..0` on a 4-segment page | **clamped** to `0..0` | a real proposal with a wrong start |
| `8..14` on a 10-segment page | **clamped** to `8..9` | same, at the other end |
| `10..0` on an 11-segment page | **clamped** to `10..10`, `needs_review: True` | see below |
| `12..15` on a 10-segment page | **dropped** | not about this page at all |
| `14..2`, or a non-integer end | **dropped** | no usable anchor |

**The reversed span is the one judgment call.** `Ketubot 22a` — found while auditing every
run on disk, and *not* previously known — proposes `10..0` with a summary describing a real
story (Shmuel, Rav, and the answer studied forty times). Deleting it would spend a
Detection miss, the expensive kind, to avoid a Boundaries error. Swapping the ends would
be a guess written where a judgment goes (Lesson 21). So it collapses to the half the
model got right and is stamped `needs_review`.

**Every repair is counted and named** — printed per page, accumulated on the detector, and
written to the run as `span_repairs`, always present, `[]` included. A key that appears
only on failure reads as absence of the check itself. A silent clamp would turn a model
defect into a boundary defect that scores as ours; a silent drop is Lesson 38's shape,
where an `isinstance` guard swallowed a 25-verdict expert round for eight months.

**Measured against every run on disk:** exactly two malformed spans in the whole corpus,
`Ketubot 112b` (clamped) and `Ketubot 22a` (collapsed). Both are now caught at Stage 2.
Guarded by `tests/test_span_bounds.py` — 15 tests, written first and watched fail,
including end-to-end failure injection through `detect_stories()`.

## 2. The boundary scorer could not see `mishnah_stories`

Lesson 27's rule is standing: move output to a key no harness reads and an invisible
deletion reads as a model failure. The recall harness and the axis review UI were taught
to read `mishnah_stories`. `scripts/score_boundary_targets.py` was not — so a target on a
withheld story scored `N/A`, whose own docstring defines it as *"this run has no story
covering that segment (a detection gap)"*. It is not a detection gap. The story was found,
bounded, and then set aside on a scope judgment still open with Jeff
(`jeff:mishnah-scope`).

The scorer now reports a fourth bucket, `WITHHELD`, folded into neither the score nor
`N/A`.

**This was not hypothetical.** On `results/v11/wave5_summaryfix/ketubot_2-60_v11_g37high.json`,
**2 of the 294 blind targets** move `N/A → WITHHELD`. Both sit on `Ketubot 54b`, one of
the two chapter-boundary mis-tags — and the current tagger no longer withholds it
(`8fd68de`), so on a fresh run they score normally. The bucket named a stale artifact's
known defect instead of burying it in the detection-gap column. Kiddushin: 0 withheld,
**85% / 91%, unchanged**; Ketubot 61–112: 0 withheld, **80% / 84%, unchanged**.

The stale claim that *"no harness or UI reads that key"* is corrected in `CLAUDE.md` and
in `new_tractate_workflow.md` Step 7, both of which now carry the per-reader table:
who reads it, and which way each one decided. `evaluate_golden.py` is still blind and
still immutable; its delta stays with `report_mishnah_filter_delta.py`.

Guarded by `tests/test_boundary_scorer_reads_mishnah_key.py`.

## What this does not do

Neither fix changes a detector prompt, a model, or any shipped score. Stage 4's own
post-processors are not bounds-checked — only the model output entering at Stage 2 is,
which is where both defects came from.
