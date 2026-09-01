# PLAN — review-verdict-axes Phase B: the per-axis review UI

**Status: proposed, not started.** Written 2026-08-31, after Phase A closed.
The item is [`work/2026-08-30-review-verdict-axes.md`](../../work/2026-08-30-review-verdict-axes.md);
this document is the implementation plan for its Phase B and is superseded by
whatever it produces.

## Why this and not something else

Every cheap measurement on the board has now been taken. What remains in Triage
and Detection is either priced-and-declined (`triage-recall-price`: 33–124 Stage 2
calls per recovered story, and the review cost of the extra false proposals is
still unpriced) or blocked on Jeff. Review throughput has been the named
bottleneck since 2026-07-06 — 2–6 weeks of one scholar's calendar against ~$0.30
of compute — and no work has ever been aimed at it. Phase B is the only open item
that is.

## What Phase B changes

The review UI records **that** an entry was rejected and never **what was being
rejected**. Four capabilities are pooled into one `incorrect` button, which is
why Classification can only be quoted as a range (Ketubot 87.9–94.8%, Kiddushin
67.4–92.1%) and why tuning the classifier would have fixed nothing — most of
those errors were in the boundary code (Lesson 30).

Axes, per the item's design:

| axis | values | shown |
|---|---|---|
| **Is it a story?** | Yes · No · **Borderline** | always — the only required question |
| **Extent** | right / starts wrong / ends wrong / both | only when something is wrong |
| **Confidence** | right / too high / too low | only when something is wrong |
| **Grouping** | right / split / merge with neighbour | only when something is wrong |

`Borderline` is Jeff's own request (2026-07-06 ledger, Part 2(d)) and is a column
the published database needs anyway (capability 6).

**Two requirements Phase A added**, both from what it found rather than from the
original design:

- **Record the detector version with every verdict.** One field. A round's
  precision is a property of the version reviewed — of 8 notes where the detector
  disagreed with a plainly-stated position at review time, today it agrees with 7
  (Lesson 36). Without the field, Phase C's point estimate inherits the same
  ambiguity in a new vocabulary.
- **Make `display` a first-class outcome.** 1 of the 34 resolved notes, plus 2 of
  the 15 verdicts in the 2026-07-06 round, were spent on our renderer rather than
  on the detector (Lesson 25). A reviewer needs somewhere to say "your page is
  broken" that does not land in the precision figure.

## The hard constraint

**A correct entry stays one click.** Review is the bottleneck; any design that
adds clicks to the common case is rejected on that ground alone, whatever it
buys. Progressive disclosure is what makes the four axes affordable: axes 2–4
do not exist on screen until axis 1 says something is wrong.

## Steps

1. **Pick one generator and make it the shared one.** `validation/generators/`
   holds six generators, ~3,900 lines, largely duplicated. Phase B builds the
   axis component **once** and the target is `generate_wave4_review_ui.py`,
   because that is the file `tests/test_review_ui_symmetry.py` already executes
   under Node. Repointing it at `results/v10/wave4_notrim/` is a precondition —
   it still reads the reverted char-offset span data, deliberately, and STATUS
   says to repoint it before showing Jeff anything new.
2. **Write the mapping table before the UI.** Three vocabularies exist
   (v4.1/v5.1/v8-delta, canonical 2026-03-17, new). Lesson 3's trap is live: a
   `correct` on *corrected* data is not a `correct` on *base* data. Assert every
   existing verdict in all 8 banked rounds maps to exactly one new shape.
3. **Build the axes** in the generator's display JavaScript, with the existing
   Hebrew quote box carried into the Extent axis.
4. **Test the actual JavaScript under Node against a real fixture**, in the
   `test_review_ui_symmetry.py` pattern, and **confirm each test fails when the
   defect is reintroduced**. A guard that cannot fail guards nothing.
5. **Teach `build_ruler.py` the new shape** without breaking its regression
   checks (Ketubot 143/149 = 96.0%; 0.879 on the 2026-03-17 round).
6. **Open it in a browser on the real artifact** before calling it done —
   CLAUDE.md critical rule 1, and the rule Lesson 25 records us breaking.

## Not in Phase B

Phase C — the point estimate — needs a review round on the new UI and is free
when that round returns. The two bundle-in asks (show Jeff `mishnah_stories`;
ask him to keep his appendix a separate file) belong to that round, not to this
work.

## Gates

| gate | threshold |
|---|---|
| Correct entry stays one click | verified by clicking it |
| `build_ruler.py` regression checks reproduce | Ketubot 143/149 = 96.0%; 0.879 on 2026-03-17 |
| Mapping table covers all 8 banked rounds | every existing verdict maps to exactly one new shape |
| Test suite | ≥ 121 passed / 1 skipped (main as of `b3aca27`) |
| Node display test fails when the defect is reintroduced | demonstrated, not asserted |
| Browser-verified on the real page | before anything goes to Jeff |

## Risks

- **A UI change that confuses Jeff costs a round, and a round is weeks.** The
  2026-05-26 round returned 1 verdict on 95 stories; 2026-07-06 returned 15.
  That is why the one-click constraint and the browser check are gates.
- **More axes, more places to be wrong.** Four, and no free-text-only escape
  hatch — that recreates the original problem inside the new UI.
