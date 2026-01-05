# Running Ketubot Test

Quick guide to test the story finder on Tractate Ketubot.

## Prerequisites

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set your Anthropic API key:**
```bash
export ANTHROPIC_API_KEY='sk-ant-...'  # Your key from console.anthropic.com
```

## Run the Test

```bash
python test_ketubot.py
```

## What to Expect

### Prompt
```
Sample rate (1=all sections, 2=every other, default=1):
```

**Recommendation:** Start with `2` (every other section) for faster/cheaper testing.
- Sample rate 1: Analyzes ~200-250 sections, costs ~$0.50-1.00, takes 15-25 minutes
- Sample rate 2: Analyzes ~100-125 sections, costs ~$0.25-0.50, takes 8-12 minutes

### During Execution

You'll see:
```
============================================================
Analyzing Ketubot (Test) for narrative structure...
Using multi-page windowing to detect stories spanning pages
============================================================
  Analyzing 124 sections...
  ✓ Ketubot 8b - dialogue_vignette (confidence: 76%)
  ✓ Ketubot 17a - brief_anecdote (confidence: 82%)
    ... analyzed 10/124 sections
  ✓✓ Ketubot 62b-63a - MULTI-PAGE full_narrative (confidence: 91%)
  ✓ Ketubot 67b - full_narrative (confidence: 88%)
    ... analyzed 20/124 sections
```

Progress updates every 10 sections.

### Output

**Console summary:**
```
SUMMARY
=======
Total stories found: 38
  Single-page stories: 34
  Multi-page stories: 4

By type:
  Full narratives: 18
  Dialogue vignettes: 12
  Brief anecdotes: 8

Average confidence: 82.3%
High confidence stories (90%+): 12

Top 5 Stories by Confidence:
1. Ketubot 62b-63a - 95%
   Type: full_narrative
   Summary: Rabbi Akiva's wife supports him for 12 years while he studies Torah
   ...
```

**JSON file:** `ketubot_stories.json`
- Full text (English + Hebrew)
- Complete analysis for each story
- Sorted by confidence

## Known Stories in Ketubot

Famous stories you might find:
- **62b-63a**: Rabbi Akiva's wife and her sacrifices
- **67b**: Nakdimon ben Gurion's daughter
- **103-104**: Rabbi Yehuda HaNasi's death
- **17a**: Wedding stories and dancing before the bride

## Interpreting Results

### Story Types
- **full_narrative**: Multi-scene story with complete arc
- **dialogue_vignette**: Brief exchange with narrative progression
- **brief_anecdote**: Short narrative (2-3 sentences)

### Confidence Scores
- **90-100%**: Clear narrative, high certainty
- **75-89%**: Strong narrative, good confidence
- **60-74%**: Probable narrative, some ambiguity
- **Below 60%**: Borderline (may be worth manual review)

### Multi-Page Detection
Stories marked `✓✓` span consecutive pages. The tool:
1. Detected incomplete story on first page
2. Combined with next page
3. Found complete narrative with higher confidence

## Example Output Structure

```json
{
  "ref": "Ketubot 62b-63a",
  "book": "Ketubot",
  "text": "Rabbi Akiva was a shepherd...",
  "hebrew_text": "רבי עקיבא היה רועה צאן...",
  "analysis": {
    "is_story": true,
    "confidence": 95,
    "story_type": "full_narrative",
    "narrative_elements": {
      "has_beginning": true,
      "has_middle": true,
      "has_end": true,
      "has_characters": true,
      "has_action": true,
      "has_dialogue": true,
      "has_temporal_progression": true
    },
    "one_sentence_summary": "...",
    "reasoning": "...",
    "continuation": {
      "seems_incomplete": false,
      "missing_beginning": false,
      "missing_end": false,
      "note": ""
    }
  },
  "spans_multiple_pages": true
}
```

## Troubleshooting

**Error: "ANTHROPIC_API_KEY not found"**
- Run: `export ANTHROPIC_API_KEY='your-key'`
- Make sure to use your actual key from console.anthropic.com

**Taking too long?**
- Use sample_rate=2 or higher
- Or interrupt (Ctrl+C) and results will be partially saved

**Rate limit errors?**
- Script has 0.3s delay between requests
- If you hit limits, increase `time.sleep(0.3)` to `time.sleep(0.5)` in find_talmud_stories.py:385

**Low confidence scores?**
- This is normal - not everything is a story
- Legal discussions correctly get low scores
- Stories should naturally have 75%+ confidence

## Next Steps

After reviewing results:
1. Check `ketubot_stories.json` for full data
2. Review high-confidence stories manually
3. Look for false positives (marked as story but isn't)
4. Look for false negatives (stories missed)
5. Use findings to refine the system

## Cost Estimate

With Claude 3.5 Haiku:
- Sample rate 1 (all sections): ~$0.50-1.00
- Sample rate 2 (every other): ~$0.25-0.50

Actual cost depends on:
- Number of sections in Ketubot
- How many trigger multi-page analysis
- Text length per section
