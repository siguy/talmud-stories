# Claude Collaboration Guide - Talmud Story Detection

> **READ THIS FIRST**: This project has expert validation. Quality > Speed. Verify before claiming done.

---

## 🚨 CRITICAL - READ BEFORE EVERY TASK

### The One Rule
**VALIDATION UIs MUST DISPLAY TEXT** (English + Hebrew, story highlighted, ±1 segment context)
- Without text, Jeff cannot validate
- Test in browser before claiming done
- This has failed multiple times - verify it works

### Red Flags (Stop and Ask)
- [ ] About to change data structures, APIs, or models
- [ ] About to modify files not explicitly mentioned
- [ ] Claiming something works without testing it
- [ ] Making second commit to fix same bug

### Quick Verification
```bash
# Before claiming UI is done:
open v5_1_review_ui.html  # Does text display? Story highlighted?
```

---

## Project Context

**Goal**: Detect narrative stories in Talmud using LLM-based classification
**Current Version**: v5.1 (categorical classification with expert validation)
**Expert Validator**: Jeff Rubenstein (Talmud scholar)
**Success Metric**: Reduce false positive rate from 50% (v4.1) to <20% (v5.1)

**Critical Path**:
1. Build detection system → 2. Generate validation UIs → 3. Jeff validates → 4. Iterate based on feedback

---

## CRITICAL REQUIREMENTS (Never Break These)

### 1. Validation UI Must Display Text
- **WHY CRITICAL**: Jeff cannot validate stories without seeing the actual Talmud text
- **Required**: Side-by-side English translation and Hebrew/Aramaic original
- **Required**: Story segments highlighted (currently yellow background)
- **Required**: 1 segment before/after for context
- **VERIFY BEFORE CLAIMING DONE**: Open HTML file in browser, confirm text displays

### 2. Preserve Expert Feedback
- **Never** overwrite or lose Jeff's validation data
- **Never** change validation JSON structure without explicit request
- Files: `validation_results.json`, `jeff_v4_1_validation.json`

### 3. Don't Change What Wasn't Asked
- **Don't** switch API models/endpoints unless requested
- **Don't** refactor working code unless requested
- **Don't** add "improvements" beyond the specific task
- **Ask first** if unclear whether a change is in scope

### 4. Data Integrity
- JSON output files from v5.1 contain the source of truth
- Structure: `pages[].segments[]` (text) + `pages[].stories[]` (classifications)
- **Never** modify these without explicit request

---

## VERIFICATION CHECKLIST

Before claiming any task is complete:

### For UI Changes
- [ ] Open HTML file in browser (not just check code)
- [ ] Verify text displays (English + Hebrew)
- [ ] Verify story segments highlighted
- [ ] Test filtering/sorting controls
- [ ] Check one story from start/middle/end of range

### For Code Changes
- [ ] Read the actual JSON data structure first
- [ ] Trace data flow from JSON → JavaScript → Display
- [ ] Test with actual data, not assumptions
- [ ] Check edge cases (first/last segment, single-segment stories)

### For Analysis/Results
- [ ] Count matches expected totals
- [ ] Spot-check 2-3 examples manually
- [ ] Verify disqualifiers/weakeners applied correctly

---

## COMMON MISTAKES TO AVOID

### 1. "It Should Work" Without Testing
**BAD**: Add `getStoryText()` function, assume it works
**GOOD**: Add function, verify `story.page_segments` is defined, test output

### 2. Not Understanding Data Flow
**BAD**: Assume stories have segments because pages have segments
**GOOD**: Check how stories are flattened from pages, verify data copying

### 3. Scope Creep
**BAD**: User asks to run validation → I also refactor the UI "while I'm at it"
**GOOD**: Run validation, report results, ask if they want UI updates

### 4. Multiple Commits for Same Bug
**BAD**: Fix A → push → doesn't work → Fix B → push → still broken → Fix C
**GOOD**: Diagnose root cause thoroughly, verify fix works, push once

---

## TOKEN MANAGEMENT STRATEGIES

### Current Session: 77k+ tokens used (high due to mistakes requiring rework)

### Specific Token-Saving Rules:

**1. Don't Re-Read Large Files**
```bash
# BAD: Read entire 5000-line JSON file 3 times (15k tokens)
Read results/v5/ketubot_v5.1_full_validation_2-39.json
Read results/v5/ketubot_v5.1_full_validation_2-39.json  # again
Read results/v5/ketubot_v5.1_full_validation_2-39.json  # again

# GOOD: Read once with limit, or use Grep (500 tokens)
Read results/v5/ketubot_v5.1_full_validation_2-39.json limit=100
Grep "classification.*YES" results/v5/
```

