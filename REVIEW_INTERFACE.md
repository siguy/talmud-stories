# Story Review Interface

Beautiful, interactive web interface for expert review of AI-identified Talmud stories.

## Quick Start

### 1. Generate the Data (if you haven't already)

```bash
export ANTHROPIC_API_KEY='your-key'
python test_ketubot.py
```

This creates `ketubot_stories.json`

### 2. Open the Review Interface

Simply **double-click** `review_stories.html` or open it in your browser:

```bash
# macOS
open review_stories.html

# Linux
xdg-open review_stories.html

# Windows
start review_stories.html
```

That's it! No server, no setup, no technical knowledge needed.

## Features

### 📊 Statistics Dashboard
- Total stories found
- Average confidence score
- High-confidence stories (90%+)
- Multi-page story count

### 🔍 Powerful Filtering
- **Search by reference**: Type "62b" to find stories on that page
- **Filter by story type**: Full narratives, dialogue vignettes, or brief anecdotes
- **Confidence slider**: Only show stories above a certain confidence level
- **Multi-page filter**: View only multi-page or single-page stories

### 📖 Story Cards
Each story displays:
- **Reference** (e.g., "Ketubot 62b-63a")
- **Confidence score** with color coding:
  - 🟢 Green (90%+): High confidence
  - 🟡 Yellow (75-89%): Medium confidence
  - 🔴 Red (<75%): Low confidence
- **Story type badge**
- **Multi-page indicator** (if applicable)
- **AI-generated summary**
- **English translation** (show/hide)
- **Hebrew/Aramaic original** (show/hide)
- **AI reasoning** explaining why it was classified as a story
- **Narrative elements** detected (beginning, middle, end, characters, dialogue, etc.)

### ✅ Expert Feedback System

For each story, mark:
- **✓ Correct** - This IS a story
- **✗ False Positive** - This is NOT a story
- **Notes field** - Add any comments or explanations

### 📥 Export Feedback

Click "Download Feedback JSON" to export your review as a structured file containing:
```json
{
  "reviewed_at": "2026-01-05T14:32:18Z",
  "tractate": "Ketubot",
  "total_stories": 38,
  "reviewed_count": 38,
  "feedback": [
    {
      "ref": "Ketubot 62b-63a",
      "feedback_type": "correct",
      "notes": "Classic Rabbi Akiva story",
      "story_confidence": 95,
      "story_type": "full_narrative",
      "spans_multiple_pages": true
    },
    {
      "ref": "Ketubot 17a",
      "feedback_type": "false_positive",
      "notes": "This is actually a legal discussion about dance, not a story",
      "story_confidence": 76,
      "story_type": "dialogue_vignette",
      "spans_multiple_pages": false
    }
  ]
}
```

## Usage Tips

### For Expert Reviewers

1. **Start with high confidence**: Set confidence slider to 90% to see the best matches first
2. **Check multi-page stories**: These often contain the most complete narratives
3. **Read the AI reasoning**: Helps understand why it was classified as a story
4. **Compare Hebrew and English**: Sometimes the narrative is clearer in one language
5. **Use notes liberally**: Your insights are valuable for improving the system

### What to Look For

**Correct Stories (✓):**
- Has clear beginning, middle, end
- Characters perform actions
- Temporal progression (things happen in sequence)
- Resolution or outcome
- Even brief vignettes count if they have narrative arc

**False Positives (✗):**
- Pure legal discussions (even with "once" or "if someone")
- Hypothetical cases for legal illustration
- Lists of rulings
- Abstract debates
- Parables without narrative structure

### Common Edge Cases

**Borderline Cases:**
- Legal case study with narrative elements → Use your judgment
- Brief dialogue with progression → Probably a story (dialogue_vignette)
- "Once Rabbi X said..." without action → Probably not a story (just a saying)

**Multi-Page Stories:**
- Check if the combined text truly forms one narrative
- Sometimes AI combines unrelated passages

## Understanding Story Types

### Full Narrative
Complete story with multiple scenes, rich detail, clear arc.
**Example:** Honi the Circle Drawer (multiple scenes, dialogue, resolution)

### Dialogue Vignette
Brief exchange with narrative progression.
**Example:** "Rabbi X asked Y about prayer. Y responded with a question. X understood and changed his practice."

### Brief Anecdote
Short narrative (2-3 sentences) showing an event.
**Example:** "Rabbi Yochanan was walking and saw carobs. He asked if they were ownerless, ate them, then had to pay."

## Exporting for Analysis

After reviewing all stories, export your feedback:

1. Click "Download Feedback JSON"
2. File saves as `ketubot_review_YYYY-MM-DD.json`
3. Share with the AI team for:
   - Calculating precision (% of AI identifications that are correct)
   - Identifying patterns in false positives
   - Improving the AI prompt
   - Training labeled dataset

## Privacy & Data

- Everything runs **locally in your browser**
- No data sent to any server
- No internet connection needed (after loading)
- Your feedback stays on your computer until you export

## Browser Compatibility

Works in all modern browsers:
- ✅ Chrome/Edge (recommended)
- ✅ Firefox
- ✅ Safari

## Troubleshooting

**"ketubot_stories.json not found"**
- Make sure you ran `python test_ketubot.py` first
- The HTML file must be in the same directory as ketubot_stories.json

**Hebrew text not displaying correctly**
- Try a different browser (Chrome/Firefox recommended)
- Hebrew displays right-to-left automatically

**Filters not working**
- Try refreshing the page
- Make sure JavaScript is enabled

**Export button does nothing**
- Check that you've marked at least one story with feedback
- Try a different browser

## Next Steps

After reviewing Ketubot:
1. Export your feedback
2. Share with the research team
3. They can use your expert labels to:
   - Calculate accuracy metrics
   - Improve the AI prompt
   - Build a training dataset
   - Run on other tractates with higher confidence

## Contact

Questions about the interface or how to provide feedback?
- The interface is self-contained HTML/JavaScript
- No installation or technical knowledge required
- Just open in browser and start reviewing!
