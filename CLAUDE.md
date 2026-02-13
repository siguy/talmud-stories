# Claude.md - Talmud Story Detection

## Project
Detect narrative stories in Talmud text using LLM classification. Expert validation by Jeff Rubenstein.

## Critical Rule
**Validation UIs must display text** (English + Hebrew, story highlighted). Test in browser before claiming done.

## Data Structure
```
pages[].segments[] → contains english/hebrew text
pages[].stories[] → references segments by index (NO text)

When flattening stories, MUST copy: page_segments: page.segments
```

## Testing Requirements
1. **Always verify changes work** - don't assume
2. **Open HTML files in browser** - not just check code
3. **Test with real data** - trace actual values, not expected values
4. **Check edge cases** - first/last segments, single-segment stories
5. **One thorough fix** - not multiple commits for same bug

## Before Claiming Done
- [ ] Tested with real data (not assumptions)
- [ ] Opened in browser (for UIs)
- [ ] Changed only what was requested
- [ ] Can explain in 2 sentences

## Token Efficiency
- Use Grep/Glob instead of reading full files
- Use `limit` parameter for large files
- Verify before committing (rework is expensive)
- Batch related git operations

## When User Reports Issue
1. Acknowledge (don't defend)
2. Reproduce it yourself
3. Find root cause (not symptoms)
4. Propose fix, get approval
5. Fix once, verify, commit

## Don't
- Change APIs/models without asking
- Add "improvements" beyond request
- Claim "fixed" without testing
- Re-read large files multiple times

## Documentation Requirements
When making changes, update these files:
- `docs/technical/VERSION_HISTORY.md` - New versions, results, patterns
- `docs/technical/HOW_IT_WORKS.md` - Pipeline changes, criteria updates
- `docs/technical/REVIEW_INTERFACE.md` - UI features, file locations
- `README.md` - Results tables, quick start if paths change

## Project Structure
```
src/                          # Core detection code
results/v6/                   # Current v6 analysis output
results/ketubot/v5/           # Historical v5.1 analysis output
validation/ui/                # HTML validation interfaces
validation/generators/        # Scripts to generate UIs
validation/feedback/          # Expert feedback JSONs
docs/                         # All documentation
tests/                        # Tests (v6 regression, v5 categorical)
archive/                      # Old versions (reference only)
```

## Key Files
| File | Purpose |
|------|---------|
| `src/story_detector_v6.py` | Current detection script (v6) |
| `src/story_detector_v5.py` | Previous detection script (v5.1) |
| `results/v6/` | v6 analysis output |
| `results/ketubot/v5/pages_*.json` | v5.1 analysis output |
| `validation/generators/generate_review_ui.py` | UI generator |
| `validation/ui/ketubot_*.html` | Validation UIs |
| `validation/feedback/v5_1_feedback_*.json` | Jeff's v5.1 feedback |
