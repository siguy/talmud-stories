# RESUME AFTER /clear — Talmud Story Detection (rewritten 2026-08-28)

You are picking up mid-project after a context clear. **Read this whole file
first, then the documents in "Read these first" before doing anything.** Stay on
the strongest available model — this is nuance-heavy Hebrew/Talmud work.

## Where we are (one paragraph)

**Where Wave 5 got to:** clause-anchored spans are built (`src/story_detector_v11.py`),
A/B'd across two models, and eliminate mid-word cuts entirely — but agree with Jeff's
stated boundaries only ~50% of the time. Wave 5b (below) is the judgment layer on top.

Wave 4 (v10) shipped LLM **character-offset** text boundaries. A full audit on
2026-08-28 proved them systematically broken: **104 of 189 cuts (55%) sever a
Hebrew word**, and of the 9 trimmed stories Jeff Rubenstein reviewed, **9 of 9
were wrong** — the mechanism had zero observed successes. **The spans are now
reverted and shipped** (`results/v10/wave4_notrim/`), score-neutral and verified
(0.9171 → 0.9171). Separately and more importantly: Jeff's **2005 Ketubot story
list** (`jeff comms/b.ketubot (1).doc`, 149 stories, genuinely detector-blind)
was parsed and used to measure **true recall for the first time — 96.0%**, far
better than the 80–85% the roadmap assumed. The 6 misses cluster into three
shapes, half of them the halakhic-story-plus-ruling case Jeff's own criteria say
*is* a story. **Next job: Wave 6** — encode Jeff's criteria. Wave 5 (clause
boundaries) is deprioritized; nothing corrupt is live. Nothing has been sent to
Jeff yet.

## Read these first (in this order)

1. **The feedback ledger — START HERE** (read the 2026-08-28 status banner at top).
   [`validation/feedback/jeff_2026-07-06_feedback_ledger.md`](../validation/feedback/jeff_2026-07-06_feedback_ledger.md)
2. **The recall finding — the project's biggest number.**
   [`docs/golden/workflow/recall_measurement_ketubot_2026-08-28.md`](../docs/golden/workflow/recall_measurement_ketubot_2026-08-28.md)
3. **The span failure audit + revert.**
   [`docs/golden/v10/wave4_span_failure_audit_2026-08-28.md`](../docs/golden/v10/wave4_span_failure_audit_2026-08-28.md)
4. **The plan to execute.** [`tasks/PLAN_wave6.md`](PLAN_wave6.md)
5. **Jeff's story criteria (Wave 6's subject).**
   [`docs/golden/workflow/jeff_story_definition_criteria.md`](../docs/golden/workflow/jeff_story_definition_criteria.md)
6. **Lessons** — especially 9 (fixture ≠ production), 11 (regenerate baselines),
   13 (score can drop when quality rises), 16 (no char offsets), 18 (measure the
   whole corpus, not the expert's sample), 19 (revert beats a better broken
   feature). [`tasks/lessons.md`](lessons.md)

### Jeff's raw inputs
- [`jeff comms/b.ketubot (1).doc`](../jeff%20comms/b.ketubot%20%281%29.doc) — **his 2005 Ketubot story list; 149 stories; detector-blind ground truth**
- [`jeff comms/wave4_kiddushin_review_2026-07-06.json`](../jeff%20comms/wave4_kiddushin_review_2026-07-06.json) — 15 verdicts
- [`jeff comms/Simon Brief Questions.docx`](../jeff%20comms/Simon%20Brief%20Questions.docx) — Part 2 strategic answers

### Tools built this session (all run free, no LLM)
```bash
python3 scripts/audit_text_spans.py --strict results/v10/wave4_notrim/*.json
```
```bash
python3 scripts/measure_recall_vs_expert_list.py --expert-doc "jeff comms/b.ketubot (1).doc" --detected results/v10/wave4_notrim/ketubot_v10_2-60_notrim.json results/v10/wave4_notrim/ketubot_v10_61-112_notrim.json --golden results/canonical/ketubot_canonical.json --out results/recall/ketubot_jeff2005_matches.json
```

## THE IMMEDIATE TASK: fix measurement + correctness. **Do NOT run Wave 5b yet.**

Wave 5b (clause-role labelling) is built but **ON HOLD**. Three independent reviews on
2026-08-30 converged: the core idea is right, but (a) two correctness bugs make failed
API calls indistinguishable from real judgments, (b) the gate cannot measure what the
wave would be judged on, and (c) the incumbent it replaces has never been run without a
known handicap. Full findings as a fix list (use this to revive Wave 5b if the cheap path fails):
[`docs/golden/v11/wave5b_review_2026-08-30.md`](../docs/golden/v11/wave5b_review_2026-08-30.md).
Plain-language why:
[`docs/golden/v11/wave5b_decision_2026-08-30.md`](../docs/golden/v11/wave5b_decision_2026-08-30.md).

