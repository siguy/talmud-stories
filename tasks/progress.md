# Progress: Kiddushin Run

**Saved:** 2026-03-27, pre-compact

## What's Done
- Golden Ketubot dataset complete (182 stories, 0.93 composite)
- All documentation updated (CLAUDE.md, FOR_SIMON.md, new_tractate_workflow, kiddushin_run_plan, false_positive_learning_plan, lessons.md with 9 lessons, VERSION_HISTORY)
- Boundary check experiment: concept proved (2/3 targeted), but full-pipeline was too noisy (28 FPs). Reverted. Reframed as "continuation check" (ask if a SPECIFIC story continues, not "find any story").
- Kiddushin selected as next tractate (164 pages, ~$0.25, Jeff suggested it)

## What's Next — Kiddushin Run
Follow `docs/golden/kiddushin_run_plan.md` exactly.

### Step 1: Write `scripts/run_kiddushin.py`
- Adapt from `scripts/run_ketubot_61_112.py`
- Tractate: Kiddushin, pages 2a-82b (164 pages)
- Model: gemini-3-flash-preview
- Output: `results/kiddushin/kiddushin_v7.json`
- Include Stage 4f: continuation check (new — see below)
- Load ground truth from v5.1 feedback only (Ketubot examples are cross-tractate, no contamination)
- Parameterize tractate name in output metadata

### Step 2: Implement Stage 4f continuation check
Add to `src/story_detector_v7.py` as a new method:
1. After all merge passes, find pages where last detected story has NO `continues_to_next_page` flag and is NOT already merged
2. Send LLM: story text + first 5-8 segments of next page
3. Ask: "Is the top of the next page a continuation of THIS specific story?"
4. Binary yes/no — NOT "find a story"
5. If yes: extend the story with `spans_pages` fields
- ~20-30 API calls, ~$0.03 cost

### Step 3: Run on Kiddushin
- Fetch pages from Sefaria API
- Run triage → detection → post-processing → continuation check
- Save results

### Step 4: Post-run checks (before Jeff)
- Count stories, classification distribution, triage skip rate
- Eyeball 10-15 stories
- Check continuation check results — how many found, do they look right?
- Spot-check cross-page stories

### Step 5: Generate review UI
- Adapt `validation/generators/generate_canonical_review_ui.py` for Kiddushin
- All stories in one section (first-pass, no needs_review split)

### Step 6: Prepare to send to Jeff
- Review UI HTML file
- Context email (adapt from `docs/golden/email_draft_jeff_v10_update.md`)
- Error taxonomy reference

## Key Files to Read After Compact
- `docs/golden/kiddushin_run_plan.md` — the full plan with checklists
- `docs/golden/false_positive_learning_plan.md` — FP handling checklists
- `docs/golden/new_tractate_workflow.md` — generic workflow
- `scripts/run_ketubot_61_112.py` — template for run script
- `src/story_detector_v7.py` — detector code (add continuation check here)
- `CLAUDE.md` — project config (up to date)
- `tasks/lessons.md` — 9 lessons (read before starting)

## Git State
- Branch: `claude/sefaria-talmud-story-search-Mw1Yg`
- Last commit: `6b2e471` (revised continuation check approach)
- Tags: `v10-golden-ketubot`, `pre-detector-changes`
- No unstaged changes (except this file)
