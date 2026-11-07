---
title: Fix the run-path defects found in the pre-Eruvin code review before spending the Eruvin run
capability: [detection, boundaries]
tractate: [eruvin]
blocked_by: []
awaiting: []
writes: [src/story_detector_v11.py, scripts/run_new_tractate.py, scripts/measure_recall_vs_expert_list.py, scripts/measure_strict_recall.py, scripts/audit_miss_anatomy.py, tests/, docs/technical/HOW_IT_WORKS.md]
finding: docs/findings/2026-11-07-pre-eruvin-code-review.md
superseded_by:
---

# Fix the run-path defects before the Eruvin run

**Self-contained.** Read [`FRAMEWORK.md`](../FRAMEWORK.md) first, then the finding this item
carries: [`2026-11-07-pre-eruvin-code-review.md`](../docs/findings/2026-11-07-pre-eruvin-code-review.md).
Every item below is a numbered finding there, with file, line and the artifact that shows it.

## The problem

The Eruvin run would be the first shipped artifact produced with the twin pass on by default,
and the review found that on that configuration Stage 4 can merge the wrong story across a
page break and delete the next page's first story (findings 1–2, **measured** on Gittin 36a
and on every twin-pass run on disk), and that a failed Stage 2 call is written as "no
stories" with no flag and then charged to Detection by the scorer (findings 3–4). Spending
the run first means scoring a defect as a recall number.

## Must land before the run (P1 + the P2s that change the number)

- [ ] **1** 4c `merge_cross_page_stories`: require the page-1 story to end at the page's last
      segment, or delete 4c (4b case 4 covers the flagged seg-0 case). Test: the Gittin 36a
      shape (one-segment story mid-page, flag only on the other side) must not merge.
- [ ] **2** Sort `stories` by `start_segment` at the end of `detect_stories`, after
      `validate_story_spans`; 4b/4c select the boundary story by max `end_segment` / min
      `start_segment`. Test: a twin appended after a flagged boundary story.
- [ ] **3** `_call_stage2`: after the second empty / truncated / unparseable response, raise
      so `_detect_with_retry` records `stage2_error`; count the no-candidates branch. Test:
      failure injection — a mocked `""` twice must produce `stage2_error`, never `stories: []`
      (Lesson 21, Lesson 31).
- [ ] **4** `measure_recall_vs_expert_list.py` and `measure_strict_recall.py`: read
      `stage2_error`; rows on a failed page are `call_failed`, out of both denominators,
      counted in the log.
- [ ] **7** `_load_checkpoint` drops entries carrying `stage2_error` so a resumed run retries
      them, and rebuilds `stage2_errors` from what it did resume.
- [ ] **6** `run_meta`: detector module name (from the import, not a literal), twin-pass env
      (`TWIN_PASS`, `TWIN_TRIGGER`, `TWIN_REACH`), `SERIES_RULE`, `_stage2_fingerprint`, git
      rev, `--refs`/`--retriage`, `triage_summary.failed`, and the detector's
      `truncated_responses` / `empty_responses` / `twin_failures` / `twin_verdicts`.
- [ ] **10 — a decision, not a fix:** which detector runs on Eruvin. v11 lacks Jeff's
      2026-10-07 rulings; v12 has them but not 2026-10-25, and both still carry the withdrawn
      "one event + discussion → LOW_CONFIDENCE" line. Record the choice in this item and in
      the run manifest. If v12 (or a v13 with 2026-10-25) runs, it is **unmeasured** — run it on
      the Yevamot 20-page slice beside v11 first (`score_noise_floor_slice.py`), twice each.

## Should land before the run (cheap, and the run is the first place they would bite)

- [ ] **5** `--retriage`: load the old cache and pop only the refs being re-triaged; refuse
      `--retriage` with `--refs` otherwise.
- [ ] **8** 429 / `RESOURCE_EXHAUSTED` retryable with backoff; `try/finally` around the final
      checkpoint write; pass `delay` into 4k.
- [ ] **9** `EventTriager(..., thinking_level=args.thinking)`; call `load_env()` before
      building the parser.
- [ ] **11** 4k: skip the end side when `spans_pages`.
- [ ] **12** 4i: `continue` on `spans_pages` (or run 4h/4i before 4b).
- [ ] **13** Biblical-actor filter: whole-token match, `'r. '` in the rabbinic signal, emit
      `OUT_OF_SCOPE`.
- [ ] **14** Stage 1 errors via `logging`; runner logs `summarize_triage()`; cached
      `TRIAGE_FAILED` pages re-tried; define `[TRIAGE_FAILED]` in the Stage 2 prompt header
      or render it `UNKNOWN`.
- [ ] **15** `measure_strict_recall.py` applies `superseded_by_rule.json`; regenerate the
      Yevamot / Gittin strict files.
- [ ] **16** `audit_miss_anatomy.py` derives its tractates from `board.TRACTATES`.
- [ ] **17** `tests/__init__.py`; retire or mark manual `test_wave4_ship_gate` (it calls a
      retired model with a live key).

## Not before the run — P3s in the finding

Flag removal (`SERIES_RULE`, `skip_triage`), the 4h/4i introducer contradiction, dedup
metadata, the `mishnah_stories` comment, the v7-importing merge test, stale docs and the
phantom `writes:` on `2026-08-30-eruvin-detection.md`. Fix that last one when opening the
Eruvin items: `board.py lanes` is grouping on a path nothing writes.

## How you know it worked

- A failure-injection test per P1 (Lesson 31: watch it fail first).
- `python3 -m pytest tests/ -q` collects and passes on this machine with no `--ignore`.
- Re-score the shipped Gittin run through fixed 4c **without re-running Stage 2** (Stage 4 is
  deterministic apart from 4d/4f/4k): Gittin 36b regains its story; Detection recall on the
  blind list does not fall.
- A `run_meta` on a smoke run (`--refs "Eruvin 2a,Eruvin 2b"`) names the detector module, the
  twin-pass setting and the fingerprint.

## Guardrails

- `evaluate_golden.py` is immutable and must be run with `--output <scratch>` if at all.
- No golden is touched. No prompt wording changes under this item except the decision in 10,
  which is its own measured change.
- Same-code repeat before attributing any score movement (Lesson 22); the detector is not
  deterministic at tractate scale (Lesson 43).

## When done

Add `## Outcome` here, then `python3 scripts/board.py finish pre-eruvin-run-fixes`.
