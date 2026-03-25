# Golden Dataset + Detector Improvement Plan

**Created:** 2026-03-25
**Updated:** 2026-03-25 (revised Phase 6 after cost analysis)
**Source:** Jeff's canonical review (2026-03-17) + analysis in `docs/golden/canonical_feedback_analysis.json`
**Goal:** Build the definitive Ketubot ground truth, then use it to improve detection for all tractates.

---

## Git Strategy & Rollback Plan

### Branch Structure
```
claude/sefaria-talmud-story-search-Mw1Yg  (current main branch)
  │
  ├── Commit A: (ac8e83c) Documentation + analysis
  ├── Commit B: (d85da87) 17 classification corrections
  ├── Commit C: (838c550) Boundary lookup tooling
  ├── Commit D: (72414c3) 32 boundary/merge corrections
  ├── Commit F: (dc16195) Eval framework + baseline (0.93)
  ├── Commit G: (7787f2c) Autoresearch infrastructure
  │
  ├── Tag: v10-golden-ketubot
  ├── Tag: pre-detector-changes  ← ROLLBACK POINT
  │
  ├── Commit H: Expand ground_truth.py with Jeff's new corrections
  ├── Commit I: Add legal disqualifier to Stage 2 prompt
  ├── Commit J: Re-run detector + evaluate improvement
  │   If composite drops below 0.90 → git revert to pre-detector-changes
  │
  └── Future: feat/generalize-tractate-X branches
```

---

## Phase 1: Machine-Readable Documentation (DONE ✓)
- [x] Analyze all 187 canonical review entries
- [x] Cross-reference with 3 prior feedback rounds for consistency
- [x] Classify error patterns and extract Hebrew boundary markers
- [x] Identify 10 repeated issues Jeff flagged before that we didn't fix
- [x] Output: `docs/golden/canonical_feedback_analysis.json`
- [x] Output: `scripts/analyze_canonical_feedback.py` (reproducible)
- [x] Output: `docs/golden/error_taxonomy.md`

**Git: Commit A** (ac8e83c)

---

## Phase 2: Classification Corrections (DONE ✓)

Applied 17 classification corrections (10 NOT_A_STORY + 5 LOW_CONFIDENCE + 1 HIGH_CONFIDENCE + 1 special case).

- [x] 10 NOT_A_STORY reclassifications
- [x] 5 LOW_CONFIDENCE reclassifications
- [x] 106a_3-3: YES → HIGH_CONFIDENCE
- [x] 111a_23-25: NOT_A_STORY → LOW_CONFIDENCE (cross-page merge stripped in Phase 3)

**Git: Commit B** (d85da87)

---

## Phase 3: Boundary Corrections (DONE ✓)

### 3a. Boundary Lookup Tool (DONE)
Built `scripts/boundary_lookup.py` — resolved 17/52 corrections automatically.

**Git: Commit C** (838c550)

### 3b-3e. Apply All Corrections (DONE)
Applied 32 corrections via `scripts/apply_boundary_corrections.py`:
- [x] 7 stories confirmed correct (needs_review removed)
- [x] 8 boundary trims (overextended into Talmud commentary)
- [x] 5 boundary extensions
- [x] 5 same-page merges
- [x] 4 new cross-page merges
- [x] 3 special cases (111a un-merge, 3a confirm, 104a cleanup)
- [x] Spot-checked 10 corrections ✓
- [x] 0 needs_review remaining ✓

**Deferred (5 items):** 103b_3-3, 60b_2-3, 60b_5-9, 49b_12-12, 12b_0-0

**Git: Commit D** (72414c3)

---

## Phase 4: Golden Dataset (DONE ✓)

- [x] Golden dataset: 182 stories (down from 189)
- [x] 0 needs_review remaining
- [x] Tag `v10-golden-ketubot` applied

Classification distribution: YES=54, HIGH=28, LOW=76, NOT_A_STORY=24

---

## Phase 5: Evaluation Framework (DONE ✓)

### 5a. Composite Scoring (DONE)
Built `scripts/evaluate_golden.py` (IMMUTABLE). Scores:
- Classification F1, Boundary IoU, Merge F1, Composite (0.4/0.4/0.2 weights)

### 5b. Baseline Score (DONE)
- Classification F1: **0.92** (156 TP, 26 FP, 2 FN)
- Boundary IoU: **0.98** (excellent overlap)
- Merge F1: **0.86** (16/19 merges detected)
- **Composite: 0.93**

Main improvement target: 26 false positives (legal discussions Jeff says are NOT stories)

### 5c. 2nd Tractate Baseline (PENDING — needs Jeff)
- [ ] Pick tractate (suggest Bava Metzia)
- [ ] Run detector on 10-15 pages
- [ ] Have Jeff spot-review → mini ground truth
- [ ] Score baseline

**Git: Commit F** (dc16195)
**Git: Tag `pre-detector-changes`** applied

---

## Phase 6: Targeted Detector Improvement (REVISED)

### Why we changed the approach

The original plan called for a 50-experiment autoresearch loop at ~$100 budget. Cost analysis
revealed the actual cost per full Ketubot re-run is **~$0.30** (Gemini Flash, not Claude), making
50 experiments ~$15 not $100. But the bigger issue is that blind iteration is wasteful when the
error taxonomy already tells us exactly what's wrong:

- **26 of 28 errors are false positives** — the detector calls legal discussions "stories"
- The error taxonomy identifies 6 specific patterns with Jeff's language
- 2-3 targeted changes should capture most gains; diminishing returns after that

### Revised approach: Focused 3-step sprint

**Cost: ~$0.30 total. Time: ~10 minutes.**

All changes on current branch (not a separate experiment branch — these are well-understood
fixes, not speculative experiments).

