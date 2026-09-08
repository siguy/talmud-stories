---
title: Tighten the story finder on quasi-speech-acts, then re-run for the score
capability: [detection, classification]
tractate: [ketubot, kiddushin, gittin]
blocked_by: []
awaiting: []
writes: [src/story_detector_v11.py, src/speech_act_lexicon.py, src/prompts/, results/v12/, tests/]
finding:
superseded_by:
---

# Tighten the story finder on quasi-speech-acts, then re-run for the score

**Self-contained.** Read [`FRAMEWORK.md`](../FRAMEWORK.md) §1.2–1.3, then
[`the span confound finding`](../docs/findings/2026-09-03-quasi-speech-acts-and-the-span-confound.md),
then this.

**Simon, 2026-09-03, resolving `which-tightening`:** *"Story finder — tighten it per what I
suggested. Then rerun it so we can see the actual score."* The tightening is the
quasi-speech-act rule. It is **not** the recall aligner's window, which is a scoring defect
handled by [`loose-credited-proposals`](2026-09-03-loose-credited-proposals.md) and needs
no run.

## What is being tightened

Jeff, 2026-09-02: *"words like 'retracted,' 'considered,' 'responded' and even 'sent'
(when what he sends is a message or question) should not be evaluated as actions for our
purposes, or those sources require extra scrutiny."*

The detector's Stage 2 currently asks for *"≥2 NARRATIVE events (physical actions, not
talk/deliberation)"* ([`src/story_detector_v11.py:191`](../src/story_detector_v11.py)) and
lists disqualifiers in prose. **Nothing distinguishes a verb from its object**, so
*sent a question*, *retracted an opinion*, *came before* and *brought the case* all read as
actions. This was measured: an earlier screen cleared entries citing exactly those verbs.

## The design decision that makes this safe — demote, never delete

**This change can only remove stories. Recall can fall and cannot rise.** That runs against
the project's stated priority, which is finding stories Jeff's 2005 list missed. So it
ships as a **confidence demotion, not a rejection**:

- a passage whose only "actions" are tier-2 quasi-speech-acts, with no tier-3 event,
  **drops one confidence band** — `YES`→`HIGH`, `HIGH`→`LOW`
- it does **not** become `NOT_A_STORY`, and it is **never removed from the output**

Recall is then untouched **by construction**, the score still moves, and Jeff still sees
every passage — he just sees it ranked lower. This is also the only defensible home for the
"weaken the confidence" half of his proposal: the model's own `confidence` field came back
`high` on 110 of 110 and carries no signal, so the demotion must be structural and computed
outside the model.

**If a later measurement shows demotion is not enough, hard rejection is a separate item
and needs Jeff's ruling** (Wave 6b, drafted and unsent).

## Method

1. **Fork v11 → v12.** v7–v11 are frozen; earlier runs must stay reproducible.
2. **Prompt.** Feed the three tiers from
   [`src/speech_act_lexicon.py`](../src/speech_act_lexicon.py) into the Stage 2 criteria as
   **abstract patterns, never as Jeff's specific passages** (Lesson 8). The rule is *judge
   the object, not the verb*: sending a messenger is an event, sending a question is not;
   retracting a get is an event, retracting an opinion is not.
3. **Post-processing demotion**, deterministic, outside the model: tier-2 verb present AND
   no tier-3 physical or emotional event → drop one band. Emotional and internal reactions
   count as events, per Jeff's 2026-07-06 rule.
4. **Guard the span confound first.** 9 of 13 candidate demotions flipped to "something
   happens" when the span was extended by two segments — the demotion rule must read the
   **two following segments** as context, or it will punish our own truncated boundaries
   rather than the passage. This is not optional; it is the single largest source of false
   demotions measured so far.
5. **Then re-run.** Ketubot, Kiddushin, Gittin, one manifest, one model. See
   [`rerun-all-tractates`](2026-09-03-rerun-all-tractates.md) for the run protocol — this
   item supplies the change; that one supplies the discipline.

## How you know it worked

Against a **same-day** v11 baseline (Lesson 11), both arms sharing cached triage so the
only variable is the change:

| | expected | abort if |
|---|---|---|
| blind recall, all three lists | **unchanged** — demotion cannot lose a story | it moves at all → the demotion is deleting, fix it |
| classification precision, CIRCULAR | rises | flat → the rule is not firing; report that |
| Gittin 18 known negatives | demoted | fewer than half → the rule does not capture what Jeff described |
| Gittin 3 known discoveries — 19a:16, 43b:4, 70a:22 | **not demoted** | any demoted → it is eating exactly the stories we exist to find |

**That last row is the real test.** All three accepted discoveries are `LOW_CONFIDENCE`
already. A rule that demotes them is worse than no rule, whatever it does to precision.

Run each arm at least twice (Lesson 22) — a story on this corpus has been observed proposed
in 7 of 8 identical runs.

## Guardrails

- **Never removes a proposal from the output.** Only reorders confidence.
- The Gittin 25 verdicts are TEST-ONLY, never few-shot (Lessons 2, 8).
- No golden is rebuilt. `build_canonical.py` refuses non-additive writes; leave it that way.
- Hard abort if either composite drops >0.02 below the same-day baseline (Lessons 5, 11).

## When done

Finding to `docs/findings/<date>-tighten-story-finder.md`, `## Outcome` here, then
`python3 scripts/board.py finish tighten-story-finder`.
