---
title: Test a wider borderline definition (R-C7, judge prompt v2)
capability: [classification]
tractate: [ketubot, kiddushin, gittin, yevamot]
blocked_by: []
awaiting: []
writes: [docs/STORY_RULES.md, src/prompts/judge_register_v2.md, scripts/judge_labelled_spans.py, scripts/judge_via_subagents.py, scripts/compare_borderline_test.py, results/consensus/phase1/bl_v4_gemini.json, results/consensus/phase1/bl_v4_claude.json, results/consensus/phase1/subagent/bl_v4_claude/, results/consensus/phase1/borderline_test_ids.txt, results/consensus/phase1/compare_borderline_test.json]
finding: docs/findings/2026-10-09-borderline-definition-test.md
superseded_by:
---

# Test a wider borderline definition

Simon, 2026-10-09: are partial stories forced to `not` because the judge's `borderline`
means R-C2 only? Test: R-C7 + `judge_register_v2.md` on 287 chosen passages, both judges.

## Outcome

Yes. Claude moved 56 of 89 rejected `yes`es to borderline; both judges find his borderlines
far more often; story-vs-not agreement 143 → 193 of 271. Cost: both keep ~10 more of his `no`s
as borderline (9 → 19). Batch 007 re-judged by a fresh agent because the first read several
files per command (truncation risk). Next: full 997 under v2; R-C7 to Jeff for confirmation.
