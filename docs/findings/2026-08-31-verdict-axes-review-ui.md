# A review UI that records which thing is wrong — 2026-08-31

**Phase B of [`work/2026-08-30-review-verdict-axes.md`](../../work/2026-08-30-review-verdict-axes.md).**
No API calls, no Jeff. Phase A read the notes we had; Phase B stops the next round
producing more of them.

**Result — shipped and browser-verified.** A correct entry is **one click**; a verdict
that contradicts its own note is now **unrecordable**; every saved verdict carries the
label the reviewer was looking at and the **direction** of the error. All nine banked
rounds migrate onto the new shape, and the migration surfaced a fourth vocabulary and
**10 boundary corrections from the project's first expert round that no harness has ever
read**.

**And the page produces BLIND boundary targets** — §8. That was not in the brief. It is
the part that makes this hill-climbing rather than only bookkeeping, because capability 4
is the one whose ruler the review round can actually add to.

| gate (from the brief) | result |
|---|---|
| Correct entry stays one click | **verified by clicking it** in the browser: one click writes `is_story: yes` with all three axes at `right` |
| `build_ruler.py` regression checks reproduce | Ketubot **143/149 = 96.0%** (strict 87.9%), 2026-03-17 round **0.879**; Kiddushin 84/90 = 93.3% |
| Mapping covers every banked round | **11 files, 792 records**, each mapping to exactly one shape; asserted by test |
| Test suite | **121 passed, 1 skipped** (gate: ≥73/1) |
| Browser-verified on the real page | yes — see §5 |

Artifacts: [`validation/generators/generate_verdict_axes_review_ui.py`](../../validation/generators/generate_verdict_axes_review_ui.py)
· [`validation/generators/_review_display.py`](../../validation/generators/_review_display.py)
· [`scripts/migrate_verdicts.py`](../../scripts/migrate_verdicts.py)
· `tests/test_verdict_axes_ui.py` · `tests/test_verdict_migration.py`
· `tests/test_review_ui_symmetry.py` (now runs against both pages)

---

## 1. The shape

Axis 1 is the only required question, and the only one that decides Classification:

> **Is this a story?**  `Yes` · `Borderline` · `No`

Axes 2–4 default to `right` and appear behind *"something else is wrong"*. Each indicts
a different capability, which is the entire point — Lesson 30 measured that most
rejections were never about whether the passage is a story:

| axis | options | capability |
|---|---|---|
| Extent | right · starts wrong · ends wrong · both | 4 Boundaries |
| Confidence | right · too high · too low | 3 Classification (calibration) |
| Grouping | right · this is two stories · joins the one next to it | 2 Detection |

`Borderline` is Jeff's own request — contested cases kept and flagged rather than
silently resolved ([ledger Part 2(d)](../../validation/feedback/jeff_2026-07-06_feedback_ledger.md))
— and capability 6 needs the column anyway.

**A fifth control sits outside all of them: *the page is showing this wrong*.** Phase A
found a verdict spent on our renderer with nowhere to put it, so it scored as a detector
error. It is never gated behind axis 1, because a display bug can co-occur with any
verdict.

## 2. Three things the shape makes impossible

**A correct entry cannot cost two clicks.** Axes 2–4 default to `right`, so `Yes` alone
writes a complete and accurate record. Verified by clicking it on the real page, not by
reading the code. `Y` / `B` / `N` advance to the next card; `J` / `K` move without
answering. Review is this project's bottleneck — weeks per tractate against ~$0.30 of
compute — and it holds the only DERIVED gate in FRAMEWORK, so throughput is a gate here
and not a preference. `batch_review.html` built exactly these shortcuts in January 2026
and they were never reused.

**A verdict cannot contradict its own note.** Answering `No` hides *and clears* axes 2–4,
which presuppose the passage is a story. Two of Phase A's 34 notes affirm and reject at
once — `Ketubot 62a_4-4` is *"This is clearly a story. Keep as a 'Yes'"* recorded as a
rejection and counted against precision. Under this shape neither is expressible.

**Direction cannot be lost.** Every saved verdict carries `classification_shown` — the
label the reviewer was actually looking at — and a `direction` derived from it. Phase A
had to recover that by re-indexing five old runs, because `incorrect` has meant both
"you wrongly called this a story" and "you wrongly called this *not* a story", and the
two were pooled into one precision figure.

