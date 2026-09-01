# Lesson — A dependency graph is not a contention graph

**2026-08-31**

`work/` items have always declared `blocked_by`: what must finish before this can start.
Nothing declared what an item *writes*. Those are different graphs, and only one of them
existed — so two items with no dependency between them were shown as concurrently
runnable by `STATE.md`, `WORK.md` and `STATUS.md` alike, whether or not they wrote the
same file.

Measured when the second graph was finally computed: **31 open items, 15 lanes.** 39
colliding pairs over 11 contended paths. Six items write `src/story_detector_v11.py`.
Six must bump the same `GOLDEN_COUNTS` dict. And four of the colliding pairs were items
`STATUS.md` recommended *in the same paragraph* as the cheapest next steps —
`golden-completeness` and `kiddushin-comments-harvest` both rewrite
`results/canonical/kiddushin_canonical.json`.

**Rule:** ordering and contention are two graphs. If a board tells you what can start,
it is answering the ordering question, and you must not read it as an answer to the
concurrency question. Declare the write-set.

**Why:** the ordering graph is about correctness of *sequence* and gets attention because
a wrong answer parks work visibly. The contention graph is about correctness of *result*,
and a wrong answer there is silent — Lesson 32's whole subject. Nobody notices the graph
that was never drawn.

**Corollary, and the part that surprised:** the *guaranteed* collision had nothing to do
with the work. Every item that is opened, finished or edited changes the generated board,
so three sessions each opening one unrelated item produced two conflicting merges, five
conflict markers committed into `WORK.md`, and a trunk on which `board.py --check`
failed. Bookkeeping collided harder than data did, and it collided for no information:
the correct content of a generated file is never a blend of two sides.

**How to apply:**
(a) **Declare `writes:` generously.** Over-declaring costs a serialized lane;
under-declaring costs a silent corruption. They are not symmetric, so when unsure,
declare it.
(b) **Run `python3 scripts/board.py lanes` before handing work to concurrent sessions.**
The lane count, not the unblocked-item count, is how many sessions the work supports.
(c) **A generated file is regenerated, never merged.** `.gitattributes` routes it to a
driver that reruns the generator; `.githooks/post-merge` produces the truth afterwards,
because a merge driver runs before the other side's files exist on disk.
(d) **A shared constant is a contention edge.** `GOLDEN_COUNTS` is a hardcoded dict in a
300-line test module, and it forces every golden-growing item into one lane. That may be
the right trade — it is a deliberate guard — but it should be a *chosen* one.
