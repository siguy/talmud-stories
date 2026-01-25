# Talmud Stories Finder - Semantic Narrative Detection

This project uses AI to identify **"Literary Stories"** in the Talmud - any narrative arc with a beginning, middle, and end, including brief two-line dialogues and vignettes.

Unlike keyword-based approaches, this uses semantic understanding through AI (Google Gemini or Anthropic Claude) to detect narrative structure.

## Latest Results

**v5.1 Categorical Classification (January 2026):**
- **Validation-driven improvements** based on expert feedback from Jeffrey Rubenstein
- New categorical system: YES, HIGH_CONFIDENCE, LOW_CONFIDENCE, NOT_A_STORY
- Stricter criteria addressing 50% false positive rate in v4.1
- Test results (Ketubot 2-10): 3 HIGH_CONFIDENCE, 6 LOW_CONFIDENCE, 27 NOT_A_STORY
- Documentation: [v5.1_test_summary.md](v5.1_test_summary.md) | [v5.1_validation_report.md](v5.1_validation_report.md)
- Code: [tests/v5_categorical/](tests/v5_categorical/)

**Previous Analysis - Tractate Ketubot (v3):**
- 258 stories identified with 95.2% average confidence
- 118 full narratives, 94 brief anecdotes, 46 dialogue vignettes
- Review interface: [jeff_review.html](jeff_review.html)

## Version History & Evolution

This project has evolved through iterative validation with Talmud scholar Jeffrey Rubenstein:

### v5.1 (Current) - Categorical Classification with Validation-Driven Improvements
**Focus:** Address false positive patterns identified in expert validation

**Key Changes:**
- **Categorical confidence:** YES, HIGH_CONFIDENCE, LOW_CONFIDENCE, NOT_A_STORY (replacing 0-100% scores)
- **New disqualifier:** `rabbi_legal_opinion` - catches rabbi attribution vs character confusion
- **Stricter causality:** "Event A CAUSED Event B, which CAUSED Event C" (not just sequential)
- **Stricter change:** "Situation TRANSFORMED" (not just action reports)
- **New weakeners:** `simple_report`, `minimal_causality`, `minimal_change`
- **Boundary detection:** Talmud commentary markers, continuation markers
- **Enhanced self-check:** 7 domain-specific validation questions

**Impact:** Expected false positive rate reduction from ~50% → <20%

**Documentation:**
- [v5.1_test_summary.md](v5.1_test_summary.md) - Executive summary
- [v5.1_validation_report.md](v5.1_validation_report.md) - Detailed pattern analysis
- [tests/v5_categorical/README_v5.1.md](tests/v5_categorical/README_v5.1.md) - Implementation details

### v5.0 - Categorical Classification System
**Focus:** Replace percentage-based confidence with actionable categories

**Changes:**
- Introduced YES/HIGH/LOW/NOT_A_STORY classification
- Self-check mechanism with 6 validation questions
- Enhanced disqualifiers and weakeners

### v4.1 - Expert Validation Phase
**Focus:** Expert validation by Jeffrey Rubenstein

**Results:**
- 30 stories validated (15 TRUE, 15 FALSE positives)
- Identified key false positive patterns:
  - Rabbi legal opinions mistaken as story characters
  - Sequential events without causal connection
  - Simple reports without transformation
  - Boundary detection issues

### v4 - Segment-Based Detection
**Focus:** Preserve Sefaria's aligned segment structure

**Changes:**
- Segment-level story boundaries
- Multi-segment story grouping
- Hebrew/Aramaic marker detection
- Continuation chain detection

### v3 - Full Tractate Analysis
**Focus:** Comprehensive Ketubot analysis

**Results:** 258 stories identified, validation UI created

### v2 - Bilingual Analysis
**Focus:** Hebrew/Aramaic + English analysis

### v1 - Initial Prototype
**Focus:** English-only semantic detection

## Setup

### Prerequisites
- Python 3.10 or higher
- pip

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your API key for AI-powered narrative detection:

**Google Gemini (Recommended - faster and cheaper):**
```bash
export GOOGLE_API_KEY='your-api-key-here'
```
Get your key from: https://aistudio.google.com/app/apikey

**Anthropic Claude (Alternative):**
```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```
Get your key from: https://console.anthropic.com/

**Note:** The script works without an API key using heuristic analysis, but AI-powered detection is much more accurate. See [GEMINI_SETUP.md](GEMINI_SETUP.md) for detailed setup instructions.

## What Makes This Different?

**Traditional Keyword Approach:**
- Searches for words like "once", "miracle", "happened"
- Misses stories without these keywords
- Includes non-narrative legal discussions that happen to use these words
- English-only analysis

