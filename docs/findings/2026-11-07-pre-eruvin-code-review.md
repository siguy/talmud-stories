# Code review of the new-tractate run path, before Eruvin

**Date:** 2026-11-07 · **Item:** `work/2026-11-07-pre-eruvin-run-fixes.md` · **Evidence:** code
reading plus shipped artifacts; no API calls; every finding marked **measured** (reproduced on
an artifact on disk or by simulation) or **indicated** (traced in code, no artifact shows it).

**Scope.** Exactly the path `python3 scripts/run_new_tractate.py --tractate eruvin` takes —
`scripts/run_new_tractate.py` → `src/event_triage.py` (Stage 1) → `src/story_detector_v11.py`
`run_pipeline` (Stage 2, twin pass, Stage 4a–4l) — and the scoring that follows it
(`measure_recall_vs_expert_list.py`, `measure_strict_recall.py`, `board.py`,
`audit_miss_anatomy.py`). Reviewed by four parallel readers, one per segment; the P1s were
re-verified by hand before this was written.

**Verdict.** The path *runs* for Eruvin unchanged — `--tractate eruvin` is known, the Sefaria
file has the right shape (207 pages, 2a–105a, contiguous segment indexes), all 74 blind-list
stories anchor on a corpus-unique phrase, and the scorer and board need no per-tractate edit.
But three defects would put **wrong stories into the artifact**, and a fourth charges **API
failures to Detection** in the number we would quote. Fix those four before spending the run.

## Executed Stage 4 order (as the code runs it, not as HOW_IT_WORKS.md lists it)

4a `refine_boundaries_with_event_tags` → 4b `merge_cross_page_stories_v7` → 4c
`merge_cross_page_stories` (legacy) → 4d `stitch_cross_page_continuation` (LLM) → 4f
`continuation_check` (LLM) → 4g `filter_mishnah_only_stories` → 4h `snap_start_to_introducer`
→ 4i `trim_trailing_stam_segments` → 4j `filter_biblical_actor_stories` → 4k
`extract_text_spans_via_clauses` (LLM, one call per story) → 4l
`extend_start_over_opening_formula` (R-B1) → `detect_duplicate_stories`.
`src/post_processing.py` (`PostProcessor`) and `src/clause_roles.py` are **not** on this path.

## P1 — would corrupt the Eruvin artifact

1. **4c merges a mid-page story across the page break and deletes the next page's first
   story.** `merge_cross_page_stories` (`story_detector_v11.py` ~L2388) bridges
   `stories_n[-1]` to `stories_n1[0]` whenever *either* side carries a continuation flag,
   with no check that the page-1 story ends at the page's last segment (the gap rule 4d/4f
   enforce). **Measured:** `results/v11/gittin/gittin_v11.json` Gittin 36a — a one-segment
   story at seg 2 of 14 now has `spans_pages: [36a, 36b]`, `end_segment_page2: 0`, and 36b's
   own first story is gone (`stories: []`). 4c stamps no marker, so the case is only findable
   by elimination. *Fix:* require `last_story['end_segment'] == len(segments)-1`, or delete
   4c — 4b case 4 already handles the flagged seg-0 merge.

2. **Twin-pass additions are appended, not sorted, so 4b/4c pick the wrong "last" story.**
   `_merge_nonoverlapping` (~L769–790) appends second-pass and twin-pass stories; 4b and 4c
   take `stories[-1]` / `stories[0]` positionally. With the twin pass **on by default since
   2026-09-25**, Eruvin would be the first shipped artifact exposed. **Measured:** in every
   twin-pass run on disk 6–33 pages are unsorted, and in 1–3 pages per run the story that
   actually touches the page boundary is not list-last (`twin_pass/yevamot_full_twinall.json`
   3, `kiddushin_full_twinall.json` 3). The shipped `yevamot_v11.json` / `gittin_v11.json`
   (pre-twin-pass) have 0. *Fix:* sort by `start_segment` at the end of `detect_stories`,
   after `validate_story_spans`; select boundary stories by max `end_segment` / min
   `start_segment` in 4b/4c.

