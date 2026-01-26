# How It Works

## Overview

This system detects narrative stories in Talmud text using AI-powered semantic analysis with expert-validated criteria.

```
Sefaria API → Fetch segments → Detect markers → AI classification → Self-check → Output
```

## Pipeline Stages

### Stage 1: Fetch Text from Sefaria

```python
# Preserves aligned segment structure
{
  "ref": "Ketubot 8b",
  "segments": [
    {"index": 0, "english": "...", "hebrew": "..."},
    {"index": 1, "english": "...", "hebrew": "..."},
    # text[] and he[] are 1:1 aligned
  ]
}
```

### Stage 2: Hebrew Marker Detection

Each segment is pre-processed to detect narrative signals:

**Story Markers (Positive):**
- `מעשה` (ma'aseh) - "an incident"
- `יומא חד` (yoma chad) - "one day"
- `פעם אחת` (pa'am achat) - "one time"
- `כי הא ד` (ki ha d') - "like this case"

**Dialogue Markers:**
- `אמר ליה` / `א"ל` (amar leih) - "said to him"
- `אמר לה` (amar lah) - "said to her"

**Legal Markers (Negative):**
- `מתני` (matni) - Mishna indicator
- `הלכה` (halakha) - legal ruling
- `תנו רבנן` (tanu rabbanan) - "the Rabbis taught"

**Boundary Markers:**
- `טַעְמָא דְּ` (ta'ama de) - commentary begins (stop)
- `זִמְנָא אַחֲרִינָא` - "on another occasion" (extend)

### Stage 3: AI Classification

Using Gemini 2.0 Flash, each segment is evaluated against **6 criteria**:

| Criterion | Question | Example |
|-----------|----------|---------|
| named_characters | Specific rabbis, not generic "a person"? | "Rav Reḥumi", "Rabban Gamliel" |
| multiple_events | More than one action/event? | Not just "Rabbi X said Y" |
| causal_chain | Event A CAUSED Event B CAUSED Outcome? | Not just sequential |
| temporal_progression | Before → during → after? | Time passes in narrative |
| descriptive | What DID happen (not hypothetical)? | Not "if X were to..." |
| change_outcome | Situation TRANSFORMED? | Not just action report |

**Classification:**
- **YES**: 6/6 criteria, no weakeners
- **HIGH_CONFIDENCE**: 5-6 criteria, minor weakeners
- **LOW_CONFIDENCE**: 3-4 criteria
- **NOT_A_STORY**: <3 criteria OR disqualifier

### Stage 4: Disqualifiers

Any of these → automatic NOT_A_STORY:

| Disqualifier | Catches |
|--------------|---------|
| `MISHNA_section` | Legal codification |
| `hypothetical_case` | "If X were to do Y..." |
| `habitual_actions` | "He would regularly..." |
| `pure_legal_ruling` | Law without narrative |
| `rabbi_legal_opinion` | "Rabbi X quotes Rabbi Y as saying..." |

### Stage 5: Weakeners

These downgrade confidence but don't disqualify:

- `minimal_causality` - Events connected but not strongly causal
- `minimal_change` - Change is subtle
- `simple_report` - Action without transformation
- `embedded_in_legal_discussion` - Story within legal context

### Stage 6: Self-Check

7 validation questions asked after initial classification:

1. Are events CAUSAL or just SEQUENTIAL?
2. Is this a TRANSFORMATION or just a REPORT?
3. Are rabbis CHARACTERS or just ATTRIBUTING opinions?
4. Is this HYPOTHETICAL or actual events?
5. Is there a real CHANGE in situation?
6. Are there NAMED characters with agency?
7. Does it have TEMPORAL progression?

If answers contradict initial classification → adjust.

## Example Classification

**Ketubot 8b (Segments 3-5):**
```
When Rav Ḥisda and Rabba bar Rav Huna would go to console mourners in
the house of the Exilarch, they would say...
```

**Criteria Met:**
- ✓ named_characters: Rav Ḥisda, Rabba bar Rav Huna
- ✓ multiple_events: Going, consoling, speaking
- ✓ causal_chain: Go → Console → Say blessing
- ✓ temporal_progression: Before visit → during → after
- ✓ descriptive: What they DID do
- ✓ change_outcome: Mourners consoled

**Result:** YES (6/6, no weakeners)

---

**Ketubot 14b (Sequential, not causal):**
```
A girl went out to draw water. She was raped.
```

**Criteria Analysis:**
- ✓ named_characters: No specific name (weak)
- ✓ multiple_events: Went out, was raped
- ✗ causal_chain: Going out didn't CAUSE rape (sequential)
- ✓ temporal_progression: Before → after
- ✓ descriptive: What happened
- ✗ change_outcome: No transformation shown

**Self-Check:** "Are events CAUSAL or just SEQUENTIAL?" → SEQUENTIAL

**Result:** NOT_A_STORY (failed causality, self-check flagged)

## Output Format

```json
{
  "tractate": "Ketubot",
  "pages": [
    {
      "ref": "Ketubot 8b",
      "segments": [
        {"index": 0, "english": "...", "hebrew": "..."}
      ],
      "stories": [
        {
          "start_segment": 3,
          "end_segment": 5,
          "classification": "YES",
          "criteria": {
            "named_characters": {"met": true, "evidence": "Rav Ḥisda..."},
            "causal_chain": {"met": true, "chain": "Go → Console → Bless"}
          },
          "criteria_met_count": 6,
          "disqualifiers_found": [],
          "weakeners_found": [],
          "one_sentence_summary": "Rav Ḥisda and Rabba bar Rav Huna..."
        }
      ]
    }
  ]
}
```

## Why This Works

**vs Keyword Matching:**
- Keywords find "once" in legal discussions → false positive
- AI understands narrative STRUCTURE, not just words

**vs Simple AI Prompts:**
- v1-v3 had 50%+ false positive rate
- Expert validation identified specific patterns
- v5.1 addresses each pattern with explicit criteria

**Key Insight from Expert Validation:**
> "The AI confuses attribution with characters. When it sees 'Rabbi X said that Rabbi Y said...', it thinks there's a story with characters, but it's just legal attribution."

This insight led to the `rabbi_legal_opinion` disqualifier, which alone caught 53 false positives in Ketubot 2-39.

## Technical Details

**Model:** Gemini 2.0 Flash (not -exp)
- Regular model has higher rate limits
- 1 second delay between requests
- ~3 minutes for 40 pages

**API:** Sefaria REST API
- No authentication required
- 15 second timeout
- Preserves segment alignment

**Cost:** ~$0.01 per 10 pages analyzed

## Running Detection

```bash
cd src
export GOOGLE_API_KEY='your-key'
python story_detector_v5.py 2 39  # Analyze pages 2-39

# Output: results/ketubot/v5/pages_2-39.json
```

## Validation UI

Results are reviewed using HTML interfaces:
- Side-by-side English/Hebrew
- Story segments highlighted (±1 context)
- Criteria breakdown visible
- Expert can mark correct/incorrect
- Feedback exported as JSON

See `validation/ui/` for interfaces.
