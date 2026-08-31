# Plan: Golden Ketubot Dataset + Generalization Framework

**Created:** 2026-03-25
**Status:** Awaiting approval
**Reference:** This is the permanent copy of the implementation plan. The working task list is in `tasks/todo.md`.

## Context

Jeff Rubenstein reviewed all 189 stories in our canonical Ketubot dataset (2026-03-17). Analysis reveals **53 stories need changes**: 15 classification corrections (auto-appliable) and 38 boundary/merge corrections (require tooling). Critically, 10 of these are issues Jeff flagged in prior rounds that we never fully fixed — we applied classification changes but ignored the boundary/merge corrections in the same notes.

This plan builds the definitive ground truth for Ketubot, creates an evaluation framework, and sets up an autoresearch self-improvement loop for generalizing to other tractates.

**Work already done (this session):**
- `scripts/analyze_canonical_feedback.py` — processes all 187 reviews into machine-readable format
- `docs/golden/canonical_feedback_analysis.json` — comprehensive correction catalog with error patterns, Hebrew markers, actions
- `docs/golden/error_taxonomy.md` — 6 error patterns with detection heuristics
- `docs/brainstorms/2026-03-25-golden-dataset-and-generalization-brainstorm.md`
- `tasks/todo.md` — detailed task list

---

## Git Commit Strategy

Each phase produces one commit. Each commit is a clean rollback point.

| Commit | Phase | Contents | Rollback risk |
|--------|-------|----------|---------------|
| **A** | 1 | Documentation + analysis scripts | None — pure docs |
| **B** | 2 | 15 classification corrections | Low — Jeff's explicit verdicts |
| **C** | 3a | Boundary lookup tooling | None — scripts only |
| **D** | 3b-e | Boundary + merge corrections | Moderate — verify segment mappings |
| **E** | 4 | Rebuilt golden dataset + tag `v10-golden-ketubot` | Low — repackaging |
| **F** | 5 | Eval framework + baseline scores + tag `pre-detector-changes` | None — measurement only |
| **G+** | 6 | Detector experiments (separate branch `feat/autoresearch`) | High — only merge if validated |

### Rollback Procedures

**After Commit B:** `git revert <B>` if any classification wrong. Low risk — these are Jeff's explicit verdicts.

**After Commit D:** `git revert <D>` to undo boundary/merge changes while keeping classification corrections. The golden dataset at Commit B is still valid, just without boundary precision.

**After Commit E (tagged `v10-golden-ketubot`):** This is the golden dataset. Always recoverable via `git checkout v10-golden-ketubot`.

**After Commit F (tagged `pre-detector-changes`):** This is THE rollback point for all detector experiments. `git checkout pre-detector-changes` discards ALL detector changes while preserving the golden dataset and eval framework.

**After Phase 6 (separate branch):** Detector experiments live on `feat/autoresearch-detector-improvements`. Only merged to main after validation gate passes. If validation fails: `git branch -D feat/autoresearch-detector-improvements`.

**Nuclear rollback:** `git checkout <Commit A>` returns to pure documentation. All of Jeff's feedback is preserved. We've lost time but no data.

---

## Phase 1: Commit Documentation (Commit A)

**Already done.** Commit the work from this session.

**Files to stage:**
- `scripts/analyze_canonical_feedback.py`
- `scripts/build_canonical.py`
- `docs/golden/canonical_feedback_analysis.json`
- `docs/golden/error_taxonomy.md`
- `docs/golden/PLAN_golden_dataset_and_generalization.md`
- `docs/brainstorms/2026-03-25-golden-dataset-and-generalization-brainstorm.md`
- `tasks/todo.md`
- `results/canonical/ketubot_canonical.json`
- `validation/feedback/canonical_review_anonymous_2026-03-17.json`
- `validation/feedback/v5_1_feedback_anonymous_2026-02-20.json`
- `validation/feedback/v8_delta_feedback_anonymous_2026-02-26.json`

**NOT staged:** `.DS_Store`, `basketball_biblical_pairings.csv`, unrelated HTML feedback files

---

## Phase 2: Classification Corrections (Commit B)

### What changes

Modify `scripts/build_canonical.py` to add the canonical review as a 4th feedback source.

The canonical review uses different verdict names than prior rounds:
- `"correct"` → no classification change
- `"incorrect"` → needs reclassification (parse note for target)
- `"approve"` → implement proposed change from needs_review
- `"adjust"` → implement with modification

Add a new function `categorize_canonical_correction()` that handles these verdict types.

**Specific corrections (15 auto-applicable):**

