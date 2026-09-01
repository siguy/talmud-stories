# The reviewer can now say which thing is wrong

**2026-08-31.** Phase B of [`review-verdict-axes`](../../work/done/2026-08-30-review-verdict-axes.md).
Capabilities **3 Classification** (primary), **5 Review**, **4 Boundaries**, **2 Detection**.
No API calls. No measurement moved — this is the instrument, not a reading from it.

## What shipped

`validation/generators/generate_axis_review_ui.py` — a review page whose verdict is
four axes instead of one button:

| axis | values | when |
|---|---|---|
| **Is it a story?** | Yes · Borderline · No | always; the only required question |
| Extent | right / starts wrong / ends wrong / both | on request |
| Confidence | right / too high / too low | on request |
| Grouping | right / should be split / merge with neighbour | on request |

Plus **⚠ Display problem** as its own control, and free-text notes as an optional
extra rather than the only place structure can live.

And, on the Extent axis, **a Hebrew quote box with a stated polarity** — see below. It
was in the item's design and was missing from the first cut of this work; Simon asked
for it by name.

It reads `results/v10/wave4_notrim/` — the honest segment-level output. The reverted
char-offset spans are not shown at all.

## The design decision that mattered

The brief says axes 2–4 appear "only when something is wrong". The obvious reading —
reveal them when the reviewer clicks **No** — is wrong, and would have thrown away the
corrections we most need. **A passage can be a story *and* be mis-bounded**; that is
what `adjust` meant, it is the commonest correction Jeff gives us, and counting it as a
rejection is how a boundary failure became a fake classification problem for months
(Lesson 30).

So the disclosure is **independent of axis 1**. A correct entry is one click on `Yes`.
"It is a story, and it ends in the wrong place" is three, and it is *sayable*, which it
has never been before. That case is now pinned by a test that fails if the extent axis
is ever gated behind a `No`.

## Where the story should actually start or end

The extent axis says *that* the extent is wrong. It does not say **where** it should be,
and without that a boundary complaint is not actionable.

**Every Hebrew quote this project holds was typed into a generic notes box and mined out
afterwards by regex.** `scripts/build_boundary_testset.py` carries a `quote_polarity()`
function whose whole job is guessing, from the surrounding prose, whether the Hebrew he
quoted is text that **belongs in** the story or text that **should be cut**. The result,
in `tests/expert_boundary_targets_v2.json`:

| polarity | targets |
|---|---|
| include | 43 |
| exclude | 11 |
| **mixed** | **11** |
| **unclear** | **5** |

**16 of 70 — 23% — we cannot tell which way the correction runs.** That is capability 4's
ground truth, and it is degraded by the same defect as capability 3's precision: a
structured judgement written into a prose box and inferred back out.

So the quote box is two controls, not one: the text, and **`belongs in the story` /
`should be cut`** as an explicit field. It opens only once the extent is called wrong, so
it costs nothing on the common path — and `right` does not open it, because that is an
answer rather than a complaint.

**He does not have to type Hebrew.** The text is already rendered on the page: highlight
it and press **Use highlighted text**. Verified in the browser — selecting a story's
Hebrew and pressing it captured 203 characters into the box with no transcription step.
Typing pointed Hebrew into a text field is both a chore and a corruption risk, and it is
the kind of friction that turns a 95-story round into 15 verdicts.

Once a round comes back in this shape, `build_boundary_testset.py` can read
`quote_polarity` as a field for those entries instead of running its regex over the note.
The banked 70 stay as they are — the mining was the only way to get them, and it does not
become retroactively better.

## Gates, and how each was met

| gate | result |
|---|---|
| Correct entry stays one click | **met** — verified in the browser: one click on `Yes` produces a complete, exported verdict, with the extra axes still closed |
| `build_ruler.py` regression checks reproduce | **met** — both rulers rebuilt **byte-identical**; Ketubot 143/149 = 96.0% and 0.879 on the 2026-03-17 round still come out |
| Mapping covers all 8 banked rounds | **met** — **605 verdicts, 0 unmapped**, across three vocabularies |
| Test suite | **152 passed, 1 skipped** (was 121) |
| Node display test fails when the defect is reintroduced | **met — demonstrated, not asserted.** All **15** injected defects fail the matching test |
| Browser-verified on the real page | **met** — 96 cards, 0 console errors, paired EN/HE cells, export carries the detector version |

## The mapping table, and what it can and cannot recover

`scripts/map_verdict_vocabularies.py`, run before the UI was written because a new
vocabulary that cannot read the old rounds is worthless.

- **605 verdicts mapped, 0 unmapped.** An unknown token **raises** rather than being
  skipped — a loader that goes quiet past what it does not recognise is how a signed
  25-verdict round stayed invisible for eight months (Lesson 38).
