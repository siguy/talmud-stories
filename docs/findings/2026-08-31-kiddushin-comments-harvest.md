# Jeff's 10 anchored Kiddushin remarks, harvested

**Date:** 2026-08-31
**Capability:** 3 Classification, 4 Boundaries
**Dataset:** `results/expert_lists/kiddushin_2005.json` `comments` stream — **CIRCULAR**
**Status:** measured (the sort, the join) + indicated (the axis assignments)
**Item:** [`work/2026-08-30-kiddushin-comments-harvest.md`](../../work/done/2026-08-30-kiddushin-comments-harvest.md)

---

## What was harvested

10 comments → **11 sentence-level remarks**, because `c_02` carries two (a boundary
instruction plus an attribution note), exactly as the item warned.

| axis | n | remarks |
|---|---|---|
| **borderline** | 3 | c_00, c_07, c_08 |
| **classification** | 3 | c_03, c_04, c_05 |
| **boundary** | 2 | c_01 (polarity **CUT**), c_02#a (polarity **ADD**) |
| open_question | 1 | c_note_28 — *"Check parallel"*, addressed to us, still owed an answer |
| attribution | 1 | c_02#b — *"These seem to be the words of Rav Hisda"* |
| provenance | 1 | c_06 — the `הוספתי--י.ר.` marker, already reflected in `blind=false` |

Nothing dropped; all 11 sorted and used or explicitly parked. Artifact:
`results/expert_lists/kiddushin_comments_harvested.json`, rebuilt by
`python3 scripts/harvest_kiddushin_comments.py`.

## The check that changed the answer

The first pass joined each remark to our output through the recall artifact's
`in_detector` flag. That flag uses the **loose window** test, which credits a proposal
anywhere near the story. Tested strictly — does one of our spans actually *contain* the
text he commented on — it credits a **different passage on the same daf** in 2 of the 6
cases:

| remark | ref | loose says | strictly, our spans covering his text |
|---|---|---|---|
| c_03 | Kiddushin 30a | found | **none** |
| c_08 | Kiddushin 58a | found | **none** |

This is the over-crediting `STATUS.md` warns about, caught in the wild on named passages.
It also killed a much more dramatic claim: read loosely, c_03/c_04/c_05 looked like Jeff's
2005 margin notes flatly contradicting his own 2026 review verdicts on the same passages
("This is not a story" vs "Yes. This is a story"). They are **different passages on the
same daf**. There is no contradiction, and no evidence here about the stability of expert
judgement over twenty years.

## What the remarks say about our output

**Three real disagreements** — he doubts it, and a span of ours actually covers it and
calls it a story:

| remark | ref | our call | his words |
|---|---|---|---|
| c_04 | Kiddushin 31b | `YES` | *"not really a story. It is a halakhic question and answer. The question related what happened but it does not really amount to a story"* |
| c_05 | Kiddushin 39b | `HIGH_CONFIDENCE` | *"Not really a story. This 'response' (teirutz) should be seen as part of the dialectical argumentation"* |
| c_07 | Kiddushin 58a | `LOW_CONFIDENCE` | *"Not sure this is a story. No real narrative."* |

The first two are the ones that matter: **`YES` and `HIGH_CONFIDENCE` on passages the
expert calls non-stories**, and both fail the same way — a halakhic exchange that narrates
an event is still not a story. That is a precision signal from a source that is
independent of every review round, because he wrote it in 2005.

c_07 is the opposite and is quietly reassuring: he hedges, and we hedge too
(`LOW_CONFIDENCE`). Calibration agreeing with the expert is the behaviour
`LOW_CONFIDENCE` exists for.

**Three agreements by silence** — he doubts it and we propose nothing covering it: c_00
(10b), c_03 (30a), c_08 (58a).

**One of those retires an open question.** `comms/JEFF.md` carries Kiddushin 58a as a case
we proposed and then classified `NOT_A_STORY`, listed as needing his ruling. His own 2005
note on that passage already says *"Not sure this is a story. Very minimal."* We do not
need to ask him about 58a — **he has already answered**, and he agrees with us. Kiddushin
44a, the other case, has no comment and remains genuinely open.

## What the classification remarks add to the criteria

Three of his own sentences, verbatim, on named passages — the material Wave 6 needs and
the criteria doc lacks. Two categories appear that our criteria do not currently name:

- **report / tradition** (c_03) — a category distinct from *story*, which we do not model
- **teirutz / dialectical argumentation** (c_05) — a response inside an argument is not a
  narrative event, however much it narrates

**Not paraphrased into a rule here**, per the item's guardrail and the failure it records:
a gloss added to his words once produced a contradiction that turned out to be ours. They
are stored verbatim with our reading in a separate field.

## Boundary targets

2 usable, both with polarity recorded — `c_01` is text to **CUT**, `c_02#a` is text to
**ADD** with the Hebrew given. They are **not** yet folded into
`tests/expert_boundary_targets_v2.json`; the harvest artifact carries them in a form the
builder can consume. Getting polarity backwards silently anchors a target one clause off,
which is why it is stored explicitly rather than inferred at build time.

## Not done, and why

- **The 16 unincorporated Kiddushin verdicts (item 7)** are not folded in. That is
  `golden-completeness`'s job, it is scoped there, and doing it inside this item would
  bury a golden-dataset change inside a comments harvest. The item remains open and the
  count is confirmed at 16.
- **The boundary targets are not yet in the test set.** Adding them changes a scored
  ruler, which wants its own before/after and a same-code repeat (Lesson 22).
- **`c_note_28`'s question is unanswered** — *"example hada ve'od that looks Amoraic.
  Check parallel"* on Kiddushin 33b. It is a question to us, not a verdict.
- **Loose end 6a — the `מו ע"ב` (46b) label with no story beside it** — not resolved.
  It is not in the comments stream; it is a row in the table, and it needs either a look
  at 46b or a question to him.

## Bounds

- **CIRCULAR.** These are comments on his own list joined to our output. Usable for
  precision, criteria and boundaries; never for recall (FRAMEWORK §3).
- The **axis assignments and polarities are ours**, recorded as explicit tables in the
  script so they are auditable. His words are verbatim.
- The strict join is only as good as the recall artifact's `located` segments; where
  those are wrong the coverage test is wrong with them.