3. **An empty or truncated model response on both attempts is written as "no stories" with
   no error flag.** `_call_google` (~L467–503) returns `""` for no-candidates, empty-parts and
   `MAX_TOKENS`; `_call_stage2` (~L807–833) turns `""` into `None`, retries once, then
   `return []`; `_detect_with_retry` only catches *exceptions*, so `stage2_error` is never set.
   Lesson 21 in its purest form. `model_config.py`'s own comment records the symptom ("0
   candidates, 0 stories" and the run reports success); at the default setting the 2026-09-14
   measurement had 1 empty page in 20 → ~10 blank pages on 207. The no-candidates branch is
   also uncounted. **Indicated** for the Eruvin run; **measured** historically. *Fix:* after the
   second empty/unparseable response, raise (or return a sentinel) so `_detect_with_retry`
   records `stage2_error`; count the no-candidates branch.

## P2 — wrong or misleading result

4. **The recall scorer charges `stage2_error` pages to Detection.** `measure_recall_vs_expert_list.py`
   (~L268–277, 583–594) and `measure_strict_recall.py` never read `stage2_error` /
   `run_meta.stage2_errors`; a page with a failed call has `stories: []` and any expert story
   on it scores "examined, nothing proposed". With fix 3 the count of such pages *rises*, so
   this fix must land with it. *Fix:* mark rows on a failed page `call_failed`, exclude from
   both denominators, log the count.
5. **`--retriage` with `--refs` destroys the whole tractate's triage cache.**
   `run_new_tractate.py` ~L134–151: under `--retriage` `cached = {}`, `todo` is the `--refs`
   subset, and `write_cache()` dumps `cached` wholesale. Even without `--refs`, the old cache is
   gone at the first checkpoint (10 pages in). *Fix:* load the old cache and pop only the refs
   being re-triaged, or refuse the flag combination.
6. **`run_meta` does not record the configuration the project says every run must carry.**
   Missing: detector module (the `'v11'` string is a literal that overwrites `run_pipeline`'s
   own wrong `'v10'`), `TWIN_PASS` / `TWIN_TRIGGER` / `TWIN_REACH` / `SERIES_RULE`, the
   `_stage2_fingerprint` the detector already computes, git rev, `--refs` / `--retriage`,
   `triage_summary.failed`, and the detector's `truncated_responses` / `empty_responses` /
   `twin_failures` / `twin_verdicts` counters (counted, written nowhere — a twin pass whose
   calls all failed is indistinguishable from one that found nothing, Lesson 38). The shipped
   Yevamot `run_meta` has 6 keys and no twin-pass setting, so "94.1% under `TWIN_PASS=1`" is
   attributable only from a work item's prose.
7. **A page that failed after 3 retries is checkpointed as done; a resumed run never retries
   it** and does not rebuild `stage2_errors` from resumed pages, so `run_meta.stage2_errors`
   under-reports. *Fix:* in `_load_checkpoint`, drop entries carrying `stage2_error`.
8. **HTTP 429 / `RESOURCE_EXHAUSTED` is not retryable** (`RETRYABLE_STATUS` = 500/502/503/504);
   it kills the run and skips the final checkpoint write, losing up to 4 finished pages. 4k
   adds one back-to-back call per story with **no delay**, so a 207-page run with the twin
   pass is a plausible place to hit it. *Fix:* add 429 with backoff; `try/finally` around the
   checkpoint; pass `delay` into 4k.
9. **Triage and Stage 2 can run at different thinking levels and `run_meta` reports only
   Stage 2's.** `EventTriager(model_name=args.model)` omits `thinking_level=args.thinking`;
   and the argparse default is evaluated before `load_env()`. No live divergence today (`.env`
   has the level empty), but the mechanism is there.
10. **v12 is not the current register either.** `diff v11 v12` is prompt-wording-only as its
    docstring says and carries the **2026-10-07** rulings (R-C0 limit, R-C2, R-C3, R-C5, R-C6).
    It does **not** carry the **2026-10-25** reply (one event then a ruling is *not* a story,
    not borderline; an implied outcome does not count; the 65a exception). Both v11 and v12
    still say "one real event + discussion → LOW_CONFIDENCE" — R-C7 shape 2, withdrawn
    2026-10-25 — so v12 tells the model NOT_A_STORY at one line and LOW_CONFIDENCE at another
    for the same shape. The runner imports v11; CLAUDE.md calls the highest-numbered file the
    active detector; nothing in `work/` decides which runs on Eruvin. **This is a decision,
    not a bug.**
