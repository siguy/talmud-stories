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


def test_kiddushin_uses_only_blind_entries_for_recall():
    """The appendix entries are our own output; they cannot score Detection."""
    entries, _, _, m = built('Kiddushin')
    assert m['detection']['denominator'] == 89, m['detection']['denominator']
    assert all(e['expert_blind'] for e in entries
               if e['expert_listed'] and e['expert_blind'] is not False) is True


def test_every_story_localises_to_at_least_one_segment():
    """An empty tight set silently falls back to the loose window and fakes a strict hit."""
    for tractate in ('Ketubot', 'Kiddushin'):
        entries, _, _, _ = built(tractate)
        bad = [e['id'] for e in entries if e['expert_listed'] and not e.get('expert_segments')]
        assert not bad, f'{tractate}: unlocalised {bad}'


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
