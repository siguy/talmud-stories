#!/usr/bin/env python3
"""Project every banked review verdict onto the verdict-axes shape.

Phase B of `work/2026-08-30-review-verdict-axes.md`. The new review UI records which
capability an objection indicts (`validation/generators/generate_verdict_axes_review_ui.py`).
Nine rounds of verdicts already exist in four older vocabularies, and a new shape that
cannot read them starts the ledger over.

WHAT THIS IS NOT
----------------
It is not a way to recover information the old rounds never captured. Where a legacy
verdict underdetermines an axis, the axis is `None` and the axis name is listed in
`undetermined`. Guessing it into a bucket to make the coverage look complete is the
failure FRAMEWORK sec.7 names, and it is how the 86/68 numbers survived. Two coarser
values exist for exactly this reason and the new UI never emits them:

    wrong_unspecified   the reviewer said this axis is wrong but the old vocabulary had
                        no way to say how ("shrink"; `adjust`)
    None + undetermined the old vocabulary could not express the question at all

FOUR VOCABULARIES, NOT THREE
----------------------------
The brief expected three. There are four, and the extra one is the oldest:

  A. `axes_2026_01`  -- the FIRST review UI, 2026-01-08, and it already had axes:
     `feedback_type` (correct / false_positive), `length_adjustment` (shrink),
     `story_confidence` (75-95), `story_type`, `spans_multiple_pages`. The project then
     replaced it with a single word and spent seven months unable to tell a boundary
     complaint from a classification one. **10 of its 25 entries carry a `shrink` --
     boundary corrections that no harness has ever read**, because `build_ruler.py` looks
     for a `reviews`/`feedback` dict and this file's `feedback` is a list.
  B. `base_pair`      -- correct / incorrect / confirm_remove / reject_remove, on BASE
     detector output (v4.1, v5.1 x2, v8-delta, both Kiddushin rounds, Wave 4).
  C. `canonical_corrected` -- correct / incorrect / approve / adjust, on ALREADY-CORRECTED
     data (2026-03-17). Lesson 3's trap lives here: a `correct` on corrected data is not
     a `correct` on base data, and merging the two lets this round's "the correction was
     right" silently overturn the earlier round's "incorrect" that caused the correction.
     Every record from this round carries `layer: 'correction'`; nothing merges layers.
  D. `verdict_axes_v1` -- the new shape. Passes through unchanged.

DIRECTION
---------
`incorrect` has meant two opposite things depending on the label under review, and the
two were pooled (`docs/findings/2026-08-31-objection-axis-hand-sort.md` sec.4). Where the
round records the label, it is used; where it does not, it is recovered from the run that
round was generated from. An `incorrect` on a span we called NOT_A_STORY is the reviewer
OVERTURNING a rejection -- a false negative -- and it migrates to `is_story: 'yes'`.

Usage:
  python3 scripts/migrate_verdicts.py                    # summary per round
  python3 scripts/migrate_verdicts.py --out results/rulers/migrated_verdicts.json
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s [migrate] %(message)s',
                    handlers=[logging.FileHandler(PROJECT_ROOT / 'project.log'),
                              logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)

KEY_RE = re.compile(r'^(.+?)_(\d+)-(\d+)$')

AXES = {
    'is_story': {'yes', 'borderline', 'no'},
    'extent': {'right', 'starts_wrong', 'ends_wrong', 'both_wrong', 'wrong_unspecified'},
    'confidence': {'right', 'too_high', 'too_low', 'wrong_unspecified'},
    'grouping': {'right', 'should_split', 'should_merge', 'wrong_unspecified'},
}

# Every verdict file on disk, the container key its records live under, and which
# vocabulary it speaks. `expert` is False for our own test exports and for automated
# self-checks -- they are listed rather than omitted, so "why is that file not in the
# ledger" has an answer on the page instead of in someone's memory.
ROUNDS = [
    # path                                                          container      vocab                  expert layer
    ('validation/feedback/ketubot_review_Jeffrey_Rubenstein_2026-01-08.json',
                                                                    'feedback',    'axes_2026_01',        True,  'base'),
    ('validation/feedback/ketubot_review_Simon_-_Test_2026-01-05.json',
                                                                    'feedback',    'axes_2026_01',        False, 'base'),
    ('validation/feedback/jeff_v4.1_validation.json',               'details',     'self_check',          False, 'base'),
    ('validation/feedback/validations_v4_2026-01-25.json',          'validations', 'base_pair',           True,  'base'),
    ('validation/feedback/v5_1_feedback_anonymous_2026-02-05 (1).json',
                                                                    'feedback',    'base_pair',           True,  'base'),
    ('validation/feedback/v5_1_feedback_anonymous_2026-02-20.json',  'feedback',    'base_pair',           True,  'base'),
    ('validation/feedback/v8_delta_feedback_anonymous_2026-02-26.json',
                                                                    'feedback',    'base_pair',           True,  'base'),
    ('validation/feedback/canonical_review_anonymous_2026-03-17.json',
                                                                    'feedback',    'canonical_corrected', True,  'correction'),
    ('validation/feedback/kiddushin_review_2026-04-23.json',        'reviews',     'base_pair',           True,  'base'),
    ('validation/feedback/kiddushin_review_2026-05-26 (1).json',    'reviews',     'base_pair',           True,  'base'),
    ('jeff comms/wave4_kiddushin_review_2026-07-06.json',           'reviews',     'base_pair',           True,  'base'),
]

# The run each round was generated from, so the label under review can be recovered where
# the round did not record it. Same index Phase A used.
ROUND_RUNS = {
    'v5_1_feedback_anonymous_2026-02-05 (1).json': ['results/v5/pages_2-39.json',
                                                    'results/v5/pages_40-60.json'],
    'v5_1_feedback_anonymous_2026-02-20.json': ['results/v5/pages_2-39.json',
                                                'results/v5/pages_40-60.json'],
    'v8_delta_feedback_anonymous_2026-02-26.json': ['results/v8/wave1/ketubot_v8_2-60.json',
                                                    'results/v8/wave1/ketubot_v8_61-112.json'],
    'canonical_review_anonymous_2026-03-17.json': ['results/v7/ketubot_v7_2-60.json',
                                                   'results/v7/ketubot_v7_61-112.json'],
    'kiddushin_review_2026-04-23.json': ['results/v7/kiddushin_v7.json'],
    'kiddushin_review_2026-05-26 (1).json': ['results/v9/wave3/kiddushin_v9.json'],
    'wave4_kiddushin_review_2026-07-06.json': ['results/v10/wave4/kiddushin_v10.json'],
}

ALL_AXES = ('extent', 'confidence', 'grouping')


def _shown_index(round_name):
    """(ref, start, end) -> the classification the reviewer was looking at."""
    out = {}
    for rel in ROUND_RUNS.get(round_name, []):
        p = PROJECT_ROOT / rel
        if not p.exists():
            continue
        for page in json.loads(p.read_text()).get('pages', []):
            for bucket in ('stories', 'mishnah_stories'):
                for s in page.get(bucket) or []:
                    out.setdefault((page.get('ref'), s.get('start_segment'),
                                    s.get('end_segment')), s.get('classification'))
    return out


def _hand_sort():
    """Phase A's reading of the notes the keyword rules could not classify."""
    p = PROJECT_ROOT / 'results/rulers/objection_axes.json'
    if not p.exists():
        return {}
    return {(r['round'], r['key']): r for r in json.loads(p.read_text())['resolutions']}


