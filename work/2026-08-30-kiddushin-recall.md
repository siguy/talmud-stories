---
title: Kiddushin recall: triage and detection
capability: [triage, detection]
tractate: [kiddushin]
blocked_by: []
awaiting: []
finding:
superseded_by:
---

# Kiddushin recall: triage and detection

**`NEXT/05` is DONE** — ground truth is
[`results/expert_lists/kiddushin_2005.json`](../results/expert_lists/kiddushin_2005.json)
(95 stories; see [`docs/findings/2026-08-30-kiddushin-list-parse.md`](../docs/findings/2026-08-30-kiddushin-list-parse.md)).
Read `STATUS.md` and `FRAMEWORK.md`.
**Capabilities: 1 Triage, 2 Detection.** **No API calls.**

## What this fills in

Two cells that have read "unmeasured" for the life of the project. Kiddushin has a
mature detector output (95 stories, a golden set, 8 review rounds) and has **never had a
blind dataset**, so we have never known what it misses. Ketubot's equivalents are
Triage 98.0% and Detection 96.0%.

## Method

Mirror the Ketubot measurement exactly — same script, so the numbers are comparable.

1. `scripts/measure_recall_vs_expert_list.py` against
   `results/v10/wave4_notrim/kiddushin_v10_notrim.json`. Do **not** re-parse the .doc —
   its `parse_expert_doc` returns 105 entries on this document, 9 of them Jeff's English
   notes (Lesson 28). Feed it the stories from `kiddushin_2005.json` instead.
   Filter `blind == true` and `duplicate_of == null`.
2. Split the misses by cause, as was done for Ketubot: triage discarded the page /
   page examined but nothing proposed / proposed but classified NOT_A_STORY. The third
   is a **Classification** failure, not Detection — keep them apart (FRAMEWORK §1).
3. Report triage recall separately from detection recall. They compose:
   `triage × detection = end-to-end` (FRAMEWORK §2b).
4. **The denominator is 89.** Use `recall_denominator` — filter `blind == true` and
   `duplicate_of == null`. The six excluded are the one Jeff added himself and the five
   `in_appendix` entries, which are our own cases merged into his list (finding §4).
   Including them would score us against stories that are there because of us.

## How you know it worked

Kiddushin's Triage and Detection cells filled, each naming its dataset as BLIND, plus a
cause breakdown of the misses. If the numbers differ markedly from Ketubot's, say so
plainly — that is a generalization finding and it matters more than the number itself.

## Guardrails

- Exclude `blind: false`. Exactly one entry qualifies: the one Jeff marked
  `הוספתי--י.ר.` ("I added — J.R.") in 2026, which is also a duplicate of an entry he
  already had. That is the *only* non-blind entry — the `NEXT/05` brief's worry that the
  list was seeded from our output did not survive checking (finding §4).
- **Do not re-derive the appendix entries as misses.** Three of the five (33a, 53a as
  partial spans, 71a and 81b not at all) are cases we handle badly, so they will look
  like findings. They are excluded from the denominator; report them separately as
  known-hard cases if useful, never inside the recall number.
- The per-run history of those five is `scripts/check_appendix_coverage.py`. **45a is a
  genuine Wave 1 win** — absent in v7, found since. Worth saying in the writeup, since
  the appendix is the only reason we can see it.
- Same script as Ketubot, or the comparison is meaningless.
- Regenerate today's baseline before comparing (Lesson 11).

## When done

Findings → `docs/golden/workflow/kiddushin_recall_<date>.md`. Update the scoreboard.
