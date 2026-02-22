# Version History

## Overview

| Version | Date | Approach | Key Change |
|---------|------|----------|------------|
| v1 | Jan 2025 | Basic Detection | Simple AI prompt, single story per page |
| v2 | Jan 2025 | Multi-Story | Multiple stories per page |
| v3 | Jan 2025 | Text Anchors | Boundary detection with anchors |
| v4 | Jan 2025 | Segment-Based | Preserve Sefaria segment structure |
| v4.1 | Jan 2025 | Expert Validation | Jeff Rubenstein validation (50% false positive rate) |
| v5.0 | Jan 2025 | Categorical | YES/HIGH/LOW/NOT_A_STORY classification |
| v5.1 | Jan 2025 | Validation-Driven | Address all false positive patterns |
| v6 | Feb 2025 | Comprehensive | Cross-page merge, self-check, anti-legal disqualifiers |
| v7 | Feb 2025 | Hybrid Pipeline | 4-stage decomposed detection, 87.4% accuracy |
| v7+pp | Feb 2025 | Post-Processing | v6 ensemble rule boosts to 89.8% |
| v7 (G3 Flash) | Feb 2026 | Model Upgrade | Gemini 3 Flash hits **92.1%** — new best |
| v7 (61-112) | Feb 2026 | Generalization | 98 stories on unseen Ketubot pages 61-112 |
| v8 | Feb 2026 | Cross-Page Fix | Fix 14 cut-off stories + 5 missing conclusions from Jeff's review |

---

## v8: Cross-Page Continuation + Story Boundary Fix

**Goal:** Fix 14 stories cut off at page boundaries and 5 stories missing their narrative conclusion, based on Jeff's review of pages 61-112.

**Expert Review (pages 61-112):** 109/113 stories reviewed, 96.3% accuracy (105 correct, 4 incorrect, 2 false positives)

**Root Causes:**
1. Pipeline processes pages individually — stories split at page boundaries not merged
2. Merge logic only handled NOT_A_STORY + real story combinations, not real + real
3. Legacy merge required BOTH continuation flags (too strict)
4. Boundary trimmer removed DELIBERATION segments that were actually resolving rulings
5. Prompt told LLM to end at "final narrative action" — too aggressive

**Changes:**

1. **Prompt: Boundary Rules** — Story END now includes rabbi's ruling that resolves the narrative case, consequences, and outcomes. Added notes that abrupt endings and "beyond the letter of the law" are not weakeners.

2. **Prompt: Cross-Page Continuation** — New section instructing LLM when to set `continues_from_previous_page` and `continues_to_next_page` flags. Explicit note that pagination is a printing artifact.

3. **Expanded Cross-Page Context** — Previous/next page context expanded from 3→5 segments, English from 150→300 chars, added Hebrew (200 chars), added event type annotations from triage.

4. **Case 4 Merge** — New merge case for when BOTH page N's last story and page N+1's first story are real stories at the boundary with continuation flags. Uses `_pick_higher_classification`, combines summaries.

5. **Relaxed Legacy Merge** — Changed from requiring BOTH continuation flags to at least ONE (`and` → `or`). NOT_A_STORY guards still prevent false merges.

6. **Boundary Trimmer Guard** — New `_segment_has_ruling()` check prevents trimming DELIBERATION segments that contain ruling verbs (ruled, permitted, forbade, etc.) AND mention a character from the story.

7. **Post-Detection Stitching** — New `stitch_cross_page_continuation()` method for stories with `continues_to_next_page=true` but no merge happened. Makes targeted LLM call with story text + first 8 segments of next page to find where the story ends. Estimated 5-8 API calls per run.

**Files Modified:**
- `src/story_detector_v7.py` — All changes (prompt, context, merge, stitching, boundary trimmer)

**Pipeline Stage 4 Updated:**
```
4a: Boundary refinement (trim DELIBERATION, guard rulings)
4b: Cross-page merge v7 (NOT_A_STORY combos + Case 4 real+real)
4c: Legacy merge (relaxed to OR for continuation flags)
4d: Cross-page stitching (targeted LLM for unmerged boundary stories)
4e: Duplicate detection
```

