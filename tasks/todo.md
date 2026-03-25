# Golden Dataset + Generalization Plan

**Created:** 2026-03-25
**Source:** Jeff's canonical review (2026-03-17) + analysis in `docs/golden/canonical_feedback_analysis.json`
**Goal:** Build the definitive Ketubot ground truth, then use it to improve detection for all tractates.

---

## Git Strategy & Rollback Plan

### Branch Structure
```
claude/sefaria-talmud-story-search-Mw1Yg  (current main branch)
  │
  ├── Commit A: "Add canonical feedback analysis and golden dataset documentation"
  │   Phase 1 output. Pure documentation, zero risk. NEVER rolled back.
  │
  ├── Commit B: "Apply 15 auto classification corrections from Jeff's canonical review"
  │   Phase 2 output. Classification-only changes. Safe rollback point.
  │
  ├── Commit C: "Add boundary lookup tooling"
  │   Phase 3a output. Scripts only, no data changes. Safe rollback point.
  │
  ├── Commit D: "Apply boundary corrections to golden dataset"
  │   Phase 3b-3e output. Data changes based on Jeff's Hebrew markers.
  │   Rollback: revert to Commit B if boundary mappings are wrong.
  │
  ├── Commit E: "Rebuild golden canonical dataset with all corrections"
  │   Phase 4 output. Final golden dataset. Tag: v10-golden-ketubot.
  │
  ├── Commit F: "Add evaluation framework and baseline score"
  │   Phase 5 output. Scoring scripts. NEVER rolled back (eval is immutable).
  │
  ├── Tag: pre-detector-changes
  │   ← ROLLBACK POINT for detector experiments
  │
  ├── feat/autoresearch-detector-improvements  (NEW BRANCH from here)
  │   │  Phase 6 output. Detector prompt/logic changes.
  │   │  Each autoresearch experiment = 1 commit.
  │   │  Only merged to main after validation on 2nd tractate.
  │   │
  │   └── (merge to main only if validated)
  │
  └── feat/generalize-tractate-X  (NEW BRANCH)
      Phase 7 output. New tractate runs.
```

### Rollback Decision Points

**After Phase 2 (classification corrections):**
- Risk: near zero. These are Jeff's explicit verdicts.
- Verify: re-run `analyze_canonical_feedback.py` → all 15 should show `implemented: true`
- Rollback: `git revert <commit B>` if any classification is wrong

**After Phase 3 (boundary corrections):**
- Risk: moderate. Boundary lookup tool may map Hebrew markers to wrong segments.
- Verify: for each correction, print the actual segment text before/after and manually spot-check 5-10
- Rollback: `git revert <commit D>` → returns to classification-only corrections
- The golden dataset at Commit B is still valid (just without boundary precision)

**After Phase 4 (golden dataset rebuild):**
- Risk: low. This is just repackaging the corrections into the canonical JSON.
- Verify: generate review UI, open in browser, check 10 random stories
- Tag `v10-golden-ketubot` so we can always return here

**After Phase 6 (detector changes):**
- Risk: HIGH. This is where overfitting can happen.
- Verify: run detector on 2nd tractate with mini ground truth (see Phase 6.5 below)
- Rollback: `git checkout pre-detector-changes` → discards ALL detector changes
- The golden dataset, eval framework, and documentation are UNAFFECTED
- Detector experiments live on `feat/autoresearch-detector-improvements` branch — only merged if validated

**After Phase 7 (generalization):**
- Risk: moderate. New tractate may reveal Ketubot-specific patterns.
- Verify: Jeff spot-reviews 20-30 stories from new tractate
- Rollback: independent branch per tractate. Failures don't affect Ketubot golden dataset.

### The Nuclear Rollback

If everything after Phase 1 goes wrong:
1. `git checkout <commit A>` — back to pure documentation
2. We still have: Jeff's feedback in JSON, error taxonomy, analysis script
3. We've lost nothing except time
4. We can restart with a different approach

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

## Phase 2: Auto-Applicable Classification Corrections (DONE ✓)

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

## Phase 4: Rebuild Golden Dataset (DONE ✓)

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

### 5c. 2nd Tractate Baseline (PENDING)
- [ ] Pick tractate (suggest Bava Metzia)
- [ ] Run detector on 10-15 pages
- [ ] Have Jeff spot-review → mini ground truth
- [ ] Score baseline

**Git: Commit F** (dc16195)
**Git: Tag `pre-detector-changes`** applied

---

## Phase 6: Self-Improvement Loop (Autoresearch)

**ALL detector changes happen on `feat/autoresearch-detector-improvements` branch.**

