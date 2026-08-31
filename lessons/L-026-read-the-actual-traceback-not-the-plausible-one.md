# Lesson 26 — Read the actual traceback, not the plausible one

**2026-08-30**

`pytest tests/` had been unrunnable: 4 collection errors aborted the whole
suite, so **nothing ran at all** — including 16 tests that were fine.

The handed-down diagnosis said all four failed on
`ModuleNotFoundError: No module named 'find_talmud_stories'`, and proposed
fixing the import. Two of the four did. The other two —
`test_categorical_classification_v5.1.py` and `_v5.2.py` — failed with
`No module named 'test_categorical_classification_v5'`: a module name that
**has never existed anywhere in this repo**. The cause is the dot in the
filename. Python reads `..._v5.1` as package `..._v5`, submodule `1`, so
the file is unimportable *by name alone*. Repairing the import would have
changed nothing; the version number in the filename was the bug.

Two further claims in the brief were also wrong on inspection:
`results/ketubot/v5/pages_2-39.json` was described as gone and untracked —
it is at `results/v5/pages_2-39.json` and **is** tracked by git. And the
defect was wider than reported: `tests/test_event_triage.py` carried the
same stale path but had never appeared in any failure list, because
collection aborted before it could run.

**Rule:** when a report names an error, reproduce it and read the
traceback yourself before planning the fix. A stated error message is a
claim about the code, not evidence.

**Why:** every one of the three corrections above was visible in the first
15 seconds of `pytest -q` and `ls`. Acting on the summary would have
produced a fix that repaired two files, left two still erroring, and never
touched the third stale path at all.

**How to apply:** (a) Run the failing command first; diff what it actually
says against what you were told it says. (b) Treat `ModuleNotFoundError`
naming a module you cannot find *anywhere* as a signal about the importing
filename, not the imported one — pytest's "make sure your test modules have
valid Python names" hint says exactly this. (c) After fixing what was
reported, grep the whole repo for the same defect: this one had **12 live
call sites**. The 5 in `src/story_detector_v{7,8,9,10,11}.py::main()` are
still stale as of this writing — each detector's CLI entrypoint will raise
`FileNotFoundError` if run directly. Not fixed here: this session's scope
was the test suite, and those are unverified by any test.
