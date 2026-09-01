# The round nothing reads — Jeff's 2026-01-08 Ketubot verdicts

**Date:** 2026-08-31
**Capability:** 3 Classification, 4 Boundaries, ground truth
**Dataset:** `validation/feedback/ketubot_review_Jeffrey_Rubenstein_2026-01-08.json` — **CIRCULAR**
**Status:** measured (the inventory) — **nothing folded into the golden**
**Feeds:** [`work/2026-08-30-golden-completeness.md`](../../work/2026-08-30-golden-completeness.md)

---

## The standing note was overstated, and it was hiding the real one

`STATE.md` has listed **three** files under *"Expert verdicts on disk that no ruler
reads … Lesson 1's failure, still live."* Opened and counted:

| file | what is actually in it |
|---|---|
| `ketubot_review_Jeffrey_Rubenstein_2026-01-08.json` | **25 real expert verdicts, 24 with notes** |
| `validations_v4_2026-01-25.json` | `validations` is an **empty dict**. Nothing to lose. |
| `jeff_v4.1_validation.json` | 6 rows of `expected` / `ai_result` / `confidence` / `reasoning` — an **automated eval trace**, not expert judgement at all |

**One file, not three.** Listing all three as lost expert work made the gap look like a
filing backlog; it is one specific, recoverable round, and the other two entries were
camouflage. `scripts/board.py` now counts verdicts and omits files holding zero, so the
generated board names the one that matters.

## Why no ruler reads it

Mechanical, and the same shape as several other defects found this week.
`build_ruler.load_reviews()` requires `reviews`/`feedback` to be a **dict** keyed
`"<ref>_<start>-<end>"`. This round stores a **list** of
`{ref, feedback_type, notes, length_adjustment, spans_multiple_pages, …}`. An
`isinstance(items, dict)` guard skips it — **silently**, with no count and no warning,
exactly like any other file whose shape does not match.

A guard that skips is indistinguishable from a file that is empty. That is why this sat
for eight months while the file itself was listed in `STATE.md` the whole time.

## What is in it

Jeff Rubenstein, by name, 2026-01-08, Ketubot, 25 of 243 stories reviewed.

| | n |
|---|---|
| verdicts | **25** (16 `false_positive`, 8 `correct`, 1 untyped) |
| carry a note | **24** |
| **cross-page refs** (`Ketubot 10b-11a`) | **9** |
| **covered by no round any ruler reads** | **9** — the same 9 |
| carry a structured `length_adjustment` | **10** |
| flagged `spans_multiple_pages` | **9** |

Two things here exist nowhere else in the corpus:

**1. Nine cross-page refs, covered by nothing.** Every other round names a single daf
with segment indices; this one names spans like `Ketubot 3b-4a`, `Ketubot 21b-22a`. Those
9 refs appear in **no** round any ruler reads. Cross-page stories are the project's known
weak spot — all 12 Ketubot stories in the strict/loose recall gap are cross-page stories
on continuation dapim where we proposed nothing. This is 9 expert judgements aimed
squarely at that weakness, unread.

**2. Boundary and merge signal in structured fields.** `length_adjustment` (10 rows) and
`spans_multiple_pages` (9 rows) are dedicated columns. Every later round buried the same
information in free text, which is exactly the problem
[`review-verdict-axes`](../../work/done/2026-08-30-review-verdict-axes.md) exists to fix —
**the UI had the right shape in January and lost it.** Worth knowing before Phase B
designs it again from scratch.

## The criteria, in his own words, six months early

24 notes, and they are the sharpest statements of his story criterion on record —
predating `2026-07-06-jeff-story-definition-criteria.md` by half a year:

> "This is a legal discussion with no story. It is prescriptive. What the law is and
> therefore what should happen … A story must be descriptive -- what did happen."

> "Narrative elements in legal codes or rulings are not stories."

> "It deals with potential or hypothetical legal cases, not one-time events."

The prescriptive/descriptive distinction and the hypothetical/actual one are both already
in the criteria doc — **independently arrived at**, which is corroboration rather than new
information. That is worth something on its own: the criteria doc is not an artifact of
one conversation.

## Why nothing was folded in

**The verdicts carry no segment spans.** Every other round names
`"<ref>_<start>-<end>"`; this one names only the daf. Attaching a verdict to a proposal
would mean re-deriving which v4-era story on that daf each refers to — and **v4 output is
not on disk**. For the 9 cross-page refs there is not even a single daf to attach to.

So the verdicts are **not** mechanically recoverable, and pretending otherwise by
attaching them to whatever we propose there today would manufacture ground truth. The
**notes** are usable as criteria evidence regardless, and they are the part worth having.

This is `golden-completeness`'s call, not a capture script's — folding a round into the
golden inside a different item is Lesson 1's failure, which is the very thing this file
is an instance of.

## What this changes

- **Nothing measured moves.** No precision or recall figure depends on this round.
- **`STATE.md`'s unread-rounds list is now accurate** — one file, with a measured count.
- **Phase B of `review-verdict-axes` gains a reference implementation**: the January UI
  already had `length_adjustment` and `spans_multiple_pages` as fields. Re-deriving the
  axes without looking at it would repeat work done in January.
- **`golden-completeness` gains a third input** alongside the 16 unincorporated Kiddushin
  verdicts, and a caveat: this one cannot be folded mechanically.

## Artifact

`results/rulers/january_2026_round_captured.json` — every verdict normalised, with the
mapped vocabulary, cross-page flag, coverage flag, and the structured boundary fields.

```bash
python3 scripts/capture_january_round.py
```

## Bounds

- **CIRCULAR.** Verdicts on our own v4-era proposals. Precision and criteria only, never
  recall (FRAMEWORK §3).
- The verdict-vocabulary mapping (`false_positive` → `incorrect`, `correct` → `correct`)
  is asserted exhaustive; one item has no `feedback_type` and is carried as `None` rather
  than guessed.
- **"Covered by no ruler-read round" is a ref-string comparison.** A cross-page ref like
  `Ketubot 3b-4a` could in principle correspond to a story some other round records under
  `Ketubot 3b_11-13`. Establishing that needs text alignment, which was not done. Read the
  9 as *indicated* uncovered, not measured.
