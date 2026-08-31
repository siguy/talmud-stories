#!/usr/bin/env python3
"""Build the best available ruler for Detection and Classification, per tractate.

WHY
---
Both of our goldens are built FROM detector output, so by construction neither can
contain a story we never proposed. That makes them usable for Classification (precision:
of what we proposed, how much did the expert accept) and useless for Detection (recall:
what did we never propose at all). Meanwhile Jeff's detector-blind lists can measure
recall but carry no verdicts.

Neither artifact alone is the ruler. This joins them:

    expert list (BLIND)  x  detector proposals  x  every verdict on disk

One entry per story, each stating what it can and cannot measure:

    expert_listed  + detector_proposed=false  -> a Detection miss. Invisible in the
                                                 golden, which is the whole problem.
    detector_proposed + a verdict             -> a Classification data point.
    both                                      -> both.

VERDICTS
--------
Verdicts come from six review rounds using four vocabularies. They are folded to one
question -- "did the expert accept this as a story?" -- and the mapping matters:

    correct, approve, reject_remove, adjust  -> accepted
    incorrect, confirm_remove                -> rejected

`adjust` is accepted on purpose. It means "this IS a story, the boundary is wrong",
which is a Boundaries failure, not a Classification one (FRAMEWORK sec.1). Counting it
against classification is how a boundary complaint becomes a fake precision problem.

For the same reason a rejection carries `objection_kind`, keyword-derived from the
expert's note and deliberately conservative: anything unclear stays `unclassified`
rather than being guessed into a bucket. Precision is reported twice -- all-causes and
classification-only -- and the gap between them is the point.

MATCHING
--------
Review keys are `Ketubot 3a_9-9` -- a page and a segment span from whichever run the
reviewer saw. Spans move between runs, so keys are matched exactly first, then by
segment overlap on the same page. Unmatched verdicts are counted, never dropped
silently.

Usage:
  python3 scripts/build_ruler.py --tractate Ketubot
  python3 scripts/build_ruler.py --tractate Kiddushin
  python3 scripts/build_ruler.py --tractate Ketubot --report
"""
import argparse
import importlib.util
import json
import logging
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [ruler] %(message)s',
    handlers=[logging.FileHandler(PROJECT_ROOT / 'project.log'), logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, PROJECT_ROOT / path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# The recall measurement's own aligner, so Detection stays comparable with the 96.0%
# already published for Ketubot (Lesson: same script, or the comparison is meaningless).
recall = _load('measure_recall', 'scripts/measure_recall_vs_expert_list.py')
kid = _load('parse_kiddushin_list', 'scripts/parse_kiddushin_list.py')

ACCEPTED = {'correct', 'approve', 'reject_remove', 'adjust'}
REJECTED = {'incorrect', 'confirm_remove'}
REVIEW_GLOBS = ['validation/feedback/*.json', 'jeff comms/*.json']
REVIEW_KEY = re.compile(r'^(.+?)_(\d+)-(\d+)$')

# Conservative note triage. Order matters: the first hit wins.
OBJECTION_RULES = [
    ('boundary', re.compile(r'boundar|should (also )?(be )?(includ|start|end|begin)|'
                            r'omit|should be cut|too (long|short)|extend|truncat|'
                            r'the story (starts|ends|begins)|more words|fewer words', re.I)),
    ('merge',    re.compile(r'\bmerge|two stories|separate stor|split|combin', re.I)),
    ('confidence', re.compile(r'low confidence|high confidence|confidence level|borderline', re.I)),
    ('classification', re.compile(r'not (really )?a story|no real narrative|halakhic|'
                                  r'not a narrative|legal (discussion|tradition)|'
                                  r'report/tradition|dialectic|is not a story', re.I)),
]

TRACTATES = {
    'Ketubot': {
        'expert_doc': 'jeff comms/b.ketubot (1).doc',
        'runs': ['results/v10/wave4_notrim/ketubot_v10_2-60_notrim.json',
                 'results/v10/wave4_notrim/ketubot_v10_61-112_notrim.json'],
        'golden': 'results/canonical/ketubot_canonical.json',
    },
    'Kiddushin': {
        'expert_json': 'results/expert_lists/kiddushin_2005.json',
        'runs': ['results/v10/wave4_notrim/kiddushin_v10_notrim.json'],
        'golden': 'results/canonical/kiddushin_canonical.json',
    },
}


def expert_stories(tractate, cfg):
    """Blind list entries: [{ref, text, blind}]. Never the old line-based parser."""
    if 'expert_json' in cfg:
        data = json.loads((PROJECT_ROOT / cfg['expert_json']).read_text())
        return [{'ref': s['ref'], 'text': s['text'], 'blind': s['blind'],
                 'not_blind_reason': None if s['blind'] else s['blind_basis']}
                for s in data['stories'] if not s['duplicate_of']]
    stories, _ = kid.parse(PROJECT_ROOT / cfg['expert_doc'], tractate)
    return [{'ref': s['ref'], 'text': s['text'], 'blind': True, 'not_blind_reason': None}
            for s in stories if not s['duplicate_of']]


def load_reviews(tractate):
    """Every verdict on disk for this tractate, keyed by (ref, start, end)."""
    out, rounds = defaultdict(list), Counter()
    for pattern in REVIEW_GLOBS:
        for path in sorted(PROJECT_ROOT.glob(pattern)):
            try:
                data = json.loads(path.read_text())
            except Exception:
                continue
            if not isinstance(data, dict):
                continue
            items = data.get('reviews') or data.get('feedback')
            if not isinstance(items, dict):
                continue
            for key, val in items.items():
                if not isinstance(val, dict) or not val.get('verdict'):
                    continue
                m = REVIEW_KEY.match(key)
                if not m or not m.group(1).startswith(tractate):
                    continue
                out[(m.group(1), int(m.group(2)), int(m.group(3)))].append({
                    'round': path.name, 'key': key, 'verdict': val['verdict'],
                    'note': (val.get('note') or val.get('notes') or '').strip()})
                rounds[path.name] += 1
    return out, rounds


def classify_objection(notes):
    for kind, pattern in OBJECTION_RULES:
        if any(pattern.search(n) for n in notes if n):
            return kind
    return 'unclassified'


def build(tractate, cfg):
    runs = [str(PROJECT_ROOT / r) for r in cfg['runs']]
    # load_detected returns a third value, `withheld` — the stories
    # filter_mishnah_only_stories() moved into `mishnah_stories`. The ruler's
    # `proposed` flag deliberately does NOT fold those in: "found then dropped"
    # and "never found" are different facts and must not be merged (Lesson 27).
    # measure_recall_vs_expert_list.py reports them separately.
    units, proposals, _withheld = recall.load_detected(runs)
    index = defaultdict(set)
    for i, (_, _, gs) in enumerate(units):
        for g in gs:
            index[g].add(i)

    reviews, rounds = load_reviews(tractate)
    log.info('%s: %d proposals on %d dapim; %d reviewed keys across %d rounds',
             tractate, sum(len(v) for v in proposals.values()), len(proposals),
             len(reviews), len(rounds))

    golden = defaultdict(list)
    for page in json.loads((PROJECT_ROOT / cfg['golden']).read_text())['pages']:
        golden[page['ref']] += [(s['start_segment'], s['end_segment']) for s in page.get('stories', [])]

    # ---- every detector proposal, with any verdicts attached --------------
    props = []
    for path in runs:
        for page in json.loads(Path(path).read_text())['pages']:
            for st in page.get('stories', []):
                span = (page['ref'], st['start_segment'], st['end_segment'])
                vs, match = list(reviews.get(span, [])), None
                if vs:
                    match = 'exact'
                else:                           # spans move between runs; try overlap
                    for (ref, lo, hi), cand in reviews.items():
                        if ref == page['ref'] and lo <= st['end_segment'] and st['start_segment'] <= hi:
                            vs += cand
                            match = 'overlap'
                accepted = None
                if vs:
                    accepted = any(v['verdict'] in ACCEPTED for v in vs) and \
                               not all(v['verdict'] in REJECTED for v in vs)
                props.append({
                    'span': span, 'classification': st.get('classification'),
                    'verdicts': vs, 'verdict_match': match, 'accepted': accepted,
                    'in_golden': any(lo <= st['start_segment'] <= hi
                                     for lo, hi in golden.get(page['ref'], [])),
                    'claimed_by': [],
                })

    # ---- one entry per expert story, however the proposals fall -------------
    # A proposal may be claimed by more than one expert story: that is our detector
    # merging two of his stories into one span, and it is worth keeping, not collapsing.
    entries = []
    for story in expert_stories(tractate, cfg):
        gs = recall.grams(story['text'])
        cov, lo, hi = recall.locate(gs, units, index)
        window = [(units[i][0], units[i][1]) for i in range(lo, hi + 1)] if lo is not None else []
        # `locate` returns a search window up to 14 segments wide, which is right for
        # deciding "did we propose anything here" but far too loose to say WHICH
        # proposal this story is. Narrow to the segments whose own text is actually
        # part of the story before linking.
        # A segment belongs to the story if either side is mostly the other: a story
        # spanning five segments puts ~20% of itself in each (so test segment-in-story),
        # while a fifteen-word story sits inside one long segment (so test
        # story-in-segment). Testing one direction only loses one case or the other.
        tight = [(units[i][0], units[i][1]) for i in range(lo, hi + 1)
                 if max(recall.overlap_frac(units[i][2], gs),
                        recall.overlap_frac(gs, units[i][2])) > 0.50] if lo is not None else []
        overlaps = lambda cells: [p for p in props
                                  if any(ref == p['span'][0] and p['span'][1] <= ix <= p['span'][2]
                                         for ref, ix in cells)]
        linked = overlaps(tight) or overlaps(window)
        strict = bool(overlaps(tight))
        eid = f'{tractate.lower()}_r{len(entries) + 1:03d}'
        for p in linked:
            p['claimed_by'].append(eid)
        vs = [v for p in linked for v in p['verdicts']]
        entries.append({
            'id': eid,
            'ref': window[0][0] if window else story['ref'],
            'expert_listed': True, 'expert_blind': story['blind'],
            'expert_text': story['text'], 'expert_coverage': round(cov, 3),
            'expert_located': window[:1] + window[-1:],
            'expert_segments': tight,
            'not_blind_reason': story['not_blind_reason'],
            'detector_proposed': bool(overlaps(window)),
            'detector_proposed_strict': strict,
            'detector_span': [list(p['span']) for p in linked] or None,
            'detector_classification': [p['classification'] for p in linked] or None,
            # Read from the GOLDEN, not from the proposals linked to this story.
            # This field used to be `any(p['in_golden'] for p in linked)`, which
            # asks "is a proposal of mine in the golden" -- so an expert story the
            # detector never proposed read False no matter what the golden held.
            # That was exactly backwards for the five stories added FROM Jeff's
            # blind 2005 list, which are in the golden BECAUSE we never proposed
            # them. Membership of the golden is a fact about the golden.
            'in_golden': any(lo <= ix <= hi for ref, ix in (tight or window)
                             for lo, hi in golden.get(ref, [])),
            'verdicts': vs,
            'verdict_match': next((p['verdict_match'] for p in linked if p['verdict_match']), None),
            # On his list IS his verdict that it is a story; a later note may still
            # reject the span we drew around it.
            'expert_accepted': True,
            'objection_kind': None,
        })

    # ---- proposals no expert story claimed: precision-only entries ----------
    for p in props:
        if p['claimed_by']:
            continue
        entries.append({
            'id': f'{tractate.lower()}_r{len(entries) + 1:03d}',
            'ref': p['span'][0],
            'expert_listed': False, 'expert_blind': None, 'expert_text': None,
            'detector_proposed': True, 'detector_span': [list(p['span'])],
            'detector_classification': [p['classification']],
            'in_golden': p['in_golden'],
            'verdicts': p['verdicts'], 'verdict_match': p['verdict_match'],
            'expert_accepted': p['accepted'],
            'objection_kind': (classify_objection([v['note'] for v in p['verdicts']])
                               if p['accepted'] is False else None),
        })
    log.info('%s: %d expert stories, %d proposals, %d proposals unclaimed',
             tractate, sum(1 for e in entries if e['expert_listed']), len(props),
             sum(1 for p in props if not p['claimed_by']))
    return entries, rounds, props


def metrics(entries, props):
    """Detection from the blind list; Classification from verdicts, per round.

    The two are kept apart on purpose. Being on Jeff's list is his judgment that a
    passage is a story, but it is not a verdict on the span *we* drew, so it cannot
    stand in for one when measuring precision.

    Precision is reported per round rather than pooled. Each round judged one detector
    version, and pooling them would average across versions and let whichever round has
    the most verdicts set the headline (Lesson 24).
    """
    blind = [e for e in entries if e['expert_listed'] and e['expert_blind']]
    found = [e for e in blind if e['detector_proposed']]

    per_round = {}
    for p in props:
        for v in p['verdicts']:
            r = per_round.setdefault(v['round'], {'accepted': 0, 'rejected': 0, 'by_kind': Counter()})
            if v['verdict'] in ACCEPTED:
                r['accepted'] += 1
            elif v['verdict'] in REJECTED:
                r['rejected'] += 1
                r['by_kind'][classify_objection([v['note']])] += 1
    for name, r in per_round.items():
        n = r['accepted'] + r['rejected']
        r['judged'] = n
        # LOWER bound: every rejection counted, whatever it objected to.
        r['precision_all_causes'] = round(r['accepted'] / n, 3) if n else None
        # UPPER bound: only rejections that dispute whether it is a story at all count
        # against Classification; boundary, merge and confidence objections belong to
        # other capabilities (FRAMEWORK sec.1). Notes we could not read fall here too,
        # which is what makes it an upper bound rather than the answer.
        not_class = n - r['accepted'] - r['by_kind'].get('classification', 0)
        r['precision_classification_only'] = round((r['accepted'] + not_class) / n, 3) if n else None
        r['unclassified_notes'] = r['by_kind'].get('unclassified', 0)
        r['bounds_note'] = ('true classification precision lies between these two; the gap '
                            f"is {r['by_kind'].get('unclassified', 0)} unreadable notes plus "
                            'the boundary/merge/confidence rejections')
        r['by_kind'] = dict(r['by_kind'])

    judged = [p for p in props if p['verdicts']]
    agree = [p for p in judged if p['claimed_by'] and p['accepted']]
    return {
        'detection': {
            'kind': 'BLIND', 'denominator': len(blind), 'found': len(found),
            'recall': round(len(found) / len(blind), 3) if blind else None,
            'recall_strict': round(sum(1 for e in blind if e.get('detector_proposed_strict'))
                                   / len(blind), 3) if blind else None,
            'missed': [e['ref'] for e in blind if not e['detector_proposed']],
            'missed_strict': [e['ref'] for e in blind
                              if e['detector_proposed'] and not e.get('detector_proposed_strict')],
            'note': 'recall uses the published window-overlap test so it stays comparable '
                    'with the 96.0% already reported. recall_strict requires a proposal to '
                    'overlap a segment the story actually occupies; the gap is stories we '
                    'are credited with only because something else on the page was proposed.',
        },
        'classification': {
            'kind': 'CIRCULAR',
            'proposals': len(props),
            'with_verdict': len(judged),
            'without_verdict': len(props) - len(judged),
            'per_round': per_round,
            'note': 'Precision per round, not pooled: each round judged a different '
                    'detector version. adjust/approve/reject_remove count as ACCEPTED.',
        },
        'cross_check': {
            'proposals_on_the_blind_list': len([p for p in props if p['claimed_by']]),
            'of_those_judged_and_accepted': len(agree),
            'proposals_claimed_by_more_than_one_expert_story': len(
                [p for p in props if len(p['claimed_by']) > 1]),
        },
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--tractate', required=True, choices=sorted(TRACTATES))
    ap.add_argument('--out')
    ap.add_argument('--report', action='store_true')
    args = ap.parse_args()

    cfg = TRACTATES[args.tractate]
    entries, rounds, props = build(args.tractate, cfg)
    m = metrics(entries, props)
    out = PROJECT_ROOT / (args.out or f'results/rulers/{args.tractate.lower()}_ruler.json')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        'tractate': args.tractate, 'built_by': 'scripts/build_ruler.py',
        'runs': cfg['runs'], 'golden': cfg['golden'],
        'review_rounds': dict(rounds),
        'verdict_mapping': {'accepted': sorted(ACCEPTED), 'rejected': sorted(REJECTED),
                            'note': 'adjust is ACCEPTED: it means the story is real and the '
                                    'boundary is wrong, which is a Boundaries failure'},
        'metrics': m, 'entries': entries}, ensure_ascii=False, indent=1))

    d, c = m['detection'], m['classification']
    log.info('DETECTION (BLIND)  recall %s = %d/%d  (strict %s)',
             d['recall'], d['found'], d['denominator'], d['recall_strict'])
    log.info('   misses: %s', ', '.join(d['missed']) or 'none')
    if d['missed_strict']:
        log.info('   credited only by page-level overlap (%d): %s',
                 len(d['missed_strict']), ', '.join(d['missed_strict'])) 
    log.info('CLASSIFICATION (CIRCULAR)  %d of %d proposals carry a verdict; precision is '
             'a RANGE - all-causes .. classification-only', c['with_verdict'], c['proposals'])
    for name, r in sorted(c['per_round'].items()):
        log.info('   %-44s n=%-4d precision %s..%s  %s',
                 name[:44], r['judged'], r['precision_all_causes'],
                 r['precision_classification_only'], r['by_kind'] or '')
    log.info('wrote %s (%d entries)', out, len(entries))

    if args.report:
        print(f"\ncross-check: {json.dumps(m['cross_check'], indent=1)}")


if __name__ == '__main__':
    main()
