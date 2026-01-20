# Switching to Google Gemini Flash

This guide explains how to switch from Anthropic Claude to Google Gemini for story detection.

## Why Switch to Gemini?

- **Lower cost**: Gemini Flash is significantly cheaper than Claude
- **Speed**: Gemini 2.0 Flash is extremely fast
- **High rate limits**: Google's free tier has generous limits
- **Comparison**: Test different models to find the best results

## Step-by-Step Setup

### 1. Install Google AI SDK

```bash
cd ~/talmud-stories
pip install google-generativeai
```

Or install from requirements:
```bash
pip install -r requirements.txt
```

### 2. Get Google API Key

1. Go to: https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Copy your API key

### 3. Set Environment Variable

**Option A: Export in terminal (temporary):**
```bash
export GOOGLE_API_KEY='your-google-api-key-here'
```

**Option B: Add to .env file (permanent):**
```bash
echo "GOOGLE_API_KEY=your-google-api-key-here" >> .env
```

Or manually edit `.env`:
```
GOOGLE_API_KEY=your-google-api-key-here
```

### 4. Update Your Scripts

#### For test_ketubot.py:

**OLD (Anthropic):**
```python
analyzer = NarrativeAnalyzer(
    api_key=api_key,
    model="claude-3-5-haiku-20241022"
)
```

**NEW (Google Gemini):**
```python
analyzer = NarrativeAnalyzer(
    api_key=api_key,
    model="gemini-2.0-flash-exp",
    provider="google"
)
```

#### For test_multi_story.py:

Same change - just add `provider="google"` parameter.

### 5. Run Tests

```bash
# Test on sample pages
python3 test_multi_story.py

# Full Ketubot analysis
python3 test_ketubot.py
```

## Available Models

### Google Gemini Models:

| Model | Speed | Cost | Best For |
|-------|-------|------|----------|
| `gemini-2.0-flash-exp` | ⚡️ Fastest | 💰 Cheapest | Production, high volume |
| `gemini-1.5-flash` | ⚡️ Fast | 💰 Cheap | General use |
| `gemini-1.5-pro` | 🐢 Slower | 💰💰 Medium | Complex analysis |

### Anthropic Claude Models:

| Model | Speed | Cost | Best For |
|-------|-------|------|----------|
| `claude-3-5-haiku-20241022` | ⚡️ Fast | 💰💰 Medium | Current default |
| `claude-3-5-sonnet-20241022` | 🐢 Slower | 💰💰💰 Expensive | Highest quality |

## Recommended: Gemini 2.0 Flash

For this project, **Gemini 2.0 Flash Experimental** (`gemini-2.0-flash-exp`) is recommended:

- **10-20× cheaper** than Claude Haiku
- **2-3× faster**
- **Excellent quality** for structured output (JSON)
- **High rate limits** (1500 requests/min on free tier)

## Cost Comparison

### Full Ketubot Analysis (~224 pages):

| Model | Estimated Cost | Time |
|-------|---------------|------|
| Claude 3.5 Haiku | $0.50-1.00 | ~15 min |
| **Gemini 2.0 Flash** | **$0.03-0.05** | **~8 min** |
| Gemini 1.5 Pro | $0.20-0.30 | ~20 min |

## Usage Examples

### Example 1: Quick test with Gemini

```python
from find_talmud_stories import NarrativeAnalyzer, SefariaStoryFinder
import os

# Initialize with Google Gemini
analyzer = NarrativeAnalyzer(
    api_key=os.getenv("GOOGLE_API_KEY"),
    model="gemini-2.0-flash-exp",
    provider="google"
)

finder = SefariaStoryFinder(analyzer)
stories = finder.search_tractate_systematically("Ketubot", "Nashim", sample_rate=10)
```

### Example 2: Compare both providers

```python
# Test with both Anthropic and Google
anthropic_analyzer = NarrativeAnalyzer(
    model="claude-3-5-haiku-20241022",
    provider="anthropic"
)

google_analyzer = NarrativeAnalyzer(
    model="gemini-2.0-flash-exp",
    provider="google"
)

# Run same analysis with both
# Compare results
```

### Example 3: Offline test (no API needed)

```python
# Test extraction logic without API calls
python3 test_extraction_offline.py
```

## Switching Back to Anthropic

To switch back to Anthropic Claude:

```python
analyzer = NarrativeAnalyzer(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    model="claude-3-5-haiku-20241022",
    provider="anthropic"
)
```

## Troubleshooting

### Error: "google-generativeai not installed"

**Solution:**
```bash
pip install google-generativeai
```

### Error: "No Google API key found"

**Solution:**
```bash
export GOOGLE_API_KEY='your-key-here'
# Or add to .env file
```

### Error: API rate limit exceeded

**Solution:**
- Gemini free tier: 1500 requests/minute
- Add delays between requests in code
- Upgrade to paid tier if needed

### Different results from Claude

**Expected:**
- Different models may identify different stories
- Gemini may be more/less strict on causality
- Compare results and iterate on prompt if needed

## Rate Limits

### Google Gemini (Free Tier):
- **Requests**: 1500 per minute
- **Tokens**: 1M input tokens/min, 4M output tokens/min
- **Daily**: 1500 requests per day

### Anthropic Claude:
- Depends on your tier
- Usually lower rate limits
- Check: https://console.anthropic.com/settings/limits

## Next Steps

1. ✅ Install Google AI SDK
2. ✅ Get API key from Google AI Studio
3. ✅ Set environment variable
4. ✅ Update analyzer initialization
5. 🔄 Run tests
6. 📊 Compare results with Jeffrey's feedback
7. 🚀 Use Gemini for production if results are good

## Quick Start Commands

```bash
# 1. Install dependencies
pip install google-generativeai

# 2. Set API key
export GOOGLE_API_KEY='your-key-here'

# 3. Test on sample pages
python3 test_multi_story.py

# 4. Full analysis (if tests pass)
python3 test_ketubot.py
# Enter sample_rate: 1

# 5. Review results
open review_stories.html
```

## Performance Tips

1. **Use Gemini 2.0 Flash** for best speed/cost ratio
2. **Batch requests** when possible (not yet implemented)
3. **Cache results** to avoid re-analyzing same pages
4. **Monitor usage** at https://aistudio.google.com/

## Support

- Google AI Docs: https://ai.google.dev/gemini-api/docs
- Gemini API Reference: https://ai.google.dev/api/python
- Report issues: Include model name and error message
