# Claude.md - Talmud Story Detection

## Project
Detect narrative stories in Talmud text using LLM classification. Expert validation by Jeff Rubenstein (NYU). Golden datasets exist for Ketubot and Kiddushin; expanding to additional tractates. Current counts and scores live in `STATUS.md` — not here.

## The route — do this, in this order

1. **Read [`STATE.md`](STATE.md)** — generated; the coverage matrix, every gate, what is
   in flight and what is blocked. Then [`STATUS.md`](STATUS.md) for the judgment and the
   live hazards. Never edit `STATE.md` or `WORK.md`; run `python3 scripts/board.py`.
2. **Before opening work on a capability, read
   [`docs/capabilities/<n>_<name>.md`](docs/capabilities/)** — what was already tried,
   and what was reverted and why. *This is the step that stops a dead end being re-run.*
   Ein Yaakov was proposed, declined by Jeff, recorded — and proposed again months later
   by someone who had not read the record.
3. **Start work by copying [`work/_TEMPLATE.md`](work/_TEMPLATE.md)** to
   `work/<today>-<slug>.md`. Never invent a numbering scheme; the counter is what
   collided four ways on 2026-08-30.
4. **Finish** by adding `## Outcome` — including *why*, especially for a revert — and
   `git mv`-ing the item to `work/done/`. **Never delete it.**
5. **Run `python3 -m pytest tests/ -q` before you stop.** `tests/test_bookkeeping.py` is
   in that suite and fails on a dangling dependency, an unknown capability slug, a moved
   golden, or a stale `STATE.md`.

Read [`FRAMEWORK.md`](FRAMEWORK.md) for how each capability is measured and why each gate
is what it is. Use its language: capability names, BLIND vs CIRCULAR on every dataset, and
measured / indicated / suspected on every finding.

**Fresh clone:** `git config core.hooksPath .githooks` once, so the pre-commit guard on
the immutable harness is active. The same check is in the test suite either way.

## Current State
Do not restate status here; this file is about *how to work in the repo*, not where we
are. `STATE.md` is generated and `STATUS.md` is rewritten each session, never appended.

**Nothing in this file may carry a count, a score, or an "active version" claim.** Those
rot the moment someone works without reading them, and this file is read first. Where one
is unavoidable, write the *rule that stays true* and the command that answers it — not the
number. (Every stale entry found on 2026-08-30 was one of these three.)

Ready-to-run work lives in [`work/`](work/) — one self-contained item per
task, each executable in a fresh session with no other context.

## Critical Rules
1. **Validation UIs must display text** (English + Hebrew, story highlighted). Test in browser before claiming done.
2. **Never use labeled examples from the same pages you're evaluating on** — causes overfitting (see `lessons/`, Lesson 2)
3. **`scripts/evaluate_golden.py` is IMMUTABLE** — do not modify the evaluation harness during experiments

## Data Structure
```
pages[].segments[] → contains english/hebrew text
pages[].stories[] → references segments by index (NO text)
pages[].mishnah_stories[] → stories Stage 4g WITHHELD from stories[] (same shape)

When flattening stories, MUST copy: page_segments: page.segments
```

