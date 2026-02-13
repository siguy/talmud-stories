# Troubleshooting Guide

## "command not found: python"

**On macOS**, Python 3 is installed as `python3` instead of `python`.

**Solution**: Use `python3` instead:

```bash
python3 src/story_detector_v6.py 2 10
```

## Common Issues

### Missing Dependencies

If you get `ModuleNotFoundError`:

```bash
pip3 install -r requirements.txt
```

### API Key Not Set

If you get "GOOGLE_API_KEY not set":

```bash
export GOOGLE_API_KEY='your-key-here'
```

Get your key from: https://aistudio.google.com/app/apikey

### google-genai Not Installed

If you get "google-genai not installed":

```bash
pip3 install google-genai
```

### Network Errors from Sefaria

If you get connection errors to www.sefaria.org:
- Check your internet connection
- Try again (sometimes Sefaria has rate limits)
- Make sure you're not behind a restrictive firewall

### Rate Limit Errors

If you get API rate limit errors:
- Google Gemini free tier: 1500 requests/minute
- The script includes 1-second delays between requests
- Wait a minute and try again

## Quick Start Commands (macOS)

```bash
# 1. Install dependencies
pip3 install -r requirements.txt

# 2. Set API key
export GOOGLE_API_KEY='your-key-here'

# 3. Run detection (small test first)
cd src
python3 story_detector_v5.py 2 10

# 4. View results
open ../validation/ui/ketubot_2-39.html
```
