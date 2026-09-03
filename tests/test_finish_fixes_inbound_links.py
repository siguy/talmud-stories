"""
Finishing an item must not break links POINTING AT it.

`board.py finish` re-roots the links *inside* the moved item, and
`test_the_closing_step_re_roots_links_so_finishing_cannot_break_them` covers that
thoroughly. Both were blind to the other direction: every link elsewhere in the repo that
points at `work/<slug>.md` breaks when the item moves to `work/done/`.

The suite therefore asserted a property it did not have — in a docstring that said
"finishing cannot break them". That is Lesson 31 at one remove: the guard *was* built by
simulating the failure it guards, but only one direction of it, and the untested direction
is the one that fired. Observed 2026-08-31, twice in one session:

  - finishing two items broke both of their rows in `work/README.md`'s redirect table
  - two new findings linked to the pre-move paths and the suite did NOT catch it, because
    the link checker walks tracked files and those findings were still untracked

→ docs/findings/2026-08-31-finish-fixes-inbound-links.md
"""

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def load_board():
    spec = importlib.util.spec_from_file_location("board", ROOT / "scripts" / "board.py")
    board = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(board)
    return board


# --- the rewrite itself, in isolation ----------------------------------------

@pytest.mark.parametrize('linking_file,before,after', [
    # from work/README.md — sibling reference, gains the done/ segment
    ('work/README.md', '[x](2026-01-01-demo.md)', '[x](done/2026-01-01-demo.md)'),
    # from the repo root — the path gains done/ in the middle
    ('STATUS.md', '[x](work/2026-01-01-demo.md)', '[x](work/done/2026-01-01-demo.md)'),
    # from one level down — same, with the ../ preserved
    ('docs/findings/f.md', '[x](../../work/2026-01-01-demo.md)',
     '[x](../../work/done/2026-01-01-demo.md)'),
    # from an ALREADY-finished item — it wrote `../<slug>.md` while the target was
    # still open, which was correct then. Once the target closes they are siblings and
    # the `../` is what breaks. This case was missing until 2026-09-02 and broke a link
    # on three consecutive finishes in one session; the same defect as Lesson 31,
    # surviving in the one direction nobody checked.
    ('work/done/other.md', '[x](../2026-01-01-demo.md)', '[x](2026-01-01-demo.md)'),
    # ...and one already correct is left alone
    ('work/done/other.md', '[x](2026-01-01-demo.md)', '[x](2026-01-01-demo.md)'),
    # ...and one already pointing into done/ is not double-rewritten
    ('work/done/other.md', '[x](../done/2026-01-01-demo.md)',
     '[x](../done/2026-01-01-demo.md)'),
])
def test_inbound_links_are_rewritten_for_the_linking_file(linking_file, before, after):
    board = load_board()
    assert board.reroot_inbound(before, linking_file, '2026-01-01-demo') == after


def test_a_link_to_a_different_item_is_untouched():
    board = load_board()
    text = '[a](work/2026-01-01-other.md) and [b](work/2026-01-01-demo.md)'
    out = board.reroot_inbound(text, 'STATUS.md', '2026-01-01-demo')
    assert '](work/2026-01-01-other.md)' in out, "only the finished slug may move"
    assert '](work/done/2026-01-01-demo.md)' in out


def test_the_rewrite_is_idempotent():
    """A second `finish` pass, or a re-run, must not produce work/done/done/."""
    board = load_board()
    once = board.reroot_inbound('[x](work/2026-01-01-demo.md)', 'STATUS.md', '2026-01-01-demo')
    assert board.reroot_inbound(once, 'STATUS.md', '2026-01-01-demo') == once
    assert 'done/done' not in once


# --- end to end: finish an item that something links to ----------------------

def test_finishing_an_item_leaves_inbound_links_resolving(tmp_path):
    """
    The whole failure, reproduced: create an item, link to it from two files at
    different depths, finish it, and require every link to still resolve.
    """
    board = load_board()
    slug = 'zz-scratch-inbound-guard'
    item = ROOT / 'work' / f'{slug}.md'
    root_linker = ROOT / f'ZZ_SCRATCH_{slug}.md'
    deep_linker = ROOT / 'docs' / 'findings' / f'ZZ_SCRATCH_{slug}.md'
    created = [item, root_linker, deep_linker]
    try:
        item.write_text('---\ntitle: scratch\ncapability: []\ntractate: []\n'
                        'blocked_by: []\nawaiting: []\nfinding:\nsuperseded_by:\n---\n\n'
                        '# scratch\n\n## Outcome\n\nScratch item for a test.\n')
        root_linker.write_text(f'[item](work/{slug}.md)\n')
        deep_linker.write_text(f'[item](../../work/{slug}.md)\n')

        board.finish(slug)

        for linker in (root_linker, deep_linker):
            text = linker.read_text()
            link = text.split('](')[1].split(')')[0]
            target = (linker.parent / link).resolve()
            assert target.exists(), f"{linker.name} -> {link} does not resolve"
            assert 'done' in link, f"{linker.name} was not rewritten: {link}"
    finally:
        for f in created + [ROOT / 'work' / 'done' / f'{slug}.md']:
            if f.exists():
                f.unlink()
        # Regenerate rather than `git checkout` the generated files: checkout restores
        # the COMMITTED board, which reverts any legitimate regeneration done earlier in
        # the session and makes `--check` report stale. Caught by this very suite.
        subprocess.run([sys.executable, 'scripts/board.py'], cwd=ROOT, capture_output=True)


