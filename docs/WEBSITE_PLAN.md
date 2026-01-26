# Talmud Story Detection Website Plan

This document defines the structure and content for the GitHub Pages site. Update this file when making changes to the website.

---

## Purpose

Create an accessible, non-technical introduction to the Talmud Story Detection project for Jewish scholars, researchers, and interested readers.

## Target Audience

- Jewish studies scholars
- Rabbis and educators
- Students of Talmud
- Digital humanities researchers
- Non-technical readers interested in the project

---

## Site Structure

```
index.html (Home)
├── Why This Matters (section)
├── The Challenge (section)
├── Our Approach (section)
├── Current Progress (section)
└── Navigation Cards
    ├── → How We Find Stories (approach.html)
    ├── → How We Validate (validation.html)
    ├── → Project History (history.html)
    └── → Try It: Review Stories (validation/ui/...)
```

---

## Page Specifications

### 1. Home Page (index.html)

**Hero Section:**
- Title: "Finding Stories in the Talmud"
- Subtitle: "Using AI to identify narrative passages across 2,711 pages of rabbinic literature"
- Visual: Simple diagram showing Talmud → AI → Identified Stories

**Why This Matters:**
- The Talmud contains hundreds of stories (aggadot) mixed with legal discussions
- Stories are scattered across 37 tractates with no index
- Scholars spend years learning to recognize narrative patterns
- Goal: Create the first comprehensive catalog of Talmud stories

**The Challenge:**
- Visual: Pie chart or simple graphic showing "Stories vs Legal Discussions"
- Not a simple search problem - stories don't have clear markers
- Same Hebrew words appear in both legal and narrative contexts
- Stories range from 2 sentences to multiple pages

**Current Progress:**
- Stats cards with current results
- Link to live validation interfaces

**Navigation Cards:**
| Card | Links To | Description |
|------|----------|-------------|
| How We Find Stories | approach.html | Our 6-criteria system explained simply |
| How We Validate | validation.html | Expert review process |
| Project History | history.html | Evolution from v1 to current |
| Review Stories | validation/ui/ | Live interfaces |

**Project Team Section:**

**Jeffrey L. Rubenstein, Ph.D.** — *Scholarship & Validation*
- Skirball Professor of Talmud and Rabbinic Literature, New York University
- One of the world's leading experts on Talmudic narratives
- Author of foundational works on Talmud stories:
  - *Talmudic Stories: Narrative Art, Composition, and Culture* (1999)
  - *The Culture of the Babylonian Talmud* (2003)
  - *Stories of the Babylonian Talmud* (2010)
  - *Rabbinic Stories* (Classics of Western Spirituality, 2002)
- His scholarship on what constitutes a Talmudic narrative directly informs our detection criteria
- Validates AI findings against decades of expertise

**Simon B.** — *Technical Development*
- Not a software engineer, but plays one on TV (with Claude Code as his co-star)
- Brought the curiosity; AI brought the code
- Proof that you don't need a CS degree to build something meaningful—just good questions and persistent debugging

**Powered By Section:**
Logos/acknowledgments for:
- **Sefaria** - "Text data provided by Sefaria, the free library of Jewish texts"
- **Google Gemini** - "AI classification powered by Google Gemini"
- **Anthropic Claude Code** - "Development assisted by Claude Code"

---

### 2. Approach Page (approach.html)

**Data Source: Sefaria**
- Acknowledgment box: "This project uses text from Sefaria.org"
- Sefaria provides free access to Jewish texts with Hebrew/English alignment
- API allows programmatic access to Talmud pages
- Link to sefaria.org

**How It Works - The Pipeline:**

Visual: 6-step horizontal flow diagram

```
[Sefaria API] → [Detect Markers] → [AI Classification] → [Apply Filters] → [Self-Check] → [Output]
```

| Step | What Happens | Plain Language |
|------|--------------|----------------|
| 1. Fetch | Get text from Sefaria API | We retrieve each Talmud page with Hebrew and English side-by-side |
| 2. Detect | Find Hebrew narrative markers | Look for words like "מעשה" (an incident) or "יומא חד" (one day) |
| 3. Classify | AI evaluates 6 criteria | Gemini checks if the passage has characters, events, causation, etc. |
| 4. Filter | Apply disqualifiers | Remove legal rulings, hypotheticals, and habitual actions |
| 5. Self-Check | Validate the classification | AI double-checks its own work with 7 validation questions |
| 6. Output | Categorize result | Label as YES, HIGH, LOW, or NOT_A_STORY |

