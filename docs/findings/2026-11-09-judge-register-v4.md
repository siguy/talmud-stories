# Judge prompt v4: dropping "one event, then a ruling" from borderline is not adopted yet

**Date:** 2026-11-09 · **Item:** `work/done/2026-11-09-judge-register-v4.md`
**Evidence:** rule-informed (the judge carries the register written from these verdicts),
**measured** on the 287-passage hard subset (not the whole set), Gemini only, two runs per
prompt. Script: `scripts/compare_judge_v2_v4.py` → `results/consensus/phase1/compare_v2_v4.json`.

## The change

`src/prompts/judge_register_v4.md` = v2 with one sentence changed. v2's `borderline` includes
"one event followed by discussion or a ruling"; v4 says that shape is `not` (R-C0,
2026-10-25) unless the ruling is itself an act that changes something (Ketubot 65a). Jeff
withdrew the shape on 2026-10-25. Shape 4 (an incident only alluded to) is left as in v2;
v3 narrowed that too and was reverted.

## Runs

| run | prompt SHA | register SHA | model | finished |
|---|---|---|---|---|
| v2a, v2b | `84bfb33fd32a` | `6a2d8e563ab7` | gemini-3-flash-preview, T=0.1 | 2026-11-09 07:35, 07:36 |
| v4a, v4b | `3ad3966c4525` | `6a2d8e563ab7` | same | 2026-11-09 07:38, 07:40 |

Same day, same register: the prompt sentence is the only variable. The first attempt ran
all four in parallel and hit Gemini's 3M-tokens/minute quota (204 failed calls); they were
resumed sequentially into the same files. Two units still have a failed call in some run
and are counted, not scored. 45 units the register now quotes are excluded (the judge is
shown their answer). **240 scored.**

## Result

Noise floor: v2a vs v2b differ on 2 verdicts, v4a vs v4b on 5. v2 vs v4: **35–36**. The
change is real.

| his label | v2 (a / b) | v4 (a / b) |
|---|---|---|
| yes (88): judge `not` | 16 / 16 | **27 / 28** |
| borderline (25): judge `not` | 7 / 7 | 8 / 8 |
| no (127): judge keeps (story or borderline) | 31 / 29 | **26 / 25** |

Consistent moves (both v2 runs → both v4 runs), borderline → not: **his yes 11, his
borderline 2, his no 5.** Story → not: his yes 1.

**So v4 drops about 5 of his `no`s from the kept set and about 12 of his `yes`es with
them.** Read case by case, the 14 yes/borderline it sends to `not` split two ways:

- **9 are the shape he withdrew** — one event (usually someone coming before a rabbi), then a
  ruling or a dispute, and nothing else narrated: Ketubot 100b:17-18, 107b:8-10 (two units), 111a:10-11 (two units), list
  ketubot_113, ketubot_134, gittin_064, Kiddushin 7b:9-10. His labels on these are older
  than 10-25. His 10-25 words — *"these cases and similar ones are not a story"* — would
  make them correct rejections, but **which passages are "similar" is ours to guess, not his
  to have said** (Lesson 27). `apply_jeff_2026-10-25_verdicts.py` already declined to apply
  100b:17-18 for this reason (FLAGGED).
- **5 are overreach** — reports of practice or a single act cited as precedent, which v4
  now reads as the same shape: Ketubot 8a:6, 86a:8, Kiddushin 33a:16, 8a:9-9, 8a:9-10. Jeff
  never ruled these not a story; v4's sentence is pulling them in.

## Decision

**Not adopted.** v2 stays the judge prompt. Before v4 can be adopted:

1. **A question for Jeff:** do his older `yes` verdicts on the 9 "came before a rabbi"
   passages above still stand after 10-25? If he says `not`, v4's cost on those is zero.
2. **Fix the overreach:** a v4 wording that names "a case brought to a rabbi and ruled on"
   rather than "one event", so habits and cited acts stay where v2 put them. Then re-run
   this test.
3. **The Claude arm** has not been run on v4. On Berakhot Claude, not Gemini, was the judge
   leaning on this shape (R-C7 cited on 46 of its 48 borderlines where Gemini said story),
   so Gemini's numbers alone cannot predict the Berakhot effect.

**For Septimus:** none of this touches the passages both judges call a story. On his `yes`
labels Gemini's `story` count is unchanged (31 → 33/34); the movement is borderline → not.
