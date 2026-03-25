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

## Phase 1: Machine-Readable Documentation (DONE)
- [x] Analyze all 187 canonical review entries
- [x] Cross-reference with 3 prior feedback rounds for consistency
- [x] Classify error patterns and extract Hebrew boundary markers
- [x] Identify 10 repeated issues Jeff flagged before that we didn't fix
- [x] Output: `docs/golden/canonical_feedback_analysis.json`
- [x] Output: `scripts/analyze_canonical_feedback.py` (reproducible)
- [x] Output: `docs/golden/error_taxonomy.md`

**Git: Commit A** — "Add canonical feedback analysis and golden dataset documentation"
Files: `scripts/analyze_canonical_feedback.py`, `docs/golden/*`, `docs/brainstorms/*`, `tasks/todo.md`

---

## Phase 2: Auto-Applicable Classification Corrections

Apply the 15 classification changes that can be done automatically.

### 2a. New NOT_A_STORY (10 stories)
- [ ] Ketubot 7a_1-1: "no events, just a legal discussion"
- [ ] Ketubot 7a_2-2: "not a story, reasoning shows it's not"
- [ ] Ketubot 13b_0-0: "hypothetical legal case, not a story"
- [ ] Ketubot 13b_16-16: "just a legal decision, dialogue only"
- [ ] Ketubot 15b_2-2: "just a reference to a story mentioned above"
- [ ] Ketubot 21b_7-8: "all legal discussion, dialogue not events"
- [ ] Ketubot 25a_9-10: "not a story, finding someone in study hall is not an event"
- [ ] Ketubot 26a_9-9: "part of a legal discussion, hypothetical scenario"
- [ ] Ketubot 26b_0-0: "continuation of hypothetical legal case"
- [ ] Ketubot 110b_24-24: "just one action and then explanation"

### 2b. New LOW_CONFIDENCE (5 stories)
- [ ] Ketubot 8a_13-13: "too little change or causality for high confidence"
- [ ] Ketubot 14b_11-11: "two events but no causality"
- [ ] Ketubot 17a_10-10: "not one-time, recounts what rabbis 'would' do repeatedly"
- [ ] Ketubot 21a_10-11: "mostly a legal case, 'explaining' is dialogue not action"
- [ ] Ketubot 25b_6-6: "two events but no real causality"

### 2c. Fix Confused Entry
- [ ] Ketubot 111a_23-25: Undo NOT_A_STORY. 111a portion → LOW_CONFIDENCE. 111b portion → separate NOT_A_STORY entry.

### 2d. Reclassification
- [ ] Ketubot 106a_3-3: Verify current classification and Jeff's intent. His "high confidence" may mean our HIGH_CONFIDENCE level.

**Script:** Update `build_canonical.py` to incorporate canonical review as a 4th feedback source. Run and verify.

**Git: Commit B** — "Apply 15 auto classification corrections from Jeff's canonical review"
Files: `scripts/build_canonical.py`, `results/canonical/ketubot_canonical.json`

---

## Phase 3: Boundary Corrections (THE HARD PART)

### 3a. Build Boundary Lookup Tool

Write `scripts/boundary_lookup.py` that:
1. Loads canonical JSON with full segment text
2. For each Hebrew marker in the analysis JSON, searches segments on that page (and adjacent pages)
3. Normalizes Unicode (strip nikud for matching, handle NFC/NFD)
4. Outputs proposed `new_start_segment` / `new_end_segment`
5. For sub-segment cases, records `start_char_offset` / `end_char_offset`
6. Produces a human-readable diff showing "before → after" for each correction

**Edge cases:**
- Nikud (vowel marks) differences between Jeff's citation and Sefaria text
- Markers that span segment boundaries
- Markers from ADJACENT pages (cross-page boundary corrections)
- Markers that appear multiple times on a page (need context to disambiguate)

**Git: Commit C** — "Add boundary lookup tooling"
Files: `scripts/boundary_lookup.py`

### 3b. Apply Boundary OVEREXTENSION Corrections (trim Talmud commentary)

- [ ] Ketubot 23a_13-16: Trim Gemara's comment (טַעְמָא דְּלָא...)
- [ ] Ketubot 54a_13-14: Trim Talmud's question (וְעַד הֵיכָא...)
- [ ] Ketubot 85b_9-9: Trim Talmud's comment (מֵעִיקָּרָא מַאי סְבַר...)
- [ ] Ketubot 104b_7-15: Trim Talmud's comment (מֵעִיקָּרָא הוּא סְבַר...)
- [ ] Ketubot 60b_5-9: Trim after (הָא רַב נַחְמָן שְׁרָא...)
- [ ] Ketubot 91b_2-7: Trim legal discussion, ends at (וְאִי לָא...)
- [ ] Ketubot 91b_15-16: Trim, story ends at (וַאֲתָא אִיהוּ וְקָא מְעַרְעַר)
- [ ] Ketubot 67b_15-15: Trim Talmud's question after Mar Ukva section

### 3c. Apply Boundary UNDEREXTENSION Corrections (extend boundaries)

**Extend START:**
- [ ] Ketubot 12b_0-0: Include first line from 12a (אמר רב אשי: שתי תקנות הוו...)
- [ ] Ketubot 52b_4-5: Start at קָרִיבֵיהּ (trim legal ruling from start)
- [ ] Ketubot 26a_1-1: Include first half from previous page (מַעֲשֶׂה בְּאָדָם אֶחָד...)
- [ ] Ketubot 53a_2-3: Include first half (begins with רב פפא)
- [ ] Ketubot 77b_6-8: Include previous line (רַבִּי יְהוֹשֻׁעַ בֶּן לֵוִי...)
- [ ] Ketubot 60b_2-3: Start at אֲרִיסֵיהּ דְּאַבָּיֵי, include Abaye's reflection

