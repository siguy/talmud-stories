#!/usr/bin/env python3
"""What did Jeff's verdict MEAN? One reading, shared by every script that reads one.

Before the axes UI (2026-09-02) every round asked "is the DETECTOR'S CALL correct?",
not "is this a story?". A `correct` on a span the detector called NOT_A_STORY is his
**no** -- 87 of the 128 verdicts of 2026-02-05. Reading `correct` as "a story" whatever
he was shown is the defect this module exists to end (finding
docs/findings/2026-09-28-consensus-phase1.md sec. 8; Lesson 42's family).

Written for consensus phase 1 (scripts/judge_labelled_spans.py) on 2026-09-28 and moved
here the same week so build_ruler.py and map_verdict_vocabularies.py read verdicts the
same way instead of three ways. The rules are in label_old()'s docstring table and in
judge_labelled_spans.py's module docstring.

Entry point:  read_verdict(round_name, key, verdict, note, is_axes, classify_objection)
              -> (label, why, shown_classification)
  label: yes | no | borderline | out_of_scope | unknown
"""
from __future__ import annotations

import json
import re
import subprocess
from functools import lru_cache
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

STORY_CALLS = {'YES', 'HIGH_CONFIDENCE', 'LOW_CONFIDENCE', 'BORDERLINE'}


# ---------------------------------------------------------------------------
# review files: every one accounted for
# ---------------------------------------------------------------------------

def _embedded(html: str, tag: str):
    m = re.search(r'<script id="%s" type="application/json">(.*?)</script>' % tag, html, re.S)
    if not m:
        raise ValueError(f'no embedded <script id="{tag}"> in the page')
    return json.loads(m.group(1))


def _git_show(rev_path: str) -> str:
    return subprocess.run(['git', 'show', rev_path], cwd=PROJECT_ROOT,
                          capture_output=True, text=True, check=True).stdout


def _shown_from_pages(data):
    out = {}
    for p in data['pages']:
        for s in p.get('stories', []):
            heb = [p['segments'][i].get('hebrew', '') for i in
                   range(s['start_segment'], s['end_segment'] + 1)
                   if i < len(p.get('segments', []))]
            out[f"{p['ref']}_{s['start_segment']}-{s['end_segment']}"] = (s.get('classification'), heb)
    return out


def shown_v5_2_60():
    out = {}
    for name in ('ketubot_2-39 (1).html', 'ketubot_40-60 (1).html'):   # the pages he sent back
        out.update(_shown_from_pages(_embedded(
            (PROJECT_ROOT / 'validation/feedback' / name).read_text(), 'storiesData')))
    return out


def shown_v5_61_112():
    # The page as it stood before his 2026-02-20 review: it was regenerated on 02-22.
    return _shown_from_pages(_embedded(_git_show('0f1f3a4:validation/ui/ketubot_61-112.html'),
                                       'storiesData'))


def shown_v8_delta():
    data = _embedded((PROJECT_ROOT / 'validation/ui/ketubot_61-112_v8_delta.html').read_text(),
                     'deltaData')
    out = {}
    for tier in ('tier1', 'tier2', 'tier3'):
        for item in data.get(tier, []):
            st = item.get('story') or {}
            key = st.get('key') or item.get('v7_key')
            out[key] = (st.get('classification') or item.get('v8_cls'), None)
    return out


def shown_canonical():
    data = _embedded((PROJECT_ROOT / 'validation/ui/ketubot_canonical_review.html').read_text(),
                     'reviewData')
    out = {}
    for group in ('review_items', 'auto_items', 'unchanged_items'):
        for s in data.get(group, []):
            out[f"{s['page_ref']}_{s['start_segment']}-{s['end_segment']}"] = (s.get('classification'), None)
    return out


def shown_in_file(rel):
    def load():
        d = json.loads((PROJECT_ROOT / rel).read_text())
        return {k: (v.get('classification'), None) for k, v in d['reviews'].items()}
    return load


def shown_run(rel):
    def load():
        d = json.loads((PROJECT_ROOT / rel).read_text())
        return _shown_from_pages(d)
    return load


