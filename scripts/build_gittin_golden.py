#!/usr/bin/env python3
"""
Build the Gittin golden dataset.

Gittin is the first tractate whose golden is assembled from TWO kinds of expert
evidence, and the whole point of this script is that it never lets them blur:

  expert_verdict     — he was shown OUR span and said yes / borderline / no.
                       25 of these, from validation/feedback/gittin_axes_review_2026-09-02.json.
                       This is the strong label: it judges the passage AND our extent.

  expert_blind_list  — his 2005 list names a story, and one of our proposals overlaps
                       its own segments (the strict test, not the loose window).
                       This says "there is a story here". It does NOT say our extent is
                       right, and it was written twenty years before the span existed.

Every entry carries `label_source`, and nothing in this file is labelled by us. A
proposal with neither kind of evidence is NOT written as an entry -- it is counted in
`unlabelled_proposals` and named there. The invariant that buys:

    every story[] entry in the golden carries an expert label.

Ketubot's golden cannot say that, and the confusion it caused is Lesson 3's whole
subject. A `null` classification in a file called "golden" gets read as a label by the
next reader, and by the reader after that it is a fact.

The three of his stories that no proposal covers strictly go to `known_missing_stories`,
which is where the Ketubot and Kiddushin goldens already put theirs.

Usage:
  python3 scripts/build_gittin_golden.py --out results/canonical/gittin_canonical.json
"""

import argparse
import importlib.util
import json
import logging
import sys
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s [golden] %(message)s',
                    handlers=[logging.FileHandler(PROJECT_ROOT / 'project.log'),
                              logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)

_spec = importlib.util.spec_from_file_location(
    'recall', PROJECT_ROOT / 'scripts' / 'measure_recall_vs_expert_list.py')
recall = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(recall)

RUN = PROJECT_ROOT / 'results/v11/gittin/gittin_v11.json'
EXPERT = PROJECT_ROOT / 'results/expert_lists/gittin_2005.json'
VERDICTS = PROJECT_ROOT / 'validation/feedback/gittin_axes_review_2026-09-02.json'

# His three axis answers, in the vocabulary the goldens already speak. `borderline` is
# deliberately NOT folded into either side: he asked for contested cases to be kept and
# flagged (2026-07-06), and a golden that rounds them is the thing he declined.
VERDICT_TO_CLASSIFICATION = {'yes': 'YES', 'borderline': 'BORDERLINE', 'no': 'NOT_A_STORY'}


def load_run():
    """Pages, and every proposal on them keyed by (ref, start, end)."""
    data = json.loads(RUN.read_text())
    pages = data['pages'] if isinstance(data, dict) else data
    proposals = {}
    for page in pages:
        for story in page.get('stories', []):
            key = (page['ref'], story.get('start_segment'), story.get('end_segment'))
            proposals[key] = (page, story)
    return pages, proposals


def strict_matches(pages, expert_stories):
    """expert story id -> the proposal keys whose span overlaps its own segments.

    The SAME narrowing measure_strict_recall.py uses -- imported from the same module
    rather than re-implemented, because a golden built on a second, subtly different
    notion of "matched" would disagree with the recall figure and nothing would say why.
    """
    units, spans, *_ = recall.load_detected([str(RUN)])
    index = defaultdict(set)
    for i, (_, _, gs) in enumerate(units):
        for g in gs:
            index[g].add(i)

    by_ref = defaultdict(list)
    for page in pages:
        for story in page.get('stories', []):
            by_ref[page['ref']].append(
                (story.get('start_segment'), story.get('end_segment')))

    locate, fell_back = recall.make_locator('exact', units, index,
                                            recall.word_corpus([str(RUN)], units))
    out = {}
    for story in expert_stories:
        gs = recall.grams(story['text'])
        _, lo, hi = locate(story)
        if lo is None:
            out[story['id']] = []
            continue
        tight = [(units[i][0], units[i][1]) for i in range(lo, hi + 1)
                 if max(recall.overlap_frac(units[i][2], gs),
                        recall.overlap_frac(gs, units[i][2])) > 0.50]
        hits = []
        for ref, seg in tight:
            for a, b in by_ref.get(ref, []):
                if a is not None and b is not None and a <= seg <= b and (ref, a, b) not in hits:
                    hits.append((ref, a, b))
        out[story['id']] = hits
    if fell_back:
        log.warning('%d expert story/stories had no corpus-unique phrase and fell back to '
                    'the 4-gram aligner: %s', len(fell_back), ', '.join(map(str, fell_back)))
    return out


