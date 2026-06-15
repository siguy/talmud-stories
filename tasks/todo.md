# Golden Dataset + Detector Improvement Plan

**Created:** 2026-03-25
**Updated:** 2026-03-25 (revised Phase 6 after cost analysis)
**Source:** Jeff's canonical review (2026-03-17) + analysis in `docs/golden/canonical_feedback_analysis.json`
**Goal:** Build the definitive Ketubot ground truth, then use it to improve detection for all tractates.

---

## Git Strategy & Rollback Plan

### Branch Structure
```
claude/sefaria-talmud-story-search-Mw1Yg  (current main branch)
  │
  ├── Commit A: (ac8e83c) Documentation + analysis
  ├── Commit B: (d85da87) 17 classification corrections
  ├── Commit C: (838c550) Boundary lookup tooling
  ├── Commit D: (72414c3) 32 boundary/merge corrections
  ├── Commit F: (dc16195) Eval framework + baseline (0.93)
  ├── Commit G: (7787f2c) Autoresearch infrastructure
  │
  ├── Tag: v10-golden-ketubot
  ├── Tag: pre-detector-changes  ← ROLLBACK POINT
  │
  ├── Commit H: Expand ground_truth.py with Jeff's new corrections
  ├── Commit I: Add legal disqualifier to Stage 2 prompt
  ├── Commit J: Re-run detector + evaluate improvement
  │   If composite drops below 0.90 → git revert to pre-detector-changes
  │
  └── Future: feat/generalize-tractate-X branches
```

---

## Phase 1: Machine-Readable Documentation (DONE ✓)
- [x] Analyze all 187 canonical review entries
- [x] Cross-reference with 3 prior feedback rounds for consistency
- [x] Classify error patterns and extract Hebrew boundary markers
- [x] Identify 10 repeated issues Jeff flagged before that we didn't fix
- [x] Output: `docs/golden/canonical_feedback_analysis.json`
- [x] Output: `scripts/analyze_canonical_feedback.py` (reproducible)
- [x] Output: `docs/golden/error_taxonomy.md`

**Git: Commit A** (ac8e83c)

---

## Phase 2: Classification Corrections (DONE ✓)

Applied 17 classification corrections (10 NOT_A_STORY + 5 LOW_CONFIDENCE + 1 HIGH_CONFIDENCE + 1 special case).

- [x] 10 NOT_A_STORY reclassifications
- [x] 5 LOW_CONFIDENCE reclassifications
- [x] 106a_3-3: YES → HIGH_CONFIDENCE
- [x] 111a_23-25: NOT_A_STORY → LOW_CONFIDENCE (cross-page merge stripped in Phase 3)

**Git: Commit B** (d85da87)

---

## Phase 3: Boundary Corrections (DONE ✓)

### 3a. Boundary Lookup Tool (DONE)
Built `scripts/boundary_lookup.py` — resolved 17/52 corrections automatically.

**Git: Commit C** (838c550)

### 3b-3e. Apply All Corrections (DONE)
Applied 32 corrections via `scripts/apply_boundary_corrections.py`:
- [x] 7 stories confirmed correct (needs_review removed)
- [x] 8 boundary trims (overextended into Talmud commentary)
- [x] 5 boundary extensions
- [x] 5 same-page merges
- [x] 4 new cross-page merges
- [x] 3 special cases (111a un-merge, 3a confirm, 104a cleanup)
- [x] Spot-checked 10 corrections ✓
- [x] 0 needs_review remaining ✓

**Deferred (5 items):** 103b_3-3, 60b_2-3, 60b_5-9, 49b_12-12, 12b_0-0

**Git: Commit D** (72414c3)

---

## Phase 4: Golden Dataset (DONE ✓)

- [x] Golden dataset: 182 stories (down from 189)
- [x] 0 needs_review remaining
- [x] Tag `v10-golden-ketubot` applied

Classification distribution: YES=54, HIGH=28, LOW=76, NOT_A_STORY=24

---

## Phase 5: Evaluation Framework (DONE ✓)

