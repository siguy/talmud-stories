#!/usr/bin/env python3
"""
Phase A of `work/2026-08-30-review-verdict-axes.md`: resolve the rejection notes
that `classify_objection()` could not read, onto the axes the ruler already uses.

Why this needs a script rather than a careful read: a verdict must be read
against **the classification the reviewer actually saw**, which is the one the
*reviewed version* produced — not the one in the ruler's
`detector_classification` column, which is today's run. Those differ, and the
difference inverts the meaning of several notes. Ketubot 10b_1-1 is the clearest
case: v5.1 classified it `NOT_A_STORY`, Jeff clicked `incorrect` and wrote "This
is definitely a story", and today's detector says `YES`. Read against today's
column the note looks like agreement recorded as a rejection; read against v5.1
it is a false negative that has since been fixed.

This script emits, per note: the round, the version reviewed, what that version
classified, what the current run classifies, and the hand-assigned axis. The
axis assignments live in AXES below and are a human judgement — they are
recorded here so they are auditable and re-runnable, not to imply they were
computed.

Output: results/rulers/unclassified_notes_resolved.json
"""

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / 'scripts'))

from build_ruler import classify_objection            # noqa: E402

# Which detector output each review round was generated from. The version
# strings come from the feedback files' own metadata where they carry one.
ROUND_SOURCES = {
    'v5_1_feedback_anonymous_2026-02-05 (1).json': (
        'v5.1_categorical',
        ['results/v5/pages_2-39.json', 'results/v5/pages_40-60.json']),
    'v8_delta_feedback_anonymous_2026-02-26.json': (
        'v8_delta',
        ['results/v8/wave1/ketubot_v8_2-60.json',
         'results/v8/wave1/ketubot_v8_61-112.json']),
    'kiddushin_review_2026-04-23.json': (
        'v7', ['results/v7/kiddushin_v7.json']),
    'kiddushin_review_2026-05-26 (1).json': (
        'v7', ['results/v7/kiddushin_v7.json']),
    'wave4_kiddushin_review_2026-07-06.json': (
        'v10_wave4', ['results/v10/wave4/kiddushin_v10.json']),
    # Added 2026-08-31 (Phase B). None of these three contributes a note to this
    # script's population, so the extension was verified score-neutral before it
    # landed: population 34, polarity 12, disagreed 8, agrees-today 7 and
    # changed-since-review 15 are all identical with and without it. They are
    # here because this table is the project's one round -> detector-version map
    # and a second copy elsewhere is how the versions drift apart.
    'canonical_review_anonymous_2026-03-17.json': (
        'canonical', ['results/canonical/ketubot_canonical.json']),
    'v5_1_feedback_anonymous_2026-02-20.json': (
        'v5.1_categorical',
        ['results/v5/pages_2-39.json', 'results/v5/pages_40-60.json']),
    # v4-era output is not on disk, so the saw-column for this round stays blank
    # and the script names it in missing_source_runs rather than going quiet.
    'ketubot_review_Jeffrey_Rubenstein_2026-01-08.json': ('v4_era', []),
}

CURRENT = {
    'Ketubot': ['results/v10/wave4_notrim/ketubot_v10_2-60_notrim.json',
                'results/v10/wave4_notrim/ketubot_v10_61-112_notrim.json'],
    'Kiddushin': ['results/v10/wave4_notrim/kiddushin_v10_notrim.json'],
}

