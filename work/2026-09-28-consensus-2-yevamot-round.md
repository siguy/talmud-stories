---
title: Consensus 2 — the first Yevamot round with the panel as a router (it sorts Jeff's queue; it clears nothing)
capability: [review, classification]
tractate: [yevamot]
blocked_by: []
awaiting: []
writes: [scripts/pool_runs.py, scripts/route_consensus.py, tests/test_pool_runs.py, tests/test_route_consensus.py, results/consensus/phase2/, validation/ui/, comms/, comms/JEFF.md, scripts/build_yevamot_golden.py, results/canonical/yevamot_canonical.json, tests/test_bookkeeping.py]
finding:
superseded_by:
---

# Consensus 2 — the Yevamot round, panel as router

> **Rewritten 2026-10-02 (Simon's decision).** Phase 1 and 1b were **no-go** under plan §4,
> and §4 is not moved: two models agreeing is **not** good enough to mark a passage done
> without Jeff. What 1b did show (finding §10) is that both kinds of agreed error sit at the
> borderline end: 9 of 444 list stories rejected (2.0% [1.1–3.8]), 4–5 of his 130 `no`s
> accepted (3.1% [1.2–7.6]), and on reading, 2–3 of those 4–5 look like stories his early labels missed.
> So the panel is used to **sort and label**, never to delete or to finalise. Every
> verdict that enters a golden is still his.

**Self-contained.** Read the plan [`consensus-at-scale`](../docs/history/2026-09-28-PLAN-consensus-at-scale.md) §5 (rewritten the same day),
the phase 1 finding §10, and [`comms/JEFF.md`](../comms/JEFF.md). Eruvin untouched.

## Method

1. **Pool** (`scripts/pool_runs.py`) the three same-code Yevamot runs on disk:
   `results/v11/twin_pass/yevamot_full_twinall.json`, `yevamot_full_twin2.json`,
   `yevamot_full_twin2_r2.json`. Union by segment overlap, **not transitively** (test the
   A∩B, B∩C chain). Each candidate: `found_in: k/3`, each run's class (`YES` /
   `LOW_CONFIDENCE` / `NOT_A_STORY`) and span. `mishnah_stories[]` is read and kept as its own
   tier, with a comment saying so. **Every** candidate any run proposed, in any class, is in
   the pool — nothing is filtered here.
2. **Judge** every candidate with phase 1's prompt (unchanged, sha `f13af144f32d`) on both
   arms: Gemini via the API, Claude via `scripts/judge_via_subagents.py` (finding §10a; audit
   the transcripts for cut-off passages before importing).
3. **Route** (`scripts/route_consensus.py`, tested) into four tiers. **No tier deletes.**

   | tier | rule | what happens |
   |---|---|---|
   | `agreed_story` | both `story` (or both `borderline`) | catalogue **candidate**, labelled with both verdicts; a random sample goes to Jeff as audit |
   | `split` | the models differ, or either is `unsure` | goes to Jeff, ranked (below) |
   | `agreed_not_kept` | both `not` | **kept**, with both reasons, flagged; a random sample goes to Jeff as audit. A candidate on his 2005 list is never removed by this tier |
   | `mishnah` | from `mishnah_stories[]` | kept as its own tier (R-C1), not judged as Talmudic |

   Split ranking: first a split where the two models cite **different rules** (the clearest
   signal that a rule is unclear), then fewest `found_in`, then `LOW_CONFIDENCE` before `YES`.
4. **Jeff's page** — axis review UI (already supports scope and quotes), checked in the
   browser: Hebrew + English, story highlighted. **≤35 items**, shuffled together, audit
   items unmarked:
   - ≤25 `split`;
   - 5 drawn at random from `agreed_story`;
   - 5 drawn at random from `agreed_not_kept`.

   Every item asks the one required question (yes / borderline / no / out of scope); the
   extent / confidence disclosure stays optional and independent, as now.
5. **Email draft** in `comms/` (Simon sends). What changed, in one line. Then the one
   question with real cases on both sides, `jeff:report-vs-incident`, now carrying the three
   Ketubot passages he said `no` to in February that read as stories under his July rule
   (50b:4 the orphans before Shmuel; 50a:10 R. Yitzḥak learns at Usha; 111a:23 Ilfa's
   lovesick man). Then `jeff:review-error-rate` and `jeff:scope-edges` as before.
6. **When he answers:**
   - Build `yevamot_canonical.json` (`build_gittin_golden.py` pattern: verdicts first, then
     his list, `label_source` on every entry; **never** a machine verdict). Update
     `GOLDEN_COUNTS`.
   - **Per-tier audit agreement with Wilson intervals**: the live error rate this phase
     exists to measure. It replaces nothing in plan §4; it is the measurement §4 deferred to.
   - **Escalation, fixed now:** if the 5 `agreed_story` audits contain **≥ 2** he rejects, or
     the 5 `agreed_not_kept` audits contain **any** story he accepts as `yes`, that tier goes
     to full review next round, not sampled review.
   - Each disagreement with the panel → a regression case with its edge class (the §10g
     classes: report-vs-incident, scholarly speech, habit, alluded incident, commentary,
     scope). A reason STORY_RULES lacks → a candidate rule in his words.

## Guardrails

- Never tell him which items are audit.
- ≤35 items on the page; the rest wait for the next round, ranked.
- No tier deletes; nothing the panel says enters a golden.
- Blind lists untouched; Eruvin untouched; STORY_RULES, the judge prompt and plan §4 unchanged.

## When done

Finding `docs/findings/<date>-consensus-yevamot-round.md`, `## Outcome`,
`python3 scripts/board.py finish 2026-09-28-consensus-2-yevamot-round`.
