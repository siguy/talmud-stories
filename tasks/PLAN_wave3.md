# PLAN — Wave 3 implementation

**Created:** 2026-05-24
**Status:** Approved, ready to execute.
**Approach doc:** `docs/history/2026-05-24-wave3-approach.md` (READ THIS FIRST — it explains the *why* behind every choice below).
**Source plan:** `tasks/PLAN_kiddushin_fixes.md` (Wave 3 section).
**Detector version:** new `src/story_detector_v9.py` (fork of v8).

This plan is self-contained — a fresh session should be able to execute it
end to end without re-deriving decisions.

---

## Critical context (read before touching code)

1. **Approach doc** explains the four items, why we forked to v9, why item 4 cannot move the score, and the gate.
2. **Lesson 11** (`lessons/`): LLM nondeterminism breaks historical baselines. Wave 2's frozen 0.9162 / 0.8962 are NOT the gate. Today's regenerated Wave 2 scores ARE.
3. **Lesson 2**: few-shots for item #9 must come from Ketubot/Berakhot, not Kiddushin.
4. **Lesson 8**: use abstract pattern descriptions in prompts, not specific Kiddushin passages.
5. **Lesson 12**: most boundary feedback is text-internal — item 4 addresses this; items 1–3 don't.
6. **CLAUDE.md**: `scripts/evaluate_golden.py` is IMMUTABLE. Don't touch it.

---

## Phase 0 — Pre-flight (deterministic, no LLM calls)

Goal: lock today's Wave 2 scores as the session-local gate.

- [ ] **0.1** Run `scripts/apply_wave2.py` on existing Wave 1 outputs for both tractates → fresh Wave 2 JSON outputs in a scratch location.
- [ ] **0.2** Score both with `scripts/evaluate_golden.py`. Save numbers to:
  - `tests/baselines/kiddushin_wave2_baseline_today.json`
  - `tests/baselines/ketubot_wave2_baseline_today.json`
- [ ] **0.3** Diff today's scores vs. the frozen wave2_results.md numbers. Expected: identical (apply_wave2 is pure Python). If they differ, STOP — Lesson 11 is in play and the comparison surface is wrong.
- [ ] **0.4** Record today's gate numbers in `tasks/PLAN_wave3.md` (this file, under "Session gate" below).

**Session gate (filled in during Phase 0.4):**
- Kiddushin Wave 2 composite (today): `0.8962` (matches frozen — Lesson 11 not in play)
- Ketubot Wave 2 composite (today): `0.9162` (matches frozen — Lesson 11 not in play)
- Per-metric: Kiddushin F1=0.9257 IoU=0.9815 Merge=0.6667 / Ketubot F1=0.8952 IoU=0.9563 Merge=0.878

---

## Phase 1 — Fork v8 → v9

- [ ] **1.1** Copy `src/story_detector_v8.py` → `src/story_detector_v9.py`. No behavior change yet.
- [ ] **1.2** Update version string / docstring at top of v9.
- [ ] **1.3** Smoke test: run v9 on one Kiddushin page; output should be identical to v8 on the same page (since prompts unchanged). If not, fork is wrong — investigate before proceeding.

---

## Phase 2 — Item 4: text-internal boundary post-processor (do this FIRST — no score risk)

Goal: implement and verify the score-neutral piece in isolation so Phase 3's prompt changes have a clean surface to layer on.

- [ ] **2.1** Add `edit_text_internal_boundaries(stories, pages)` to v9.
  - Reuse the introducer regex list from `snap_start_to_introducer` (Wave 2).
  - Reuse the trailing-marker regex list from `trim_trailing_stam_segments` (Wave 2).
  - For each story's first segment: if introducer is found at char offset > 0 AND prefix has no narrative verbs (start with a narrow narrative-verb list; expand if too restrictive), record `text_span_start: {segment: i, char_offset: N}`.
  - For each story's last segment: if trailing marker is found at char offset > 0, record `text_span_end: {segment: j, char_offset: M}`.
  - Wire into v9 Stage 4 after `filter_biblical_actor_stories`.
- [ ] **2.2** Create `scripts/apply_wave3_item4.py` — applies ONLY item 4 to Wave 2 outputs. Mirrors `apply_wave2.py`.
- [ ] **2.3** Run on Wave 2 Kiddushin output. Inspect all 16 Jeff-flagged boundary cases (list them by ID in `validation/feedback/kiddushin_review_2026-04-23.json`):
  - For each: print original segment text, proposed text-span slice, Jeff's quoted intent.
  - Hand-audit: how many of 16 produce a slice matching Jeff's intent?
  - Target: ≥10/16 land cleanly. <8/16 means heuristic needs tightening before proceeding.
- [ ] **2.4** Score-neutrality check: run `scripts/evaluate_golden.py` on Wave 2 output vs. item-4-applied output. Composites must be **bit-identical** (harness ignores `text_span_*`). If they differ, item 4 is accidentally changing segment indices — bug.
- [ ] **2.5** Update `validation/ui` generator to render text-span slice when present, fall back to full segment when absent.
- [ ] **2.6** Spot-check 3 Jeff-flagged cases in browser: verify rendering matches the slice.

---

## Phase 3 — Items 1, 2, 3: prompt changes (real LLM calls, gate applies)

Goal: layer prompt changes one at a time so a regression can be bisected without redoing all three.

### 3a — Item 1: multi-story per page

