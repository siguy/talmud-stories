# Quick Start: Switch to Google Gemini

## ✅ Done - Changes Committed

All code changes are complete and pushed to GitHub!

## 🚀 Steps to Use Gemini (On Your Mac)

### 1. Pull Latest Changes

```bash
cd ~/talmud-stories
git pull origin claude/sefaria-talmud-story-search-Mw1Yg
```

### 2. Install Google AI SDK

```bash
pip install google-generativeai
```

Or:
```bash
pip install -r requirements.txt
```

### 3. Get Google API Key

1. Visit: **https://aistudio.google.com/app/apikey**
2. Click "Create API Key"
3. Copy your key

### 4. Set Environment Variable

```bash
export GOOGLE_API_KEY='your-google-api-key-here'
```

### 5. Run Test

```bash
python3 test_multi_story.py
```

When prompted:
- Choose **option 2** (Google Gemini)
- Watch it analyze Ketubot 10b, 62b, 67b

## 💰 Cost Comparison

| Model | Full Ketubot (~224 pages) | Speed |
|-------|--------------------------|-------|
| Gemini 3 Flash Preview | **$0.03-0.05** ⭐ | ~8 min |
| Claude 3.5 Haiku | $0.50-1.00 | ~15 min |

**Gemini is 10-20× cheaper!**

## 📊 What to Expect

The test will:
1. Connect to Sefaria API
2. Fetch pages: Ketubot 10b, 62b, 67b
3. Analyze with Gemini 3 Flash Preview
4. Show results:
   - How many stories found per page
   - Story boundaries (start/end markers)
   - Extraction success/failure

**Expected results:**
- Ketubot 10b: Should find **3 stories**
- Ketubot 62b: Should find **2 stories**
- Ketubot 67b: Should find **4 stories**

## 🔄 If You Want to Switch Back to Claude

Just choose **option 1** when prompted, or edit the test scripts:

```python
analyzer = NarrativeAnalyzer(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    model="claude-3-5-haiku-20241022",
    provider="anthropic"
)
```

## 📝 Full Documentation

See **GEMINI_SETUP.md** for:
- Detailed setup instructions
- All available models
- Rate limits
- Troubleshooting
- Performance tips

## ⚡ Ready to Test!

Once you've set `GOOGLE_API_KEY`, just run:

```bash
python3 test_multi_story.py
```

And watch the multi-story detection in action with Gemini! 🎉
