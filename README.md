# Talmud Story Detection

AI-powered detection of narrative stories in the Babylonian Talmud using semantic analysis.

## Project Structure

```
talmud-stories/
├── CLAUDE.md                    # AI collaboration guide
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── index.html                   # GitHub Pages entry
│
├── src/                         # Core detection code
│   ├── story_detector_v6.py     # Current detection script (v6)
│   └── story_detector_v5.py     # Previous detection script (v5.1)
│
├── results/                     # Analysis output (by tractate)
│   ├── v6/                      # Current version results
│   └── ketubot/
│       ├── v4/                  # Previous version results
│       └── v5/                  # v5.1 results
│           ├── pages_2-39.json
│           └── pages_40-60.json
│
├── validation/                  # Expert validation system
│   ├── ui/                      # HTML review interfaces
│   │   ├── ketubot_2-39.html
│   │   ├── ketubot_40-60.html
│   │   └── jeff_comparison.html
│   ├── generators/              # Scripts to generate UIs
│   └── feedback/                # Expert feedback JSONs
│
├── docs/                        # Documentation
│   ├── setup/                   # Installation guides
│   ├── technical/               # How it works
│   └── communication/           # Expert reviewer materials
│
├── tests/                       # Test implementations
│   └── v5_categorical/          # Current version
│
└── archive/                     # Old versions (reference)
```

## Current Version: v6

**Comprehensive revision** based on Jeff Rubenstein's review of 128 passages (86% accuracy in v5.1 → targeting >90% in v6).

### What Changed in v6

- **Anonymous characters count fully** — "a certain man/woman" = valid character (was penalized before)
- **Refined "narrative event"** — legal arguments, deliberation, debate settings no longer count as events
- **Cross-page story merging** — stories split by arbitrary page boundaries are now detected and combined
- **Borderline calibration** — one event + discussion = LOW_CONFIDENCE (not rejected)
- **Boundary trimming** — legal rulings before/after stories excluded from story boundaries
- **Duplicate detection** — same story quoted on multiple pages flagged

### Classification System
- **YES**: Definite story (all 6 criteria met, no weakeners)
- **HIGH_CONFIDENCE**: Strong story (5-6 criteria, minor weakeners)
- **LOW_CONFIDENCE**: Borderline story (3-4 criteria, or 1 event + discussion)
- **NOT_A_STORY**: Not a narrative (fails criteria or has disqualifiers)

### Six Criteria
1. Identifiable characters (named rabbis OR anonymous "a certain man/woman" — both valid!)
2. Multiple NARRATIVE events (physical actions, not legal talk)
3. Causal chain (Event A → Event B → Outcome)
4. Temporal progression (before → during → after)
5. Descriptive (what DID happen, not hypothetical)
6. Change/outcome (situation transforms)

### Ketubot Results (v5.1)
| Range | Stories | YES | HIGH | LOW |
|-------|---------|-----|------|-----|
| Pages 2-39 | 33 | 3 | 14 | 16 |
| Pages 40-60 | 22 | 2 | 15 | 5 |

*v6 results pending — run detector to generate new results.*

## Quick Start

### Installation
```bash
pip install -r requirements.txt
```

### Set API Key
```bash
export GOOGLE_API_KEY='your-key'  # Get from https://aistudio.google.com/app/apikey
```

### Run Detection
```bash
cd src
python story_detector_v6.py 2 39  # Analyze Ketubot pages 2-39
```

### View Results
Open `validation/ui/ketubot_2-39.html` in a browser.

## How It Works

1. **Fetch** all pages from Sefaria API (Hebrew + English aligned segments)
2. **Detect** Hebrew narrative markers (מעשה, יומא חד, אמר ליה)
3. **Classify** each page with cross-page context using Gemini 2.0 Flash against 6 criteria
4. **Apply** disqualifiers (MISHNA, hypotheticals, legal opinions, debate settings)
5. **Self-check** with 9 validation questions (including boundary trimming)
6. **Merge** cross-page stories split by arbitrary page boundaries
7. **Detect** duplicate stories quoted on multiple pages
8. **Output** categorized stories with evidence

## Documentation

- [Setup Guide](docs/setup/QUICKSTART.md)
- [How It Works](docs/technical/HOW_IT_WORKS.md)
- [Version History](docs/technical/VERSION_HISTORY.md)
- [Gemini Setup](docs/setup/GEMINI_SETUP.md)

## Expanding to Other Tractates

Results are organized by tractate for easy expansion:

```bash
# Run on a different tractate
cd src
python story_detector_v6.py 2 39  # Default: Ketubot

# Results saved to: results/v6/ketubot_v6_2-39.json
```

## Expert Validation

Stories are validated by Talmud scholars using HTML review interfaces:
- Side-by-side English/Hebrew text
- Story segments highlighted
- Criteria breakdown (which of 6 met/failed)
- Disqualifiers and weakeners displayed
- One-click feedback export

## References

- [Sefaria API](https://www.sefaria.org)
- [Google Gemini](https://aistudio.google.com/)
