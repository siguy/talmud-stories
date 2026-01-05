# Reviewer Guide: How to Review Talmud Stories

This guide will help you review AI-identified stories from the Talmud and provide expert feedback.

## Getting Started

### Step 1: Open the Review Interface

Open this link in your web browser:

**https://siguy.github.io/talmud-stories/review_stories.html**

The review interface will load automatically. You should see:
- A "Reviewer Name" field at the top
- Statistics about the stories
- Filter controls
- A list of stories to review

### Step 2: Enter Your Name

At the top of the page, you'll see a **"Reviewer Name"** field:
- Enter your full name (e.g., "Dr. Sarah Cohen")
- This will be saved automatically and included in your feedback
- You only need to enter it once - it will be remembered

---

## Understanding the Interface

### Top Section: Statistics

You'll see summary statistics:
- **Total Stories**: How many stories the AI found
- **Average Confidence**: The AI's average confidence score
- **Multi-Page Stories**: Stories spanning multiple Talmud pages
- **Story Types**: Breakdown by narrative type

### Filter Controls

Use these to focus your review:

1. **Search by Reference**
   - Type a page number (e.g., "62b", "67a", "103")
   - Instantly filters to matching stories

2. **Story Type**
   - **Full Narratives**: Complete stories with beginning, middle, end
   - **Dialogue Vignettes**: Brief exchanges with narrative progression
   - **Brief Anecdotes**: Short 2-3 sentence narratives

3. **Minimum Confidence**
   - Drag the slider to filter by AI confidence level
   - Example: Set to 80% to only see high-confidence results

4. **Multi-Page Stories**
   - Filter to see only stories spanning multiple pages
   - Or only single-page stories

---

## How to Review Stories

### Understanding Each Story Card

Each story shows:

