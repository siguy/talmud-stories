# Widening `borderline` moves partial stories off `not` — at a cost on his `no`s

**Date:** 2026-10-09 · **Item:** `work/done/2026-10-09-borderline-definition-test.md`
**Evidence:** rule-informed, **measured** on a chosen subset (not the whole set); one run.
Script: `scripts/compare_borderline_test.py` → `results/consensus/phase1/compare_borderline_test.json`.

**Question.** The judge prompt defined `borderline` as *"the expert's own category (R-C2)"* —
speech with conflict only. Were passages that are partly stories being forced to `not`?

**Change.** New register entry R-C7 (our grouping of ~40 of his borderline verdicts, in his
words: mainly speech but something happens; one event then discussion or a ruling; weak
causality or little change; an incident alluded to) and `judge_register_v2.md`, which points
`borderline` at R-C7 and says *prefer borderline to not*. Everything else as `full_v3_*`.

**Subset (287, 271 scored):** his 41 borderlines, his 157 `no`s, and the 127 passages
Gemini called a story and Claude `not` in v3. 16 passages quoted in the rules excluded.

| his label | Claude v3 → v4 | Gemini v3 → v4 |
|---|---|---|
| yes (89, all Claude-`not` in v3) | not 89 → **not 33, borderline 56** | story 80 / bl 9 → story 38 / **bl 49** / not 2 |
| borderline (29) | bl 5 → **18** (not 12 → 5) | bl 2 → **9** (not 6 → 4) |
| no (153) | not 142 → 128; **bl 7 → 22** | not 112 → 99; **bl 13 → 36** |

| both judges | v3 | v4 |
|---|---|---|
| agree story-vs-not | 143/271 | **193/271** |
| both reject his yes/borderline | 4 | **2** |
| both keep (story/borderline) his `no` | 9 | **19** |

**Reading.** Simon's hypothesis 1 holds: the narrow definition was forcing partial stories to
`not`. With R-C7, Claude moves 56 of the 89 to borderline, both judges find his borderlines
far more often, and the judges agree on 50 more passages. **The cost:** about ten more of his
`no`s are kept as borderline by both. That is the trade Simon has chosen before (recall over
precision) — and borderline-vs-no is exactly the disagreement phase 2 routes to Jeff.
Gemini now over-uses borderline on his `yes`es (49 of 89 here) — on a subset chosen for
being hard, so not a whole-set rate.

**Not done:** the full 997 under v2; a repeat. R-C7 is ours and needs his confirmation.

## v5 — R-C7 narrowed to his later words (`judge_register_v3.md`)

Shape 2 narrowed (one event then discussion is `not` unless something changes, per his
April–October notes) and shape 4 narrowed (named-only incident is `not`). Same 287; scored on
265 (22 quoted passages excluded **for all three runs**), and with three label fixes applied
to all runs: two merge approvals that `verdict_reading` misread as `no` (bug fixed — Ketubot
104a, 8b:6) and Ketubot 7a:1's March `no` superseded by his 2026-09-23 borderline.

| both judges, 265 scored | v3 old | v4 R-C7 | v5 narrowed |
|---|---|---|---|
| agree story-vs-not | 141 | 187 | **195** |
| both reject his yes/borderline | 4 | **2** | 6 |
| both keep his `no` | 5 | 11 | **10** |
| Claude `not` on his yes | 89 | **33** | 47 |

**The narrowing was a bad trade:** it gave back 19 of Claude's recovered stories to save one
`no`. The 19 are the shapes the narrowing named — one act then a ruling, coming before a
rabbi, an incident named in passing — and three of them (Ketubot 54a:22, 60b:7-9, 74a:11) are
passages **he himself** called borderline in February. His own rulings on this shape disagree
across time: borderline in February, `not` from April. That is a question for him, not one to
settle by picking a date. Also: with the label fixes, v4's real cost on his `no`s was +6
(5 → 11), not +10 as first reported.
