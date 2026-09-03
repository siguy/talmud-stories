# Every structured field came back empty, and the page says exactly why

**2026-09-02.** The per-axis review UI exists to stop boundary corrections being mined out
of prose — 16 of the 70 banked targets are `mixed` or `unclear` for want of it. On its
**first real round** it returned 25 verdicts with `extent`, `confidence`, `grouping`,
`quote` and `quote_polarity` empty on **all 25**, and five boundary corrections written as
prose, two of them quoting the Hebrew to cut.

`display_problem` was false throughout, so the renderer was fine. This is not a display
bug.

## First: the file came out of that page. Who was driving it is a separate question

**Correction, 2026-09-03.** Simon read this finding and objected: *"Jeff sent me the json
file which contained the results. That html was never meant to hold his responses."* That
is worth settling before anything below is trusted, because the whole diagnosis rests on
him having used the page.

The JSON is **`buildExport()`'s output, exactly.** Its envelope is that function's return
literal key-for-key and in order — `tractate, schema_version, detector_version,
applies_to, date, total_stories, reviewed, reviews` — and every review object carries
`index`, `classification_shown`, `mishnah_withheld`, `quote_start`, `quote_end`, in the
order the function emits them. `date: "2026-09-02"` is `new Date()` at the moment Save was
clicked.

It also **cannot be a blank template we sent him to fill in.** `buildExport()` skips any
card that is not complete (`if (!isComplete(v)) return`), so an unanswered page exports
`reviews: {}` and `reviewed: 0`. A 25-entry skeleton with every field present and null is
not something this code can produce.

So the page produced the file. **What the file cannot tell us is whose hands were on it.**
Two possibilities remain, and they have different consequences:

1. **Jeff used the page.** Then everything below holds: the layout is why the structured
   fields are empty, and the fix is aimed at the right thing.
2. **Jeff answered in prose — by email or on paper — and someone transcribed his answers
   into the page.** Then the empty fields say nothing about how *he* reads the UI. They
   say the transcriber had prose in hand and filled the field that takes prose. The
   layout finding would be about the transcription step, not about him.

**This is Simon's to answer, not the artifact's,** and it is one line. Until it is
answered, read the diagnosis below as **indicated**, not measured.

**The fix does not depend on which it is.** A single-line `<input>` is wrong for
sentence-length notes either way, and revealing the axes when someone reaches for prose
helps a transcriber exactly as much as it helps Jeff — in reading (2) it helps *more*,
because a transcriber holding a boundary correction in prose is precisely the person who
should be shown the boundary boxes. Nothing here is gated, so no path gets worse under
either reading.

## The item posed two readings. Opening the page settled it without asking him

1. he never opened the disclosure, or
2. he opened it and preferred prose.

The work item said not to guess, because the fix differs completely. So the page was
served and inspected — `validation/ui/axis_gittin_unlisted.html`, the exact file he
reviewed. What a fresh card offers, in the DOM:

| control | where it lives | visible without a click? |
|---|---|---|
| Yes / Borderline / No | top level | **yes** |
| ⚠ Display problem | top level | **yes** |
| *"Something else is wrong ▾"* | top level | **yes** (a toggle) |
| Extent, Confidence, Grouping | inside `.more-axes` | **no** — `display: none` |
| the Hebrew quote boxes | inside `.more-axes` | **no** |
| **notes** — *"Anything else, in your own words (optional)"* | **top level, outside the disclosure** | **yes** |

**The only always-visible free-text control invites prose, and every structured control is
behind a discovery step.** He used what was in front of him. Reading (1), with a cause
precise enough to fix.

Two aggravating details from the same inspection:

- The notes control was an `<input>` — **single-line**. Every one of his 25 notes was a
  sentence or more; the longest quotes a full Hebrew clause. He was writing paragraphs
  into a box that showed about eight words at a time.
- Its placeholder, *"anything else"*, is only honest if the reviewer has already seen the
  structured fields. For someone who has not, it does not read as *anything else* — it
  reads as *anything*.

## The fix, and what it deliberately does not do

1. `<input>` → `<textarea rows="2">`.
2. **Typing in the notes box reveals the axes** — once, in place, non-modal.
3. The placeholder now points at the boxes: *"if it is about where the story starts or
   ends, the boxes above capture it better."*

That is the whole change. It **adds a path and removes none**:

- a correct entry is still **one click** — `Yes` and nothing else, still complete, still
  exports; the axes stay shut on that path
- prose is still a complete review; a reviewer who keeps typing has given us a valid
  verdict, exactly as before
- the reveal is **one-shot**: closing it deliberately keeps it closed. A panel that
  reopens itself is worse than one that never opened
- nothing is gated behind a `No`. A passage can be a story *and* be mis-bounded — the
  standing rule, and a test still fails if it regresses

**Not done:** making the disclosure open by default. That is a layout decision about a
page a busy reader has to face 25 times, and there is no evidence it would help — it
trades a discovery problem for a density problem. The targeted reveal answers the observed
behaviour without guessing at the rest.

## Verified in the browser, and pinned

Served locally and driven through the DOM: the notes control is a `textarea` and outside
the disclosure; typing fires the reveal (`more-axes` goes from 0 to 628px and the quote
box becomes reachable); a deliberate close stays closed; a bare `Yes` is still complete
and leaves the axes shut; the export still reads `axes-2`.

*A screenshot of the expanded state is not attached: the page is 800KB and the hidden
preview pane would not paint below the fold at a 5,500px scroll. The assertions above are
DOM reads, which is the stronger evidence anyway — but the limitation is stated rather
than implied.*

The properties are now test `I` in `tests/test_review_ui_axes.py`, which runs the page's
own JavaScript under Node. Per that file's convention it was **confirmed to fail when the
defect is reintroduced**: reverting the textarea alone fails it.

## `axis_gittin_unlisted.html` was NOT regenerated

It is the record of what he actually saw. Regenerating it would silently rewrite the
evidence for this finding and make the round unauditable. The generator's own outputs
(`axis_ketubot_review.html`, `axis_kiddushin_review.html`) are rebuilt; the Gittin page is
a one-off artifact and stays as it was.

## The part that generalises

**The round succeeded and the instrument failed, and those are different facts.** He
answered all 25, gave us three stories we did not have, and wrote five boundary
corrections. Nothing was lost that he chose to tell us — it just arrived in a shape that
needs mining.

The lesson is about where to look. It was tempting to write this up as a question about
the reviewer's habits and put it in the next email. The answer was in the page's own
layout, available for the cost of serving a file, and **cheaper than a question that would
have spent one of his scarce replies.**

**And the correction at the top of this file is the same lesson turned around.** Reading
the layout told us how the page behaves. It could not tell us who was operating it, and
the finding was written as though it had — the one question that needed a human was the
one assumed away. Provenance of a verdict is not recoverable from its shape: `axes-2`
proves which code wrote the file, never who filled it in. If reviews are ever transcribed
rather than entered by the reviewer, the export needs a field saying so, and no amount of
looking at the artifact substitutes for that.
