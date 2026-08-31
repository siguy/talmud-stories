---
title: Harvest Jeff's 10 anchored Kiddushin remarks
capability: [classification, boundaries]
tractate: [kiddushin]
blocked_by: []
awaiting: []
writes: [results/canonical/kiddushin_canonical.json, results/rulers/, tests/expert_boundary_targets_v2.json, scripts/build_boundary_testset.py, tests/test_bookkeeping.py]
finding:
superseded_by:
---

# Harvest Jeff's 10 anchored Kiddushin remarks

**`NEXT/05` is DONE.** The comments are the `comments` stream in
[`results/expert_lists/kiddushin_2005.json`](../results/expert_lists/kiddushin_2005.json),
each carrying its `anchor_cp` and `attached_story_id`. Read `STATUS.md`, `FRAMEWORK.md`
and [the finding](../docs/findings/2026-08-30-kiddushin-list-parse.md) §5–6.
**Capabilities: 3 Classification, 4 Boundaries.** **No API calls.**

## What is in there

**10 expert remarks**, not 9: nine Word comments (each with a true anchor position,
recovered from the .doc's `PlcfandRef` — not "the story it follows") plus one in the
notes column. They are not noise — they are expert judgments we have never used:

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
- *"Here is … example hada ve'od that looks Amoraic. Check parallel"* — the notes-column
  one, on 33b; a source-critical observation, and an open question addressed to us

## Why it matters

The classification notes are **exactly the material Wave 6 needs**: Jeff drawing the
line between a story and a halakhic exchange, in his own words, on real passages. Our
criteria doc rests on one paragraph of his; this is several more, each attached to a
specific text.

The boundary notes extend the corrections set, which is the smaller of the two Kiddushin
rulers.

## Method

1. Take the `comments` stream from `NEXT/05`. Each is already attached to the passage
   it anchors to — **the attachment is the whole value**; a comment without its passage
   is unusable. The attachments are self-verifying: each note names something present in
   the passage it points at (see the finding, §5). Sort **at the sentence level, not the
   comment level** — `c_02` is two remarks in one annotation, a boundary instruction plus
   an attribution note.
2. Sort into: boundary correction / classification judgment / borderline flag / other.
3. Boundary ones → extend `tests/expert_boundary_targets_v2.json` via
   `scripts/build_boundary_testset.py`. Mind `quote_polarity` — whether the quoted
   Hebrew is text to keep or text to cut. Getting this backwards silently anchors a
   target one clause off, which went unnoticed for months.
4. Classification ones → append to `docs/findings/2026-07-06-jeff-story-definition-criteria.md`
   as cases, quoting him verbatim. **Do not paraphrase into a rule.** A gloss added to
   his words once produced a contradiction that turned out to be ours, not his.
5. Append everything to the feedback ledger first (Lesson 17).

6. **Two loose ends** from the parse, both worth an answer:
   - Jeff wrote a `מו ע"ב` (46b) location label with **no story beside it**, in the row
     he edited in 2026. Check what sits at 46b, or ask him.
   - The one entry he marked `הוספתי--י.ר.` is a *shorter* form of a story he already
     had, trimmed before the `אמר אביי` scriptural coda. Given his other 2026 notes are
     boundary corrections, this is probably one too — and if so it is a boundary target
     stated by example rather than in words. Confirm before using it as one.

7. **While you are here: 16 Kiddushin verdicts have never been folded into the golden.**
   `results/canonical/kiddushin_canonical.json` was built from the 2026-04-23 round only
   (`feedback_source` says so). Two later rounds sit unused:
   `validation/feedback/kiddushin_review_2026-05-26 (1).json` (1 reviewed) and
   `jeff comms/wave4_kiddushin_review_2026-07-06.json` (15 reviewed). That is Lesson 1
   happening again — feedback split into piles and one pile never revisited. Append them
   to the ledger and either fold them in or record why not, per Lesson 17.

## How you know it worked

Every remark either sorted and used, or explicitly listed as unusable with a reason.
Nothing silently dropped. The count to reconcile against is **10** remarks, plus the
**16** unincorporated verdicts in item 7.

## Guardrails

- Quote Jeff verbatim; mark any interpretation as ours.
- These are CIRCULAR — they are comments on our output. Fine for precision and criteria,
  never for recall (FRAMEWORK §3).
