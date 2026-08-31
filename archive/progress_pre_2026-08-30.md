# Progress: Kiddushin Run

**Saved:** 2026-03-27, post-run

## What's Done

### Previously
- Golden Ketubot dataset complete (182 stories, 0.93 composite)
- All documentation updated
- Boundary check experiment reverted, reframed as "continuation check"
- Kiddushin selected as next tractate (Jeff suggested it)

### This Session — Steps 1-5 COMPLETE
- [x] Step 1: Wrote `scripts/run_kiddushin.py` (adapted from run_ketubot_61_112.py)
- [x] Step 2: Implemented Stage 4f continuation check in `src/story_detector_v7.py`
  - New method `continuation_check()` — fires for last story on each page near boundary
  - Conservative prompt: requires same characters, same situation, direct continuation
  - Wired into `run_pipeline()` after stage 4d stitch
  - Also parameterized `tractate` in `run_pipeline()` (was hardcoded 'Ketubot')
- [x] Step 3: Ran on Kiddushin 2a-82b — completed successfully
- [x] Step 4: Post-run spot checks — all look good
- [x] Step 5: Generated review UI — verified in browser

### Results
- **162 pages** fetched (2a-82b)
- **109 skipped** by triage (67% skip rate — slightly higher than Ketubot's ~60%)
- **53 pages** processed
- **96 stories** detected (higher than predicted 65-80)
  - YES: 34
  - HIGH_CONFIDENCE: 16
  - LOW_CONFIDENCE: 46
  - NOT_A_STORY: 5
- **12 cross-page stories** detected:
  - 5 via merge (continuation flags)
  - 4 via stitch (targeted LLM)
  - **3 via continuation check (4f)** — NEW, working!
    - Kiddushin 29b→30a (Rav Huna/Rav Hamnuna)
    - Kiddushin 31a→31b (Dama ben Netina — famous story)
    - Kiddushin 81b→82a (actions for sake of Heaven)

### Files Created
- `scripts/run_kiddushin.py` — run script
- `results/kiddushin/kiddushin_v7.json` — detection results
- `results/kiddushin/event_triage_kiddushin.json` — triage results
- `results/kiddushin/kiddushin_pages.json` — cached Sefaria pages
- `validation/generators/generate_kiddushin_review_ui.py` — review UI generator
- `validation/ui/kiddushin_review.html` — review UI for Jeff

### Files Modified
- `src/story_detector_v7.py` — added `continuation_check()` method, `tractate` param in `run_pipeline()`

## What's Next
- [x] Write context email for Jeff — `docs/golden/email_draft_jeff_kiddushin.md`
- [ ] Commit all changes
- [ ] Send Jeff: review UI HTML + email + error taxonomy reference
- [ ] After Jeff reviews: score, analyze FPs, build golden dataset (see kiddushin_run_plan.md)
