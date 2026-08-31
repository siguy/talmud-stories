"""The Detection/Classification ruler: does it reproduce what is already established?

A ruler that disagrees with the published numbers is either a discovery or a bug, and
the only way to tell is to pin the numbers that were arrived at independently. Ketubot's
recall of 96.0% (143/149) came from `measure_recall_vs_expert_list.py`; the 86%
classification figure came from the 2026-03-17 review round. Both must come back out.

Run:  pytest tests/test_build_ruler.py -v
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

_spec = importlib.util.spec_from_file_location('build_ruler', ROOT / 'scripts' / 'build_ruler.py')
ruler = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ruler)

_cache = {}


def built(tractate):
    if tractate not in _cache:
        entries, rounds, props = ruler.build(tractate, ruler.TRACTATES[tractate])
        _cache[tractate] = (entries, rounds, props, ruler.metrics(entries, props))
    return _cache[tractate]


def test_ketubot_detection_reproduces_the_published_recall():
    """96.0% = 143/149, from measure_recall_vs_expert_list.py. The anchor."""
    _, _, _, m = built('Ketubot')
    d = m['detection']
    assert (d['found'], d['denominator']) == (143, 149), (d['found'], d['denominator'])
    assert d['recall'] == 0.96


def test_ketubot_classification_reproduces_the_published_precision():
    """The 2026-03-17 round is where the quoted 86% comes from."""
    _, _, _, m = built('Ketubot')
    r = m['classification']['per_round']['canonical_review_anonymous_2026-03-17.json']
    assert 0.86 <= r['precision_all_causes'] <= 0.89, r['precision_all_causes']
    assert r['precision_classification_only'] > r['precision_all_causes']


def test_kiddushin_classification_reproduces_the_published_precision():
    """The 2026-04-23 round is where the quoted 68% comes from."""
    _, _, _, m = built('Kiddushin')
    r = m['classification']['per_round']['kiddushin_review_2026-04-23.json']
    assert 0.66 <= r['precision_all_causes'] <= 0.69, r['precision_all_causes']


def test_every_expert_story_gets_exactly_one_entry():
    """Two of Jeff's stories inside one proposed span must not collapse into one."""
    for tractate, expected in [('Ketubot', 149), ('Kiddushin', 94)]:
        entries, _, _, _ = built(tractate)
        listed = [e for e in entries if e['expert_listed']]
        assert len(listed) == expected, f'{tractate}: {len(listed)} != {expected}'
        assert len({e['id'] for e in listed}) == len(listed), f'{tractate}: duplicate ids'


def test_every_proposal_is_represented():
    for tractate in ('Ketubot', 'Kiddushin'):
        entries, _, props, _ = built(tractate)
        linked = {tuple(s) for e in entries for s in (e['detector_span'] or [])}
        for p in props:
            assert list(p['span']) in [list(x) for x in linked], f'{tractate}: {p["span"]} orphaned'


def test_adjust_counts_as_accepted():
    """It means the story is real and the boundary is wrong -- a Boundaries failure."""
    assert 'adjust' in ruler.ACCEPTED
    assert 'reject_remove' in ruler.ACCEPTED and 'confirm_remove' in ruler.REJECTED
    assert not (ruler.ACCEPTED & ruler.REJECTED)


def test_kiddushin_recall_excludes_only_the_appendix_cases_we_proposed():
    """Circularity is only dangerous in the direction that flatters.

    Four appendix cases are in Jeff's list because we proposed them; counting them
    could only raise recall, so they stay out. The fifth (81b) we never proposed --
    he found it in page text our review UI displayed -- so it can only count against
    us, and leaving it out is what inflates the number. Denominator 90, not 89.
    """
    entries, _, _, m = built('Kiddushin')
    assert m['detection']['denominator'] == 90, m['detection']['denominator']

    listed = [e for e in entries if e['expert_listed']]
    counted = [e for e in listed if e['expert_blind']]
    assert len(counted) == 90, len(counted)

    # 81b counts, and is still not strictly blind: both must hold at once.
    b81 = [e for e in listed if e['ref'] == 'Kiddushin 81b' and e.get('not_blind_reason')]
    assert b81, 'the appendix 81b entry should carry a not-blind reason'
    assert all(e['expert_blind'] for e in b81), '81b must count toward recall'
    assert all(e['expert_strictly_blind'] is False for e in b81), '81b is not blind'