| Story | Current | Target | Jeff's reason |
|-------|---------|--------|---------------|
| 7a_1-1 | YES | NOT_A_STORY | No events, legal discussion |
| 7a_2-2 | YES | NOT_A_STORY | Not a story |
| 13b_0-0 | HIGH_CONFIDENCE | NOT_A_STORY | Hypothetical legal case |
| 13b_16-16 | YES | NOT_A_STORY | Legal decision, dialogue only |
| 15b_2-2 | HIGH_CONFIDENCE | NOT_A_STORY | Reference to story, not story |
| 21b_7-8 | HIGH_CONFIDENCE | NOT_A_STORY | Legal discussion |
| 25a_9-10 | HIGH_CONFIDENCE | NOT_A_STORY | Not an event |
| 26a_9-9 | HIGH_CONFIDENCE | NOT_A_STORY | Hypothetical scenario |
| 26b_0-0 | HIGH_CONFIDENCE | NOT_A_STORY | Continuation of hypothetical |
| 110b_24-24 | LOW_CONFIDENCE | NOT_A_STORY | One action + explanation |
| 8a_13-13 | HIGH_CONFIDENCE | LOW_CONFIDENCE | Too little causality |
| 14b_11-11 | HIGH_CONFIDENCE | LOW_CONFIDENCE | Two events, no causality |
| 17a_10-10 | HIGH_CONFIDENCE | LOW_CONFIDENCE | Habitual, not one-time |
| 21a_10-11 | HIGH_CONFIDENCE | LOW_CONFIDENCE | Mostly legal case |
| 25b_6-6 | HIGH_CONFIDENCE | LOW_CONFIDENCE | No real causality |

**Special cases:**
- **111a_23-25:** Currently NOT_A_STORY (auto-applied from v8_delta). Jeff now says the 111a portion is LOW_CONFIDENCE and the 111b portion is NOT_A_STORY. Need to split into two entries and undo the merge.
- **106a_3-3:** Jeff says "should be high confidence" — need to check current classification. If it's YES, this might mean Jeff wants HIGH_CONFIDENCE (a downgrade in our system). Verify by looking at the actual story.

**Verification:**
1. Run `python3 scripts/build_canonical.py` → check output counts
2. Run `python3 scripts/analyze_canonical_feedback.py` → verify 15 items show as addressed
3. Spot-check 5 stories in the JSON to confirm correct classification

---

## Phase 3: Boundary Corrections (Commits C + D)

### Phase 3a: Build Boundary Lookup Tool (Commit C)

**New file: `scripts/boundary_lookup.py`**

Purpose: Map Jeff's Hebrew text markers to specific segment indices.

```
Input:  docs/golden/canonical_feedback_analysis.json (hebrew_boundary_markers field)
        results/canonical/ketubot_canonical.json (segment text)

Output: docs/golden/boundary_corrections.json
        Human-readable before/after diff for each correction
```

**Algorithm:**
1. For each correction with hebrew_boundary_markers:
   a. Load the page's segments (English + Hebrew text)
   b. Strip nikud (vowel marks) from both Jeff's marker and segment text for matching
   c. Search each segment for the marker text
   d. If found: record segment index + character offset within segment
   e. If not found on the page: search adjacent pages (for cross-page corrections)
   f. If still not found: flag for manual review

**Nikud stripping:**
```python
import unicodedata
def strip_nikud(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text)
                   if unicodedata.category(c) != 'Mn')
```

**Output schema per correction:**
```json
{
    "story_key": "Ketubot 52b_4-5",
    "correction_type": "trim_start",
    "marker_text": "...",
    "found_in_segment": 4,
    "char_offset": 42,
    "current_start": 4, "current_end": 5,
    "proposed_start": 4, "proposed_end": 5,
    "proposed_start_char_offset": 42,
    "confidence": "high",
    "before_text_preview": "...",
    "after_text_preview": "..."
}
```

Uses Sefaria MCP tools for cross-page corrections where we need text from pages not in our results (e.g., Ketubot 12a).

### Phase 3b-3e: Apply Corrections (Commit D)

**New file: `scripts/apply_boundary_corrections.py`**

Reads `boundary_corrections.json` and applies to canonical JSON.

**Three correction types:**

**1. Boundary adjustments (15 stories):**
- Change `start_segment` or `end_segment`
- Add `start_text_marker` / `end_text_marker` for sub-segment precision (future use)
- For extend-start from previous page: convert to cross-page merge

**2. Same-page merges (3 stories):**
- 85a_8-8 + 85a_9-10 → single story 85a_8-10
- 25b_5-5 absorbed into 25b_4-5
- 103b_3-3 into longer narrative

**3. Cross-page merges (14 stories):**
Using existing merge fields:
```python
story['spans_pages'] = [page_n_ref, page_n1_ref]
story['start_segment_page2'] = <first continuation segment>
story['end_segment_page2'] = <last continuation segment>
# Remove continuation story from page N+1
```

For merge FIXES: undo bad merge first (pattern from `remerge_v9.py:undo_merge()`), then re-merge correctly.

**Verification:**
- [ ] Print before/after for each of 38 corrections
- [ ] Spot-check 10 corrections by reading segment text
- [ ] Verify 134 "correct" stories unchanged
- [ ] Run analysis script → all 53 items addressed

---

## Phase 4: Rebuild Golden Dataset (Commit E)

- Regenerate `ketubot_canonical.json` with all corrections
- Generate updated review UI for spot-checking
- Open in browser, verify 10 random stories
- Count: expect ~170-175 stories (down from 189)

**Git tag: `v10-golden-ketubot`**

---

## Phase 5: Evaluation Framework (Commit F)

