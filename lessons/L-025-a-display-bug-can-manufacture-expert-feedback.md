# Lesson 25 — A display bug can manufacture expert feedback

**2026-08-30**

The review UI trimmed the Hebrew at the detector's character offsets and
showed the full English beside it. Reviewers therefore saw a Hebrew
passage that stopped early next to an English one that did not.

Cost, measured: **2 of the 15 verdicts** in Jeff Rubenstein's 2026-07-06
round were spent on our renderer rather than on the detector. One of them
— Kiddushin 8b seg 14, *"English right but Hebrew cut off; continues to
seg 0 of next page"* — was filed in the ledger under **cross-page merge
defects and sat there for seven weeks.** The detector had merged it
correctly the whole time (`spans_pages: ['Kiddushin 8b', 'Kiddushin 9a']`,
`continues_to_next_page: true`). Only the UI dropped the Hebrew.

A second asymmetry nobody had recorded: cross-page stories emitted a block
titled "English (continued)" with **no Hebrew counterpart at all** — 35
stories across the three outputs.

**Rule:** an expert's attention is the scarcest resource in this project.
Before any review round, render the real artifact, look at it, and check
that every language shows the same extent of the same text. A UI defect
does not merely waste that attention — it enters the record as a *finding*
and misdirects work for as long as nobody re-reads it.

**Why:** we already had the rule "open validation UIs in a browser before
calling them done". It was not followed, and the cost was not the bug —
it was seven weeks of a false entry on the defect list, and an expert's
goodwill spent describing our own rendering to us.

**How to apply:** (a) Render both languages from **one** code path, so
emitting one without the other is structurally impossible rather than
merely avoided. (b) Prefer **highlighting** a proposed span inside the
full text over **trimming** to it — highlighting states the judgment
without hiding the evidence a reviewer needs to judge it. (c) When an
expert reports something that sounds like a display problem, check the
renderer *before* filing it against the detector.
(d) Guard it with a test that executes the page's real display code, and
confirm the test fails when the bug is reintroduced — see
`tests/test_review_ui_symmetry.py`.
