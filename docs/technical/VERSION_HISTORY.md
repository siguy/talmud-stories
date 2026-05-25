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
| v9 | Feb 2026 | Remerge | Undo 12 bad cross-page merges, re-stitch from segment 0 |
| Canonical | Mar 2026 | Unified Dataset | Merge all feedback into single 189-story canonical file |
| v10 Golden | Mar 2026 | Golden Dataset | 182 stories, 48 corrections, composite 0.93. Detector experiments reverted. |
| Kiddushin | Mar 2026 | Generalization Test | 96 stories on new tractate. Stage 4f continuation check. Awaiting Jeff review. |
| v8 Wave 1 | May 2026 | Mechanical fixes | Cross-page seg-0 fix, gap-aware continuation, triage lexical override, Mishnah filter |
| v8 Wave 2 | May 2026 | Boundary + biblical | Start-snap to introducer, end-trim stam markers, biblical-actor demotion; first Kiddushin golden |

---

## v8 Wave 2: Boundary Snap + Biblical Filter (2026-05-24)

**Goal:** Address remaining classes of error from Jeff's 2026-04-23 Kiddushin review with deterministic post-processors.

**Changes** (all in `src/story_detector_v8.py`, Stage 4):
1. **`snap_start_to_introducer`** — extends story start back when the segment immediately before the detected start opens with a canonical introducer (`ההוא ד`, `ההיא`, `מעשה ב`, `כי הא ד`, etc.). Snap-forward variant fires on segments within the first 3 of a story.
2. **`trim_trailing_stam_segments`** — drops trailing segments opening with stam-Talmud markers (`שמע מינה`, `מאי טעמא`, `אי הכי`, `שאני`, `תא שמע`, etc.).
3. **`filter_biblical_actor_stories`** — demotes stories whose `criteria.identifiable_characters.evidence` names only biblical figures (Moses, David, Nebuchadnezzar, Ezra, "Jewish people" collective, etc.) to NOT_A_STORY.

**Kiddushin golden built this session:** `results/canonical/kiddushin_canonical.json` from `scripts/build_kiddushin_canonical.py`, promoting Jeff's 96 reviews into 85 confirmed real stories + 11 NOT_A_STORY reclassifications.

**Scores** (fresh both waves, same day):

| Tractate | Metric | Wave 1 | Wave 2 | Δ |
|---|---|---:|---:|---:|
| Kiddushin | Classification F1 | 0.9101 | 0.9257 | +0.016 |
| Kiddushin | Boundary IoU | 0.9856 | 0.9815 | -0.004 |
| Kiddushin | Merge F1 | 0.6667 | 0.6667 | 0.000 |
| **Kiddushin** | **Composite** | **0.8916** | **0.8962** | **+0.005** |
| Ketubot | Classification F1 | 0.8952 | 0.8952 | 0.000 |
| Ketubot | Boundary IoU | 0.9569 | 0.9563 | -0.001 |
| Ketubot | Merge F1 | 0.8780 | 0.8780 | 0.000 |
| **Ketubot** | **Composite** | **0.9164** | **0.9162** | **-0.0002** |

