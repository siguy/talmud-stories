# NEXT 08 — Harvest the review comments embedded in the Kiddushin list

**Needs `NEXT/05` first.** Read `STATUS.md` and `FRAMEWORK.md`.
**Capabilities: 3 Classification, 4 Boundaries.** **No API calls.**

## What is in there

Jeff's Kiddushin document carries at least **9 English review notes** mixed in with the
stories. They are not noise — they are expert judgments we have never used:

- *"I think these words should be omitted. It is the Talmud's comment on the alternative
  story"* — a boundary correction
- *"A few more words should be included in the story: סֵירוּס דְּמַאי? …"* — a boundary
  correction with the Hebrew given
- *"This is not really a story. It is a halakhic question and answer. The question
  related what happened but it does not really amount to a story"* — a classification
  judgment, and a sharp one
- *"Not really a story. This 'response' (teirutz) should be seen as part of the
  dialectical argumentation"* — classification
- *"This is a very minimal story, if at all. Just a dialogue"* — a borderline case

## Why it matters

The classification notes are **exactly the material Wave 6 needs**: Jeff drawing the
line between a story and a halakhic exchange, in his own words, on real passages. Our
criteria doc rests on one paragraph of his; this is several more, each attached to a
specific text.

The boundary notes extend the corrections set, which is the smaller of the two Kiddushin
rulers.

## Method

1. Take the `comments` stream from `NEXT/05`, each still attached to the story it
   follows — **the attachment is the whole value**; a comment without its passage is
   unusable.
2. Sort into: boundary correction / classification judgment / borderline flag / other.
3. Boundary ones → extend `tests/expert_boundary_targets_v2.json` via
   `scripts/build_boundary_testset.py`. Mind `quote_polarity` — whether the quoted
   Hebrew is text to keep or text to cut. Getting this backwards silently anchors a
   target one clause off, which went unnoticed for months.
4. Classification ones → append to `docs/golden/workflow/jeff_story_definition_criteria.md`
   as cases, quoting him verbatim. **Do not paraphrase into a rule.** A gloss added to
   his words once produced a contradiction that turned out to be ours, not his.
5. Append everything to the feedback ledger first (Lesson 17).

## How you know it worked

Every comment either sorted and used, or explicitly listed as unusable with a reason.
Nothing silently dropped.

## Guardrails

- Quote Jeff verbatim; mark any interpretation as ours.
- These are CIRCULAR — they are comments on our output. Fine for precision and criteria,
  never for recall (FRAMEWORK §3).