`stories[]` is not the whole output. Stage 4g moves Mishnah-internal stories to
`mishnah_stories[]`, and no harness or UI reads that key — a withheld story therefore
scores as a story we never found (4 of Ketubot's 15 golden false negatives; Lesson 27).
Any code that reads a run for scoring or display must decide about that key explicitly.
Report it with `scripts/report_mishnah_filter_delta.py` before trusting a golden number.

## Running the Detector on a New Tractate
See `docs/technical/new_tractate_workflow.md` for the step-by-step guide.

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
  report_mishnah_filter_delta.py  #   What Stage 4g withholds, and its cost vs the golden
  boundary_lookup.py              #   Match Hebrew markers to segments
  autoresearch/                   #   Experiment infrastructure (unused)
results/                          # See results/README.md for full layout
  canonical/                      #   GOLDEN LABELS (Jeff's validations)
    ketubot_canonical.json        #     Ketubot golden (grows with each review round)
    kiddushin_canonical.json      #     Kiddushin golden (from Jeff's 2026-04-23 review)
    source_runs/                  #     Detector runs that fed golden corrections
                                  #     (formerly results/v10/ — NOT a detector version)
  v4/, v5/, v6/                   #   Historical detector outputs
  v7/                             #   FROZEN v7 baseline + Sefaria/triage caches
  v7_fresh/                       #   v7 re-run 2026-05-18 (use as same-day baseline; Lesson 11)
  v8/                             #   FROZEN Wave 1+2 baseline
    wave1/                        #     Wave 1 outputs (kiddushin_v8.json, ketubot_v8_*)
    wave2/                        #     Wave 2 outputs (frozen gate for Wave 3)
  v9/                             #   Wave 3 outputs
    wave3/                        #     Wave 3 outputs (kiddushin_v9.json, ketubot_v9_*)
    wave3_item4/                  #     Item 4 score-neutrality artifact
validation/
  ui/                             #   HTML review interfaces
  generators/                     #   Scripts to generate UIs
  feedback/                       #   Expert feedback JSONs (4 rounds)
docs/
  capabilities/                   #   Per-capability history: tried / reverted / best / untried
  findings/                       #   Dated findings, YYYY-MM-DD-slug.md. Corrected, never edited silently
  history/                        #   Plans and approach docs, superseded by what they produced
  technical/                      #   Pipeline docs (HOW_IT_WORKS, new_tractate_workflow, etc.)
  brainstorms/                    #   Design exploration
  golden/                         #   DATA ONLY since 2026-08-30 + a redirect table in its README
work/                             # One self-contained item per ready task (dated slug, no counter)
  done/                           #   Finished items with an ## Outcome. NEVER deleted
  _TEMPLATE.md                    #   Copy this to start work
lessons/                          # One file per lesson, L-001..L-030. Numbers are permanent
comms/                            # Correspondence with Jeff
  sent/                           #   What was sent, dated
tests/                            # Regression tests
archive/                          # Old versions (reference only)
```

## Key Files
| File | Purpose |
|------|---------|
| `results/canonical/ketubot_canonical.json` | **THE golden dataset.** It grows — count it, don't quote a number. Entries include `NOT_A_STORY`; filter those out for a story count. |
| `scripts/evaluate_golden.py` | IMMUTABLE evaluation harness |
| `docs/golden/v7/baseline_ketubot.json` | v7 baseline scores (historical 0.93; not reproducible — Lesson 11) |
| `docs/findings/2026-05-25-wave3-results.md` | Wave 3 writeup (for current state read `STATUS.md`) |
| `docs/findings/2026-05-24-wave2-results.md` | Wave 2 writeup |
| `docs/findings/2026-05-18-wave1-results.md` | Wave 1 writeup |
| `docs/history/2026-05-24-wave3-approach.md` | Wave 3 approach + design decisions |
| `docs/findings/2026-03-17-error-taxonomy.md` | 6 error patterns from Jeff's reviews |
| `docs/findings/2026-03-25-golden-dataset-v10.md` | v10 session writeup |
| `docs/findings/2026-03-25-overfitting-and-generalization-research.md` | Why prompt engineering has a ceiling |
| `docs/technical/new_tractate_workflow.md` | Step-by-step for new tractates |
| `src/story_detector_v*.py` | **The highest-numbered file is the active detector; every lower one is a frozen ship point — never edit those in place.** `ls src/story_detector_v*.py` is the source of truth; a version number written in this file is not. What each version changed: its own module docstring, and `docs/golden/`. |
| `src/event_triage.py` | Stage 1 event classification |
| `src/ground_truth.py` | Ground Truth DB (Jeff's labels) |
| `results/v7/kiddushin_v7.json` | Kiddushin v7 results, pre-Wave-1 |
| `results/v8/wave2/kiddushin_v8.json` | Kiddushin Wave 2 (frozen baseline for Wave 3 gate) |
| `results/v9/wave3/kiddushin_v9.json` | Kiddushin Wave 3 results |
| `results/v9/wave3/ketubot_v9_2-60.json`, `results/v9/wave3/ketubot_v9_61-112.json` | Ketubot Wave 3 results |
| `tests/baselines/{kiddushin,ketubot}_wave2_baseline_today.json` | Today-regenerated Wave 2 numbers (gate per Lesson 11) |
| `scripts/run_wave3.py` | Parameterized Wave 3 runner (--tractate / --range / --refs) |
| `scripts/apply_wave3_item4.py` | Apply item 4 to Wave 2 outputs (score-neutrality fast path) |
| `scripts/audit_wave3_item4.py` | Audit item 4 against Jeff's 17 boundary cases (`AUDIT_INPUT` env override) |
| `scripts/verify_wave3.py` | Wave 3 per-item pass/fail report |
| `scripts/compare_v8_v9.py` | Wave 2 vs Wave 3 side-by-side metrics |
| `scripts/run_kiddushin_wave1.py` | Kiddushin Wave 1 runner (v8) |
| `scripts/verify_wave1.py` | Wave 1 verification |
| `scripts/audit_text_spans.py` | **Structural gate** — mid-word / clause-edge rates; `--strict` fails the build |
| `scripts/strip_text_spans.py` | Reverts LLM char-offset spans to segment-level boundaries |
| `scripts/measure_recall_vs_expert_list.py` | **True recall** vs. an expert's detector-blind list; reports what Stage 4g withheld |
| `scripts/report_mishnah_filter_delta.py` | What the Mishnah filter costs vs. the golden — scores twice through the immutable harness |
| `docs/findings/2026-08-30-mishnah-filter-delta.md` | The measurement + why it is a scope question for Jeff |
| `comms/JEFF.md` | **Open questions for the next email to Jeff** — ask in the order listed |
| `jeff comms/b.ketubot (1).doc` | Jeff's 2005 Ketubot story list — detector-blind ground truth. Count it with `parse_kiddushin_list.py --self-test` |
| `jeff comms/8-30-2026/kidushin.doc` | Jeff's Kiddushin list — parse with `parse_kiddushin_list.py`, NOT `parse_expert_doc` |
| `scripts/parse_kiddushin_list.py` | **Table-aware expert-list parser** — reads the .doc's OLE streams; `--self-test` asserts Ketubot == 149 |
| `results/expert_lists/kiddushin_2005.json` | **Kiddushin blind ground truth** — per-story `blind` and `counts_for_recall` flags, plus Jeff's anchored remarks. **Filter on the flags; never take the raw length as the denominator.** |
| `docs/findings/2026-08-30-kiddushin-list-parse.md` | Why the line-based parse gave 105, and how the count was verified |
| `jeff comms/8-30-2026/Kiddushin missed stories.docx` | **The appendix** — our own cases, which Jeff merged into his list. Those 5 entries are NOT blind |
| `scripts/check_appendix_coverage.py` | **Blindness check** — run on every new expert list before trusting it (Lesson 29) |
| `scripts/build_ruler.py` | **THE ruler** — joins blind lists + proposals + all 6 review rounds; measures Detection and Classification together |
| `results/rulers/{ketubot,kiddushin}_ruler.json` | Per-story: expert-listed? proposed? every verdict, and what each rejection objected to |
| `docs/findings/2026-08-30-detection-classification-ruler.md` | Why the old Classification precision figures were not Classification numbers, and why loose recall overstates strict |
| `results/recall/ketubot_jeff2005_matches.json` | Per-story recall match output (incl. the 6 misses) |
| `results/v10/wave4_notrim/` | **Current honest outputs** — segment-level boundaries, no spans |
| `docs/findings/2026-08-28-recall-measurement-ketubot.md` | The first blind recall measurement, and the method (Hebrew 4-grams + a corpus-wide window) |
| `docs/findings/2026-08-28-wave4-span-failure-audit.md` | Span failure audit + revert |
| `docs/history/2026-08-30-PLAN-wave5b-clause-roles.md` | Clause-role labelling — the judgment layer on Wave 5 |
| `docs/history/2026-08-29-PLAN-wave6-story-criteria.md` | Jeff's story criteria (6c blocked on his answer) |
| `src/prompts/clause_roles_v*.md` | Versioned labelling prompts |
| `tests/expert_boundary_targets_2005.json` | **294 detector-blind boundaries** from Jeff's 2005 list — the neutral ruler; catches regressions |
| `tests/expert_boundary_targets_v2.json` | 70 correction boundaries (was 52) — widened harvest + `quote_polarity` |
| `tests/expert_boundary_targets.json` | 52 sub-segment boundaries Jeff stated (superseded by _v2) |
| `scripts/build_boundary_testset_2005.py` | Aligns Jeff's 2005 story texts to Sefaria Hebrew -> exact boundaries |
| `docs/findings/2026-08-30-boundary-ruler-rebuild.md` | **Ruler rebuild** — why a corrections-only exam cannot see a regression, and what replaced it |
| `scripts/build_boundary_testset.py` | Rebuilds that test set (text-anchored, version-proof) |
| `scripts/score_boundary_targets.py` | Scores any run against it |
| `results/clause_labels/` | Per-clause labels — a reusable asset, not a wave by-product |
| `docs/findings/2026-08-30-wave5-summary-fix.md` | Wave 5 steps 1-2, and the first noise floor this project ever measured |
| `results/v11/wave5_summaryfix/` | Wave 5 spans with the summary fix (+ a same-code repeat = noise floor) |
| `tests/test_wave5b_runner_outcomes.py` | **Failure-injection guard** — a failed call must never be stamped as a judgment (Lesson 21) |
| `tests/fixtures/wave5b_runner_pages.json` | Real 4-page Kiddushin slice covering every outcome bucket |
| `lessons/` | Durable rules from past sessions. Read before starting; append after any correction. |
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
- `docs/findings/2026-03-25-golden-dataset-v10.md` - Golden dataset work
- `lessons/` - After any correction or surprise
- `CLAUDE.md` - If project structure or key files change

## Don't
- Change APIs/models without asking
- Add "improvements" beyond request
- Claim "fixed" without testing
- Modify `evaluate_golden.py` during experiments
- Use few-shot examples from pages being evaluated
- Ask an LLM for a character offset into text (Lesson 16) — anchor to real text units
- Ingest ground truth from a converter's output (Lesson 28) — parse the source format; `textutil` silently drops table columns and relocates Word comments
- Call an expert list blind without checking it against what we sent him (Lesson 29) — 5 of Jeff's 95 Kiddushin stories are our own output, merged in and unmarked
- Plan a fix from an expert's sample without first measuring the defect's corpus-wide rate (Lesson 18)
- Attribute a score change to a code change without a same-code repeat run (Lesson 22)
- Move detector output to a new key without making the harnesses read it (Lesson 27) — an invisible deletion reads as a model failure
- Generalise one expert correction into a corpus-wide rule without counting how many of their *other* labels it touches (Lesson 27)