# Hand-assigned axis per (round, key). Assigned by reading each note against the
# classification the reviewed version produced (the `saw` field in the output).
#
#   classification  - "this is not a story" / "this IS a story" against a
#                     NOT_A_STORY call. A genuine capability-3 objection.
#   boundary        - the extent is wrong (start, end, or a quoted correct span)
#   merge           - grouping: one story not two, or two not one
#   confidence      - the confidence level is wrong, story judgement not disputed
#   display         - a renderer defect, not a judgement about the text at all
#   unresolvable    - the note is empty; nothing is recoverable
AXES = {
    ("v5_1_feedback_anonymous_2026-02-05 (1).json", "Ketubot 10b_1-1"): "classification",
    ("v5_1_feedback_anonymous_2026-02-05 (1).json", "Ketubot 10b_3-3"): "classification",
    ("v5_1_feedback_anonymous_2026-02-05 (1).json", "Ketubot 10b_6-6"): "classification",
    ("v5_1_feedback_anonymous_2026-02-05 (1).json", "Ketubot 40b_11-11"): "classification",
    ("v5_1_feedback_anonymous_2026-02-05 (1).json", "Ketubot 42b_8-8"): "classification",
    ("v5_1_feedback_anonymous_2026-02-05 (1).json", "Ketubot 56a_2-2"): "classification",
    ("v5_1_feedback_anonymous_2026-02-05 (1).json", "Ketubot 52b_17-17"): "boundary",
    ("v5_1_feedback_anonymous_2026-02-05 (1).json", "Ketubot 56b_11-11"): "boundary",
    ("v5_1_feedback_anonymous_2026-02-05 (1).json", "Ketubot 8b_6-10"): "merge",

    ("v8_delta_feedback_anonymous_2026-02-26.json", "Ketubot 61b_1-1"): "unresolvable",
    ("v8_delta_feedback_anonymous_2026-02-26.json", "Ketubot 62a_4-4"): "classification",
    ("v8_delta_feedback_anonymous_2026-02-26.json", "Ketubot 62b_9-9"): "merge",
    ("v8_delta_feedback_anonymous_2026-02-26.json", "Ketubot 63a_2-2"): "unresolvable",
    ("v8_delta_feedback_anonymous_2026-02-26.json", "Ketubot 69b_10-12"): "unresolvable",
    ("v8_delta_feedback_anonymous_2026-02-26.json", "Ketubot 85a_3-4"): "unresolvable",
    ("v8_delta_feedback_anonymous_2026-02-26.json", "Ketubot 86a_4-4"): "unresolvable",
    ("v8_delta_feedback_anonymous_2026-02-26.json", "Ketubot 106a_3-3"): "unresolvable",
    ("v8_delta_feedback_anonymous_2026-02-26.json", "Ketubot 111a_9-9"): "unresolvable",

    ("kiddushin_review_2026-04-23.json", "Kiddushin 13a_3-3"): "confidence",
    ("kiddushin_review_2026-04-23.json", "Kiddushin 30a_7-7"): "classification",
    ("kiddushin_review_2026-04-23.json", "Kiddushin 31b_4-4"): "classification",
    ("kiddushin_review_2026-04-23.json", "Kiddushin 32b_1-1"): "confidence",
    ("kiddushin_review_2026-04-23.json", "Kiddushin 39b_13-13"): "confidence",
    ("kiddushin_review_2026-04-23.json", "Kiddushin 52a_4-6"): "classification",
    ("kiddushin_review_2026-04-23.json", "Kiddushin 66a_5-5"): "confidence",
    ("kiddushin_review_2026-04-23.json", "Kiddushin 72b_4-4"): "classification",
    ("kiddushin_review_2026-04-23.json", "Kiddushin 73a_5-5"): "classification",

    ("kiddushin_review_2026-05-26 (1).json", "Kiddushin 9a_1-1"): "boundary",

    ("wave4_kiddushin_review_2026-07-06.json", "Kiddushin 8b_14-14"): "display",
    ("wave4_kiddushin_review_2026-07-06.json", "Kiddushin 12b_8-8"): "boundary",
    ("wave4_kiddushin_review_2026-07-06.json", "Kiddushin 12b_10-10"): "boundary",
    ("wave4_kiddushin_review_2026-07-06.json", "Kiddushin 13a_3-3"): "boundary",
    ("wave4_kiddushin_review_2026-07-06.json", "Kiddushin 22b_18-18"): "boundary",
    ("wave4_kiddushin_review_2026-07-06.json", "Kiddushin 25a_1-3"): "boundary",
}