**Extend END:**
- [ ] Ketubot 56b_11-11: Include next line (Shmuel's statement)
- [ ] Ketubot 25b_4-4: Include next paragraph (continuation)
- [ ] Ketubot 109b_12-12: Include deliberation lines
- [ ] Ketubot 61a_12-12: Include next two paragraphs (soft suggestion — "could be")
- [ ] Ketubot 103a_24-32: Include next paragraph (הָהוּא יוֹמָא דְּאַשְׁכָּבְתֵּיהּ...)

### 3d. Cross-Page Merges (17 stories)

**New merges:**
- [ ] Ketubot 54a_22-22 → merge with 54b continuation
- [ ] Ketubot 67b_17-17 → merge with top of 68a
- [ ] Ketubot 49b_12-12 → merge with 50a
- [ ] Ketubot 69b_10-12 → merge with top of 70a

**Same-page merges:**
- [ ] Ketubot 25b_5-5 → merge into 25b_4-4
- [ ] Ketubot 85a_8-8 + 85a_9-10 → one story (Jeff said this TWICE)
- [ ] Ketubot 103b_3-3 → part of longer Rabbi Yehudah HaNasi story

**Implement approved merges from needs_review:**
- [ ] Ketubot 8b_6-10 → merge with 8b_3-4
- [ ] Ketubot 62b_6-7 + 62b_9-9 → merge
- [ ] Ketubot 52b_17-17 → merge with 53a continuation
- [ ] Ketubot 103b_20-21 → add to 103a death narrative
- [ ] Ketubot 62b_14-14 → fix cross-page merge with 63a
- [ ] Ketubot 69a_14-16 → fix merge to include top of 69b
- [ ] Ketubot 84b_11-11 → include top of 85a continuation
- [ ] Ketubot 85b_9-9 → include top of 86a continuation
- [ ] Ketubot 91a_19-20 → include top of 91b, separate independent stories
- [ ] Ketubot 105b_14-16 → include top of 106a stories

### 3e. Handle "adjust" verdicts (4 stories)
- [ ] Ketubot 3a_9-9: Metadata update only (Jeff says no adjustment needed)
- [ ] Ketubot 56b_11-11: Handled in 3c
- [ ] Ketubot 85b_9-9: Handled in 3b
- [ ] Ketubot 103a_24-32: Handled in 3c

**Git: Commit D** — "Apply boundary and merge corrections to golden dataset"
Files: `results/canonical/ketubot_canonical.json`, `scripts/build_canonical.py`

**Verification before committing:**
- [ ] Print before/after segment text for each boundary change → spot-check 10
- [ ] Verify no regressions on the 134 "correct" stories
- [ ] Run `analyze_canonical_feedback.py` → all 53 actionable items addressed

---

## Phase 4: Rebuild Golden Dataset

- [ ] Regenerate `ketubot_canonical.json` with all corrections
- [ ] Generate updated review UI for spot-checking
- [ ] Open in browser, verify 10 random stories display correct boundaries
- [ ] Compute story count (expect ~170-175 after removing false positives + merges)
- [ ] Update `docs/golden/canonical_feedback_analysis.json` with `implemented: true` flags

**Git: Commit E** — "Rebuild golden canonical dataset with all Jeff corrections"
**Git: Tag `v10-golden-ketubot`** — permanent reference to the golden dataset

---

## Phase 5: Evaluation Framework

### 5a. Composite Scoring Metric

Build `scripts/evaluate_golden.py` (IMMUTABLE after creation):
- **Classification F1**: YES/HIGH/LOW vs NOT_A_STORY against Jeff's labels
- **Boundary IoU**: Intersection-over-union of detected vs. golden segment ranges
- **Merge accuracy**: Did we correctly identify cross-page stories?
- **Composite**: 0.4 * classification_F1 + 0.4 * boundary_IoU + 0.2 * merge_accuracy
- Output: single JSON with all subscores + composite

### 5b. Baseline the Current Detector

**Critical step before any detector changes:**
1. Run current v7 detector on all Ketubot pages
2. Score against the golden dataset → **this is the pre-improvement baseline**
3. Record: `docs/golden/baseline_score.json`
4. This score is the bar that detector improvements must beat

### 5c. Baseline on a 2nd Tractate (Pre-Improvement)

1. Pick a candidate tractate (Bava Metzia, Gittin, or Sanhedrin)
2. Run current v7 detector on 10-15 representative pages
3. Have Jeff spot-review ~20-30 detected stories → mini ground truth
4. Score → **this is the cross-tractate baseline**
5. If the autoresearch loop improves Ketubot but NOT this tractate, we've overfitted

**Git: Commit F** — "Add evaluation framework and baseline scores"
**Git: Tag `pre-detector-changes`** — ← THE ROLLBACK POINT for all detector experiments

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

## Verification Checklist (before claiming golden dataset done)

- [ ] Every one of Jeff's 53 actionable items addressed
- [ ] All 10 repeated issues finally fixed
- [ ] Classification accuracy >95% against Jeff's labels
- [ ] Boundary adjustments verified against actual segment text
- [ ] Cross-page merges include correct continuation text
- [ ] No regressions on 134 confirmed-correct stories
- [ ] Review UI generated and spot-checked in browser
- [ ] Baseline score recorded before any detector changes
- [ ] Cross-tractate baseline recorded
- [ ] Tag `v10-golden-ketubot` applied
- [ ] Tag `pre-detector-changes` applied before autoresearch begins