### 5a. Composite Scoring Script

**New file: `scripts/evaluate_golden.py`** (IMMUTABLE after creation)

**Metrics:**
- **Classification F1:** Binary story/not-story against Jeff's labels
- **Boundary IoU:** Segment-level intersection-over-union for true positives
- **Merge accuracy:** Precision/recall of cross-page merge detection
- **Composite:** 0.4 * F1 + 0.4 * IoU + 0.2 * merge

Output: JSON with all subscores + per-story breakdown.

### 5b. Baseline Current Detector on Ketubot

Score existing v7/v9 results against golden dataset → `docs/golden/baseline_ketubot.json`

### 5c. Baseline on 2nd Tractate (Pre-Improvement)

1. Pick candidate tractate (suggest Bava Metzia — narrative-heavy)
2. Run current detector on 10-15 representative pages
3. Jeff spot-reviews ~20-30 stories → mini ground truth
4. Score → `docs/golden/baseline_tractate2.json`
5. **Purpose:** Catches overfitting. If Ketubot improves but tractate 2 doesn't, we've overfit.

**Git tag: `pre-detector-changes`** — THE rollback point for detector experiments

---

## Phase 6: Autoresearch Loop (Separate Branch)

**Branch: `feat/autoresearch-detector-improvements`**

### 6a. Setup

- `scripts/autoresearch/program.md` — agent instructions (what to optimize, constraints)
- `scripts/autoresearch/run_experiment.py` — automation (run detector, score, compare)

### 6b. Expand Ground Truth DB

Modify `src/ground_truth.py`: 128 → 187 entries, new error types, boundary correction fields.

### 6c. Run Loop

Each experiment = 1 commit. Improved → keep. Not improved → `git reset --hard HEAD~1`.
Target: ~50 experiments. Budget: ~$100.

### 6.5 VALIDATION GATE (before merging to main)

| Ketubot improved? | 2nd tractate improved? | Action |
|---|---|---|
| Yes (>5%) | Yes (>5%) | **MERGE to main** |
| Yes (>5%) | No change | Investigate overfitting |
| Yes (>5%) | Worse | **ROLLBACK** — overfitting |
| No change | — | More experiments needed |
| Worse | — | **ROLLBACK immediately** |

---

## Phase 7: Generalize to Other Tractates

Each tractate on its own branch: `feat/generalize-<name>`

1. Run detector with improvements + expanded few-shots
2. Auto-flag stories matching known error patterns
3. Jeff reviews only flagged stories (~70% workload reduction)
4. Each review batch → expand golden dataset → re-run autoresearch → detector improves

---

## Files Modified/Created Summary

| Phase | File | Action |
|-------|------|--------|
| 1 | `scripts/analyze_canonical_feedback.py` | Already created |
| 1 | `docs/golden/canonical_feedback_analysis.json` | Already created |
| 1 | `docs/golden/error_taxonomy.md` | Already created |
| 2 | `scripts/build_canonical.py` | Modify — add 4th feedback source |
| 2 | `results/canonical/ketubot_canonical.json` | Regenerate |
| 3 | `scripts/boundary_lookup.py` | Create |
| 3 | `docs/golden/boundary_corrections.json` | Create (output of lookup) |
| 3 | `scripts/apply_boundary_corrections.py` | Create |
| 4 | `results/canonical/ketubot_canonical.json` | Regenerate (final golden) |
| 4 | `validation/ui/canonical_review.html` | Regenerate (spot-check UI) |
| 5 | `scripts/evaluate_golden.py` | Create (IMMUTABLE) |
| 5 | `docs/golden/baseline_ketubot.json` | Create |
| 5 | `docs/golden/baseline_tractate2.json` | Create |
| 6 | `scripts/autoresearch/program.md` | Create |
| 6 | `scripts/autoresearch/run_experiment.py` | Create |
| 6 | `src/ground_truth.py` | Modify — expand to 187 entries |
| 6 | `src/story_detector_v7.py` | Modify — on branch only |

---

## Verification Summary

| Phase | Verification | Pass criteria |
|-------|-------------|---------------|
| 2 | Run analysis script | 15 classification items addressed |
| 3 | Print before/after text | 10/10 spot-checks correct |
| 3 | Regression check | 134 "correct" stories unchanged |
| 4 | Browser UI check | 10 random stories display correctly |
| 5 | Baseline score | F1 ~0.75-0.85 (reasonable range) |
| 6 | Validation gate | Both tractates improve >5% |

---

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Boundary lookup maps Hebrew markers to wrong segments | Print before/after text, spot-check 10 manually |
| Classification corrections have edge cases (106a, 111a) | Handle as special cases, verify individually |
| Cross-page merge logic introduces bugs | Use existing undo/redo pattern from remerge_v9.py |
| Autoresearch overfits to Ketubot | Validate on 2nd tractate before merging |
| Jeff's patterns don't generalize | Self-validation flags known patterns; Jeff reviews only flagged |
| Budget overrun on autoresearch | Cap at 50 experiments (~$100); review ROI after 25 |
| Composite metric doesn't capture quality | Compare scores with Jeff's qualitative spot-checks |
