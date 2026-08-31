# Lesson 5 — Prompt engineering has a ceiling

**2026-03-25**

**What happened:** We tried two levels of prompt modification — aggressive (5 new disqualifiers) and light (just confidence calibration). The aggressive version caused a catastrophic regression (0.93 → 0.57). The light version still regressed (0.93 → 0.89). The remaining 26 false positives are genuine judgment calls that can't be resolved by telling the model "legal discussions aren't stories" — it already knows that. The ambiguity is in passages that have BOTH narrative and legal elements.

**Rule:** When your baseline is already 0.93, the remaining errors are the hard cases. Prompt engineering works for systematic, clear-cut errors. It doesn't work for judgment calls that require domain expertise. The next step is either fine-tuning, a different model, or acceptance.
