# Lesson 4 — Cost estimates should be verified before building infrastructure

**2026-03-25**

**What happened:** The brainstorm estimated $2/run for detector experiments ($100 for 50 runs). Actual cost: $0.30/run (Gemini Flash, not Claude). We built autoresearch infrastructure (program.md, run_experiment.py) for a 50-experiment loop that turned out to be both cheap enough to run impulsively and also unnecessary — the error taxonomy already told us what was wrong.

**Rule:** Before building experiment infrastructure, verify: (a) the actual cost per experiment, (b) whether you already know what to try. If you know the answer, run 2-3 targeted experiments, not 50 blind ones.
