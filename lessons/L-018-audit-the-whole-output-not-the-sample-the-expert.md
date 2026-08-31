# Lesson 18 — Audit the whole output, not the sample the expert happened to see

**2026-08-28**

Jeff reviewed 15 of 95 Kiddushin stories and flagged 8 bad trims. We
wrote the Wave 5 plan around "8 stories to fix." A full audit of every
emitted cut — cheap, no LLM, no expert — showed **104 of 189 cuts
(55%) sever a Hebrew word** and 96% land mid-clause, across all three
v10 outputs. ~100 corrupted cuts sat in the two Ketubot files nobody
had reviewed. The cross-tab was worse: of the 9 reviewed stories that
were actually trimmed, **9 were marked incorrect**; of the 6 untrimmed,
4 were correct. The feature had zero observed successes.

**Rule:** When an expert flags N instances of a defect, measure the
defect's population rate over the entire corpus before planning the
fix. Expert samples locate a bug; they never size it. Write the
structural check that counts *all* violations — it usually takes
minutes and no API budget.

**Why:** Expert review is a sparse, non-random sample (Jeff reviewed
16% of one tractate). Planning from it silently assumes the unreviewed
90% is fine. Here the plan's scope, its urgency, and its correct
sequencing were all wrong as a result.

**How to apply:** Before writing a fix plan from feedback, ask "what
fraction of all outputs has this property?" If the property is
structural — a boundary that must sit on a word edge, a field that must
parse, a ref that must resolve — it is checkable deterministically.
Build that check first, record the baseline in the script's docstring,
and make it the ship gate (`scripts/audit_text_spans.py --strict`).
See `docs/findings/2026-08-28-wave4-span-failure-audit.md`.
