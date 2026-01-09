# Prompt Improvements Based on Expert Feedback

## Summary

Expert reviewer Jeffrey Rubenstein reviewed 25 AI-identified stories from Tractate Ketubot and found:
- **60% false positives** (15/25) - Legal discussions incorrectly marked as stories
- **32% correct** (8/25) - Real stories, but most needed "shrinking" to exclude legal context
- **Critical issue**: AI cannot distinguish legal hypotheticals from actual stories

## Changes Made

### 1. Updated AI Prompt (find_talmud_stories.py)

**New Requirements Added:**

#### Descriptive vs Prescriptive
- Stories must be **descriptive** (what DID happen)
- NOT **prescriptive** (what SHOULD happen, what the law is)
- Example: "A virgin is married on Wednesday" = prescriptive rule, NOT a story

#### One-Time Specific Events
- Must be a **specific instance** with named individuals
- NOT general rules or repeated actions
- Example: "Ravina arranged his son's marriage" ✅ vs "Women are always married on Wednesday" ❌

#### Causality Requirement
- **At least 2 events** with causal relationship
- Must show **change** (before → after)
- NOT single facts: "Rav Zevid had intercourse" = one event, not a story

#### Legal Hypotheticals Excluded
- "If X then Y" = hypothetical legal case, NOT a story
- Rabbi debates about law = legal positions, NOT stories
- Hypothetical scenarios used to illustrate legal principles = NOT stories

#### Validation Checklist
Added 7-point checklist AI must verify before marking something as a story:
1. Descriptive (not prescriptive)?
2. One-time specific event?
3. At least 2 events with causality?
4. Change or outcome?
5. Rabbis/post-biblical (not biblical)?
6. Actual event (not hypothetical)?
7. If embedded, identified just story portion?

### 2. Story Extraction Guidance

**Problem**: When AI found real stories, it included entire legal passages

**Solution**: Added guidance to:
- Identify where story begins and ends
- Return new fields: `story_start_marker`, `story_end_marker`
- Mark when story is `embedded_in_legal_context`
- AI should note just the story portion

### 3. Few-Shot Examples from Expert

Added real examples from Jeffrey's feedback:

**False Positive Examples:**
- "A virgin is married on Wednesday..." (prescriptive rule)
- "If a man gives a woman a ring..." (hypothetical)

**True Story Examples:**
- Ravina's son's marriage retraction (specific event, causality, change)
- Rabbi Gamliel's burial reform (before → after, causality)

### 4. New Response Fields

Added to JSON response:
```json
{
  "embedded_in_legal_context": true/false,
  "story_start_marker": "first few words where story begins",
  "story_end_marker": "last few words where story ends",
  "validation_notes": "explain which validation criteria were met or failed"
}
```

### 5. Validation Test Script

Created `validate_improvements.py` to test on expert-reviewed cases:
- Tests 6 cases (3 false positives, 3 true stories)
- Measures accuracy of improved prompt
- Saves detailed results to JSON

## Expected Improvements

### Before (Based on Feedback):
- 60% false positive rate
- Legal discussions marked as stories
- AI 85% confident on wrong calls
- Entire legal passages returned instead of just stories

### After (Expected):
- <20% false positive rate
- Legal discussions correctly excluded
- Lower confidence on edge cases
- Story extraction to return just story text

## Testing

Run validation:
```bash
export ANTHROPIC_API_KEY='your-key'
python3 validate_improvements.py
```

This tests the improved prompt on actual false positives from expert review.

## Key Insights from Expert

### What IS a Story:
1. **Specific one-time event**: "A certain man came before Rav Nahman..."
2. **Causal progression**: Event A → caused → Event B → resulted in → Outcome
3. **Change**: Before state → After state
4. **Named individuals**: Specific rabbis or characters
5. **Descriptive**: Tells what happened, not what should happen

### What is NOT a Story:
1. **Legal hypotheticals**: "If X then Y, the law is..."
2. **General rules**: "A virgin is married on Wednesday"
3. **Repeated actions**: "When Rabbi X would come..." (habitual)
4. **Single events**: "Rav Zevid did X" (no causality)
5. **Prescriptive**: "Should", "must", "the law is"

## Next Steps

1. ✅ Update prompt with expert distinctions
2. ✅ Add validation checklist
3. ✅ Add few-shot examples
4. ✅ Create test script
5. ⏳ Run validation tests
6. ⏳ If accuracy >80%, deploy to full analysis
7. ⏳ Re-analyze Ketubot with improved prompt
8. ⏳ Compare old vs new results
9. ⏳ Get expert validation on improved results

## Files Modified

- `find_talmud_stories.py` - Updated AI prompt with all improvements
- `validate_improvements.py` - New test script for validation

## Cost Estimate

Testing the 6 validation cases:
- ~$0.03-0.05 (using Claude 3.5 Haiku)

Re-analyzing all of Ketubot (224 pages):
- ~$0.50-1.00 (similar to original cost)

## Expert Contact

Jeffrey Rubenstein provided the feedback.
Next review: After implementing improvements and re-running analysis.