**If you only read one thing:** a totally failed run currently scores 6% HIT / 38%
HIT+NEAR — identical to the legitimate no-trim baseline — and stamps every story
`clause_kept_full`, which means "the model judged all of this in-story." See Lesson 21.

### Step 0 — correctness (no API calls, own commit)

In `scripts/run_clause_labeling.py`: on failure write `text_span_source='skipped'` and
set `needs_review`; never write a fabricated `speech_profile`; exactly one counter per
story (`no_clause_split` currently double-counts and its provenance is overwritten);
extract one `emit_span()` shared by `main()` and `reassemble()`, which have diverged.
Write the failure-injection test FIRST — stub the model to raise, then assert no story
gets a success provenance and `sum(counts.values()) == stories_labelled`.

### Step 1 — triple the evidence base (2 commands, pennies)

29 of the 52 expert targets are Ketubot, and Wave 5 was never run on Ketubot. Both
inputs are already on disk.

```bash
python3 scripts/run_wave5_clause_spans.py --in results/v10/wave4_notrim/ketubot_v10_2-60_notrim.json --out results/v11/wave5/ketubot_2-60_v11_g37high.json --model gemini-3.7-flash --thinking high
```
```bash
python3 scripts/run_wave5_clause_spans.py --in results/v10/wave4_notrim/ketubot_v10_61-112_notrim.json --out results/v11/wave5/ketubot_61-112_v11_g37high.json --model gemini-3.7-flash --thinking high
```
```bash
python3 scripts/score_boundary_targets.py --runs kid=results/v11/wave5/kiddushin_v11_g37high.json ket2_60=results/v11/wave5/ketubot_2-60_v11_g37high.json ket61=results/v11/wave5/ketubot_61-112_v11_g37high.json
```

### Step 2 — fix the incumbent's handicap (one line), then re-score

`src/story_detector_v11.py`, `_llm_text_span_for_story`: the prompt reads
`story['summary']`, present on **0 of 95** stories, so it falls back to a joined events
list that **drops the story's resolution** — while **35 of 52 targets are END
boundaries**. Put `one_sentence_summary` first in the fallback chain. Then re-run
Step 1 and compare. Also add the English text and `classification_reasoning` to that
prompt as CONTEXT (~6 lines) — no labels, no `covers`.

### Step 3 — the human hour that makes every number mean something

Anchor-verify [`tests/expert_boundary_targets.json`](../tests/expert_boundary_targets.json):
resolve the 2 contradictions (Ketubot 67b seg15 wants 5 AND 6; Kiddushin 12b seg4 wants
0 AND 1 — a perfect run currently scores 50/52), merge the 3 duplicates, and set
`quote_polarity`/`anchor_verified` by reading each note. 23 `include` / 10 `exclude` /
5 `mixed` / 14 `unclear` today, none verified.

### Step 4 — only if a properly-fed one-shot still stalls near 50%

Then Wave 5b earns its place, cut down: **3 roles (`story`/`not_story`/`unclear`) +
`is_speech`, Hebrew only, one assembly rule.** Change one thing at a time — as built it
alters taxonomy, adds an English channel and adds an assembly choice simultaneously,
judged on ~14 effective cases, so nothing would be attributable.

## Guardrails (do not violate)
- New detector work = **new versioned file** (`story_detector_v11.py`); never edit
  v10 in place (memory `feedback_detector_versioning.md`).
- `scripts/evaluate_golden.py` is **immutable**.
- Never few-shot on the tractate you're evaluating (Lesson 2).
- Regenerate today's baseline before comparing (Lesson 11).
- Never ask an LLM for a character offset (Lesson 16).
- Measure a defect's corpus-wide rate before planning the fix (Lesson 18).
- Append new Jeff feedback to the ledger FIRST (Lesson 17).
- **Do not reply to Jeff yet** — walk the ledger's open-items tracker; Simon
  decides when and what to send.

## Open items after Wave 6 (tracked in the ledger)
Ask Jeff which **other tractates** he has lists for (highest value / lowest cost);
add the 5 expert-list stories missing from the Ketubot golden; investigate Ketubot
77a (in golden, missed by v10); fix the review-UI Hebrew/English trim asymmetry;
Wave 5 clause boundaries; segment-boundary + cross-page pass (8a, 8b_14, 20a);
multi-story dedup (12a); design the crowd-sourced DB using Jeff's own 2005 schema
(מיקום / טקסט / מקבילות / הערות); draft the reply to Jeff.