Each is a test that fails when the behaviour is removed, checked by reintroducing the bug
and watching the guard go red.

## 3. The migration: four vocabularies, not three, and the oldest one already had axes

The brief expected three vocabularies. There are four, and the extra one is the **first
review UI this project ever built**.

`ketubot_review_Jeffrey_Rubenstein_2026-01-08.json` records `feedback_type`
(correct / false_positive), **`length_adjustment`** (shrink), `story_confidence` (75–95),
`story_type` and `spans_multiple_pages`. That is a classification axis, a boundary axis
and a confidence axis, in January 2026. The project then replaced it with a single word
and spent seven months unable to tell a boundary complaint from a classification one.

**10 of its 25 entries carry a `shrink`.** They are boundary corrections from the first
expert round, and no harness has ever read one — the file keys its records under a *list*
rather than a dict, so `build_ruler.py` skips it silently. STATE.md lists it under
*"expert verdicts on disk that no ruler reads"*; this is why.

Two of the other three files in that STATE.md list are not what the label suggests, and
saying so is cheaper than someone else re-discovering it:

- `validations_v4_2026-01-25.json` — its `validations` object is **empty**. The round
  recorded in `94f7844` (30 stories, 15 true / 15 false) has no verdicts on disk.
- `jeff_v4.1_validation.json` — 6 records of `expected` vs `ai_result`. An automated
  self-check, not expert verdicts. Marked `expert: false`.

### What the mapping does, and what it refuses to do

| legacy | condition | migrates to |
|---|---|---|
| `correct` | label shown was a story | `is_story: yes`, all axes `right` |
| `correct` | label shown was `NOT_A_STORY` | **`is_story: no`** — he confirmed the rejection |
| `incorrect` | label shown was `NOT_A_STORY` | **`is_story: yes`**, `direction: under_call` — 8 cases |
| `incorrect` | label shown was a story | whatever the objection names, else **undetermined** |
| `adjust` | (canonical round) | `is_story: yes`, `extent: wrong_unspecified` |
| `confirm_remove` / `reject_remove` | | `is_story: no` / `yes` |
| `length_adjustment: shrink` | (2026-01 round) | `extent: wrong_unspecified` |

Two coarser values exist because the old vocabularies were coarser, and the new UI never
emits either: **`wrong_unspecified`** (this axis is wrong, but the old words could not say
how) and **`None` + `undetermined`** (the question could not be expressed at all).
Filling those in to make coverage look complete is the failure FRAMEWORK §7 names.

**Of 133 rejections across all rounds, 120 now determine whether the passage is a story
and 13 do not.** Eight are empty notes. Four are readable notes outside Phase A's
population (§6). The thirteenth, `Kiddushin 8b_14-14`, names its axis — `display` — and
correctly says nothing about whether the passage is a story, because a complaint about our
renderer is not a judgment about the text.

**`correct` on a rejection is not an accepted story, and a test caught us getting that
wrong.** The first draft mapped the canonical round's `correct` to `is_story: yes`
unconditionally. Five of its verdicts sit on spans we had labelled `NOT_A_STORY`, and
those five would have migrated as approvals nobody gave. With the 2026-02-05 round's 87,
that is **92 invented approvals** the test stopped. The same bug ran the other way too:
before the fix, three canonical-round entries were being counted as *overturned*
rejections. Corrected, the project has **8** of those, not 13 — Phase A saw 4 because its
population was what the ruler's join reaches.

**Layers do not merge** (Lesson 3). The 2026-03-17 round judged *already-corrected* data,
so every record from it carries `layer: 'correction'`. Merging it with base-layer verdicts
lets its "the correction was right" silently overturn the earlier round's "incorrect" that
caused the correction. The keys genuinely overlap, which is exactly the trap; a test
asserts the layers stay apart.

## 4. One display, two pages

The paired English/Hebrew renderer moved to
[`validation/generators/_review_display.py`](../../validation/generators/_review_display.py)
and both pages import it. A second generator with its own copy of that code is the Wave 4
asymmetry waiting to happen again, and `tests/test_review_ui_symmetry.py` now runs its
four invariants against **every** generator in the module's list — plus a new one
asserting that no generator has grown a private copy.

The extraction is provably faithful: the existing symmetry tests passed unchanged against
the refactored Wave 4 page before anything else was built.