#### Header
- **Reference** (e.g., "Ketubot 62b-63a")
- **Confidence Badge** (the AI's confidence: 60-100%)
- **Story Type Badge** (full_narrative, dialogue_vignette, brief_anecdote)
- **Multi-Page Badge** (if the story spans pages)

#### Summary
- One-sentence summary of what happens in the story

#### Length Adjustment Controls
- **➕ Expand Context** - Click if the story seems cut off or needs more context
- **➖ Shrink** - Click if too much non-story text is included
- These are recorded in your feedback

#### Text Display (Side-by-Side)
- **Left Column**: English Translation
- **Right Column**: Hebrew/Aramaic Original
- Both shown simultaneously for easy comparison

#### AI Reasoning
- Yellow box explaining why the AI thinks this is a story
- Helps you understand the AI's decision-making

#### Narrative Elements
- Checkmarks showing what elements the AI detected:
  - ✓ Beginning, Middle, End
  - ✓ Characters, Action, Dialogue
  - ✓ Temporal Progression

---

## Providing Feedback

For each story, you have three tasks:

### 1. Mark as Correct or False Positive

**✓ Correct Button (Green)**
- Click if the AI correctly identified a story
- The button will turn green when selected
- Click again to unmark if you change your mind

**✗ False Positive Button (Red)**
- Click if this is NOT actually a story
- Examples of false positives:
  - Pure legal discussions
  - Hypothetical cases without narrative
  - Rabbi debates about law (not stories about people)
  - Technical halakhic analysis
- The button will turn red when selected

### 2. Add Notes (Optional but Helpful)

In the notes field, you can add:
- Why you agree or disagree with the AI
- Additional context
- Suggestions for improvement
- Examples:
  - "Great catch! This is Rabbi Akiva's famous story"
  - "False positive - this is legal debate, not narrative"
  - "Story is correct but seems to start mid-narrative"
  - "Missing the conclusion - needs expansion"

### 3. Adjust Length If Needed

If the story boundaries seem wrong:
- **Click ➕ Expand**: If the story seems cut off or needs more context
- **Click ➖ Shrink**: If too much non-story text is included

This helps improve future story detection.

---

## Auto-Save Feature

### Your Progress is Automatically Saved! 💾

Every time you:
- Mark a story as correct/false positive
- Add or edit notes
- Adjust story length

Your feedback is **automatically saved** in your browser.

### Auto-Save Status

At the bottom of the page, you'll see:
- **💾 Auto-saved (X stories)** - Shows how many you've reviewed
- **Last saved: 2 minutes ago** - When your last change was saved

### What This Means

✅ **You can close the browser** - Your work is saved
✅ **Come back later** - Open the page again and continue
✅ **No "Save" button needed** - Everything saves automatically
✅ **Works offline** - After initial load, no internet needed for saving

**Important:** Your feedback is saved in **your browser** on **this computer**. If you switch to a different computer or browser, you'll start fresh.

---

## Exporting Your Feedback

### When You're Done Reviewing

1. Scroll to the bottom of the page
2. Click **📥 Download Feedback JSON** button
3. A file will download with a name like:
   ```
   ketubot_review_Sarah_Cohen_2026-01-05.json
   ```

### What Gets Exported

The JSON file contains:
- Your name
- Review date and time
- Total stories reviewed
- For each story you reviewed:
  - Reference (e.g., "Ketubot 62b")
  - Your feedback (correct/false positive)
  - Your notes
  - Length adjustments
  - Original AI confidence and story type

### Sharing Your Feedback

Email the downloaded JSON file to the AI team. They'll use it to improve the story detection system.

---

## Clearing Feedback

If you need to start over:

1. Click the **🗑️ Clear All Feedback** button (red)
2. You'll see a warning with confirmation
3. Click OK to clear everything

**⚠️ Warning:** This deletes all your saved progress. Export first if you want to keep a backup!

---

## Review Tips

### 1. What Makes a Story?

A story has:
- **Characters**: Named individuals doing things (not just holding legal positions)
- **Action**: Events that happen in sequence
- **Temporal progression**: Things unfold over time
- **Resolution**: Some outcome or conclusion

### 2. What is NOT a Story?

Common false positives:
- **Legal debates**: "Rabbi X says this, Rabbi Y says that" about law
- **Hypothetical cases**: "If a man does X, what is the law?"
- **Halakhic analysis**: Technical discussions of legal principles
- **Brief attributions**: "Rabbi X taught..." without narrative context

### 3. Edge Cases

**Dialogue-heavy stories:**
- Some stories are mostly dialogue but still narrative
- Ask: Do events progress? Is there resolution?

**Embedded stories in legal discussion:**
- Sometimes a story illustrates a legal point
- If it has narrative elements, it's still a story

**Multi-sentence exchanges:**
- Not every dialogue is a story
- Look for: setup, progression, outcome

### 4. Working Efficiently

**Start with high confidence:**
- Drag confidence slider to 90%
- Review the AI's most confident calls first
- These are usually easier decisions

**Then review low confidence:**
- Drop slider to 60-75%
- These need your expert eye most

**Use filters strategically:**
- Review by story type (do all full_narratives first)
- Review multi-page stories separately
- Search for specific pages you know well

**Take breaks:**
- Your work auto-saves
- Come back when fresh

### 5. How Much Detail in Notes?

**Minimum (helpful):**
- Just mark correct/false positive
- No notes needed for obvious cases

**Better (very helpful):**
- Brief note on why: "Legal debate, not story"
- Or: "Classic Rabbi Akiva story - correct"

**Best (extremely helpful):**
- Explain edge cases: "Technically a story but very brief - borderline"
- Note patterns: "AI keeps flagging hypothetical cases as stories"
- Suggest improvements: "Should look for 'ma'aseh' marker more"

---

## Common Questions

### Q: Do I need to review every story?

**No!** Review as many or as few as you have time for. Even reviewing 20-30 stories provides valuable data.

### Q: What if I'm not sure if something is a story?

Mark it based on your best judgment and add a note: "Borderline case - could go either way." Your uncertainty is valuable feedback!

### Q: Can I skip stories?

Yes! Just scroll past any you don't want to review. Only the ones you mark/comment on are included in your export.

### Q: What if the AI missed a story?

This interface only shows stories the AI found. To report missed stories, note them separately and share with the AI team.

### Q: How long will this take?

Depends on how many you review:
- Quick pass (mark 20 stories): ~10-15 minutes
- Thorough review (mark 100 stories): ~1-2 hours
- Complete review (all 243): ~3-4 hours

Remember: You can do it in multiple sessions since it auto-saves!

### Q: What happens to my feedback?

The AI team uses it to improve the story detection system through:
1. Pattern analysis (what types of errors does the AI make?)
2. Prompt refinement (how to teach the AI to avoid those errors)
3. Validation (how accurate is the system overall?)

Your expert knowledge directly improves the AI!

---

## Troubleshooting

### Problem: Page won't load the stories

**Solution:**
- Make sure you're using the correct link: https://siguy.github.io/talmud-stories/review_stories.html
- Check your internet connection
- Try refreshing the page (press F5 or Cmd+R)
- Try a different browser (Chrome, Firefox, or Safari)

### Problem: My feedback disappeared

**Possible causes:**
- Switched browsers (feedback is browser-specific)
- Switched computers (feedback is local to your machine)
- Cleared browser cache (clears localStorage)

**Prevention:** Export your feedback regularly!

### Problem: Can't click buttons

**Solution:** Refresh the page. If that doesn't work, clear your browser cache and reload.

### Problem: Hebrew text not showing

**Solution:** Make sure your browser supports Unicode and RTL text. Try Chrome or Firefox.

---

## Quick Reference Card

| Action | How To |
|--------|--------|
| Mark as correct story | Click green **✓ Correct** button |
| Mark as false positive | Click red **✗ False Positive** button |
| Add notes | Type in "Optional notes..." field |
| Story needs more text | Click **➕ Expand Context** |
| Story includes too much | Click **➖ Shrink** |
| Filter to specific page | Type in "Search by Reference" |
| See only high confidence | Drag "Minimum Confidence" slider |
| Save your work | **Automatic** - no action needed! |
| Export feedback | Click **📥 Download Feedback JSON** |
| Start over | Click **🗑️ Clear All Feedback** |

---

## Getting Help

If you encounter any issues or have questions:

1. **Technical issues**: Contact the AI development team
2. **Questions about Talmudic content**: Use your expert judgment
3. **Unclear edge cases**: Make your best call and add a note explaining your reasoning

---

## Thank You!

Your expert review is invaluable for improving AI story detection in the Talmud. Every piece of feedback helps the system get better at identifying and understanding narrative structures in rabbinic literature.

**Happy reviewing!** 📚