- **14 extent complaints recovered** from structured fields: the canonical round's 4
  `adjust` verdicts, and **10 `length_adjustment: shrink`** values in the January
  2026-01-08 round. That round is the only one that ever recorded an extent objection
  in a field rather than in prose — 40% of its verdicts carry one. The review UI had
  the right shape in January and lost it, which is the argument for this item in one
  sentence.
- **129 verdicts are marked `lossy` and left that way.** A bare `incorrect` pooled four
  capabilities into one button and no table can un-pool it afterwards. Phase B stops
  the pooling **going forward, not backward** (FRAMEWORK §7).
- **`applies_to` is carried on every row.** A `correct` on already-corrected data is not
  a `correct` on base data; merging them lets the canonical round silently undo the
  correction an earlier round asked for (Lesson 3). Only the 2026-03-17 round is
  `corrected`, and a test asserts no other round drifts across that line.

## Structural choices, so this cannot rot the way the last one did

- **The display core is extracted, not copied.** `validation/generators/review_ui_core.py`
  holds the paired-row builder; the wave 4 page and the axis page share it. Proof the
  extraction was safe: the wave 4 pages regenerate **byte-identical** except for the
  moved code itself, and `tests/test_review_ui_symmetry.py` still passes. The new page
  therefore inherits the Hebrew/English guarantee **by construction** — it cannot show
  one language at a different extent unless that test also fails.
- **`mishnah_stories` is displayed, badged and filterable.** CLAUDE.md requires any code
  reading a run for display to decide about that key explicitly. Those passages have
  been shown to nobody, and Jeff is the one person who can settle `jeff:mishnah-scope`.
  Kiddushin 1, Ketubot 4.
- **Every exported verdict carries `detector_version`** (Lesson 36) and
  `schema_version: axes-1`.
- **An unanswered card is absent from the export**, not exported as a null verdict:
  "not asked" and "answered nothing" are different facts.
- **An untouched axis exports `null`, never `right`.** Residue is reported, not guessed.
- **A quote never lands in `notes`,** and a quote without a polarity is refused by a test:
  a quote whose direction is unknown is the ambiguity, not the fix.

## What the ruler does with it

`build_ruler.py` reads both shapes. For an axes-1 verdict the objection is **read**
rather than inferred from free text, and `borderline` is deliberately in neither the
accepted nor the rejected set — recording a contested case and then resolving it either
way would put back the false certainty the status exists to remove (Jeff's request,
2026-07-06 ledger Part 2(d)).

No round on disk speaks this vocabulary yet, so the path is driven by **8 tests against
a synthetic round** rather than left to be exercised for the first time by Jeff, where a
defect costs weeks. One of them is Phase C's acceptance test in miniature: an axes-1
round produces **zero** `unclassified` notes.

## What this does not do

**It does not make review faster.** Four axes with progressive disclosure is
click-neutral on a correct entry and strictly more clicks on a wrong one. This item
buys *fidelity* — it turns Classification from a range into a number once a round comes
back (Phase C) — and it should not be quoted as work against the throughput bottleneck.
Simon confirmed that trade explicitly before it was built.

The historical evidence on throughput points elsewhere, and is recorded here because it
was found while reading `docs/capabilities/5_review.md` for this item: the one round Jeff
completed **100%** of (2026-02-26, 49/49) was the **delta** UI that showed him only what
had changed, and the two rounds that showed him all 95 stories again returned **1** and
**15**. `batch_review.html`'s keyboard shortcuts are named there as "the only throughput
mechanism this project has ever built, and it was never measured or reused". Both are
*indicated, not measured* — n is tiny and his calendar is an obvious confound — and
neither is in this change.

## What was missing from the first cut

The Hebrew quote box. The item's design names it — "*Extent — right / starts wrong /
ends wrong / both, with the existing Hebrew quote box*" — and I read that as describing
something already built. **It never existed.** No generator in `validation/generators/`
has ever had one; the phrase refers to a box that was assumed rather than written, and
every quote we hold came through a general-purpose notes field.

That is worth recording as a pattern and not just a slip: **the brief described an
existing component that did not exist, and the description was confident enough that I
did not check.** The same sentence would have been true of the whole item — "the review
UI records that an entry was rejected" — which was checked, because it was the premise.
An aside inside a design was not.

## Corrections owed to this document

While setting up the browser check I overwrote `.claude/launch.json`, which already
carried the exact static server this needed plus a second one. Restored; nothing was
lost. The rule it breaks is an existing one — look at the target before overwriting it —
so it is recorded here rather than made into a new lesson.