**The guards were checked by breaking the code.** Reintroducing the Hebrew-trim bug makes
`test_B_no_story_text_is_hidden_in_either_language` report
`['seg 2: HEBREW truncated']`; removing the axis-clearing makes
`test_B_not_a_story_clears_the_axes_that_presuppose_one` fail with *"an extent complaint
survived 'this is not a story'"*. Both pass again once restored.

## 5. Browser verification

Served from `validation/ui`, driven in the browser, not inspected as source.

- **96 cards, 655 English cells and 655 Hebrew cells** — the symmetry holds in a real
  layout engine, not only under Node.
- Computed styles on a card: Hebrew `direction: rtl` and non-empty, story rows painted
  `rgb(255,251,230)` against context `rgb(251,252,253)`, `text-decoration: none`
  everywhere. That is `CLAUDE.md` critical rule 1 checked against the DOM.
- One real DOM click on `Yes` → `{is_story: yes, extent: right, confidence: right,
  grouping: right}`, card marked answered, extra axes not shown.
- Disclosure → three axes labelled Extent / Confidence / Grouping. Setting *ends wrong*
  reveals the RTL Hebrew quote box and projects to legacy `adjust`.
- Clicking *Not a story* → axes cleared to `right`, quote cleared, the whole block gone
  from the DOM, direction `over_call`, legacy `incorrect`.
- Keyboard `Y` writes a verdict and advances; `B` records `borderline`.
- Save → `verdict_axes_v1`, every record carrying `classification_shown` and `direction`.
- No console errors. Load 87 ms, full render of 96 cards 45 ms, 10,487 DOM nodes.

## 6. What this does not do

**It does not narrow any existing number.** Phase A took the banked rounds as far as
reading can; this changes only what the *next* round can say. Classification stays a
range until a round is run on this page — that is Phase C, and its acceptance test is
now mechanical: `build_ruler.py` reads the axes directly, so a `verdict_axes_v1` round
cannot produce an `unclassified` note. A test pins that, including that the fallback does
not start guessing when the axes are absent.

