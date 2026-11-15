---
title: Septimus site card text leak, Sanhedrin 52b:4 as a regular story, and the G6 judge-prompt re-pin
capability: [publication]
tractate: []
blocked_by: []
awaiting: []
writes: [scripts/build_site_data.py, site/data/, docs/technical/septimus-story-filter.md, scripts/check_tractate_run.py, tests/test_site_data.py, tests/test_check_tractate_run.py, tests/test_claude_subset.py]
finding:
superseded_by:
---

# Septimus site card text leak, Sanhedrin 52b:4 as a regular story, and the G6 judge-prompt re-pin

**Self-contained.** A fresh session executes this with no other context.
Read [`FRAMEWORK.md`](../../FRAMEWORK.md) first, then this.

## The claim to test / the problem

Three changes Simon approved on 2026-11-13:

1. **Card text leak** ("fix it"). Some site cards show detector-internal reasoning instead of a summary, e.g.
   Sanhedrin 52b:3: *"Passage B describes a distinct historical incident involving a different court ..."*. A rough
   regex hit 71 shipped stories (indicated). Find the field and its source, measure the displayed count, fix at the
   root in `build_site_data.py` with no model calls, guard with a test.
2. **Sanhedrin 52b:4** ("just count it as a regular story"). The previous commit shipped it with `reviewed: true`
   and `included_by`. It should read like any story of an unreviewed tractate; provenance stays in
   `results/shas_run/septimus_site_decisions.json`.
3. **G6 judge-prompt pin** ("Update"). Commit d4a6674 edited `docs/STORY_RULES.md`, which the consensus judge prompt
   embeds, so its sha moved `84bfb33fd32a` -> `88e8fff62716` and any new judge run would be red at G6. Re-pin; every
   judge output on disk must stay green.

## Method

1. The site renders `summary` (`site/app.js`), taken from the exported run's `one_sentence_summary`. For every
   twin-pass addition `story_detector_v14._find_adjacent_twins` copies the twin judge's `reason` into that field.
   Build: a summary is reader-facing unless it is a `[Restored ...]` placeholder or `source == twin_pass`; otherwise
   take the same passage's (identical cells) reader-facing summary from another run; otherwise none.
2. `reviewed` is the tractate's own state; the `included_by` field is dropped from the site data.
3. `JUDGE_PROMPT_SHA` becomes the current prompt's sha; the old one moves to `EARLIER_JUDGE_PROMPT_SHAS`, accepted, so
   outputs judged under it stay green.

## How you know it worked

- Shipped cards whose summary is a twin-pass `reason`: 76 at HEAD (71 caught by the rough regex, 5 more that avoid
  its words) -> **0**. All 76 now show no summary line. 85 cards have no summary in all (the other 9 are Ketubot
  golden placeholders, unchanged).
- G6 over every unreviewed tractate, both judges: 64 green / 4 amber (the four Claude-alone rulings) before and after.

## Guardrails

No model calls. Goldens, runs and judge outputs read-only. Story count unchanged (1,784).

## Outcome

Done 2026-11-13. **Measured.**

- **Leak, cause:** one cause only — twin-pass additions (v14 `_find_adjacent_twins` writes the twin judge's `reason`
  into `one_sentence_summary`). 76 shipped cards displayed that reason (71 matched the rough regex, 5 began
  "It describes / This is a distinct ..."). After: 0. All 76 show no summary line — no reader-facing text exists for
  them in any field: the other run either has no story on those exact cells or has its own twin-pass addition there,
  and the judge `units.json` summary is copied from the same field. (Yevamot 15a:16 and Eruvin 53b:24 also carry a
  twin-pass duplicate of the same span in run 1, but the card was already built from the earlier, regular entry.)
  The rule still takes the other run's summary of an identical passage when one exists. An overlapping story was
  deliberately not used: in both such cases (Bava Metzia 85b:4, Bava Batra 30b:5) it is a wider, different passage.
  Guard: `tests/test_site_data.py::test_no_card_summary_is_pipeline_reasoning` (twin-prompt vocabulary markers plus
  the structural check that no shipped summary equals a twin-pass `reason`).
  *Why not fix the detector:* v14 is the active detector and every shipped run is on disk; the review UI relies on that
  field being non-empty. A later run could write a real summary; the site rule holds either way.
- **Sanhedrin 52b:4:** ships with the same keys as every Sanhedrin story, `reviewed: false`; the test pins that and
  that the decisions file still names Jeff and Simon.
- **G6:** `84bfb33fd32a` -> `88e8fff62716` (= `judge_labelled_spans.prompt_sha()` under
  `src/prompts/judge_register_v2.md` today); the old sha kept in `EARLIER_JUDGE_PROMPT_SHAS`. No precedent for a
  re-pin existed (the pin was introduced once, bb1f91d). Gate read-only on all 34 unreviewed tractates: 64 green /
  4 amber, identical before and after; new test pins that both shas are green.
