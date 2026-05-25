# Results — organized by detector version

Every subdir corresponds to a detector version. Files inside are named with the
tractate and page range. Triage and Sefaria page caches live in the version dir
they were first generated in.

| Dir          | Contents |
|--------------|----------|
| `canonical/` | Golden labels (`ketubot_canonical.json`) — IMMUTABLE. |
| `v4/`        | Historical v4 Ketubot detections. |
| `v5/`        | v5 Ketubot pages (used as Stage-2 input by every later run). |
| `v6/`        | v6 Ketubot detection. |
| `v7/`        | v7 baseline. Also holds Sefaria + triage caches for Ketubot and Kiddushin (kiddushin_pages.json, event_triage_*.json). |
| `v7_fresh/`  | v7 re-run on 2026-05-18 to establish a same-day baseline for Wave 1 (LLM drift compensation — see Lesson 11). |
| `v8/`        | Wave 1 fixes from Jeff's 2026-04-23 Kiddushin review. |
| `v10/`       | Experimental branch — reverted, kept for reference. |

## Conventions

- Detector versions live in `src/story_detector_v{N}.py`. Each version gets its
  own output dir under `results/v{N}/`. Never edit a canonical detector file
  in place — copy to a new version (Lesson re-noted in memory).
- Cached Sefaria pages and triage results are version-agnostic in principle,
  but in practice they're parked under the version that first created them.
- Log files (`*_run.log`) are transient and not committed.
