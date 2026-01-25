# Multi-Page Story Detection and Continuation Analysis

## Overview

The tool now detects stories that span multiple consecutive pages (e.g., 2a → 2b → 3a) using intelligent windowing and continuation detection.

## The Three Key Features

### 1. Hebrew Markers Are HINTS, Not Requirements ✓

**Important:** The AI performs **semantic analysis** of narrative structure, NOT keyword matching.

Hebrew narrative markers like ויהי (vayehi), מעשה ב (ma'aseh be), פעם אחת (pa'am achat) are mentioned to the AI as **optional hints**, not requirements.

**Many stories have NONE of these markers** and are still correctly identified by analyzing:
- Does it have a beginning (setup)?
- Does it have a middle (action/conflict)?
- Does it have an end (resolution)?

### 2. Multi-Page Story Detection

Stories often span across consecutive Talmud pages. The tool now:

**Two-Pass Analysis:**

#### Pass 1: Analyze Each Page Individually
```
2a → Analyze alone
2b → Analyze alone
3a → Analyze alone
```

#### Pass 2: Detect Continuation & Combine
```
If 2a analysis shows: "seems_incomplete: true, missing_end: true"
  → Fetch 2a + 2b together
  → Analyze combined text
  → If combined version has:
     - Higher confidence (+10% or more)
     - Complete story (no missing end)
     → Mark as multi-page story with ref "2a-2b"
```

**Example:**
```
Page 23a alone:
  "Once there was drought. Honi drew circle..."
  Analysis: is_story=true, confidence=65%, missing_end=true

Page 23b alone:
  "...rain fell properly. People went to Temple."
  Analysis: is_story=false, confidence=40%, missing_beginning=true

Pages 23a-23b combined:
  "Once there was drought...rain fell properly. People went to Temple."
  Analysis: is_story=true, confidence=95%, seems_incomplete=false
  ✓✓ SAVED AS MULTI-PAGE STORY
```

### 3. Continuation Detection

The AI now analyzes whether a story appears complete or continues beyond the passage.

**New JSON field in analysis:**
```json
"continuation": {
  "seems_incomplete": true/false,
  "missing_beginning": true/false,
  "missing_end": true/false,
  "note": "explanation if story continues or starts mid-narrative"
}
```

**Use cases:**

#### Story Starts Mid-Narrative
```json
{
  "ref": "Taanit 23b",
  "text": "...and then rain fell heavily",
  "continuation": {
    "seems_incomplete": true,
    "missing_beginning": true,
    "missing_end": false,
    "note": "Story appears to start mid-action, likely continues from previous page"
  }
}
```

#### Story Ends Mid-Narrative
```json
{
  "ref": "Berakhot 34a",
  "text": "Rabbi Akiva began to speak...",
  "continuation": {
    "seems_incomplete": true,
    "missing_beginning": false,
    "missing_end": true,
    "note": "Story setup and action present, but no resolution shown"
  }
}
```

#### Complete Story
```json
{
  "ref": "Taanit 23a",
  "continuation": {
    "seems_incomplete": false,
    "missing_beginning": false,
    "missing_end": false,
    "note": ""
  }
}
```

## How It Works

### Algorithm Flow

```
For each page in tractate:

  1. Fetch and analyze page alone
     ↓
  2. Check if is_story = true
     ↓ yes
  3. Save story
     ↓
  4. Check continuation.seems_incomplete or continuation.missing_end
     ↓ yes
  5. Fetch current page + next page
     ↓
  6. Analyze combined text
     ↓
  7. Is combined confidence > single confidence + 10%?
     AND combined story is complete (no missing_end)?
     ↓ yes
  8. Save as multi-page story (ref: "23a-23b")
     Mark: spans_multiple_pages = true
     ↓
  9. Deduplication: Don't save same story twice
```

### Deduplication

Stories are deduplicated using a key: `first_200_chars:ref`

This prevents:
- Saving both "23a" and "23a-23b" for the same story
- Duplicate stories in overlapping windows

### Output Fields

**New fields in results:**

