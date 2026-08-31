---
title: Make the reviewer say which thing is wrong
capability: [classification, review]
tractate: []
blocked_by: []
awaiting: []
finding:
superseded_by:
---

# Make the reviewer say which thing is wrong

**Self-contained.** Read [`FRAMEWORK.md`](../FRAMEWORK.md) first, then this.
**Capabilities: 3 Classification (primary), 5 Review, 4 Boundaries, 2 Detection.**
**Depends on Jeff: no** — Phases A and B need nobody. Phase C needs one review round.
**Cost:** Phase A ~1 hour, no API. Phase B a session, no API. Phase C free.
**Replaces `NEXT/04`,** whose file was deleted in `b394489` when its first job (the
Hebrew/English display asymmetry) was completed; `4de7135` repointed the *name* at this
job without writing a brief, so `STATUS.md` has been listing a ready task with nothing
behind it. Dated slug, not a number: `work/` has already collided twice on `09` and
`10`, and step 8 of the reorg migrates this file to `work/2026-08-30-review-verdict-axes.md`
unchanged.

## The problem in one line

The review UI records **that** Jeff rejected an entry and never **what he was rejecting**.

## Why it matters — measured, `results/rulers/*.json`, 2026-08-30

Sorting every rejection by what he actually objected to:

| round | n | classification | boundary | confidence | merge | **unreadable** |
|---|---|---|---|---|---|---|
| Ketubot 2026-03-17 | 173 | 9 | 7 | 4 | 1 | 0 |
| Ketubot 2026-02-26 (v8 delta) | 43 | 2 | 7 | 1 | 4 | **9** |
| Kiddushin 2026-04-23 | 89 | 7 | 3 | 10 | 0 | **9** |
| Kiddushin 2026-07-06 | 15 | 0 | 5 | 0 | 0 | **6** |

**Most rejections are not about whether the passage is a story.** Pooling them gives an
all-causes error rate reported as Classification precision, so the number can only be
quoted as a range — **Ketubot 87.9–94.8%, Kiddushin 67.4–92.1%** — and **the 24 unreadable
notes are exactly the width of that range**.

What that already cost: months treating Classification as the weakest capability and
Kiddushin as far worse than Ketubot. Separated, both land near 92–95% and most of the gap
evaporates. Worse, the pooled number is the one that would have been "improved" by tuning
the classifier, which would have done nothing — the errors were largely in the boundary
code (Lesson 30, [`detection_classification_ruler`](../docs/findings/2026-08-30-detection-classification-ruler.md)).

## The insight the design rests on

Each objection indicts a **different capability**. The axes are not invented; they are
read off the taxonomy the ruler already computes:

| what he objects to | capability | what he clicks today |
|---|---|---|
| this is not a story | **3 Classification** | `incorrect` |
| the extent is wrong | **4 Boundaries** | `incorrect` **or** `adjust` |
| the confidence level is wrong | **3 Classification** (calibration) | `incorrect` |
| this is one story, not two — or two, not one | **2 Detection** | `incorrect` |

`adjust` already means *"this IS a story and the boundary is wrong."* So part of the
structure exists and is being **discarded by the scorer**, not missing from the UI. That
is why counting `adjust` against precision converted a boundary failure into a fake
classification problem, and why `build_ruler.py` now treats it as **accepted**.

## The design

**Axis 1 — is it a story?** Required, and the only required question.
`Yes` · `No` · **`Borderline`**.

`Borderline` is new and is **Jeff's own request**: contested cases kept and flagged rather
than silently resolved
([ledger Part 2(d)](../validation/feedback/jeff_2026-07-06_feedback_ledger.md)). It is
also the thing [`FRAMEWORK.md` §1.3](../FRAMEWORK.md) says makes this the one capability
where "let database users decide" is a legitimate answer, and it is a column the published
database needs anyway ([capability 6](../docs/capabilities/6_publication.md)).

**Axes 2–4 — shown only when something is wrong.** Progressive disclosure:

- **Extent** — right / starts wrong / ends wrong / both, with the existing Hebrew quote box
- **Confidence** — right / too high / too low
- **Grouping** — right / should be split / should be merged with the neighbour

**The throughput rule, and it is a hard constraint:** a correct entry stays **one click**.
Review is this project's bottleneck — 2–6 weeks per tractate, 3–5 years for Shas, against
~$0.30 of compute — and it holds the only *derived* gate in FRAMEWORK. Any design that
adds clicks to the common case is rejected on that ground alone, whatever it buys.

## Migration — three vocabularies, not two

| rounds | vocabulary | applied to |
|---|---|---|
| v4.1 / v5.1 / v8-delta | `correct` · `incorrect` · `confirm_remove` · `reject_remove` | **base** data |
| canonical 2026-03-17 | `correct` · `incorrect` · `approve` · `adjust` | **already-corrected** data |
| new | per-axis | base data |

**Lesson 3's trap, and it is live here:** a `correct` on *corrected* data is not a
`correct` on *base* data — treating them alike lets the canonical round's "the correction
was right" override the prior round's "incorrect" that triggered the correction, silently
undoing it. That is why the canonical round is applied as a separate post-processing layer
today, and any new vocabulary must ship an explicit mapping table rather than assume.

## Phases

### Phase A — recover what is recoverable (nobody else needed, ~1 hour) — **DONE 2026-08-31**

