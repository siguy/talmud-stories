---
title: Detector v13 — v12's 2026-10-07 wording plus the 2026-10-25 rulings, measured on the slice before Eruvin
capability: [classification, detection]
tractate: [eruvin, yevamot]
blocked_by: [2026-11-07-pre-eruvin-run-fixes]
awaiting: []
writes: [src/story_detector_v13.py, scripts/run_new_tractate.py, results/v11/v13_slice/, docs/findings/2026-11-07-detector-v13-slice.md, tests/test_prompt_is_fully_substituted.py, tests/test_twin_pass.py, tests/test_model_default.py, tests/test_examine_all_pages.py, tests/test_prompt_carries_the_rules.py, tests/test_run_new_tractate.py, tests/test_new_detector_code_is_v11_code.py, src/story_detector_v14.py, comms/JEFF.md]
finding:
superseded_by:
---

# Detector v13: the current rule register in the prompt, measured before it runs on Eruvin

**Self-contained.** Read [`FRAMEWORK.md`](../../FRAMEWORK.md), then
[`docs/STORY_RULES.md`](../../docs/STORY_RULES.md) R-C0, R-C2, R-C5, R-C7, then finding 10 of
[`2026-11-07-pre-eruvin-code-review.md`](../../docs/findings/2026-11-07-pre-eruvin-code-review.md).

## The decision (Simon, 2026-11-07)

**Eruvin runs on v13, measured first.** v11 (what `run_new_tractate.py` imports) carries none
of Jeff's October rulings. v12 (`src/story_detector_v12.py`, 2026-10-09, never run) carries
the 2026-10-07 ones but not the 2026-10-25 reply, and both files still say *"one real event +
discussion → LOW_CONFIDENCE"* — R-C7 shape 2, which he withdrew on 2026-10-25. The only
argument for v11 was that it is the only wording with a measured score; the measurement
below removes that argument rather than deferring to it.

## Why it is blocked

`src/story_detector_v12.py` is v11 plus 46 lines of prompt wording. The fix item changes
v11's **code** (4c boundary check, sorted stories, failed calls flagged). v13 must be built
from the **fixed** v11, or it re-imports the three P1s under a new version number. So: wait
for `fix/pre-eruvin-run-path` to merge, then build.

## Method

1. `cp src/story_detector_v11.py src/story_detector_v13.py` (the fixed v11). Apply the v12
   prompt diff to it (`diff src/story_detector_v11.py src/story_detector_v12.py` at the
   pre-fix commit `e88a159` — 46 lines, all prompt text, in the Stage 2 criteria block
   ~L282–347 and the twin-pass question ~L1012). v12 stays frozen as the record of what was
   written on 2026-10-09; it is never edited.
