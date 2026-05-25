# PLAN — Kiddushin fixes from Jeff's 2026-04-23 feedback

Companion to: `docs/golden/kiddushin_feedback_analysis_2026-04-23.md`.

Each issue is ranked by impact. For each, three options are weighed, then a chosen path is recommended on the simplest-thing-that-works principle (per CLAUDE.md: simplicity first, minimal blast radius, no premature abstraction).

The plan is ordered so that **purely mechanical fixes ship first** (no model changes, no risk of overfitting). Model-prompt changes come last and only on tractates NOT being scored.

---

## Issue #1 — Cross-page first-segment skip ("the glitch")

**Evidence:** Reviews #75 (70b), #77 (71b). Jeff named this explicitly.
**Effect:** Continuations lose the first segment of the second page.

**Options considered:**
- **A. Off-by-one fix in the stitching code.** Inspect the merge function in Stage 4 and ensure `seg_index_start_on_page2 = 0`, not `1`.
- **B. Re-fetch the full text range from Sefaria after continuation is decided** and trust Sefaria's range string.
- **C. Post-process diff against raw page text** — detect any segment-0 of a continued page that is not included and force-include.

**Synthesis & choice → A.** Pure bug. Find the loop, fix the index, add a unit test on pages 70a-b and 71a-b. B is heavier and introduces a network dep. C is a band-aid.

**Tasks:**
- [ ] Reproduce on Kiddushin 70a–70b and 71a–71b with debug logging.
- [ ] Patch the off-by-one in the merge routine.
- [ ] Add regression test: assert seg 0 of page2 is in the merged story when continuation fires.
- [ ] Re-run continuation check across Kiddushin, diff old vs new.

**Risk:** very low. Mechanical change.

---

## Issue #2 — Continuation check false positives (non-continuous bridges)

**Evidence:** #11 (12b→13a), #21 (29b→30a), #26 (31a→31b), #47 (39b→40a). All cases have *intervening* sugya material between the two halves.

**Options considered:**
- **A. Gap-aware check:** require that segments between candidate-end on page1 and candidate-start on page2 be either (i) empty or (ii) all triaged as non-story.
- **B. Semantic continuity prompt:** call Gemini with both halves + intervening text, ask "is page2's content a direct continuation of page1's story?"
- **C. Hebrew connective check:** require the page2 candidate to start with a strict continuation marker (`וְ…`, `אֲמַר לֵיהּ…`, named-actor continuation) and reject otherwise.

**Synthesis & choice → A, with C as a cheap secondary signal.** A is deterministic, explainable, free. B costs an LLM call per continuation candidate (~12 on Kiddushin) and re-introduces a confidence wobble. C alone is too lexical and will reject valid bridges.

**Tasks:**
- [ ] In continuation-check stage, compute `intervening_segments = page1.segments[end+1:] + page2.segments[:start]`.
- [ ] If any intervening segment is labeled `STORY` or `HIGH_NARRATIVITY` by triage, reject the bridge.
- [ ] Add Jeff's 4 cases as negative regression fixtures.
- [ ] Add Jeff's 12 detected continuations as positive regression fixtures.

**Risk:** low. Could over-reject; mitigate by reviewing the 12 known-good cases against the new gate.

---

## Issue #3 — Story-START boundary snapping (~11 cases)

**Evidence:** #1, 2, 16, 20, 34, 38, 45, 52, 64, 72, 73. Detector starts before the introducer.

**Options considered:**
- **A. Lexical snap.** After Stage 2 returns a story span, scan inside it for the canonical introducers (`מַעֲשֶׂה ב…`, `כִּי הָא ד…`, `הָנְהוּ בֵּי תְרֵי`, `הַהוּא בַּר…`). If found, snap `start` to that segment.
- **B. Prompt refinement.** Tell Stage 2 explicitly: "stories begin at `מַעֲשֶׂה ב…` / `כִּי הָא ד…`; do not include the preceding halakhic framing."
- **C. Boundary LLM pass.** A dedicated boundary-only LLM step over each detected story.

**Synthesis & choice → A.** Jeff's rule is consistent and lexical. Deterministic snap is auditable, costs no tokens, ships today. B competes with detector instincts and re-opens calibration. C is overkill and slow.

**Tasks:**
- [ ] Build introducer regex list in Hebrew (covering nikud variants).
- [ ] Post-process: if a known introducer is found within the first 3 segments of a detected story, set `start = introducer_segment`. If found in the segment *immediately before* start, extend to include it.
- [ ] Regression-test on the 11 flagged Kiddushin cases.
- [ ] Verify it doesn't regress Ketubot's IoU.

**Risk:** low–medium. Must validate on Ketubot golden set so we don't drop IoU below 0.97.

---

## Issue #4 — Story-END boundary trimming (~9 cases)

**Evidence:** #7, 18, 19, 33, 61, 80, 81, 86, 87. End sweeps Talmud's commentary.

