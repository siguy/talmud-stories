# Talmud Stories Finder

This project uses the Sefaria MCP (Model Context Protocol) server to search through Talmud tractates and identify stories.

## Setup

### Prerequisites
- Python 3.10 or higher
- pip

### Installation

1. Install the Sefaria MCP server:
```bash
pip install sefaria-mcp
```

2. Install dependencies for the story finder script:
```bash
pip install requests anthropic
```

### Running the MCP Server

Start the Sefaria MCP server:
```bash
python -m sefaria_mcp.main
```

The server will run at `http://127.0.0.1:8088/sse`

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

Run the story finder script:
```bash
python find_talmud_stories.py
```

This will:
1. Search through major Talmud tractates
2. Look for narrative passages and stories
3. Save results to `talmud_stories.json`

## Available Talmud Orders (Sedarim)

The Babylonian Talmud contains 6 orders with 37 tractates:

1. **Zeraim** (Seeds) - Agricultural laws
2. **Moed** (Festival) - Sabbath and holidays
3. **Nashim** (Women) - Marriage and divorce
4. **Nezikin** (Damages) - Civil and criminal law
5. **Kodashim** (Holy Things) - Sacrifices and Temple
6. **Tahorot** (Purities) - Ritual purity

## Sefaria MCP Tools Available

- `get_text` - Retrieve text by reference (e.g., "Berakhot 2a")
- `text_search` - Search entire library
- `search_in_book` - Search within specific tractate
- `get_links_between_texts` - Find cross-references
- `english_semantic_search` - Semantic similarity search

## References

- [Sefaria MCP GitHub](https://github.com/Sefaria/sefaria-mcp)
- [Sefaria.org](https://www.sefaria.org)
