#!/usr/bin/env python3
"""
Build a sub-segment boundary test set from Jeff Rubenstein's 2005 Ketubot list.

WHY THIS EXISTS: the existing test set (tests/expert_boundary_targets.json) is
built entirely from Jeff's CORRECTIONS, so every question is a case we already
know we got wrong. Its own header says it measures "do we fix known failures",
never "do we stay right on the ones we had". It is also small — 52 targets, 35
of them gradeable.

Jeff's 2005 list (`jeff comms/b.ketubot (1).doc`, columns מיקום | טקסט | מקבילות |
הערות) contains the FULL HEBREW TEXT of 149 Ketubot stories, transcribed twenty
years before this detector existed. That makes it genuinely detector-blind and a
NEUTRAL sample rather than a list of our failures — and because he wrote each
story out start to finish, every entry carries both a start and an end boundary.

METHOD. Locate each story's segment window by 4-gram voting (same as
measure_recall_vs_expert_list.py), then align Jeff's text against that window's
Hebrew with difflib and take the first and last matching blocks as the story's
edges. Jeff's text is his own edition — unvocalised and abbreviated (א"ל for
אמר ליה) — so exact substring matching fails; sequence alignment does not.
Measured 2026-08-30: 147 of 149 align with >=85% of his letters matched in order.

Every target records `align_fraction` and `bracket_ratio` so a consumer can
filter on alignment quality rather than trusting all of them equally, and
`exact_clause_edge` — whether Jeff's boundary falls ON a clause boundary or
INSIDE a clause. That last field is not bookkeeping: if his boundaries routinely
land mid-clause, clause-anchored spans (Wave 5) have a ceiling no prompt can
lift, and we would want to know that before tuning further.

Usage:
  python3 scripts/build_boundary_testset_2005.py \
      --expert-doc "jeff comms/b.ketubot (1).doc" \
      --out tests/expert_boundary_targets_2005.json
"""
import argparse
import difflib
import glob
import json
import logging
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from src.story_detector_v11 import _split_into_clauses  # noqa: E402
from scripts.measure_recall_vs_expert_list import (grams, locate,  # noqa: E402
                                                   parse_expert_doc)

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s [testset2005] %(message)s',
                    handlers=[logging.FileHandler(PROJECT_ROOT / 'project.log'),
                              logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)

NIKUD = re.compile(r'[֑-ׇ]')
HTML = re.compile(r'<[^>]+>')

MIN_ALIGN_FRACTION = 0.85   # of Jeff's letters, matched in order
MAX_BRACKET_RATIO = 1.6     # bracketed region vs his text length
MIN_BLOCK = 5               # ignore incidental short matches


def norm_map(text):
    """Letters-only string plus a map from each kept letter to its original index.

    Nikud and HTML are blanked rather than removed so positions stay aligned
    while we build the map.
    """
    blank = lambda m: ' ' * len(m.group())
    flat = HTML.sub(blank, NIKUD.sub(blank, text or ''))
    keep, idx = [], []
    for i, ch in enumerate(flat):
        if 'א' <= ch <= 'ת':
            keep.append(ch)
            idx.append(i)
    return ''.join(keep), idx


def load_units(tractate):
    """Every segment of the tractate, in reading order: (ref, index, hebrew)."""
    units = []
    # Detector output for tractates we have run, plus raw Sefaria text for those we
    # have only fetched (Gittin, Yevamot, Eruvin as of 2026-08-30). Without the second
    # glob this returned 0 segments for every un-run tractate, silently producing an
    # empty test set rather than an error.
    paths = (sorted(glob.glob(str(PROJECT_ROOT / 'results/v10/wave4_notrim/*.json')))
             + sorted(glob.glob(str(PROJECT_ROOT / 'results/sefaria/*.json'))))
    seen = set()
    for path in paths:
        data = json.loads(Path(path).read_text())
        name = str(data.get('tractate') or Path(path).stem)
        if tractate.lower() not in name.lower() and tractate.lower() not in Path(path).stem.lower():
            continue
        for page in data['pages']:
            for s in page.get('segments', []):
                key = (page['ref'], s['index'])
                if key in seen:
                    continue
                seen.add(key)
                units.append((page['ref'], s['index'], s['hebrew']))
    if not units:
        raise SystemExit(
            f"no segments found for {tractate!r}. Fetch it first "
            f"(scripts/fetch_tractate_pages.py) or check the tractate name.")
    daf = lambda ref: (int(re.search(r'(\d+)', ref).group(1)), 0 if ref.rstrip()[-1] == 'a' else 1)
    units.sort(key=lambda u: (daf(u[0]), u[1]))
    return units


HEB_LETTER = re.compile(r'[א-ת]')


def clause_of(hebrew, letter_pos, side):
    """(clause index holding `letter_pos`, n_clauses, does it sit at a clause edge).

    `letter_pos` is the position of Jeff's FIRST (side='start') or LAST
    (side='end') Hebrew letter. "At a clause edge" must tolerate non-letters:
    a clause range runs to just past its final '.', and Jeff's text ends on a
    letter, so a strict equality test would report every end as mid-clause.
    The question is whether any Hebrew LETTER of the clause is left outside his
    boundary.
    """
    clauses = _split_into_clauses(hebrew)
    if not clauses:
        return None, 0, False
    for ci, (a, b) in enumerate(clauses):
        if a <= letter_pos < b:
            gap = hebrew[a:letter_pos] if side == 'start' else hebrew[letter_pos + 1:b]
            return ci, len(clauses), not HEB_LETTER.search(gap)
    ci = len(clauses) - 1
    return ci, len(clauses), False


