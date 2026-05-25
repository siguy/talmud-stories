# Wave 3 Approach — Decisions Before Implementation

**Session date:** 2026-05-24
**Status:** Approved by Simon; implementation pending.
**Companion to:** `docs/golden/v8/wave2_results.md`, `tasks/PLAN_kiddushin_fixes.md` (Wave 3 section).

This doc records the design decisions for Wave 3 *before* any code is
written, so the implementation can be checked against an explicit plan and
so a future reader can see what alternatives were rejected and why.

---

## Scope

Wave 3 ships four changes:

1. **Issue #8** — multi-story-per-page prompt change (catch 71a's missed second story).
2. **Issue #9** — embedded-story few-shots in Stage 2 prompt (catch 33a objection-embedded, 81b baraita-embedded).
3. **Issue #6(B)** — sharper story-vs-non-story rules in Stage 2 prompt.
4. **NEW sub-issue from Lesson 12** — text-internal boundary editing for the 16 Kiddushin cases Wave 2 segment-level snap/trim could not reach.

Items 1–3 are prompt changes — they move the composite score and require the
gate. Item 4 is a deterministic post-processor that adds a new field;
the score harness does not read that field, so item 4 cannot move the
composite either direction.

---

## Critical finding driving the design

`scripts/evaluate_golden.py` computes Boundary IoU on **segment indices
only** (`start_segment`, `end_segment`). It never reads story text.

Implication: any fix for text-internal boundaries (where Jeff's desired
start/end is INSIDE a segment, not at a segment boundary) cannot register
as a Boundary IoU change unless we also change the segment indices.
Changing segment indices means re-segmenting the corpus, which would break
the existing golden labels in both tractates.

Therefore item 4 is a **review-debt repayment**, not a score-improvement
play. Its value is qualitative: Jeff's next review UI shows story text
that starts and ends at the right Hebrew phrase, even when that phrase
lives mid-segment.

---

## Options weighed for item 4 (text-internal boundaries)

| Option | What it does | Why rejected / accepted |
|---|---|---|
| **A. Sub-segment text trimming with `text_span` field** | Find introducer/trailer inside the start/end segment; record a `text_span: {start_char, end_char}` slice; render UI uses the slice. Segment indices unchanged. | **ACCEPTED.** Zero score risk (harness ignores `text_span`). Directly addresses Lesson 12. Pure-Python post-processor, fits Wave 2's pattern. Reversible. |
| **B. Re-segment at intake on hard punctuation** | Split Sefaria segments on `:` / `.` so each clause is its own segment. | Rejected. Changes all segment indices → breaks both goldens → multi-session re-labeling effort. Violates the spirit of the IMMUTABLE harness rule. |
| **C. Prompt-side text spans** | Ask Stage 2 to emit Hebrew quoted spans alongside indices. | Rejected. Harness still ignores the spans (same as A on score), plus it layers a prompt change on top of the three other prompt changes in Wave 3 — compounding nondeterminism risk for no measurement benefit. |

---

## Why option A over deferring (option B/"do nothing")

Considered: just skip text-internal boundaries this wave, leave for Wave 4.

Rejected because:
1. Jeff explicitly named these boundary cases in 2026-04-23. Wave 2 already
   shipped without fixing them and said so in the writeup. Skipping again
   means Round 3 review surfaces the same 16 complaints.
2. The `text_span` field is a forward-compatible primitive — once it
   exists, future expert feedback on boundaries can be applied automatically.
3. Item 4 carries no score risk, so bundling it into Wave 3 costs only
   implementation time, not gate margin.

---

## Detector versioning decision

Wave 3 changes the Stage 2 prompt (items 1, 2, 3). Per the project
convention (memory: `feedback_detector_versioning.md`): **detector changes
must create a new versioned file, not edit canonical in place.**

Decision: **fork `src/story_detector_v8.py` → `src/story_detector_v9.py`.**

Rationale:
- The prompt diff for items 1+2+3 is large enough to warrant a clean
  version boundary rather than a wave flag inside v8.
- v8 stays the frozen Wave 2 baseline; v9 is Wave 3. Same pattern as
  v7 → v8.
- Item 4 (`text_span` post-processor) lives in v9 too — runs after Stage 4.
- All Wave 2 post-processors (snap, trim, biblical-actor) carry forward
  unchanged into v9.

---

## Score gate

Per Lesson 11 (LLM nondeterminism breaks historical baselines), the gate
must compare today-Wave-3 against today-Wave-2, NOT against the frozen
Wave 2 scores in `wave2_results.md`.