# What the note argues the passage IS, where it says so plainly. Hand-assigned,
# same discipline as AXES: "says_story" means the note asserts it is a story,
# "says_not_story" that it is not, and None that the note takes no position on
# the story/not-story question (a pure boundary, merge or display complaint, or
# an empty note). Used to test mechanically whether today's detector has since
# come to agree.
POLARITY = {
    ("v5_1_feedback_anonymous_2026-02-05 (1).json", "Ketubot 10b_1-1"): "says_story",
    ("v5_1_feedback_anonymous_2026-02-05 (1).json", "Ketubot 10b_3-3"): "says_story",
    ("v5_1_feedback_anonymous_2026-02-05 (1).json", "Ketubot 10b_6-6"): "says_story",
    ("v5_1_feedback_anonymous_2026-02-05 (1).json", "Ketubot 40b_11-11"): "says_not_story",
    ("v5_1_feedback_anonymous_2026-02-05 (1).json", "Ketubot 42b_8-8"): "says_not_story",
    ("v5_1_feedback_anonymous_2026-02-05 (1).json", "Ketubot 56a_2-2"): "says_not_story",
    ("v8_delta_feedback_anonymous_2026-02-26.json", "Ketubot 62a_4-4"): "says_story",
    ("kiddushin_review_2026-04-23.json", "Kiddushin 30a_7-7"): "says_story",
    ("kiddushin_review_2026-04-23.json", "Kiddushin 31b_4-4"): "says_story",
    ("kiddushin_review_2026-04-23.json", "Kiddushin 52a_4-6"): "says_not_story",
    ("kiddushin_review_2026-04-23.json", "Kiddushin 72b_4-4"): "says_not_story",
    ("kiddushin_review_2026-04-23.json", "Kiddushin 73a_5-5"): "says_story",
}

STORY_CALLS = {"YES", "HIGH_CONFIDENCE", "LOW_CONFIDENCE"}


def agrees(call, polarity):
    """
    Does a detector classification agree with what the note argues?

    `call is None` is NOT "no opinion": it means the run carries no proposal at
    that key. For a note arguing "not a story" that is agreement by omission —
    the detector no longer claims it. For a note arguing "this IS a story" it is
    the opposite of agreement: the passage has gone missing entirely, which is a
    Detection loss, not a Classification fix. Collapsing the two would let a
    disappeared story read as a resolved complaint.
    """
    if polarity is None:
        return None
    if call is None:
        return polarity == "says_not_story"
    is_story = call in STORY_CALLS
    return is_story if polarity == "says_story" else not is_story


KEY_RE = re.compile(r'^(.+?)_(\d+)-(\d+)$')


def lookup(table, ident):
    """
    The classification of any span OVERLAPPING ident, preferring an exact match.

    Returns None only when the run proposes nothing touching those segments.
    """
    if ident is None:
        return None
    if ident in table:
        return table[ident]
    ref, a, b = ident
    overlapping = [cls for (r, s2, e2), cls in table.items()
                   if r == ref and s2 is not None and e2 is not None
                   and s2 <= b and a <= e2]
    if not overlapping:
        return None
    # Prefer a story call over NOT_A_STORY: the question asked is whether the
    # run still asserts a story here, and a rejected sibling span does not
    # cancel an accepted one.
    for cls in overlapping:
        if cls in STORY_CALLS:
            return cls
    return overlapping[0]


def load_classifications(rels):
    """
    (ref, start, end) -> classification, from a detector output.

    Callers must look these up with `lookup()`, not by exact key. A verdict key
    names the span the REVIEWED version proposed; a later version proposing the
    same passage with a different extent is a boundary change, not a missing
    story. Keying exactly makes every re-bounded story read as "no longer
    proposed" — which is how Ketubot 10b_3-3 was briefly reported as a
    regression when the current run in fact proposes 10b segments 3-5.
    """
    out = {}
    for rel in rels:
        path = REPO / rel
        if not path.exists():
            continue
        data = json.loads(path.read_text())
        pages = data['pages'] if isinstance(data, dict) and 'pages' in data else data
        for p in pages:
            ref = p.get('ref', '')
            for s in (p.get('stories') or []) + (p.get('mishnah_stories') or []):
                key = (ref, s.get('start_segment'), s.get('end_segment'))
                out[key] = s.get('classification')
    return out


