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
   collided four ways on 2026-08-30. **Fill in `writes:`** — the paths the item will
   modify. `blocked_by` says what must finish *first*; `writes:` is the only thing that
   says what cannot run *beside* it, and they are different graphs.
3b. **Before running anything concurrently, `python3 scripts/board.py lanes`.** It groups
   open items so two items in different lanes never write a common path. **The lane count
   is how many sessions the work supports — not the unblocked-item count**, and it is
   always the smaller number. Do not guess it from `STATE.md`: items that file lists side
   by side as ready have been found writing the same golden.
4. **Finish** by adding `## Outcome` — including *why*, especially for a revert — then
   `python3 scripts/board.py finish <slug>`. It refuses without an Outcome, re-roots the
   item's relative links (they break one level deeper, which is where done items live),
   and moves it. **Never delete it.**
5. **Run `python3 -m pytest tests/ -q` before you stop.** `tests/test_bookkeeping.py` is
   in that suite and fails on a dangling dependency, an unknown capability slug, a moved
   golden, or a stale `STATE.md`.

Read [`FRAMEWORK.md`](FRAMEWORK.md) for how each capability is measured and why each gate
is what it is. Use its language: capability names, BLIND vs CIRCULAR on every dataset, and
measured / indicated / suspected on every finding.

**Fresh clone:** `pip install -r requirements.txt && python3 scripts/board.py setup`.
`setup` is idempotent and wires two things that cannot travel in a commit: the pre-commit
guard on the immutable harness, and the merge drivers that regenerate `STATE.md` /
`WORK.md` instead of merging them. Without it those two files conflict on **every** pair
of concurrent branches — for no information, since a generated file's correct content is
never a blend of two sides. The same checks are in the test suite either way.
*A clone was found on 2026-08-31 with `core.hooksPath` unset: the guard this file calls
active was not active. One command, so there is nothing to remember but the one.*

**Concurrency, in one line:** each session takes **one lane** (`board.py lanes`), works on
`work/<slug>`, and **does not rewrite `STATUS.md`** — that is an integration step done
once on main after merging, not a thing each branch does, because it is hand-written and
"rewritten every session" means two sessions always conflict over the whole file.
Merging several branches back, or recovering a worktree that was never pushed:
[`docs/technical/integrating-concurrent-work.md`](docs/technical/integrating-concurrent-work.md).
**Capture before you integrate** — a commit is recoverable forever, an uncommitted working
tree is one `git checkout` from gone, and `git checkout` is step one of every merge.

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
4. **Always run `evaluate_golden.py` with `--output <scratch path>`.** Bare, it overwrites
   `docs/golden/v7/baseline_ketubot.json` — a score from a run that cannot be reproduced
   (Lesson 11), so the loss is permanent. *Guarded: `test_bookkeeping.py` and the
   pre-commit hook both pin that file's hash. If it fires, `git checkout --` the file.*
5. **Never verify with the composite score.** It is built from ratios over pages already
   in the golden, so *deleting* expert validations makes it go **up** — it is
   anti-correlated with the risk. Verify with **counts** and `git hash-object` instead.
   The counts live in one place — `GOLDEN_COUNTS` in `tests/test_bookkeeping.py`, which
   asserts them on every run. Read them from there; do not copy them into prose, including
   here. *Guarded for the values, not for the habit.*
6. **Never `git stash`.** `refs/stash` is shared across every worktree, so a stash in one
   session is visible and poppable in another. Commit to your branch instead.
   (`git stash create` also silently drops untracked files.) *Not enforceable — this one
   is on you.*

## Data Structure
```
pages[].segments[] → contains english/hebrew text
pages[].stories[] → references segments by index (NO text)
pages[].mishnah_stories[] → stories Stage 4g WITHHELD from stories[] (same shape)

When flattening stories, MUST copy: page_segments: page.segments
```

