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
│   ├── story_detector_v7.py     # Current detection script (v7)
│   ├── event_triage.py          # Event triage (Stage 1)
│   ├── ground_truth.py          # Ground Truth DB (Jeff's labels)
│   ├── post_processing.py       # Mechanical post-processing rules
│   ├── story_detector_v6.py     # Previous detection script (v6)
│   └── story_detector_v5.py     # Previous detection script (v5.1)
│
├── results/                     # Analysis output (by tractate)
│   ├── v7/                      # Current version results
│   ├── v6/                      # Previous version results
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
│   ├── v7_regression_test.py    # Regression test vs Jeff's labels
│   ├── model_comparison.py      # Multi-model comparison runner
│   ├── ablation_test.py         # Ablation test framework
│   └── v5_categorical/          # Historical tests
│
└── archive/                     # Old versions (reference)
```

## Current Version: v7 + Gemini 3 Flash

**92.1% accuracy** (117/127) on Jeff Rubenstein's 128 expert-labeled passages. Decomposed 4-stage pipeline with Gemini 3 Flash.

### Pipeline

- **Event triage** — classifies every segment into NARRATIVE_EVENT/VERBAL_ACT/DELIBERATION/HABITUAL, skips 66% of pages
- **Constrained detection** — event-annotated prompt with anti-legal few-shot examples from Ground Truth DB
- **Boundary refinement** — trims DELIBERATION segments from story edges
- **Cross-page merge** — uses triage event types at page boundaries to detect story fragments
- **Post-processing** — mechanical rules (v6 ensemble) for additional accuracy

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

### Ketubot Results
| Version | Model | Agreement with Jeff |
|---------|-------|---------------------|
| v5.1 | — | 84.3% (107/127) |
| v6 | gemini-2.0-flash | 82.7% (105/127) |
| v7 | gemini-2.0-flash | 87.4% (111/127) |
| v7+pp | gemini-2.0-flash | 89.8% (114/127) |
| **v7** | **gemini-3-flash** | **92.1% (117/127)** |

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
# v7 pipeline with Gemini 3 Flash (current best)
GEMINI_MODEL=gemini-3-flash-preview PYTHONPATH=. python3 src/story_detector_v7.py

# Model comparison (run detection + regression test)
PYTHONPATH=. python3 tests/model_comparison.py --model gemini-3-flash-preview

# Regression test (compare against Jeff's labels)
PYTHONPATH=. python3 tests/v7_regression_test.py

# Score all existing model results
PYTHONPATH=. python3 tests/model_comparison.py --score
```

### View Results
Open `validation/ui/ketubot_2-39.html` in a browser, or see `results/v7/ketubot_v7_2-60.json`.

## How It Works

1. **Fetch** all pages from Sefaria API (Hebrew + English aligned segments)
2. **Triage** every segment into event types (NARRATIVE_EVENT, VERBAL_ACT, DELIBERATION, HABITUAL)
3. **Skip** pages with insufficient narrative events (~66% of pages)
4. **Detect** stories using event-annotated prompt with anti-legal few-shot examples
5. **Refine** boundaries by trimming DELIBERATION segments from story edges
6. **Merge** cross-page stories using triage event types at page boundaries
7. **Deduplicate** stories quoted on multiple pages
8. **Post-process** with mechanical rules (v6 ensemble)
9. **Output** categorized stories with evidence and criteria evaluation

## Documentation

- [Setup Guide](docs/setup/QUICKSTART.md)
- [How It Works](docs/technical/HOW_IT_WORKS.md)
- [Version History](docs/technical/VERSION_HISTORY.md)
- [Gemini Setup](docs/setup/GEMINI_SETUP.md)

## Expanding to Other Tractates

Results are organized by tractate for easy expansion. The pipeline is tractate-agnostic — tested on Ketubot 2a-60b with plans to validate on additional tractates.

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
