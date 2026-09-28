---
title: Consensus C — the rule panel: one narrow judge per rule, two model families
capability: [classification, boundaries]
tractate: []
blocked_by: [2026-09-28-consensus-a-calibration-set]
awaiting: []
writes: [src/consensus/, src/prompts/judges/, scripts/run_rule_panel.py, tests/test_rule_panel.py, requirements.txt, results/consensus/panel/]
finding:
superseded_by:
---

# Consensus C — the rule panel

**Self-contained.** Read [`FRAMEWORK.md`](../FRAMEWORK.md), the plan
[`consensus-at-scale`](../docs/history/2026-09-28-PLAN-consensus-at-scale.md) §3b, and [`docs/STORY_RULES.md`](../docs/STORY_RULES.md)
in full. Blocked on A because the precedent list and the held-out set are fixed there.

## What to build

1. **Judges** (`src/prompts/judges/<judge>.md`, versioned like `clause_roles_v*.md`):
   J-actual, J-event, J-conflict, J-report, J-custom, J-commentary, J-scope, J-bounds
   (plan §3b table). Each carries only its rule, Jeff's words with date, and his precedent
   cases from STORY_RULES — **never a case from a held-out page**. Output schema:
   `{answer: yes|no|unsure, segments: [int], quote_he: str, reason: str}`. Segments are
   indices into the passage shown; `quote_he` must be a substring of those segments
   (validated in code — Lesson 16).
2. **Decision table** (`src/consensus/decide.py`): judges' answers → `story` /
   `borderline` / `not` / `out_of_scope` / `unsure`. Every row cites the STORY_RULES
   rule it implements. Unit-tested on every precedent case in the register (their
   verdicts are known).
3. **Two backends** (`src/consensus/backends.py`):
   - Gemini: the project's existing client and default model.
   - Claude: `anthropic` SDK, model **`claude-opus-5`** (Simon, 2026-09-28). Batch API
     (`client.messages.batches`) for full runs; judge prompt as a cached prefix
     (verify `usage.cache_read_input_tokens` > 0); structured output via
     `output_config.format`; adaptive thinking; handle `stop_reason == "refusal"` as a
     counted failure. Read the `claude-api` skill before writing this file.
   - A failed or unparseable answer is **counted** on the run, never read as `no`
     (Lesson 21). Failure-injection test first, watched fail.
4. **Runner** (`scripts/run_rule_panel.py`): pool file in → per-candidate, per-judge,
   per-backend answers + both decisions out, to `results/consensus/panel/`. `--dry-run`
   prints the call count and an estimated cost with no calls.

## Pilot before the full run

On 20 held-out candidates: effort level for Claude (low / medium / high) and the cost per
candidate, both measured. Pick the lowest effort whose answers match the higher one on
the pilot; record the choice and the numbers. **Then** run the full pools from phase B
(or the existing `results/v11/twin_pass/yevamot_full_twin2*.json` if B is not done).

## How you know it worked

Plan §5 gate C: zero uncounted failures; every answer cites a real segment and a real
Hebrew substring; the decision table passes every precedent.

## Guardrails

- No judge sees the 2005 lists or any verdict on the page it judges.
- Adding `anthropic` to `requirements.txt`: pin the installed version.
- The detector's own prompts and defaults are not touched.

## When done

Finding `docs/findings/<date>-rule-panel.md` (mechanics, pilot, cost), `## Outcome`,
`python3 scripts/board.py finish 2026-09-28-consensus-c-rule-panel`.