**Options considered:**
- **A. Lexical trim.** Strip trailing segments that start with stam-Talmud markers (`שְׁמַע מִינַּהּ`, `מַאי טַעְמָא`, `וְאִי`, `שָׁאנֵי`, `הָכִי קָאָמַר`, attribution chains `אָמַר רַבִּי X אָמַר רַבִּי Y`) when they follow a narrative.
- **B. Register-shift detection via LLM** ("is the last segment dialectic commentary or narrative continuation?").
- **C. Train a small classifier** on Ketubot's boundary-corrected dataset.

**Synthesis & choice → A.** Same logic as Issue #3 — Jeff's pattern is lexically recoverable. C is interesting later (we have a corrected Ketubot dataset that could train it) but premature now.

**Tasks:**
- [ ] Compile trailing-segment marker list with nikud variants.
- [ ] Post-process: walk the detected story from the end backward and drop segments that start with these markers, while a story-like segment remains.
- [ ] Regression-test on the 9 flagged Kiddushin cases.
- [ ] Verify no Ketubot regression.

**Risk:** low–medium. Same Ketubot validation step.

---

## Issue #5 — Stage 1 triage recall on `מַעֲשֶׂה ב…` / `הָנְהוּ בֵּי תְרֵי`

**Evidence:** Missed 45a and 53a (Category 5). Both had `skipped_by_triage: True`.

**Options considered:**
- **A. Lexical auto-include.** If a page contains any of `מַעֲשֶׂה ב…`, `הָנְהוּ בֵּי תְרֵי`, `הַהוּא ד…`, `כִּי הָא ד…` anywhere, force Stage 2 to run.
- **B. Loosen triage threshold globally.** Cheaper triage, more Stage 2 calls everywhere.
- **C. Replace triage with a different prompt.**

**Synthesis & choice → A.** Triage's job is recall, not precision; the cost of running Stage 2 on a false-positive page is a few cents, the cost of missing a story is catastrophic. Lexical override is dirt-cheap and targeted.

**Tasks:**
- [ ] Add lexical override pass before Stage 1 emits `skipped_by_triage`.
- [ ] On Kiddushin re-run, confirm 45a and 53a now flow into Stage 2 and produce stories.
- [ ] Audit other tractates' triage decisions for the same false-negatives.

**Risk:** very low. May produce a few false-positive pages that Stage 2 will correctly discard.

---

## Issue #6 — Story-discrimination false positives (10 cases)

**Evidence:** #13, 22, 31, 40, 41, 42, 44, 51, 69, 82. Sub-patterns: (a) dialogue-only, (b) biblical content, (c) single-event no-change.