ROUNDS = {
    'v5_1_feedback_anonymous_2026-02-05 (1).json': dict(applies_to='base', shown=shown_v5_2_60),
    'v5_1_feedback_anonymous_2026-02-20.json': dict(applies_to='base', shown=shown_v5_61_112),
    'v8_delta_feedback_anonymous_2026-02-26.json': dict(applies_to='base', shown=shown_v8_delta),
    'canonical_review_anonymous_2026-03-17.json': dict(applies_to='corrected', shown=shown_canonical),
    'kiddushin_review_2026-04-23.json': dict(
        applies_to='base', shown=shown_in_file('validation/feedback/kiddushin_review_2026-04-23.json')),
    'kiddushin_review_2026-05-26 (1).json': dict(
        applies_to='base', shown=shown_in_file('validation/feedback/kiddushin_review_2026-05-26 (1).json')),
    'wave4_kiddushin_review_2026-07-06.json': dict(
        applies_to='base', shown=shown_run('results/v10/wave4/kiddushin_v10.json')),
    'gittin_axes_review_2026-09-02.json': dict(applies_to='base', shown=None),
    'review_2026-09-16_bundle_jeff_2026-09-23.json': dict(applies_to='base', shown=None),
}
EXCLUDED = {
    'ketubot_review_Simon_-_Test_2026-01-05.json': "Simon's test round -- not an expert verdict",
    'review_2026-09-15_bundle_simon_prescreen_2026-09-16.json': "Simon's pre-screen -- not an expert verdict",
    'ketubot_review_Jeffrey_Rubenstein_2026-01-08.json':
        'keyed per daf, not per span (25 verdicts); load_reviews() cannot read it and it '
        'cannot be joined to a span mechanically (capture_january_round.py, Lesson 38)',
    'jeff_v4.1_validation.json': 'carries no span verdicts',
    'validations_v4_2026-01-25.json': 'carries no verdicts',
}
REVIEW_GLOBS = ('validation/feedback/*.json', 'jeff comms/*.json')


class UnaccountedFile(RuntimeError):
    """A review file nobody decided about. Raised, never skipped (Lesson 38)."""


def account_for_review_files(root: Path = PROJECT_ROOT):
    """Every review file on disk is either read or excluded by name. Returns the inventory."""
    inventory = {}
    for pattern in REVIEW_GLOBS:
        for path in sorted(root.glob(pattern)):
            if path.name in ROUNDS:
                json.loads(path.read_text())          # unreadable -> raises
                inventory[path.name] = 'read'
            elif path.name in EXCLUDED:
                inventory[path.name] = 'excluded: ' + EXCLUDED[path.name]
            else:
                raise UnaccountedFile(f'{path} is neither in ROUNDS nor EXCLUDED -- decide about it')
    return inventory



SCOPE_NOTE = re.compile(r'\bscope\b|class of stories', re.I)

# Hand reading of the notes the rules above read wrongly, found by printing every
# `incorrect` note and every `correct` note that argues a polarity (2026-09-28). A human
# judgment, recorded so it is auditable -- the pattern of resolve_unclassified_notes.AXES.
HAND_LABELS = {
    ('v5_1_feedback_anonymous_2026-02-20.json', 'Ketubot 88a_8-8'):
        ('no', '"this is not enough even for a borderline story" -- the word is negated'),
    ('v5_1_feedback_anonymous_2026-02-20.json', 'Ketubot 105b_9-9'):
        ('yes', '"borderline" is said of a second story inside the span, not of the span'),
    ('v5_1_feedback_anonymous_2026-02-20.json', 'Ketubot 67b_17-17'):
        ('yes', '"borderline" is said of the previous line, not of the span'),
    ('kiddushin_review_2026-04-23.json', 'Kiddushin 41a_3-3'):
        ('no', '"This is not even a story of low confidence" -- read as a confidence objection'),
    ('kiddushin_review_2026-04-23.json', 'Kiddushin 72b_4-4'):
        ('out_of_scope', '"This is a biblical story. It is not about the rabbis" -- R-S1 says '
                         'OUT_OF_SCOPE, never NOT_A_STORY'),
}
BORDERLINE_NOTE = re.compile(r'\bborderline\b', re.I)


