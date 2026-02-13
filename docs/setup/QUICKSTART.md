# Quick Start Guide - Finding Talmud Stories with AI

## What This Does

Uses **AI to detect narrative structure** in Talmud passages - not just keyword matching!

**"Literary Stories"** = any passage with beginning, middle, end (including 2-line dialogues)

## Setup (One-time)

```bash
# Install dependencies
pip install -r requirements.txt

# Set your Google API key
export GOOGLE_API_KEY='your-key-from-aistudio.google.com'
```

## Run Story Detection

```bash
cd src
python3 story_detector_v6.py 2 39  # Analyze Ketubot pages 2-39
```

## View Results

```bash
open validation/ui/ketubot_2-39.html
```

## Output Format

Results saved to `results/v6/ketubot_v6_2-39.json`:

```json
{
  "tractate": "Ketubot",
  "version": "v6",
  "pages": [...],
  "summary": {
    "yes": 3,
    "high_confidence": 14,
    "low_confidence": 16,
    "not_a_story": 0
  }
}
```

## Classification System

| Classification | Meaning |
|----------------|---------|
| **YES** | Definite story (6/6 criteria, no weakeners) |
| **HIGH_CONFIDENCE** | Likely story (5-6 criteria, minor weakeners) |
| **LOW_CONFIDENCE** | Possible story (3-4 criteria, needs review) |
| **NOT_A_STORY** | Not a narrative |

## Story-Rich Tractates to Start With

1. **Ketubot** - Marriage cases and narratives
2. **Taanit** - Stories about rain, drought, and miracles
3. **Berakhot** - Stories about prayer and divine encounters
4. **Sanhedrin** - Historical narratives and parables
5. **Shabbat** - Stories about Sabbath observance

## Need Help?

- See [GEMINI_SETUP.md](GEMINI_SETUP.md) for API setup
- See [HOW_IT_WORKS.md](../technical/HOW_IT_WORKS.md) for detection details
- See [REVIEW_INTERFACE.md](../technical/REVIEW_INTERFACE.md) for validation UI