**2. Verify BEFORE Committing (Not After)**
```bash
# BAD: Costs 20k+ tokens in rework
Edit file → Commit → Doesn't work → Edit again → Commit → Still broken → Edit third time

# GOOD: Costs 5k tokens total
Edit file → Test locally → Verify works → Commit once
```

**3. Use Grep/Glob Instead of Reading**
```bash
# BAD: Read 5 HTML files to find where getStoryText is defined (25k tokens)
Read v5_1_review_ui.html
Read jeff_review_v5_1.html
# ... etc

# GOOD: Grep finds it instantly (100 tokens)
Grep "function getStoryText" *.html
```

**4. Read Summaries Before Details**
```bash
# BAD: Read 620-line comprehensive email to check if UIs are mentioned (3k tokens)
Read email_to_jeff_COMPREHENSIVE.txt

# GOOD: Read READY_TO_SEND_TO_JEFF.md first (300 tokens)
Read READY_TO_SEND_TO_JEFF.md  # Lists all files
```

**5. Batch Git Operations**
```bash
# BAD: 5 separate commits for related changes
git add file1 && git commit && git push
git add file2 && git commit && git push
# ... (overhead cost: ~2k tokens)

# GOOD: Batch related changes
git add file1 file2 file3 && git commit && git push  # (overhead: ~400 tokens)
```

### Token Budget Targets

| Task Type | Target Tokens | Red Flag If Exceeds |
|-----------|---------------|---------------------|
| Generate UI | 5k | 10k |
| Run analysis | 8k | 15k |
| Fix bug | 10k | 20k |
| Create documentation | 7k | 12k |
| Full session | 40k | 80k |

**This session used 77k (nearly 2x target)** due to:
- Text display bug (3 fix iterations): ~30k wasted
- Re-reading large JSON files: ~15k wasted
- Verbose explanations: ~10k could be saved

---

## DECISION FRAMEWORK: When to Ask vs Act

### ASK FIRST:
- Changing data structures or APIs
- Adding features not explicitly requested
- Unclear if change is in scope
- Multiple valid approaches exist
- Risk of breaking existing functionality

### ACT (then report):
- Fixing obvious bugs in code I wrote
- Implementing explicitly requested changes
- Following established patterns in codebase
- Formatting/style consistency
- Documentation updates

### VERIFY THEN REPORT:
- Generated UIs → Open in browser first
- Analysis results → Spot-check examples
- Code changes → Test with real data
- Claims of "fixed" → Actually verify fix works

---

## PROJECT-SPECIFIC PATTERNS

### v5.1 System Architecture
```
Sefaria API → fetch pages with segments
    ↓
Gemini 2.0 Flash → classify each story candidate
    ↓
Output: pages[].segments[] + pages[].stories[]
    ↓
HTML Generator → flatten stories, copy segments
    ↓
Validation UI → display for expert review
```

### Data Structure Quick Reference (Memorize This)

```javascript
// ═══════════════════════════════════════════════════════════════
// JSON OUTPUT STRUCTURE (from v5.1 analysis)
// ═══════════════════════════════════════════════════════════════
{
  "tractate": "Ketubot",
  "pages": [
    {
      "ref": "Ketubot 2a",

      // TEXT IS HERE (array of segments)
      "segments": [
        {
          "index": 0,
          "english": "MISHNA: A virgin is married on Wednesday...",
          "hebrew": "בְּתוּלָה נִשֵּׂאת לַיּוֹם הָרְבִיעִי..."
        },
        // ... more segments
      ],

      // STORIES REFERENCE SEGMENTS (but don't contain text)
      "stories": [
        {
          "start_segment": 5,      // Index into segments array
          "end_segment": 6,        // Index into segments array
          "classification": "HIGH_CONFIDENCE",
          "criteria": { /* 6 criteria */ },
          "one_sentence_summary": "...",
          // NOTE: No english/hebrew text in story object!
        }
      ]
    }
  ]
}

// ═══════════════════════════════════════════════════════════════
// CRITICAL: How to Get Text for Display
// ═══════════════════════════════════════════════════════════════

// STEP 1: Flatten stories (in HTML generator)
page.stories.forEach(story => {
  allStories.push({
    ...story,
    page_ref: page.ref,
    page_segments: page.segments,  // ⚠️ MUST COPY - This is easy to forget!
    storyId: `${page.ref}_${story.start_segment}-${story.end_segment}`
  });
});

// STEP 2: Extract text (in getStoryText function)
function getStoryText(story) {
  const start = story.start_segment;
  const end = story.end_segment;
  const segments = story.page_segments || [];  // ⚠️ Will be [] if step 1 forgot to copy!

  // Show ±1 segment for context
  const contextStart = Math.max(0, start - 1);
  const contextEnd = Math.min(segments.length - 1, end + 1);

  for (let i = contextStart; i <= contextEnd; i++) {
    const seg = segments[i];
    const isStory = i >= start && i <= end;
    // Display with isStory segments highlighted
  }
}

// ═══════════════════════════════════════════════════════════════
// COMMON BUG: Forgetting to Copy Segments
// ═══════════════════════════════════════════════════════════════

// ❌ WRONG - Story has no text
allStories.push({
  ...story,
  page_ref: page.ref,
  // Missing: page_segments: page.segments
});
// Result: getStoryText() gets empty array, no text displays

// ✅ CORRECT - Story can access text
allStories.push({
  ...story,
  page_ref: page.ref,
  page_segments: page.segments  // ← This line is critical!
});
// Result: getStoryText() gets segments, text displays
```