**Activity:**
- Biblical filter fired 3x on Kiddushin (38a, 69b, 72b). Zero on Ketubot.
- Start snap fired 3x (Kid 12a, Ket 67b, Ket 85a) — all extend-back to a textbook introducer.
- End trim fired 0x — Lesson 12 explains why (Jeff's end-boundary cases are text-internal).

**Files added:**
- `scripts/apply_wave2.py` — runs Wave 2 filters on Wave 1 outputs without LLM re-call
- `scripts/build_kiddushin_canonical.py` — Kiddushin golden builder
- `scripts/verify_wave2.py` — 10-check pass/fail report
- `scripts/compare_v8_waves.py` — Wave 1 vs Wave 2 delta table
- `results/v8/wave2/{kiddushin_v8,ketubot_v8_2-60,ketubot_v8_61-112}.json`
- `docs/golden/v8/wave2_results.md` — full writeup
- `docs/golden/v8/baselines/{kiddushin,ketubot}_wave1_baseline.json`

**Key findings (Lessons 12, 13):**
- Most of Jeff's boundary feedback is text-internal (within a single segment); segment-level mechanical fixes can't reach it. Wave 3 must edit at sub-segment text granularity.
- Strict composite-score gates penalize correct improvements when expert hasn't reviewed the affected cases. Shipped Wave 2 despite -0.0002 on Ketubot — both Ketubot snaps are rabbinically correct and flagged for Jeff's next review round.

**Commit:** `1c4d18d`

---

## v8 Wave 1: Mechanical Fixes from Jeff's 2026-04-23 Kiddushin Review (2026-05-17)

**Goal:** Ship four mechanical fixes targeting Jeff's first-pass Kiddushin feedback. No model change, no prompt rewrite.

**Changes:**
1. **Cross-page first-segment skip fix** (Issue #1) — `merge_cross_page_stories_v7` Case 5: when both pages flag continuation and page2 starts at seg 1, force include seg 0.
2. **Gap-aware continuation** (Issue #2) — reject any cross-page bridge with intervening segments between story end and page boundary.
3. **Triage lexical override** (Issue #5) — pages containing canonical introducers (`מעשה ב`, `הנהו בי תרי`, `ההוא ד`, `כי הא ד`) force Stage 2 to run.
4. **Mishnah-only story filter** (Issue #7) — stories entirely within a Mishnah block (Sefaria `מתני׳`/`גמ׳` markers) moved to `mishnah_stories`.

**Results:**
- Kiddushin: 11/11 verification checks pass. 2 missed stories recovered (45a, 53a). 3/4 false bridges removed. 1 Mishnah story bucketed.
- Ketubot: composite 0.8576 → 0.9164 (+0.06) — Issue #1 fix also caught same bug on 103b→104a.

**Key finding (Lesson 11):** LLM nondeterminism breaks historical baselines. Always generate a fresh baseline same-day before comparing.

**Files:** `src/story_detector_v8.py` (forked from v7, kept v7 untouched), `scripts/run_kiddushin_wave1.py`, `scripts/verify_wave1.py`, `scripts/compare_ketubot_v7_v8.py`, `docs/golden/v8/wave1_results.md`.

**Commit:** `eff0218`

---

## Kiddushin Run: First Generalization Test

**Date:** 2026-03-27
**Tractate:** Kiddushin 2a-82b (162 pages)
**Model:** gemini-3-flash-preview

**What this tests:** Does the detector generalize beyond Ketubot? Uses Ketubot examples as cross-tractate few-shots (no contamination). Target: 0.85+ composite.

**Results:**
- 162 pages fetched, 109 skipped by triage (67% skip rate)
- 53 pages processed → 96 stories detected
- Classification: 34 YES, 16 HIGH, 46 LOW, 5 NOT_A_STORY
- 12 cross-page stories: 5 merge, 4 stitch, 3 continuation check (new)

**New: Stage 4f Continuation Check**
Added `continuation_check()` method to `story_detector_v7.py`. For stories near page boundaries without continuation flags, asks: "Does THIS specific story continue on the next page?" Caught 3 stories the existing merge passes missed (including the Dama ben Netina story, 31a→31b). See `docs/golden/kiddushin_run_plan.md` for design rationale.

**Pipeline Stage 4 Updated:**
```
4a: Boundary refinement
4b: Cross-page merge v7
4c: Legacy merge (continuation flags)
4d: Cross-page stitching (targeted LLM)
4f: Continuation check (new — for unmerged boundary stories)
4e: Duplicate detection
```

**Files created:**
- `scripts/run_kiddushin.py` — Run script
- `results/kiddushin/kiddushin_v7.json` — Detection results
- `results/kiddushin/event_triage_kiddushin.json` — Triage results
- `results/kiddushin/kiddushin_pages.json` — Cached Sefaria pages
- `validation/generators/generate_kiddushin_review_ui.py` — Review UI generator
- `validation/ui/kiddushin_review.html` — Review UI for Jeff

**Review URL:** https://siguy.github.io/talmud-stories/validation/ui/kiddushin_review.html

**Status:** Awaiting Jeff's review. Will score against his labels and compare to Ketubot baseline.

---

## v10 Golden: Definitive Ketubot Ground Truth

**Date:** 2026-03-25
**Tag:** `v10-golden-ketubot`

**What changed:** Processed Jeff's comprehensive canonical review (all 189 stories, March 2026) into the definitive ground truth. Applied 17 classification corrections + 32 boundary/merge corrections. Built evaluation framework.

**Results:**
- 182 stories (down from 189: merges + FP removal)
- Classification F1: 0.92, Boundary IoU: 0.98, Merge F1: 0.86, Composite: 0.93
- 26 false positives identified (legal discussions with narrative framing)
- 0 needs_review remaining

**Detector experiments (REVERTED):**
- Tried expanding few-shot examples from 128 to 282 entries → overfitting (0.93 → 0.89)
- Tried strengthening legal disqualifiers in prompt → catastrophic regression (0.93 → 0.57)
- Tried ML post-processing classifier → features don't separate FPs from TPs
- Root cause: train/test contamination + genuine ambiguity at domain expertise level
- Conclusion: 0.93 is the prompt-based ceiling for Ketubot. Tag `pre-detector-changes` marks rollback point.

**Key files:**
- `results/canonical/ketubot_canonical.json` — the golden dataset
- `scripts/evaluate_golden.py` — IMMUTABLE evaluation harness
- `docs/golden/` — findings, research, error taxonomy, workflow docs
- `tasks/lessons.md` — 8 lessons learned

**Documentation:** See `docs/golden/findings_v10_golden_dataset.md` for full writeup.

---

## Canonical: Unified Dataset for Ketubot

**Goal:** Merge all of Jeff's feedback (v4 through v8) into a single validated canonical file.

**Canonical File:** `results/canonical/ketubot_canonical.json`
- Base: v7 (pages 2-60) + v9 (pages 61-112)
- 189 total stories

**Corrections Applied:**
| Category | Count |
|----------|-------|
| Auto-applied (clear Jeff feedback) | 30 |
| Needs review (ambiguous notes) | 19 |
| No change needed | 143 |

**AI Accuracy:** 84% (143/170 stories correct where Jeff gave clear verdicts)

**Most Common Error:** Over-classification — 21 of 30 corrections were downgrades (AI classified higher than Jeff would)

**Review UI:** `validation/ui/ketubot_canonical_review.html`
- 3 collapsible sections: Needs Review (19), Auto-Applied (27), All Other (143)
- Classification filter (YES/HIGH_CONFIDENCE/LOW_CONFIDENCE/NOT_A_STORY)
- Full story cards with text, criteria, feedback buttons
- Hosted: https://siguy.github.io/talmud-stories/validation/ui/ketubot_canonical_review.html

**Files:**
- `scripts/build_canonical.py` — Builds canonical from base results + feedback
- `results/canonical/ketubot_canonical.json` — The canonical file
- `validation/generators/generate_canonical_review_ui.py` — UI generator (all 189 stories)
- `validation/ui/ketubot_canonical_review.html` — Review interface

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
