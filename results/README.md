# Results — organized by detector version + golden-source

## Detector versions

The story-finder code lives in `src/story_detector_v{N}.py`. Each version's
runs live in `results/v{N}/`. **v7 is frozen.** **v8 is active development**
(Wave 1 done, Wave 2 next). Future v9 is not on the table yet.

| Dir          | What |
|--------------|------|
| `v4/`        | Historical v4 Ketubot detections. |
| `v5/`        | v5 Ketubot pages (still used as Stage-2 input by every later run). |
| `v6/`        | v6 Ketubot. |
| `v7/`        | **v7 baseline** (frozen). Also holds Sefaria + triage caches for both tractates: `ketubot_v7_*.json`, `ketubot_v9_61-112.json`, `ketubot_pages_61-112.json`, `event_triage_*.json`, `kiddushin_v7.json`, `kiddushin_pages.json`, `event_triage_kiddushin.json`. |
| `v7_fresh/`  | v7 re-run on 2026-05-18 to fight LLM drift (Lesson 11). Use this as the same-day baseline when scoring any v8 wave. |
| `v8/`        | **Active development.** Wave outputs go under `wave1/`, `wave2/`, etc. |
| `v8/wave1/`  | Wave 1 outputs: `kiddushin_v8.json`, `ketubot_v8_*.json`. |

## Golden labels — `canonical/`

The golden labels are Jeff Rubenstein's expert validations. They sit in
`canonical/` because they aren't tied to any detector version — every detector
is scored against them.

| Path | What |
|------|------|
| `canonical/ketubot_canonical.json` | **THE Ketubot golden labels** (187 entries, 164 accepted as stories; iteration 10 of corrections plus 5 additions from Jeff's blind 2005 list; tagged `v10-golden-ketubot` at 182). |
| `canonical/kiddushin_canonical.json` | **TODO** — promote `validation/feedback/kiddushin_review_2026-04-23.json` into the canonical schema so it can be scored by `evaluate_golden.py`. |
| `canonical/source_runs/` | The detector outputs that fed the golden-label corrections rounds. Formerly `results/v10/`. NOT a detector version — kept as the historical source. |

## Conventions

- One detector version per `src/story_detector_v{N}.py`. Never edit a frozen
  version in place — copy to a new file.
- Wave development inside an active version uses subdirs (`v8/wave1/`,
  `v8/wave2/`) so each wave is independently scorable.
- Cached Sefaria pages and triage results are version-agnostic in principle
  but park under the version that first generated them (`v7/`).
- Log files (`*_run.log`) are transient; not committed.
- **A run's `stories[]` is not its whole output.** Stage 4g moves Mishnah-internal
  stories to `pages[].mishnah_stories[]`, which no harness or UI reads — so a withheld
  story scores as one we never found (4 of Ketubot's 15 golden false negatives).
  Check it with `scripts/report_mishnah_filter_delta.py` before quoting a golden number.
  See `docs/findings/2026-08-30-mishnah-filter-delta.md` and Lesson 27.