**v8 Results (pages 61-112):**
| Metric | v7 | v8 | Change |
|--------|-----|-----|--------|
| Total stories | 113 | 103 | -10 (merges reduced count) |
| Real stories (YES+HIGH+LOW) | 107 | 100 | -7 |
| Cross-page stories | 7 | 16 | +9 new merges |
| Unmerged continuations | 14 | 0 | All resolved |

**Delta Review UI:**
- `validation/generators/generate_delta_review_ui.py` — compares v7 vs v8 results
- `validation/ui/ketubot_61-112_v8_delta.html` — focused review showing only changes
- Tier 1 (8): Cross-page merges — stories that now span two pages
- Tier 2 (10): New stories (5), status flips (1), truly removed (4)
- Tier 3 (31): Absorbed into merges (11) + classification changes (20)
- Skipped: 69 unchanged stories

---

## Phase 4: Ketubot 61-112 — Generalization Test

**Goal:** Test pipeline on unseen Ketubot pages (61a-112b) to validate generalization.

**Setup:**
- 104 new pages fetched from Sefaria API (pages 61a through 112b)
- Winning pipeline: v7 + Gemini 3 Flash (92.1% on pages 2-60)
- Full pipeline: triage → detection → boundary refinement → cross-page merge

**Results:**
| Metric | Value |
|--------|-------|
| Total pages | 104 |
| Triage skip rate | 50% (52 skipped, 52 kept) |
| Stories found | 98 (35 YES, 20 HIGH, 43 LOW) |
| NOT_A_STORY | 8 |
| Cross-page merges | 7 |

**Comparison with pages 2-60:**
| Metric | Pages 2-60 | Pages 61-112 |
|--------|-----------|--------------|
| Total pages | 118 | 104 |
| Triage skip rate | 66% | 50% |
| Stories/kept page | ~2.5 | ~1.9 |

The lower skip rate (50% vs 66%) suggests pages 61-112 have more narrative content.
Awaiting Jeff's review for accuracy validation.

**New Files:**
- `scripts/run_ketubot_61_112.py` — Phase 4 execution script
- `results/v7/ketubot_v7_61-112.json` — Detection results
- `results/v7/event_triage_61-112.json` — Triage results
- `results/v7/ketubot_pages_61-112.json` — Cached Sefaria pages
- `validation/ui/ketubot_61-112.html` — Review UI for Jeff

**Technical Changes:**
- Fixed `event_triage.py` for Gemini 3 compatibility (thinking mode, JSON repair)
- Fixed `story_detector_v7.py` to handle list-type JSON responses from Gemini 3

---

## v7 + Gemini 3 Flash: 92.1% (Current Best)

**Goal:** Migrate from gemini-2.0-flash (sunset March 2026) and test newer models

**Result:** 117/127 (92.1%) — +6 over v7 baseline, +3 over v7+pp

**Model Comparison (all using v7 pipeline + triage):**
| Model | Raw | +Post-Processing | Cost (40 pages) |
|-------|-----|------------------|-----------------|
| gemini-2.0-flash | 87.4% (111/127) | 89.8% (114/127) | ~$0.05 |
| gemini-3-pro-preview | 89.8% (114/127) | 90.6% (115/127) | ~$1.23 |
| **gemini-3-flash-preview** | **92.1% (117/127)** | **92.1% (117/127)** | ~$0.31 |

**Key Findings:**
- Flash > Pro (surprise) — Pro is too conservative, misses borderline stories
- Post-processing adds nothing to G3 Flash (model itself is better)
- G3 Flash found 8b_6-10 story that no previous version detected
- Gemini 3 models require `response_mime_type='application/json'` + thinking config