### Step 1: Expand ground_truth.py (Commit H)

Add Jeff's canonical review corrections to the Ground Truth DB. The detector's few-shot
example bank currently has 128 entries from prior rounds. Adding the new corrections teaches
the model what legal false positives look like.

**Specific additions:**

11 LEGAL_FALSE_POSITIVE examples:
- 7a_1-1: "no events, just legal discussion" (was LOW_CONFIDENCE)
- 7a_2-2: "not a story, reasoning leads to that conclusion" (was LOW_CONFIDENCE)
- 13b_0-0: "hypothetical legal case" (was LOW_CONFIDENCE)
- 13b_16-16: "just a legal decision, dialogue only" (was LOW_CONFIDENCE)
- 15b_2-2: "just a reference to a story mentioned above" (was LOW_CONFIDENCE)
- 21b_7-8: "all legal discussion, dialogue not events" (was HIGH_CONFIDENCE)
- 25a_9-10: "finding someone in study hall is not an event" (was LOW_CONFIDENCE)
- 26a_9-9: "hypothetical scenario" (was LOW_CONFIDENCE)
- 26b_0-0: "continuation of hypothetical" (was YES)
- 110b_24-24: "just one action and explanation" (was LOW_CONFIDENCE)
- 8a_13-13: downgraded HIGH → LOW, "too little causality"

5 CONFIDENCE_MISCALIBRATION examples:
- 14b_11-11: "two events, no causality" (HIGH → LOW)
- 17a_10-10: "habitual, not one-time" (YES → LOW)
- 21a_10-11: "mostly legal case" (HIGH → LOW)
- 25b_6-6: "two events, no real causality" (YES → LOW)
- 106a_3-3: "minimal action, request and rejection" (YES → HIGH)

Each entry includes:
- Story key, page ref, segment range
- Jeff's verdict and reasoning (exact quote)
- Error pattern classification
- Old and new classification

### Experiment Results: REVERTED (composite dropped 0.93 → 0.89)

We ran two experiments on 2026-03-25:

**Experiment 1: Expanded few-shots + aggressive disqualifiers**
- Added 5 new disqualifiers to the prompt (dialogue-only, references, one-action-plus-ruling, etc.)
- Added confidence calibration section
- Expanded ground_truth.py from 128 → 282 entries with canonical review
- Result: **CATASTROPHIC regression.** Pages 2-60 dropped from 72 to 44 stories.
  Composite: 0.57. Model became far too conservative — rejected legitimate stories.

**Experiment 2: Expanded few-shots + light confidence calibration only**
- Reverted the aggressive disqualifiers, kept only confidence calibration (3 lines)
- Kept expanded ground_truth.py (282 entries)
- Result: **Still a regression.** Pages 2-60 dropped from 72 to 52 stories.
  Full composite: 0.89 (vs 0.93 baseline). Pages 61-112 barely changed (110 → 109).

**Root cause:** The few-shot examples from the canonical review are mostly from pages 2-60.
When the model sees examples of passages from pages 2-60 that Jeff says are NOT stories,
it over-applies that reasoning to other passages on the same pages. This is textbook
overfitting to the training data.

**Decision: REVERT all detector changes.** The baseline detector (0.93) is better.

**Lesson learned:** The 26 false positives are genuine judgment calls where the model and
Jeff disagree. They can't be fixed by prompt engineering or few-shot examples from the same
data. Improvement requires either:
1. A fundamentally different detection approach (e.g., fine-tuning on Jeff's labels)
2. A post-processing step that uses the golden labels directly (but that's just lookup, not detection)
3. Accepting 0.93 as the ceiling for prompt-based detection on Ketubot

The v10 results are preserved in `results/v10/` for reference.

**Cost of experiments: ~$0.60 (two full Ketubot runs at ~$0.30 each).**

---

## Phase 7: Generalize to Other Tractates (FUTURE)

**Each tractate gets its own branch: `feat/generalize-tractate-X`**

### 7a. Apply Ketubot Lessons to New Tractate

1. Run detector with Ketubot-learned improvements
2. Use expanded few-shot examples
3. Measure error pattern rates → compare to Ketubot rates
4. Focus on: legal false positive rate, boundary precision, cross-page merges

### 7b. Self-Validation Protocol

Without Jeff reviewing every story:
1. Run detector
2. Run adversarial validation with Ketubot-calibrated few-shots
3. Auto-flag stories matching known error patterns
4. Present ONLY flagged stories for Jeff → reduce his workload by ~70%

### 7c. Continuous Improvement

Each Jeff review batch:
1. Incorporate into golden dataset (tractate-specific)
2. Re-run detector with updated few-shots
3. Cross-tractate validation prevents overfitting

---

## Deferred Items

1. **5 boundary corrections:** 103b_3-3, 60b_2-3, 60b_5-9, 49b_12-12, 12b_0-0
2. **Review UI regeneration** — generate updated HTML for spot-checking in browser
3. **2nd tractate baseline** — needs Jeff's review time
4. **Narrative cycle grouping** — Rabbi Yehudah HaNasi's death spans 103a-104a

---

## Verification Checklist

- [x] 48/53 actionable items addressed (5 deferred)
- [x] Classification corrections verified (17/17 spot-checked)
- [x] Boundary corrections verified (10/10 spot-checked)
- [x] 0 needs_review remaining
- [x] Baseline score: 0.93 composite
- [x] Tag `v10-golden-ketubot` applied
- [x] Tag `pre-detector-changes` applied
- [x] Step 1-3: Ran detector improvement experiments → REVERTED (regression)
- [ ] Review UI generated and spot-checked in browser
- [ ] Cross-tractate baseline (pending Jeff review)