def align_story(story, units, window):
    """Locate Jeff's text inside `window` and return its two edges.

    Returns None when the alignment is too weak to trust.
    """
    parts, owners = [], []       # owners[i] = (ref, seg_index, offset_in_segment)
    for ref, seg_idx, heb in window:
        for k in range(len(heb)):
            owners.append((ref, seg_idx, k))
        parts.append(heb)
    joined = ''.join(parts)

    H, Hmap = norm_map(joined)
    J, _ = norm_map(story['text'])
    if len(J) < 20 or not H:
        return None

    blocks = [b for b in difflib.SequenceMatcher(None, H, J, autojunk=False)
              .get_matching_blocks() if b.size >= MIN_BLOCK]
    if not blocks:
        return None

    matched = sum(b.size for b in blocks)
    frac = matched / len(J)
    start_n, end_n = blocks[0].a, blocks[-1].a + blocks[-1].size - 1
    bracket = (end_n - start_n + 1) / len(J)
    if frac < MIN_ALIGN_FRACTION or bracket > MAX_BRACKET_RATIO:
        return None

    edges = {}
    by_seg = {(r, i): h for r, i, h in window}
    for side, n_pos in (('start', start_n), ('end', end_n)):
        ref, seg_idx, off = owners[Hmap[n_pos]]
        ci, n_cl, exact = clause_of(by_seg[(ref, seg_idx)], off, side)
        if ci is None:
            return None
        edges[side] = {'located_on': ref, 'segment': seg_idx, 'clause': ci,
                       'n_clauses': n_cl, 'exact_clause_edge': exact}
    return {'edges': edges, 'align_fraction': round(frac, 3),
            'bracket_ratio': round(bracket, 3)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--expert-doc', required=True)
    ap.add_argument('--tractate', default='Ketubot')
    ap.add_argument('--out', default='tests/expert_boundary_targets_2005.json')
    args = ap.parse_args()

    expert = parse_expert_doc(args.expert_doc, args.tractate)
    units = load_units(args.tractate)
    log.info('expert stories: %d | corpus segments: %d', len(expert), len(units))

    index = defaultdict(set)
    unit_grams = [grams(h) for _, _, h in units]
    for i, gs in enumerate(unit_grams):
        for g in gs:
            index[g].add(i)

    targets, rejected = [], []
    for n, story in enumerate(expert):
        gs = grams(story['text'])
        cov, a, b = locate(gs, [(r, i, g) for (r, i, _), g in zip(units, unit_grams)], index)
        if a is None:
            rejected.append({**story, 'reason': 'not_located', 'coverage': round(cov, 3)})
            continue
        aligned = align_story(story, units, units[a:b + 1])
        if aligned is None:
            rejected.append({**story, 'reason': 'weak_alignment', 'coverage': round(cov, 3)})
            continue
        for side, edge in aligned['edges'].items():
            targets.append({
                'ref': story['ref'], 'direction': side, **edge,
                'source_round': 'jeff_2005_ketubot_list', 'review_key': f'2005#{n}',
                'expert_words': story['words'], 'coverage': round(cov, 3),
                'align_fraction': aligned['align_fraction'],
                'bracket_ratio': aligned['bracket_ratio'],
                'quote_polarity': 'include',   # his text IS the story, not a thing to remove
                'anchor_verified': False,
            })

    out = {
        '_comment': 'Sub-segment boundary targets derived from Jeff Rubenstein\'s 2005 '
                    'Ketubot story list by sequence-aligning his verbatim story text against '
                    'the Sefaria Hebrew. UNLIKE tests/expert_boundary_targets.json these are '
                    'NOT corrections — the list predates the detector by ~20 years, so it is a '
                    'neutral sample and can catch REGRESSIONS as well as known failures. '
                    'Filter on align_fraction / bracket_ratio; exact_clause_edge says whether '
                    'his boundary falls on a clause edge or inside a clause.',
        'source_doc': args.expert_doc, 'tractate': args.tractate,
        'thresholds': {'min_align_fraction': MIN_ALIGN_FRACTION,
                       'max_bracket_ratio': MAX_BRACKET_RATIO, 'min_block': MIN_BLOCK},
        'n_stories': len(expert), 'n_aligned': len(targets) // 2,
        'n_rejected': len(rejected), 'n_targets': len(targets),
        'targets': targets, 'rejected': rejected,
    }
    Path(PROJECT_ROOT / args.out).write_text(json.dumps(out, ensure_ascii=False, indent=1))

    edge = Counter(t['exact_clause_edge'] for t in targets)
    log.info('aligned %d/%d stories -> %d targets (%d rejected) -> %s',
             len(targets) // 2, len(expert), len(targets), len(rejected), args.out)
    log.info('boundary falls ON a clause edge: %d | INSIDE a clause: %d (%.0f%%)',
             edge[True], edge[False], 100 * edge[False] / max(len(targets), 1))
    log.info('by direction: %s', dict(Counter(t['direction'] for t in targets)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
