# NEXT 06 — Kiddushin recall: triage and detection

**`NEXT/05` is DONE** — ground truth is
[`results/expert_lists/kiddushin_2005.json`](../../results/expert_lists/kiddushin_2005.json)
(95 stories; see [`docs/golden/v11/kiddushin_list_parse_2026-08-30.md`](../../docs/golden/v11/kiddushin_list_parse_2026-08-30.md)).
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
   notes (Lesson 25). Feed it the stories from `kiddushin_2005.json` instead.
   Filter `blind == true` and `duplicate_of == null`.
2. Split the misses by cause, as was done for Ketubot: triage discarded the page /
   page examined but nothing proposed / proposed but classified NOT_A_STORY. The third
   is a **Classification** failure, not Detection — keep them apart (FRAMEWORK §1).
3. Report triage recall separately from detection recall. They compose:
   `triage × detection = end-to-end` (FRAMEWORK §2b).
4. **Report recall over both denominators, 89 and 94, and quote the range.** Five
   entries carry `expert_flagged_miss_2026` — the stories Jeff told us in April 2026 we
   had missed. They are his, not ours, so they are not circular; but they were selected
   *because* we missed them, so counting them biases recall **downward**. Whether they
   were in his 2005 original is indicated, not measured. The true value is one of the
   two numbers, not between them — say which entries move it.

## How you know it worked

Kiddushin's Triage and Detection cells filled, each naming its dataset as BLIND, plus a
cause breakdown of the misses. If the numbers differ markedly from Ketubot's, say so
plainly — that is a generalization finding and it matters more than the number itself.

## Guardrails

- Exclude `blind: false`. Exactly one entry qualifies: the one Jeff marked
  `הוספתי--י.ר.` ("I added — J.R.") in 2026, which is also a duplicate of an entry he
  already had. Note the direction: the brief for `NEXT/05` guessed this marked stories
  taken from our output, which would inflate recall. It does not — see §4 of the
  finding. The contamination that does exist pushes the other way.
- Same script as Ketubot, or the comparison is meaningless.
- Regenerate today's baseline before comparing (Lesson 11).

## When done

Findings → `docs/golden/workflow/kiddushin_recall_<date>.md`. Update the scoreboard.
