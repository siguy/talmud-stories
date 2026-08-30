# Claude.md - Talmud Story Detection

## Project
Detect narrative stories in Talmud text using LLM classification. Expert validation by Jeff Rubenstein (NYU). Golden dataset for Ketubot complete (182 stories, 0.93 composite score). Expanding to additional tractates.

## Current State
**See [`STATUS.md`](STATUS.md) — where the project is, and the first thing to read in
any session. Then [`FRAMEWORK.md`](FRAMEWORK.md) — the six capabilities, how each is
measured, and what the gates are. Use its language: capability names, BLIND vs
CIRCULAR datasets, and measured / indicated / suspected on every finding.** It is rewritten each session,
never appended. Do not restate status here; this file is about *how to work in the
repo*, not where we are.

Ready-to-run work lives in [`tasks/NEXT/`](tasks/NEXT/) — one self-contained brief per
task, each executable in a fresh session with no other context.

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
    ketubot_canonical.json        #     Ketubot golden — 182 entries, 159 accepted; v7 + v9
    kiddushin_canonical.json      #     Kiddushin golden — 96 entries, 85 accepted; v7 + the 2026-04-23 round ONLY
    source_runs/                  #     Detector runs that fed golden corrections
                                  #     (formerly results/v10/ — NOT a detector version)
  v4/, v5/, v6/                   #   Historical detector outputs
  v7/                             #   FROZEN v7 baseline + Sefaria/triage caches
  v7_fresh/                       #   v7 re-run 2026-05-18 (use as same-day baseline; Lesson 11)
  v8/                             #   FROZEN Wave 1+2 baseline
    wave1/                        #     Wave 1 outputs (kiddushin_v8.json, ketubot_v8_*)
    wave2/                        #     Wave 2 outputs (frozen gate for Wave 3)
  v9/                             #   ACTIVE DEVELOPMENT — current detector
    wave3/                        #     Wave 3 outputs (kiddushin_v9.json, ketubot_v9_*)
    wave3_item4/                  #     Item 4 score-neutrality artifact
validation/
  ui/                             #   HTML review interfaces
  generators/                     #   Scripts to generate UIs
  feedback/                       #   Expert feedback JSONs (4 rounds)