**What Makes a Talmud Story?**

Visual flowchart showing the 6 criteria (non-technical):

1. **Named Characters** - Specific rabbis, not "someone"
2. **Multiple Events** - More than one thing happens
3. **Cause and Effect** - Events connect logically
4. **Time Passes** - Before, during, after
5. **Actually Happened** - Not hypothetical
6. **Something Changes** - Beginning differs from end

**What We Filter Out:**
- Legal rulings
- Hypothetical cases ("If someone...")
- Habitual actions ("He would always...")
- Mishnah sections

**Example: A Real Story**
Show Ketubot 62b (Rav Reḥumi) with visual highlighting

**Example: Not a Story**
Show a legal discussion that looks similar but isn't

---

### 3. Validation Page (validation.html)

**Why Human Review Matters:**
- AI is a tool, not the final word
- Expert scholars validate each finding
- We measure accuracy against expert judgment

**Our Validation Process:**
Visual: 3-step flow
1. AI identifies candidates
2. Expert reviews with Hebrew/English text
3. Feedback improves the system

**Classification System:**
Visual badges:
- YES (green) = Definite story
- HIGH (blue) = Likely story
- LOW (yellow) = Needs review

**Expert Validator:**
- Photo/headshot area
- **Jeffrey L. Rubenstein, Ph.D.**
- Skirball Professor of Talmud and Rabbinic Literature, NYU
- "Jeff's scholarship literally wrote the book on Talmud stories. His validation ensures our AI learns from the best."
- Key insight quote: "The AI was confusing attribution with characters. When it sees 'Rabbi X said that Rabbi Y said...', it thought there was a story with characters, but it's just legal attribution."
- Link to validation interfaces

---

### 4. History Page (history.html)

**Timeline visual showing evolution:**

| Version | Date | What We Learned |
|---------|------|-----------------|
| v1 | Jan 2025 | Basic detection missed many stories |
| v2 | Jan 2025 | Found multiple stories per page |
| v3 | Jan 2025 | Better text boundaries |
| v4 | Jan 2025 | Preserved Hebrew/English alignment |
| v4.1 | Jan 2025 | Expert validation revealed 50% false positives |
| v5.0 | Jan 2025 | Categorical classification (YES/HIGH/LOW) |
| v5.1 | Jan 2025 | Addressed all false positive patterns |

**Key Insight from Expert Validation:**
Quote from Jeff about attribution vs characters

**What's Next:**
- Expand beyond Ketubot to other tractates
- Build comprehensive story index
- Make findings available to scholars

---

## Visual Style Guide

**Colors:**
- Primary: #1e3a5f (deep blue - scholarly)
- Accent: #2563eb (bright blue - interactive)
- Success: #16a34a (green - YES)
- Warning: #ca8a04 (yellow - LOW)
- Background: #f8fafc (light gray)

**Typography:**
- Headings: System fonts, bold
- Body: Clean, readable, 16px minimum
- Hebrew: Include proper font support

**Icons/Visuals:**
- Use simple SVG icons or emoji
- Prefer diagrams over dense text
- Show Hebrew text examples where relevant

---

## File Locations

```
talmud-stories/
├── index.html              # Home page
├── approach.html           # How we find stories
├── validation.html         # How we validate
├── history.html            # Project evolution
└── validation/ui/          # Live review interfaces
    ├── ketubot_2-39.html
    ├── ketubot_40-60.html
    └── jeff_comparison.html
```

---

## Update Checklist

When updating the website:

- [ ] Update stats on index.html (pages analyzed, stories found)
- [ ] Update approach.html if criteria change
- [ ] Add new version to history.html timeline
- [ ] Ensure all links work
- [ ] Test on mobile

---

## Current Stats (Update with each run)

| Metric | Value | Last Updated |
|--------|-------|--------------|
| Pages Analyzed | 76 | Jan 2025 |
| Stories Found (v5.1) | 55 | Jan 2025 |
| YES Classification | 5 | Jan 2025 |
| HIGH Classification | 29 | Jan 2025 |
| LOW Classification | 21 | Jan 2025 |
| Tractates Covered | 1 (Ketubot) | Jan 2025 |