### File Locations (Quick Reference)

**Don't re-read these, reference this table:**

| File | Purpose | Size | Read Strategy |
|------|---------|------|---------------|
| `results/v5/ketubot_v5.1_full_validation_2-39.json` | v5.1 output (pages 2-39) | 5007 lines | Use limit=100, Grep for searching |
| `results/v5/ketubot_v5.1_full_validation_40-60.json` | v5.1 output (pages 40-60) | 3000+ lines | Use limit=50, Grep for searching |
| `generate_v5_1_review_ui.py` | UI generator (general) | 400 lines | Read sections with offset |
| `generate_jeff_review_v5_1.py` | UI generator (comparison) | 450 lines | Read sections with offset |
| `email_to_jeff_COMPREHENSIVE.txt` | Full email (all details) | 620 lines | Read summary files first |
| `email_to_jeff_DIRECT.txt` | Concise email | 168 lines | OK to read fully |
| `READY_TO_SEND_TO_JEFF.md` | Status summary | 297 lines | Read this first for overview |

### File Organization
- `/tests/v5_categorical/` - v5.1 implementation
- `/results/v5/` - JSON output files
- `generate_v5_1_review_ui.py` - General UI generator
- `generate_jeff_review_v5_1.py` - Comparison UI generator
- `*.html` - Validation UIs (committed to git for GitHub Pages)

---

## LESSONS FROM SPECIFIC MISTAKES

### Mistake: Text Display Bug (3 commits to fix)

