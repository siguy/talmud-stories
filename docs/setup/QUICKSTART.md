# Quick Start Guide - Finding Talmud Stories with AI

## What This Does

Uses **AI to detect narrative structure** in Talmud passages - not just keyword matching!

**"Literary Stories"** = any passage with beginning, middle, end (including 2-line dialogues)

## Option 1: AI-Powered Analysis (Recommended)

### Setup (One-time)
```bash
# Install dependencies
pip install -r requirements.txt

# Set your Anthropic API key
export ANTHROPIC_API_KEY='your-key-from-console.anthropic.com'
```

### Run the Script
```bash
python find_talmud_stories.py
```

### Choose Your Search
- **Option 1**: All tractates (~2-4 hours with AI, comprehensive)
- **Option 2**: Specific tractate (10-30 minutes)
- **Option 3**: Story-rich tractates - Taanit, Berakhot, Sanhedrin (20-40 minutes, **recommended**)

### Output
Results in `talmud_stories.json` include:
- **Narrative analysis** (has beginning/middle/end, characters, dialogue, etc.)
- **Story type** (full_narrative, dialogue_vignette, brief_anecdote)
- **Confidence score** (0-100%)
- **AI-generated summary**
- Full text of passage

Example:
```json
{
  "ref": "Taanit 23a",
  "analysis": {
    "is_story": true,
    "confidence": 95,
    "story_type": "full_narrative",
    "one_sentence_summary": "Honi draws circle and refuses to leave until God sends proper rain",
    "narrative_elements": {
      "has_beginning": true,
      "has_middle": true,
      "has_end": true,
      "has_characters": true,
      "has_action": true,
      "has_dialogue": true
    }
  }
}
```

---

## Option 2: Without API Key (Heuristic Fallback)

If you don't have an Anthropic API key:
```bash
pip install requests
python find_talmud_stories.py
```

Uses heuristic analysis (less accurate but free). Looks for narrative indicators like dialogue, actions, temporal markers.

---

## Option 3: MCP Server with Claude Desktop (Interactive)

### Setup (One-time)
```bash
# Install the Sefaria MCP server
pip install sefaria-mcp

# Add to Claude Desktop config
# Copy contents from claude_desktop_config_example.json
# to your Claude Desktop config file

# Restart Claude Desktop
```

### Use with Claude
Ask Claude in Claude Desktop:
```
Use the Sefaria MCP to search Tractate Taanit for stories about miracles.
For each story found, get the full text and provide a summary.
```

See `MCP_USAGE_GUIDE.md` for detailed prompts and examples.

---

## Story-Rich Tractates to Start With

1. **Taanit** - Stories about rain, drought, and miracles
2. **Berakhot** - Stories about prayer and divine encounters
3. **Sanhedrin** - Historical narratives and parables
4. **Megillah** - Stories related to Purim
5. **Shabbat** - Stories about Sabbath observance

---

## Need Help?

- Read `README.md` for full setup instructions
- Read `MCP_USAGE_GUIDE.md` for detailed MCP usage
- Visit https://www.sefaria.org to browse texts manually
- Check https://github.com/Sefaria/sefaria-mcp for MCP documentation
