---
title: Kiddushin recall: triage and detection
capability: [triage, detection]
tractate: [kiddushin]
blocked_by: []
awaiting: []
finding: docs/findings/2026-08-31-kiddushin-recall.md
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

Findings → `docs/findings/<date>-kiddushin-recall.md`. Update the scoreboard.

## Outcome

**Done 2026-08-31. Both cells filled.** →
[`docs/findings/2026-08-31-kiddushin-recall.md`](../docs/findings/2026-08-31-kiddushin-recall.md)

| | Ketubot | Kiddushin |
|---|---|---|
| **1 Triage** | 98.0% (146/149) at 44% of pages | **95.6%** (86/90) at **38%** of pages |
| **2 Detection**, given the page survived triage | 97.9% | **97.7%** |
| end-to-end, loose / strict | 96.0% / 87.9% | 93.3% / 83.3% |

**The finding is the one this brief asked for, and it is a reassignment.** Kiddushin's
recall is 2.7 points below Ketubot's and **none of it is Detection** — 97.7% against
97.9%, one story apart. All of it is Triage, which Kiddushin had never measured and
which skips 62% of the tractate against Ketubot's 56%. The scoreboard had been reading
this deficit in the Detection column since 2026-08-30.

Cause split of the 6 misses: **4 triage-discarded** (every page the story occupies was
skipped, the same shape as Ketubot's 3), **2 examined-and-nothing-proposed**. Two further
stories are proposed and then classified `NOT_A_STORY` (44a, 58a) — kept out of the recall
figure as Classification, and the reason the figure reaching output is 91.1% not 93.3%.

**Two things came out that the brief did not ask for:**

- **Kiddushin 81b holds two of Jeff's stories, not one.** Every prior document discusses
  only the appendix case. The second is blind, examined, and never proposed.
- **Wave 1's lexical override is worth +1.1 points of triage recall** (one story, 49b),
  for 9 extra Stage 2 calls. First time it has been priced against a blind set; its two
  known wins, 45a and 53a, are appendix cases outside the denominator.

### Where this brief was wrong, and it did not matter

It says "the denominator is 89" and in the same sentence to use `recall_denominator`,
which is **90**. It predates
[`appendix-provenance-correction`](../docs/findings/2026-08-30-appendix-provenance-correction.md),
which split *blind* from *counts for recall*. 90 was used. All three readings (89 / 90 /
94) were run: **they span 0.3 points and change no conclusion.**

### Guardrails, as followed

Ketubot's baseline was regenerated today before anything was compared (Lesson 11) and
reproduces 96.0% / 98.0% / 44% and its 19 / 16 / 3 triage exposure exactly — which is
what proves the script changes are inert. The appendix entries were not re-derived as
misses. 45a is confirmed as the Wave 1 win the brief describes.

**Not done, and deliberately:** no noise floor for recall. It needs re-running the
detector (API calls, which this brief excludes). Stated as a caveat in the finding
rather than papered over — the figures are one run per tractate.