**What Happened**:
1. Generated UIs without text display (didn't notice)
2. Added `getStoryText()` function (claimed fixed, wasn't)
3. Realized `page_segments` was undefined (actually fixed)

**Should Have Done**:
1. Check existing UIs to see what features they had
2. Read JSON structure to understand data flow
3. Test in browser before claiming done
4. One commit with verified fix

**Lesson**: Critical features require verification, not assumptions

### Mistake: Rate Limiting Model Choice

**What Happened**:
- Used `gemini-2.0-flash-exp` (10 req/min hard limit)
- User identified this was the wrong model
- Should have been `gemini-2.0-flash` (higher limits)

**Should Have Done**:
- Read existing code to see what model was used
- Research rate limits before choosing experimental model
- Ask user which model to use if uncertain

**Lesson**: Don't change APIs/models without checking current usage

---

## SUCCESS PATTERNS (What Works Well)

1. **Following Direct Instructions**: "Run v5.1 on pages 40-60" → Execute exactly that
2. **Incorporating Specific Feedback**: Jeff's patterns → Implemented all 4 correctly
3. **Git Workflow**: Well-structured commits with clear messages
4. **Documentation**: Comprehensive summaries, analysis files
5. **Responding to Corrections**: When user identifies issue, fix it immediately

---

## PRE-FLIGHT CHECKLIST (Use Before Every Major Action)

### Before Generating/Modifying UIs
- [ ] Do I understand where text comes from? (page.segments, not story object)
- [ ] Will getStoryText() have access to segments? (page_segments copied during flatten?)
- [ ] Am I displaying ±1 segment context? (Not whole page, not just story)
- [ ] Will I test in browser before claiming done? (Open the HTML file)

### Before Running Analysis
- [ ] Which model am I using? (gemini-2.0-flash, NOT -exp)
- [ ] What rate limits apply? (Regular model: OK, Exp model: 10/min)
- [ ] Do I have page range correct? (2-39 vs 40-60)
- [ ] Will output file have unique name? (Not overwrite existing)

### Before Modifying Code
- [ ] Did I read the current code first? (Not assume how it works)
- [ ] Am I changing only what was requested? (No "improvements")
- [ ] Do I understand the data flow? (Can trace from input to output)
- [ ] Will this break existing functionality? (Test edge cases)

### Before Committing
- [ ] Did I test this change? (Not just wrote it)
- [ ] Is this one logical unit? (Not partial fix requiring another commit)
- [ ] Did I check git status? (Not committing junk files)
- [ ] Is commit message clear? (Explains what AND why)

### Before Claiming "Done"
- [ ] Did I verify with real data? (Not just "should work")
- [ ] Would this pass Jeff's review? (Expert validation standard)
- [ ] Did I use tokens efficiently? (Minimal re-reads, batched operations)
- [ ] Can I explain what I did in 2 sentences? (If not, too complex)

## SELF-CHECK QUESTIONS (Before Saying "Done")

1. **Did I verify this actually works?** (Not just "should work")
2. **Did I test with real data?** (Not just look at code)
3. **Did I change only what was requested?** (No scope creep)
4. **Did I break any critical requirements?** (Check list above)
5. **Can I explain the data flow?** (Not just copy/paste code)
6. **Did I use tokens efficiently?** (Minimal re-reading)
7. **Would this survive expert review?** (Jeff will see this)
8. **If this failed, would I need another commit?** (If yes, diagnose more first)

---

## WHEN IN DOUBT

**DEFAULT BEHAVIOR**:
1. Acknowledge the request
2. Explain my understanding
3. Ask for clarification if ANY uncertainty
4. Verify before claiming done
5. Report results concisely

**NEVER**:
- Assume critical features are working without testing
- Change things beyond the specific request
- Claim something is "fixed" without verification
- Make multiple commits for same bug due to insufficient diagnosis

---

## EMERGENCY CHECKLIST (If User Says "This Is Wrong")

1. **Stop and Listen**: What specifically is wrong?
2. **Verify the Issue**: Reproduce it myself
3. **Diagnose Root Cause**: Not just symptoms
4. **Propose Fix**: Share plan before implementing
5. **Verify Fix Works**: Test before committing
6. **One Commit**: Fix it properly once

---

## PROTOCOL: When User Says "There's Still a Mistake"

This happened multiple times in this session. Here's the correct response:

### Step 1: STOP and Acknowledge (Don't Defend)
```
❌ BAD: "But I added the getStoryText() function, it should work..."
✅ GOOD: "You're right. Let me investigate the actual issue."
```

### Step 2: Reproduce the Issue
- If they say "UIs don't show text" → Actually open an HTML file and check
- If they say "Wrong model" → Check what model is actually in the code
- Don't assume - verify the specific problem they're reporting

### Step 3: Diagnose Root Cause (Not Symptoms)
```
❌ BAD: "Text isn't showing → add more CSS styling"
✅ GOOD: "Text isn't showing → trace data flow → page_segments undefined → forgot to copy segments during flatten"
```

### Step 4: Propose Fix BEFORE Implementing
```
"I found the root cause: [specific issue]

Proposed fix:
1. [Change A in file X]
2. [Change B in file Y]
3. Verify by [specific test]

Should I proceed?"
```

### Step 5: Fix Once, Verify, Commit Once
- Not: Fix → push → still broken → fix again → push
- Yes: Fix thoroughly → test locally → verify → push

### Step 6: Learn and Document
- Add to this file's "Common Mistakes" section
- Update checklists to catch this earlier next time

---

## Version History

- **2026-01-25**: Initial version after multiple mistakes in session
  - Text display bug (3 commits to fix): UI generated without text → Added function but didn't work → Actually fixed by copying segments
  - Token usage: 80k+ tokens (2x target due to rework)
  - Mistakes documented: UI text exclusion, multiple fix iterations, model changes, data structure misunderstanding

---

## Metrics to Track

**This Session (2026-01-25)**:
- Tokens used: 80,310 (target: 40k, red flag: 80k) ⚠️ AT RED FLAG
- Commits: 8 total (3 for same bug) - should have been 5
- Mistakes requiring user correction: 3 major
  1. Text display missing entirely
  2. Text display "fixed" but didn't work (page_segments undefined)
  3. Model choice (experimental vs regular)

**Target for Next Session**:
- Tokens: <40k
- Commits: Minimal revisions of same code
- User corrections: 0-1 (everyone makes mistakes, but learn fast)

---

## Notes to Future Claude Sessions

**Context**:
- This project has expert validation in the loop - quality matters more than speed
- Jeff's time is valuable - validation UIs MUST be fully functional
- The v5.1 JSON files are correct - UI bugs are usually in JavaScript flattening

**Core Principles**:
1. **Verify before claiming done** - Test with real data, open in browser, trace data flow
2. **Read data structures first** - Don't assume, understand actual format
3. **One fix, done right** - Not multiple commits for same bug
4. **Stay in scope** - Don't change things not requested
5. **Use tokens wisely** - Grep > Read, limit files, batch operations

**If you only remember one thing**: Open the HTML file in a browser before saying the UI is done.
