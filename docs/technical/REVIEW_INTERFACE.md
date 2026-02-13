# Validation Review Interface

Interactive web interface for expert validation of AI-detected Talmud stories.

## Quick Start

### Open a Validation UI

```bash
# macOS
open validation/ui/ketubot_2-39.html

# Or double-click the file in Finder/Explorer
```

No server needed - runs entirely in browser.

## Available Interfaces

| File | Content | Purpose |
|------|---------|---------|
| `validation/ui/ketubot_2-39.html` | 33 stories | General review (pages 2-39) |
| `validation/ui/ketubot_40-60.html` | 22 stories | Fresh content review |
| `validation/ui/jeff_comparison.html` | 33 stories | Compare with v4.1 validations |

## Features

### Statistics Dashboard
- Stories by classification (YES / HIGH / LOW)
- Review progress counter
- Filter counts

### Classification Badges

| Badge | Meaning | Criteria |
|-------|---------|----------|
| **YES** (green) | Definite story | 6/6 criteria, no weakeners |
| **HIGH** (blue) | Strong story | 5-6 criteria, minor weakeners |
| **LOW** (yellow) | Possible story | 3-4 criteria, needs review |

### Story Cards

Each story displays:

**Text Display:**
- Side-by-side English and Hebrew/Aramaic
- Story segments highlighted (yellow background)
- ±1 segment context shown

**Criteria Breakdown:**
```
✓ identifiable_characters - Rav Ḥisda, Rabba bar Rav Huna (or "a certain man")
✓ multiple_events - Going, consoling, speaking (physical actions)
✓ causal_chain - Go → Console → Say blessing
✓ temporal_progression - Before → during → after
✓ descriptive - What they DID do
✓ change_outcome - Mourners consoled
```

**Disqualifiers/Weakeners:**
- 🚫 Disqualifiers (if any) - would make NOT_A_STORY
- ⚠️ Weakeners (if any) - downgrade confidence

**AI Reasoning:**
- One-sentence summary
- Classification reasoning
- Self-check adjustments (if any)

### Filtering

- **Classification**: YES only, HIGH only, LOW only, or all
- **Page search**: Type "8b" to find stories on that page
- **Disqualifiers**: Show only stories with/without disqualifiers

### Feedback System

For each story:
- **✓ Correct** - Classification is accurate
- **✗ Incorrect** - Classification is wrong
- **Notes** - Add explanation or observations

Feedback auto-saves to browser localStorage.

### Export

Click "Download Feedback JSON" to export:

```json
{
  "reviewer": "Jeff",
  "version": "v5.1_validation",
  "exportDate": "2026-01-25T...",
  "totalStories": 33,
  "reviewed": 33,
  "feedback": {
    "Ketubot 8b_3-5": {
      "verdict": "correct",
      "note": "Clear mourning narrative",
      "reviewer": "Jeff",
      "timestamp": "2026-01-25T..."
    }
  }
}
```

## Review Guidelines

### What Makes a Story (YES/HIGH)

✓ **Identifiable characters** - named rabbis OR anonymous ("a certain man/woman") - both valid!
✓ **Multiple NARRATIVE events** - physical actions, state changes (not legal talk)
✓ **Causal chain** - Event A CAUSED Event B (not just sequential)
✓ **Temporal progression** - before → during → after
✓ **Descriptive** - what DID happen (not hypothetical)
✓ **Transformation** - situation changed from beginning to end

### What's a Borderline Story (LOW)

○ One real event + rabbinic discussion about it
○ Mainly dialogue/speech acts but with some real events
○ Weak causality but some change

### What's NOT a Story

✗ **Rabbi legal opinions** - "Rabbi X quotes Rabbi Y as saying..." (attribution, not narrative)
✗ **Legal deliberation** - Thinking about acting, experiencing legal difficulty
✗ **Legal debate settings** - Sage sitting before another debating, academy vs academy
✗ **Sequential events** - Things that happened but didn't cause each other
✗ **Simple reports** - Actions without transformation
✗ **Hypotheticals** - "If someone were to..."
✗ **MISHNA sections** - Legal codifications
✗ **Habitual actions** - "He would regularly..."
✗ **Verbal statements as events** - "It is all talk" (objections, rulings, orders)

### Common Edge Cases

**Legal case with narrative elements:**
- If it has all 6 criteria → probably a story
- If just illustrating a law → probably not

**Brief dialogue:**
- Has progression and change → dialogue vignette (story)
- Just statement and response → probably not

**"Once Rabbi X...":**
- Followed by actions and outcome → story
- Just attribution of a saying → not a story

## Generating New UIs

After running analysis:

```bash
cd validation/generators
python generate_review_ui.py ../../results/ketubot/v5/pages_2-39.json ../../validation/ui/ketubot_2-39.html
```

## Technical Notes

- **No server required** - Pure HTML/JavaScript
- **Auto-save** - Feedback saved to localStorage
- **Works offline** - After initial load
- **All browsers** - Chrome, Firefox, Safari, Edge

## File Locations

```
validation/
├── ui/                          # HTML interfaces
│   ├── ketubot_2-39.html
│   ├── ketubot_40-60.html
│   └── jeff_comparison.html
├── generators/                  # Scripts to create UIs
│   ├── generate_review_ui.py
│   └── generate_jeff_comparison_ui.py
└── feedback/                    # Expert feedback JSONs
    └── jeff_v4.1_validation.json
```

## Workflow

1. **Run detection** → `src/story_detector_v6.py` (current) or `src/story_detector_v5.py`
2. **Generate UI** → `validation/generators/generate_review_ui.py`
3. **Review stories** → Open HTML in browser
4. **Export feedback** → Click download button
5. **Analyze results** → Use feedback to improve detection