**Technical: Gemini 3 Thinking Mode**
- Gemini 3 models use "thinking" tokens that count against `max_output_tokens`
- Without fix: truncated JSON, 78.7% accuracy (most pages get 0 stories)
- Flash fix: `thinking_budget=0` disables thinking for structured output
- Pro fix: `max_output_tokens=32768` (Pro requires thinking, can't disable it)
- Both: filter out thinking parts from response, use `response_mime_type='application/json'`

**Ablation Results (which v7 components matter):**
| Configuration | Score |
|--------------|-------|
| v6 (baseline) | 82.7% (105/127) |
| v7-no-triage (all 118 pages) | 83.5% (106/127) |
| v6+triage+merge | 87.4% (111/127) |
| v7 | 87.4% (111/127) |
| v7+pp | 89.8% (114/127) |
| **v7 + G3 Flash** | **92.1% (117/127)** |

Triage is the key component (+4.7%). v7 constrained prompt ≈ v6 when both use triage.

**New Files:**
- `src/post_processing.py` — Mechanical post-processing rules (v6 ensemble)
- `tests/ablation_test.py` — Ablation test framework
- `tests/model_comparison.py` — Multi-model comparison runner
- `results/v7/ketubot_g3flash_2-60.json` — G3 Flash results
- `results/v7/ketubot_g3pro_2-60.json` — G3 Pro results
- `results/v7/ablation_*.json` — Ablation test results

---

## v7: Hybrid Pipeline — Decomposed Detection + Cross-Page Merge

**Goal:** Decompose the monolithic v6 prompt into stages, reducing legal misidentification errors

**Expert Review Stats (v6):** 82.7% agreement (105/127) with Jeff's labels
**v7 Result:** 87.4% agreement (111/127), +6 net improvement over v6

**Architecture: 4-Stage Pipeline**

```
Stage 1: Event Triage → classify segments as NARRATIVE_EVENT/VERBAL_ACT/DELIBERATION/HABITUAL
                        → skip pages with <2 narrative events (~66% skip rate)
Stage 2: Constrained Detection → event-annotated prompt, anti-legal few-shots from Ground Truth DB
Stage 3: Adversarial Validation → three-call pattern (disabled — net negative in testing)
Stage 4: Boundary Refinement → trim DELIBERATION at edges + improved cross-page merge
```

**Key Components:**

1. **Ground Truth DB** (`src/ground_truth.py`)
   - Structures Jeff's 128 labels with error types and passage patterns
   - Auto-generates few-shot examples per stage
   - Error types: LEGAL_MISIDENTIFICATION, MISSED_STORY, BOUNDARY_ERROR, CROSS_PAGE_BLEED

2. **Event Triage** (`src/event_triage.py`)
   - Classifies every segment into 4 event types using Gemini Flash
   - Skip pages with <2 NARRATIVE_EVENT (or <1 NARRATIVE + <2 VERBAL_ACT)
   - 66.1% skip rate, 1 false skip (saves ~60% of detection API calls)

3. **Constrained Detection** (`src/story_detector_v7.py`)
   - Segments pre-annotated with event types: `[NARRATIVE_EVENT] Seg 3: "Rabbi Yochanan said..."`
   - Explicit "legal is not a story" instruction with Jeff's examples
   - Self-check can only DEMOTE or CONFIRM (never promote)

4. **Boundary Refinement + Cross-Page Merge**
   - Trim DELIBERATION segments from story edges using triage event types
   - Improved cross-page merge: uses NARRATIVE_EVENT at page boundaries to detect
     story fragments even when one side is NOT_A_STORY
   - Promotes and merges when both sides have narrative events at boundary

**Scorecard vs Jeff's 128 labels:**
| Metric | v6 | v7 |
|--------|-----|-----|
| Agreement | 82.7% (105/127) | 87.4% (111/127) |
| Fixes from v6 | — | 10 |
| Regressions from v6 | — | 4 |
| Net change | — | +6 |

**Remaining regressions (4):**
- 3 legal misidentifications (8a, 40b, 52a)
- 1 triage false skip (51a)

**Files:**
- `src/ground_truth.py` — Ground Truth DB
- `src/event_triage.py` — Event Triage (Stage 1)
- `src/story_detector_v7.py` — Detection + Adversarial + Merge
- `results/v7/ketubot_v7_2-60.json` — Results
- `results/v7/event_triage_2-60.json` — Pre-computed triage
- `tests/v7_regression_test.py` — Side-by-side regression test

---

## v6: Comprehensive Revision from Jeff's v5.1 Validation

**Goal:** Address all 20 errors and ~12 refinements from Jeff's 128-passage review

**Expert Review Stats (v5.1):** 128 reviewed, 107 correct (86%), 18 incorrect, 3 null-with-notes

**Error Breakdown:**
| Category | Count | Root Cause |
|----------|-------|------------|
| False positives (legal activity ≠ story) | 7 | Legal deliberation/debate mistaken for events |
| False negatives (anonymous chars) | 5 | Anonymous characters penalized incorrectly |
| Cross-page / boundary splits | 5 | No cross-page awareness |
| Should be borderline, not rejected | 3 | Too strict on borderline classification |

**Key Changes:**

1. **Criterion renamed: `identifiable_characters` (was `named_characters`)**
   - Anonymous characters ("a certain man/woman") now count FULLY
   - Jeff: "Stories can be about unnamed people. The anonymous character does not weaken the confidence."
   - Partial naming removed as weakener

2. **What constitutes a "narrative event" (refined)**
   - NOT events: verbal statements, legal arguments, deliberation, thinking about acting, traveling to debate, legal difficulty/resolution, ordering someone, "instituting" a practice
   - ARE events: physical actions, changes in state, concrete outcomes
   - Jeff: "The events here are rabbis making legal arguments... that is not really an event"

3. **New disqualifiers: `legal_deliberation`, `legal_debate_setting`**
   - "Levi thought about acting" = deliberation, not event
   - "Legal debate between Pumbedita and Matta Mehasia" = not story
   - "One sage sitting before another debating" = setting, not story

4. **Removed disqualifier: `biblical_narrative`**
   - Jeff validated a King David story as correct (Ketubot 9b)

5. **Borderline story calibration**
   - One event + discussion = LOW_CONFIDENCE (not NOT_A_STORY)
   - Jeff: "should be marked a borderline story" (~15 instances)
   - New LOW_CONFIDENCE examples from Jeff's actual feedback

6. **Story boundary trimming**
   - Stories start at first narrative event, not preceding legal ruling
   - Stories end at final action, not following Talmudic commentary
   - Exception: Rabbi who directly references story events IS part of story
   - Self-check now suggests boundary adjustments

7. **Cross-page story merging (new)**
   - Phase 1: Fetch all pages
   - Phase 2: Classify with cross-page context (prev/next page segments visible)
   - Phase 3: Post-processing merge of stories split by page boundaries
   - Fixes ~5 errors from Jeff's review

8. **Duplicate story detection (new)**
   - Detects same story quoted on multiple pages
   - Jeff: "This is the same story as on Ketubot 2b"

9. **Self-check expanded to 9 questions**
   - Added: boundary check, borderline check, character role test
   - Boundary adjustments applied automatically

10. **12+ new curated examples from Jeff's v5.1 feedback**
    - Including borderline (LOW_CONFIDENCE) examples
    - NOT_A_STORY examples for legal debate settings, deliberation

**Files:**
- `src/story_detector_v6.py`
- `results/ketubot/v6/` (when run)

---

## v5.1: Validation-Driven Improvements

**Goal:** Reduce false positive rate from 50% to <20%

**Key Changes:**
1. **New disqualifier: `rabbi_legal_opinion`**
   - Jeff's insight: "AI confuses attribution with characters"
   - Catches: "Rabbi X quotes Rabbi Y as saying..."
   - Impact: Applied 53 times on Ketubot 2-39

2. **Stricter causality test**
   - Before: "Events connected by cause and effect"
   - After: "Event A CAUSED Event B, which CAUSED Event C"
   - Rejects sequential events without causal connection

3. **Stricter change test**
   - Before: "Situation different at end"
   - After: "Situation TRANSFORMED from beginning to end"
   - Rejects simple reports without transformation

4. **Boundary detection**
   - Commentary markers: טַעְמָא דְּ (ta'ama de)
   - Continuation markers: זִמְנָא אַחֲרִינָא (on another occasion)

5. **Self-check mechanism**
   - 7 validation questions including Jeff's patterns
   - Made 21 adjustments on Ketubot 2-39

6. **Curated examples**
   - 12 validated examples with exact Hebrew text
   - 4 YES, 4 NOT_A_STORY from expert validation

**Results (Ketubot):**
| Range | Stories | YES | HIGH | LOW |
|-------|---------|-----|------|-----|
| Pages 2-39 | 33 | 3 | 14 | 16 |
| Pages 40-60 | 22 | 2 | 15 | 5 |

**Files:**
- `src/story_detector_v5.py`
- `tests/v5_categorical/test_categorical_classification_v5.1.py`
- `results/ketubot/v5/`

---

## v5.0: Categorical Classification

**Goal:** Replace percentage scores with actionable categories

**Classification System:**
- **YES**: All 6 criteria met, no weakeners
- **HIGH_CONFIDENCE**: 5-6 criteria, minor weakeners
- **LOW_CONFIDENCE**: 3-4 criteria, needs review
- **NOT_A_STORY**: <3 criteria or disqualifier

**Six Criteria:**
1. Named characters (specific rabbis)
2. Multiple events (not single action)
3. Causal chain (A → B → Outcome)
4. Temporal progression (before → during → after)
5. Descriptive (what DID happen)
6. Change/outcome (transformation)

**Disqualifiers:**
- MISHNA section
- Hypothetical scenario
- Habitual actions
- Pure legal ruling
- Rabbi legal opinion (added in v5.1)

**Weakeners:**
- Minimal causality
- Minimal change
- Simple report
- Embedded in legal discussion

---

## v4.1: Expert Validation Phase

**Goal:** Get expert feedback on v4 detection accuracy

**Validator:** Jeffrey Rubenstein (Talmud scholar)

**Results:** 30 stories validated
- 15 TRUE positives
- 15 FALSE positives (50% error rate)

**False Positive Patterns Identified:**
1. **Rabbi legal opinions (27%)** - Attribution confused with characters
2. **Simple reports (33%)** - Actions without transformation
3. **Sequential events (7%)** - Events without causal connection
4. **Boundary issues (33%)** - Stories too long or too short

**Key Examples:**
- Ketubot 14b: Girl drew water, was raped = SEQUENTIAL not causal
- Levi wedding visit = REPORT not transformation
- Rabbi attribution = LEGAL OPINION not story

**Impact:** All patterns addressed in v5.1

---

## v4: Segment-Based Detection

**Goal:** Preserve Sefaria's aligned segment structure

**Key Innovations:**
1. **Segment preservation**: text[] and he[] arrays 1:1 aligned
2. **Hebrew markers**: מעשה, כי הא ד, פעם אחת, יומא חד
3. **Continuation detection**: Pronouns, shared characters, flow words
4. **Story grouping**: Merge connected segments into single stories

**Validation Results:**
| Page | v4 Result | Expert | Match |
|------|-----------|--------|-------|
| Ketubot 2a | 0 stories | NOT a story | ✓ |
| Ketubot 3a | 0 stories | NOT a story | ✓ |
| Ketubot 8b | 1 story | IS a story | ✓ |
| Ketubot 10b | 3 stories | 3 stories | ✓ |

**Files:** `tests/v4_segment_based/`

---

## v3: Full Page + Text Anchors

**Goal:** Better boundary detection

**Approach:**
- Store full page text
- AI returns text anchors (first/last words)
- Programmatic anchor matching

**Issues:**
- Hebrew/English alignment imperfect
- Anchor matching fragile

**Files:** `tests/v3_full_page/`

---

## v2: Multi-Story Detection

**Goal:** Find multiple stories per page

**Approach:**
- Enhanced prompt for multiple stories
- Added initial expert criteria

**Issues:**
- Character offsets unreliable
- Boundaries cut mid-sentence

**Files:** `tests/v2_multi_story/`

---

## v1: Basic Detection

**Goal:** Initial prototype

**Approach:**
- Simple AI prompt
- Full page text
- Single story per page

**Issues:**
- High false positive rate on legal discussions
- Missed multi-story pages

**Files:** `tests/v1_basic/`

---

## Expert Validations Reference

Stored in `validation/feedback/jeff_v4.1_validation.json`

| Reference | Expert Verdict | Notes |
|-----------|----------------|-------|
| Ketubot 2a | NOT a story | Legal discussion about wedding days |
| Ketubot 3a | NOT a story | Hypothetical legal case |
| Ketubot 8b | IS a story | Mourning narratives |
| Ketubot 10b | IS a story (3) | Three separate case stories |
| Ketubot 14b | NOT a story | Sequential events, not causal |

---

## Running Current Version

```bash
export GOOGLE_API_KEY='your-key'

# v7 with Gemini 3 Flash (current best)
GEMINI_MODEL=gemini-3-flash-preview PYTHONPATH=. python3 src/story_detector_v7.py
# Or pass model_name to V7StoryDetector constructor

# Model comparison (run detection + regression test)
PYTHONPATH=. python3 tests/model_comparison.py --model gemini-3-flash-preview

# Score all existing results
PYTHONPATH=. python3 tests/model_comparison.py --score

# Ablation tests
PYTHONPATH=. python3 tests/ablation_test.py --test score

# Regression test
PYTHONPATH=. python3 tests/v7_regression_test.py
```
