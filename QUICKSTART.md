# Quick Start Guide - Finding Talmud Stories

## Option 1: Use the Python Script (Fastest)

### Install and Run
```bash
# Install dependencies
pip install requests

# Run the script
python find_talmud_stories.py
```

### Choose Your Search
- **Option 1**: Search all tractates (30+ minutes, comprehensive)
- **Option 2**: Search specific tractate (5-10 minutes)
- **Option 3**: Search story-rich tractates (10-15 minutes, recommended)

### Output
Results saved to `talmud_stories.json` with:
- Story references (e.g., "Taanit 23a")
- Full text of passages
- Story score (based on narrative keywords)
- Keywords found

---

## Option 2: Use MCP Server with Claude Desktop (Interactive)

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
