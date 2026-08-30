# RESUME AFTER /clear — Talmud Story Detection (rewritten 2026-08-30)

You are picking up mid-project after a context clear. **Read this whole file first,
then the documents in "Read these first" before doing anything.** Stay on the
strongest available model — this is nuance-heavy Hebrew/Talmud work.

## Where we are (one paragraph)

The 2026-08-30 session did three things. **(1)** Fixed the Wave 5b runner so a failed
API call can no longer be recorded as a judgment (Lesson 21), guarded by a
failure-injection test. **(2)** Ran Wave 5 on Ketubot for the first time and fixed the
span prompt's broken summary fallback — which turned out to be a null result the old
gate could not even measure. **(3)** Rebuilt the measurement itself: the boundary exam
went from **35 gradeable targets to 249** by mining Jeff's detector-blind 2005 Ketubot
list, and the run-to-run noise floor went from **7 points to zero**. That immediately
overturned two things we believed: Wave 5's benefit is far smaller than the old exam
claimed, and **the two expert sources encode different definitions of where a story
ends** (Lesson 24). Wave 5b is **shelved**, not revived — its trigger condition was
measured on the biased ruler.

## Read these first (in this order)

1. **The ruler rebuild — start here.**
   [`docs/golden/v11/boundary_ruler_rebuild_2026-08-30.md`](../docs/golden/v11/boundary_ruler_rebuild_2026-08-30.md)
2. **The trim asymmetry + the two-rulers problem.**
   [`docs/golden/v11/trim_asymmetry_2026-08-30.md`](../docs/golden/v11/trim_asymmetry_2026-08-30.md)
3. **Lessons 21-24** — failed calls as decisions; noise floors; corrections-only
   exams; two sources / two tasks. [`tasks/lessons.md`](lessons.md)
4. **The Steps 1-2 writeup** (the summary fix and why it measured nothing).
   [`docs/golden/v11/wave5_summary_fix_2026-08-30.md`](../docs/golden/v11/wave5_summary_fix_2026-08-30.md)
5. **The feedback ledger** (open items, and what has never been sent to Jeff).
   [`validation/feedback/jeff_2026-07-06_feedback_ledger.md`](../validation/feedback/jeff_2026-07-06_feedback_ledger.md)