### 6a. Structure the Mutable Surface

What the autoresearch agent CAN modify:
- `src/story_detector_v7.py` → Stage 2 prompt, criteria, rules, examples
- `src/event_triage.py` → Stage 1 event type classifications
- Boundary trimming rules in Stage 4
- Cross-page merge heuristics

What it CANNOT modify:
- `scripts/evaluate_golden.py` (the eval harness)
- `results/canonical/ketubot_canonical.json` (the golden labels)
- `docs/golden/*` (documentation)
- Test infrastructure

### 6b. Few-Shot Example Bank

Convert Jeff's corrections into structured few-shot examples by error pattern:
- **LEGAL_FALSE_POSITIVE**: 11 passages with Jeff's reasoning
- **BOUNDARY_OVEREXTENSION**: 5 passages with before/after boundaries
- **CONFIDENCE_MISCALIBRATION**: 9 passages with calibration notes
- **MERGE examples**: Stories Jeff says should be combined

Expand `src/ground_truth.py` from 128 → ~187 entries.

### 6c. The Autoresearch Loop

```
prepare.py  = scripts/evaluate_golden.py (IMMUTABLE)
train.py    = src/story_detector_v7.py (MUTABLE)
program.md  = instructions for the agent

while True:
    1. Agent reads current prompts and prior results
    2. Hypothesizes an improvement
    3. Modifies the prompt/logic
    4. Commits the change (one commit per experiment)
    5. Runs detector on all labeled pages (~5 min)
    6. Evaluates composite score
    7. If improved: keep. If not: git reset --hard HEAD~1
    8. Repeat.
```

Target: ~50 experiments overnight. Budget: ~$100 at $2/run.

### 6d. Aramaic Structural Markers

Explore automated detection of Talmud meta-commentary:
- Interrogative openings: הֵיכִי, מַאי, מְנָא
- "The Gemara asks/objects" patterns
- Narrative→analytical tense shifts

### 6.5. VALIDATION GATE (before merging detector changes)

**This is the key rollback decision point.**

1. Run improved detector on Ketubot → score against golden dataset
2. Run improved detector on 2nd tractate (same pages as Phase 5c) → score against mini ground truth
3. Compute improvement:
   - Ketubot improvement = new_score - baseline_score
   - 2nd tractate improvement = new_score - cross_tractate_baseline

**Decision matrix:**

| Ketubot improved? | 2nd tractate improved? | Action |
|---|---|---|
| Yes (>5%) | Yes (>5%) | MERGE to main |
| Yes (>5%) | No change | Investigate overfitting. Try removing Ketubot-specific rules. Re-test. |
| Yes (>5%) | Worse | ROLLBACK. Detector is overfitting to Ketubot. |
| No change | - | More experiments needed. |
| Worse | - | ROLLBACK immediately. |

**Rollback procedure:**
```bash
git checkout pre-detector-changes      # Return to pre-experiment state
git branch -D feat/autoresearch-*      # Clean up experiment branch (optional)
```

The golden dataset, eval framework, and all documentation remain intact.

---

## Phase 7: Generalize to Other Tractates

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
2. Re-run autoresearch loop (now with multi-tractate ground truth)
3. Detector improves with each tractate
4. Cross-tractate validation prevents overfitting

---

## Edge Cases to Handle

1. **Stories spanning 3+ pages**: Verify merge logic handles this.
2. **Sub-segment mixed content**: Jeff says "trim last sentence" within a segment. Schema supports this but implementation is Phase 2.
3. **Duplicate stories across pages**: Ketubot 3a has same story as 2b. Need deduplication.
4. **Jeff's "soft" suggestions**: "could be included" vs "should be included". Track confidence.
5. **Hebrew vocalization differences**: Normalize nikud before matching.
6. **106a_3-3 terminology**: Jeff's "high confidence" vs our classification labels. Clarify.
7. **Narrative cycles**: Rabbi Yehudah HaNasi's death spans 103a-104a. Grouping mechanism vs. mega-story.

---

## Verification Checklist

- [x] 48/53 actionable items addressed (5 deferred)
- [x] Classification corrections verified (17/17 spot-checked)
- [x] Boundary corrections verified (10/10 spot-checked)
- [x] 0 needs_review remaining
- [x] Baseline score: 0.93 composite
- [x] Tag `v10-golden-ketubot` applied
- [x] Tag `pre-detector-changes` applied
- [ ] Review UI generated and spot-checked in browser (TODO)
- [ ] Cross-tractate baseline (pending Jeff review)
- [ ] Remaining 5 deferred corrections