- [ ] **3a.1** Edit v9 Stage 2 prompt: add explicit instruction to return ALL distinct stories on the page, not the most salient one.
- [ ] **3a.2** Run v9 on Kiddushin 71a only (single-page smoke test). Expect ≥2 stories.
- [ ] **3a.3** If 71a still returns 1 story, fall back to iterative Stage 2 (per PLAN_kiddushin_fixes.md Issue #8 Option A).

### 3b — Item 2: embedded-story few-shots

- [ ] **3b.1** Pick 1 baraita-embedded story and 1 objection-embedded story from `src/ground_truth.py` — must NOT be from Kiddushin (Lesson 2). Record story IDs in code comments.
- [ ] **3b.2** Add as few-shots in v9 Stage 2 prompt with their correct boundaries.
- [ ] **3b.3** Run v9 on Kiddushin 33a + 81b only. Expect: 33a detects objection-embedded story; 81b detects baraita-embedded story.

### 3c — Item 3: sharper not-a-story rules

- [ ] **3c.1** Add Jeff's abstract rules to v9 Stage 2 prompt:
  - "A passage where all activity is verbal acts (אֲמַר / אָמַר לוֹ exchanges) without physical actions is NOT a story."
  - "Stories must be about rabbinic actors, not biblical ones."
  - "Stories require ≥2 distinct actions and some change or conflict."
- [ ] **3c.2** Use abstract pattern descriptions only — NO specific Kiddushin examples in the prompt (Lesson 8).

### 3d — Full runs + gate check

- [ ] **3d.1** Create `scripts/run_kiddushin_wave3.py` and `scripts/run_ketubot_wave3.py` (or parameterized runner).
- [ ] **3d.2** Full Kiddushin run with v9 (162 pages). Save to `results/v9/wave3/kiddushin_v9.json`.
- [ ] **3d.3** Full Ketubot runs with v9 (2-60 and 61-112). Save to `results/v9/wave3/ketubot_v9_2-60.json` and `results/v9/wave3/ketubot_v9_61-112.json`.
- [ ] **3d.4** Apply item 4 post-processor to all three outputs.
- [ ] **3d.5** Score all three with `scripts/evaluate_golden.py`.

**Gate check:**
- Kiddushin Wave 3 composite ≥ Kiddushin Wave 2 today's
- Ketubot Wave 3 composite ≥ Ketubot Wave 2 today's

- [ ] **3d.6** If Ketubot regresses: bisect by disabling items 3c → 3b → 3a (highest risk last). Item 4 cannot be the cause — skip it in the bisect.
- [ ] **3d.7** If bisect identifies a problematic item, document the failure mode in `docs/findings/2026-05-25-wave3-results.md` and ship the others.

---

## Phase 4 — Verification + ship

- [ ] **4.1** Build `scripts/verify_wave3.py` with concrete pass/fail per item:
  - Item 1: Kiddushin 71a has ≥2 stories.
  - Item 2: Kiddushin 33a has the objection-embedded story; 81b has the baraita-embedded story.
  - Item 3: Kiddushin false-positive count ≤4 (was 10 pre-Wave 3).
  - Item 4: ≥10/16 Jeff-flagged boundary cases now have correct `text_span_*` slices.
  - Gate: Kiddushin composite ≥ today-Wave-2; Ketubot composite ≥ today-Wave-2.
- [ ] **4.2** Build `scripts/compare_v8_v9.py` — side-by-side metric table for both tractates, both versions.
- [ ] **4.3** All checks green → commit. Tag `v9-wave3`.
- [ ] **4.4** Write `docs/findings/2026-05-25-wave3-results.md` mirroring `wave2_results.md` structure:
  - TL;DR for Jeff
  - What we shipped + per-item findings
  - How we know it worked (gate table)
  - What's deferred to Wave 4
  - Methodology notes (especially: why item 4 has score-neutral results)
  - Files changed
- [ ] **4.5** Update `CLAUDE.md` "Key Files" table: add v9 entries.
- [ ] **4.6** Update `docs/technical/VERSION_HISTORY.md` and `docs/technical/HOW_IT_WORKS.md`.
- [ ] **4.7** Add new Lesson(s) to `lessons/` for any surprises encountered.

---

## Files expected to be created or modified

**New:**
- `src/story_detector_v9.py`
- `scripts/apply_wave3_item4.py`
- `scripts/run_kiddushin_wave3.py` (or parameterized)
- `scripts/run_ketubot_wave3.py` (or parameterized)
- `scripts/verify_wave3.py`
- `scripts/compare_v8_v9.py`
- `results/v9/wave3/kiddushin_v9.json`
- `results/v9/wave3/ketubot_v9_2-60.json`
- `results/v9/wave3/ketubot_v9_61-112.json`
- `tests/baselines/kiddushin_wave2_baseline_today.json`
- `tests/baselines/ketubot_wave2_baseline_today.json`
- `docs/findings/2026-05-25-wave3-results.md`

**Modified:**
- `validation/ui` generator (text-span rendering)
- `CLAUDE.md` (Key Files table)
- `docs/technical/VERSION_HISTORY.md`
- `docs/technical/HOW_IT_WORKS.md`
- `lessons/` (if any new lessons)
- `tasks/todo.md` (check off Wave 3 items)

**Untouched (do NOT modify):**
- `src/story_detector_v8.py` (frozen Wave 2 baseline)
- `scripts/evaluate_golden.py` (IMMUTABLE)
- `results/canonical/*.json` (golden datasets)
- `results/v8/wave2/*.json` (frozen Wave 2 outputs)
