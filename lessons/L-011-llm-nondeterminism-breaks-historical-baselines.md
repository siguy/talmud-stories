# Lesson 11 — LLM nondeterminism breaks historical baselines

**2026-05-18**

**Context:** Wave 1 Ketubot regression check. The "0.9308 composite" baseline
(`docs/golden/baseline_ketubot.json`) was generated months ago from a specific
Gemini Flash run. Today, running the same v7 detector + same triage cache +
same prompts yields composite 0.858 — a 7-point swing from LLM drift alone.

**Rule:** When testing a detector change against a historical score, generate
a FRESH baseline from the unchanged code on the same day. Compare new-fresh
against old-fresh, not against the frozen JSON. The frozen JSON is only valid
as a sanity floor for the GOLDEN dataset itself, not for detector evaluation.

**Why:** The first Wave 1 check looked like a regression (-0.014 composite vs
the frozen 0.93), but apples-to-apples (v7 fresh vs v8 fresh) showed +0.06.
Trusting the frozen baseline would have killed a real improvement.

**How to apply:** Any "did this regress?" test must run BOTH versions today,
in the same window, before comparing. Cache the fresh baseline only for the
duration of the session.
