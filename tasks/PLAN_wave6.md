# Wave 6 Plan — Story-definition criteria (SPLIT: measure → ask Jeff → implement)

**Status:** Phase 6a executable now. **6c is BLOCKED on Jeff's answer — by design.**
**Restructured 2026-08-29** after an audit found that the original plan's core
justification was half wrong and that it would silently redefine ~40% of the golden.

---

## Why this wave is split

Jeff gave us a sharp story-definition rule on 2026-07-06
([criteria](../docs/golden/workflow/jeff_story_definition_criteria.md)). Encoding
it looks like a prompt change. It isn't — it is a **question about what the dataset
means**, and we cannot answer it for him. Two findings force the split.

### Finding 1 — Jeff's 2026-07-06 rule contradicts Jeff's 2026-03-17 rulings

Both are his. Neither is wrong. They cannot both be mechanically applied.

| 2026-03-17 (the 187-review corpus behind [error_taxonomy.md](../docs/golden/workflow/error_taxonomy.md)) | 2026-07-06 ([criteria](../docs/golden/workflow/jeff_story_definition_criteria.md)) |
|---|---|
| *"There is only one action followed by a legal ruling"* → **not a story** | *"A man stole another man's cow and sold it. Rava ruled…. In this case you may have a story."* |
| *"The actions mentioned in the reasoning, 'stating, objecting, asking questions' are all part of a dialogue, and not really events."* | *"speech-acts don't count… minimally there must be some action beyond the speech"* — implying speech **plus** action qualifies |
| *"Low confidence. It is mostly a legal case. The action 'explaining' is dialogue, not really an action."* → **LOW_CONFIDENCE, still a story** | the same passage type now reads as **not a story at all** |

LEGAL_FALSE_POSITIVE is the project's **largest error category (11 instances, 21%)**.
Relaxing the rule that suppresses it, to recover 1–2 false negatives, is a trade that
must be argued and measured — not assumed.

### Finding 2 — the blast radius is ~40% of the golden, not a short list

| | Total stories | LOW_CONFIDENCE |
|---|---|---|
| Ketubot golden | 182 | **77 (42%)** |
| Kiddushin golden | 96 | **33 (34%)** |

Per the taxonomy, *"mostly dialogue with minimal physical action → LOW_CONFIDENCE"*
is Jeff's **existing applied policy**: such passages are stories, just weak ones. His
new rule says speech-acts are not stories at all. The rule therefore points directly
at a bucket holding **110 of 278 golden stories**. That is a redefinition of the
dataset, and it is his call, not ours.

### Finding 3 — the original plan mis-attributed its own evidence

Wave 6 was justified on recovering Ketubot 20a and 77a as criteria failures. **20a's
page was never processed** — both 19b and 20a were skipped by triage, so Stage 2
never saw it. Of the 6 known recall misses:

| Miss | Responsible stage | Fix belongs to |
|---|---|---|
| 20a, 72b, 82b | **TRIAGE** — page never processed | triage recovery (no criteria change can help) |
| 67b | Stage 2 — opener `אמרו עליו` outside lexicon | [Wave 7](PLAN_wave7.md) |
| 53a, 77a | Stage 2 — plausibly criteria | **this wave** |

Realistic criteria payoff: **1–2 stories**, not 3. That is Lesson 12 — audit the
evidence at the granularity the mechanism operates on.

---

## Phase 6a — Measure the blast radius (NO Jeff, ~$0.10)

Classify each of the 110 LOW_CONFIDENCE golden stories on one axis only:
**does anything non-speech happen?** (physical action, movement, state change, or an
emotional/internal reaction — which Jeff says *does* count).

- Output: `results/criteria/speech_act_blast_radius.json` + a human-readable table.
- Deliverable to Jeff: *"N stories currently in your golden would be demoted by your
  new rule. Here are examples."*
- This is a **measurement**, not a relabeling. Nothing in the golden changes.
- Use abstract criteria in the prompt, never the specific passages (Lesson 8).

## Phase 6b — Ask Jeff (the ONLY thing here needing his input)

Present the contradiction **in his own words**, side by side, with the count from 6a
and 3–4 concrete examples. Then one question:

> Passages where rabbis only speak — no action, no emotional reaction — are currently
> **LOW_CONFIDENCE stories** in the database, per your 2026-03-17 reviews. Your newer
> rule reads as **not stories at all**. There are N of them. Should they become
> NOT_A_STORY, stay LOW_CONFIDENCE, or get a new **borderline** status that the
> database surfaces rather than decides?

Frame it as a decision his data forces, not as an inconsistency to defend. His own
crowd-sourcing answer (keep contested cases, flagged) suggests he may well pick
`borderline` — but he chooses.

## Phase 6c — Implement (BLOCKED until 6b is answered)

Fork v11 → v12. Then:

1. Promote **hypothetical vs. actual** to the primary test; demote "has physical
   action" to a secondary signal.
2. Replace the blanket anti-legal disqualifier with the mixed-case rule (real event +
   ruling = story), **and measure the FP regression on the legal bucket in the same
   run** — recovery and regression are one trade, reported together.
3. Apply Jeff's 6b answer to the speech-act policy; emit a `borderline` flag if he
   chooses that.
4. Count emotional/internal reactions as qualifying events.

**Rollback discipline (Lesson 5: a prompt rewrite once cost 0.93 → 0.57):**
git checkpoint before the first prompt edit; **hard abort if either composite drops
> 0.02** below the same-day baseline; revert rather than iterate blindly.

**Approach note (Lesson 7):** a post-hoc classifier is the safer instrument for
false positives and *can never create new false negatives* — but it also **cannot
recover false negatives**, which is what this wave is for. So the two are separate
jobs and must not be bundled into one prompt. The FP classifier proceeds independently
and is not blocked on Jeff.

## Gates

| Gate | Threshold |
|---|---|
| Conformance set, **per axis** | beats v10 baseline on every axis (no averaging away a regression) |
| Legal-FP bucket | no net increase in NOT_A_STORY misclassification |
| Both composites, regenerated today | within 0.02, **both Ketubot ranges + Kiddushin** (Lessons 6, 11) |
| Recall vs Jeff's 2005 list | ≥ current; ideally recovers 53a/77a |
| Held-out | develop on Ketubot, gate on Kiddushin (Lesson 9) |

The conformance set is **TEST-ONLY and never few-shot material** (Lessons 2, 8).

Lesson 13/14 applies: if composite falls while conformance and expert-list recall
rise, that is a win and must be argued explicitly, not silently "fixed."

## Cost

6a ≈ $0.10. 6c ≈ $1–2 (re-detection per tractate at ~$0.30–0.60, plus gate re-runs).