> **Outcome.** → [`docs/findings/2026-08-31-objection-axis-hand-sort.md`](../docs/findings/2026-08-31-objection-axis-hand-sort.md)
>
> **The population was 34, not 24.** The table above lists four rounds; the ruler scores
> seven. Ketubot 2026-02-05 carries 9 more and Kiddushin 2026-05-26 one more. Correct the
> table before quoting it again.
>
> **27 of 34 sorted; residue 7, every one an empty note.** Kiddushin 2026-04-23 narrows
> 0.674–0.921 → **0.674–0.899**; Ketubot 2026-02-05 narrows 0.667–1.000 → **0.667–0.806**.
> Every `precision_all_causes` unchanged; Ketubot 143/149 = 96.0% and the 0.879 gate both
> reproduce. Artifacts: `results/rulers/objection_axes.json` (hand sort, one row per note,
> each quoting the note and naming the label under review), `scripts/build_ruler.py`
> (reads it, keyword rules as fallback), 4 new tests in `tests/test_build_ruler.py`.
>
> **Three things Phase B must add that the design below does not have:**
> 1. **A fifth option — *the display is wrong*.** `Kiddushin 8b_14-14` is a verdict spent
>    on our renderer. With nowhere to put it, a UI bug scores as a detector error, which
>    is how one sat misfiled for seven weeks (Lesson 25). The Risks section below already
>    predicts this; the axes do not accommodate it.
> 2. **A direction on every rejection.** `incorrect` has meant two opposite things:
>    4 of the 34 are Jeff **overturning a `NOT_A_STORY`** — a false negative, pooled with
>    false positives today. The 2026-02-05 round put 95 of its 125 verdicts on spans we had
>    labelled `NOT_A_STORY`, so this is not an edge case.
> 3. **A verdict may not contradict its own note.** 2 of the 34 affirm and reject at once
>    (`Ketubot 62a_4-4`, `Kiddushin 73a_5-5`). Asking axis 1 first makes that unrecordable.
>
> Not done here, deliberately: the direction defect is **surfaced**
> (`rejections_inverted_direction` per round) and not re-scored. Whether an overturned
> rejection belongs in a precision denominator is a definition question, not a note-reading
> one.

*Original brief:*

Read the **24 `unclassified` notes** by hand and sort them onto the four axes. Bounded
population, no API, no Jeff.

Output: a dated finding plus a re-run ruler, reporting the narrowed range **and what
remains genuinely unresolvable**. Do not guess the residue into a bucket to make the range
look tighter — an indication presented as a measurement is the failure
[`FRAMEWORK.md` §7](../FRAMEWORK.md) names, and it is how the 86/68 numbers survived.

*Why by hand and not with an LLM pass:* the notes are free text about specific passages,
and an LLM classifier adds a second layer of inference on top of the one we are removing.
At n=24 a person is cheaper and auditable. At n=240 the answer would be different — say so
in the finding, so the rule is reusable rather than a preference.

### Phase B — stop widening the range (the UI change)

Implement the axes in `validation/generators/`. Four constraints, each bought by a past
failure:

- **Render both languages from one code path.** True since `b394489`; do not regress it.
- **Highlight the proposed span inside the full text; never trim to it** (Lesson 25).
- **Test the page's actual display JavaScript under Node against a real fixture, and
  confirm the test fails when the bug is reintroduced** — the
  `tests/test_review_ui_symmetry.py` pattern. A guard that cannot fail guards nothing.
- **Open it in a browser on the real artifact before calling it done** — `CLAUDE.md`
  critical rule 1, and the rule Lesson 25 records us breaking.

### Phase C — the point estimate

After the first round on the new UI, `build_ruler.py` should report
`unclassified_notes: 0` and Classification becomes a **number** rather than a range. That
is the acceptance test for the whole item.

## Bundle into the same round — both cost Jeff nothing extra

- **Show him `mishnah_stories`.** The Mishnah filter's withheld passages are displayed to
  nobody, and he is the one person who can settle whether they belong in the database
  ([`mishnah_filter_delta`](../docs/findings/2026-08-30-mishnah-filter-delta.md)).
- **Ask him to keep his appendix a separate file.** One sentence. It cannot be
  reconstructed afterwards, and the window closes the moment we send Gittin / Yevamot /
  Eruvin results (Lesson 29, `09_kiddushin_parse_open_calls.md` item 1b).

## What this cannot do

The 24 banked notes stay however resolvable they turn out to be; Phase A recovers some and
the rest is permanent. No vocabulary change retro-fixes a round already run. The range
narrows going forward, not backward.

## Risks

- **We get very few review rounds.** 2026-05-26 returned **1 verdict on 95 stories**;
  2026-07-06 returned 15. A UI change that confuses Jeff costs a round, and a round is
  weeks. This is why the one-click constraint and the browser check are gates, not
  suggestions.
- **A display bug manufactures expert feedback.** Measured: 2 of the 15 verdicts in the
  2026-07-06 round were spent on our renderer, and one of them sat misfiled as a
  cross-page merge defect for **seven weeks** (Lesson 25).
- **More axes, more places to be wrong.** Keep it to four. Resist adding a free-text-only
  escape hatch, which recreates the original problem inside the new UI.

## Gates

| gate | threshold |
|---|---|
| Correct entry stays one click | verified by clicking it |
| `build_ruler.py` regression checks still reproduce | Ketubot 143/149 = 96.0%; 0.879 on the 2026-03-17 round |
| Mapping table covers all 8 banked rounds | assert every existing verdict maps to exactly one new shape |
| Test suite | ≥ 73 passed / 1 skipped |
| Browser-verified on the real page | before anything goes to Jeff |

## When done

Finding → `docs/findings/` (dated). Update the scoreboard row for **3 Classification** in
`STATUS.md` and the *Untried* section of
[`docs/capabilities/3_classification.md`](../docs/capabilities/3_classification.md) and
[`5_review.md`](../docs/capabilities/5_review.md), which both name this item.
