"""Expert-list parsing: the table, the comments, and the blindness flags.

Guards the ground truth NEXT/06, /07 and /08 are all built on. The failure this
exists to prevent is silent: a line-based read of Jeff's Kiddushin .doc returns
105 "stories", nine of which are his English review notes wearing whatever daf
reference happened to precede them in the flattened text. Kiddushin 81b came out
holding eleven stories. Nothing errors; the numbers are just wrong.

The strongest assertion here is the Ketubot one. The same parser, pointed at the
list whose count the project already established by other means, must return 149
-- so the table-aware reader is checked against a known answer rather than
against itself.

Run directly:  python3 -m tests.test_kiddushin_list_parse
Or via pytest: pytest tests/test_kiddushin_list_parse.py -v
"""
from __future__ import annotations

import importlib.util
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

KIDDUSHIN_DOC = ROOT / 'jeff comms/8-30-2026/kidushin.doc'
KETUBOT_DOC = ROOT / 'jeff comms/b.ketubot (1).doc'
MISSED_DOCX = ROOT / 'jeff comms/8-30-2026/Kiddushin missed stories.docx'

_spec = importlib.util.spec_from_file_location(
    'parse_kiddushin_list', ROOT / 'scripts' / 'parse_kiddushin_list.py')
parser = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(parser)


def _kiddushin():
    return parser.parse(KIDDUSHIN_DOC, 'Kiddushin', MISSED_DOCX)


def test_ketubot_still_parses_to_its_established_count():
    """The known answer. 149 is the count the recall measurement was built on."""
    stories, comments = parser.parse(KETUBOT_DOC, 'Ketubot')
    assert len(stories) == 149, f'expected 149 Ketubot stories, got {len(stories)}'
    assert comments == [], 'the Ketubot list carries no expert comments'


def test_kiddushin_story_and_comment_counts():
    stories, comments = _kiddushin()
    assert len(stories) == 95, f'expected 95 story paragraphs, got {len(stories)}'
    assert len(comments) == 10, f'expected 10 expert remarks, got {len(comments)}'
    assert sum(1 for c in comments if c['kind'] == 'word_comment') == 9
    assert sum(1 for c in comments if c['kind'] == 'notes_column') == 1


def test_no_comment_is_mistaken_for_a_story():
    """The original defect: English review notes counted as Hebrew stories."""
    stories, _ = _kiddushin()
    for s in stories:
        latin = len(re.findall(r'[A-Za-z]', s['text']))
        assert latin <= 2, f"{s['id']} looks like an English note: {s['text'][:60]}"


def test_no_daf_holds_an_implausible_number_of_stories():
    """81b showed eleven when the comments inherited its reference."""
    stories, _ = _kiddushin()
    counts = {}
    for s in stories:
        counts[s['ref']] = counts.get(s['ref'], 0) + 1
    worst = max(counts.items(), key=lambda kv: kv[1])
    assert worst[1] <= 6, f'{worst[0]} holds {worst[1]} stories'
    assert counts.get('Kiddushin 81b', 0) == 4


def test_every_comment_attaches_to_a_story():
    stories, comments = _kiddushin()
    ids = {s['id'] for s in stories}
    for c in comments:
        assert c['attached_story_id'] in ids, f"{c['id']} attaches to nothing"


def test_jeffs_own_addition_is_flagged_not_blind():
    """`hosafti--y.r.` marks the one entry he added in 2026. It cannot score recall."""
    stories, comments = _kiddushin()
    marked = [c for c in comments if c.get('marks_addition')]
    assert len(marked) == 1, f'expected one addition marker, got {len(marked)}'
    added = next(s for s in stories if s['id'] == marked[0]['added_story_id'])
    assert not added['blind'], 'an entry he added in 2026 cannot score recall'
    assert not added['in_appendix'], 'this one is his own, not from the appendix'
    assert added['vocalized'], 'the added entry was pasted from Sefaria, so it carries nikud'
    assert added['duplicate_of'], 'it duplicates the entry he already had'


