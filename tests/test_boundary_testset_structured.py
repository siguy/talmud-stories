"""build_boundary_testset.py reads the axes export's STRUCTURED quotes.

Finding P2-4 (docs/findings/2026-11-07-review-ui-review.md): `quote_start`,
`quote_end` and `quote_polarity` are exported by the axis review page and nothing
read them -- the harvester regex-mined `notes` only, so the first structured
boundaries Jeff ever gave (2026-09-23: 4 starts, 3 ends) were never scored.
No API calls.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location('bts', ROOT / 'scripts' / 'build_boundary_testset.py')
bts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bts)

# Two real Yevamot clauses (15a seg 12), with a third sentence after them.
SEG = ('מֵתִיב רַב מְשַׁרְשְׁיָא: מַעֲשֶׂה בְּרַבִּי עֲקִיבָא שֶׁלִּיקֵּט אֶתְרוֹג בְּאֶחָד בִּשְׁבָט, '
       'וְנָהַג בּוֹ שְׁנֵי עִשּׂוּרִין. אֶחָד כְּדִבְרֵי בֵּית שַׁמַּאי, וְאֶחָד כְּדִבְרֵי בֵּית הִלֵּל.')
SEGS = {'Yevamot 15a': {12: SEG}}


def _item(**kw):
    base = {'page_ref': 'Yevamot 15a', 'start_segment': 12, 'end_segment': 12,
            'is_story': 'yes', 'extent': 'both_wrong', 'quote': '', 'quote_polarity': None,
            'quote_start': '', 'quote_end': '', 'notes': ''}
    base.update(kw)
    return base


def test_quote_start_and_end_become_targets():
    item = _item(quote_start='מַעֲשֶׂה בְּרַבִּי עֲקִיבָא שֶׁלִּיקֵּט אֶתְרוֹג',
                 quote_end='וְנָהַג בּוֹ שְׁנֵי עִשּׂוּרִין')
    targets, unresolved = bts.targets_for_item('Yevamot 15a_12-12', item, 'r.json', SEGS)
    assert not unresolved
    by = {t['direction']: t for t in targets}
    assert set(by) == {'start', 'end'}
    assert by['start']['harvest_rule'] == 'axes_quote_start'
    assert by['end']['harvest_rule'] == 'axes_quote_end'
    assert by['start']['clause'] == 1, 'starts at the clause the quote opens'
    assert by['end']['clause'] == 1, 'ends at the clause the quote closes'
    assert all(t['quote_polarity'] == 'include' for t in targets), \
        'a START/END box names story text by construction'
    assert not any(t.get('needs_human') for t in targets)


def test_the_single_quote_uses_its_stated_polarity_and_the_extent_axis():
    # "should be cut" + ends_wrong: the end sits one clause BEFORE the quote.
    item = _item(extent='ends_wrong', quote='אֶחָד כְּדִבְרֵי בֵּית שַׁמַּאי, וְאֶחָד כְּדִבְרֵי בֵּית הִלֵּל',
                 quote_polarity='exclude')
    targets, _ = bts.targets_for_item('k', item, 'r.json', SEGS)
    assert len(targets) == 1
    t = targets[0]
    assert (t['direction'], t['quote_polarity'], t['harvest_rule']) == ('end', 'exclude', 'axes_quote')
    assert t['clause'] == 1


def test_structured_quote_wins_over_the_same_direction_in_notes():
    item = _item(extent='starts_wrong',
                 quote_start='מַעֲשֶׂה בְּרַבִּי עֲקִיבָא שֶׁלִּיקֵּט אֶתְרוֹג',
                 notes='It should start with מַעֲשֶׂה בְּרַבִּי עֲקִיבָא שֶׁלִּיקֵּט אֶתְרוֹג בְּאֶחָד')
    targets, _ = bts.targets_for_item('k', item, 'r.json', SEGS)
    assert [t['harvest_rule'] for t in targets] == ['axes_quote_start'], \
        'one boundary, stated twice, is one target'


def test_notes_still_mined_when_nothing_structured():
    item = _item(notes='It should start with מַעֲשֶׂה בְּרַבִּי עֲקִיבָא שֶׁלִּיקֵּט אֶתְרוֹג בְּאֶחָד')
    targets, _ = bts.targets_for_item('k', item, 'r.json', SEGS)
    assert [t['direction'] for t in targets] == ['start']
    assert targets[0]['harvest_rule'].endswith('_start')