### 5a. Composite Scoring (DONE)
Built `scripts/evaluate_golden.py` (IMMUTABLE). Scores:
- Classification F1, Boundary IoU, Merge F1, Composite (0.4/0.4/0.2 weights)

### 5b. Baseline Score (DONE)
- Classification F1: **0.92** (156 TP, 26 FP, 2 FN)
- Boundary IoU: **0.98** (excellent overlap)
- Merge F1: **0.86** (16/19 merges detected)
- **Composite: 0.93**

Main improvement target: 26 false positives (legal discussions Jeff says are NOT stories)

### 5c. 2nd Tractate Baseline (PENDING — needs Jeff)
- [ ] Pick tractate (suggest Bava Metzia)
- [ ] Run detector on 10-15 pages
- [ ] Have Jeff spot-review → mini ground truth
- [ ] Score baseline

**Git: Commit F** (dc16195)
**Git: Tag `pre-detector-changes`** applied

---

## Phase 6: Targeted Detector Improvement (REVISED)

### Why we changed the approach

The original plan called for a 50-experiment autoresearch loop at ~$100 budget. Cost analysis
revealed the actual cost per full Ketubot re-run is **~$0.30** (Gemini Flash, not Claude), making
50 experiments ~$15 not $100. But the bigger issue is that blind iteration is wasteful when the
error taxonomy already tells us exactly what's wrong:

- **26 of 28 errors are false positives** — the detector calls legal discussions "stories"
- The error taxonomy identifies 6 specific patterns with Jeff's language
- 2-3 targeted changes should capture most gains; diminishing returns after that

### Revised approach: Focused 3-step sprint

**Cost: ~$0.30 total. Time: ~10 minutes.**

All changes on current branch (not a separate experiment branch — these are well-understood
fixes, not speculative experiments).

### Step 1: Expand ground_truth.py (Commit H)

Add Jeff's canonical review corrections to the Ground Truth DB. The detector's few-shot
example bank currently has 128 entries from prior rounds. Adding the new corrections teaches
the model what legal false positives look like.

**Specific additions:**

11 LEGAL_FALSE_POSITIVE examples:
- 7a_1-1: "no events, just legal discussion" (was LOW_CONFIDENCE)
- 7a_2-2: "not a story, reasoning leads to that conclusion" (was LOW_CONFIDENCE)
- 13b_0-0: "hypothetical legal case" (was LOW_CONFIDENCE)
- 13b_16-16: "just a legal decision, dialogue only" (was LOW_CONFIDENCE)
- 15b_2-2: "just a reference to a story mentioned above" (was LOW_CONFIDENCE)
- 21b_7-8: "all legal discussion, dialogue not events" (was HIGH_CONFIDENCE)
- 25a_9-10: "finding someone in study hall is not an event" (was LOW_CONFIDENCE)
- 26a_9-9: "hypothetical scenario" (was LOW_CONFIDENCE)
- 26b_0-0: "continuation of hypothetical" (was YES)
- 110b_24-24: "just one action and explanation" (was LOW_CONFIDENCE)
- 8a_13-13: downgraded HIGH → LOW, "too little causality"

5 CONFIDENCE_MISCALIBRATION examples:
- 14b_11-11: "two events, no causality" (HIGH → LOW)
- 17a_10-10: "habitual, not one-time" (YES → LOW)
- 21a_10-11: "mostly legal case" (HIGH → LOW)
- 25b_6-6: "two events, no real causality" (YES → LOW)
- 106a_3-3: "minimal action, request and rejection" (YES → HIGH)

Each entry includes:
- Story key, page ref, segment range
- Jeff's verdict and reasoning (exact quote)
- Error pattern classification
- Old and new classification

### Experiment Results: REVERTED (composite dropped 0.93 → 0.89)

We ran two experiments on 2026-03-25:

**Experiment 1: Expanded few-shots + aggressive disqualifiers**
- Added 5 new disqualifiers to the prompt (dialogue-only, references, one-action-plus-ruling, etc.)
- Added confidence calibration section
- Expanded ground_truth.py from 128 → 282 entries with canonical review
- Result: **CATASTROPHIC regression.** Pages 2-60 dropped from 72 to 44 stories.
  Composite: 0.57. Model became far too conservative — rejected legitimate stories.

**Experiment 2: Expanded few-shots + light confidence calibration only**
- Reverted the aggressive disqualifiers, kept only confidence calibration (3 lines)
- Kept expanded ground_truth.py (282 entries)
- Result: **Still a regression.** Pages 2-60 dropped from 72 to 52 stories.
  Full composite: 0.89 (vs 0.93 baseline). Pages 61-112 barely changed (110 → 109).

**Root cause:** The few-shot examples from the canonical review are mostly from pages 2-60.
When the model sees examples of passages from pages 2-60 that Jeff says are NOT stories,
it over-applies that reasoning to other passages on the same pages. This is textbook
overfitting to the training data.

**Decision: REVERT all detector changes.** The baseline detector (0.93) is better.

**Lesson learned:** The 26 false positives are genuine judgment calls where the model and
Jeff disagree. They can't be fixed by prompt engineering or few-shot examples from the same
data. Improvement requires either:
1. A fundamentally different detection approach (e.g., fine-tuning on Jeff's labels)
2. A post-processing step that uses the golden labels directly (but that's just lookup, not detection)
3. Accepting 0.93 as the ceiling for prompt-based detection on Ketubot

The v10 results are preserved in `results/v10/` for reference.

**Cost of experiments: ~$0.60 (two full Ketubot runs at ~$0.30 each).**

---

## Phase 7: Generalize to Other Tractates (FUTURE)

**Each tractate gets its own branch: `feat/generalize-tractate-X`**

### 7a. Apply Ketubot Lessons to New Tractate

1. Run detector with Ketubot-learned improvements
2. Use expanded few-shot examples
3. Measure error pattern rates → compare to Ketubot rates
4. Focus on: legal false positive rate, boundary precision, cross-page merges

### 7b. Self-Validation Protocol

Without Jeff reviewing every story:
1. Run detector
2. Run adversarial validation with Ketubot-calibrated few-shots
3. Auto-flag stories matching known error patterns
4. Present ONLY flagged stories for Jeff → reduce his workload by ~70%

### 7c. Continuous Improvement

Each Jeff review batch:
1. Incorporate into golden dataset (tractate-specific)
2. Re-run detector with updated few-shots
3. Cross-tractate validation prevents overfitting

---

## Deferred Items

1. **5 boundary corrections:** 103b_3-3, 60b_2-3, 60b_5-9, 49b_12-12, 12b_0-0
2. **Review UI regeneration** — generate updated HTML for spot-checking in browser
3. **2nd tractate baseline** — needs Jeff's review time
4. **Narrative cycle grouping** — Rabbi Yehudah HaNasi's death spans 103a-104a

---

## Verification Checklist

- [x] 48/53 actionable items addressed (5 deferred)
- [x] Classification corrections verified (17/17 spot-checked)
- [x] Boundary corrections verified (10/10 spot-checked)
- [x] 0 needs_review remaining
- [x] Baseline score: 0.93 composite
- [x] Tag `v10-golden-ketubot` applied
- [x] Tag `pre-detector-changes` applied
- [x] Step 1-3: Ran detector improvement experiments → REVERTED (regression)
- [ ] Review UI generated and spot-checked in browser
- [ ] Cross-tractate baseline (pending Jeff review)

---

## Wave 3 (2026-05-24 / 2026-05-25, SHIPPED per Lesson 13)

**Result:** Ketubot composite 0.9162 → 0.9170 (+0.044 recall, −7 FNs). Kiddushin composite 0.8962 → 0.8859 (5 new candidate stories incl. Jeff's flagged-missing 33a seg 5 bathhouse story). Shipped despite Kiddushin gate fail per Lesson 13. Full writeup: `docs/golden/v9/wave3_results.md`.

**Approach doc:** `docs/golden/v8/wave3_approach.md`
**Detector:** new `src/story_detector_v9.py` (fork of v8)
**Gate:** Kiddushin + Ketubot composites must each be ≥ today's regenerated Wave 2 score (Lesson 11).

### Pre-flight (do BEFORE any Wave 3 change)
- [x] Regenerate today's Wave 2 baselines for both tractates → save to `docs/golden/v8/baselines/{kiddushin,ketubot}_wave2_baseline_today.json`
- [x] Lock today's Wave 2 composite numbers as the session-local gate

### Item 1 — Issue #8 multi-story per page (prompt change)
- [x] Edit Stage 2 prompt in v9: "return every distinct story on the page; do not stop at the most salient one"
- [x] Add iterative Stage 2 fallback (one additional "find more stories" call per page when ≥1 found)
- [x] Fixture: Kiddushin 71a expects ≥2 stories — **FIXTURE FAILED** (71a still 1 story; "Babylon dough" segs 2-3 is debate more than narrative). Item 1 still ships — drove the Ketubot recall lift.

### Item 2 — Issue #9 embedded-story few-shots (prompt change)
- [x] Pick 1 baraita-embedded + 1 objection-embedded story from Ketubot golden (Ketubot 111b 13 + Ketubot 91a 19-20; NOT Kiddushin — Lesson 2)
- [x] Add as few-shots in v9 Stage 2 prompt
- [x] Fixtures: **partial** — Kiddushin 33a 5-5 (objection-embedded) **now detected** ✓; Kiddushin 81b seg 9 (baraita-embedded) **still missed** (lead-in `אלא תנאי היא. דתניא, אמר רבי מאיר…` doesn't match few-shot pattern closely enough)

### Item 3 — Issue #6(B) sharper story-vs-non-story rules (prompt change)
- [x] Add Jeff's abstract rules (no dialogue-only; rabbinic only; ≥2 actions; change/conflict required) to v9 Stage 2 prompt
- [x] Use ABSTRACT pattern descriptions, not specific Kiddushin examples (Lesson 8)
- [x] Verify the 10 false-positive cases on Kiddushin drop to ≤4 without Ketubot regression — **FAILED** (FP 9→14 — but new FPs include Jeff's flagged-missing 33a 5 and 5 other defensible narratives, Lesson 14)

### Item 4 — Text-internal boundary editing (post-processor, score-neutral)
- [x] Implement `edit_text_internal_boundaries(stories, pages)` in v9 Stage 4
- [x] Adds `text_span_start` / `text_span_end` fields when introducer/trailer is mid-segment
- [x] Verify on all 17 Kiddushin cases Jeff flagged in 2026-04-23 review — **10/17 PASS** ✓
- [x] Verify harness output is bit-identical with/without the field (score-neutrality check) — ✓
- [x] Update `validation/ui` generator to render the slice when present — green highlight on kept slice, strikethrough on trimmed framing

### Verification + ship (Lesson 13 path)
- [x] `scripts/verify_wave3.py` — concrete pass/fail per item
- [x] `scripts/compare_v8_v9.py` — side-by-side metric table
- [x] Run on both tractates: Kiddushin 0.8962→0.8859 (FAIL by gate, ship per Lesson 13/14); Ketubot 0.9162→0.9170 (PASS)
- [x] Bisect skipped: Ketubot did NOT regress; Kiddushin regression is detector-overtaking-golden per Lesson 14
- [x] Commit `dcefb30`, tag `v9-wave3`, push to origin
- [x] Write `docs/golden/v9/wave3_results.md`
- [x] Update docs/technical/{VERSION_HISTORY,HOW_IT_WORKS}.md, CLAUDE.md, tasks/lessons.md (Lesson 14)
- [x] Generate Kiddushin Wave 3 review UI, deploy to https://siguy.github.io/talmud-stories/validation/ui/kiddushin_review_wave3.html
- [x] Email sent to Jeff (jr6@nyu.edu) with 7 new Kiddushin candidates + 4 new Ketubot candidates + 10 boundary-slice confirmations

### Wave 3 follow-up (awaiting Jeff)
- [ ] Receive Jeff's verdicts on 7 new Kiddushin candidates (NOT received in 2026-06-03 reply — asked again)
- [ ] Receive Jeff's verdicts on 4 new Ketubot candidates
- [x] Receive Jeff's verdicts on 10 boundary-slice text edits (PARTIAL — 5 confirmed working, 7 flagged as over-trim; regex approach retired)
- [x] Apply Jeff's 4 Ketubot golden corrections from 2026-06-03 (7a_1, 26a_9, 102a_6, 106a_2-3) — `scripts/apply_jeff_2026-06-03_corrections.py`
- [x] Re-score Wave 3 Ketubot against updated golden: composite 0.9170 → 0.9171, F1 0.910 → 0.914 (`docs/golden/v9/wave3_round2_ketubot_rescore.md`)
- [x] Draft reply to Jeff (`docs/golden/v9/email_draft_jeff_wave3_round2.md`) — awaiting Simon to send
- [ ] Re-run canonical build with full Kiddushin verdicts once Jeff completes
- [ ] Re-score Wave 3 against updated Kiddushin golden once new candidates verdicted

### Wave 3 Round 2 (2026-06-03, IN PROGRESS)
Plan: `tasks/PLAN_wave3_round2.md`
- [x] Step 1: Apply Ketubot corrections + rescore
- [ ] Step 2: Send reply to Jeff (draft ready)
- [x] Step 3: Update docs (CLAUDE.md, todo.md, VERSION_HISTORY, Lesson 15)
- [x] Step 4: Drafted `tasks/PLAN_wave4.md` — Option B (Stage 4 LLM text-span call) recommended; 14-case held-out test set built from Jeff's labels; awaiting Simon approval before Phase 0 execution

---

## NEXT — Resume command (works post-/clear, fully self-contained)

Copy-paste this block to Claude Code to pick up where this session ended:

```
Resume the Talmud story detector project after Wave 3 ship.

Project state: v9 (Wave 3) is committed (dcefb30) on branch
claude/sefaria-talmud-story-search-Mw1Yg, tagged v9-wave3, pushed.
Email sent to Jeff Rubenstein (jr6@nyu.edu) on 2026-05-25 with the
Kiddushin Wave 3 review UI link
(https://siguy.github.io/talmud-stories/validation/ui/kiddushin_review_wave3.html)
asking him to verdict 7 new Kiddushin candidates + 4 new Ketubot
candidates + 10 boundary-slice confirmations.

READ FIRST (in order):
1. CLAUDE.md (project conventions, immutable files, current state)
2. tasks/todo.md (you are picking up at the "NEXT" section)
3. tasks/lessons.md (especially Lessons 2, 8, 11, 13, 14)
4. docs/golden/v9/wave3_results.md (what Wave 3 shipped + why)

DECIDE which track to start:

Track A — Jeff replied:
  - His export will be a JSON in validation/feedback/ (or attached
    to his reply — check Gmail via `gws gmail +read` or via the
    Gmail MCP).
  - Promote his verdicts into results/canonical/kiddushin_canonical.json
    and (if Ketubot verdicts present) ketubot_canonical.json using a
    new scripts/build_canonical_from_wave3.py modeled on
    scripts/build_kiddushin_canonical.py. Do NOT modify
    scripts/evaluate_golden.py (IMMUTABLE).
  - Re-score Wave 3 against the updated golden with
    `scripts/evaluate_golden.py`. Expected: Kiddushin composite ≥
    Wave 2 (because previously-FP candidates Jeff confirmed flip to
    TP). Write findings to docs/golden/v9/wave3_round2_results.md.

Track B — Jeff has not replied yet, start Wave 4 prep:
  - Open a brainstorm doc at docs/brainstorms/wave4_brainstorm.md.
  - Three concrete Wave 4 candidates ranked by impact:
    1. **Post-detection FP classifier** (highest leverage per Lesson 7
       — prompt rules hit a ceiling at 0.93). Train a small classifier
       (logistic regression / LightGBM) on Jeff's NOT_A_STORY labels
       from results/canonical/*.json that runs AFTER Stage 4 and
       demotes detected stories matching the FP pattern. Per Lesson 7
       this is safer than prompt mods (can never cause new FNs).
       Inputs: criteria_met_count, disqualifiers, named-actor type,
       segment-count, etc. Eval: must keep Ketubot recall ≥ 0.9367.
    2. **Second baraita-embedded few-shot** for the
       `אלא תנאי היא. דתניא, אמר רבי X… אמר רבי Y` shape (Kiddushin
       81b seg 9 still missed in Wave 3). Source from Ketubot or
       Berakhot canonical (Lesson 2 — never Kiddushin). Add as a
       third item-2-style example in the v10 Stage 2 prompt (fork v9
       → v10; do NOT edit v9 in place per detector-versioning rule).
    3. **Remaining 7 text-internal boundary cases.** Pattern in
       scripts/audit_wave3_item4.py output. Most need either:
       (a) non-canonical narrative-verb introducer like `רבי X הוה קאי`
           (33a seg 16) — extend _START_INTRODUCERS but carefully
       (b) end-phrase trim where trailing text doesn't start with a
           canonical stam marker (52b, 72a×2, 32b 2) — likely need
           prompt-side text-span emission rather than a regex.
  - Pick ONE for Wave 4 and write a plan at tasks/PLAN_wave4.md
    mirroring tasks/PLAN_wave3.md structure (Phase 0 baseline, Phase
    1 fork, Phase 2 implement, Phase 3 LLM runs, Phase 4 ship). Wait
    for user approval before executing.

Track C — Pivot to 3rd tractate:
  - Bava Metzia was the suggested next per todo.md Section 5c.
  - Follow docs/golden/workflow/new_tractate_workflow.md.
  - Use scripts/run_wave3.py as the runner template (parameterized
    by tractate); add a `--tractate bavametzia` config block. Will
    need Sefaria pages cache + triage cache (~10 min one-time run).
  - First-run gate is "does Wave 3 detector generalize" — no
    pre-existing golden, so plan for sending Jeff a fresh review UI.

RULES (NEVER violate):
- scripts/evaluate_golden.py is IMMUTABLE.
- Never use Kiddushin labels as few-shot examples when evaluating
  Kiddushin (Lesson 2).
- Always regenerate today's baseline before comparing — never trust
  frozen scores from past sessions (Lesson 11).
- Detector changes require a new versioned file (v9 → v10); never
  edit canonical detector in place.
- All multi-step work goes through tasks/PLAN_<wave>.md with user
  approval BEFORE LLM-billable execution.

Start by reading the four files above, then ask: "Has Jeff replied?
Or which Wave 4 track should we prep?"
```

### Wave 4 candidates (pick one per planning session)
- [ ] **Track 1 — Post-detection FP classifier** (Lesson 7 path). Train on Jeff's NOT_A_STORY labels. New file `src/post_detection_classifier.py`. Cannot cause new FNs by construction.
- [ ] **Track 2 — Second baraita-embedded few-shot** for the 81b shape (`אלא תנאי היא. דתניא, אמר רבי X…`). Fork v9 → v10.
- [ ] **Track 3 — Remaining 7 text-internal boundary cases** (non-canonical introducers + non-stam-marker end phrases). Likely needs prompt-side text-span emission.
- [ ] **Track 4 — Pivot to 3rd tractate (Bava Metzia)**. Tests Wave 3 generalization on a tractate where the golden isn't built from our detector's output (cleaner gate). Follow `docs/golden/workflow/new_tractate_workflow.md`.

### Stretch / longer-term
- [ ] Refresh `FOR_SIMON.md` to cover Wave 1/2/3 (currently pre-Wave-3)
- [ ] Document Lesson 5 ceiling-breaking options (fine-tuning on Jeff's labels vs post-detection classifier vs accepting 0.93)
- [ ] GitHub Pages site (`docs/WEBSITE_PLAN.md`) — non-technical project intro