11. **4k writes a `text_span_end` on cross-page stories** — it asks where the story ends inside
    page 1's last segment while the story continues on page 2. **Measured:** 10 shipped cases
    (Yevamot 66a/96b/121b, Gittin 5b/65b/72a, Kiddushin 22b/39a/45a/49b). *Fix:* skip the end
    side when `spans_pages`.
12. **4i trims page 1's last segment off a cross-page story**, leaving a hole before the page
    break. **Measured:** Yevamot 87a and 95a in `series_rule_experiment/yevamot_B.json`.
    *Fix:* `continue` on `spans_pages`, or run 4h/4i before 4b.
13. **The biblical-actor filter matches names as bare substrings:** `'eli'` ⊂ Eliezer / Elijah;
    `'samuel'` alone demotes a story to NOT_A_STORY with no `OUT_OF_SCOPE` label (R-S1 says it
    should carry one). Fired once in shipped runs (Kiddushin 72b, correct). **Indicated** for
    Eruvin. *Fix:* whole-token match, add `'r. '` to the rabbinic signal, emit `OUT_OF_SCOPE`.
14. **Stage 1 failures never reach `project.log`** — `event_triage.py` uses `print()` for the
    API error, the parse error and `TRIAGE FAILED`; the runner's summary never calls
    `summarize_triage`, so `failed` is uncounted in the log. Cached `TRIAGE_FAILED` pages are
    never re-tried except by all-or-nothing `--retriage` (finding 5), and the Stage 2 prompt
    header never defines the `[TRIAGE_FAILED]` label it then shows.
15. **`measure_strict_recall.py` does not apply `superseded_by_rule.json`**, so `_strict.json`
    uses the raw denominator while the matches file uses the current standard; `board.py`
    prints `_strict.json` for any tractate without a ruler. STATE.md's Yevamot line (102) is
    already stale against the matches file (100). Eruvin will drift the same way after Jeff's
    first Eruvin ruling.
16. **`audit_miss_anatomy.py` hardcodes four tractates**; `--tractates eruvin` raises
    `KeyError`, and the default silently omits it.
17. **Test suite.** (a) `python3 -m pytest tests/` aborts at collection on this machine:
    `tests/test_site_data.py` imports `tests.test_bookkeeping`, and an editable install of
    another project (`_the_sacks_protocol.pth`) puts a different `tests` package first on
    `sys.path`. A `tests/__init__.py` makes pytest insert the repo root first and ends it.
    (b) `tests/test_wave4_text_spans.py::test_wave4_ship_gate` calls the live API with
    `gemini-2.0-flash` (retired) whenever `GOOGLE_API_KEY` is set — a superseded Wave 4 gate
    that costs money and fails in the regular suite. With both ignored: **410 passed**.

## P3 — cleanup (not blocking)

- `SERIES_RULE` is off, unmeasured, superseded by the twin pass, and kept alive by two tests
  and the checkpoint fingerprint; `skip_triage` deprecated parameter still in the live
  signature; `run_pipeline` returns `'version': 'v10'` and the module docstring is titled v10.
- Twin candidates are computed from real stories but merged against ranges that include
  `NOT_A_STORY` spans — a neighbour inside one is asked (wasted call) and then dropped silently.
- 4d/4f LLM failures are printed, never counted in the output (Lesson 38 shape).
- 4d/4f take `end_segment_page2` from the model with no range check against page 2.
- 4h and 4i contradict each other: `תניא` is both a start-introducer to snap to and a trailing
  marker to trim; `ההיא` prefix-matches `ההיא שעתא`. Low historical fire rate; live hazard on a
  new tractate (Lesson 15).
- `detect_duplicate_stories` records the page's own ref for same-page duplicates; nothing
  consumes the flag.
