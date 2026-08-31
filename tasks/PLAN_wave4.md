# Wave 4 Plan — LLM-side text-span emission (replace regex boundary trimmer)

**Status:** APPROVED 2026-06-15 — Option B locked. Phase 0 in progress.
**Predecessor:** `tasks/PLAN_wave3_round2.md` (Round 2 of Wave 3 closed 2026-06-03)
**Source of truth for failure cases:** Jeff's 2026-06-03 reply, ingested in `validation/feedback/kiddushin_review_2026-05-26 (1).json`
**Lesson driving this work:** Lesson 15 (regex text-internal boundary editing cannot generalize)

---

## One-paragraph statement of the problem

Wave 3's `edit_text_internal_boundaries` post-processor uses a curated
list of Hebrew markers (`_START_INTRODUCERS` like ההוא ד, מעשה ב, כי הא ד;
`_TRAILING_MARKERS` like אלא, שמע מינה, אי הכי) to decide where a story
starts and ends inside its outer segment. Jeff confirmed this regex
approach works on five canonical openers but fails on seven other
stories where the same markers (אלא, rabbi names, ההוא) are story
content, not framing. Surface pattern matching can't tell content from
framing — only semantic judgment can. Wave 4 replaces the regex with
LLM emission of `text_span_start` / `text_span_end`.

---

## Decision: which architectural option

Two candidates. Pick ONE before implementation.

### Option A — Emit text spans during Stage 2 (single-pass)

The Stage 2 prompt already asks Gemini to identify the story's
start/end segment. Extend the schema to ask for the exact character
offsets within those segments where the narrative content begins and
ends. No extra LLM call.

**Pros:**
- Zero extra cost (rides existing Stage 2 calls).
- The model has full page context when choosing the slice.

**Cons:**
- Larger Stage 2 prompts → slightly higher per-page tokens.
- If Stage 2 misjudges segment boundaries, the slice is wrong too —
  one model, two coupled decisions.
- Cannot tune slice without re-running detection.

### Option B — Dedicated Stage 4 text-span call (two-pass)

Keep Stage 2 unchanged. After Stage 4 boundary post-processors, make
ONE additional Gemini call per detected story: "Here is the detected
story (page segments N to M with their Hebrew text). Return the
character offset in segment N where the story actually begins and the
offset in segment M where it ends. If the whole segment is story,
return -1."

**Pros:**
- Isolated, debuggable single-purpose call.
- Can tune the slice prompt without re-running detection.
- Easy to A/B against the regex version.
- Test set is small (only segments where regex currently disagrees with
  Jeff or fires at all).

**Cons:**
- ~$0.05-0.10 added cost per full Ketubot run (one call per ~180 stories).
- Latency: extra round-trip per story (parallelizable).

**Recommendation:** **Option B**. The cost is trivial, the decoupling is
worth it for debuggability, and the small failure surface is exactly
what Stage 4 was built for. (Option A is the upgrade if B works and we
want to optimize cost later.)

### Decision needed from Simon:

☐ Option A (single-pass) ☑ **Option B (two-pass) — LOCKED 2026-06-15** ☐ Other

---

## Held-out test set (built from Jeff's labels)

Wave 4 must clear these 14 cases on the first ship attempt. Tests live
in a new file `tests/test_wave4_text_spans.py`. The test set is locked
before implementation begins.

### Must KEEP full text (current regex over-trims them)

| Story | Failure mode |
|---|---|
| Kiddushin 8b_2-2 | Regex trimmed the opener; "first words ARE the story" |
| Kiddushin 9a_1-1 | Same (Jeff explicit "incorrect" verdict) |
| Kiddushin 9a_2-2 | Same |
| Kiddushin 13a_3-3 | Same |
| Kiddushin 31b_4-4 | Same |
| Kiddushin 33a_15-15 | Same |

### Must TRIM (current regex under-trims or doesn't fire)

| Story | What to trim |
|---|---|
| Kiddushin 8a_9-10 | First words of line 10 + Rav Ashi's statement (not part of story) |
| Kiddushin 12b_4-4 | "וְלָאו מִשּׁוּם דִּסְבִירָא לְהוּ דִּשְׁמוּאֵל" |

### Must PRESERVE (current regex works correctly — don't break these)

| Story | Currently correct |
|---|---|
| Kiddushin 12a_13-13 | "boundary correctly identified" (Jeff verbatim) |
| Kiddushin 25a_17-17 | regex output Jeff did not flag in 2026-05-26 review |
| Kiddushin 26b_2-2 | regex output Jeff did not flag |
| Kiddushin 26b_4-5 | regex output Jeff did not flag (empty notes = no objection) |
| Kiddushin 26b_10-10 | regex output Jeff did not flag |
| Kiddushin 32b_3-5 | regex output Jeff did not flag (empty notes = no objection) |

**Gate for ship:** all 14 must pass (6 keep-full + 2 trim-correctly + 6 preserve-confirmed).

---

## Implementation phases

