# L-041 — A similarity score that can only grow cannot reject a wrong answer

**Date:** 2026-09-03
**Found in:** `scripts/measure_recall_vs_expert_list.locate` — the aligner behind every
recall figure the project has ever published
→ [`2026-09-03-exact-anchor-matcher.md`](../docs/findings/2026-09-03-exact-anchor-matcher.md),
[`2026-09-03-exact-matcher-cutover.md`](../docs/findings/2026-09-03-exact-matcher-cutover.md)

## The rule

**If a matcher's score is monotone in the amount of text it looks at, it has no way to say
"too much". Before trusting a fuzzy match, ask what makes the score go DOWN — and if the
answer is "nothing", the match is not evidence of location, only of presence.**

The fix is a test the wrong answer can fail. Ours was position: a phrase *k* words into
the story belongs *k* words into the passage. Any such test will do; having none will not.

## What happened

`locate` found an expert's story by comparing **sets of Hebrew 4-grams per segment**, then
growing a window while coverage improved:

```python
for end in range(start, min(start + max_window, len(units))):
    acc |= units[end][2]                     # accumulate — never shrinks
    cov = len(story_grams & acc) / len(story_grams)
    if cov > best[0]:
        best = (cov, start, end)
```

`acc` is a union. Adding a segment can only add grams, so coverage can only rise or stay
flat. A neighbouring passage sharing `אמר ליה` extended the window and **improved** the
score. Windows ran to 14 segments, and the recall figure credited a proposal anywhere
inside one.

The consequences were everywhere and none of them looked like a bug:

- The **loose/strict double-quote** we had been careful to always give in pairs was not a
  real ambiguity about what we had found. It was this window. Loose collapses onto strict
  on all four tractates once the match is exact; three of the four strict figures are
  unchanged **to the story**.
- **35 proposals** read as corroborated by Jeff's list, 11 of them top-confidence, and a
  whole work item existed to review them. The true number is **one**.
- **A Gittin golden entry** (34a:9) was labelled `YES` from the blind list because the
  window covering Jeff's `אי לא נסיבנא` story at 34a:11 also covered its formulaic
  near-twin one segment away. Nobody had ever labelled it.
- Two Ketubot stories were filed as **Detection** misses that are **Triage** misses: their
  windows reached an examined neighbouring daf while their own daf was skipped.

## Why it survived so long

The output was never obviously wrong. Every window contained the right story — the score
was 1.0 — it just contained more. A too-wide match fails in the direction of **generosity**,
so every number it touches reads as good news, and good news does not get audited. It also
had a plausible justification in its own docstring: Jeff's text is abbreviated (`א"ל` vs
`אמר ליה`), so character n-grams were chosen over words. That was true, and it was tested
against nothing — **97% of his phrases turn out to match Sefaria exactly**, and every one
of the 452 stories contains a 6-word phrase unique in its own tractate.

## What to do instead

- **Name what makes the score fall.** Coverage, overlap, containment — check the direction
  of the metric before believing a maximum of it. A monotone measure needs an external
  stopping rule, and "a fixed window cap" is not one.
- **Test the workaround's premise.** The abbreviation problem was assumed, not measured.
  One counting script would have retired the whole design.
- **Look for a free scorecard.** The expert's own daf labels were sitting in the same file
  and nothing read them: agreement went 51→85, 90→104, 72→97 across three tractates. A
  signal the matcher does not consume is worth more than any internal confidence.