**Semantic Narrative Detection (This Project):**
- Uses AI to understand narrative structure
- Identifies beginning, middle, and end
- Finds brief vignettes and dialogues with narrative arcs
- Distinguishes stories from legal discussions
- **Analyzes both Hebrew/Aramaic original AND English translation**
- Detects Hebrew narrative markers: ויהי (vayehi), מעשה ב (ma'aseh be), פעם אחת (pa'am achat)

## Usage

### Using with Claude Desktop

Configure Claude Desktop to connect to the Sefaria MCP server by adding to your config file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "sefaria": {
      "command": "python",
      "args": ["-m", "sefaria_mcp.main"]
    }
  }
}
```

### Finding Stories in Talmud

Run the AI-powered story finder:
```bash
# Using Gemini (recommended)
export GOOGLE_API_KEY='your-key'
python test_ketubot.py gemini 1

# Using Claude
export ANTHROPIC_API_KEY='your-key'
python test_ketubot.py claude 1
```

The script will:
1. Systematically analyze passages from Talmud tractates
2. Fetch both Hebrew/Aramaic original and English translation
3. Use AI to detect narrative structure in BOTH languages
4. Classify story types (full narratives, dialogue vignettes, brief anecdotes)
5. Provide confidence scores and summaries
6. Save detailed results to `talmud_stories.json` with both texts

**Example output:**
```
✓ Taanit 23a - full_narrative (confidence: 95%)
  Summary: Honi draws circle and demands rain from God
  Elements: has_beginning, has_middle, has_end, has_characters, has_action, has_dialogue
```

## Available Talmud Orders (Sedarim)

The Babylonian Talmud contains 6 orders with 37 tractates:

1. **Zeraim** (Seeds) - Agricultural laws
2. **Moed** (Festival) - Sabbath and holidays
3. **Nashim** (Women) - Marriage and divorce
4. **Nezikin** (Damages) - Civil and criminal law
5. **Kodashim** (Holy Things) - Sacrifices and Temple
6. **Tahorot** (Purities) - Ritual purity

## Story Definition

**"Literary Stories"** - Any passage with a narrative arc containing:
- **Beginning:** Setup, characters introduced, situation established
- **Middle:** Action, dialogue, conflict, or change
- **End:** Resolution, conclusion, or outcome

This includes:
- Full multi-scene narratives (e.g., Honi the Circle Drawer)
- Brief two-line dialogues with progression
- Vignettes showing character actions and outcomes
- Anecdotes with temporal progression

Does NOT include:
- Pure legal discussions without narrative
- Abstract philosophical debates
- Lists of rulings without story context
- Bare statements of law

## Enhanced Story Detection Logic

The system uses a sophisticated multi-stage pipeline for accurate story detection, developed with expert validation from Jeffrey Rubenstein (Talmud scholar).

### Stage 1: Segment-Based Processing

Instead of analyzing pages as raw text, we preserve Sefaria's **aligned segment structure**:
- Each page is divided into numbered segments (typically 10-20 per page)
- English `text[]` and Hebrew `he[]` arrays are 1:1 aligned (same index = same content)
- This enables precise story boundary detection at the segment level

### Stage 2: Hebrew Narrative Marker Detection

Each segment is pre-processed to detect Hebrew/Aramaic markers:

**Story Markers (Positive Signals):**
- `מעשה` (ma'aseh) - "an incident/story"
- `כי הא ד` (ki ha d') - "like this case of..."
- `פעם אחת` (pa'am achat) - "one time"
- `יומא חד` (yoma chad) - "one day"
- `זמנא חדא` (zimna chada) - "one time" (Aramaic)

**Dialogue Markers:**
- `אמר ליה` / `א"ל` (amar leih) - "said to him"
- `אמר לה` (amar lah) - "said to her"

