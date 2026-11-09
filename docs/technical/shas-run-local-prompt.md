# Prompt: run the story finder on one tractate, on Simon's machine

Paste into Claude Code in your local clone of `talmud-stories`. Change `Berakhot` to run another tractate.
Approved by Simon 2026-11-09 for **Berakhot only** (~$5 estimated). Every other tractate needs his OK on the re-quoted cost.

---

Run the story finder on Berakhot. Plan: docs/technical/shas-finder-plan.md. Work item: work/2026-11-08-shas-finder-run.md.

1. git fetch origin && git checkout septimus/signup-plan && git pull, then make a new branch septimus/shas-berakhot from it.
   Read CLAUDE.md, then the plan §3–§5. Never edit scripts/evaluate_golden.py or results/canonical/*. Never git stash.
2. Configuration = the most accurate measured one, which is the runner's defaults: detector module as imported by
   scripts/run_new_tractate.py (v11; v13/v14 were measured and not adopted), model gemini-3-flash-preview, thinking off,
   twin pass on (TWIN_TRIGGER=all). Check .env does NOT override GEMINI_MODEL, GEMINI_THINKING_LEVEL, TWIN_PASS or
   TWIN_TRIGGER; if it does, unset them for this run and tell me in one line. GOOGLE_API_KEY comes from .env; never print it.
3. Fetch: python3 scripts/fetch_tractate_pages.py --tractates Berakhot  (no expert list exists; "NO EXPERT DOC FOUND"
   is expected). Confirm the page count is ~126 and every amud is present.
4. Smoke test: python3 scripts/run_new_tractate.py --tractate berakhot --refs "Berakhot 3b,Berakhot 4a"
   --output results/v11/berakhot/smoke.json. Read run_meta: tokens must be non-zero with unmetered 0, stage2_errors
   empty. Estimate the full cost from the per-page tokens (look up current gemini-3-flash-preview prices on
   ai.google.dev/pricing). If the full-run estimate is over $10, STOP and tell me the number.
5. Full run: python3 scripts/run_new_tractate.py --tractate berakhot. Then require: every fetched page in the output,
   stage2_errors empty, triage_failed count 0 (re-run the same command once to resume if not).
6. Report the measured cost: total tokens by stage from run_meta.tokens × the prices, and $ per page. Write it into
   docs/technical/shas-finder-plan.md §3 as measured (keep the estimate beside it), and re-quote the other 31
   tractates (4,276 pages) from it.
7. Count stories with the ship rule (YES + HIGH_CONFIDENCE = story, BORDERLINE separate, LOW_CONFIDENCE excluded,
   mishnah_stories separate) and compare stories per page with Gittin and Yevamot. Read 3 random stories and give me
   each in one line (ref + what happens) so I can sanity-check.
8. Delete results/v11/berakhot/smoke.json, run python3 scripts/board.py and python3 -m pytest tests/ -q
   (say which failures were already failing on main), commit, push, open a draft PR "[Shas] Berakhot run, cost measured".
9. Reply in at most 5 lines: stories found, measured $ per page, re-quoted total for the rest, PR link, anything odd.
