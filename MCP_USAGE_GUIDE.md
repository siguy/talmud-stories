# Using Sefaria MCP Server to Find Talmud Stories

This guide shows you how to use the Sefaria MCP (Model Context Protocol) server with Claude to search for stories in the Talmud.

## Two Approaches

### Approach 1: Standalone Python Script (Immediate Use)
Uses Sefaria's public API directly - no MCP server needed.

```bash
python find_talmud_stories.py
```

### Approach 2: MCP Server with Claude Desktop (Recommended for Interactive Use)
Connect Claude Desktop to the Sefaria MCP server for interactive exploration.

## Setting Up the MCP Server

### 1. Install the Sefaria MCP Server

```bash
pip install sefaria-mcp
```

### 2. Configure Claude Desktop

Add the Sefaria MCP server to your Claude Desktop configuration:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**Linux:** `~/.config/Claude/claude_desktop_config.json`

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

### 3. Restart Claude Desktop

After saving the configuration, restart Claude Desktop. You should see "sefaria" listed in your MCP servers.

## Using MCP Tools to Find Stories

Once connected, you can ask Claude to use these Sefaria MCP tools:

### Search for Stories in a Specific Tractate

```
Use the search_in_book tool to search for stories in Tractate Taanit.
Look for passages containing words like "story", "once", "miracle", or "happened".
```

### Get Specific Text

```
Use the get_text tool to retrieve Berakhot 5a
```

### Semantic Search for Story Themes

```
Use the english_semantic_search tool to find passages about:
- Miracles and divine intervention
- Rabbis meeting with Roman emperors
- Dreams and prophecies
- Acts of kindness and charity
```

### Search Entire Library

```
Use the text_search tool to search for "Elijah the Prophet appeared"
across all Talmud tractates
```

## Example Workflow for Finding Stories

### Step 1: Search Story-Rich Tractates

Story-rich tractates in the Talmud include:
- **Taanit** (Fasts) - Many stories about rain, drought, and miracles
- **Berakhot** (Blessings) - Stories about prayer and divine encounters
- **Sanhedrin** (Court) - Historical narratives and parables
- **Megillah** (Esther) - Stories related to Purim
- **Shabbat** - Stories about Sabbath observance

### Step 2: Use Multiple Search Strategies

Ask Claude to:
1. Search for narrative keywords ("once there was", "story", "miracle")
2. Search for key figures (Rabbi Akiva, Rabbi Yochanan, Elijah)
3. Search for locations (Jerusalem, Rome, Babylonia)
4. Use semantic search for themes (righteousness, charity, wisdom)

### Step 3: Retrieve and Analyze

For each promising reference:
1. Use `get_text` to retrieve the full passage
2. Use `get_links_between_texts` to find related commentary
3. Use `get_english_translations` to see available translations

## Sample Prompts for Claude Desktop

Here are ready-to-use prompts when you have the Sefaria MCP configured:

### Find Rain Miracle Stories
```
Use the Sefaria MCP tools to search Tractate Taanit for stories about rain
miracles. Search for terms like "rain", "drought", "Honi", and "miracle".
For each result, retrieve the full text and summarize the story.
```

### Find Stories About Specific Rabbis
```
Search the Talmud for stories featuring Rabbi Akiva. Use search_in_book
across major tractates (Berakhot, Sanhedrin, Nedarim, Pesachim).
List all references found.
```

### Thematic Story Collection
```
Find all stories in the Talmud about acts of charity and kindness.
Use semantic search and keyword search across all tractates.
Create a summary of the top 10 most relevant passages.
```

### Explore a Specific Reference
```
Get the full text of Taanit 23a (the story of Honi the Circle Drawer).
Then find all links and commentaries on this passage using get_links_between_texts.
```

## Available MCP Tools Reference

| Tool | Purpose | Example Use |
|------|---------|-------------|
| `get_text` | Retrieve specific passage | Get Berakhot 5b |
| `text_search` | Search entire library | Search for "Elijah appeared" |
| `search_in_book` | Search within tractate | Find "miracle" in Taanit |
| `english_semantic_search` | Semantic similarity | Find passages about charity |
| `get_links_between_texts` | Find cross-references | Get commentary on Berakhot 5a |
| `get_current_calendar` | Jewish calendar info | Today's learning schedule |
| `clarify_name_argument` | Autocomplete book names | Suggest names starting with "Ber" |

## Tips for Finding Stories

1. **Keywords that indicate narratives:**
   - "once", "there was", "it happened"
   - "said to him", "asked him", "replied"
   - Named individuals (not just "Rabbi X said")
   - Geographic locations
   - "story", "tale", "miracle"

2. **Story-rich contexts:**
   - Aggadic (narrative) sections vs. Halakhic (legal) sections
   - Discussions of ethics and character
   - Historical events and personalities
   - Supernatural events

3. **Use multiple search passes:**
   - First pass: broad keyword search
   - Second pass: named individuals
   - Third pass: semantic search for themes
   - Fourth pass: follow cross-references

## Troubleshooting

### MCP Server Not Showing Up
- Check that `sefaria-mcp` is installed: `pip list | grep sefaria`
- Verify the config file path is correct
- Check the JSON syntax is valid
- Restart Claude Desktop

### Search Returns No Results
- Try broader search terms
- Check spelling of tractate names
- Use `clarify_name_argument` to get correct book names
- Try `text_search` instead of `search_in_book`

### Rate Limiting
- The Sefaria API has rate limits
- Add delays between requests
- Cache results when possible

## Additional Resources

- **Sefaria.org** - Browse texts manually: https://www.sefaria.org
- **Sefaria MCP GitHub** - Server documentation: https://github.com/Sefaria/sefaria-mcp
- **Model Context Protocol** - MCP specification: https://modelcontextprotocol.io

## Example Output Format

When you find stories, format them like this:

```
Story Reference: Taanit 23a
Title: Honi the Circle Drawer and the Rain

Summary: Honi draws a circle and refuses to leave it until God sends rain.
When light rain falls, he demands proper rain. When too much rain falls,
he asks for it to stop. Demonstrates the power of righteous prayer but also
the fine line of demanding from God.

Keywords: miracle, rain, prayer, Honi
Category: Divine intervention, Prayer efficacy
```
