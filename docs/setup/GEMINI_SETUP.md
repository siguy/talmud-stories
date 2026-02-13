# Google Gemini Setup Guide

This guide explains how to set up Google Gemini for Talmud story detection.

## Quick Start

```bash
# 1. Install Google AI SDK
pip install google-genai

# 2. Get API key from https://aistudio.google.com/app/apikey

# 3. Set environment variable
export GOOGLE_API_KEY='your-key-here'

# 4. Run detection
cd src
python3 story_detector_v6.py 2 39
```

## Setup Steps

### 1. Install Google AI SDK

```bash
pip install google-genai
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

### 4. Run Detection

```bash
cd src
python3 story_detector_v6.py 2 39  # Analyze Ketubot pages 2-39
```

Results saved to `results/v6/ketubot_v6_2-39.json`

## Model Information

### Gemini 2.0 Flash (Default)

| Aspect | Details |
|--------|---------|
| Model | `gemini-2.0-flash` |
| Speed | Very fast |
| Cost | ~$0.01 per 10 pages |
| Quality | Excellent for structured JSON output |
| Rate Limits | 1500 requests/min (free tier) |

## Troubleshooting

### Error: "google-genai not installed"

```bash
pip install google-genai
```

### Error: "GOOGLE_API_KEY not set"

```bash
export GOOGLE_API_KEY='your-key-here'
```

### Error: API rate limit exceeded

- Free tier: 1500 requests/minute
- Add delays between requests (1 second default)
- Upgrade to paid tier if needed

## Rate Limits (Free Tier)

- **Requests**: 1500 per minute
- **Tokens**: 1M input tokens/min, 4M output tokens/min
- **Daily**: 1500 requests per day

## Resources

- Google AI Studio: https://aistudio.google.com/
- Gemini API Docs: https://ai.google.dev/gemini-api/docs
- API Reference: https://ai.google.dev/api/python