def test_the_link_checker_sees_untracked_files():
    """
    The second, sneakier instance: two findings linked to pre-move paths and the suite
    stayed green because they were untracked. A guard whose coverage depends on git state
    is not a guard you can rely on the moment it matters most — right after you write a
    file (Lesson 38).
    """
    import test_bookkeeping
    probe = ROOT / 'ZZ_SCRATCH_untracked_link_probe.md'
    try:
        probe.write_text('[nope](does/not/exist/at/all.md)\n')
        assert probe in test_bookkeeping.tracked('*.md'), (
            "an untracked, non-ignored markdown file is invisible to the link checker, "
            "so its broken links stay green until it is committed")
        with pytest.raises(AssertionError):
            test_bookkeeping.test_no_markdown_link_is_broken()
    finally:
        probe.unlink(missing_ok=True)


# --- links OUT of the moved item, to a sibling -------------------------------
#
# `reroot_links` handled `](../x)` and nothing else. An item that cites a sibling item —
# the normal way to write "the rest of this is that item's territory" — broke that link at
# the moment of finishing, while `finish`'s docstring claimed links "run BOTH ways and both
# are handled". Lesson 31's shape a third time, and the same overclaim the module docstring
# above was written about. Caught 2026-09-01 by the link checker, on the first item ever to
# link a sibling.

@pytest.mark.parametrize('before,after', [
    # out of work/ entirely — the only case the old implementation handled
    ('[a](../FRAMEWORK.md)',              '[a](../../FRAMEWORK.md)'),
    ('[a](../docs/findings/f.md)',        '[a](../../docs/findings/f.md)'),
    ('[a](../../FRAMEWORK.md)',           '[a](../../FRAMEWORK.md)'),
    # a still-open sibling: one level up once we are inside work/done/
    ('[a](2026-09-01-other-item.md)',     '[a](../2026-09-01-other-item.md)'),
    # an already-finished sibling: `done/` is our own directory now
    ('[a](done/2026-08-30-old.md)',       '[a](2026-08-30-old.md)'),
    # not links into the tree at all
    ('[a](https://example.com/z.md)',     '[a](https://example.com/z.md)'),
    ('[a](#a-section)',                   '[a](#a-section)'),
])
def test_outbound_links_are_rerooted_for_every_shape(before, after):
    assert load_board().reroot_links(before) == after


def test_the_sibling_and_done_rules_do_not_compose():
    """
    Written as sequential `re.sub` calls, the `done/` rule strips the prefix and the
    bare-sibling rule then re-adds `../` to its own output — each rule correct alone,
    wrong together. Every link must be considered exactly once.
    """
    assert load_board().reroot_links('[a](done/x.md)') == '[a](x.md)'


def test_a_real_item_body_survives_the_move_intact():
    """All four link shapes in one document, as an actual item writes them."""
    body = (
        "Read [`FRAMEWORK.md`](../FRAMEWORK.md) first.\n"
        "That is [`other`](2026-09-01-other-item.md)'s territory.\n"
        "See [`old`](done/2026-08-30-old.md) and the\n"
        "[finding](../docs/findings/2026-09-01-x.md).\n"
    )
    got = load_board().reroot_links(body)
    assert "](../../FRAMEWORK.md)" in got
    assert "](../2026-09-01-other-item.md)" in got
    assert "](2026-08-30-old.md)" in got
    assert "](../../docs/findings/2026-09-01-x.md)" in got


@pytest.mark.parametrize('before,after', [
    # Items link to data and code, not only to markdown. Restricting the `../` rule to
    # .md silently stopped re-rooting these — a regression caught the same day by
    # test_every_open_item_would_survive_being_closed, not by the cases above.
    ('[a](../results/expert_lists/kiddushin_2005.json)',
     '[a](../../results/expert_lists/kiddushin_2005.json)'),
    ('[a](../scripts/board.py)', '[a](../../scripts/board.py)'),
    ('[a](../lessons/)',         '[a](../../lessons/)'),
])
def test_non_markdown_links_are_rerooted_too(before, after):
    assert load_board().reroot_links(before) == after


@pytest.mark.parametrize('link', ['[a](#a-section)', '[a](#top)'])
def test_a_same_page_anchor_is_never_rerooted(link):
    """
    Anchors became reachable by the rewrite only when the pattern stopped excluding `#`
    — which it had to, so that `../results/x.json` kept being re-rooted. Widening a
    pattern re-opens every case the old exclusion was quietly covering.
    """
    assert load_board().reroot_links(link) == link


def test_a_sibling_link_carrying_an_anchor_still_moves():
    assert load_board().reroot_links('[a](2026-09-01-x.md#outcome)') \
        == '[a](../2026-09-01-x.md#outcome)'
