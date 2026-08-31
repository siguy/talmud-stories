---
title: Parse Jeff's Kiddushin story list
capability: [detection, boundaries]
tractate: [kiddushin]
blocked_by: []
awaiting: []
finding: docs/findings/2026-08-30-kiddushin-list-parse.md
superseded_by:
---

# Parse Jeff's Kiddushin story list

**PREREQUISITE for 06, 07, 08. Nothing downstream is trustworthy until this is done.**
Read `STATUS.md` and `FRAMEWORK.md` first. **Capability: ground truth for 1, 2, 4.**
**No API calls.**

## Why this is its own task

`jeff comms/8-30-2026/kidushin.doc` is **not** the same shape as the Ketubot list.
Running `parse_expert_doc` on it returns 105 entries, but:

- **9 of them are Jeff's English review comments, not stories** — "I think these words
  should be omitted", "This is not really a story. It is a halakhic question and
  answer", "Not sure this is a story. No real narrative."
- Those comments sit in a trailing block, so they **inherit the preceding reference** —
  which is why Kiddushin 81b appears to hold 11 stories. Any measurement on that daf
  would be corrupted.
- The doc contains `הוספתי--י.ר.` — *"I added — J.R."* This very likely marks stories
  Jeff **added from our output**. Those are NOT blind: measuring recall against a story
  we ourselves proposed is circular, and inflates the number (FRAMEWORK §3).
- Daf references appear in Hebrew form (`פא ע"ב`), not the English form the Ketubot doc
  used.

The Ketubot doc has **0** English entries. It was clean; this one is not. Assuming
otherwise is how a corrupted ground truth gets built.

## Method

1. Write `scripts/parse_kiddushin_list.py` (do not edit the Ketubot parser — it works).
2. Separate the file into three streams, each written out and counted:
   - **stories** — Hebrew entries with a resolvable daf reference
   - **comments** — English review notes, kept with the story they follow (they are
     boundary and classification feedback; hand them to `NEXT/08`)
   - **added-by-Jeff** — anything under `הוספתי--י.ר.`, flagged `blind: false`
3. Handle Hebrew daf refs (`פא ע"ב` → `Kiddushin 81b`).
4. Emit `results/expert_lists/kiddushin_2005.json` with `blind: true|false` on **every**
   story. Downstream must be able to exclude non-blind entries.
5. Sanity-check the count by hand against the document. State the number and how it was
   arrived at.

## How you know it worked

- A story count you can defend, with the 9 comments removed and the added-by-Jeff
  entries flagged rather than deleted.
- No reference holds an implausible number of stories (81b's 11 was the tell).
- A spot-check of five entries read against the original document.

## Guardrails

- **Never delete Jeff's comments** — they are expert feedback and `NEXT/08` needs them.
- A story he added from our output is not blind. Flag it, keep it, exclude it from
  recall. Say so wherever a number is reported (FRAMEWORK §3).
- Label the finding measured / indicated / suspected.

## When done

Update `STATUS.md` ground-truth block with the defensible count. Unblocks 06, 07, 08.

## Outcome

**Done 2026-08-30 (`0ee1995`).** 95 stories, read from the .doc's own OLE table streams rather than a converter's line dump — the line-based read returned 105, of which 9 were Jeff's English review comments and 4 were parallels-column citations. Ten expert remarks came back with their exact anchor positions. **This brief's blindness guess was backwards** and the correction took two further passes: `הוספתי--י.ר.` marks one entry *he* added, not stories taken from our output; the real contamination is five appendix entries he merged in (`240c3cb`), of which four are excluded and one — 81b, which we never proposed — stays because dropping it would inflate recall (`2cd1094`). Denominator 90. -> Lessons 28, 29.
