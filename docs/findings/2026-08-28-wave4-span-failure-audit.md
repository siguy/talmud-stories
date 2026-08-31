# Wave 4 Text-Span Failure: Full Audit and Revert

**Date:** 2026-08-28
**Status:** Diagnosis complete; revert shipped and verified.
**Trigger:** Jeff Rubenstein's 2026-07-06 review
([ledger](../../validation/feedback/jeff_2026-07-06_feedback_ledger.md)) flagged
8 mis-trimmed Kiddushin stories, one cut mid-word.
**Supersedes the scale claim in:** [docs/history/2026-08-28-PLAN-wave5.md](../history/2026-08-28-PLAN-wave5.md)
(drafted before this audit, which assumed the damage was limited to the 8 stories
Jeff happened to review).

---

## 1. What we thought, and what is actually true

Wave 4 (v10) asked Gemini for a **character offset** into the boundary segment to
mark where a story begins and ends inside it. Jeff reviewed 15 of 95 Kiddushin
stories and marked 8 as mis-trimmed. The working assumption was that this was a
sample of a moderate problem.

It is not. Auditing **every** emitted cut across all three v10 outputs
([scripts/audit_text_spans.py](../../scripts/audit_text_spans.py)):

| Output | Stories | Trimmed | Cuts | Mid-word | At clause edge |
|---|---|---|---|---|---|
| `ketubot_v10_2-60.json` | 67 | 31 | 40 | 24 (60%) | 0 (0%) |
| `ketubot_v10_61-112.json` | 116 | 54 | 63 | 37 (59%) | 6 (10%) |
| `kiddushin_v10.json` | 106 | 68 | 86 | 43 (50%) | 1 (1%) |
| **Total** | **289** | **153** | **189** | **104 (55%)** | **7 (4%)** |

**Over half of all cuts sever a Hebrew word.** Kiddushin 30a was not an outlier;
it was the one Jeff happened to look at. ~100 further corrupted cuts sit in the
two Ketubot files, which no expert has ever reviewed.

## 2. The decisive evidence: the mechanism has no observed successes

Cross-tabulating Jeff's 15 verdicts against whether v10 actually trimmed that story:

| | Reviewed | Correct | Incorrect |
|---|---|---|---|
| **Story was trimmed** | 9 | **0** | **9** |
| Story was not trimmed | 6 | 4 | 2 |

Every story the trimmer touched and a human then inspected was judged wrong. The
two incorrect untrimmed cases (8b_14, 20a_12-14) fail for unrelated segment-level
and cross-page reasons (Cause B in the ledger).

This is a stronger result than "the mechanism is inaccurate." On the only evidence
available, the feature is **net-negative in every observed instance**.

## 3. Root cause (confirmed, not re-litigated)

The nikud-stripping position map in [src/story_detector_v10.py](../../src/story_detector_v10.py)
is faithful — `stripped[i] == hebrew[map[i]]` holds for every `i`. The mapping code
is correct, so the bad cuts come from the model's raw offset numbers.

LLMs reproduce text reliably and count characters unreliably. See
[lessons/](../../lessons/README.md) Lesson 16.

## 4. The revert (shipped)

Rather than leave corrupt output live while a better trimmer is built, the spans
were removed, restoring segment-level boundaries.

The reasoning is asymmetric-risk, not perfectionism: **an over-inclusive segment
boundary is recoverable by a human reader — a mid-word cut is not.** On Jeff's own
sample, shipping untrimmed would have scored 4/6 rather than 4/15.

- Script: [scripts/strip_text_spans.py](../../scripts/strip_text_spans.py)
- Outputs: `results/v10/wave4_notrim/*_notrim.json`
- v10 outputs and `src/story_detector_v10.py` are untouched
  (memory `feedback_detector_versioning.md`).

### Verification

| Check | Result |
|---|---|
| Ketubot composite, v10 with spans | **0.9171** |
| Ketubot composite, no-trim | **0.9171** (identical) |
| Spans removed from | 153 stories |
| `audit_text_spans.py --strict` on no-trim | **PASS** (0 mid-word) |

Score-neutrality was *proven by running the harness both ways*, not inferred from
reading it. (It also holds by construction: `scripts/evaluate_golden.py` reads only
`start_segment` / `end_segment`.)

## 5. What this leaves behind

**A permanent gate.** [scripts/audit_text_spans.py](../../scripts/audit_text_spans.py)
measures mid-word rate and clause-edge rate on any detector output, with the v10
baseline recorded in its docstring. `--strict` exits non-zero on any mid-word cut.
Any future span mechanism (Wave 5) must pass it. This converts Lesson 16 from prose
into an executable check — the Lesson 17 pattern.

**A caution about review UIs.** [validation/generators/generate_wave4_review_ui.py](../../validation/generators/generate_wave4_review_ui.py)
(`renderHebrew`, ~line 304) trims **Hebrew only**; English is highlighted at full
segment granularity. That is why Jeff repeatedly wrote "the English is right but the
Hebrew is cut off" (9a_2, 8b_14) — the UI showed him a mismatch by construction.
Fix before the next review round, or the same confusion is purchased twice.

**A sequencing consequence.** With nothing corrupt in the current outputs, Wave 5
(clause-anchored spans) is no longer urgent. See
[docs/history/2026-08-29-PLAN-wave6-story-criteria.md](../history/2026-08-29-PLAN-wave6-story-criteria.md) for what took its place and why.