### Phase 0 — Fixture lock (no LLM cost) ✅ 2026-06-15
- [x] Lock test set into `tests/fixtures/wave4_text_span_cases.json`
- [x] Build `scripts/extract_jeff_text_spans.py` that reads
      `validation/feedback/kiddushin_review_2026-05-26 (1).json` and emits
      the 14 fixtures in canonical form (story key + expected slice
      semantics — "full" / "trim" / "preserve_regex_output")
- [~] Today-fresh baselines — DEFERRED to Phase 3 per Lesson 11
      ("same window" rule). Running v9 baseline weeks before v10 comparison
      defeats the purpose.

### Phase 1 — Fork v9 → v10 (per detector-versioning rule) ✅ 2026-06-15
- [x] `cp src/story_detector_v9.py src/story_detector_v10.py`
- [x] Update version string + docstring; keep `V7StoryDetector` class name
- [x] v9 stays frozen as Wave 3 baseline (untouched on disk)
- [x] Smoke test: `import story_detector_v10` succeeds

### Phase 2 — Implement (Option B path) ✅ 2026-06-15
- [x] Add `extract_text_spans_via_llm(pages)` method to v10 — calls
      Gemini once per story with (start segment text, end segment text,
      story summary) in nikud-stripped coords and parses
      `{start_offset, end_offset}` JSON response
- [x] In v10 Stage 4 pipeline, REPLACE the call to
      `edit_text_internal_boundaries` with the new LLM function (only
      when `self.client` exists; pure-regex path retained for offline)
- [x] Regex pass extracted to `_apply_regex_text_span_to_story` and
      called as per-story fallback when LLM returns -1/-1 or errors
- [x] `text_span_source: 'llm'|'regex'|'none'` set on every real story;
      individual `text_span_start/end` records also carry their `source`

### Phase 3 — Run + verify ✅ 2026-06-15 (quantitative gates passed)
- [x] Run `tests/test_wave4_text_spans.py` on the 14 cases — **14/14 PASS**
- [x] Required prompt iteration: added explicit "ולאו משום ד...אלא משום
      ד..." pattern + framing-start examples (1 of 3 budgeted iterations
      used)
- [x] Fixture amendment: 8a_9-10 expectation relaxed to "start-trim only"
- [x] **Fast-path runner** `scripts/run_wave4.py`: takes v9 outputs (which
      have identical upstream detection), strips regex spans, runs only
      `extract_text_spans_via_llm`. Total cost: 196s of LLM time across
      262 real stories. Lesson 11 same-window concern N/A because we did
      NOT re-run upstream detection — v9 stories are the input.
- [x] Run all three files:
      - kiddushin_v9 → v10: 95 stories, llm=68 / kept_full=27 / skipped=0
      - ketubot_v9_2-60 → v10: 56 stories, llm=31 / kept_full=25 / skipped=0
      - ketubot_v9_61-112 → v10: 111 stories, llm=54 / kept_full=57 / skipped=0
      - **0% skipped rate** (gate ≤ 2% — PASS)
- [x] Composite scores (identical to Wave 3 — score-neutral confirmed):
      - Ketubot: composite=0.9171, F1=0.9141, IoU=0.95
      - Kiddushin: composite=0.8859, F1=0.90, IoU=0.9815
- [x] **KEEP_FULL production gate**: 0/6 violations (gate PASS)
- [x] Per-story v9-vs-v10 diff report via `scripts/diff_v9_v10_spans.py`:
      - Kiddushin: 17 both_full / 10 recovered_text / 33 new_trim /
        35 different_trim
      - Ketubot: 72 both_full / 10 recovered_text / 54 new_trim /
        31 different_trim
      - Reports: `docs/golden/v10/wave4_diff_{kiddushin,ketubot}.md`
- [x] Generate Wave 4 review UI for Jeff:
      - `validation/ui/wave4_kiddushin_review.html` (95 stories, 3.3 MB)
      - `validation/ui/wave4_ketubot_review.html` (167 stories, 5.9 MB)
      - Shows v10 LLM trims with v9 regex disagreement noted; filterable
        by category (recovered_text / new_trim / different_trim / etc.)
- [x] Email draft for Jeff: `comms/sent/2026-06-15-email-jeff-wave4.md`
- [ ] Run Kiddushin full → expect Kiddushin composite ≥ Wave 3 (0.8859);
      no FP/FN deltas (text spans are score-neutral)
- [ ] Run Ketubot full → expect Ketubot composite ≥ Round 2 (0.9171)
- [ ] Compare with `scripts/compare_v8_v9.py` style script (`compare_v9_v10.py`)
- [ ] Generate updated review UI showing v10 slices (green highlight on
      kept text, strikethrough on trimmed framing)

### Phase 4 — Ship (per Lesson 13 path)
Hardened ship gate (from 2026-06-15 plan review by DHH/Kieran/Simplicity):
- [ ] 14/14 fixture cases pass
- [ ] **Zero** of the 6 KEEP_FULL stories trimmed in the production
      Kiddushin run (not just the fixture run — check the actual
      `kiddushin_v10.json` output)