**Four readable notes are still unsorted, and they are named rather than quietly
absorbed.** The migration reaches verdicts the ruler's join does not, so it sees four
notes with real text that Phase A's population excluded: `Ketubot 49b_9-10`
(*"Ravin sending a letter is just one event"*), `Ketubot 51b_7-9` (*"just a theoretical
discussion"*), `Ketubot 52a_13-14` (*"There are no real events"*) and `Kiddushin 50b_10-10`
(*"This story is in the Mishnah"* — which also bears on `jeff:mishnah-scope`). All four
read as classification objections on sight. Adding them to `objection_axes.json` would
break that file's stated population — *notes the ruler filed unclassified* — so they are
named here for whoever widens it rather than folded in quietly.

**Whether Jeff will use the extra axes is unmeasured.** The design protects throughput
and the display path, and both are tested. Whether a reviewer reaches for *"something
else is wrong"* rather than typing a note is a question only a round answers, and the
free-text box is deliberately still there — supplementary, never the only signal.

## 8. Boundaries: the page produces blind targets, not just corrections

Everything above improves *measurement*. This is the one part that adds to a ruler.

**Boundary truth in this project is a clause.** `scripts/score_boundary_targets.py` asks
*"is the run's boundary at the target clause"* and scores HIT / NEAR / MISS on
`(ref, segment, direction, clause)`. The clause splitter's own docstring says its ranges
are over the original string *"so offsets map directly onto what the review UI renders"* —
the hook was built and never used.

So the page renders each Hebrew clause as a clickable span, from ranges computed **in
Python by the detector's own `_split_into_clauses`** and shipped with the story. Not a
JavaScript reimplementation: a boundary target that means something different to the page
than to the scorer is worse than no target. A test asserts the shipped ranges equal the
splitter's, story by story and segment by segment.

Median 5 clauses per story segment, p90 9. Clicking one is a click.

### The move that makes a review-round boundary blind

A boundary answer is circular only if **our span** anchored it. So the page asks for the
extent **before our span is on screen**: on a deterministic sample (1 in 7, hashed on the
story key so regenerating the page cannot reshuffle it), the card shows the passage with
*no highlight and no verdict buttons*, and asks where the story begins and ends. Only then
does the highlight appear and the ordinary card resume.

**Boundary-blindness and detection-blindness are different properties.** We chose which
passage he saw; we did not choose the boundary he marked. Choosing the passage biases
*which* boundaries get measured — toward passages the detector finds, which is also the
population the shipped database needs boundaries for. It cannot bias the answer *within*
a passage, and that is what the metric reads. This is the same distinction
`results/expert_lists/kiddushin_2005.json` already draws between `blind` and
`counts_for_recall`: circularity matters in the direction that flatters, and this one
cannot flatter.

**Two residual anchors, recorded rather than argued away**, in `blind_basis` on every
target: the one-sentence English summary is on the card (it names the story, not its
edges), and the displayed window is centred on our span — widened to ±4 segments for the
blind pass for exactly this reason, which at clause resolution leaves tens of clauses of
freedom. Our *classification* badge also stays visible; it says the passage is a story,
not where it runs, and hiding it would tighten a claim this design is not making.

### Why this is worth having when the 2005 lists exist

Those lists already yield blind targets — 294 for Ketubot — by aligning his verbatim story
text to Sefaria. Three things a clicked clause adds:

1. **It is stated, not inferred.** Every 2005 target carries an `align_fraction` and
   `anchor_verified: false`; 2 of his 149 Ketubot stories would not align at all. A click
   has nothing to verify.
2. **It covers stories his list does not.** His Ketubot list has 149 entries; our golden
   has 187. Stories we found that he never listed have no blind boundary truth and never
   can — and they are in the database.
3. **It answers the question capability 4 is blocked on, by demonstration.** The end rule —
   *when a ruling is what makes a passage a story, is that ruling part of it?* — has his
   2005 lists saying keep and his review notes saying cut. An abstract question has been
   sitting in his inbox. Twenty clicked end-clauses on passages with a trailing ruling
   settle it as data.

### Two files, never one

`scripts/build_boundary_targets_from_review.py` writes `..._review_blind.json` and
`..._review_corrections.json` separately, because they answer different questions and
pooling them is Lesson 24. The scorer reads both with no changes.

**It did need one fix, and it is the exact error this whole design exists to prevent.**
`score_boundary_targets.py` decided a target's provenance by comparing its *filename*
against one hardcoded string, so the new blind file was reported as corrections — a blind
number labelled circular. Provenance is now read from the target itself
(`target_is_blind`), the 2005 sets still classify as blind (294 / 0, pinned by a test),
and the real sets score identically to before.

### End to end, in the browser

On `Kiddushin 22b_18-18`: two clicks marked the story as running clause 1 → clause 5 of
segment 18, `blind: true`; the card then revealed our span and reported the comparison;
Save produced a `verdict_axes_v1` round; the converter split it into two files; the scorer
read the blind file and returned **2 HIT, 100%**.

That case is worth naming. It is Phase A's note #32, where Jeff wrote *"Nothing should
have been trimmed here. That is, all of 18 is the story."* Marking clause 1 through
clause 5 of segment 18 **is** that sentence, captured as a scoreable target instead of
prose somebody has to read.

### A bug the tests could not have caught

The blind pass never armed itself: `marking` had to be set somewhere and nothing set it,
so the first blind card silently swallowed every click. **The test passed anyway**, because
the probe was arming it by hand. The browser found it in one click. The state is now
*derived* from which marks exist rather than stored, and the probe no longer arms
anything — reintroducing the bug now fails 5 tests. This is what `CLAUDE.md` critical
rule 1 is for, and it is the second time this project has been saved by opening the page.

## 7. Bundled into the page, because both cost him nothing

- **`mishnah_stories` is shown**, badged *withheld: inside a Mishnah*, with the scope
  question stated on the page. Stage 4g moves those passages into a key no harness and no
  UI reads (Lesson 27), so the one person who can settle `jeff:mishnah-scope` has never
  seen them. Ketubot has 4, Kiddushin 1.
- **`--include-rejected`** adds the entries we classified `NOT_A_STORY`, with a banner
  explaining that saying *Yes* to one tells us something no other round can. Off by
  default because it costs reviewer time; it is the only way to measure this capability's
  invisible half, and the four cases we know of all came from one February round whose UI
  happened to show them.

The third bundled item — asking Jeff to keep his appendix a separate file — is a sentence
in an email, not a UI change. It stays in [`comms/JEFF.md`](../../comms/JEFF.md), and the
window closes the moment we send him Gittin, Yevamot or Eruvin results (Lesson 29).
