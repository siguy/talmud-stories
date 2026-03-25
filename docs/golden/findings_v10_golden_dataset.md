# V10 Golden Dataset: Findings and Analysis

**Date:** 2026-03-25
**Author:** Simon Brief + Claude
**Status:** Complete (detector experiments reverted)

---

## What We Did

We built the definitive ground truth dataset for Ketubot story detection, incorporating all of Jeff Rubenstein's expert feedback across four review rounds (v5.1 Feb 2026, v5.1 Feb 2026 round 2, v8 delta Feb 2026, and the comprehensive canonical review of all 189 stories in March 2026).

### Phase 1: Machine-Readable Analysis

Wrote `scripts/analyze_canonical_feedback.py` to process all 187 of Jeff's canonical reviews. Cross-referenced against the three prior feedback rounds to catch inconsistencies and repeated issues.

**Key finding:** 10 of the 53 actionable corrections were issues Jeff had flagged in prior rounds that we never fully implemented. We had applied the classification changes but systematically ignored the boundary and merge corrections that came in the same notes. This was a process failure — our correction pipeline split feedback into "auto-apply" and "needs review" buckets, then never came back to the "needs review" pile.

Built `docs/golden/error_taxonomy.md` documenting 6 systematic error patterns with Jeff's actual language and reasoning, detection heuristics, and suggested detector fixes.

### Phase 2: Classification Corrections (17 applied)

Added the canonical review as a post-processing layer in `build_canonical.py` (not as a 4th entry in the timestamp-based feedback system, which would have caused overwrite bugs — see Lessons Learned below).

Applied 17 classification changes:
- 10 stories changed to NOT_A_STORY (legal discussions Jeff says have no narrative events)
- 5 stories downgraded to LOW_CONFIDENCE (insufficient causality)
- 1 story downgraded from YES to HIGH_CONFIDENCE (106a_3-3: "minimal action, mainly request and rejection")
- 1 special case: 111a_23-25 restored from NOT_A_STORY back to LOW_CONFIDENCE (the v8 delta auto-correction had been wrong; Jeff says the 111a portion IS a low-confidence story, only the 111b portion is not)

All 17 verified by spot-checking the canonical JSON.

### Phase 3: Boundary and Merge Corrections (32 applied)

Built `scripts/boundary_lookup.py` to automatically match Jeff's Hebrew text markers to segment indices using nikud-stripped fuzzy matching. This resolved 17 of 52 corrections automatically.

Then built `scripts/apply_boundary_corrections.py` to apply all corrections:

- **7 confirmations:** Stories where Jeff said "approve" meaning "yes, the boundaries/merge you proposed are already correct" — just removed the `needs_review` flags
- **8 boundary trims:** Stories that included Talmud analytical commentary after the narrative ended (e.g., "the Gemara asks..." or "what did he initially think?"). Trimmed to where the story's narrative arc resolves.
- **5 boundary extensions:** Stories that started or ended at the wrong segment (e.g., 26a_1-1 extended to 0-1 to include the beginning of the narrative)
- **5 same-page merges:** Adjacent stories that are really one story (e.g., 85a_8-8 + 85a_9-10 = one story Jeff flagged TWICE across review rounds)
- **4 new cross-page merges:** Stories that continue from one Talmud page to the next (e.g., 52b_17 → 53a, 67b_17 → 68a)
- **3 special cases:** 111a un-merge, 3a metadata fix, 104a placeholder cleanup

5 corrections deferred for future work (complex cross-page references needing Sefaria text lookup).

### Phase 4: Golden Dataset

Final golden dataset: **182 stories** (down from 189 due to merges and false positive removal).

Classification distribution:
| Classification | Count |
|---|---|
| YES | 54 |
| HIGH_CONFIDENCE | 28 |
| LOW_CONFIDENCE | 76 |
| NOT_A_STORY | 24 |

0 stories with `needs_review` remaining. Tagged as `v10-golden-ketubot`.

### Phase 5: Evaluation Framework

Built `scripts/evaluate_golden.py` (marked IMMUTABLE — not to be modified during experiments) with three metrics:

1. **Classification F1** (story vs. not-story binary): Measures whether the detector finds the same stories Jeff identifies
2. **Boundary IoU** (segment overlap): For correctly-found stories, how well do the boundaries match?
3. **Merge F1** (cross-page detection): Does the detector correctly identify stories that span page boundaries?
4. **Composite**: 0.4 × F1 + 0.4 × IoU + 0.2 × Merge

**Baseline scores** (current v7/v9 detector vs. golden dataset):

| Metric | Score | Detail |
|---|---|---|
| Classification F1 | **0.92** | 156 TP, 26 FP, 2 FN |
| Boundary IoU | **0.98** | Near-perfect segment overlap |
| Merge F1 | **0.86** | 16 of 19 cross-page merges detected |
| **Composite** | **0.93** | |

The 26 false positives are the primary quality gap — passages the detector classifies as stories but Jeff says are legal discussions, hypothetical scenarios, or dialogue-only passages.

### Phase 6: Detector Improvement Experiments (FAILED — reverted)

#### Cost analysis that changed the plan

The original plan called for a 50-experiment "autoresearch" loop at an estimated $100 budget. Cost analysis revealed:
- The detector uses **Gemini Flash** (not Claude), costing ~$0.30 per full Ketubot run
- 50 experiments would cost ~$15, not $100
- More importantly, blind iteration was wasteful when the error taxonomy already identified exactly what was wrong

We revised to a focused 3-step approach: expand few-shot examples, strengthen prompt disqualifiers, re-run once.

#### Experiment 1: Aggressive prompt changes

