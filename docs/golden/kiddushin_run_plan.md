# Kiddushin Run Plan

**Created:** 2026-03-27
**Tractate:** Kiddushin (Betrothal/Marriage)
**Pages:** 2a–82b (164 pages, 82 dapim)
**Estimated cost:** ~$0.25
**Estimated time:** ~7 min

---

## What We're Testing

1. **Does the detector generalize?** Ketubot composite was 0.93. Target: 0.85+ on Kiddushin.
2. **Do the false positive patterns generalize?** Are Kiddushin's FPs the same type (legal discussions with narrative framing)?
3. **Do cross-tractate few-shots help?** Ketubot FP examples will be in the prompt — first clean test without contamination.
4. **Are boundaries accurate on a new tractate?** Ketubot IoU was 0.98. Does that hold?
5. **Does cross-page merge detection work?** Ketubot Merge F1 was 0.86. Same quality on new pagination?

---

## Pre-Run Checklist

### From false_positive_learning_plan.md:
- [ ] Few-shot examples come from Ketubot only (automatic — no Kiddushin feedback exists)
- [ ] Abstract pattern descriptions from error taxonomy are in the prompt (verify in Stage 2 prompt)

### Boundary and merge readiness:
- [ ] Verify Stage 4 boundary refinement is tractate-agnostic (it is — no hardcoded refs in `refine_boundaries_with_event_tags`)
- [ ] Verify cross-page merge uses page adjacency, not hardcoded page lists (it does — iterates `pages[i]` and `pages[i+1]`)
- [ ] Verify cross-page stitching handles Kiddushin page refs (format: "Kiddushin 2a", "Kiddushin 2b", etc.)
- [ ] Parameterize the tractate name in the output metadata (line 645 in story_detector_v7.py says 'Ketubot')

### Script readiness:
- [ ] Write `scripts/run_kiddushin.py` adapting from `run_ketubot_61_112.py`
- [ ] Test that Sefaria API returns Kiddushin pages correctly (spot-check 1 page)

---

## Run Steps

### 1. Fetch pages from Sefaria
Pages 2a through 82b. Cache locally to avoid re-fetching.

### 2. Event triage (Stage 1)
Classify every segment. Skip pages with < 2 NARRATIVE_EVENT.
**Track:** Skip rate. Ketubot was ~60%. Kiddushin should be similar (same seder/legal domain).

### 3. Story detection (Stage 2)
Run on kept pages with:
- Ketubot-trained Ground Truth DB few-shot examples (cross-tractate, no contamination)
- Full 6-criteria classification
- Cross-page context (previous/next page segments)

### 4. Post-processing (Stage 4)
- **Boundary refinement:** Trim story boundaries using event type annotations
- **Cross-page merge (v7):** Detect fragments at page boundaries with narrative events on both sides
- **Cross-page merge (continuation flags):** Merge stories with continues_to/continues_from flags
- **Cross-page stitching:** Extend stories to include undetected continuation text at page tops
- **Duplicate detection:** Flag stories quoted on multiple pages

### 5. Save results
To `results/kiddushin/kiddushin_v7.json`

---

## Post-Run Checks (Before Sending to Jeff)

### Story count and distribution:
- [ ] Total stories detected (expect 65-80 based on Ketubot ratio)
- [ ] Classification distribution: YES / HIGH / LOW / NOT_A_STORY
- [ ] Triage skip rate (expect ~60%)

### Boundary spot-check:
- [ ] Read 10 stories — do boundaries look right? Do stories start at narrative events and end when the arc resolves?
- [ ] Check for OVEREXTENSION pattern: does any story include Talmud analytical commentary (הֵיכִי, מַאי questions) at the end?
- [ ] Check for UNDEREXTENSION: are there obvious story beginnings that got cut off?

### Cross-page merge spot-check:
- [ ] How many cross-page stories detected? (Ketubot: 19 out of ~180)
- [ ] Read 3-5 cross-page stories — do the merged segments make sense?
- [ ] Are there obvious page-boundary stories that DIDN'T get merged?

### False positive spot-check:
- [ ] Read 10 LOW_CONFIDENCE stories — are any clearly legal discussions with narrative settings?
- [ ] Compare to Ketubot error taxonomy patterns — do the same types appear?

---

## Review UI Generation

Adapt `validation/generators/generate_canonical_review_ui.py` for Kiddushin:
- Change input path to `results/kiddushin/kiddushin_v7.json`
- Change output path to `validation/ui/kiddushin_review.html`
- All stories in one section (no needs_review/auto-applied split — this is first-pass detection)
- Verdict options: Correct / Incorrect with notes field
- **Must show:** English + Hebrew text, story highlighted, classification, confidence
- **Must show for cross-page stories:** Both pages' text with merge indicator
- **Notes field must prompt for:** boundary issues, merge issues, classification disagreements

---

## What to Send Jeff

### The review UI (HTML file)
All detected stories, classified by confidence. Jeff can open in any browser.