`stories[]` is not the whole output. Stage 4g moves Mishnah-internal stories to
`mishnah_stories[]`. A reader blind to that key scores a withheld story as one we never
found (4 of Ketubot's 15 golden false negatives; Lesson 27). **Any code that reads a run
for scoring or display must decide about that key explicitly** — and say which way, in a
comment, so the next reader can tell a decision from an oversight. Who reads it today:

| reader | decision |
|---|---|
| `measure_recall_vs_expert_list.py` | reads it, reports withheld **separately**, never in the headline |
| `score_boundary_targets.py` | reads it; a target on a withheld story scores **`WITHHELD`**, not `N/A` |
| `build_ruler.py` | deliberately does **not** fold it into `proposed` — found-then-dropped ≠ never found |
| `generate_axis_review_ui.py` | shows it, **badged** and filterable |
| `evaluate_golden.py` | **blind, and immutable.** Its Mishnah delta comes from `report_mishnah_filter_delta.py`, which scores twice through the same harness. Run it before trusting a golden number |

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
| `scripts/measure_recall_vs_expert_list.py` | **True recall** vs. an expert's detector-blind list; reports what Stage 4g withheld. Also the only committed measurement of **triage recall**, and it splits the misses by cause: triage-discarded / examined-but-nothing-proposed / proposed-then-`NOT_A_STORY`. Use `--expert-json` for any list that is not the Ketubot `.doc` |
| `scripts/report_mishnah_filter_delta.py` | What the Mishnah filter costs vs. the golden — scores twice through the immutable harness |
| `scripts/run_triage_recall_price.py` | **Prices what triage discards** — runs Stage 2 on the skipped pages using their *cached* triage labels, so the skip decision is the only variable. `--dry-run` verifies the page partition with no API calls. Never uses the all-DELIBERATION `--skip-triage` default; that changes the prompt and confounds the result |
| `scripts/audit_no_triage_ablation.py` | **Proves `results/v7/ablation_v7_no_triage.json` is not a no-triage run** — the arm examining 3x the pages finds 5 fewer of Jeff's stories. No API calls. Why the 2026-02-13 ablation conclusion is retracted |
| `scripts/merge_triage_recall_run.py` | Splices that output back into a shipped run so the recall harness can score the **whole** tractate. `--live-rule` splices only the pages the *current* `should_skip_page()` would examine — that is how a triage rule change is measured against the blind lists |
| `scripts/sweep_triage_rules.py` | **Prices candidate Stage 1 rules with no API calls**, reusing the discarded-page output. Read [Lesson 37](lessons/) first: the on/off endpoints bracket a trade but do not locate it. Restricted to rules strictly looser than the shipped one, asserted per candidate |
| `scripts/resolve_unclassified_notes.py` | The hand-sort of the rejection notes `classify_objection()` cannot read, onto the four axes. Carries the **round → detector-version** map (`ROUND_SOURCES`) — extend it, do not re-derive it. Matches spans by **overlap**; exact-key matching makes a re-bounded story read as deleted (Lesson 36) |
| `scripts/harvest_kiddushin_comments.py` | Jeff's 10 anchored Kiddushin remarks, sorted at the **sentence** level onto axes, joined to our output by **strict span coverage**. The loose recall window credits a different passage on the same daf in 2 of 6 cases |
| `scripts/capture_january_round.py` | Recovers the **2026-01-08 round no ruler reads** — 25 verdicts skipped for eight months by an `isinstance` guard because it stores a list where every other round stores a dict (Lesson 38) |
| `docs/findings/2026-08-30-mishnah-filter-delta.md` | The measurement + why it is a scope question for Jeff |
| [`docs/STORY_RULES.md`](docs/STORY_RULES.md) | **THE RULE REGISTER** — one numbered rule per decision, with the expert's words, the date, and what it implies for data already on disk. **Read it before changing a prompt, a boundary or a dataset.** Carries the standing principle: his lists are evidence, so a rule that contradicts one is an *annotation*, never an edit |
| `comms/JEFF.md` | **Open questions for the next email to Jeff** — ask in the order listed |
| `jeff comms/b.ketubot (1).doc` | Jeff's 2005 Ketubot story list — detector-blind ground truth. Count it with `parse_kiddushin_list.py --self-test` |
| `jeff comms/8-30-2026/kidushin.doc` | Jeff's Kiddushin list — parse with `parse_kiddushin_list.py`, NOT `parse_expert_doc` |
| `scripts/parse_kiddushin_list.py` | **Table-aware expert-list parser, all five lists** (`--tractate`) — reads the .doc's OLE streams and detects each document's **column order** from its own header row, because `eruvin.doc` stores them right-to-left. Anchors multi-label rows against Sefaria; **never moves an unambiguous label** — a disagreement is a question for Jeff. `--self-test` asserts Ketubot == 149 |
| `results/expert_lists/kiddushin_2005.json` | **Kiddushin blind ground truth** — per-story `blind` and `counts_for_recall` flags, plus Jeff's anchored remarks. **Filter on the flags; never take the raw length as the denominator.** |
| `results/expert_lists/{gittin,yevamot,eruvin}_2005.json` | **The three pristine blind lists**, parsed 2026-09-01 — 112 / 102 / **74**, every entry blind. No detector has run on these tractates, so nothing of ours can be in them. Filter on the flags, as with Kiddushin |
| `docs/findings/2026-09-01-new-tractate-expert-lists.md` | The parse, and why Eruvin has 74 stories rather than the 73 on record |
| `docs/findings/2026-09-01-expert-list-daf-attribution.md` | **Per-daf attribution in the expert lists.** Two-amud headers are text-anchored; a reversed-column list is refused. Read before measuring any new tractate per daf |
| `docs/findings/2026-08-30-kiddushin-list-parse.md` | Why the line-based parse gave 105, and how the count was verified |
| `docs/findings/2026-08-31-kiddushin-recall.md` | Kiddushin Triage 95.6% / Detection 97.7%. **Quote Detection *given the page survived triage*** — the end-to-end figure charges Triage's losses to Detection as well |
| `docs/findings/2026-08-31-kiddushin-boundary-set.md` | The blind Kiddushin boundary set: 85%/91%, noise 7pt → 0.77 |
| `docs/findings/2026-08-31-triage-recall-price.md` | **What triage discards, priced on both tractates.** Exchange rates, and the reattribution of Ketubot 20a/82b from Triage to Detection |
| `docs/findings/2026-08-31-triage-single-narrative.md` | **The shipped triage rule change** — one narrative event is enough. Why `N>=1` and not `keep everything`, and why `V>=4` was rejected |
| `docs/findings/2026-08-31-unclassified-notes-resolved.md` | The 34 unreadable rejection notes, sorted. **Banked round precision is per detector-version** (Lesson 36). Carries a same-day Correction |
| `docs/findings/2026-08-31-kiddushin-comments-harvest.md` | Jeff's 10 anchored remarks. Retires the Kiddushin 58a question — he answered it in 2005 |
| `docs/findings/2026-08-31-january-round-recovered.md` | **The round nothing reads**: 25 of Jeff's verdicts, 9 cross-page refs covered by nothing, not mechanically foldable |
| `jeff comms/8-30-2026/Kiddushin missed stories.docx` | **The appendix** — our own cases, which Jeff merged into his list. Those 5 entries are NOT blind |
| `scripts/check_appendix_coverage.py` | **Blindness check** — run on every new expert list before trusting it (Lesson 29) |
| `validation/generators/generate_axis_review_ui.py` | **The per-axis review UI** — *is it a story* (yes/borderline/no) as the only required question; extent / confidence / grouping behind a disclosure that is **independent of it**, because "it IS a story and the boundary is wrong" is the commonest correction we get. `display_problem` is a field, not a note. On a wrong extent it opens a **Hebrew quote box with a stated `include`/`exclude` polarity** — highlight the text on the page rather than typing it — so a boundary correction stops being mined out of prose (16 of the 70 banked targets are `mixed`/`unclear` for want of it). Every exported verdict carries `detector_version` and `schema_version: axes-1`. Reads `wave4_notrim` and shows `mishnah_stories`, badged |
| `validation/generators/review_ui_core.py` | **The display core, shared** — one segment, one row, both languages. Both review pages import it, so neither can drift; guarded by `tests/test_review_ui_symmetry.py`. Pass `spanRangeFn=null` when there are no spans to annotate |
| `scripts/map_verdict_vocabularies.py` | **Three verdict vocabularies → the axis shape.** 605 banked verdicts, 0 unmapped. An unknown token **raises**. Carries `applies_to` (base vs already-corrected — Lesson 3) and marks a bare `incorrect` **lossy** rather than guessing which capability it indicted |
| `scripts/build_ruler.py` | **THE ruler** — joins blind lists + proposals + all 6 review rounds; measures Detection and Classification together |
| `results/rulers/{ketubot,kiddushin}_ruler.json` | Per-story: expert-listed? proposed? every verdict, and what each rejection objected to |
| `docs/findings/2026-08-30-detection-classification-ruler.md` | Why the old Classification precision figures were not Classification numbers, and why loose recall overstates strict |
| `results/recall/<tractate>_jeff2005_matches.json` | Per-story recall match output (incl. the misses), carrying `survived_triage` / `only_rejected` per story. **The unsuffixed name is always the recall denominator**; sensitivity variants take a suffix. `scripts/board.py` fills the Triage and Detection cells from these, so do not rename one casually |
| `results/v10/wave4_notrim/` | **Current honest outputs** — segment-level boundaries, no spans |
| `docs/findings/2026-08-28-recall-measurement-ketubot.md` | The first blind recall measurement, and the method (Hebrew 4-grams + a corpus-wide window) |
| `docs/findings/2026-08-28-wave4-span-failure-audit.md` | Span failure audit + revert |
| `docs/history/2026-08-30-PLAN-wave5b-clause-roles.md` | Clause-role labelling — the judgment layer on Wave 5 |
| `docs/history/2026-08-29-PLAN-wave6-story-criteria.md` | Jeff's story criteria (6c blocked on his answer) |
| `src/prompts/clause_roles_v*.md` | Versioned labelling prompts |
| `tests/expert_boundary_targets_2005.json` | **294 detector-blind Ketubot boundaries** from Jeff's 2005 list — the neutral ruler; catches regressions |
| `tests/expert_boundary_targets_2005_kiddushin.json` | **176 detector-blind Kiddushin boundaries.** Retires the 15-target corrections gate and its ±7pt noise. Built with `--expert-filter blind` (89), *not* the recall filter (90) — a boundary target must be an extent Jeff chose |
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
| `tests/test_examine_all_pages.py` | **Failure-injection guard** — bypassing Stage 1 must not fabricate its output. Pins that the flag only ever *adds* pages, that labels are identical with and without it, and that v7-v10 keep the stub so the archived ablation stays reproducible |
| `tests/fixtures/wave5b_runner_pages.json` | Real 4-page Kiddushin slice covering every outcome bucket |
| `tests/test_board_reports_what_it_holds.py` | **The board must report what an artifact HOLDS**, not what its loader recognised. Pins that every expert list gets its own row (two Kiddushin files collided on a key and the blind list was silently overwritten), that a comment harvest is sized in remarks and never as `0 parsed`, that an unrecognised shape is **named with its keys** rather than sized at zero, that the board's count-for-recall equals the harness filter *and* the ruler denominator, and that a verdict with a null type but a note still counts |
| `docs/findings/2026-09-01-board-guards-verify-the-wrong-property.md` | **Why `board.py --check` passing means less than it looks.** Three defects behind a green check; the STATE/code triage disagreement is still open |
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
- Ingest ground truth from a converter's output (Lesson 28) — parse the source format; `textutil` silently drops table columns and relocates Word comments. **A second instance, 2026-09-01:** `eruvin.doc` stores its columns right-to-left, so `textutil`'s flattened stream puts each location cell *after* its story and the line-based parser credited **53 of 73** entries to the previous row's daf — with the right story count, on real nearby dapim, so nothing looked wrong. `parse_expert_doc` now refuses such a list by name
- Call an expert list blind without checking it against what we sent him (Lesson 29) — 5 of Jeff's 95 Kiddushin stories are our own output, merged in and unmarked
- Plan a fix from an expert's sample without first measuring the defect's corpus-wide rate (Lesson 18)
- Quote a recall number without saying whether it is end-to-end or given-the-page-survived-triage — they differ by 2.7 points on Kiddushin and put the deficit in different columns
- Distinguish blind from circular ground truth by a **filename**; test the property (`source_round`, the `blind` / `counts_for_recall` flags). A filename comparison in `score_boundary_targets.py` would have labelled the blind Kiddushin set a corrections set
- Attribute a score change to a code change without a same-code repeat run (Lesson 22)
- Use `skip_triage=True` to mean "no triage" — **fixed in v11 on 2026-09-01 and renamed `examine_all_pages`; still live in the frozen v7-v10, deliberately.** It stamped every segment `DELIBERATION`, which Stage 2's prompt, the cross-page context, boundary refinement and post-processing all believed, and it overwrote labels the caller had supplied. `results/v7/ablation_v7_no_triage.json` is its output and is contaminated; the 2026-02-13 "largest accuracy driver" claim built on it is retracted (`docs/findings/2026-09-01-contaminated-no-triage-ablation.md`)
- Move detector output to a new key without making the harnesses read it (Lesson 27) — an invisible deletion reads as a model failure
- Generalise one expert correction into a corpus-wide rule without counting how many of their *other* labels it touches (Lesson 27)
- Act on an ablation's **endpoints** — "as-is" vs "off" — without sweeping the rules between them (Lesson 37). Once the "off" run exists every intermediate rule is a free re-partition of results you already hold, and the good deal is rarely at either end: on triage, the first step inside the interval was **28x cheaper** than turning the filter off
- Ship the best row of a sweep without saying whether it is a **principled boundary or a tuned threshold** (Lesson 37, Lesson 18). `N>=1` = "any evidence at all" and shipped; `V>=4` fitted one story in one tractate and was rejected *with a test pinning the rejection*
- Let a loader `continue` past an input it does not recognise without **counting and naming** what it dropped (Lesson 38) — an `isinstance` guard hid a signed 25-verdict expert round for eight months, and the file was listed in `STATE.md` the whole time. Absence is quiet; nobody investigates a zero
- Trust `board.py --check` as evidence that `STATE.md` is **true**. It verifies that STATE.md matches what `board.py` computed — if the generator misreads an artifact it misreads it identically on both sides and the check passes. It is a guard against hand edits and nothing else. **Right now its Triage cells describe the superseded corroboration rule** (`work/2026-09-01-board-reads-stale-triage.md`); read the caveat in `docs/capabilities/1_triage.md` before quoting them
- Key a dict by a **prefix of a filename** (`f.stem.split("_")[0]`). `kiddushin_2005` and `kiddushin_comments_harvested` both key to `kiddushin`, and the second silently overwrote the first — so `STATE.md`'s ground-truth table showed a row of zeros *instead of* the 90-story Kiddushin blind list, for as long as both files existed
- Count an expert verdict by whether its judgement field is **truthy**. Jeff's most informative Ketubot 17a verdict carries `feedback_type: null` plus a note quoting the Hebrew of the story he says the excerpt contains — declining the dropdown and answering in prose is a verdict, not an absence (Lesson 38's shape, reproduced inside the fix written for Lesson 38)
- List artifacts in an inventory **without their size**. Three filenames with no counts read as backlog; "**25 verdicts**" beside one of them reads as a problem (Lesson 38)
- Join a verdict to a proposal on an **exact `(ref, start, end)` key** — a later version re-bounding the same story then reads as the story having been deleted (Lesson 36). Match by overlap
- Gate the **extent / confidence / grouping** axes of the review UI behind a `No` on "is it a story". A passage can be a story *and* be mis-bounded — that is what `adjust` meant, and it is the commonest correction Jeff gives us. A test fails if this regresses
- Quote a **review round's precision as the current capability's number** without checking the current detector still makes those calls (Lesson 36). Of 8 notes where the detector disagreed at review time, 7 now agree