def build():
    pages, proposals = load_run()
    expert_stories = recall.load_expert_json(str(EXPERT), 'recall')
    verdicts = json.loads(VERDICTS.read_text())

    matches = strict_matches(pages, expert_stories)

    # ---- label pass 1: his verdicts. Strongest evidence, applied first, and it WINS.
    # He saw the span. A 2005 list entry that disagrees is a twenty-year-old note about
    # a passage; the verdict is a judgement about this proposal.
    labels = {}
    for key, v in verdicts['reviews'].items():
        k = (v['page_ref'], v['start_segment'], v['end_segment'])
        if k not in proposals:
            log.warning('verdict %s matches no proposal in the run -- skipped', key)
            continue
        labels[k] = {
            'classification': VERDICT_TO_CLASSIFICATION[v['is_story']],
            'label_source': 'expert_verdict',
            'expert_answer': v['is_story'],
            'expert_notes': v['notes'],
            'review_key': key,
            'review_date': verdicts['date'],
            'schema_version': verdicts['schema_version'],
            'detector_version': v['detector_version'],
            'applies_to': v['applies_to'],
            'classification_shown': v['classification_shown'],
        }

    # ---- label pass 2: his 2005 list. Weaker, and it never overwrites a verdict.
    missing = []
    for story in expert_stories:
        hits = matches[story['id']]
        if not hits:
            missing.append(story)
            continue
        for k in hits:
            if k in labels:
                continue          # a verdict already speaks for this span
            labels[k] = {
                'classification': 'YES',
                'label_source': 'expert_blind_list',
                'expert_list_id': story['id'],
                'expert_list_ref': story['ref'],
                'expert_list_text': story['text'],
                'label_means': ('his 2005 list names a story that this span overlaps. It '
                                'does NOT validate the extent -- no one has judged this '
                                'span.'),
            }

    # ---- assemble
    out_pages, entries, unlabelled = [], 0, []
    for page in pages:
        kept = []
        for story in page.get('stories', []):
            k = (page['ref'], story.get('start_segment'), story.get('end_segment'))
            if k not in labels:
                unlabelled.append({'ref': page['ref'],
                                   'start_segment': story.get('start_segment'),
                                   'end_segment': story.get('end_segment'),
                                   'detector_classification': story.get('classification')})
                continue
            entry = {'start_segment': story.get('start_segment'),
                     'end_segment': story.get('end_segment'),
                     'one_sentence_summary': story.get('one_sentence_summary'),
                     'detector_classification': story.get('classification'),
                     'corpus': 'talmud'}
            entry.update(labels[k])
            kept.append(entry)
            entries += 1
        out_pages.append({'ref': page['ref'], 'segments': page.get('segments', []),
                          'stories': kept,
                          'mishnah_stories': page.get('mishnah_stories', []),
                          'skipped_by_triage': page.get('skipped_by_triage', False)})

    dist = Counter(e['classification'] for pg in out_pages for e in pg['stories'])
    src = Counter(e['label_source'] for pg in out_pages for e in pg['stories'])

    return {
        'tractate': 'Gittin',
        'version': 'gittin_canonical_v1',
        'built': '2026-09-02',
        'source_run': str(RUN.relative_to(PROJECT_ROOT)),
        'expert_list': str(EXPERT.relative_to(PROJECT_ROOT)),
        'verdict_source': str(VERDICTS.relative_to(PROJECT_ROOT)),
        'verdict_date': verdicts['date'],
        'label_sources': dict(src),
        'classification_distribution': dict(dist),
        'recall_denominator': len(expert_stories),
        'unlabelled_proposals': unlabelled,
        'known_missing_stories': [
            {'id': s['id'], 'ref': s['ref'], 'text': s['text']} for s in missing],
        'how_to_read_this': [
            'BLIND. No Gittin material was in any prompt: the run predates the list being '
            'opened, and the verdicts came after.',
            'label_source is not decoration. expert_verdict judged THIS span. '
            'expert_blind_list only says a story is there -- the extent is unvalidated.',
            'BORDERLINE is neither accepted nor rejected. Do not round it. He asked for '
            'contested cases to be kept and flagged (2026-07-06).',
            'Every entry carries an expert label. Proposals with no expert evidence are '
            'in unlabelled_proposals, not in pages[].stories[].',
            'Count entries against entries and accepted against accepted, never one of '
            'each (STATE.md).',
        ],
        'pages': out_pages,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()

    golden = build()
    n_pages = len(golden['pages'])
    n_entries = sum(len(p['stories']) for p in golden['pages'])
    accepted = sum(1 for p in golden['pages'] for s in p['stories']
                   if s['classification'] not in ('NOT_A_STORY', 'BORDERLINE'))

    log.info('pages %d · entries %d · accepted %d', n_pages, n_entries, accepted)
    log.info('label sources: %s', golden['label_sources'])
    log.info('classifications: %s', golden['classification_distribution'])
    log.info('unlabelled proposals (NOT in the golden): %d', len(golden['unlabelled_proposals']))
    log.info('his stories no proposal covers strictly: %d', len(golden['known_missing_stories']))

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(golden, indent=2, ensure_ascii=False) + '\n')
    log.info('wrote %s', out)
    return 0


if __name__ == '__main__':
    sys.exit(main())
