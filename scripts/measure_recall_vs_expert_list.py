#!/usr/bin/env python3
"""
Measure TRUE recall against an expert's detector-blind story list.

This closes the circular-recall problem described in
docs/golden/workflow/approach_review_and_scaling_2026-07-06.md §3.1: the golden
datasets contain only stories the detector itself proposed, so they cannot see
systematic misses.

Ground truth: `jeff comms/b.ketubot (1).doc` — Jeff Rubenstein's Ketubot story
list, created 2005-02-02 (twenty years before this detector existed, therefore
genuinely detector-blind). Table columns: מיקום | טקסט | מקבילות | הערות
(location | text | parallels | notes).

Matching: Jeff's text is unvocalized and heavily abbreviated (א"ל, ר"ע) while
Sefaria's is vocalized and expanded, so word-level matching fails. This uses
Hebrew character 4-grams with an inverted index, and searches a sliding window
over the whole tractate in segment order — stories routinely start on the last
segment of one daf and finish on the next (e.g. R. Akiva at Ketubot 62b seg 14).

Usage:
  python3 scripts/measure_recall_vs_expert_list.py \
      --expert-doc "jeff comms/b.ketubot (1).doc" \
      --detected results/v10/wave4_notrim/ketubot_v10_2-60_notrim.json \
                 results/v10/wave4_notrim/ketubot_v10_61-112_notrim.json \
      --golden results/canonical/ketubot_canonical.json \
      --out results/recall/ketubot_jeff2005_matches.json
"""
import argparse
import json
import logging
import re
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [recall] %(message)s',
    handlers=[logging.FileHandler(PROJECT_ROOT / 'project.log'), logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)

NIKUD = re.compile(r'[֑-ׇ]')
HTML = re.compile(r'<[^>]+>')
GEMATRIA = {'א':1,'ב':2,'ג':3,'ד':4,'ה':5,'ו':6,'ז':7,'ח':8,'ט':9,'י':10,'כ':20,'ך':20,
            'ל':30,'מ':40,'ם':40,'נ':50,'ן':50,'ס':60,'ע':70,'פ':80,'ף':80,'צ':90,'ץ':90,'ק':100}
DAF_HEADER = re.compile(r'^([א-ת]{1,4})\s*ע["״\']?([אב])["״\']?\s*$')
CITATION = re.compile(r'(ירושלמי|תוספתא|בר["״]ר|מכילתא|ספרי|ספרא|אדר["״]נ|מדרש|פסיקתא|תנחומא)')
SUBREF = re.compile(r'ע["״][אב]|פ["״][א-ת]|ה["״][א-ת]')


def normalize(text):
    text = HTML.sub(' ', NIKUD.sub('', text))
    return re.sub(r'\s+', ' ', re.sub(r'[^א-ת ]', ' ', text)).strip()


def grams(text, n=4):
    flat = normalize(text).replace(' ', '')
    return {flat[i:i + n] for i in range(len(flat) - n + 1)}


def gematria(letters):
    letters = re.sub(r'["״\']', '', letters)
    return sum(GEMATRIA[c] for c in letters) if letters and all(c in GEMATRIA for c in letters) else None


def parse_expert_doc(path, tractate):
    """macOS `textutil` converts legacy .doc; returns [{ref, text, words}]."""
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp:
        subprocess.run(['textutil', '-convert', 'txt', '-output', tmp.name, str(path)], check=True)
        lines = [l.strip() for l in Path(tmp.name).read_text().split('\n')]

    stories, current = [], None
    for line in lines:
        header = DAF_HEADER.match(line)
        if header:
            daf = gematria(header.group(1))
            if daf:
                current = f"{tractate} {daf}{'a' if header.group(2) == 'א' else 'b'}"
                continue
        if not current or not line or len(line.split()) < 8:
            continue
        if CITATION.search(line) and SUBREF.search(line) and len(line.split()) <= 25:
            continue  # parallels column, not a story
        stories.append({'ref': current, 'text': line, 'words': len(line.split())})
    log.info('parsed %s: %d expert stories', Path(path).name, len(stories))
    return stories


