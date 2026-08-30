# NEXT 06 — Kiddushin recall: triage and detection

**Needs `NEXT/05` first.** Read `STATUS.md` and `FRAMEWORK.md`.
**Capabilities: 1 Triage, 2 Detection.** **No API calls.**

## What this fills in

Two cells that have read "unmeasured" for the life of the project. Kiddushin has a
mature detector output (95 stories, a golden set, 8 review rounds) and has **never had a
blind dataset**, so we have never known what it misses. Ketubot's equivalents are
Triage 98.0% and Detection 96.0%.

## Method

Mirror the Ketubot measurement exactly — same script, so the numbers are comparable.

1. `scripts/measure_recall_vs_expert_list.py` with the blind-only subset from `NEXT/05`
   against `results/v10/wave4_notrim/kiddushin_v10_notrim.json`.
2. Split the misses by cause, as was done for Ketubot: triage discarded the page /
   page examined but nothing proposed / proposed but classified NOT_A_STORY. The third
   is a **Classification** failure, not Detection — keep them apart (FRAMEWORK §1).
3. Report triage recall separately from detection recall. They compose:
   `triage × detection = end-to-end` (FRAMEWORK §2b).

## How you know it worked

Kiddushin's Triage and Detection cells filled, each naming its dataset as BLIND, plus a
cause breakdown of the misses. If the numbers differ markedly from Ketubot's, say so
plainly — that is a generalization finding and it matters more than the number itself.

## Guardrails

- Exclude non-blind entries (the ones Jeff added from our output). Recall measured
  against a story we proposed is circular and inflates the result.
- Same script as Ketubot, or the comparison is meaningless.
- Regenerate today's baseline before comparing (Lesson 11).

## When done

Findings → `docs/golden/workflow/kiddushin_recall_<date>.md`. Update the scoreboard.