def _blank(**kw):
    rec = {'is_story': None, 'extent': None, 'confidence': None, 'grouping': None,
           'display_broken': False, 'extent_quote': '', 'direction': None,
           'undetermined': list(ALL_AXES) + ['is_story']}
    rec.update(kw)
    return rec


def _settle(rec, **kw):
    """Set axes and drop them from `undetermined` in one place, so the two cannot drift."""
    rec.update(kw)
    rec['undetermined'] = [a for a in rec['undetermined'] if a not in kw]
    return rec


def _direction(shown, is_story):
    if not is_story or not shown:
        return None
    we_said_story = shown != 'NOT_A_STORY'
    if we_said_story and is_story == 'no':
        return 'over_call'
    if not we_said_story and is_story == 'yes':
        return 'under_call'
    if not we_said_story and is_story == 'borderline':
        return 'under_call_borderline'
    return 'agrees'


def _from_objection(rec, objection, direction):
    """Fill what a read objection determines, and nothing more.

    The axis names come straight from Phase A's hand sort and from build_ruler.py's
    keyword rules, which is why they line up with the new UI's axes -- the axes were
    read off that taxonomy rather than invented.
    """
    if objection == 'classification':
        return _settle(rec, is_story=('yes' if direction == 'under_call' else 'no'))
    if objection == 'boundary':
        level = {'extend_start': 'starts_wrong', 'extend_end': 'ends_wrong'}.get(
            direction, 'wrong_unspecified')
        return _settle(rec, is_story='yes', extent=level)
    if objection == 'confidence':
        level = {'raise': 'too_low', 'lower': 'too_high'}.get(direction, 'wrong_unspecified')
        return _settle(rec, is_story='yes', confidence=level)
    if objection == 'merge':
        return _settle(rec, is_story='yes', grouping='wrong_unspecified')
    if objection == 'display':
        rec['display_broken'] = True
        return rec
    if objection == 'not_an_objection':
        # The note affirms and the verdict rejects. Phase A found two of these; the
        # affirmation is the readable half, so the entry migrates as accepted.
        return _settle(rec, is_story='yes', extent='right', confidence='right', grouping='right')
    return rec  # unclassified / unresolvable: nothing is determined, and we say so