def test_appendix_entries_are_flagged_and_excluded_from_recall():
    """The appendix is our own output, merged into his list. Circular -- never blind."""
    stories, _ = _kiddushin()
    appendix = [s for s in stories if s['in_appendix']]
    assert {s['ref'] for s in appendix} == {'Kiddushin 33a', 'Kiddushin 45a', 'Kiddushin 53a',
                                            'Kiddushin 71a', 'Kiddushin 81b'}
    for s in appendix:
        assert not s['blind'], f"{s['id']} is appendix-sourced and cannot be blind"
        assert s['appendix_verdict'] in ('Yes', 'Low confidence')


def test_recall_denominator_is_the_blind_unique_count():
    stories, _ = _kiddushin()
    blind = [s for s in stories if s['blind'] and not s['duplicate_of']]
    assert len(blind) == 89, f'expected 89 strictly-blind unique stories, got {len(blind)}'
    assert len([s for s in stories if not s['blind']]) == 6


def test_an_appendix_case_we_never_proposed_stays_in_the_denominator():
    """Blindness and the recall denominator are different questions.

    Four appendix cases we proposed ourselves: counting them could only flatter
    recall, so they come out. The fifth (81b) we never proposed -- Jeff found it in
    page text our review UI displayed -- so it can only count AGAINST us. Dropping
    a story we missed is what inflates recall, which is the direction that matters.
    """
    stories, _ = _kiddushin()
    appendix = {s['ref']: s for s in stories if s['in_appendix']}
    assert len(appendix) == 5

    for ref in ('Kiddushin 33a', 'Kiddushin 45a', 'Kiddushin 53a', 'Kiddushin 71a'):
        s = appendix[ref]
        assert not s['blind'], f'{ref} is appendix-sourced and cannot be blind'
        assert not s['counts_for_recall'], f'{ref} was proposed by us; it must not count'

    s = appendix['Kiddushin 81b']
    assert not s['blind'], '81b is still not blind -- we showed him the page'
    assert s['counts_for_recall'], (
        '81b was never proposed by any run, so it must stay in the denominator; '
        'excluding it inflates recall')

    counted = [x for x in stories
               if x.get('counts_for_recall', x['blind']) and not x['duplicate_of']]
    assert len(counted) == 90, f'expected a denominator of 90, got {len(counted)}'


def test_story_text_matches_an_independent_renderer():
    """Apple's textutil and this binary reader must agree, character for character.

    SKIPS off macOS. `textutil` is an Apple binary, so on Linux this raised
    FileNotFoundError and no cloud or CI session could ever get a green suite -- while
    CLAUDE.md makes a green suite the condition for stopping. A skip states the gap;
    a hard failure on every non-Mac machine trains people to ignore the suite.

    The cross-check is still real where it can run, and it is the check that caught
    Lesson 28 (textutil silently drops table columns), so it is deliberately not deleted.
    """
    if shutil.which('textutil') is None:
        pytest.skip("textutil is macOS-only; this cross-check runs on a Mac. "
                    "Run it there before trusting a change to the .doc parser.")
    stories, _ = _kiddushin()
    raw = subprocess.run(['textutil', '-convert', 'txt', '-stdout', str(KIDDUSHIN_DOC)],
                         capture_output=True, text=True, check=True).stdout
    flat = re.sub(r'\s+', ' ', raw)
    bad = [s['id'] for s in stories if re.sub(r'\s+', ' ', s['text']).strip() not in flat]
    assert not bad, f'text differs from the independent rendering: {bad}'


def test_hebrew_daf_references_resolve():
    stories, _ = _kiddushin()
    assert all(re.fullmatch(r'Kiddushin \d+[ab]', s['ref']) for s in stories)
    assert parser.parse_daf_label('ח ע"ב-ט ע"א', 'Kiddushin') == ['Kiddushin 8b', 'Kiddushin 9a']
    assert parser.parse_daf_label('כו ע"א-ע"ב', 'Kiddushin') == ['Kiddushin 26a', 'Kiddushin 26b']
    assert parser.parse_daf_label('פא ע"ב', 'Kiddushin') == ['Kiddushin 81b']


if __name__ == '__main__':
    failures = 0
    for name, fn in sorted(globals().items()):
        if not name.startswith('test_') or not callable(fn):
            continue
        try:
            fn()
            print(f'PASS  {name}')
        except AssertionError as exc:
            failures += 1
            print(f'FAIL  {name}: {exc}')
    print(f'\n{failures} failure(s)')
    sys.exit(1 if failures else 0)
