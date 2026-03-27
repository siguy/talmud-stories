# Claude.md - Talmud Story Detection

## Project
Detect narrative stories in Talmud text using LLM classification. Expert validation by Jeff Rubenstein (NYU). Golden dataset for Ketubot complete (182 stories, 0.93 composite score). Expanding to additional tractates.

## Current State (March 2026)
- **Golden Ketubot dataset**: 182 expert-validated stories (`results/canonical/ketubot_canonical.json`)
- **Evaluation framework**: Scores any detector output against golden labels (`scripts/evaluate_golden.py`)
- **Baseline**: Classification F1=0.92, Boundary IoU=0.98, Merge F1=0.86, Composite=0.93
- **Key finding**: Prompt engineering and few-shot examples cannot improve beyond 0.93 on Ketubot (see `docs/golden/research_overfitting_and_generalization.md`)
- **Next step**: Run detector on Kiddushin, have Jeff review ~30 stories

## Critical Rules
1. **Validation UIs must display text** (English + Hebrew, story highlighted). Test in browser before claiming done.
2. **Never use labeled examples from the same pages you're evaluating on** — causes overfitting (see `tasks/lessons.md`, Lesson 2)
3. **`scripts/evaluate_golden.py` is IMMUTABLE** — do not modify the evaluation harness during experiments

## Data Structure
```
pages[].segments[] → contains english/hebrew text
pages[].stories[] → references segments by index (NO text)

When flattening stories, MUST copy: page_segments: page.segments
```

## Running the Detector on a New Tractate
See `docs/golden/new_tractate_workflow.md` for the step-by-step guide.

Quick version:
1. Fetch pages from Sefaria API
2. Run event triage (Stage 1)
3. Run story detection (Stage 2) with ground truth few-shots
4. Post-process: boundary refinement + cross-page merge (Stage 4)
5. Generate review UI for expert validation
6. Expert reviews → feedback JSON → golden dataset

## Project Structure
```
src/                              # Core detection code
  story_detector_v7.py            #   Current detector (Gemini Flash)
  event_triage.py                 #   Stage 1 event classification
  ground_truth.py                 #   Jeff's expert labels for few-shot learning
scripts/                          # Execution and analysis scripts
  run_ketubot_61_112.py           #   Run detector on Ketubot 61-112
  rerun_detector_v10.py           #   Re-run with modified prompts (experimental)
  build_canonical.py              #   Build golden dataset from base + feedback
  analyze_canonical_feedback.py   #   Analyze all feedback rounds
  apply_boundary_corrections.py   #   Apply boundary/merge corrections
  evaluate_golden.py              #   IMMUTABLE evaluation harness
  boundary_lookup.py              #   Match Hebrew markers to segments
  autoresearch/                   #   Experiment infrastructure (unused)
results/
  canonical/                      #   Golden dataset (v10)
  v7/                             #   Detector output (v7/v9 baseline)
  v10/                            #   Experiment output (reverted)
  v6/, ketubot/v5/                #   Historical
validation/
  ui/                             #   HTML review interfaces
  generators/                     #   Scripts to generate UIs
  feedback/                       #   Expert feedback JSONs (4 rounds)
docs/
  golden/                         #   Golden dataset docs, research, Jeff email
  technical/                      #   Pipeline docs (HOW_IT_WORKS, etc.)
  brainstorms/                    #   Design exploration
tasks/
  todo.md                         #   Current task list with progress
  lessons.md                      #   Ongoing learning log (8 lessons)
tests/                            # Regression tests
archive/                          # Old versions (reference only)
```

## Key Files
| File | Purpose |
|------|---------|
| `results/canonical/ketubot_canonical.json` | **THE golden dataset** (182 stories) |
| `scripts/evaluate_golden.py` | IMMUTABLE evaluation harness |
| `docs/golden/baseline_ketubot.json` | Baseline scores (0.93 composite) |
| `docs/golden/error_taxonomy.md` | 6 error patterns from Jeff's reviews |
| `docs/golden/findings_v10_golden_dataset.md` | Full session writeup |
| `docs/golden/research_overfitting_and_generalization.md` | Why prompt engineering has a ceiling |
| `docs/golden/new_tractate_workflow.md` | Step-by-step for new tractates |
| `src/story_detector_v7.py` | Current detector (Gemini Flash) |
| `src/event_triage.py` | Stage 1 event classification |
| `src/ground_truth.py` | Ground Truth DB (Jeff's labels) |
| `tasks/lessons.md` | 8 lessons learned across all sessions |
| `FOR_SIMON.md` | Plain-English project explanation |

## Git Tags
- `v10-golden-ketubot` — golden dataset checkpoint
- `pre-detector-changes` — rollback point for detector experiments

## Testing Requirements
1. Always verify changes work — don't assume
2. Open HTML files in browser — not just check code
3. Test with real data — trace actual values
4. One thorough fix — not multiple commits for same bug

## Documentation Requirements
When making changes, update these files as relevant:
- `docs/technical/VERSION_HISTORY.md` - New versions, results
- `docs/technical/HOW_IT_WORKS.md` - Pipeline changes
- `docs/golden/findings_v10_golden_dataset.md` - Golden dataset work
- `tasks/lessons.md` - After any correction or surprise
- `CLAUDE.md` - If project structure or key files change

## Don't
- Change APIs/models without asking
- Add "improvements" beyond request
- Claim "fixed" without testing
- Modify `evaluate_golden.py` during experiments
- Use few-shot examples from pages being evaluated