def test_the_loose_window_credits_a_story_we_never_proposed():
    """The concrete case that shows the loose recall figure is an upper bound.

    Jeff's 81b story is at segment 9. Every run proposed segments 1-3 and 14 on that
    page and nothing at 9 -- 9% text overlap, measured by
    scripts/check_appendix_coverage.py. The loose window credits it anyway; the
    strict test does not. This pins the gap to a case that does not depend on the
    aligner being right.
    """
    entries, _, _, _ = built('Kiddushin')
    # built() returns the in-memory structure, where cells are tuples; the written
    # JSON has them as lists. Compare in a shape-independent way.
    cells = lambda e: [tuple(c) for c in (e.get('expert_segments') or [])]
    hits = [e for e in entries
            if e['ref'] == 'Kiddushin 81b' and e.get('not_blind_reason')
            and cells(e) == [('Kiddushin 81b', 9)]]
    assert hits, 'expected the appendix 81b entry, localised to segment 9'
    e = hits[0]
    assert e['detector_proposed'] is True, 'loose window credits it'
    assert e['detector_proposed_strict'] is False, 'strict test must not credit it'


def test_every_story_localises_to_at_least_one_segment():
    """An empty tight set silently falls back to the loose window and fakes a strict hit."""
    for tractate in ('Ketubot', 'Kiddushin'):
        entries, _, _, _ = built(tractate)
        bad = [e['id'] for e in entries if e['expert_listed'] and not e.get('expert_segments')]
        assert not bad, f'{tractate}: unlocalised {bad}'


def test_hand_sort_rows_all_point_at_a_verdict_the_ruler_scores():
    """A dangling row is a sort that has drifted off the data it claims to read.

    Round files get renamed and spans get re-keyed. When that happens the row stops
    applying and the note silently reverts to `unclassified` -- the range widens again
    and nothing says so. docs/findings/2026-08-31-objection-axis-hand-sort.md
    """
    assert ruler.HAND_SORT, 'results/rulers/objection_axes.json did not load'
    scored = set()
    for tractate in ('Ketubot', 'Kiddushin'):
        _, _, props, _ = built(tractate)
        scored |= {(v['round'], v['key']) for p in props for v in p['verdicts']
                   if v['verdict'] in ruler.REJECTED}
    dangling = sorted(set(ruler.HAND_SORT) - scored)
    assert not dangling, f'hand-sorted rows the ruler no longer scores: {dangling}'
    assert len(ruler.HAND_SORT) == 34, len(ruler.HAND_SORT)


def test_the_residue_is_exactly_the_empty_notes():
    """The finding's central claim: every note with text in it was readable.

    If a future row files a non-empty note as `unresolvable`, that is a judgment call
    being hidden in the residue bucket -- which is the failure FRAMEWORK sec.7 names.
    """
    AXES = {'classification', 'boundary', 'confidence', 'merge',
            'display', 'not_an_objection', 'unresolvable'}
    for key, row in ruler.HAND_SORT.items():
        assert row['axis'] in AXES, f'{key}: unknown axis {row["axis"]!r}'
        if row['axis'] == 'unresolvable':
            assert not row['note'].strip(), f'{key}: filed unresolvable but has a note'
        else:
            assert row['note'].strip(), f'{key}: sorted onto {row["axis"]} with no note'
    empty = [k for k, r in ruler.HAND_SORT.items() if r['axis'] == 'unresolvable']
    assert len(empty) == 7, len(empty)


def test_reading_notes_never_moves_the_lower_bound():
    """precision_all_causes counts every rejection whatever it objected to.

    It is definitional, so no reading of the notes may change it. Only the upper bound
    and the residue are allowed to move; the two rounds below are the ones that did.
    """
    _, _, _, ket = built('Ketubot')
    _, _, _, kid = built('Kiddushin')
    v5 = ket['classification']['per_round']['v5_1_feedback_anonymous_2026-02-05 (1).json']
    k4 = kid['classification']['per_round']['kiddushin_review_2026-04-23.json']
    assert v5['precision_all_causes'] == 0.667, v5['precision_all_causes']
    assert k4['precision_all_causes'] == 0.674, k4['precision_all_causes']
    # ... and the upper bounds these notes pulled down, from 1.000 and 0.921.
    assert v5['precision_classification_only'] == 0.806, v5['precision_classification_only']
    assert k4['precision_classification_only'] == 0.899, k4['precision_classification_only']
    assert v5['unclassified_notes'] == 0 and k4['unclassified_notes'] == 0


def test_the_only_residue_left_is_the_v8_delta_round():
    """34 notes named no axis; 7 do. All 7 are in one round, and all 7 are empty."""
    _, _, _, ket = built('Ketubot')
    _, _, _, kid = built('Kiddushin')
    left = {name: r['unclassified_notes']
            for m in (ket, kid) for name, r in m['classification']['per_round'].items()
            if r['unclassified_notes']}
    assert left == {'v8_delta_feedback_anonymous_2026-02-26.json': 7}, left


def test_strict_recall_is_a_subset_of_loose_recall():
    for tractate in ('Ketubot', 'Kiddushin'):
        entries, _, _, m = built(tractate)
        for e in entries:
            if e.get('detector_proposed_strict'):
                assert e['detector_proposed'], f"{tractate}: {e['id']} strict but not loose"
        assert m['detection']['recall_strict'] <= m['detection']['recall']


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