- Everything after 4g is blind to `mishnah_stories` by construction (no spans, snap, trim,
  biblical filter or dedup on withheld entries) — acceptable, but the comment CLAUDE.md
  requires is missing.
- `tests/test_cross_page_merge.py` imports **v7**, so v11's 4b (which differs by case 5) is
  unpinned. No test covers 4h, 4i, 4j, 4a, dedup, 4d/4f failure injection, or the executed
  step order.
- Runner: `--model` default is a literal that ignores `GEMINI_MODEL`; the docstring
  advertises an `--examine-all-pages` flag that does not exist; the Stage 1 summary counts
  `should_skip_page` only, not the lexical override, so the logged skip rate is wrong by a few
  pages; the triage cache records only the last `--model` used.
- Scorer: `--tractate` defaults to Ketubot so `--expert-json eruvin_2005.json` alone raises a
  misleading `ValueError`; the workflow doc shows `--golden` unconditionally (no Eruvin golden
  exists); `check_appendix_coverage.py` is Kiddushin-only and has nothing to check for Eruvin
  (all 74 entries `in_appendix: false`, no detector output exists); `stamp_superseded_recall.py`
  hardcodes four tractates; `measure_strict_recall.py` references `recall.build_index`, which
  does not exist (dead branch).
- Two Eruvin list entries carry a daf label one amud off from where the matcher finds the
  text (`eruvin_046` 53b → 54a:0–1, `eruvin_063` 67a → 67b:15–16). Recall is unaffected; the
  `MISS` log lines print the label.
- Stale pointers: `work/2026-08-30-eruvin-detection.md` `writes:` names
  `results/detection/eruvin.json`, which nothing writes (the runner writes
  `results/v11/eruvin/eruvin_v11.json`), so `board.py lanes` is grouping on a phantom path;
  `docs/capabilities/1_triage.md` cites line numbers ~450 lines stale; `new_tractate_workflow.md`
  never names `run_new_tractate.py`; `HOW_IT_WORKS.md` describes 4k as the regex path and omits
  4l and the clause step.

## What is fine

`should_skip_page` is exactly `TRIAGE_FAILED → keep; N>=1 → keep; else skip`, pinned; the
lexical override lives in `run_pipeline`, correctly wired. A triage parse failure is
`TRIAGE_FAILED`, never DELIBERATION; an API exception writes the cache and re-raises. Stage 1
and Stage 2 both checkpoint and resume; the Stage 2 fingerprint covers prompt source, twin
flags, model and thinking level, so a v11 checkpoint cannot resume into v12. The prompt
f-string is whole and `test_prompt_is_fully_substituted.py` scans the rendered prompt. The
twin pass only adds, never moves or removes; a failed twin call adds nothing. Few-shots are
Ketubot-only and deterministic. `examine_all_pages` only adds pages; untriaged renders
`UNKNOWN`. 4k cannot cut mid-word; a failed 4k call leaves spans absent and marked `skipped`.
`mishnah_stories` is read and reported apart by the scorer. The exact-anchor matcher needs no
per-tractate configuration, and `board.py` discovers Eruvin's files by convention.

## Command sequence for the Eruvin run, once the item is done

```
python3 scripts/run_new_tractate.py --tractate eruvin
python3 scripts/audit_text_spans.py --strict results/v11/eruvin/eruvin_v11.json
python3 scripts/measure_recall_vs_expert_list.py --expert-json results/expert_lists/eruvin_2005.json \
    --expert-filter recall --tractate Eruvin --detected results/v11/eruvin/eruvin_v11.json \
    --out results/recall/eruvin_jeff2005_matches.json
python3 scripts/measure_strict_recall.py --expert-json results/expert_lists/eruvin_2005.json \
    --detected results/v11/eruvin/eruvin_v11.json --tractate Eruvin --out results/recall/eruvin_strict.json
python3 scripts/board.py && python3 -m pytest tests/ -q
```
No `--golden` (none exists); do not run `stamp_superseded_recall.py` (the scorer applies the
rulings itself and Eruvin has none). The recall command reproduced the committed Yevamot
matches file field for field, so it is verified, not inferred. Run the tractate **twice**
(Lesson 43): one run cannot tell a story from the ~1-per-35-pages flip.