**Temporal Markers:**
- `לסוף` / `לבסוף` (l'sof) - "in the end"
- `באותה שעה` (b'otah sha'ah) - "at that moment"

**Legal Markers (Negative Signals):**
- `מתני` (matni) - Mishna indicator
- `הלכה` (halakha) - legal ruling
- `תנו רבנן` (tanu rabbanan) - "the Rabbis taught" (legal)

**English Markers:**
- "It is related", "There was an incident", "A certain person"
- "MISHNA" (negative), hypothetical language ("If X were to...")

### Stage 3: Character Extraction

The system identifies rabbi/character names for continuation detection:
- Patterns: "Rabbi X", "Rav X", "Rabban X", "Mar X"
- Compound names: "Rabbi X bar Y", "Rabbi X ben Y"
- Common names: Abaye, Rava, Reish Lakish

### Stage 4: Continuation Detection

Multi-segment stories are detected using several signals:

**Continuation Indicators:**
- **Pronoun starters:** "He ", "She ", "They " (referring back)
- **Narrative flow words:** "When he", "After", "By the time", "Meanwhile"
- **Shared characters:** Same rabbi appears in adjacent segments
- **Same rabbi continuing:** Segment starts with rabbi from previous segment

**New Story Indicators (Break Continuation):**
- Section markers: `§`, "MISHNA", "GEMARA"
- New story intros: "It is related further that", "A certain person"
- "The Gemara relates:"

### Stage 5: Story Grouping

Connected segments are grouped into story units:
- Continuation chains are followed (Seg 10 → 11 → 12 → 13)
- Result: One story spanning segments 10-13, not four separate stories
- Only segments with HIGH or MEDIUM story likelihood are considered

### Stage 6: AI Analysis with Expert Criteria

The AI receives:
1. Pre-processed segments with marker annotations
2. Detected continuations and suggested story groups
3. **Jeff Rubenstein's validated criteria:**

**A passage IS A STORY if it has ALL of:**
- ✓ Specific named characters (e.g., "Rav Reḥumi", "Rabban Gamliel")
- ✓ Dialogue between characters
- ✓ Temporal progression (before → during → after)
- ✓ Causal chain (Event A → Event B → Outcome)
- ✓ Change in situation or outcome
- ✓ Descriptive of what DID happen (not prescriptive)

**A passage is NOT A STORY if it has ANY of:**
- ✗ Hypothetical scenarios ("If X were to do Y...")
- ✗ Legal rulings without narrative
- ✗ MISHNA sections (almost always legal codifications)
- ✗ Habitual actions without specific incident
- ✗ Purely theoretical debates

### Validation Results

Tested against Jeff Rubenstein's expert validations:

| Page | AI Result | Expert Validation | Match |
|------|-----------|-------------------|-------|
| Ketubot 2a | 0 stories | NOT a story | ✓ |
| Ketubot 3a | 0 stories | NOT a story | ✓ |
| Ketubot 3b | 0 stories | NOT a story | ✓ |
| Ketubot 8b | 1 story | IS a story | ✓ |
| Ketubot 10b | 3 stories | 3 stories | ✓ |
| Ketubot 20b | 1 story | IS a story | ✓ |

### Example: Multi-Segment Story Detection

**Ketubot 62b - Rabbi Ḥananya Story:**
- Segments 10-13 all discuss Rabbi Ḥananya ben Ḥakhinai and Rabbi Hama bar Bisa
- Continuation detection identifies shared characters across segments
- AI correctly reports ONE story (segments 10-13) instead of four separate stories

## AI Models Supported

**Google Gemini (Recommended):**
- **Gemini 2.0 Flash** (default) - Fast, cheap, excellent multilingual support

**Anthropic Claude:**
- **Claude 3.5 Haiku** - Fast and cost-effective
- **Claude 3.5 Sonnet** - More nuanced understanding, higher cost

All models are fully multilingual and can read Hebrew, Aramaic, and English. Gemini is 10-20x cheaper than Claude. See [GEMINI_SETUP.md](GEMINI_SETUP.md) for setup and [BILINGUAL_ANALYSIS.md](BILINGUAL_ANALYSIS.md) for bilingual analysis details.

## Sefaria MCP Tools (Optional)

For interactive exploration with Claude Desktop, you can also use:
- `get_text` - Retrieve text by reference (e.g., "Berakhot 2a")
- `text_search` - Search entire library
- `search_in_book` - Search within specific tractate
- `get_links_between_texts` - Find cross-references
- `english_semantic_search` - Semantic similarity search

## Documentation

- **[GEMINI_SETUP.md](GEMINI_SETUP.md)** - Quick start with Google Gemini (recommended)
- **[HOW_IT_WORKS.md](HOW_IT_WORKS.md)** - Detailed explanation of semantic narrative detection
- **[BILINGUAL_ANALYSIS.md](BILINGUAL_ANALYSIS.md)** - How Hebrew/Aramaic + English analysis works
- **[REVIEWER_GUIDE.md](REVIEWER_GUIDE.md)** - Guide for expert reviewers
- **[MCP_USAGE_GUIDE.md](MCP_USAGE_GUIDE.md)** - Using with Claude Desktop via MCP

## References

- [Sefaria MCP GitHub](https://github.com/Sefaria/sefaria-mcp)
- [Sefaria.org](https://www.sefaria.org)
