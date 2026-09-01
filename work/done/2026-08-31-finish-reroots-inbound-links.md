---
title: Finishing an item re-roots its outbound links and breaks every inbound one
capability: []
tractate: []
blocked_by: []
awaiting: []
finding:
superseded_by:
---

# Finishing an item re-roots its outbound links and breaks every inbound one

**Self-contained.** A fresh session executes this with no other context.
Read [`FRAMEWORK.md`](../../FRAMEWORK.md) first, then this.
**Cross-cutting** — bookkeeping, not a capability.
**Depends on Jeff: no. Cost: under an hour, no API calls.**

## The problem, and why it is more interesting than it looks

`python3 scripts/board.py finish <slug>` moves an item to `work/done/` and re-roots the
links **inside** it, because one level deeper every `../` breaks. That half works, is
tested, and the test is a good one.

It does nothing about links **pointing at** the item from elsewhere. Those break instead.

**The guard already exists and is one-directional.** `tests/test_bookkeeping.py` has
`test_the_closing_step_re_roots_links_so_finishing_cannot_break_them` — its docstring says
*"finishing cannot break them"* — and `test_every_open_item_would_survive_being_closed`.
Both check only links **from** the moved file. So the suite asserts a property it does not
have, in a docstring that overclaims.

That makes this Lesson 31 at one remove: the guard *was* verified by simulating the failure
it guards — but only one direction of that failure, and the untested direction is the one
that fires.

## Observed 2026-08-31

Finishing `2026-08-30-triage-recall-price` and `2026-08-30-kiddushin-comments-harvest`
broke both of their rows in `work/README.md` — a redirect table mapping the retired
`tasks/NEXT/NN` numbers to current slugs. `test_no_markdown_link_is_broken` then failed on
grounds unrelated to the work just completed, and both rows were fixed by hand into the
`done/<slug>.md` form the table already uses for finished items.

A second, sneakier instance the same day: two brand-new findings in `docs/findings/` linked
to the items at their pre-move paths. **The suite did not catch it**, because the link
checker walks tracked files and both findings were still untracked. They failed only after
being committed — i.e. the guard's coverage depends on git state, which is worth
establishing deliberately rather than discovering.

## Method

1. **Write the failing test first** and watch it fail: create a scratch item, link to it
   from a second file, finish it, assert the link still resolves.
2. **Fix `board.py`'s finish path** to rewrite inbound links repo-wide after the `git mv`,
   adjusting each for the linking file's own directory (a link from `work/README.md` and
   one from `docs/findings/x.md` need different rewrites).
3. **Share one path-rewriting helper.** Inbound fix-up is the inverse of the re-rooting
   `finish` already does; two independent implementations of the same arithmetic will drift.
4. **Correct the overclaiming docstring** and extend both existing tests to cover the
   inbound direction, so the suite stops asserting a property it does not have.
5. **Decide what the link checker should do about untracked files** and record the reason.
   Scanning them would have caught the findings before the commit; it may also produce
   noise on scratch files. Either answer is defensible; silently depending on git state is
   not.

## How you know it worked

- Finishing an item that is linked from `work/README.md`, `STATUS.md` and a
  `docs/findings/` file leaves all three resolving.
- A test exists that fails when the inbound fix-up is removed — **demonstrated, not
  assumed**.
- `python3 -m pytest tests/ -q` passes (was 107 passed / 1 skipped on 2026-08-31), and
  passes **immediately after** a `finish`, with no hand-editing.
- `work/README.md`'s redirect table is correct for every finished item.

## Guardrails

- **Never delete a finished item** to make a link resolve. The `work/done/` record is the
  answer to "what has already been done"; that is the whole point of the layout.
- `STATE.md` and `WORK.md` are generated — never hand-edit them; run `scripts/board.py`.
- Rewriting links repo-wide touches a lot of files. Do it in its own commit, and diff the
  result before committing rather than trusting the rewrite.
- Do not rewrite links inside `work/done/` items to point at their own new location in a
  way that changes what a **historical** record says. A finished item is a permanent
  record; fixing a path is fine, editing its claims is not.

## When done

Write the finding to `docs/findings/<date>-<slug>.md`, add an `## Outcome` section
below, then `python3 scripts/board.py finish <slug>`. **This item finishing is its own
acceptance test** — if closing it breaks a link, it is not done.

## Outcome

**Fixed 2026-08-31.** → [`docs/findings/2026-08-31-finish-fixes-inbound-links.md`](../../docs/findings/2026-08-31-finish-fixes-inbound-links.md)

`reroot_inbound()` + `fix_inbound_links()` in `board.py`, called by `finish` after the
move; they share the same one-segment rewrite as the outbound path rather than
re-implementing the arithmetic. Idempotent, correct from any depth.

**The two decisions the item asked to be made deliberately:**

1. **`tracked()` now includes untracked-but-not-ignored files.** `--exclude-standard`
   keeps scratch and generated artifacts out, so the added set is exactly the files about
   to be committed. This widens every guard in `test_bookkeeping.py`, not just the link
   checker. The alternative — leaving coverage dependent on git state — makes the guard
   weakest right after a file is written, which is when it is needed.
2. **The overclaiming test was renamed, not deleted**, to
   `test_the_closing_step_re_roots_the_moved_item_s_own_links`, with a note naming the
   direction it covers and where the other lives. The overclaim stays visible in history.

**One of my own new tests passed vacuously** and had to be rewritten: it asserted against
the wrong function body, because the file enumeration lives in a `tracked()` helper rather
than inline in the checker. Caught only by asking *why* it passed when the other six
failed. Rewritten behaviourally — plant an untracked file with a broken link, require the
checker to catch it.

Suite 107 → **121 passed, 1 skipped**. **Closing this item is its own acceptance test.**
