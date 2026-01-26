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
│   └── story_detector_v5.py     # Current detection script
│
├── results/                     # Analysis output (by tractate)
│   └── ketubot/
│       ├── v4/                  # Previous version results
│       └── v5/                  # Current version results
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

## Current Version: v5.1

**Categorical classification** with expert validation from Jeffrey Rubenstein (Talmud scholar).

### Classification System
- **YES**: Definite story (all 6 criteria met, no weakeners)
- **HIGH_CONFIDENCE**: Strong story (5-6 criteria, minor weakeners)
- **LOW_CONFIDENCE**: Possible story (3-4 criteria, needs review)
- **NOT_A_STORY**: Not a narrative (fails criteria or has disqualifiers)

### Six Criteria
1. Named characters (specific rabbis, not generic "a person")
2. Multiple events (not single action)
3. Causal chain (Event A → Event B → Outcome)
4. Temporal progression (before → during → after)
5. Descriptive (what DID happen, not hypothetical)
6. Change/outcome (situation transforms)

### Ketubot Results (v5.1)
| Range | Stories | YES | HIGH | LOW |
|-------|---------|-----|------|-----|
| Pages 2-39 | 33 | 3 | 14 | 16 |
| Pages 40-60 | 22 | 2 | 15 | 5 |

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
python story_detector_v5.py 2 39  # Analyze Ketubot pages 2-39
```

### View Results
Open `validation/ui/ketubot_2-39.html` in a browser.

## How It Works

1. **Fetch** text from Sefaria API (Hebrew + English aligned segments)
2. **Detect** Hebrew narrative markers (מעשה, יומא חד, אמר ליה)
3. **Classify** using Gemini 2.0 Flash against 6 criteria
4. **Apply** disqualifiers (MISHNA, hypotheticals, legal opinions)
5. **Self-check** with 7 validation questions
6. **Output** categorized stories with evidence

## Documentation

- [Setup Guide](docs/setup/QUICKSTART.md)
- [How It Works](docs/technical/HOW_IT_WORKS.md)
- [Version History](docs/technical/VERSION_HISTORY.md)
- [Gemini Setup](docs/setup/GEMINI_SETUP.md)

## Expanding to Other Tractates

Results are organized by tractate for easy expansion:

```bash
# Run on a different tractate
python src/story_detector_v5.py --tractate "Bava Metzia" 2 39

# Results saved to: results/bava_metzia/v5/pages_2-39.json
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