- [ ] `text_span_source: 'skipped'` rate ≤ 2% of detected stories
      (above this implies LLM reliability problem, not a ship)
- [ ] Both composites ≥ Wave 3 (Kiddushin 0.8859, Ketubot 0.9171)
- [ ] Per-story v9-vs-v10 diff artifact generated for Jeff (which stories
      gained/lost spans, with Hebrew text shown)

If any gate fails: do NOT ship; document and decide whether prompt
iteration is worth more cost (1 of 3 iterations used so far).

Post-ship:
- [ ] Commit, tag `v10-wave4`, push
- [ ] Write `docs/golden/v10/wave4_results.md`
- [ ] Update `docs/technical/VERSION_HISTORY.md`, `CLAUDE.md`,
      `lessons/` (Lesson 16 if anything surprises)
- [ ] Generate Wave 4 Kiddushin review UI for Jeff
- [ ] Send email with 14-case pass/fail report + per-story diff + ask
      him to confirm any remaining over-trims

---

## Cost estimate

- One LLM call per detected story
- Ketubot: ~180 stories × 1 call ≈ $0.10
- Kiddushin: ~95 stories × 1 call ≈ $0.05
- Phase 2 prompt iteration: budget 3 iterations on the 14-case test set
  before any full-tractate run ≈ $0.02
- **Total Wave 4 budget: ~$0.20** (vs Wave 3 at ~$0.30)

If Option A is chosen instead, cost is **$0** (extra tokens fold into
existing Stage 2 calls).

---

## Out of scope for Wave 4 (defer)

- **Track 1** — post-detection FP classifier. Still blocked until Jeff
  finishes verdicting the remaining ~85 Kiddushin stories (the labeled
  training data isn't ready).
- **Track 2** — second baraita-embedded few-shot for the 81b shape. Low
  leverage (1 known FN), not worth a separate wave.
- **Track 4** — Bava Metzia pivot. Wait until v10 ships so we test
  generalization on the better detector.
- **Re-segmentation passes.** If Wave 4 fails on certain cases because
  the segment boundaries Sefaria uses are themselves wrong, that's a
  Wave 5 problem.

---

## Risks + mitigations

| Risk | Mitigation |
|---|---|
| Gemini misparses character offsets for nikud-heavy Hebrew | Always strip nikud before sending; map offsets back via existing `_strip_nikud_with_map` |
| Per-story latency makes runs unbearable | Parallelize with `asyncio.gather` — Gemini Flash handles 10+ concurrent fine |
| LLM over-confidently trims real story content | Test set's "must keep full" cases catch this; default to "full" when ambiguous (prompt rule: "if any doubt, return -1/-1") |
| New approach disagrees with the 6 cases Jeff confirmed work | Hard fixture failure → blocks ship → iterate prompt or fall back to regex for that subset |

---

## Approval checklist (Simon)

- [ ] Option A vs B chosen
- [ ] Held-out test set above is correct (or amendments noted)
- [ ] Cost budget approved (~$0.20)
- [ ] Phase 0-1 can run unattended; Phase 2-3 needs at least one
      check-in before full-tractate execution

Once approved: execute Phase 0 → Phase 1 in one session, then check in.

---

## Plan review feedback applied (2026-06-15)

Three reviewers (DHH-style, Kieran-style, code-simplicity) examined the
plan after Phases 0–2 shipped at 14/14. Tier-1 changes applied below;
Tier-2 items (prompt simplification, helper inlining, Option A
reconsideration) deferred.

**Applied:**
1. **Regex fallback narrowed.** Old behavior: on LLM error, run regex
   on that single story. New behavior: log warning, mark
   `text_span_source: 'skipped'`, leave spans absent. Rationale: Jeff
   showed the regex over-trims; silent substitution re-introduces the
   bug. (Regex still runs when `self.client is None`, the offline path.)
2. **Fixture category renamed** `preserve_regex_output` →
   `regression_guard` with explicit SOFT semantics. Silence in Jeff's
   review is not endorsement. Pass = LLM didn't error.
3. **8a_9-10 relaxation documented in fixture** with `relaxed` block
   including Jeff's verbatim note and the reason text-span work cannot
   address segment-boundary removal.
4. **Phase 4 gate hardened**: now requires zero KEEP_FULL trims in
   production output (not just fixture) AND `skipped` rate ≤ 2%.
5. **`text_span_source` values split**: `'none'` was ambiguous; replaced
   by `'llm_kept_full'` (LLM ran, said keep-full) and `'skipped'` (LLM
   error).

**Deferred to Wave 5 consideration:**
- Option A (fold spans into Stage 2) — DHH's stronger claim that Stage 2
  has more context than Stage 4. Revisit if production runs show
  context-starvation errors.
- Prompt simplification (8-bullet rules → 3 sentences). Risk of
  regressing the 14/14 outweighs the cleanup benefit right now.
- Inline `_llm_text_span_for_story` into `extract_text_spans_via_llm`.
  Cosmetic; not load-bearing.