def load_detected(paths):
    """Returns (units, spans, withheld).

    `withheld` holds the spans that `filter_mishnah_only_stories()` moved out of
    `stories` and into `mishnah_stories`. They are reported separately and never
    folded into the headline recall: a withheld story was found and then dropped
    on a scope judgement, which is not the same thing as never finding it, and
    the two must not be silently merged. Before this key was read, a withheld
    story was indistinguishable from a miss (see tasks/PLAN_wave6.md).
    """
    units, spans, withheld = [], defaultdict(list), defaultdict(list)
    for path in paths:
        for page in json.loads(Path(path).read_text())['pages']:
            spans[page['ref']] += [(s['start_segment'], s['end_segment']) for s in page.get('stories', [])]
            withheld[page['ref']] += [(s['start_segment'], s['end_segment'])
                                      for s in page.get('mishnah_stories', [])]
            units += [(page['ref'], s['index'], grams(s['hebrew'])) for s in page.get('segments', [])]
    daf = lambda ref: (int(re.search(r'(\d+)', ref).group(1)), 0 if ref.rstrip()[-1] == 'a' else 1)
    units.sort(key=lambda u: (daf(u[0]), u[1]))
    return units, spans, withheld


def locate(story_grams, units, index, max_window=14, seeds=12):
    """Best contiguous segment window covering the expert story."""
    votes = defaultdict(int)
    for g in story_grams:
        for i in index.get(g, ()):
            votes[i] += 1
    if not votes:
        return 0.0, None, None
    best = (0.0, None, None)
    for seed in sorted(votes, key=votes.get, reverse=True)[:seeds]:
        for start in range(max(0, seed - 6), seed + 1):
            acc = set()
            for end in range(start, min(start + max_window, len(units))):
                acc |= units[end][2]
                cov = len(story_grams & acc) / len(story_grams)
                if cov > best[0]:
                    best = (cov, start, end)
                if cov > 0.97:
                    break
    return best


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--expert-doc', required=True)
    ap.add_argument('--detected', nargs='+', required=True)
    ap.add_argument('--golden')
    ap.add_argument('--tractate', default='Ketubot')
    ap.add_argument('--out')
    args = ap.parse_args()

    expert = parse_expert_doc(args.expert_doc, args.tractate)
    units, detected, withheld = load_detected(args.detected)
    log.info('detector corpus: %d segments across %d dapim', len(units), len({u[0] for u in units}))

    golden = defaultdict(list)
    if args.golden:
        for page in json.loads(Path(args.golden).read_text())['pages']:
            golden[page['ref']] += [(s['start_segment'], s['end_segment']) for s in page.get('stories', [])]

    index = defaultdict(set)
    for i, (_, _, gs) in enumerate(units):
        for g in gs:
            index[g].add(i)

    rows = []
    for story in expert:
        gs = grams(story['text'])
        cov, start, end = locate(gs, units, index)
        window = [(units[i][0], units[i][1]) for i in range(start, end + 1)] if start is not None else []
        covered = lambda table: any(lo <= ix <= hi for ref, ix in window for lo, hi in table.get(ref, []))
        rows.append({**story, 'coverage': round(cov, 3), 'segments': len(window),
                     'located': window[:1] + window[-1:],
                     'in_detector': covered(detected),
                     'in_mishnah_filtered': covered(withheld),
                     'in_golden': covered(golden) if args.golden else None})

    found = [r for r in rows if r['in_detector']]
    unlocated = [r for r in rows if r['coverage'] < 0.6]
    log.info('RECALL vs expert list: %d/%d = %.1f%%  (unlocated in text: %d)',
             len(found), len(rows), 100 * len(found) / len(rows), len(unlocated))
    if args.golden:
        g = sum(1 for r in rows if r['in_golden'])
        log.info('GOLDEN coverage of expert list: %d/%d = %.1f%%', g, len(rows), 100 * g / len(rows))

    # The Mishnah-only filter deletes stories from `stories` after detection.
    # Report what it withheld rather than counting it either way.
    held = sum(len(v) for v in withheld.values())
    overlaps = [r for r in rows if r['in_mishnah_filtered']]
    unmatched = [r for r in overlaps if not r['in_detector']]
    log.info('MISHNAH FILTER withheld %d detected stories corpus-wide; %d expert stories overlap '
             'one, %d of those are otherwise undetected (NOT counted in the recall above)',
             held, len(overlaps), len(unmatched))
    for r in unmatched:
        # A located window runs up to `max_window` segments, so an overlap is a
        # lead, not proof: check the withheld story is the expert's story and not
        # a neighbour on the same daf (Ketubot 77a is exactly that trap).
        log.info('  CHECK %s (window %d segs, %s..%s): %s', r['ref'], r['segments'],
                 r['located'][0][1], r['located'][-1][1], r['text'][:70])
    for r in rows:
        if not r['in_detector']:
            log.info('  MISS %s: %s', r['ref'], r['text'][:80])
    if args.out:
        Path(args.out).write_text(json.dumps(rows, ensure_ascii=False, indent=1))
        log.info('wrote %s', args.out)


if __name__ == '__main__':
    main()
