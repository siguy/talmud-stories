---
title: Consensus 1 — test the bet: do two models agreeing mean Jeff agrees?
capability: [classification, review]
tractate: [ketubot, kiddushin, gittin, yevamot]
blocked_by: []
awaiting: []
writes: [scripts/judge_labelled_spans.py, src/prompts/judge_register_v1.md, results/consensus/phase1/, tests/test_judge_labelled_spans.py, requirements.txt]
finding: docs/findings/2026-09-28-consensus-phase1.md
superseded_by:
---

# Consensus 1 — test the bet

**Self-contained.** Read [`FRAMEWORK.md`](../../FRAMEWORK.md), the plan
[`consensus-at-scale`](../../docs/history/2026-09-28-PLAN-consensus-at-scale.md) §1–4 (the go/no-go in §4 was fixed before this ran — do
not move it), and [`docs/STORY_RULES.md`](../../docs/STORY_RULES.md) in full.
**Do not use Eruvin for anything.**

## The claim to test

When `gemini-3-flash-preview` and `claude-opus-5`, each given the rule register, agree
on a passage Jeff has judged, they agree with him — in particular they do not agree on
"story" where he said no.

## Method

1. **Labels.** Reuse `load_reviews()` from `scripts/build_ruler.py` for the four
   labelled tractates, plus the 2005 lists (positives only). Clean, and count what each
   rule removes:
   - exclude `ketubot_review_Simon_-_Test_2026-01-05.json` and Simon's pre-screen;
   - a bare `incorrect` with no readable objection → **unknown**, not *not*;
   - `applies_to: corrected` rows reported separately;
   - one span with two conflicting verdicts → both kept, reported, excluded from scoring;
   - tag each row CIRCULAR (Ketubot, Kiddushin), rule-informed (Gittin, Yevamot), and
     whether its page is cited as a case in STORY_RULES.
   Every source file read is counted and named; an unreadable one is an error (Lesson 38).
2. **The judge.** `src/prompts/judge_register_v1.md`: STORY_RULES rules in his words,
   then the passage (Hebrew + English, segment-indexed) with one segment of context each
   side, marked as context. Answer JSON:
   `{verdict: story|borderline|not|out_of_scope|unsure, rules: [ids], segments: [ints], reason}`.
   Code validates segments are inside the span; an invalid or failed answer is **counted**,
   never scored (Lesson 21 — failure-injection test first, watched fail).
3. **Backends.** Gemini via the project's existing client. Claude via the `anthropic`
   SDK (pin the installed version in `requirements.txt`), model `claude-opus-5`,
   synchronous `messages.create`, structured output via `output_config.format`,
   `stop_reason == "refusal"` counted as a failure. **Read the `claude-api` skill
   before writing this.** `--dry-run` prints call count and estimated cost.
4. **Smoke test first — 20 spans, stop if it fails.** 10 of his \`yes\` and 10 of his \`no\`
   (BLIND-est available: Gittin 2026-09-02 first), both models. Put the answers beside
   his in a table and read it. The one question: **when both models agree, do they call
   a story something he said is not?** If yes on more than 2 of the 10 \`no\`s, stop and
   write that up as the finding. Otherwise continue.
5. **Run** once per backend over every scored span (~300 each). Record model, prompt
   sha, commit. Then **repeat the Gemini run once** to report its own spread (Lesson 43).
6. **Report** (per tractate and pooled, Wilson 95% intervals):
   inter-model agreement; when agreed, agreement with his `no`s and with his `yes`es
   separately; list stories called `not`; on splits, which model sides with him; the
   rules cited in every disagreement with him; failures.

## How you know it worked

The plan's §4 table gives go or no-go. Either is a result; the finding states which,
labelled **indicated**.

## Guardrails

- The detector is not run and not changed. No golden is written.
- The judge prompt carries no verdict on the span it is judging beyond what STORY_RULES
  already quotes; pages STORY_RULES cites are flagged and reported both in and out.

## When done

Finding `docs/findings/<date>-consensus-phase1.md`, `## Outcome`,
`python3 scripts/board.py finish 2026-09-28-consensus-1-test-the-bet`.

## Outcome

**No-go (indicated)** — [`2026-09-28-consensus-phase1`](../../docs/findings/2026-09-28-consensus-phase1.md).

- Two criteria met on the spans both models answered (Ketubot + Gittin): agreement
  **197/235 = 84% [79–88]**; agreed `story` on his `no` **1** (plus 5 agreed `borderline`,
  all R-C2, four on February `no`s that predate the category).
- The list criterion fails: Gemini alone calls **47 of 444** of his 2005 list stories
  `not`; on his review `yes`es Claude followed Gemini's `not` 10 times of 11, so the
  consensus count projects to ~43 against a limit of 2. Both models agree `not` on 10 of
  76 of his review `yes`es. **Why:** the models apply R-C5 (*a bare report is not a
  story*) far more broadly than he does — it is cited in 98 of 229 rule citations on
  answers that disagree with him.
- **Incomplete, and said so:** the Anthropic account ran out of credit after 403 of 997
  Claude calls; Kiddushin, Yevamot and every list story have no Claude answer. The 594
  failed calls are counted as failures, never scored. `run` resumes them. The decision
  does not wait on them (finding §3).
- Gemini repeat: 0 of 359 review verdicts moved. Claude, across two smoke runs: 3 of 20.
- Labels: old verdicts read against the classification he was **shown** — 98 Ketubot
  `no`s, not the ~24 the plan expected. Found on the way: `map_verdict_vocabularies.py`
  reads `correct` as *yes* whatever he was shown (not fixed here).
- Cost: Claude $8.94.
