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

---

## v5.1: Validation-Driven Improvements (Current)

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
cd src
export GOOGLE_API_KEY='your-key'
python story_detector_v5.py 2 39  # Ketubot pages 2-39
```

Results saved to `results/ketubot/v5/pages_2-39.json`
