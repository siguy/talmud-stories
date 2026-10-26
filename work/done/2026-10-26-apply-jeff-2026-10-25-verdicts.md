---
title: Apply Jeff's 2026-10-25 reply — one event then a ruling is not a story; 65a borderline
capability: [classification]
tractate: [ketubot, gittin, yevamot]
blocked_by: []
awaiting: []
writes: [results/canonical/ketubot_canonical.json, results/canonical/gittin_canonical.json, results/expert_lists/superseded_by_rule.json, tests/test_bookkeeping.py, scripts/apply_jeff_2026-10-25_verdicts.py]
finding: jeff comms/10-25-2026/reply.md
superseded_by:
---

# Apply Jeff's 2026-10-25 reply

**Self-contained.** Read [`FRAMEWORK.md`](../../FRAMEWORK.md), then R-C0 and R-C7 in
[`docs/STORY_RULES.md`](../../docs/STORY_RULES.md), then this.

## The problem

Jeff answered both questions of the 2026-10-11 email (`jeff comms/10-25-2026/reply.md`):
one event then a ruling or discussion is **not** a story (his February borderlines on the
shape withdrawn); Ketubot 65a:10 borderline; Yevamot 45a:16 and Gittin 89a:19 not.
Rules recorded 2026-10-26. The golden and the list annotations are not yet changed.

## Method

`scripts/apply_jeff_2026-10-25_verdicts.py --dry-run` prints the blast radius. Two tiers:

| tier | what | golden | list annotations | recall denominators |
|---|---|---|---|---|
| `direct` | passages he named | Ketubot 50b:9-10 → NOT, 51a:1-2 added NOT, 65a:10 → BORDERLINE; Gittin 89a:19 → NOT. Ketubot accepted 162 → 161, Gittin 116 → 115 | 4 (ketubot_030, ketubot_065 borderline, yevamot_014, gittin_111) | Ketubot 147→146, Gittin 111→110, Yevamot 101→100 |
| `+ description` | his own February borderlines whose note names the shape | + 53a:12, 54a:13-14, 77a:8 → NOT. Ketubot accepted → 158 | + ketubot_034, ketubot_036 | Ketubot → 144 |

Printed, never applied: 3 FLAGGED near-cases (49b:6, 100b:17-18, 54a:21, where his 65a line
could keep them borderline) and 19 judge-indicated passages (CIRCULAR).

**Simon decides the tier.** Then run without `--dry-run`, update `GOLDEN_COUNTS` in
`tests/test_bookkeeping.py` in the same commit, re-run the recall harness for the three
tractates, and `python3 scripts/board.py`.

## Not done here, on purpose

- **No re-score of the v4/v5 judge runs.** The Q2 passages are not in that 287-passage
  subset, and on the Q1 passages v4 and v5 differ on 2. The labels move to match the rule
  v5 encodes, so its gain would be partly circular. The real test is a fresh judge run on
  the updated register (`work/2026-10-09-judge-answer-categories.md` or a successor).
- **Gittin golden is built by `scripts/build_gittin_golden.py`**, which does not read this
  ruling. Edited in place like the Ketubot golden; a rebuild would undo 89a:19 until the
  builder reads `superseded_by_rule.json` or this script is re-run.
- Detector v12's prompt (`src/story_detector_v12.py`) must be checked against R-C0's new
  lines before it is run.

## How you know it worked

Dry run's counts equal the post-apply counts; `python3 -m pytest tests/ -q` passes with the
new `GOLDEN_COUNTS`; the recall harness logs `SUPERSEDED` for each new annotation.

## When done

Add `## Outcome`, then `python3 scripts/board.py finish 2026-10-26-apply-jeff-2026-10-25-verdicts`.

## Outcome

Done 2026-10-26. Applied `--tier description` with **Ketubot 54a:13-14 held back**
(Simon): his February note names the shape, but Rav Nahman *changes his ruling*, which his
65a line may count as change — it is FLAGGED with 49b:6, 100b:17-18, 54a:21 for the next
email. Goldens: Ketubot 189/162 → **190/160** (50b:9-10, 53a:12 → NOT; 51a:1-2 added
NOT; 65a:10 → BORDERLINE); Gittin accepted 116 → **115** (89a:19 → NOT; header
distribution and `recall_denominator` refreshed). List annotations +5 (ketubot_030,
ketubot_034, ketubot_065 borderline, yevamot_014, gittin_111). Recall, stamped with
`scripts/stamp_superseded_recall.py` (no re-match): Ketubot 129/147 → **128/145**, Gittin
108/111 → **107/110**, Yevamot 90/101 → **89/100**; Kiddushin unchanged. Every story that
left a denominator was one we had found, so the rates barely move.
**Why no v4/v5 re-score:** the Q2 passages are not in that subset, v4 and v5 differ on 2 of
the Q1 passages, and the labels moved toward the rule v5 encodes — a circular gain. The
measurement is a fresh judge run on the updated register.

**Correction, same day:** 77a:8 was applied with the `description` tier and reverted when `tests/test_golden_rules.py::test_the_two_ketubot_cases_he_affirmed_are_marked_not_deleted` fired: it is the Mishnah story he affirmed (R-C1), and his note gives it an implied change. Which way his Q1 reasoning cuts there is his call; it is FLAGGED. Ketubot accepted is 160, not 159. `tests/test_superseded_by_rule.py::test_unruled_rows_still_count` used Gittin as an unruled tractate; it uses Eruvin now.
