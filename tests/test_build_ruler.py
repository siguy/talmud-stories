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
    """87.2% = 130/149, from measure_recall_vs_expert_list.py. The anchor.

    Was 143/149 = 96.0% until 2026-09-03, when every reader of an expert list moved onto
    the exact-anchor matcher. The 13 stories that left were credited by a 4-gram window up
    to 14 segments wide reaching a neighbour on the same daf; loose and strict now agree
    (docs/findings/2026-09-03-exact-matcher-cutover.md). The point of this test is that the
    ruler and the recall harness answer with the same number, whatever the number is.
    """
    _, _, _, m = built('Ketubot')
    d = m['detection']
    assert (d['found'], d['denominator']) == (130, 149), (d['found'], d['denominator'])
    assert d['recall'] == 0.872


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


def test_the_window_no_longer_credits_a_story_we_never_proposed():
    """The concrete case the exact-anchor cutover was for, kept as its regression test.

    Jeff's 81b story is at segment 9. Every run proposed segments 1-3 and 14 on that
    page and nothing at 9 -- 9% text overlap, measured by
    scripts/check_appendix_coverage.py. Until 2026-09-03 the 4-gram window credited it
    anyway and only the strict test refused; this test pinned that gap. Both now refuse,
    so it pins the fix instead -- on a case that does not depend on the aligner being
    right, which is why it was worth keeping rather than deleting.
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
    assert e['detector_proposed'] is False, 'the exact anchor must not credit it either'
    assert e['detector_proposed_strict'] is False, 'strict test must not credit it'


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


# ---------------------------------------------------------------------------
# The axes-1 vocabulary (Phase B). No round on disk speaks it yet, so these
# drive the new path with a synthetic file rather than leaving it unexercised
# until the first real round -- by which time a defect costs weeks, not minutes.
# ---------------------------------------------------------------------------
import json as _json
import tempfile


def _load_axes_round(reviews, applies_to='base'):
    """Run load_reviews() over one synthetic axes-1 file and return its verdicts."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / 'validation' / 'feedback').mkdir(parents=True)
        (root / 'validation' / 'feedback' / 'axes_round.json').write_text(_json.dumps({
            'tractate': 'Kiddushin', 'schema_version': 'axes-1',
            'detector_version': 'v10-notrim', 'applies_to': applies_to,
            'reviews': reviews}))
        old = ruler.PROJECT_ROOT
        try:
            ruler.PROJECT_ROOT = root
            out, rounds = ruler.load_reviews('Kiddushin')
        finally:
            ruler.PROJECT_ROOT = old
    return out, rounds


def test_axes_round_is_read_at_all():
    out, rounds = _load_axes_round({
        'Kiddushin 8b_14-14': {'is_story': 'yes', 'detector_version': 'v10-notrim'}})
    assert sum(rounds.values()) == 1, 'the axes-1 round was skipped entirely'
    v = out[('Kiddushin 8b', 14, 14)][0]
    assert v['verdict'] == 'correct'
    assert v['detector_version'] == 'v10-notrim', 'Lesson 36: the version must survive'
    assert v['applies_to'] == 'base'


def test_axes_rejection_names_its_own_capability():
    """The whole point: the objection is READ, not guessed from prose."""
    out, _ = _load_axes_round({
        'Kiddushin 8b_14-14': {'is_story': 'no', 'extent': 'starts_wrong', 'notes': ''}})
    v = out[('Kiddushin 8b', 14, 14)][0]
    assert v['verdict'] == 'incorrect'
    assert ruler.objection_from_axes(v['axes']) == 'boundary'
    assert ruler.classify_objection([v['note']]) == 'unclassified', (
        'the note alone is unreadable — which is exactly the range this replaces')


def test_a_story_can_carry_a_boundary_complaint():
    """`adjust`, said properly. Accepted as a story AND counted as a boundary
    objection, so it can never become a fake classification problem again."""
    out, _ = _load_axes_round({
        'Kiddushin 8b_14-14': {'is_story': 'yes', 'extent': 'ends_wrong'}})
    v = out[('Kiddushin 8b', 14, 14)][0]
    assert v['verdict'] in ruler.ACCEPTED
    assert ruler.objection_from_axes(v['axes']) == 'boundary'


def test_borderline_is_neither_accepted_nor_rejected():
    out, _ = _load_axes_round({'Kiddushin 8b_14-14': {'is_story': 'borderline'}})
    v = out[('Kiddushin 8b', 14, 14)][0]
    assert v['verdict'] == 'borderline'
    assert v['verdict'] not in ruler.ACCEPTED and v['verdict'] not in ruler.REJECTED, (
        'a contested case recorded as contested must not be silently resolved '
        'either way — that is why Jeff asked for the status')


def test_display_problem_is_not_charged_to_any_judgement_capability():
    out, _ = _load_axes_round({
        'Kiddushin 8b_14-14': {'is_story': 'no', 'display_problem': True}})
    v = out[('Kiddushin 8b', 14, 14)][0]
    assert ruler.objection_from_axes(v['axes']) == 'display', (
        'a renderer bug must not read as a story judgement (Lesson 25)')


def test_axes_with_nothing_wrong_is_a_classification_objection():
    out, _ = _load_axes_round({
        'Kiddushin 8b_14-14': {'is_story': 'no', 'extent': 'right',
                               'confidence': 'right', 'grouping': 'right'}})
    v = out[('Kiddushin 8b', 14, 14)][0]
    assert ruler.objection_from_axes(v['axes']) == 'classification', (
        '"not a story, and nothing else is wrong" is the one genuine '
        'Classification rejection')


def test_unknown_is_story_value_is_named_not_swallowed(caplog):
    """Lesson 38: a loader that goes quiet past what it does not recognise hid a
    signed 25-verdict round for eight months."""
    import logging
    with caplog.at_level(logging.WARNING):
        out, rounds = _load_axes_round({'Kiddushin 8b_14-14': {'is_story': 'maybe'}})
    assert not out and not rounds
    assert any('maybe' in r.getMessage() for r in caplog.records), (
        'the unreadable value was never named')


def test_an_axes_round_produces_no_unclassified_notes():
    """Phase C's acceptance test, in miniature: with the axes recorded, the
    unreadable-note count that sets the width of the Classification range goes
    to zero."""
    reviews = {
        'Kiddushin 8b_14-14': {'is_story': 'no', 'extent': 'starts_wrong'},
        'Kiddushin 9a_2-2': {'is_story': 'no', 'confidence': 'too_high'},
        'Kiddushin 12a_1-3': {'is_story': 'no'},
    }
    out, _ = _load_axes_round(reviews)
    kinds = [ruler.objection_from_axes(v['axes'])
             for vs in out.values() for v in vs]
    assert 'unclassified' not in kinds
    assert sorted(kinds) == ['boundary', 'classification', 'confidence']
