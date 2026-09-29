# An old `correct` means "the detector was right" — read that way, Classification precision is ~0.92–0.95, not a range from 0.47

**2026-09-29.** Status: **measured** (re-reading verdicts on disk; no model calls).
Item: [`verdicts-read-against-the-call-shown`](../../work/done/2026-09-28-verdicts-read-against-the-call-shown.md).
Found by: [`consensus-phase1`](2026-09-28-consensus-phase1.md) §8.

## The defect

Before the axes UI (2026-09-02), every review round asked Jeff *is the detector's call
correct?* — not *is this a story?*. So a `correct` on a span the detector showed as
`NOT_A_STORY` is his **no**, and an `incorrect` with a boundary complaint on a story is his
**yes** (it is a story, drawn wrong). `scripts/build_ruler.py` and
`scripts/map_verdict_vocabularies.py` read every `correct` as "accepted as a story" and
every `incorrect` as "rejected", whatever he was shown. The per-round "precision" they
published was therefore *agreement with the call shown*, counted over every proposal —
including the detector's own `NOT_A_STORY` calls.

Consensus phase 1 had already read them correctly (its `shown_*` functions recover the
classification from the page he actually reviewed). That reading now lives in
**`scripts/verdict_reading.py`**, and all three scripts use it.

## What changed

- **`build_ruler.py`**: each verdict carries `read_as` (yes / no / borderline /
  out_of_scope / unknown), `read_why` and `shown`. Each round gains **`story_precision`** —
  of the proposals the current detector calls a story, the share he says *is* one — beside
  the old fields, which are **unchanged**, so the published 86% and 68% stay reproducible
  and are now labelled for what they are.
- **Simon's rounds are no longer scored as Jeff's.** The 2026-09-16 pre-screen had been
  counted as a review round in all three rulers since it landed; it is now in
  `excluded_rounds`, counted and named (Lesson 38).
- **`map_verdict_vocabularies.py`**: `is_story` read against the call shown;
  `is_story_by_token` keeps the old reading row by row. Re-read: **109 yes→no, 66 no→yes,
  31 yes→borderline, 6 no→borderline**; rows marked lossy fall **129 → 57**.
- **The committed rulers were stale** (found 2026-09-28): regenerated. Apart from the new
  fields and the exclusion, the only moves are the newer rounds appearing (2026-09-16 /
  2026-09-23) and Kiddushin 2026-04-23 accepted 60 → 59 (the 39b re-bound of 2026-09-25).

## The numbers

| tractate | round | old: all causes (lower bound) | old: classification only (upper) | **story precision** | his answers on story calls |
|---|---|---|---|---|---|
| Ketubot | canonical 2026-03-17 (*corrected data*) | 0.879 | 0.948 | **0.920** | 150 yes · 13 no |
| Ketubot | v5.1 2026-02-05 | 0.667 | 1.0 | **0.714** | 10 yes · 4 no · 10 borderline · 2 unknown |
| Ketubot | v5.1 2026-02-20 | 0.961 | 0.99 | **0.952** | 79 yes · 4 no · 16 borderline |
| Ketubot | v8 delta 2026-02-26 | 0.465 | 0.953 | **0.939** | 31 yes · 2 no · 3 borderline · 7 unknown |
| Kiddushin | 2026-04-23 (the "68%") | 0.670 | 0.920 | **0.928** | 77 yes · 6 no |
| Kiddushin | wave 4 2026-07-06 (the "11 of 15 incorrect") | 0.267 | 1.0 | **1.0** | 15 yes |
| Gittin | axes 2026-09-02 (**unlisted extras only**) | 0.143 | 0.143 | **0.143** | 3 yes · 18 no · 4 borderline |

**How to read it.**
- The "precision range" the capability doc has carried since 2026-08-30 was the gap
  between the two old bounds. **Read against what he was shown, the answer falls inside
  that range and near its top** for every story-by-story round: ~0.92–0.95.
- **Wave 4's "11 of 15 incorrect" was never a classification failure** — all 15 are
  stories; the complaints were about extent. Lesson 30 said this in words; this is it in
  the number.
- **Gittin's 0.143 is not comparable**: that round showed him only the proposals his 2005
  list does *not* contain, so it measures discovery, not precision.
- **Not pooled, and not today's detector.** Each round judged a different detector version
  (Lesson 36), and the join to today's proposals is by overlap.

## What this did not check

The goldens (`results/canonical/`) were built by other scripts (`build_canonical.py` and
the per-round apply scripts), which carry the classification alongside each verdict. Whether
any of them read a `correct` on a `NOT_A_STORY` call as a story was **not checked here**,
and is worth one query before anyone builds a golden from an old round again.
`GOLDEN_COUNTS` is unchanged by this item.