def _accept_as_shown(rec, shown):
    """What "you got this right" means, which depends on what we had said.

    `correct` endorses OUR judgment, whatever it was -- so on a span we labelled
    NOT_A_STORY it means "you were right to reject", not "this is a story". Every UI
    that showed the reviewer our rejections has verdicts of this shape: 87 in the
    2026-02-05 round and 5 in the canonical round, all of which would otherwise migrate
    as accepted stories and invent 92 approvals nobody gave.
    """
    if shown == 'NOT_A_STORY':
        return _settle(rec, is_story='no')
    return _settle(rec, is_story='yes', extent='right', confidence='right', grouping='right')


def migrate_base_pair(item, key, shown, objection, direction):
    """correct / incorrect / confirm_remove / reject_remove, on BASE output."""
    verdict = item.get('verdict')
    rec = _blank()
    if verdict == 'correct':
        return _accept_as_shown(rec, shown)
    if verdict == 'reject_remove':
        return _settle(rec, is_story='yes')
    if verdict == 'confirm_remove':
        return _settle(rec, is_story='no')
    if verdict == 'incorrect':
        if shown == 'NOT_A_STORY':
            return _settle(rec, is_story='yes')      # an overturned rejection
        return _from_objection(rec, objection, direction)
    return rec  # no verdict recorded: nothing is determined


def migrate_canonical(item, key, shown, objection, direction):
    """correct / incorrect / approve / adjust, on ALREADY-CORRECTED data."""
    verdict = item.get('verdict')
    rec = _blank()
    if verdict in ('correct', 'approve'):
        # The canonical UI showed all 189 entries in three sections, rejections included,
        # so the same rule applies here as on base data: 5 of its `correct` verdicts sit
        # on spans we had labelled NOT_A_STORY.
        return _accept_as_shown(rec, shown)
    if verdict == 'adjust':
        # The ruler's own reading, and the reason `adjust` counts as ACCEPTED: the story
        # is real and the boundary is wrong. Which end, the vocabulary cannot say.
        return _settle(rec, is_story='yes', extent='wrong_unspecified')
    if verdict == 'incorrect':
        return _from_objection(rec, objection, direction)
    return rec


def migrate_axes_2026_01(item, key, shown, objection, direction):
    """The first UI's own axes: feedback_type + length_adjustment + story_confidence."""
    rec = _blank()
    ft = item.get('feedback_type')
    if ft == 'correct':
        _settle(rec, is_story='yes')
    elif ft == 'false_positive':
        _settle(rec, is_story='no')
    adj = item.get('length_adjustment')
    if adj in ('shrink', 'grow'):
        # It says the extent is wrong. It does not say which end, so neither do we.
        _settle(rec, extent='wrong_unspecified')
        rec['legacy_length_adjustment'] = adj
    # story_confidence is the reviewer's own 0-100 number, not a judgment about OUR
    # label, so it cannot become too_high/too_low. Carried, never converted.
    if item.get('story_confidence') is not None:
        rec['legacy_story_confidence'] = item['story_confidence']
    if item.get('story_type'):
        rec['legacy_story_type'] = item['story_type']
    if item.get('spans_multiple_pages'):
        rec['legacy_spans_multiple_pages'] = True
    return rec


def migrate_verdict_axes_v1(item, key, shown, objection, direction):
    """Already the target shape."""
    rec = _blank()
    return _settle(rec, **{a: item[a] for a in ('is_story',) + ALL_AXES if item.get(a)})


