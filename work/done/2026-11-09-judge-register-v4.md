---
title: Judge prompt v4 — drop the borderline shape Jeff withdrew on 2026-10-25
capability: [classification]
tractate: []
blocked_by: []
awaiting: []
writes: [src/prompts/judge_register_v4.md, scripts/compare_judge_v2_v4.py, results/consensus/phase1/bl_v6_*, results/consensus/phase1/compare_v2_v4.json, results/consensus/phase1/subagent/bl_v6*, docs/findings/2026-11-09-judge-register-v4.md]
finding: docs/findings/2026-11-09-judge-register-v4.md
superseded_by:
---

# Judge prompt v4 — drop the borderline shape Jeff withdrew on 2026-10-25

**Self-contained.** A fresh session executes this with no other context.
Read [`FRAMEWORK.md`](../../FRAMEWORK.md) first, then this.

## The claim to test / the problem

`src/prompts/judge_register_v2.md` (the judge prompt in use) defines `borderline` to include
"one event followed by discussion or a ruling". Jeff withdrew that shape on 2026-10-25
(`docs/STORY_RULES.md` R-C0, R-C7 shape 2): *"not a story rather than … borderline"*, unless
the ruling is itself an act that changes something (Ketubot 65a). On Berakhot the Claude
judge cited R-C7 on 46 of the 48 passages it called borderline where Gemini said story.

v3 (2026-10-09) narrowed this shape **and** shape 4 and was reverted for costing 19 of his
yes/borderline. His 10-25 answer turns the shape-2 part of that cost into correct
rejections. v4 makes only the shape-2 change he ruled on.

## Method

Same 287-unit hard subset as the 2026-10-09 test (`borderline_test_ids.txt`), same model,
same register, today: v2 and v4 on Gemini (paired, so the prompt line is the only
variable). Labels: `current_labels()` plus his 2026-10-25 direct verdicts. Passages the
register quotes are excluded (the judge is shown their answer).

## How you know it worked

v4 moves his `no`s from borderline to `not` and does not move his `yes`/`borderline`
passages to `not` beyond the v2-vs-v2 repeat noise.

## Guardrails

No change to v2 or the register. `evaluate_golden.py` untouched. Eruvin never read.

## When done

Write the finding to `docs/findings/<date>-<slug>.md`, add an `## Outcome` section
below, and `git mv` this file to `work/done/`. **Never delete it.**

## Outcome

**Not adopted; v2 stays.** Finding: [`docs/findings/2026-11-09-judge-register-v4.md`](../../docs/findings/2026-11-09-judge-register-v4.md).
Gemini, 240 scored, two runs per prompt (noise 2–5 verdicts; v2→v4 moved 35–36). v4 drops
about 5 of his `no`s from the kept set and about 12 of his `yes`es. Of the 14 yes/borderline
it sends to `not`, 9 are the withdrawn shape (older labels his 10-25 rule may overturn —
a question for Jeff) and 5 are overreach (habits, a cited act). **Why not adopted:** the
overreach is a wording defect, and the 9 are our guess at his "similar ones". Next: ask him
about the 9, narrow the sentence to "a case brought to a rabbi and ruled on", re-run, then
run the Claude arm.
