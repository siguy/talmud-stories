# Bilingual Analysis - Hebrew/Aramaic + English

## Why Analyze Both Languages?

The tool analyzes **both the original Hebrew/Aramaic text and the English translation** simultaneously. This provides significantly better accuracy.

## Hebrew Narrative Markers

Hebrew has specific markers that signal narrative content:

| Marker | Transliteration | Translation | Usage |
|--------|-----------------|-------------|-------|
| **ויהי** | vayehi | "and it was" | Classic biblical/Talmudic story opener |
| **מעשה ב-** | ma'aseh be- | "an incident involving" | Explicit story introduction |
| **פעם אחת** | pa'am achat | "one time" | Temporal story marker |
| **אמר לו** | amar lo | "said to him" | Dialogue marker (gendered) |
| **אמרה לו** | amrah lo | "said to him" (fem.) | Dialogue with female speaker |
| **מה עשה** | mah asah | "what did he do?" | Action/response indicator |
| **בא אצל** | ba etzel | "came to" | Movement/action |
| **שלח לו** | shalach lo | "sent to him" | Communication action |

## Examples Where Hebrew Reveals More

### Example 1: Temporal Markers

**English:** "There was a time when..."
**Hebrew:** **פעם אחת** היה...

The Hebrew **פעם אחת** (pa'am achat - "one time") is a much stronger narrative signal than the English translation suggests.

### Example 2: Explicit Story Markers

**English:** "Rabbi Akiva had a case involving..."
**Hebrew:** **מעשה ברבי עקיבא** ש...

The Hebrew **מעשה ב-** (ma'aseh be-) literally means "an incident/story involving" - this is an explicit flag that what follows is a narrative, which might be lost in translation.

### Example 3: Dialogue Nuance

**English:** "He said, 'Why did you do this?'"
**Hebrew:** **אמר לו**: מפני מה עשית כך?

Hebrew preserves the direct dialogue marker **אמר לו** (said to him) which signals interpersonal narrative, whereas English might paraphrase.

### Example 4: Aramaic Storytelling Patterns

**Aramaic:** **הוה עובדא** (hava uvda - "there was an incident")
**English:** "It happened that..."

Aramaic portions of the Talmud have their own narrative markers.

## How the AI Uses Both

When analyzing, Claude:

1. **Reads both texts** side by side
2. **Identifies narrative markers** in Hebrew that may be obscured in English
3. **Cross-validates** - if both languages show narrative structure, confidence increases
4. **Handles translation gaps** - if one text is clearer, relies on that version
5. **Detects cultural context** - Hebrew preserves nuances lost in translation

## Example AI Analysis with Both Languages

**Input:**

**English:** "Once Rabbi Yochanan was walking and saw a poor man."

**Hebrew:** **פעם אחת** היה רבי יוחנן מהלך, וראה עני אחד.

**AI Assessment:**
```json
{
  "is_story": true,
  "confidence": 90,
  "reasoning": "Both English and Hebrew show strong narrative markers.
               Hebrew פעם אחת (pa'am achat) is explicit story opener.
               Both have temporal progression (was walking) and
               character action (saw). High confidence due to
               bilingual validation.",
  "hebrew_markers_found": ["פעם אחת", "ראה"]
}
```

## When Hebrew/Aramaic Isn't Available

Some passages may only have English translations. In these cases:
- AI analyzes English only
- Confidence scores may be slightly lower
- Still identifies narrative structure accurately

## Benefits of Bilingual Approach

✅ **Higher Accuracy** - Cross-validation between languages
✅ **Cultural Context** - Hebrew preserves Talmudic storytelling conventions
✅ **Better Coverage** - Finds stories missed by English-only analysis
✅ **Translation Quality Check** - Can identify when translations are incomplete
✅ **Wordplay Detection** - Hebrew puns and literary devices preserved

## Technical Details

The AI prompt includes both texts:

```
English Translation:
[English text here]

Hebrew/Aramaic Original:
[Hebrew text here]

Note: You can read both Hebrew and English. Use BOTH to determine if this is a story.
Hebrew narrative markers include: ויהי (vayehi), מעשה ב (ma'aseh be),
פעם אחת (pa'am achat), אמר לו (amar lo).
```

Claude models are fully multilingual and can understand:
- Modern Hebrew
- Biblical Hebrew
- Talmudic Aramaic
- Mixed Hebrew/Aramaic text (common in Talmud)

## Output Format

Stories are saved with **both** texts:

```json
{
  "ref": "Taanit 23a",
  "text": "Once the world was in need of rain...",
  "hebrew_text": "פעם אחת היה העולם צריך למטר...",
  "analysis": {
    "is_story": true,
    "confidence": 95
  }
}
```

## Future Enhancements

Possible improvements:
- Extract and tag specific Hebrew narrative markers found
- Analyze Aramaic vs. Hebrew sections differently
- Identify stories that ONLY work in Hebrew (wordplay, etc.)
- Detect when translation significantly differs from original
- Score translation quality for narrative clarity