### Context email covering:
1. **What we did:** "Ran the same detector we used on Ketubot, now on Kiddushin"
2. **What we expect:** "~85% correct based on Ketubot. ~15% are likely legal discussions with narrative framing"
3. **What to watch for** (from error taxonomy):
   - Legal discussions where all 'events' are verbal acts (asking, objecting, ruling)
   - Hypothetical scenarios that describe what COULD happen
   - Narrative settings followed by legal debate
   - Stories that should start earlier or end sooner (boundary issues)
   - Stories that continue across page boundaries (merge issues)
4. **What's most helpful:** "For each story, tell us: correct/incorrect + notes. For boundary issues, note where the story should start/end. For merges, note if two stories should be combined or if a merge has wrong segments."
5. **Scope:** "Review as many as you can — even 30 stories gives us solid data. Prioritize the ones you're uncertain about."

### Link to error taxonomy
`docs/golden/error_taxonomy.md` — Jeff's own language, so he'll recognize the patterns.

---

## After Jeff Reviews

### Scoring:
- [ ] Run `evaluate_golden.py` with Jeff's labels
- [ ] Record: Classification F1, Boundary IoU, Merge F1, Composite
- [ ] Compare to Ketubot baseline (F1=0.92, IoU=0.98, Merge=0.86, Composite=0.93)

### False positive analysis:
- [ ] Count FPs, group by confidence level
- [ ] Classify each FP by error pattern (from taxonomy)
- [ ] Compare FP rate to Ketubot (14%)
- [ ] New patterns? → Update error taxonomy
- [ ] Store in `docs/golden/fp_analysis_kiddushin.md`

### Boundary analysis:
- [ ] Mean IoU for Kiddushin vs Ketubot (0.98)
- [ ] Count OVEREXTENSION and UNDEREXTENSION errors
- [ ] Any Kiddushin-specific boundary patterns?

### Merge analysis:
- [ ] Merge precision/recall vs Ketubot (0.86 F1)
- [ ] Missed merges — what page patterns?
- [ ] Wrong merges — what went wrong?

### Decision gates:
- [ ] If composite ≥ 0.85: detector generalizes → proceed to more tractates
- [ ] If composite < 0.75: detector may be Ketubot-specific → investigate why
- [ ] If total labeled examples ≥ 200: evaluate fine-tuning option (see false_positive_learning_plan.md, Tier 3)
- [ ] Update all documentation with findings

---

## Cross-Page Merge: Current State and Potential Improvement

### Current approach (v9)
The detector processes one Talmud page at a time. It includes the last 5 segments of the
previous page and first 5 of the next page as READ-ONLY context, but tells the LLM to
only detect stories on THIS page, then set continuation flags. Stage 4 merges stories
across pages using those flags + a targeted LLM "stitch" pass.

**Performance:** 16/19 cross-page merges detected (86%). The 3 misses happen when the
LLM doesn't set continuation flags during per-page detection — Stage 4 has no signal to
merge on. This is an architectural limitation, not a bug.

### Why this matters
Every version (v1–v9) uses page-by-page processing. The cross-page problem was always
solved via post-processing. We've never tried changing the input windowing.

### Potential improvement: Sliding segment windows
Sefaria gives us segments individually. The page boundary (5a vs 5b) is an arbitrary
printing artifact. Instead of "analyze page 5a with context from 5b," we could give the
LLM overlapping windows of segments that cross page boundaries:

```
Window 1: 5a all segments + 5b segments 0-5
Window 2: 5b all segments + 6a segments 0-5
```

A story at the 5a/5b boundary would fall INSIDE a window — detected as a single unit,
no merge logic needed.

**Tradeoffs:**
- Pro: Eliminates 14% merge miss rate for boundary stories
- Pro: No dependence on LLM setting continuation flags correctly
- Con: ~25% more tokens per window (overlapping segments analyzed twice)
- Con: Need deduplication for stories detected in multiple windows
- Con: Triage (Stage 1) currently works per-page, would need rethinking
- Cost impact: Negligible (~$0.07 more per tractate)

**Status:** Not yet tested. Could be a good experiment for Kiddushin if the standard
page-by-page run shows the same ~14% merge miss rate. Would require modifying
`story_detector_v7.py`'s `run_pipeline()` to use segment windows instead of pages.

**Decision:** Run Kiddushin with the current page-by-page approach first. Measure merge
accuracy. If merge misses are a significant issue, implement sliding windows as a follow-up.

---

## Files This Run Will Create

| File | Purpose |
|---|---|
| `scripts/run_kiddushin.py` | Run script for Kiddushin |
| `results/kiddushin/kiddushin_v7.json` | Detection results |
| `results/kiddushin/event_triage_kiddushin.json` | Triage results |
| `results/kiddushin/kiddushin_pages.json` | Cached Sefaria pages |
| `validation/ui/kiddushin_review.html` | Review UI for Jeff |
| `docs/golden/fp_analysis_kiddushin.md` | False positive analysis (after Jeff review) |
| `docs/golden/baseline_kiddushin.json` | Evaluation scores (after Jeff review) |
