# Claude.md - Talmud Story Detection

## Project
Detect narrative stories in Talmud text using LLM classification. Expert validation by Jeff Rubenstein (NYU). Golden dataset for Ketubot complete (182 stories, 0.93 composite score). Expanding to additional tractates.

## Current State (March 2026)
- **Golden Ketubot dataset**: 182 expert-validated stories (`results/canonical/ketubot_canonical.json`)
- **Evaluation framework**: Scores any detector output against golden labels (`scripts/evaluate_golden.py`)
- **Ketubot baseline**: Classification F1=0.92, Boundary IoU=0.98, Merge F1=0.86, Composite=0.93
- **Key finding**: Prompt engineering and few-shot examples cannot improve beyond 0.93 on Ketubot (see `docs/golden/research_overfitting_and_generalization.md`)
- **Kiddushin run complete**: 96 stories detected across 162 pages, 12 cross-page stories (3 via new continuation check). Review UI sent to Jeff. Awaiting his feedback.
- **Next step**: Score Kiddushin against Jeff's labels, compare to Ketubot baseline (target: 0.85+ composite)

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
4. Post-process: boundary refinement + cross-page merge + continuation check (Stage 4)
5. Generate review UI for expert validation
6. Expert reviews → feedback JSON → golden dataset

## Project Structure
```
src/                              # Core detection code
  story_detector_v7.py            #   Current detector (Gemini Flash)
  event_triage.py                 #   Stage 1 event classification
  ground_truth.py                 #   Jeff's expert labels for few-shot learning
scripts/                          # Execution and analysis scripts
  run_kiddushin.py                #   Run detector on Kiddushin 2a-82b
  run_ketubot_61_112.py           #   Run detector on Ketubot 61-112
  rerun_detector_v10.py           #   Re-run with modified prompts (experimental)
  build_canonical.py              #   Build golden dataset from base + feedback
  analyze_canonical_feedback.py   #   Analyze all feedback rounds
  apply_boundary_corrections.py   #   Apply boundary/merge corrections
  evaluate_golden.py              #   IMMUTABLE evaluation harness
  boundary_lookup.py              #   Match Hebrew markers to segments
  autoresearch/                   #   Experiment infrastructure (unused)
results/                          # See results/README.md for full layout
  canonical/                      #   GOLDEN LABELS (Jeff's validations)
    ketubot_canonical.json        #     Ketubot golden (182 stories, iteration 10)
    kiddushin_canonical.json      #     Kiddushin golden (85 stories from Jeff's 2026-04-23 review)
    source_runs/                  #     Detector runs that fed golden corrections
                                  #     (formerly results/v10/ — NOT a detector version)
  v4/, v5/, v6/                   #   Historical detector outputs
  v7/                             #   FROZEN v7 baseline + Sefaria/triage caches
  v7_fresh/                       #   v7 re-run 2026-05-18 (use as same-day baseline; Lesson 11)
  v8/                             #   ACTIVE DEVELOPMENT — current detector
    wave1/                        #     Wave 1 outputs (kiddushin_v8.json, ketubot_v8_*)
    wave2/                        #     (next session)
validation/
  ui/                             #   HTML review interfaces
  generators/                     #   Scripts to generate UIs
  feedback/                       #   Expert feedback JSONs (4 rounds)
docs/
  golden/                         # ORGANIZED BY DETECTOR VERSION (reorg 2026-05-24)
    workflow/                     #   Cross-version process docs and research
    v7/                           #   v7-era analyses + Kiddushin feedback
    v8/                           #   Wave 1 results
    v10/                          #   v10 findings + post-improvement email
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
| `docs/golden/v7/baseline_ketubot.json` | v7 baseline scores (historical 0.93; not reproducible — Lesson 11) |
| `docs/golden/v8/wave1_results.md` | **Wave 1 writeup** (start here for current state) |
| `docs/golden/workflow/error_taxonomy.md` | 6 error patterns from Jeff's reviews |
| `docs/golden/v10/findings_v10_golden_dataset.md` | v10 session writeup |
| `docs/golden/workflow/research_overfitting_and_generalization.md` | Why prompt engineering has a ceiling |
| `docs/golden/workflow/new_tractate_workflow.md` | Step-by-step for new tractates |
| `src/story_detector_v7.py` | Canonical detector — DO NOT modify in place |
| `src/story_detector_v8.py` | v7 + Wave 1 fixes (mechanical post-processors) |
| `src/event_triage.py` | Stage 1 event classification |
| `src/ground_truth.py` | Ground Truth DB (Jeff's labels) |
| `results/v7/kiddushin_v7.json` | Kiddushin v7 results (96 stories, pre-Wave-1) |
| `results/v8/kiddushin_v8.json` | Kiddushin Wave 1 results (93 stories) |
| `scripts/run_kiddushin.py` | Run script for Kiddushin (v7) |
| `scripts/run_kiddushin_wave1.py` | Kiddushin Wave 1 runner (v8) |
| `scripts/verify_wave1.py` | Kiddushin Wave 1 verification (11 checks) |
| `scripts/compare_ketubot_v7_v8.py` | Ketubot v7-vs-v8 regression check |
| `tasks/lessons.md` | 11 lessons learned across all sessions |
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