docs/
  golden/                         # ORGANIZED BY DETECTOR VERSION (reorg 2026-05-24)
    workflow/                     #   Cross-version process docs and research
    v7/                           #   v7-era analyses + Kiddushin feedback
    v8/                           #   Wave 1+2 results
    v9/                           #   Wave 3 results
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
| `results/canonical/ketubot_canonical.json` | **THE golden dataset** — 182 entries, 159 accepted (23 NOT_A_STORY) |
| `scripts/evaluate_golden.py` | IMMUTABLE evaluation harness |
| `docs/golden/v7/baseline_ketubot.json` | v7 baseline scores (historical 0.93; not reproducible — Lesson 11) |
| `docs/golden/v9/wave3_results.md` | **Wave 3 writeup** (start here for current state) |
| `docs/golden/v8/wave2_results.md` | Wave 2 writeup |
| `docs/golden/v8/wave1_results.md` | Wave 1 writeup |
| `docs/golden/v8/wave3_approach.md` | Wave 3 approach + design decisions |
| `docs/golden/workflow/error_taxonomy.md` | 6 error patterns from Jeff's reviews |
| `docs/golden/v10/findings_v10_golden_dataset.md` | v10 session writeup |
| `docs/golden/workflow/research_overfitting_and_generalization.md` | Why prompt engineering has a ceiling |
| `docs/golden/workflow/new_tractate_workflow.md` | Step-by-step for new tractates |
| `src/story_detector_v7.py` | v7 — DO NOT modify in place |
| `src/story_detector_v8.py` | FROZEN Wave 2 baseline (v7 + Wave 1/2 post-processors) |
| `src/story_detector_v9.py` | **ACTIVE** — v8 + Wave 3 prompt changes + text_span post-processor |
| `src/event_triage.py` | Stage 1 event classification |
| `src/ground_truth.py` | Ground Truth DB (Jeff's labels) |
| `results/v7/kiddushin_v7.json` | Kiddushin v7 results (96 stories, pre-Wave-1) |
| `results/v8/wave2/kiddushin_v8.json` | Kiddushin Wave 2 (frozen baseline for Wave 3 gate) |
| `results/v9/wave3/kiddushin_v9.json` | Kiddushin Wave 3 results (95 stories) |
| `results/v9/wave3/ketubot_v9_2-60.json`, `results/v9/wave3/ketubot_v9_61-112.json` | Ketubot Wave 3 results |
| `docs/golden/v8/baselines/{kiddushin,ketubot}_wave2_baseline_today.json` | Today-regenerated Wave 2 numbers (gate per Lesson 11) |
| `scripts/run_wave3.py` | Parameterized Wave 3 runner (--tractate / --range / --refs) |
| `scripts/apply_wave3_item4.py` | Apply item 4 to Wave 2 outputs (score-neutrality fast path) |
| `scripts/audit_wave3_item4.py` | Audit item 4 against Jeff's 17 boundary cases (`AUDIT_INPUT` env override) |
| `scripts/verify_wave3.py` | Wave 3 per-item pass/fail report |
| `scripts/compare_v8_v9.py` | Wave 2 vs Wave 3 side-by-side metrics |
| `scripts/run_kiddushin_wave1.py` | Kiddushin Wave 1 runner (v8) |
| `scripts/verify_wave1.py` | Wave 1 verification |
| `scripts/audit_text_spans.py` | **Structural gate** — mid-word / clause-edge rates; `--strict` fails the build |
| `scripts/strip_text_spans.py` | Reverts LLM char-offset spans to segment-level boundaries |
| `scripts/measure_recall_vs_expert_list.py` | **True recall** vs. an expert's detector-blind list |
| `jeff comms/b.ketubot (1).doc` | Jeff's 2005 Ketubot story list — 149 stories, detector-blind ground truth |
| `jeff comms/8-30-2026/kidushin.doc` | Jeff's Kiddushin list — parse with `parse_kiddushin_list.py`, NOT `parse_expert_doc` |
| `scripts/parse_kiddushin_list.py` | **Table-aware expert-list parser** — reads the .doc's OLE streams; `--self-test` asserts Ketubot == 149 |
| `results/expert_lists/kiddushin_2005.json` | **Kiddushin blind ground truth** — 95 stories with `blind` flags, 10 anchored expert remarks |
| `docs/golden/v11/kiddushin_list_parse_2026-08-30.md` | Why the line-based parse gave 105, and how the count was verified |
| `jeff comms/8-30-2026/Kiddushin missed stories.docx` | **The appendix** — our own cases, which Jeff merged into his list. Those 5 entries are NOT blind |
| `scripts/check_appendix_coverage.py` | **Blindness check** — run on every new expert list before trusting it (Lesson 26) |
| `scripts/build_ruler.py` | **THE ruler** — joins blind lists + proposals + all 6 review rounds; measures Detection and Classification together |
| `results/rulers/{ketubot,kiddushin}_ruler.json` | Per-story: expert-listed? proposed? every verdict, and what each rejection objected to |
| `docs/golden/v11/detection_classification_ruler_2026-08-30.md` | Why 86%/68% were not Classification numbers, and why 96% recall is 88% strict |
| `results/recall/ketubot_jeff2005_matches.json` | Per-story recall match output (incl. the 6 misses) |
| `results/v10/wave4_notrim/` | **Current honest outputs** — segment-level boundaries, no spans |
| `docs/golden/workflow/recall_measurement_ketubot_2026-08-28.md` | The 96% recall finding + method |
| `docs/golden/v10/wave4_span_failure_audit_2026-08-28.md` | Span failure audit + revert |
| `tasks/PLAN_wave5b_clause_roles.md` | Clause-role labelling — the judgment layer on Wave 5 |
| `tasks/PLAN_wave6.md` | Jeff's story criteria (6c blocked on his answer) |
| `src/prompts/clause_roles_v*.md` | Versioned labelling prompts |
| `tests/expert_boundary_targets_2005.json` | **294 detector-blind boundaries** from Jeff's 2005 list — the neutral ruler; catches regressions |
| `tests/expert_boundary_targets_v2.json` | 70 correction boundaries (was 52) — widened harvest + `quote_polarity` |
| `tests/expert_boundary_targets.json` | 52 sub-segment boundaries Jeff stated (superseded by _v2) |
| `scripts/build_boundary_testset_2005.py` | Aligns Jeff's 2005 story texts to Sefaria Hebrew -> exact boundaries |
| `docs/golden/v11/boundary_ruler_rebuild_2026-08-30.md` | **Ruler rebuild** — 35 -> 249 targets, noise floor 7pts -> 0 |
| `scripts/build_boundary_testset.py` | Rebuilds that test set (text-anchored, version-proof) |
| `scripts/score_boundary_targets.py` | Scores any run against it |
| `results/clause_labels/` | Per-clause labels — a reusable asset, not a wave by-product |
| `docs/golden/v11/wave5_summary_fix_2026-08-30.md` | **Steps 1-2 writeup** — 35 targets, +29pts vs no-trim, and the gate's noise floor |
| `results/v11/wave5_summaryfix/` | Wave 5 spans with the summary fix (+ a same-code repeat = noise floor) |
| `tests/test_wave5b_runner_outcomes.py` | **Failure-injection guard** — a failed call must never be stamped as a judgment (Lesson 21) |
| `tests/fixtures/wave5b_runner_pages.json` | Real 4-page Kiddushin slice covering every outcome bucket |
| `tasks/lessons.md` | 14 lessons learned across all sessions |
| `FOR_SIMON.md` | Plain-English project explanation |

## Git Tags
- `v10-golden-ketubot` — golden dataset checkpoint
- `pre-detector-changes` — rollback point for detector experiments
- `v9-wave3` — Wave 3 ship point

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
- Ask an LLM for a character offset into text (Lesson 16) — anchor to real text units
- Ingest ground truth from a converter's output (Lesson 25) — parse the source format; `textutil` silently drops table columns and relocates Word comments
- Call an expert list blind without checking it against what we sent him (Lesson 26) — 5 of Jeff's 95 Kiddushin stories are our own output, merged in and unmarked
- Plan a fix from an expert's sample without first measuring the defect's corpus-wide rate (Lesson 18)
- Attribute a score change to a code change without a same-code repeat run (Lesson 22)
