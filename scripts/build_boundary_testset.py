#!/usr/bin/env python3
"""
Build a sub-segment boundary test set from Jeff Rubenstein's past review notes.

WHY THIS EXISTS: Wave 5 changes where a story is trimmed *inside* a segment, but
until now the only sub-segment ground truth in use was 8 hand-picked cases from
one review round — not enough to measure anything (Lessons 9, 18).

In fact Jeff has stated boundaries in Hebrew across SEVEN review rounds spanning
both tractates, e.g.:
    "It should start with קָרִיבֵיהּ דְּרַבִּי יוֹחָנָן הֲוָה..."
    "the story should end with: אִי אִית בַּהּ שָׁוֶה פְּרוּטָה - אִין, אִי לָא - לָא."

KEY POINT — why pooling non-consecutive rounds is safe: those rounds ran on
different detector versions with different segment numbering, so matching by index
would be meaningless. Every note carries a Hebrew QUOTE, so we locate the boundary
by TEXT. Version drift becomes irrelevant, and rounds need not be consecutive.

KNOWN BIAS (state it whenever these numbers are reported): every target is a case
where Jeff found something WRONG. This measures "do we fix known failures", NOT
"do we break things that were already right." Pair it with the structural gate
(scripts/audit_text_spans.py, 100% coverage) and a RANDOM sample of currently-
correct stories to catch regressions.

Usage:
  python3 scripts/build_boundary_testset.py --out tests/expert_boundary_targets.json
"""
import argparse
import glob
import json
import logging
import os
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from src.story_detector_v11 import _split_into_clauses  # noqa: E402

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s [testset] %(message)s',
                    handlers=[logging.FileHandler(PROJECT_ROOT / 'project.log'),
                              logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)

NIKUD = re.compile(r'[֑-ׇ]')
HTML = re.compile(r'<[^>]+>')
HEB_RUN = re.compile(r'[֐-׿\s־"\'–—.,:;?!()\[\]]{12,}')
START_RE = re.compile(r'\b(should (begin|start)|starts? with|begins? with|start of the story|first (line|words|half))\b', re.I)
END_RE = re.compile(r'\b(should end|ends? with|continues? (with|through)|not part|last (line|words|few words)|next (line|paragraph|sentence)|through the next)\b', re.I)


def norm(s):
    return re.sub(r'[^א-ת]', '', HTML.sub('', NIKUD.sub('', s or '')))


def load_segments():
    """ref -> {index: hebrew} from every cached source we have."""
    segs = {}
    for path in glob.glob(str(PROJECT_ROOT / 'results/v10/wave4_notrim/*.json')):
        for page in json.loads(Path(path).read_text())['pages']:
            segs.setdefault(page['ref'], {}).update(
                {s['index']: s['hebrew'] for s in page.get('segments', [])})
    kid = PROJECT_ROOT / 'results/v7/kiddushin_pages.json'
    if kid.exists():
        for page in json.loads(kid.read_text()):
            segs.setdefault(page['ref'], {}).update(
                {s['index']: s['hebrew'] for s in page.get('segments', [])})
    return segs


def review_items(path):
    data = json.loads(Path(path).read_text())
    container = data.get('reviews') or data.get('feedback') or data
    if isinstance(container, dict):
        for key, val in container.items():
            if isinstance(val, dict):
                yield key, val
    elif isinstance(container, list):
        for val in container:
            if isinstance(val, dict):
                yield (val.get('page_ref') or val.get('ref') or '?'), val


def longest_hebrew_quote(note):
    cands = [c.strip() for c in HEB_RUN.findall(note)]
    cands = [c for c in cands if len(norm(c)) >= 12]
    return max(cands, key=lambda c: len(norm(c))) if cands else None


def page_ref_from(key, item):
    ref = item.get('page_ref')
    if ref:
        return ref
    m = re.match(r'^([A-Za-z ]+\d+[ab])', str(key))
    return m.group(1) if m else None


