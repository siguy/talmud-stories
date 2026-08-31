# Talmud Story Detection v5: Categorical Classification

## Overview

Version 5 implements a **categorical classification system** that replaces numerical confidence scores with actionable categories: **YES**, **HIGH_CONFIDENCE**, **LOW_CONFIDENCE**, and **NOT_A_STORY**.

## Key Changes from v4

### 1. Classification System
Instead of:
```json
{"is_story": true, "confidence": 72}
```

We now have:
```json
{
  "classification": "HIGH_CONFIDENCE",
  "criteria_met_count": 5,
  "reasoning": "..."
}
```

### 2. Explicit Criteria Evaluation
Every potential story is evaluated against 6 boolean criteria:

| Criterion | Requirement |
|-----------|-------------|
| **Named Characters** | Specific post-biblical figures (Rav X, Rabbi Y) |
| **Multiple Events** | At least 2 distinct events |
| **Causal Chain** | Events connected by cause/effect (A→B→C) |
| **Temporal Progression** | Time markers or clear sequence |
| **Descriptive** | Describes what DID happen (not what SHOULD) |
| **Change/Outcome** | Situation different at end vs beginning |

### 3. Disqualifier Detection
Automatic rejection if ANY present:
- MISHNA section (מתני׳)
- Hypothetical case ("If X were to...")
- Biblical narrative (Moses, David, etc.)
- Habitual action (היה רגיל = "was accustomed to")
- Pure legal ruling without narrative

### 4. Weakener Detection
Factors that push YES → HIGH_CONFIDENCE:
- Embedded in legal discussion
- Short (≤2 segments)
- Implied causality (not explicit)
- Partial character naming ("a certain man")
- Ambiguous outcome
- Continues to/from another page

### 5. Jeff's Curated Examples
Incorporated **12 validated examples** from Jeff's reviews:
- **4 YES examples** with exact Hebrew text
- **2 HIGH_CONFIDENCE examples** with borderline reasoning
- **4 NOT_A_STORY examples** with specific disqualifiers

Each example includes:
- Full Hebrew text (not summarized)
- English translation
- Explicit criteria evaluation
- Jeff's validation notes

### 6. Jeff's Self-Check Questions
Replaced generic self-check with domain-specific questions:

1. **Descriptive vs Prescriptive**: "Is this describing what someone DID, or what the law SAYS?"
2. **Habitual Marker Check**: "Does היה רגיל or רגיל appear?"
3. **Ma'aseh Follow-through**: "If מעשה appears, does a story follow, or just legal discussion?"
4. **Event Count**: "Can I list at least 2 distinct events?"
5. **Causality Test**: "Can I state the chain as: A caused B, which caused C?"
6. **Change Test**: "What is different at the end compared to the beginning?"

## Decision Logic

```
┌─────────────────────────────────────────────────────────────┐
│                    DISQUALIFIER CHECK                        │
│  MISHNA? Hypothetical? Biblical? Pure Legal? Habitual?       │
└─────────────────────────────────────────────────────────────┘
                            │
                   Any TRUE? ──YES──► NOT A STORY
                            │
                           NO
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    CRITERIA COUNT                            │
│  How many of 6 criteria are TRUE?                           │
└─────────────────────────────────────────────────────────────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
           6/6          5-6/6          3-4/6        <3/6
              │             │             │            │
              ▼             ▼             ▼            ▼
┌──────────────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│  WEAKENER CHECK  │  │   HIGH   │  │   LOW    │  │   NOT    │
│  Short? Fuzzy?   │  │CONFIDENCE│  │CONFIDENCE│  │ A STORY  │
│  Embedded?       │  └──────────┘  └──────────┘  └──────────┘
└──────────────────┘
         │
    Any TRUE? ──YES──► HIGH CONFIDENCE
         │
        NO
         ▼
       YES
```

## Output Schema

```json
{
  "page_ref": "Ketubot 2a",
  "stories": [
    {
      "start_segment": 5,
      "end_segment": 8,
      "classification": "YES | HIGH_CONFIDENCE | LOW_CONFIDENCE | NOT_A_STORY",

      "criteria": {
        "named_characters": {"met": true, "evidence": "Rav Reḥumi, his wife"},
        "multiple_events": {"met": true, "count": 5, "events": ["studying", "didn't return", ...]},
        "causal_chain": {"met": true, "chain": "engrossed → missed → distressed → death"},
        "temporal_progression": {"met": true, "markers": ["יומא חד", "באותה שעה"]},
        "descriptive": {"met": true, "evidence": "narrates past events"},
        "change_outcome": {"met": true, "before": "alive, studying", "after": "dead"}
      },

      "criteria_met_count": 6,
      "disqualifiers_found": [],
      "weakeners_found": [],

      "one_sentence_summary": "...",
      "classification_reasoning": "All 6 criteria met with strong evidence. No disqualifiers or weakeners.",

      "self_check_results": {
        "descriptive_test": {"passed": true, "note": "..."},
        "habitual_check": {"passed": true, "note": "..."},
        ...
      }
    }
  ]
}
```

## Usage

### Prerequisites
Set your Google API key:
```bash
export GOOGLE_API_KEY="your_key_here"
```

### Run Test
```bash
python3 tests/v5_categorical/test_categorical_classification.py
```

### Customize Test Range
Edit the file to change pages:
```python
if __name__ == "__main__":
    # Test on different pages
    results = analyze_tractate_v5("Ketubot", start_page=2, end_page=10)
    save_results(results, "ketubot_v5_test.json")
```

## What's Additive from Jeff's Validation Data

| Component | v4 (Current) | v5 (Additive) |
|-----------|--------------|---------------|
| Story criteria | 5-7 points in prompt | Explicit boolean evaluation of 6 criteria |
| Examples | 6 summary examples | 12 with exact Hebrew text |
| Borderline cases | None | 2 with Jeff's reasoning |
| Anti-patterns | Generic descriptions | Hebrew markers (רגיל, היה רגיל) |
| Self-check | 5 generic questions | 6 Jeff-specific questions |
| Hebrew boundaries | Not used | Exact text from validation |
| Confidence | 0-100 percentage | YES/HIGH/LOW/NOT categories |

## Benefits

1. **Actionable Categories**
   - YES → Include in results
   - HIGH → Include, flag for spot-check
   - LOW → Needs human review
   - NOT → Exclude

2. **Transparent Reasoning**
   - Know exactly WHY something is HIGH vs YES
   - See which specific criteria failed

3. **Aligned with Jeff's Thinking**
   - Uses his actual validation language
   - Evaluates features he evaluates, not arbitrary percentages

4. **Consistent**
   - Same features always produce same category
   - No AI randomness in scores

5. **Trainable**
   - As Jeff reviews LOW items, we learn boundaries
   - Can adjust criteria weights based on feedback

## Next Steps

1. **Set GOOGLE_API_KEY** and run initial test
2. **Review results** from first 5 pages of Ketubot
3. **Send sample to Jeff** for validation
4. **Iterate on criteria weights** based on feedback
5. **Run full Ketubot analysis** once validated
6. **Create validation UI** for v5 output format

## Files Created

- `test_categorical_classification.py` - Main v5 implementation
- `README.md` - This documentation
- Results will be saved to: `results/v5/ketubot_v5_test.json`
