# Lesson 29 — A blind list stops being blind when the expert merges your output into it

**2026-08-30**

Jeff's Kiddushin list has 95 stories. Five of them are cases from our own
runs, which we sent him, which he annotated `Yes` / `Low confidence`, and
which he then **merged into the list**. In the merged document they are
indistinguishable from his other 90: same column, same hand, no marker,
no date. The list still looks like a 2005 artifact.

We caught it for one reason only — the appendix he built them from
survived as a separate file in the same folder. Nothing inside the list
would ever have shown it.

Worse, the first two attempts to settle it both went wrong in *our
favour* in one direction or another. Reasoning from where the file sat
said "these are his, they count" (denominator 94, three known-hard cases
scored against us). Reasoning from a partial look at the runs said "we
never found them, so they can't be ours" — because only four of the
thirteen Kiddushin runs had been checked. The answer came from Simon
knowing what Jeff had actually been sent.

**Rule:** provenance is a property to be **tested**, not inferred from a
file's name, its creation date, or where it sits. Before quoting any
expert artifact as blind, check it against everything we have sent that
expert. If the check cannot be run, the artifact is not blind — it is
unverified.

**Why:** blindness is the whole value of the ruler. A circular entry in a
recall denominator does not announce itself; it just quietly changes the
number, and it changes it in the flattering direction as often as not.
This is Lesson 23's problem arriving through a new door: there the
corrections set had selection baked in, here the neutral set had our own
output baked in.

**How to apply:** (a) `scripts/check_appendix_coverage.py` — run it on
every new expert list before trusting it. Gittin, Yevamot and Eruvin are
still ahead of us. (b) Ask the expert to keep his appendix a separate
file, or to mark its entries. It costs him nothing and it cannot be
reconstructed afterwards — this belongs in the next email. (c) Check
*every* run, not the current one: 45a is absent from v7 and found from
Wave 1 on, so "is it in our output" has a different answer depending on
which output you look at. (d) When a provenance question moves a headline
number, say which way it moves it and who that flatters, before deciding.