MIGRATORS = {
    'base_pair': migrate_base_pair,
    'canonical_corrected': migrate_canonical,
    'axes_2026_01': migrate_axes_2026_01,
    'verdict_axes_v1': migrate_verdict_axes_v1,
}


def _items(data, container):
    """Every record in a round, as (key, item). Handles both list and dict containers."""
    raw = data.get(container)
    if isinstance(raw, dict):
        return list(raw.items())
    if isinstance(raw, list):
        # The 2026-01 files key by `ref` only -- a page, not a span. Kept as-is rather
        # than invented into a span key; the ref is what the reviewer was given.
        return [(i.get('ref', f'{container}[{n}]'), i) for n, i in enumerate(raw)]
    return []


def migrate_round(path, container, vocab, expert, layer, hand=None, ruler=None):
    p = PROJECT_ROOT / path
    if not p.exists():
        return None
    data = json.loads(p.read_text())
    if not isinstance(data, dict):
        return None
    name = p.name
    shown_idx = _shown_index(name)
    hand = hand if hand is not None else _hand_sort()
    out = []
    for key, item in _items(data, container):
        if not isinstance(item, dict):
            continue
        m = KEY_RE.match(key)
        shown = item.get('classification')
        if not shown and m:
            shown = shown_idx.get((m.group(1), int(m.group(2)), int(m.group(3))))
        h = hand.get((name, key))
        objection = h['axis'] if h else (
            ruler.classify_objection([item.get('note') or item.get('notes') or ''])
            if ruler else 'unclassified')
        direction = h['direction'] if h else None

        rec = MIGRATORS[vocab](item, key, shown, objection, direction) \
            if vocab in MIGRATORS else _blank()
        rec.update({
            'key': key,
            'page_ref': item.get('page_ref') or (m.group(1) if m else key),
            'classification_shown': shown,
            'source_round': name,
            'source_vocabulary': vocab,
            'layer': layer,
            'expert': expert,
            'legacy_verdict': item.get('verdict') or item.get('feedback_type'),
            'note': (item.get('note') or item.get('notes') or '').strip(),
            'objection_axis': objection,
        })
        rec['direction'] = rec['direction'] or _direction(shown, rec['is_story'])
        out.append(rec)
    return out


def migrate_all():
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            'build_ruler', PROJECT_ROOT / 'scripts' / 'build_ruler.py')
        ruler = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ruler)
    except Exception as exc:  # pragma: no cover - the keyword fallback is optional
        log.warning('build_ruler unavailable (%s); notes will not be keyword-sorted', exc)
        ruler = None
    hand = _hand_sort()
    out = {}
    for path, container, vocab, expert, layer in ROUNDS:
        recs = migrate_round(path, container, vocab, expert, layer, hand=hand, ruler=ruler)
        if recs is None:
            log.warning('missing: %s', path)
            continue
        out[Path(path).name] = recs
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out')
    args = ap.parse_args()

    rounds = migrate_all()
    total = und = 0
    for name, recs in rounds.items():
        vocab = recs[0]['source_vocabulary'] if recs else '-'
        layer = recs[0]['layer'] if recs else '-'
        determined = sum(1 for r in recs if r['is_story'])
        u = sum(1 for r in recs if 'is_story' in r['undetermined'])
        total += len(recs)
        und += u
        axes = Counter(a for r in recs for a in ALL_AXES if r[a] not in (None, 'right'))
        log.info('%-46s %-20s %-10s n=%-4d is_story determined=%-4d undetermined=%-4d %s',
                 name[:46], vocab, layer, len(recs), determined, u, dict(axes) or '')
    log.info('%d records across %d rounds; %d carry no is_story (the old vocabulary '
             'could not express it, and we do not guess)', total, len(rounds), und)

    if args.out:
        p = PROJECT_ROOT / args.out
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({
            'what': 'Every banked review verdict, projected onto the verdict-axes shape.',
            'built_by': 'scripts/migrate_verdicts.py',
            'axes': {k: sorted(v) for k, v in AXES.items()},
            'coarser_values': {
                'wrong_unspecified': 'the old vocabulary said this axis is wrong but not how',
                'undetermined': 'the old vocabulary could not express the question at all',
            },
            'rounds': rounds}, ensure_ascii=False, indent=1))
        log.info('wrote %s', p)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