def label_axes(verdict, note):
    if verdict == 'correct':
        return 'yes', 'is_story=yes'
    if verdict == 'borderline':
        return 'borderline', 'is_story=borderline'
    if verdict == 'incorrect':
        if SCOPE_NOTE.search(note or ''):
            return 'out_of_scope', 'is_story=no, note puts it outside the scope (R-S1)'
        return 'no', 'is_story=no'
    return 'unknown', f'unknown axes verdict {verdict!r}'


def label_old(verdict, shown, note, hand, classify_objection):
    """His verdict on an old round, read against the classification he was SHOWN."""
    if verdict == 'confirm_remove':
        return 'no', 'confirmed the removal'
    if verdict in ('reject_remove', 'adjust'):
        return 'yes', f'{verdict}: a story'
    if shown is None:
        return 'unknown', 'the classification he was shown is not on disk'
    storyish = shown in STORY_CALLS
    if verdict in ('correct', 'approve'):
        if not storyish:
            return 'no', f'{verdict} on {shown}'
        if BORDERLINE_NOTE.search(note or ''):
            return 'borderline', f'{verdict} on {shown}; his note says borderline (Lesson 42)'
        return 'yes', f'{verdict} on {shown}'
    if verdict == 'incorrect':
        kind = classify_objection([note]) if note else 'unclassified'
        polarity = None
        if kind == 'unclassified' and hand:
            kind, polarity = hand.get('axis') or 'unclassified', hand.get('note_polarity')
        if kind == 'classification':
            if polarity == 'says_story':
                return 'yes', 'incorrect; his note says it is a story'
            if polarity == 'says_not_story':
                return 'no', 'incorrect; his note says it is not a story'
            return ('no' if storyish else 'yes'), f'incorrect on {shown}; classification objection'
        if kind in ('boundary', 'merge', 'display'):
            return (('yes', f'incorrect on {shown}; {kind} objection -- a story, mis-drawn')
                    if storyish else ('unknown', f'incorrect on {shown}; {kind} objection'))
        if kind == 'confidence':
            if BORDERLINE_NOTE.search(note or ''):
                return 'borderline', f'incorrect on {shown}; confidence objection saying borderline'
            return 'yes', f'incorrect on {shown}; confidence objection -- a story'
        return 'unknown', 'bare incorrect, no readable objection'
    return 'unknown', f'unmapped verdict {verdict!r}'


@lru_cache(maxsize=None)
def shown_calls(round_name):
    """{review key: (classification shown, hebrew or None)} for one round; {} if none."""
    cfg = ROUNDS.get(round_name)
    return (cfg['shown']() if cfg and cfg['shown'] else {})


@lru_cache(maxsize=None)
def _hand_resolved():
    path = PROJECT_ROOT / 'results/rulers/unclassified_notes_resolved.json'
    if not path.exists():
        return {}
    return {(r['round'], r['key']): r for r in json.loads(path.read_text())['rows']}


def read_verdict(round_name, key, verdict, note, is_axes, classify_objection):
    """(label, why, shown) for one verdict. Rounds not in ROUNDS -> ('unknown', ..., None)."""
    if round_name in EXCLUDED:
        return 'unknown', 'excluded round: ' + EXCLUDED[round_name], None
    if round_name not in ROUNDS:
        return 'unknown', 'round not in ROUNDS', None
    if is_axes:
        label, why = label_axes(verdict, note)
        shown = None
    else:
        shown, _ = shown_calls(round_name).get(key, (None, None))
        label, why = label_old(verdict, shown, note, _hand_resolved().get((round_name, key)),
                               classify_objection)
    if (round_name, key) in HAND_LABELS:
        label, why = HAND_LABELS[(round_name, key)]
        why = 'hand reading: ' + why
    return label, why, shown
