# Autoresearch: Improve Talmud Story Detection

## Objective
Maximize composite score on Ketubot golden dataset while maintaining generalizability.

## Current Baseline
- Classification F1: 0.92
- Boundary IoU: 0.98
- Merge F1: 0.86
- **Composite: 0.93**

## What You Can Modify
- `src/story_detector_v7.py` — Stage 2 classification prompt, criteria, rules, examples
- `src/event_triage.py` — Stage 1 event type classifications
- Boundary trimming rules in Stage 4
- Cross-page merge heuristics

## What You CANNOT Modify
- `scripts/evaluate_golden.py` — the evaluation harness (IMMUTABLE)
- `results/canonical/ketubot_canonical.json` — the golden labels (IMMUTABLE)
- `docs/golden/*` — documentation (IMMUTABLE)

## Constraints
1. Do not drop classification_f1 below 0.85
2. Do not drop composite below 0.90
3. Each experiment = one focused change + one commit
4. Run `python3 scripts/autoresearch/run_experiment.py` after each change

## Primary Improvement Targets

### 1. Reduce False Positives (26 currently)
The detector classifies 26 passages as stories that Jeff says are NOT stories.
These are mostly **legal discussions** and **hypothetical scenarios**.

Error patterns (from `docs/golden/error_taxonomy.md`):
- LEGAL_FALSE_POSITIVE (11): Legal debates classified as stories
  - Key: dialogue (asking, objecting, explaining) ≠ narrative events
  - Key: hypothetical scenarios are not stories
  - Key: a rabbi making a ruling is not an event
- CONFIDENCE_MISCALIBRATION (9): Stories at wrong confidence level
  - Key: habitual/repeated actions → LOW, not HIGH
  - Key: require causality for HIGH_CONFIDENCE

### 2. Fix 2 False Negatives
- 8b_3-10: Was split into two stories (3-4 and 6-10) — detector needs to see it as one
- 54b_1-2: Restored from a bad merge — detector doesn't know about it

### 3. Improve Merge Detection (3 missed)
3 of 19 cross-page merges were not detected by the current detector.

## Experiment Ideas (ordered by expected impact)

1. **Add legal discussion disqualifier** to Stage 2 prompt
   - Add few-shot examples of legal-with-setting false positives
   - Strengthen: "dialogue is not events" rule

2. **Add hypothetical scenario detector**
   - "If a man..." / "In a case where..." patterns → NOT_A_STORY

3. **Calibrate confidence thresholds**
   - Require explicit causality chain for HIGH_CONFIDENCE
   - Habitual actions → LOW_CONFIDENCE by default

4. **Improve boundary detection**
   - After narrative arc resolves, look for structural markers (הֵיכִי, מַאי)
   - Trim Talmud analytical commentary

5. **Improve merge detection**
   - Check segment 0 of next page for narrative continuity
   - Look for character name overlap across page boundaries

## How to Run an Experiment

```bash
# 1. Make your change to src/story_detector_v7.py or src/event_triage.py
# 2. Commit with descriptive message
git commit -am "experiment: <description>"
# 3. Run evaluation
python3 scripts/autoresearch/run_experiment.py
# 4. If improved: keep. If not: revert
git reset --hard HEAD~1
```