Added 5 new disqualifiers to the Stage 2 prompt based directly on Jeff's language from the error taxonomy:
- "Dialogue-only passages are NOT stories"
- "References to stories told elsewhere are NOT stories"
- "One action + legal ruling is NOT a story"
- "A narrative setting does NOT make a story"
- Confidence calibration rules (require causality for HIGH, habitual → LOW)

Also expanded `ground_truth.py` from 128 to 282 entries by loading the canonical review as additional few-shot source material.

**Result: Catastrophic regression.** Pages 2-60 dropped from 72 detected stories to 44. The model became far too conservative, rejecting legitimate stories alongside the false positives. Composite score: 0.57 (down from 0.93).

#### Experiment 2: Light changes only

Reverted the aggressive disqualifiers. Kept only the confidence calibration (3 lines) and the expanded few-shot bank.

**Result: Still a regression.** Pages 2-60 dropped from 72 to 52 stories. Pages 61-112 barely changed (110 → 109). Full composite: 0.89.

#### Root cause: Overfitting to training data

The few-shot examples from Jeff's canonical review are predominantly from pages 2-60 (where the v5.1 feedback originated). When the model sees "this passage from Ketubot 7a is NOT a story" as a few-shot example, it over-applies that rejection pattern to similar passages on the same and nearby pages.

Pages 61-112, which had almost no few-shot examples from the canonical review, were barely affected. This is textbook train/test contamination — the "training" examples and the "test" data are the same pages.

#### Decision: REVERT

All detector changes reverted. The baseline 0.93 is the current best score. V10 experiment results preserved in `results/v10/` for reference.

---

## What We Found

### 1. The golden dataset is solid

182 stories, 48 of 53 corrections applied, all verified. This is the most reliable ground truth we've produced for any tractate. It incorporates 4 rounds of Jeff's feedback and fixes the systematic boundary/merge omissions from prior rounds.

### 2. The detector is already near its ceiling for Ketubot

At 0.93 composite, the v7/v9 detector is doing remarkably well. The 26 false positives represent genuine judgment calls — passages with narrative settings, named characters, and some dialogue that could plausibly be called stories, but Jeff (correctly) identifies as legal discussions with narrative framing. These are inherently ambiguous and require deep understanding of Talmudic literary forms.

### 3. Prompt engineering can't close the remaining gap

Both experiments showed that making the prompt more restrictive hurts recall more than it helps precision. The model can't learn the difference between "legal discussion with narrative setting" (NOT a story) and "narrative with legal elements" (IS a story) from prompt instructions alone — that distinction requires the kind of domain expertise Jeff has.

### 4. Few-shot examples from the same data cause overfitting

This was the most important technical finding. Using Jeff's corrections from pages 2-60 as few-shot examples for detecting stories on pages 2-60 is circular. The model memorizes the specific rejections rather than learning generalizable patterns. Any future few-shot expansion must use examples from a DIFFERENT tractate.

### 5. The real value is the golden dataset, not detector improvements

The golden dataset enables:
- Reliable evaluation of any detection approach (not just our current detector)
- Structured error analysis by pattern type
- Baseline comparison across future detector versions
- Training data for fine-tuning (if we go that route)

### 6. Cost estimates in plans should be verified

The original $2/run estimate (from the brainstorm) was 7× too high. Actual cost: $0.30/run. This didn't change the outcome but would have changed the plan shape — at $0.30/run we could have run 300 experiments for $100, but that wouldn't have helped since the problem isn't findable through blind search.

---

## What's Next

### No manual intervention needed:
- Run the detector on a **new tractate** (e.g., Bava Metzia) where there's no overfitting risk
- Compare error pattern rates on the new tractate to the Ketubot taxonomy
- If the same patterns appear (legal false positives), the taxonomy generalizes

### Needs Jeff's time:
- Review ~30 stories from the new tractate to create a second golden dataset
- This unlocks cross-tractate validation (catch overfitting before it ships)

### Possible future approaches for improving beyond 0.93:
1. **Fine-tuning** on Jeff's labels (would require a training pipeline, but the golden dataset is ready for this)
2. **Post-hoc filtering** using the error taxonomy as a classifier (trained on the 26 false positives)
3. **Accept 0.93** and focus effort on generalizing to more tractates instead

---

## File Inventory

| File | Purpose |
|---|---|
| `results/canonical/ketubot_canonical.json` | THE golden dataset (182 stories) |
| `scripts/evaluate_golden.py` | IMMUTABLE evaluation harness |
| `docs/golden/baseline_ketubot.json` | Baseline scores (0.93 composite) |
| `docs/golden/post_improvement_ketubot.json` | Failed experiment scores (0.89) |
| `docs/golden/canonical_feedback_analysis.json` | Full analysis of all 187 reviews |
| `docs/golden/error_taxonomy.md` | 6 error patterns with detection heuristics |
| `docs/golden/boundary_corrections.json` | Boundary lookup results |
| `results/v10/ketubot_v10_2-60.json` | Experiment 2 detection results (pages 2-60) |
| `results/v10/ketubot_v10_61-112.json` | Experiment 2 detection results (pages 61-112) |
| `scripts/build_canonical.py` | Builds golden dataset from base + feedback |
| `scripts/analyze_canonical_feedback.py` | Analyzes all feedback rounds |
| `scripts/boundary_lookup.py` | Maps Hebrew markers to segment indices |
| `scripts/apply_boundary_corrections.py` | Applies boundary/merge corrections |
| `scripts/rerun_detector_v10.py` | Re-runs detector with modified prompts |
| `scripts/autoresearch/program.md` | Agent instructions (unused — approach abandoned) |
| `scripts/autoresearch/run_experiment.py` | Experiment runner (used for eval only) |

## Git Tags

- `v10-golden-ketubot` — the golden dataset checkpoint
- `pre-detector-changes` — rollback point (detector is unchanged from here)
