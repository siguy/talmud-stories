# Finishing an item now fixes links in both directions

**Date:** 2026-08-31
**Capability:** — (cross-cutting bookkeeping)
**Status:** fixed, guarded
**Item:** [`work/2026-08-31-finish-reroots-inbound-links.md`](../../work/done/2026-08-31-finish-reroots-inbound-links.md)

---

## The defect, and why the guard did not catch it

`board.py finish` re-rooted the links **inside** a moved item and ignored every link
**pointing at** it. Closing an item therefore broke references to it — on 2026-08-31, two
rows in `work/README.md`'s redirect table, twice in one session.

The interesting part is that a guard existed and was one-directional:
`test_the_closing_step_re_roots_links_so_finishing_cannot_break_them` checked only links
*from* the moved file, while its **name** promised finishing could not break links at all.
**The suite asserted a property the repo did not have.**

That is Lesson 31 at one remove. The guard *was* built by simulating the failure it
guards — the right instinct, done once — but only one direction of that failure, and the
untested direction is the one that fired. A guard is only as good as the failure you
imagined when writing it.

## A second instance, quieter

Two findings written the same session linked to the pre-move paths, and **the suite stayed
green**: `test_no_markdown_link_is_broken` enumerated files with `git ls-files`, and both
findings were still untracked. They failed only after `git add`.

A guard whose coverage depends on git state is weakest exactly when it matters most —
right after you write a file (Lesson 38: absence is quiet).

## The fix

**`reroot_inbound(text, linking_file, slug)`** — the inverse of the existing
`reroot_links`. Only the `work/` → `work/done/` segment moves; whatever prefix got the
linker there is preserved, so the rewrite is correct from any depth:

| linking file | before | after |
|---|---|---|
| `work/README.md` | `](2026-01-01-demo.md)` | `](done/2026-01-01-demo.md)` |
| `STATUS.md` | `](work/2026-01-01-demo.md)` | `](work/done/2026-01-01-demo.md)` |
| `docs/findings/f.md` | `](../../work/2026-01-01-demo.md)` | `](../../work/done/2026-01-01-demo.md)` |

Idempotent — a path already containing `work/done/` is skipped, so a re-run cannot produce
`done/done`. `finish` calls `fix_inbound_links(slug)` after the move and prints what it
repointed.

**`tracked()` now includes untracked-but-not-ignored files.** `--exclude-standard`
respects `.gitignore`, so scratch and generated artifacts stay out; the added set is
precisely the files you are about to commit. This widens *every* guard in
`test_bookkeeping.py`, not only the link checker.

**The overclaiming test was renamed** to
`test_the_closing_step_re_roots_the_moved_item_s_own_links`, with a note saying which
direction it covers and where the other lives. Renaming rather than deleting keeps the
overclaim visible in history.

## Verified

- 7 tests in `tests/test_finish_fixes_inbound_links.py`, written first and watched fail.
  Six failed for the right reason; the seventh **passed vacuously** — it asserted against
  the wrong function body, since the enumeration lives in a `tracked()` helper rather than
  inline. Rewritten as a behavioural test that plants an untracked file with a broken link
  and requires the checker to catch it.
- End-to-end: create an item, link it from two files at different depths, `finish` it,
  require every link to still resolve.
- Full suite **121 passed, 1 skipped** (was 107 / 1).
- **This item's own closing is the acceptance test.** It is linked from `STATUS.md` and
  from this finding; if closing it breaks a link, the fix does not work.

## Bounds

- Handles markdown `](...)` links. Bare paths in prose and links inside code fences are
  not rewritten — deliberately: rewriting a path inside an example command would corrupt
  the example.
- Rewrites only the exact finished slug. An item referred to by title rather than path
  still goes stale, and nothing detects that.
- The scan is repo-wide on each finish. Cheap at this size; if `work/done/` grows large it
  is a linear cost per closure, not a problem yet.