def main():
    current = {t: load_classifications(r) for t, r in CURRENT.items()}
    reviewed = {rnd: load_classifications(rels)
                for rnd, (_, rels) in ROUND_SOURCES.items()}
    missing_sources = [rnd for rnd, m in reviewed.items() if not m]

    # Collect the population exactly as the ruler defines it.
    notes = {}
    for f in sorted((REPO / 'results/rulers').glob('*_ruler.json')):
        d = json.loads(f.read_text())
        for e in d['entries']:
            for v in (e.get('verdicts') or []):
                if v['verdict'] not in ('incorrect', 'confirm_remove'):
                    continue
                if classify_objection([v.get('note')]) != 'unclassified':
                    continue
                k = (v['round'], v['key'])
                if k in notes:
                    continue
                notes[k] = {'tractate': d['tractate'], 'note': v.get('note') or ''}

    rows, unassigned = [], []
    for (rnd, key), meta in sorted(notes.items()):
        m = KEY_RE.match(key)
        ident = (m.group(1), int(m.group(2)), int(m.group(3))) if m else None
        version = ROUND_SOURCES.get(rnd, ('unknown', []))[0]
        axis = AXES.get((rnd, key))
        if axis is None:
            unassigned.append((rnd, key))
        rows.append({
            'round': rnd,
            'version_reviewed': version,
            'tractate': meta['tractate'],
            'key': key,
            'note': meta['note'],
            'classification_reviewer_saw': lookup(reviewed.get(rnd, {}), ident),
            'classification_today': lookup(current.get(meta['tractate'], {}), ident),
            'axis': axis,
            'note_polarity': POLARITY.get((rnd, key)),
            'agreed_at_review': agrees(lookup(reviewed.get(rnd, {}), ident),
                                       POLARITY.get((rnd, key))),
            'agrees_today': agrees(lookup(current.get(meta['tractate'], {}), ident),
                                   POLARITY.get((rnd, key))),
        })

    assert not unassigned, f"notes with no hand-assigned axis: {unassigned}"

    counts = Counter(r['axis'] for r in rows)
    by_round = defaultdict(Counter)
    for r in rows:
        by_round[r['round']][r['axis']] += 1

    # A note is "fixed since" when the version reviewed and today disagree AND
    # today's call is the one the note argues for. Reported, never inferred:
    # only the two mechanical cases are counted.
    fixed = [r for r in rows
             if r['classification_reviewer_saw'] and r['classification_today']
             and r['classification_reviewer_saw'] != r['classification_today']]

    polar = [r for r in rows if r['note_polarity']]
    then_wrong = [r for r in polar if r['agreed_at_review'] is False]
    now_right = [r for r in then_wrong if r['agrees_today'] is True]

    out = {
        'polarity_stated': len(polar),
        'detector_disagreed_at_review': len(then_wrong),
        'detector_agrees_today': len(now_right),
        'built_by': 'scripts/resolve_unclassified_notes.py',
        'population': len(rows),
        'note': ('Population is the set of rejection verdicts whose note '
                 'classify_objection() returns "unclassified" for, deduped by '
                 '(round, key). It is 34, not the 24 quoted in '
                 'work/2026-08-30-review-verdict-axes.md, whose table omits the '
                 'v5.1 round (9) and the 2026-05-26 round (1).'),
        'axes': dict(counts),
        'by_round': {k: dict(v) for k, v in by_round.items()},
        'classification_changed_since_review': len(fixed),
        'missing_source_runs': missing_sources,
        'rows': rows,
    }
    dest = REPO / 'results/rulers/unclassified_notes_resolved.json'
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print(f"population: {len(rows)} (deduped by round+key)")
    print("\naxes:")
    for axis, n in counts.most_common():
        print(f"  {axis:16s} {n}")
    print("\nby round:")
    for rnd, c in by_round.items():
        print(f"  {rnd[:44]:44s} {dict(c)}")
    if missing_sources:
        print(f"\nWARNING missing source runs (saw-column blank): {missing_sources}")
    print(f"\nclassification differs between reviewed version and today: {len(fixed)}")
    for r in fixed:
        print(f"  {r['key']:22s} {r['version_reviewed']:16s} "
              f"{r['classification_reviewer_saw']} -> {r['classification_today']}")
    print(f"\nnotes stating a story/not-story position: {len(polar)}")
    print(f"  detector disagreed at review time:        {len(then_wrong)}")
    print(f"  ...of which today's detector AGREES:      {len(now_right)}")
    for r in then_wrong:
        if r['classification_today'] is None:
            mark = ('FIXED - no longer proposed'
                    if r['note_polarity'] == 'says_not_story'
                    else 'WORSE - story no longer proposed at all')
        else:
            mark = 'FIXED' if r['agrees_today'] else 'still disagrees'
        print(f"    {r['key']:22s} {r['note_polarity']:14s} "
              f"{r['classification_reviewer_saw']} -> {r['classification_today']}  [{mark}]")
    print(f"\nWrote {dest}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
