# The unreadable rejection notes, read — and the version they were about

**Date:** 2026-08-31
**Capability:** 3 Classification (primary), 5 Review, 4 Boundaries
**Dataset:** all 8 banked review rounds, CIRCULAR
**Status:** measured (population, axes) + indicated (the axis assignments are judgement)
**CORRECTED same day** — see *Correction* at the end. The "live regression" this finding
originally reported was an artifact of exact-span matching and is withdrawn.
**Item:** Phase A of [`work/2026-08-30-review-verdict-axes.md`](../../work/done/2026-08-30-review-verdict-axes.md)

---

## Two corrections to the item's own premise

**1. The population is 34, not 24.** The item's table covers four review rounds. Two
more carry unreadable rejections — the **v5.1 round (9)** and the **2026-05-26 round
(1)**. Deduped by `(round, key)`, the true population is 34. The 24 figure counted only
the rounds the table listed. *(The raw per-verdict count is 41; 7 of those are the same
verdict attached to more than one ruler entry.)*

**2. A note cannot be read against the ruler's `detector_classification` column.**
That column is **today's** run. The reviewer was looking at whatever the *reviewed
version* produced, and the two differ on **12 of the 34**. Read against today's column,
several notes look like a contradiction — Jeff clicking `incorrect` while writing
"This is definitely a story" about an entry we currently classify `YES`. Read against
the version he actually saw, the same note is an ordinary, correct objection:

| key | version | what he saw | his note | today |
|---|---|---|---|---|
| Ketubot 10b_1-1 | v5.1 | `NOT_A_STORY` | "This is definitely a story" | `YES` |
| Ketubot 40b_11-11 | v5.1 | `HIGH_CONFIDENCE` | "not really an event that makes for a story" | `NOT_A_STORY` |
| Ketubot 56a_2-2 | v5.1 | `HIGH_CONFIDENCE` | "it is just a debate" | `NOT_A_STORY` |

This mattered enough to invert the sort: an early pass over these notes classified the
first row as *"Jeff agreeing with us, miscoded as a rejection"*. It is the opposite — a
false negative he caught and we have since fixed.

## The resolution

All 34 assigned. **7 are permanently unresolvable and every one is an empty note from
a single round** (`v8_delta`, 2026-02-26) — that round contributed no readable rejection
text at all beyond two notes.

| axis | n | capability it indicts |
|---|---|---|
| **classification** | 12 | 3 |
| **boundary** | 8 | 4 |
| **unresolvable** | 7 | — (empty notes) |
| **confidence** | 4 | 3 (calibration) |
| **merge** | 2 | 2 |
| **display** | 1 | none — a renderer defect |

Per round:

| round | classification | boundary | confidence | merge | display | unresolvable |
|---|---|---|---|---|---|---|
| v5.1 2026-02-05 | 6 | 2 | — | 1 | — | — |
| v8_delta 2026-02-26 | 1 | — | — | 1 | — | **7** |
| Kiddushin 2026-04-23 | 5 | — | 4 | — | — | — |
| Kiddushin 2026-05-26 | — | 1 | — | — | — | — |
| Kiddushin 2026-07-06 | — | 5 | — | — | 1 | — |

The item predicted most rejections would turn out not to be about whether the passage
is a story. Among the *unreadable* subset that holds but less strongly than for the
readable ones: 12 of 34 are genuine Classification objections. The rounds differ sharply
in character — 2026-07-06 is **almost entirely boundary complaints**, 2026-04-23 splits
between classification and confidence, and v5.1 is mostly classification.

## The result that changes what we should measure

Of the 12 notes stating a plain story / not-a-story position, the detector **disagreed
with 8 at review time**. Today it **agrees with 7 of those 8**:

```
Kiddushin 72b_4-4   says_not_story   HIGH_CONFIDENCE  -> NOT_A_STORY      FIXED
Ketubot   10b_1-1   says_story       NOT_A_STORY      -> YES              FIXED
Ketubot   10b_3-3   says_story       NOT_A_STORY      -> HIGH_CONFIDENCE  FIXED
Ketubot   10b_6-6   says_story       NOT_A_STORY      -> HIGH_CONFIDENCE  FIXED
Ketubot   40b_11-11 says_not_story   HIGH_CONFIDENCE  -> NOT_A_STORY      FIXED
Ketubot   42b_8-8   says_not_story   YES              -> NOT_A_STORY      FIXED
Ketubot   56a_2-2   says_not_story   HIGH_CONFIDENCE  -> NOT_A_STORY      FIXED
Kiddushin 52a_4-6   says_not_story   YES              -> HIGH_CONFIDENCE  STILL DISAGREES
```

