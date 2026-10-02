---
title: Rule panel — split "is it a story?" into one narrow question per feature, then decide in code; does it match Jeff better than the single question?
capability: [classification, review]
tractate: [ketubot, kiddushin, gittin, yevamot]
blocked_by: []
awaiting: []
writes: [src/consensus/, src/prompts/judges/, scripts/run_rule_panel.py, tests/test_rule_panel.py, results/consensus/panel/, docs/findings/2026-10-02-rule-panel-lenses.md]
finding:
superseded_by:
---

# Rule panel — one question per feature, a decision table in code

**Self-contained.** Read [`FRAMEWORK.md`](../FRAMEWORK.md), then
[`docs/STORY_RULES.md`](../docs/STORY_RULES.md) in full, then the consensus finding
`docs/findings/2026-09-28-consensus-phase1.md` §7 and §10, then the plan
`docs/history/2026-09-28-PLAN-consensus-at-scale.md` §9. Eruvin untouched.

## The claim to test

Today both models answer one question, *is this a story?*, with the whole register in the
prompt: **one lens, two readers**. When they are wrong we learn only which rule they cited.
1b's errors (finding §10g) all fall on a handful of features: *something happened once*,
*someone responds / something follows*, *speech only (with or without conflict)*, *a habit*,
*an incident only alluded to*, *the Gemara's commentary*, *scope*. **Claim:** asking each
feature as its own narrow question and computing the verdict from the answers in code
(a) matches Jeff at least as well as the single question, and (b) says *which feature*
every disagreement is about, which is what a question to Jeff needs.

This was designed on 2026-09-28 (`consensus-c-rule-panel`, in git at `e2b6d1e^`) and cut
by that day's review: *"decompose only where a rule fails."* 1b now shows which rules fail.

## Method

1. **Judges** (`src/prompts/judges/<judge>_v1.md`), each carrying only its rule, Jeff's words
   with date, and his precedent cases from STORY_RULES, never a case from the page being
   judged:

   | judge | question | rule |
   |---|---|---|
   | J-actual | Does it narrate something that happened, not a hypothetical or a legal case? | R-C0 |
   | J-event | Beyond speech, does something happen? (*sent a question, responded* = speech) | R-C2 |
   | J-conflict | If speech only: is there conflict? | R-C2 |
   | J-response | Does someone respond, or does something follow the act? | R-C0 / R-C5 |
   | J-custom | Is it a custom? Does a one-time event follow? | R-C3 |
   | J-allusion | Is the incident narrated, or only alluded to? | R-C5 (our line; flag it) |
   | J-commentary | Is this the Gemara commenting on a story told elsewhere? | R-B4 |
   | J-scope | Are the actors biblical figures? | R-S1 |

   Output per judge: `{answer: yes|no|unsure, segments: [int], quote_he: str, reason: str}`;
   `quote_he` must be a substring of the cited segments, checked in code (Lesson 16).
2. **Decision table** (`src/consensus/decide.py`): answers → `story` / `borderline` / `not`
   / `out_of_scope` / `unsure`. Every row cites the rule it implements; rows that encode
   **our** proposals (the allusion line, "a custom stays a custom") are marked as ours.
   Unit-tested on every precedent case in STORY_RULES (their verdicts are known).
3. **Two arms, as in 1b:** Gemini via the API; Claude via `scripts/judge_via_subagents.py`
   style batches (one batch file per span carrying all eight questions). Transcript audit for
   cut-off passages before import. Failures counted, never scored (Lesson 21).
4. **Score on the same 997 units** (`results/consensus/phase1/labels.json`), with
   `compare_consensus_1b.py`'s measures, side by side with 1b's single-lens numbers: the
   §4 criteria, per-stratum agreement, his `no`s called `story`, his list stories called
   `not`, and run-to-run spread from one repeat per arm.
5. **The per-feature table:** for every unit where the panel disagrees with him, the judge
   whose answer flipped the decision. That table is the input to
   `2026-10-02-jeff-feature-questions`.

## How you know it worked

The claim holds only if both are true, judged on the same units:
- the panel's agreed errors (his `no`s called `story`, his list stories called `not`) are
  **no higher** than 1b's single lens, beyond the measured spread; and
- ≥ 80% of its disagreements with him trace to **one** judge (attributable, not diffuse).

Report it **same-data / indicated**: the precedents and these labels overlap.

## Guardrails

- No judge sees the 2005 lists, any verdict, or a span id (a `list:` id is the label).
- The decision table encodes stated rules only; a threshold fitted to these labels is
  forbidden (Lesson 37). Changing a row after seeing the scores is reported both ways.
- STORY_RULES, the single-lens judge prompt and plan §4 unchanged. No detector default touched.

## When done

Finding `docs/findings/2026-10-02-rule-panel-lenses.md`, `## Outcome`,
`python3 scripts/board.py finish 2026-10-02-rule-panel-lenses`.
