# How It Works

## Overview

This system detects narrative stories in Talmud text using AI-powered semantic analysis with expert-validated criteria. Version 6 incorporates comprehensive feedback from Jeff Rubenstein's review of 128 passages.

```
Sefaria API → Fetch ALL pages → Classify with cross-page context → Self-check (9 questions) → Cross-page merge → Duplicate detection → Output
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

### Stage 3: AI Classification (v6)

Using Gemini 2.0 Flash, each page is evaluated with cross-page context (last 3 segments of previous page, first 3 of next page) against **6 criteria**:

| Criterion | Question | Example |
|-----------|----------|---------|
| identifiable_characters | Any specific actors? Anonymous characters count! | "a certain man", "Rabban Gamliel" |
| multiple_events | More than one NARRATIVE event? (not legal talk) | Physical actions, state changes |
| causal_chain | Event A CAUSED Event B CAUSED Outcome? | Not just sequential |
| temporal_progression | Before → during → after? | Time passes in narrative |
| descriptive | What DID happen (not hypothetical)? | Not "if X were to..." |
| change_outcome | Situation TRANSFORMED? | Not just action report |

**Key v6 refinements:**
- Anonymous characters ("a certain man/woman") are FULLY valid characters (not weakeners)
- What is NOT a narrative event: verbal statements, legal arguments, deliberation, traveling to debate, ordering someone, "instituting" a practice
- Rabbis who only state legal opinions are NOT characters in a story

**Classification:**
- **YES**: 6/6 criteria, no weakeners
- **HIGH_CONFIDENCE**: 5-6 criteria, minor weakeners
- **LOW_CONFIDENCE**: 3-4 criteria, OR 1 event + discussion (borderline stories)
- **NOT_A_STORY**: <3 criteria OR disqualifier

### Stage 4: Disqualifiers (v6 expanded)

Any of these → automatic NOT_A_STORY:

| Disqualifier | Catches |
|--------------|---------|
| `MISHNA_section` | Legal codification |
| `hypothetical_case` | "If X were to do Y..." |
| `habitual_actions` | "He would regularly..." |
| `pure_legal_ruling` | Law without narrative |
| `rabbi_legal_opinion` | "Rabbi X quotes Rabbi Y as saying..." |
| `legal_deliberation` | Thinking about acting, legal difficulty (v6) |
| `legal_debate_setting` | Physical setting of debate, academy debates (v6) |

**Removed in v6:** `biblical_narrative` — Jeff validated biblical stories as correct

### Stage 5: Weakeners

These downgrade confidence but don't disqualify:

- `minimal_causality` - Events connected but not strongly causal
- `minimal_change` - Change is subtle
- `simple_report` - Action without transformation
- `embedded_in_legal_discussion` - Story within legal context

### Stage 6: Self-Check (v6: 9 questions)

9 validation questions asked after initial classification:

1. **Descriptive test**: What DID happen vs what SHOULD happen?
2. **Habitual check**: Does היה רגיל appear?
3. **Ma'aseh follow-through**: If מעשה appears, does a story follow?
4. **Event count**: 2+ NARRATIVE events? (legal talk doesn't count)
5. **Causality test**: A CAUSED B CAUSED C? (strict)
6. **Change test**: What transformed?
7. **Character role test**: Acting in narrative, or legal discourse? Anonymous = valid!
8. **Boundary check** (v6): Does story start/end include legal framing that should be trimmed?
9. **Borderline check** (v6): One event + discussion = LOW_CONFIDENCE, not NOT_A_STORY

If answers contradict initial classification → adjust.
Boundary adjustments are applied automatically in v6.

### Stage 7: Cross-Page Merging (v6 new)

Post-processing pass to merge stories split by arbitrary page boundaries:

1. Scan for stories at page boundaries with continuation flags
2. Merge stories where page N ends incomplete and page N+1 starts mid-narrative
3. Combined story gets higher confidence of the two halves

### Stage 8: Duplicate Detection (v6 new)

Flag stories that appear to be the same passage quoted on multiple pages.
Uses text fingerprinting of first 100 characters of English translation.

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

**Key Insights from Expert Validation:**

> v4.1: "The AI confuses attribution with characters. When it sees 'Rabbi X said that Rabbi Y said...', it thinks there's a story with characters, but it's just legal attribution."
> → Led to `rabbi_legal_opinion` disqualifier (53 false positives caught)

> v5.1: "Stories can be about unnamed people. The anonymous character does not weaken the confidence."
> → Renamed criterion to `identifiable_characters`, anonymous chars count fully

> v5.1: "The events here are rabbis making legal arguments... that is not really an event that makes for a story."
> → Refined what constitutes a "narrative event" vs legal/intellectual activity

> v5.1: "The page is a totally arbitrary marker and should be ignored when identifying the boundaries of stories."
> → Added cross-page merging and context in v6

> v5.1: "Passages with one event and then discussion should be identified as borderline stories."
> → Calibrated LOW_CONFIDENCE for borderline stories in v6

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

# v6 (current)
python story_detector_v6.py 2 39  # Analyze pages 2-39
# Output: results/v6/ketubot_v6_2-39.json

# v5.1 (previous)
python story_detector_v5.py 2 39
# Output: results/v5/ketubot_v5.1_full_validation_2-39.json
```

## Validation UI

Results are reviewed using HTML interfaces:
- Side-by-side English/Hebrew
- Story segments highlighted (±1 context)
- Criteria breakdown visible
- Expert can mark correct/incorrect
- Feedback exported as JSON

See `validation/ui/` for interfaces.