```json
{
  "ref": "Taanit 23a-23b",  // Combined reference
  "spans_multiple_pages": true,  // New field
  "analysis": {
    "continuation": {  // New nested object
      "seems_incomplete": false,
      "missing_beginning": false,
      "missing_end": false,
      "note": ""
    }
  }
}
```

## Examples

### Example 1: Story Spanning Two Pages

**Scenario:** Honi the Circle Drawer story spans 23a and 23b

**Output:**
```json
{
  "ref": "Taanit 23a-23b",
  "text": "[Full combined text from both pages]",
  "hebrew_text": "[Full combined Hebrew from both pages]",
  "analysis": {
    "is_story": true,
    "confidence": 95,
    "story_type": "full_narrative",
    "continuation": {
      "seems_incomplete": false,
      "missing_end": false
    }
  },
  "spans_multiple_pages": true
}
```

**Console output:**
```
✓✓ Taanit 23a-23b - MULTI-PAGE full_narrative (confidence: 95%)
```

### Example 2: Story Contained in Single Page

**Output:**
```json
{
  "ref": "Berakhot 5b",
  "spans_multiple_pages": false,
  "analysis": {
    "continuation": {
      "seems_incomplete": false
    }
  }
}
```

**Console output:**
```
✓ Berakhot 5b - brief_anecdote (confidence: 85%)
```

### Example 3: Incomplete Fragment (Not Combined)

If a page has a partial story but combining doesn't improve confidence:

**Page 12a alone:**
```json
{
  "confidence": 60,
  "continuation": {
    "missing_end": true,
    "note": "Story seems to continue but next page not available or doesn't complete it"
  }
}
```

**Page 12a-12b combined:**
```json
{
  "confidence": 62,  // Only +2%, not enough improvement
  "continuation": {
    "seems_incomplete": true  // Still incomplete
  }
}
```

**Result:** Only single-page version saved (combined didn't help)

## Performance Considerations

### Additional API Calls

Multi-page detection requires extra API calls:
- **Without windowing:** N calls for N pages
- **With windowing:** ~1.2-1.5× N calls (only when continuation detected)

**Cost impact:** ~20-50% more API calls, but catches stories that would otherwise be missed

### Rate Limiting

Script includes `time.sleep(0.3)` between analyses to respect API limits.

For combined analyses, the same rate limiting applies.

## Configuration

### Enable/Disable Windowing

```python
# Enable multi-page detection (default)
finder = SefariaStoryFinder(analyzer, use_windowing=True)

# Disable (single-page only, faster)
finder = SefariaStoryFinder(analyzer, use_windowing=False)
```

### Tuning Parameters

In the code (find_talmud_stories.py:398):

```python
# Confidence boost required to use combined version
if combined_analysis['confidence'] > analysis['confidence'] + 10:
    # Use combined version
```

You can adjust `+ 10` to be more or less aggressive:
- `+ 5`: More aggressive combining (may combine unrelated content)
- `+ 15`: More conservative (may miss some multi-page stories)

## Limitations

### Currently Handles:
- ✓ Stories spanning 2 consecutive pages (2a→2b, 2b→3a)
- ✓ Deduplication of overlapping stories
- ✓ Continuation detection

### Does Not Yet Handle:
- ✗ Stories spanning 3+ pages (would need recursive windowing)
- ✗ Non-consecutive page spanning (story on 2a, continues on 4a)
- ✗ Stories interrupted by unrelated content

### Future Enhancements:

1. **Recursive windowing:** If 2a-2b still incomplete, try 2a-2b-3a
2. **Smart chunking:** Detect natural boundaries (paragraph breaks, topic shifts)
3. **Story threading:** Follow story across non-consecutive references
4. **Confidence calibration:** Learn optimal threshold from labeled data

## Validation

To validate multi-page detection works:

1. Test on known multi-page stories (e.g., Honi in Taanit 23a-23b)
2. Check for false positives (unrelated pages combined)
3. Compare single-page vs. multi-page confidence scores
4. Review `continuation.note` explanations

## Summary

✅ **Hebrew markers** are hints, NOT requirements - semantic analysis is primary
✅ **Multi-page detection** finds stories spanning 2a→2b→3a using intelligent windowing
✅ **Continuation detection** identifies incomplete stories and triggers combining

The tool now catches stories that were previously missed due to page boundaries!
