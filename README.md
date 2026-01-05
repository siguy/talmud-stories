# Talmud Stories Finder - Semantic Narrative Detection

This project uses AI to identify **"Literary Stories"** in the Talmud - any narrative arc with a beginning, middle, and end, including brief two-line dialogues and vignettes.

Unlike keyword-based approaches, this uses semantic understanding through Claude AI to detect narrative structure.

## Setup

### Prerequisites
- Python 3.10 or higher
- pip

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your Anthropic API key for AI-powered narrative detection:
```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

Get your API key from: https://console.anthropic.com/

**Note:** The script works without an API key using heuristic analysis, but AI-powered detection is much more accurate.

## What Makes This Different?

**Traditional Keyword Approach:**
- Searches for words like "once", "miracle", "happened"
- Misses stories without these keywords
- Includes non-narrative legal discussions that happen to use these words

**Semantic Narrative Detection (This Project):**
- Uses AI to understand narrative structure
- Identifies beginning, middle, and end
- Finds brief vignettes and dialogues with narrative arcs
- Distinguishes stories from legal discussions

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
export ANTHROPIC_API_KEY='your-key'
python find_talmud_stories.py
```

The script will:
1. Systematically analyze passages from Talmud tractates
2. Use AI to detect narrative structure (beginning, middle, end)
3. Classify story types (full narratives, dialogue vignettes, brief anecdotes)
4. Provide confidence scores and summaries
5. Save detailed results to `talmud_stories.json`

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

## AI Models Supported

- **Claude 3.5 Haiku** (default) - Fast and cost-effective
- **Claude 3.5 Sonnet** - More nuanced understanding, higher cost

## Sefaria MCP Tools (Optional)

For interactive exploration with Claude Desktop, you can also use:
- `get_text` - Retrieve text by reference (e.g., "Berakhot 2a")
- `text_search` - Search entire library
- `search_in_book` - Search within specific tractate
- `get_links_between_texts` - Find cross-references
- `english_semantic_search` - Semantic similarity search

## References

- [Sefaria MCP GitHub](https://github.com/Sefaria/sefaria-mcp)
- [Sefaria.org](https://www.sefaria.org)
