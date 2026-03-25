# Brainstorm: Golden Dataset + Generalization Strategy

**Date:** 2026-03-25
**Status:** Active
**Participants:** Simon, Claude

---

## What We're Building

A "golden" Ketubot dataset that incorporates ALL of Jeff Rubenstein's expert feedback — not just classification corrections but boundary adjustments and merges too. Then, a self-improvement loop (based on Karpathy's autoresearch pattern) that uses this golden dataset to autonomously improve the story detector for other tractates.

## Why This Approach

### The Problem We Discovered

Our `build_canonical.py` has been systematically applying only the **classification half** of Jeff's feedback and ignoring **boundary/merge corrections** stated in the same notes. Jeff has now repeated himself on at least 10 stories. This is the #1 issue.

### The Numbers

From `docs/golden/canonical_feedback_analysis.json`:
- **187** stories reviewed by Jeff
- **53** need changes (28% error rate)
- **15** auto-applicable (classification changes only)
- **38** need manual/tooled work (boundaries + merges)
- **10** are issues Jeff flagged before that we never fully addressed

### Error Pattern Breakdown

| Pattern | Count | Description |
|---------|-------|-------------|
| NONE | 134 | Correct, no changes needed |
| MERGE_NEEDED | 17 | Stories need to be combined |
| LEGAL_FALSE_POSITIVE | 11 | Legal discussion misidentified as story |
| BOUNDARY_UNDEREXTENSION | 10 | Story starts/ends beyond detected range |
| CONFIDENCE_MISCALIBRATION | 9 | Wrong confidence level |
| BOUNDARY_OVEREXTENSION | 5 | Talmud commentary included in story |
| MERGE_INCORRECT | 1 | Cross-page merge has wrong segments |

## Key Decisions

### 1. Schema Design: Sub-segment Precision from Day 1

Design the golden dataset schema to support character-level boundary markers within segments, even though we'll implement segment-level corrections first. This means each story has:
- `start_segment` / `end_segment` (segment-level, implement now)
- `start_text_marker` / `end_text_marker` (Hebrew text boundaries, implement later)
- These are Jeff's actual Hebrew phrases that mark where stories begin/end

### 2. Boundary Correction Tooling

Build a script that:
1. Takes Jeff's Hebrew text markers from the analysis JSON
2. Searches segment text to find which segment contains that text
3. Proposes segment-level boundary adjustments
4. For sub-segment cases, records the character offset for future use

Uses the Sefaria MCP tools to look up actual text when needed.

### 3. Autoresearch Loop for Generalization

Apply Karpathy's autoresearch pattern:
- **`prepare.py` (immutable):** Jeff's golden labels + eval script producing composite score
- **`train.py` (mutable):** Detection prompts, criteria weights, boundary rules
- **Metric:** Composite of classification F1 + boundary IoU + merge accuracy
- **Loop:** Modify prompt → run detector on labeled pages → score → keep/revert

### 4. Generalization Lessons as Few-Shot Examples

Convert Jeff's corrections into structured few-shot examples organized by error pattern. The detector can use these to avoid the same mistakes on new tractates.

## Open Questions

1. **How do we score boundary precision?** Segment-level IoU seems right, but Jeff sometimes says "the last sentence shouldn't be included" which is sub-segment. For now: segment-level IoU, with a penalty for including Talmud meta-commentary.

2. **How many autoresearch experiments can we run?** Each full Ketubot run is ~100 API calls. At ~$2/run, overnight we could do ~50 experiments for ~$100. Worth discussing budget.

3. **Which tractate next?** After Ketubot is golden, which tractate should we generalize to first? Ideally one where we have some informal validation from Jeff.

4. **Should we build a persistent boundary refinement UI?** The current review UI shows text + boundaries. Could add inline editing so Jeff can drag boundaries directly. Would produce perfect sub-segment data.

## What We Could Also Explore

1. **Structural markers for boundary detection** — Talmud meta-commentary often starts with specific Aramaic phrases (הֵיכִי, מַאי, questions starting with interrogative words). These could be automatically detected.

2. **Passage pattern classification** — Jeff's corrections cluster by passage type (legal-with-setting, extended-narrative, etc.). A pre-classification step could route passages to specialized prompts.

3. **Cross-tractate ground truth** — Even without Jeff's full review, we could use his Ketubot patterns to generate synthetic labels for other tractates and self-validate.

---

**Next:** Run `/workflows:plan` to produce the implementation plan.
