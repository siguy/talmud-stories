# Troubleshooting Guide

## "command not found: python"

**On macOS**, Python 3 is installed as `python3` instead of `python`.

**Solution**: Use `python3` instead:

```bash
python3 test_ketubot.py
```

## Other Common Issues

### Missing Dependencies

If you get `ModuleNotFoundError`:

```bash
pip3 install -r requirements.txt
```

### API Key Not Set

If you get "ANTHROPIC_API_KEY not found":

```bash
export ANTHROPIC_API_KEY='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'
```

### Network Errors from Sefaria

If you get connection errors to www.sefaria.org:
- Check your internet connection
- Try again (sometimes Sefaria has rate limits)
- Make sure you're not behind a restrictive firewall

## Quick Start Commands (macOS)

```bash
# 1. Install dependencies
pip3 install -r requirements.txt

# 2. Set API key
export ANTHROPIC_API_KEY='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'

# 3. Run the analysis
python3 test_ketubot.py

# 4. When prompted, enter sample rate (try 2 for faster testing)
2

# 5. Wait for analysis to complete (8-12 minutes for sample_rate=2)

# 6. Open the review interface
open review_stories.html
```