**Options considered:**
- **A. Three small deterministic post-filters** layered on Stage 2 output:
  - (a) **Dialogue-only filter:** if every segment in the detected story consists primarily of speech-act markers (`אֲמַר`, `אָמַר לוֹ`, `אֲמַר לֵיהּ`) with no physical-action verbs, demote to non-story.
  - (b) **Biblical-actor filter:** if the only named actors are biblical (Adam, Moses, David, etc. — finite list from Sefaria's topic graph), demote.
  - (c) **Change/conflict check:** ask Stage 2 to emit a `narrative_actions_count` and `has_change_or_conflict` field; demote stories with `<2` actions or no change.
- **B. Sharper Stage 2 prompt** including Jeff's explicit rules (no dialogue-only; rabbinic only; ≥2 actions; change/conflict required).
- **C. Add a Stage 3 "is this really a story?" reviewer LLM** that re-rates each detected story.

**Synthesis & choice → mix of A(b) + B.**
- (b) biblical-actor filter is cheap and high-precision — do this.
- (a) and (c) are tricky to get right deterministically; better expressed in prompt (B).
- C is the heaviest hammer; reserve for if A+B don't close the gap.

**Tasks:**
- [ ] Build biblical-actor name list (export from Sefaria topics).
- [ ] Add filter post Stage 2: if `actors ⊆ biblical_names`, drop.
- [ ] Refine Stage 2 prompt: add explicit "not a story" examples from Jeff's 10 cases — but **only after holding out Kiddushin from the few-shot pool** (Lesson 2: never train on the eval set).
- [ ] Use Ketubot/Berakhot examples for the negative few-shots.

**Risk:** medium. Prompt changes risk Ketubot regression — must re-score Ketubot golden after every change. **This is the only step that touches the model and must be guarded by `scripts/evaluate_golden.py`.**

---

## Issue #7 — Mishnah-segment filter

**Evidence:** #58 (50b), #59 (52a).

**Options considered:**
- **A. Use Sefaria's structural metadata** — each segment has a `category` / `is_mishnah` flag. Skip those at intake.
- **B. Lexical detection of Mishnah voice** (tannaitic Hebrew register, formula `מַתְנִי׳`).
- **C. Run a separate Mishnah corpus pipeline** and exclude Mishnah-source segments from Talmud results.

**Synthesis & choice → A.** Sefaria exposes the structural info; trust it.

**Tasks:**
- [ ] In Stage 1 input fetch, tag each segment with `source = mishnah | gemara`.
- [ ] Filter `source == mishnah` segments out of story detection input.
- [ ] If Mishnah-tagged stories are interesting separately, log them to a parallel file.

**Risk:** very low.

---

## Issue #8 — Multi-story-per-page under-recall

**Evidence:** Missed 71a — page had 2+ stories, detector kept only 1.

**Options considered:**
- **A. Iterative Stage 2:** after a story is detected, re-prompt with remaining ungrouped segments to detect more.
- **B. Single-shot prompt change:** instruct Stage 2 to return *all* story groupings, not just the most salient one.
- **C. Sliding-window:** run Stage 2 on overlapping segment windows.

**Synthesis & choice → B first, A as fallback.** B is one prompt edit and should suffice if the model is capable (it is — Stage 2 already returns multiple stories on most pages). A is a clean fallback if B underperforms.

**Tasks:**
- [ ] Strengthen Stage 2 instruction: "Return every distinct story on the page; do not stop at the most salient one. Output an array."
- [ ] Add Jeff's 71a as a fixture: expect ≥2 stories.
- [ ] If 71a still fails, implement A.

**Risk:** low. Same Ketubot validation gate.

---

## Issue #9 — Embedded-story blindspots (baraita-embedded, objection-embedded)

**Evidence:** Missed 33a (objection-embedded) and 81b (baraita-embedded).

**Options considered:**
- **A. Few-shot example pair** in Stage 2 prompt: one objection-embedded story (from Ketubot/Berakhot) and one baraita-embedded story, each with their correct boundaries.
- **B. Pre-segmentation pass:** explicitly split sugyot at `דְּתַנְיָא:`, `וְהָא…וְלָא…`, then run Stage 2 on each sub-block.
- **C. Topic-graph cross-check** with Sefaria's links to known stories.

**Synthesis & choice → A.** Few-shot is the lightest touch and directly addresses the model's blindspot. B is heavy and risks fracturing pages. C is interesting but data-quality-dependent.

**Tasks:**
- [ ] Pick one baraita-embedded story and one objection-embedded story from Ketubot golden — they must NOT be from Kiddushin and not from the page being evaluated.
- [ ] Add as few-shots in Stage 2 prompt.
- [ ] Verify Kiddushin 33a and 81b now detect the missed stories.
- [ ] Re-score Ketubot golden — must stay ≥0.93.

**Risk:** medium. Few-shots can shift behavior unpredictably. Strict eval gate required.

---

## Issue #10 — Confidence calibration (lowest priority)

**Evidence:** 16 disagreements. Jeff: "these should not be considered errors."
**Action:** **defer.** Not worth touching now — risk of breaking other things outweighs the upside on a category Jeff says doesn't matter.

If we touch this later: add a brief rubric to the Stage 2 prompt (HIGH = ≥2 actions + conflict/change + named rabbinic actors + concrete setting; LOW = thin narrative or partial event; YES = canonical story like `מַעֲשֶׂה ב…`).

---

## Sequencing

**Wave 1 — mechanical, no model change, ship in one session:**
1. Issue #1 — first-segment skip
2. Issue #2 — continuation check gap-aware
3. Issue #7 — Mishnah filter
4. Issue #5 — triage lexical override

Validation: re-run Kiddushin pipeline; expect 45a + 53a recovered, 4 false bridges removed, glitch gone, 2 corpus errors gone. **No Ketubot risk** in this wave.

**Wave 2 — deterministic post-processors, model untouched:**
5. Issue #3 — start-boundary snap
6. Issue #4 — end-boundary trim
7. Issue #6(b) — biblical-actor filter

Validation: re-run Kiddushin AND Ketubot. Ketubot composite must stay ≥0.93 — that's the gate.

**Wave 3 — prompt changes (highest risk, separate session):**
8. Issue #8 — multi-story prompt
9. Issue #9 — embedded-story few-shots
10. Issue #6(B) — sharper story-vs-non-story rules

Validation: full Ketubot + Kiddushin eval. If Ketubot drops, revert. Few-shots must NOT come from Kiddushin (Lesson 2).

**Wave 4 — deferred:**
- Issue #10 confidence calibration

---

## Success criteria

Before sending Jeff the next round:
- All 5 missed stories present in output.
- The 4 false-continuation bridges (#11, 21, 26, 47) no longer fire.
- The 2 first-segment-skip cases (#75, 77) include segment 0.
- The 10 "not a story" cases drop to ≤4.
- The 2 Mishnah cases gone.
- Boundary issues drop from ~30 to <10.
- Ketubot composite stays ≥0.93 (immutable eval harness).

If we hit these, we send Jeff Round 2. Otherwise we iterate before sending.