**These are historical defects, already corrected, still sitting in the pool that gets
quoted as Classification precision.** The ruler's per-round precision figures are
properties of *the version reviewed in that round* — v5.1, v8, v7, v10 — and quoting
them as the current capability's number charges today's detector for calls it no longer
makes. That is Lesson 30's shape displaced along a third dimension: 30 pooled across
*reasons for rejection*, Lesson 35 pooled across *pipeline stages*, and this pools
across **detector versions**.

`agrees()` deliberately does not treat "no proposal today" as neutral. For a
*not-a-story* note it is agreement by omission; for a *this-is-a-story* note it is the
passage vanishing, which is a Detection loss, not a Classification fix. Collapsing them
would let a disappeared story read as a resolved complaint.

### The one that still disagrees

**Kiddushin 52a_4-6** — v7 said `YES`; Jeff wrote *"This is just a reference to the
Mishnah's story. The rest is just legal comments about the Mishnah"*; today we say
`HIGH_CONFIDENCE`. A standing false positive, and the only note in the set where the
detector has not come round. It is also a **Mishnah-scope** case, so it may be a symptom
of `jeff:mishnah-scope` rather than a classification defect on its own.

## Bounds on the resolution

- **The axis and polarity assignments are judgement, not computation.** They are stored
  as explicit tables in `scripts/resolve_unclassified_notes.py` so they are auditable
  and re-runnable — recorded that way to be arguable, not to look measured.
- **The 7 empty notes stay unresolvable.** They are not guessed into a bucket to narrow
  the range; per FRAMEWORK §7 an indication presented as a measurement is exactly the
  failure that let the 86/68 figures survive. The residue is reported as residue.
- **This narrows the range going forward only.** No vocabulary change retro-fixes a
  round already run, and 7 notes are gone for good.
- **Span matching is by overlap, not exact key** (see *Correction*). That is correct for
  the question asked — *does the run still assert a story on this passage* — but it will
  credit a proposal whose extent is badly wrong. It answers a Classification question and
  says nothing about Boundaries.

## Artifact

`results/rulers/unclassified_notes_resolved.json` — per note: round, version reviewed,
what that version classified, what today's run classifies, hand-assigned axis, stated
polarity, and whether the detector agreed then and now.

```bash
python3 scripts/resolve_unclassified_notes.py
```

## What Phase B should carry that the item does not yet say

The item's four axes are right. Two additions fall out of this pass:

1. **Record the detector version alongside every verdict.** Every figure derived from
   the banked rounds is version-ambiguous today, and the fix is one field. Without it,
   Phase C's point estimate inherits the same defect in a new vocabulary.
2. **`display` needs to be a first-class outcome, not a note.** One of these 34 is a
   renderer defect, and the 2026-07-06 round already spent 2 of its 15 verdicts on our
   own rendering (Lesson 25). A reviewer who can say *"the text is wrong, not the
   judgement"* in one click stops those from being spent as content verdicts — and
   review verdicts are the scarcest resource this project has.


---

## Correction (same day)

**The "live regression" at Ketubot 10b_3-3 is withdrawn. It was an artifact of this
script's own matching, not a defect in the detector.**

`load_classifications()` keyed spans by the exact `(ref, start, end)` tuple, and the
lookup used that key directly. A verdict key names the span **the reviewed version**
proposed; when a later version proposes the same passage with a different extent, the
exact key misses and the passage reads as *not proposed at all*. Ketubot 10b_3-3 is
exactly that: the current run proposes **10b segments 3–5 at `HIGH_CONFIDENCE`**, and the
golden carries 10b_3-3 as `YES`. Nothing is missing. It is a boundary change on a story
that was **fixed**, not a story that vanished.

Matching now uses **overlap**, preferring an exact hit and preferring a story call over a
`NOT_A_STORY` sibling. Two rows change:

| key | was reported | actually |
|---|---|---|
| Ketubot 10b_3-3 | `-> (not proposed)` **WORSE** | `-> HIGH_CONFIDENCE` **FIXED** |
| Kiddushin 52a_4-6 | `-> (not proposed)` FIXED by omission | `-> HIGH_CONFIDENCE` **STILL DISAGREES** |

The headline count is unchanged at **7 of 8 fixed** — but the composition is different,
and both errors pointed the same way: **exact-span matching reports a re-bounded story as
a deleted one.** That is Lesson 27's family (an invisible deletion reading as a model
failure), reached through a join rather than through a schema.

Neither error touches the axis sort, the population of 34, or the version-pooling result
that Lesson 36 rests on — those never used the span join.