6. **The recall finding** (96% on Ketubot, still the project's biggest number).
   [`docs/golden/workflow/recall_measurement_ketubot_2026-08-28.md`](../docs/golden/workflow/recall_measurement_ketubot_2026-08-28.md)
7. **Wave 6's subject** — Jeff's story criteria.
   [`docs/golden/workflow/jeff_story_definition_criteria.md`](../docs/golden/workflow/jeff_story_definition_criteria.md)

## The measurement stack (know this before quoting any number)

| ruler | targets | covers | what it answers |
|---|---|---|---|
| `tests/expert_boundary_targets_2005.json` | 294 | Ketubot | "are we right in general?" — neutral, catches regressions |
| `tests/expert_boundary_targets_v2.json` | 70 | both | "did we fix the known failures?" — corrections only |
| `tests/expert_boundary_targets.json` | 52 | both | superseded by _v2 |
| `scripts/evaluate_golden.py` | — | both | detection, IMMUTABLE, blind to sub-segment spans |

```bash
python3 scripts/score_boundary_targets.py --by-source \
  --targets tests/expert_boundary_targets_v2.json tests/expert_boundary_targets_2005.json \
  --runs name=path/to/run.json
```

**Never pool the two rulers into one headline** (Lesson 24). Always report `--by-source`.

## THE OPEN DECISION — needs Simon, blocks end-boundary work

Jeff-2005 (building a story index) **keeps** the legal discussion after a story.
Jeff-2026 (reviewing our tool) says **cut it**. Start boundaries agree 7/7; end
boundaries are where they split. Any end-boundary metric can be moved by choosing a
ruler, so **which definition are we building?** Until that is answered:

- `MAX_END_TRIM_CLAUSES = 3` in `src/story_detector_v11.py` is **shipped but
  CONTESTED**. It gains +1 HIT / +2 hit+near on the neutral ruler and costs
  −5/−5 on the corrections ruler. One constant, trivially reversible.

## Next work, in order

1. **Ein Yaakov as a neutral ruler for Kiddushin.** Jeff has no more lists. But Ein
   Yaakov (a 16th-c. compilation of the Talmud's non-legal passages) **is on Sefaria
   with full Hebrew, including Kiddushin** — verified 2026-08-30 via
   `api/texts/Ein_Yaakov,_Kiddushin.1`. Its unit is looser than "story" (the first
   Kiddushin entry includes Mishnah and a grammatical discussion), so **validate it
   against Jeff's 149 Ketubot boundaries first**; deploy only if it agrees. This is the
   only route to a neutral ruler for any tractate beyond Ketubot.
2. **Read the 33 remaining MISSes** on the neutral ruler. Today's best change came from
   reading the regression list, not from model work. Expect the same again.
3. **Fix the real over-cutting bug.** Ketubot 62a and 105b discard a whole *second*
   story sharing a segment. Detection-shaped; same family as the open multi-story item
   (Kiddushin 12a). The principled guard is *never trim away a clause that is itself
   narrative* — see "Wave 5b salvage" below.
4. **Wave 6** ([`tasks/PLAN_wave6.md`](PLAN_wave6.md)) — encode Jeff's story criteria.
   Untouched by today's findings and now the most valuable *model* work: it is about
   detection, and half the measured recall misses are the halakhic-story shape his
   criteria call a story.
5. **Small cleanup:** the corrections set has 3 contradictions and 4 duplicates. Only
   **Ketubot 104b** is a genuine two-round disagreement needing a human; Ketubot 103b
   and 67b are harvester artifacts (67b is the same judgment written once in Hebrew and
   once in English). The Kiddushin 12b contradiction the old review flagged was the
   `quote_polarity` bug and is now resolved.

## Wave 5b — SHELVED, and what to salvage

Its trigger was "revive if a properly-fed run stalls near 50%". The real number is
**81% against an ~87% ceiling** (13% of Jeff's boundaries do not sit on a clause edge,
so no prompt can reach them). Six points of reachable headroom does not justify 433
lines. Full review: [`docs/golden/v11/wave5b_review_2026-08-30.md`](../docs/golden/v11/wave5b_review_2026-08-30.md).

**Keep:**
- `is_speech` — Wave 6 needs it for Jeff's speech-act question; independent of boundaries.
- The `variant` rule (`אִיכָּא דְּאָמְרִי` = an alternative telling of the SAME story, keep it).
  Jeff stated this at Kiddushin 22b_18 and both Wave 5 models got it wrong. One sentence
  in the span prompt, no taxonomy required.
- The `comment` heuristic, verbatim: *"narrative tells you what happened, comment
  discusses what happened."* Portable straight into the v11 span prompt.
- **A one-role labeller as a trim GUARD** (item 3 above) — "is this clause narrative?"
  used to veto a trim, not to compute the boundary. This is the elegant form of the
  contested depth cap, and it is now testable because the ruler is stable.

**Drop:** the 8-role taxonomy (`assemble()` reads only 2), English labelling and
`covers` (the nesting premise is false on 21% of segments), the second assembly rule,
and the separate labels artifact.

## Guardrails (do not violate)
- New detector work = **new versioned file**; never edit v10 in place.
- `scripts/evaluate_golden.py` is **immutable**.
- Never few-shot on the tractate you're evaluating (Lesson 2).
- Regenerate today's baseline before comparing (Lesson 11).
- Never ask an LLM for a character offset (Lesson 16).
- Measure a defect's corpus-wide rate before planning the fix (Lesson 18).
- A failed call must never carry a success provenance (Lesson 21).
- Run the same code twice before attributing a score change (Lesson 22).
- A corrections-only exam cannot show a regression (Lesson 23).
- Two expert sources may encode two different tasks — report separately (Lesson 24).
- Append new Jeff feedback to the ledger FIRST (Lesson 17).
- **Do not reply to Jeff yet** — Simon decides when and what to send.

## Still open in the ledger
Add the 5 expert-list stories missing from the Ketubot golden; investigate Ketubot 77a
(in golden, missed by v10); fix the review-UI Hebrew/English trim asymmetry;
segment-boundary + cross-page pass (8a, 8b_14, 20a); multi-story dedup (12a); design
the crowd-sourced DB using Jeff's own 2005 schema (מיקום / טקסט / מקבילות / הערות);
draft the reply to Jeff.
