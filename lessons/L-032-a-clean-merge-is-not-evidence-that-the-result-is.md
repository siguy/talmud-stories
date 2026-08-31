# Lesson 32 — A clean merge is not evidence that the result is correct

**2026-08-31**

Git compares text. It knows nothing about whether the text still means what it did. Two
instances on 2026-08-30, both verified:

**1. The collision was invisible *because* the names differed.** Two sessions each wrote a
brief numbered `09` and one numbered `10`, for four different jobs. Because the slugs
differed, the *filenames* differed — so git saw four unrelated files, merged them all
cleanly, and warned about nothing. A conflict would have stopped somebody. A clean merge
did not. Both pairs are recorded in `work/README.md`'s redirect table, which is the only
reason a citation of "NEXT/09" can still be resolved.

**2. A clean rebase, a stale artifact.** `results/rulers/ketubot_ruler.json` was derived
from the 182-entry golden. Trunk grew the golden to 187 and never touched
`results/rulers/`, so the branch would have rebased with **zero conflicts** while the
ruler's `in_golden` flags stayed wrong for the five highest-value entries in the corpus —
the blind-list stories that were the whole point of the addition. Caught before the merge
and fixed at the source by `e4fbd13`, which made the ruler read `in_golden` from the
golden rather than from the proposals linked to a story.

A third, smaller version of the same error: reading `git diff <trunk>..<branch>` for a
branch that forked earlier makes every commit trunk gained look like a **deletion** by the
branch. "Never had it" and "deleted it" render identically. Check `merge-base` before
reading a diff as intent.

**Rule:** git guarantees textual consistency, never derivational consistency. After any
merge or rebase that touches a source of truth, **regenerate everything derived from it
and diff** — the absence of conflicts is not a reason to skip that, it is the reason the
problem is invisible.

**Why:** every failure mode here is silent by construction. Two sessions in separate
worktrees cannot see each other, and the merge that joins them reports success in exactly
the cases where nobody has checked the meaning. This repo runs several concurrent sessions
as a matter of course, so this is the normal condition, not an edge case.

**How to apply:**
(a) **Record what a derived artifact was derived from** — the git SHA of the golden, list
or run that produced it — so staleness is checkable rather than remembered.
(b) **Prefer fixing the derivation to regenerating the output.** `e4fbd13` is the better
shape: reading `in_golden` from the golden means the artifact cannot go stale again.
(c) **When two files can collide in meaning but not in name, that is what a test is for.**
`tests/test_bookkeeping.py::test_lesson_numbers_are_unique_across_every_local_ref` reads
*all* local refs, because the four-way Lesson 26 collision was invisible from inside any
single worktree.
(d) Dated slugs (`work/`, `lessons/`) remove the naming half of this. They do not touch
the derived-data half, which needs (a) and (b).