def locate(quote, segments):
    """Find (segment_index, clause_index, position) for a quoted boundary."""
    q = norm(quote)
    if len(q) < 12:
        return None
    for seg_idx, heb in sorted(segments.items()):
        flat = norm(heb)
        pos = flat.find(q[:60])           # prefix match tolerates trailing ellipsis
        if pos < 0:
            continue
        # map the normalized position back onto a clause
        clauses = _split_into_clauses(heb)
        acc = 0
        for ci, (a, b) in enumerate(clauses):
            n = len(norm(heb[a:b]))
            if acc + n > pos:
                return {'segment': seg_idx, 'clause': ci, 'n_clauses': len(clauses)}
            acc += n
    return None


def neighbours(ref):
    """The daf itself plus its neighbours.

    Jeff files a note under the story's page, but the boundary he quotes often
    sits on the adjacent daf — stories routinely straddle page breaks (it is the
    single largest error category in the taxonomy). Searching only the filed ref
    loses those, so widen by one amud in each direction.
    """
    m = re.match(r'^(.*?)(\d+)([ab])$', (ref or '').strip())
    if not m:
        return [ref]
    book, daf, amud = m.group(1), int(m.group(2)), m.group(3)
    seq = [(daf, 'a'), (daf, 'b')]
    order = [(daf - 1, 'a'), (daf - 1, 'b'), (daf, 'a'), (daf, 'b'), (daf + 1, 'a'), (daf + 1, 'b')]
    i = order.index((daf, amud))
    near = [order[i]] + [order[j] for j in (i + 1, i - 1, i + 2, i - 2) if 0 <= j < len(order)]
    return [f"{book}{d}{a}" for d, a in near]


def locate_near(quote, ref, segs):
    """Locate the quote on the filed daf, then on its neighbours."""
    for cand in neighbours(ref):
        hit = locate(quote, segs.get(cand, {}))
        if hit:
            hit['located_on'] = cand
            hit['cross_page'] = (cand != ref)
            return hit
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', default='tests/expert_boundary_targets.json')
    args = ap.parse_args()

    segs = load_segments()
    log.info('source pages loaded: %d', len(segs))

    targets, unresolved = [], []
    files = sorted(glob.glob(str(PROJECT_ROOT / 'validation/feedback/*.json'))) + \
            sorted(glob.glob(str(PROJECT_ROOT / 'jeff comms/*.json')))
    for path in files:
        for key, item in review_items(path):
            note = (item.get('notes') or item.get('note') or '').strip()
            if not note:
                continue
            direction = 'start' if START_RE.search(note) else ('end' if END_RE.search(note) else None)
            if not direction:
                continue
            quote = longest_hebrew_quote(note)
            if not quote:
                continue
            ref = page_ref_from(key, item)
            rec = {'ref': ref, 'direction': direction, 'quote': quote.strip(),
                   'note': note, 'source_round': os.path.basename(path), 'review_key': str(key)}
            hit = locate_near(quote, ref, segs) if ref else None
            if hit:
                rec.update(hit)
                targets.append(rec)
            else:
                unresolved.append(rec)

    out = {
        '_comment': 'Sub-segment boundary targets extracted from Jeff Rubenstein review '
                    'notes across all rounds. Located by Hebrew TEXT, not segment index, '
                    'so rounds from different detector versions pool safely. BIAS: every '
                    'target is a case Jeff flagged as wrong — measures fixing known '
                    'failures, not avoiding new ones. Pair with the structural gate and a '
                    'random sample of currently-correct stories.',
        'generated_from': [os.path.basename(f) for f in files],
        'n_targets': len(targets), 'n_unresolved': len(unresolved),
        'targets': targets, 'unresolved': unresolved,
    }
    Path(PROJECT_ROOT / args.out).write_text(json.dumps(out, ensure_ascii=False, indent=1))
    log.info('resolved %d targets, %d unresolved -> %s', len(targets), len(unresolved), args.out)

    from collections import Counter
    tr = Counter('Ketubot' if 'Ketubot' in (t['ref'] or '') else 'Kiddushin' for t in targets)
    log.info('by tractate: %s | by direction: %s', dict(tr),
             dict(Counter(t['direction'] for t in targets)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
