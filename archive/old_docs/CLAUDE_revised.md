# Claude.md - Talmud Story Detection

## Project
Detect narrative stories in Talmud text using LLM classification (Anthropic/Gemini).
Generates static HTML review UIs for expert validation.

## Common Commands
- **Run Extraction**: `python find_talmud_stories.py` (Interactive CLI)
- **Run Validation**: `python run_v*_full.py` (Check folder for latest version)
- **Generate Review UI**: `python generate_jeff_review_v*.py` (Check folder for latest version)
- **Install Dependencies**: `pip install -r requirements.txt`

## Environment Setup
Required API keys in `.env` or environment:
- `ANTHROPIC_API_KEY` (for Claude models)
- `GOOGLE_API_KEY` (for Gemini models)

## Data Structure
```json
pages[].segments[] → contains english/hebrew text
pages[].stories[] → references segments by index (NO text)
```
Flattening rule: MUST copy `page_segments: page.segments` when creating story objects.

## Testing Guidelines
1. **Always verify changes work** - don't assume.
2. **Open HTML files in browser** - not just check code.
3. **Test with real data** - trace actual values, not expected values.
4. **Check edge cases** - first/last segments, single-segment stories.
5. **Token Efficiency**: Use `limit` parameter for large files.

## Workflow Rules
1. **Validation UIs**: Must display text (English + Hebrew, story highlighted).
2. **Before Committing**:
   - [ ] Tested with real data (not assumptions)
   - [ ] Opened in browser (for UIs)
   - [ ] Verified narrative extraction boundaries
   - [ ] Run current validation script

## Key Files
| File | Purpose |
|------|---------|
| `find_talmud_stories.py` | Core narrative extraction logic (Anthropic/Gemini) |
| `run_v*_full.py` | Validation run scripts (e.g. `run_v5_1_full.py`) |
| `generate_jeff_review_v*.py` | Expert review UI generators |
| `jeff_review_v*.html` | Output UIs for validation |
| `results/v*/*.json` | Analysis output (text in segments) |
| `validation_results.json` | Previous validation data (Jeff Rubenstein) |