**Before Wave 3 runs:** regenerate today's Wave 2 baseline by re-running
`scripts/apply_wave2.py` on the existing Wave 1 outputs and re-scoring.
(Apply_wave2 is deterministic Python, so this should produce identical
scores to the frozen ones — but we lock today's numbers as the
session-local comparison point. If they drift, Lesson 11 is in play and
we investigate before proceeding.)

**Pass criteria:**
- Kiddushin composite (Wave 3) ≥ Kiddushin composite (Wave 2, today)
- Ketubot composite (Wave 3) ≥ Ketubot composite (Wave 2, today)
- Each Wave 3 issue has a concrete pass/fail check in `scripts/verify_wave3.py`

If gate fails on Ketubot, the prompt changes (items 1, 2, 3) are the
likely cause — bisect by disabling them one at a time. Item 4 cannot
cause a gate failure since the harness can't see it.

---

## Few-shot source for item #9

Per Lesson 2 (don't train on the eval set): few-shot examples for the
embedded-story prompt MUST NOT come from Kiddushin pages.

Sources:
- Baraita-embedded example: Ketubot golden (e.g. a known `דְּתַנְיָא` story).
- Objection-embedded example: Ketubot or Berakhot golden.

Specific stories to be picked during implementation from the existing
Ground Truth DB (`src/ground_truth.py`), verified not-from-Kiddushin
before insertion.

---

## Item 4 implementation sketch (the new piece)

A new post-processor `edit_text_internal_boundaries(stories, pages)`
runs after Wave 2's `filter_biblical_actor_stories` in v9's Stage 4.

For each story:
1. Look at the FIRST segment of the story. Search its text for any of
   the canonical Hebrew introducers (same regex list as Wave 2's
   `snap_start_to_introducer`).
2. If found AND the introducer is not at the very start of the segment
   AND the prefix before the introducer looks like halakhic framing
   (heuristic: contains no narrative verbs), record
   `text_span_start: {segment: i, char_offset: N}`.
3. Look at the LAST segment of the story. Search its text for any of
   the trailing stam-Talmud markers (same regex list as Wave 2's
   `trim_trailing_stam_segments`).
4. If found AND the marker is not at the very start of the segment,
   record `text_span_end: {segment: j, char_offset: M}`.
5. The rendered UI uses these offsets to slice the segment text;
   absent the field, it falls back to the full segment as today.

Verification:
- Apply to the 16 Kiddushin cases Jeff flagged. For each, confirm the
  proposed text-span matches Jeff's intent (manual review against the
  feedback JSON).
- Confirm `text_span_*` fields are present where expected and absent
  where the introducer/trailer is at a true segment boundary (Wave 2
  already handled those).
- Confirm score harness output is bit-identical with and without the
  post-processor (harness should not see the new fields).

---

## What item 4 does NOT promise

- No general quality lift outside the 16 flagged cases (and any others
  that happen to match the same patterns).
- No vindication of the introducer-detection regex until Jeff's Round 3
  review confirms.
- No effect on Boundary IoU — by design. The fix is qualitative.

---

## Files expected to change in Wave 3

- **NEW:** `src/story_detector_v9.py` — v8 + prompt changes for #8/#9/#6(B)
  + `edit_text_internal_boundaries` post-processor.
- **NEW:** `scripts/run_kiddushin_wave3.py`, `scripts/run_ketubot_wave3.py`
  (or a single parameterized runner).
- **NEW:** `scripts/apply_wave3.py` — apply text-span post-processor to
  Wave 2 outputs (fast-path that doesn't re-bill the LLM, mirrors
  `apply_wave2.py`). Note: prompt-change items 1/2/3 require a real
  LLM re-run; apply_wave3 only covers item 4.
- **NEW:** `scripts/verify_wave3.py` — concrete pass/fail per Wave 3 item.
- **NEW:** `scripts/compare_v8_v9.py` (or extend `compare_v8_waves.py`).
- **NEW:** `results/v9/wave3/{kiddushin_v9,ketubot_v9_2-60,ketubot_v9_61-112}.json`
- **NEW:** `docs/golden/v8/baselines/{kiddushin,ketubot}_wave2_baseline_today.json`
  (today's regenerated Wave 2 numbers per Lesson 11).
- **NEW (at end of session):** `docs/golden/v9/wave3_results.md`.
- Update: `validation/ui` generator to render `text_span_*` if present.

---

## Open questions to resolve during implementation

1. Heuristic for "prefix before introducer looks like halakhic framing"
   in item 4. Start with: "no verbs from a narrative-verb list." If
   too restrictive, fall back to: "snap whenever introducer is found
   mid-segment." Decision deferred to implementation when the 16 cases
   are visible.
2. Whether `apply_wave3.py` should also re-run items 1/2/3 via LLM, or
   strictly the deterministic item 4. Default: strictly item 4. Prompt
   re-runs go through the full `run_*_wave3.py` runners and are billed.
