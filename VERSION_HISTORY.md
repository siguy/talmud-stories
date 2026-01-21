# Test Version History

This document tracks all test versions and their results for the Talmud Stories detection project.

---

## Version Overview

| Version | Name | Date | Approach | Key Files |
|---------|------|------|----------|-----------|
| v1 | Basic Detection | Jan 5, 2025 | Simple AI prompt, full page text | `tests/v1_basic/` |
| v2 | Multi-Story | Jan 19, 2025 | Enhanced prompt for multiple stories per page | `tests/v2_multi_story/` |
| v3 | Full Page + Anchors | Jan 20, 2025 | Text anchor boundaries instead of char offsets | `tests/v3_full_page/` |
| v4 | Segment-Based | Jan 20, 2025 | Segment preservation + marker detection + continuation merging | `tests/v4_segment_based/` |

---

## v1: Basic Detection (Jan 5, 2025)

**Approach:**
- Simple AI prompt asking "is this a story?"
- Full page text sent to AI
- Single story per page assumption

**Files:**
- `tests/v1_basic/test_ketubot.py`
- `results/v1/ketubot_stories_b_pages.json`
- `results/v1/ketubot_stories_complete.json`

**Results:**
- ~200 stories found in Ketubot
- High false positive rate on legal discussions
- No multi-story detection

**Issues:**
- Ketubot 2a incorrectly flagged as story (legal discussion)
- Ketubot 3a, 3b false positives
- Missed multi-story pages

---

## v2: Multi-Story Detection (Jan 19, 2025)

**Approach:**
- Enhanced prompt for multiple stories per page
- Added Jeff Rubenstein's criteria
- Better false positive filtering

**Files:**
- `tests/v2_multi_story/test_multi_story.py`
- `results/v2/test_multi_story_results.json`

**Results:**
- Improved detection of multiple stories per page
- Better rejection of legal discussions
- Still had boundary accuracy issues

**Issues:**
- Character offsets unreliable (AI can't count accurately)
- Story boundaries cut off mid-sentence

---

## v3: Full Page + Text Anchors (Jan 20, 2025)

**Approach:**
- Store full page text
- AI returns text anchors (first/last words) instead of char offsets
- Programmatic anchor matching with fuzzy search

**Files:**
- `tests/v3_full_page/test_full_page_approach.py`
- `results/v3/test_full_page_results.json`

**Results:**
- Better boundary accuracy
- Hebrew text still truncated vs English
- Anchor matching sometimes fragile

**Issues:**
- Hebrew/English alignment imperfect
- Over-segmentation on story-rich pages

---

## v4: Segment-Based Detection (Jan 20, 2025)

**Approach:**
- Preserve Sefaria's aligned segment structure
- Pre-process with Hebrew/English marker detection
- Character extraction for continuation detection
- Story grouping to merge multi-segment narratives
- Jeff Rubenstein's validated criteria in prompt

**Files:**
- `tests/v4_segment_based/test_segment_approach.py`
- `results/v4/test_segment_results.json`

**Key Innovations:**
1. **Segment Preservation**: `text[]` and `he[]` arrays are 1:1 aligned
2. **Hebrew Markers**: מעשה, כי הא ד, פעם אחת, יומא חד
3. **Continuation Detection**: Pronoun starters, shared characters, flow words
4. **Story Grouping**: Merge connected segments into single stories

**Validation Results:**

| Page | v4 Result | Jeff's Validation | Match |
|------|-----------|-------------------|-------|
| Ketubot 2a | 0 stories | NOT a story | ✓ |
| Ketubot 3a | 0 stories | NOT a story | ✓ |
| Ketubot 3b | 0 stories | NOT a story | ✓ |
| Ketubot 8b | 1 story | IS a story | ✓ |
| Ketubot 10b | 3 stories | 3 stories | ✓ |
| Ketubot 20b | 1 story | IS a story | ✓ |

**Improvements over v3:**
- Ketubot 62b: 7 stories (was 10) - proper merging
- Ketubot 67b: 5 stories with correct multi-segment grouping
- Zero false positives on legal discussion pages

---

## Jeff Rubenstein's Expert Validations

Reference validations from Talmud scholar (stored in `results/validation_results.json`):

| Reference | Expert Verdict | Notes |
|-----------|----------------|-------|
| Ketubot 2a | NOT a story | Legal discussion about wedding days |
| Ketubot 3a | NOT a story | Hypothetical legal case |
| Ketubot 3b | NOT a story | Legal discussion |
| Ketubot 8b | IS a story | Mourning narratives |
| Ketubot 10b | IS a story (3) | Three separate case stories |
| Ketubot 20b | IS a story | Rav Ashi memory story |

---

## Directory Structure

```
talmud-stories/
├── tests/
│   ├── v1_basic/           # Original simple approach
│   ├── v2_multi_story/     # Multi-story detection
│   ├── v3_full_page/       # Text anchor approach
│   └── v4_segment_based/   # Current best approach
├── results/
│   ├── v1/                 # v1 output files
│   ├── v2/                 # v2 output files
│   ├── v3/                 # v3 output files
│   ├── v4/                 # v4 output files
│   └── validation_results.json
├── find_talmud_stories.py  # Main library
├── review_stories.html     # Review UI
└── VERSION_HISTORY.md      # This file
```

---

## Running Tests

```bash
# v4 (current best) - segment-based approach
python tests/v4_segment_based/test_segment_approach.py

# Full tractate analysis
python test_ketubot.py gemini 1
```