2. Add the 2026-10-25 rulings, **as abstract rules in his words, no passage quoted**
   (Lesson 2 / Lesson 8):
   - **Replace** the line *"LOW_CONFIDENCE — Borderline story: 1 real event + discussion"*
     and *"One real event + discussion about it → LOW_CONFIDENCE"* with: one event, then a
     ruling or a discussion, and nothing changes afterwards → **NOT_A_STORY** (*"not a story
     rather than borderline"*). An order that only *implies* its outcome does not count as a
     change (*"not really stated explicitly"*).
   - **Keep** borderline (LOW_CONFIDENCE) where the ruling is itself an act that changes
     something (*"the rabbi 'apportions' wine… more change"*); a bare statement by the rabbi
     *"would not even be borderline"*.
   - Make the same change in the twin-pass question's disqualifier list.
3. **Drop the dead weight while copying, since v13 is a new file and v11 stays frozen:** the
   `SERIES_RULE` flag and both `_SERIES_RULE*` strings (off, unmeasured, superseded by the
   twin pass), and the deprecated `skip_triage` alias with its `TypeError`/`DeprecationWarning`
   branch (its last caller, `tests/ablation_test.py`, moved to `archive/legacy_tests/` on
   2026-11-07). Retarget `tests/test_prompt_is_fully_substituted.py` to the single prompt and
   delete `test_skip_triage_alias_still_works_and_warns` for v13 (v7–v10 keep the stub, pinned).
4. Module docstring: "v13 = fixed v11 code + v12 wording + 2026-10-25 rulings; UNMEASURED
   at creation". `run_pipeline` returns `'version': 'v13'`; `run_new_tractate.py` imports
   v13 and takes its version string from the module, not a literal (review finding 6).
5. Update the tests that import the detector by version (`tests/test_prompt_is_fully_substituted.py`,
   `tests/test_twin_pass.py`, `tests/test_default_model.py` `LIVE_ENTRY_POINTS`, and any other
   `grep -l story_detector_v11 tests/`) so they pin v13; v11's own tests stay on v11.
   `test_prompt_is_fully_substituted` must pass on v13 — the 2026-09-09 incident was a
   prompt edit that ended an f-string early and lost every few-shot.
6. **Measure on the Yevamot slice** (copy `results/v11/twin_pass/slice.txt` to `results/v11/v13_slice/slice.txt`; 20 pages), the
   configuration every shipped number comes from (`gemini-3-flash-preview`, thinking off,
   twin pass on): v11 twice, v13 twice, same day. `python3 scripts/score_noise_floor_slice.py results/v11/v13_slice`
   gives mean recall, spread and `span_repairs` per arm. ~4 min and a few cents a run.
7. **Read the delta by name, not by the mean.** The new wording is *supposed* to drop list
   stories Jeff has since ruled out (the `superseded_by_rule.json` denominator already
   excludes 107b and 45a). A v13 loss that is one of his `not`s is the rule working; a loss
   that is a story he affirms (61a-shape habit-that-causes, 65a-shape ruling-that-acts) is a
   wording defect. Print both lists.

## How you know it worked

- v13 within v11's spread on the slice on stories he affirms, and dropping the ones he ruled
  out; both runs per arm, so a one-story delta is not read as a result (Lesson 43).
- `tests/test_prompt_is_fully_substituted.py` green on v13; `TWIN_PASS=0` vs `1` page prompt
  byte-identical on v13.
- `grep -c "event + discussion" src/story_detector_v13.py` is 0.

## Guardrails

- No passage Jeff ruled on appears in the prompt (Lesson 2, Lesson 8).
- Do not edit v11 or v12 in place; every lower version is a frozen ship point.
- Same-code repeat per arm before attributing anything (Lesson 22).
- `evaluate_golden.py` is immutable and must be run with `--output <scratch>` if at all.

## When done

Finding to `docs/findings/<date>-detector-v13-slice.md`, `## Outcome` here, then
`python3 scripts/board.py finish detector-v13-october-rulings`. Then the Eruvin items open
on v13.

## Outcome

**Built and measured; recommendation is not to run Eruvin on v13 as it stands.** Finding:
[`docs/findings/2026-11-07-detector-v13-slice.md`](../../docs/findings/2026-11-07-detector-v13-slice.md).

- `src/story_detector_v13.py`: fixed v11 + v12's 2026-10-07 lines byte for byte + the
  2026-10-25 rulings (one event then a ruling/discussion and no change → NOT_A_STORY;
  implied outcome is not a change; a ruling that is itself an act stays LOW_CONFIDENCE),
  in the Stage 2 criteria and the twin-pass question. `grep -c "event + discussion"` = 0.
  `SERIES_RULE` and the `skip_triage` alias dropped. The runner imports v13.
- Tests: prompt/twin/rules/examine-all/runner tests follow v13; v11's fix tests stay on
  v11 and `tests/test_new_detector_code_is_v11_code.py, src/story_detector_v14.py` pins that v13's code is v11's except five
  named prompt/version functions, so they still vouch for v13. (`writes:` named
  `tests/test_default_model.py`; the file is `tests/test_model_default.py`.)
- Slice, BLIND Yevamot list, 2 runs per arm, same day (indicated): v11 35/36 both runs,
  v13 34/36 both runs, spread 0, span repairs 0 everywhere. The one list story lost
  (78b:9, a question and answer) is the register applied but unruled by Jeff. v13 also
  kept a biblical episode (78b:13–20, YES) and Gemara commentary (105b:14–15) that v11
  rejects (R-S1, R-B4), merged two incidents at 90b, and the 2026-10-25 rule moved no
  proposal to NOT_A_STORY.
- **Why not ship:** two new errors the register already forbids, and the rule it was
  built for has no visible effect. Next: a v13-minus-step-2 arm (v11 code + v12 wording)
  on the same slice to locate the wording behind the two errors, then a v14.
- **Third arm, same day** (v11 code + v12's 2026-10-07 wording only, `df29904`): 35/36 both
  runs. It introduces the 105b commentary error and the 90b merge, and starts the 78b
  biblical error (1 of 2 runs); the 2026-10-25 lines finish it (2 of 2, YES), drop 78b:9 and
  add 65b:12 as borderline — likely our word "enforces", not his "apportions". No single
  sentence; three one-line v14 edits proposed in the finding, not written. 78b:9 is now
  `jeff:question-and-answer` in `comms/JEFF.md`.
- **v14** (v13 + the three edits), 2 runs beside 2 fresh v11 runs, same day: 34/36 both
  runs vs v11 35/36 (all four v11 runs). Edit 1 worked (65b:12 out), edit 2 did not
  (105b:14–15 still LOW), edit 3 worked in one run of two (78b:13–20). By the decision rule
  set before the runs, **the runner points back at v11**; v13 and v14 stay as measured
  records. Open: CLAUDE.md's "highest-numbered file is the active detector" is now false.
