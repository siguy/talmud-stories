# Jeff answers the four lines — and the 2005 lists stop outranking him

**Date:** 2026-10-09 · **Source:** `jeff comms/10-7-2026/Brief response, 10.7.docx`, his
reply (2026-10-07) to the eight passages in `comms/2026-10-02-email-jeff-DRAFT.md`.
**Evidence:** his verdicts; **measured** for the counts below.

## What he said

| Q | passage | on his 2005 list | his verdict | rule |
|---|---|---|---|---|
| 1A | Kiddushin 80b:11, the widow and the guard | yes | **borderline** — the incident *"has to be filled in… with the help of the Talmudic commentaries"* | new **R-C6** |
| 1B | Yevamot 107b:7, Pishon's wife | yes | **not** — *"one thing Pishon's wife did—without change or causality"* | R-C5 |
| 2A | Ketubot 21b:0, Rav Ashi to Ameimar | yes | **not** — praise and rebuke *"is not that exceptional in Talmudic dialogue"* | R-C2 |
| 2B | Ketubot 53a:11, Rav Ḥisda | yes | **not** — *"standard rabbinic dialogue"* | R-C2 |
| 3A | Ketubot 50b:4, the orphan daughters | no | **not** — *"not really another action or change that is narrated"* | R-C0's limit |
| 3B | Ketubot 50a:10, forty times | no | **borderline** — *"mainly about rabbinic teaching, speech-acts"* | R-C2 |
| 4A | Ketubot 61a:14, the two pious men | yes | **story** — *"at least two actions and change… leads to a change—that Elijah visits him"* | R-C3 |
| 4B | Ketubot 67b:17, R. Abba's coins | yes | **blank** — re-asked 2026-10-09 | open |

(Segment indices are 0-based; the email's Sefaria links were 1-based.)

**Separately, to Simon:** the 2005 lists were initial, non-comprehensive attempts;
inconsistencies are expected; use his recent thinking and rulings.

## The one principle under all four answers

He asks for **at least two actions and a change.** A single act (107b), a ruling with
nothing else narrated (50b), ordinary scholarly back-and-forth (21b, 53a) and teaching
(50a) fall short. A habit that *causes* something (61a) clears it. An incident that is
complete in the world but only alluded to in the text (80b) is borderline.

## What changed

- **Rule register:** R-C0 limit, R-C2 extended, R-C3 extended, R-C5 fifth case, R-C6 new, and
  a standing statement that his recent rulings outrank the lists (`docs/STORY_RULES.md`).
- **Goldens** (`scripts/apply_jeff_2026-10-07_verdicts.py`, idempotent): Ketubot entries
  187 → 189, accepted 163 → 162 — 21b:0, 53a:11, 50b:4 → `NOT_A_STORY`; 50a:10 added
  `BORDERLINE`; 61a:14 added `YES`. Kiddushin 80b:11 `LOW_CONFIDENCE` → `BORDERLINE`
  (counts unchanged).
- **Recall denominators** (`results/expert_lists/superseded_by_rule.json`, stamped by
  `scripts/stamp_superseded_recall.py`, applied on every new run of
  `measure_recall_vs_expert_list.py`): the three `not`s leave the denominator; the list text
  is untouched. `--standard 2005` reproduces the old number.

| tractate | end-to-end recall before | after |
|---|---|---|
| Ketubot | 130/149 | 129/147 (21b was found, 53a was a miss) |
| Yevamot | 91/102 | 90/101 (107b was found) |
| Kiddushin, Gittin | unchanged | 80b is borderline and still counts |

## What is open

1. **4B** — re-asked in the same thread (Gmail draft, `comms/2026-10-09-email-jeff-4B-DRAFT.md`).
2. **Re-run the two consensus judges** with the new register and count how far the splits
   shrink (76 / 79 / 32 on questions 1–3; 17 rejected list stories on question 4,
   `docs/findings/2026-10-02-rule-panel-lenses.md`). That is the payoff measurement; not run
   here. The 2026-10-07 verdicts are not yet a labelled round the judge scores against.
3. **Stage 2 prompt** (`src/story_detector_v11.py`) does not carry the new wording yet.
