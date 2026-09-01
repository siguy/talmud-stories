#!/usr/bin/env python3
"""
Measure TRUE recall against an expert's detector-blind story list.

This closes the circular-recall problem described in
docs/findings/2026-07-06-approach-review-and-scaling.md §3.1: the golden
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
from collections import defaultdict, namedtuple
from pathlib import Path

Triage = namedtuple('Triage', 'examined skipped')

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


def overlap_frac(a, b):
    """Fraction of a's n-grams present in b. Added for scripts/build_ruler.py;
    the recall measurement itself does not use it and is unchanged."""
    return len(a & b) / len(a) if a else 0.0


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


def load_expert_json(path, which):
    """Read a pre-parsed expert list instead of re-parsing the source document.

    Use this, never `parse_expert_doc`, on the Kiddushin .doc: the line-based
    parser returns 105 entries there, 9 of them Jeff's English review comments
    relocated to the end of the file, where they inherit the last daf seen
    (Lesson 28). `scripts/parse_kiddushin_list.py` reads the OLE table instead
    and returns 95, each carrying its own provenance flags.

    Which entries form the denominator is a provenance question, not a filter
    detail — see docs/findings/2026-08-30-appendix-provenance-correction.md:

      recall  `counts_for_recall` — the 90 whose presence on the list cannot
              flatter us. Excludes the four appendix cases that are on the list
              *because we proposed them*; keeps 81b, which is there because he
              read a page we surfaced and found a story we had missed, so
              dropping it is what would inflate the number.
      blind   `blind` — the 89 he wrote with no output of ours in front of him.
      all     everything except the one duplicate (94).
    """
    keep = {'recall': lambda s: s['counts_for_recall'],
            'blind': lambda s: s['blind'],
            'all': lambda s: True}[which]
    data = json.loads(Path(path).read_text())
    stories = [{'id': s['id'], 'ref': s['ref'], 'text': s['text'], 'words': s['words'],
                'blind': s['blind'], 'in_appendix': s['in_appendix']}
               for s in data['stories'] if s['duplicate_of'] is None and keep(s)]
    log.info('loaded %s: %d of %d entries (--expert-filter %s)',
             Path(path).name, len(stories), len(data['stories']), which)
    return stories


def load_detected(paths):
    """Returns (units, spans, withheld, triage, rejected).

    `triage` is the shipped keep/skip decision per page, read from
    `skipped_by_triage`. That flag is the decision *after* the Wave 1 lexical
    override, which forces Stage 2 on a page holding a canonical story
    introducer whatever Stage 1 said — so it is the number that describes what
    the pipeline actually examined, and it is smaller than `triage_summary.skipped`.

    `rejected` and `accepted` partition `spans` by classification. Both stay
    inside `spans`, because Detection proposes and does not judge (FRAMEWORK
    §1.2); the split is reported separately so a Classification failure is never
    filed as a Detection miss (Lesson 30).

    `withheld` holds the spans that `filter_mishnah_only_stories()` moved out of
    `stories` and into `mishnah_stories`. They are reported separately and never
    folded into the headline recall: a withheld story was found and then dropped
    on a scope judgement, which is not the same thing as never finding it, and
    the two must not be silently merged. Before this key was read, a withheld
    story was indistinguishable from a miss (see docs/history/2026-08-29-PLAN-wave6-story-criteria.md).
    """
    units, spans, withheld = [], defaultdict(list), defaultdict(list)
    rejected, accepted = defaultdict(list), defaultdict(list)
    examined, skipped = set(), set()
    for path in paths:
        for page in json.loads(Path(path).read_text())['pages']:
            spans[page['ref']] += [(s['start_segment'], s['end_segment']) for s in page.get('stories', [])]
            for s in page.get('stories', []):
                table = rejected if s.get('classification') == 'NOT_A_STORY' else accepted
                table[page['ref']].append((s['start_segment'], s['end_segment']))
            withheld[page['ref']] += [(s['start_segment'], s['end_segment'])
                                      for s in page.get('mishnah_stories', [])]
            units += [(page['ref'], s['index'], grams(s['hebrew'])) for s in page.get('segments', [])]
            (skipped if page.get('skipped_by_triage') else examined).add(page['ref'])
    daf = lambda ref: (int(re.search(r'(\d+)', ref).group(1)), 0 if ref.rstrip()[-1] == 'a' else 1)
    units.sort(key=lambda u: (daf(u[0]), u[1]))
    return units, spans, withheld, Triage(examined, skipped), rejected, accepted


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



def cause_buckets(rows):
    """
    Split the MISSES by cause. Returns (missed, triage_lost, kept_missed).

    Both buckets are derived from `missed`, so they partition it by construction. The
    earlier version derived `triage_lost` from all rows — every story on an unexamined
    page, found or not — and compared it against a miss count derived from proposals.
    Those coincide only while a story on an unexamined page cannot be found, which stops
    being true the moment a detected file's proposals disagree with its own
    `skipped_by_triage` flags (the merged artifacts in results/v11/triage_recall/ do
    exactly that, by design). It then printed splits like "3 misses: 4 ... 2 ...".

    This line is the only place the pipeline attributes a miss to Triage rather than
    Detection, so a split that does not cover the misses sends the fix to the wrong
    capability (Lesson 35).
    """
    missed = [r for r in rows if not r['in_detector']]
    triage_lost = [r for r in missed if not r['survived_triage']]
    kept_missed = [r for r in missed if r['survived_triage']]
    assert len(triage_lost) + len(kept_missed) == len(missed), (
        "miss-cause buckets are not a partition — they are derived from `missed`, so "
        "this can only fire if the derivation above was edited")
    return missed, triage_lost, kept_missed


def flags_disagreeing_with_proposals(rows):
    """
    Stories FOUND on a page the detected file flags `skipped_by_triage`.

    Legitimate for the merged measurement artifacts, which override the skip decision on
    purpose. Not legitimate silently: while any exist, the triage-vs-detection attribution
    describes the shipped skip decision and not the run in front of you. Reported, never
    swallowed (Lesson 38 — absence is quiet).
    """
    return [r for r in rows if r['in_detector'] and not r['survived_triage']]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    source = ap.add_mutually_exclusive_group(required=True)
    source.add_argument('--expert-doc', help='parse the .doc directly (Ketubot)')
    source.add_argument('--expert-json', help='pre-parsed list (Kiddushin — see load_expert_json)')
    ap.add_argument('--expert-filter', default='recall', choices=['recall', 'blind', 'all'],
                    help='which entries form the denominator; --expert-json only')
    ap.add_argument('--detected', nargs='+', required=True)
    ap.add_argument('--golden')
    ap.add_argument('--tractate', default='Ketubot')
    ap.add_argument('--out')
    args = ap.parse_args()

    expert = (parse_expert_doc(args.expert_doc, args.tractate) if args.expert_doc
              else load_expert_json(args.expert_json, args.expert_filter))
    units, detected, withheld, triage, rejected, accepted = load_detected(args.detected)
    pages = len(triage.examined) + len(triage.skipped)
    log.info('detector corpus: %d segments across %d dapim; triage examined %d/%d pages (%.0f%%)',
             len(units), len({u[0] for u in units}), len(triage.examined), pages,
             100 * len(triage.examined) / pages)

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
        pages_touched = sorted({ref for ref, _ in window})
        rows.append({**story, 'coverage': round(cov, 3), 'segments': len(window),
                     'located': window[:1] + window[-1:],
                     'pages_touched': pages_touched,
                     'survived_triage': any(ref in triage.examined for ref in pages_touched),
                     'in_detector': covered(detected),
                     'only_rejected': covered(rejected) and not covered(accepted),
                     'in_mishnah_filtered': covered(withheld),
                     'in_golden': covered(golden) if args.golden else None})

    found = [r for r in rows if r['in_detector']]
    unlocated = [r for r in rows if r['coverage'] < 0.6]
    log.info('RECALL vs expert list: %d/%d = %.1f%%  (unlocated in text: %d)',
             len(found), len(rows), 100 * len(found) / len(rows), len(unlocated))

    # Triage and Detection are separate capabilities and compose (FRAMEWORK §2b):
    #   triage recall x detection-given-triage = the end-to-end figure above.
    # A story lost to triage sits on pages that were never examined, so no Stage 2
    # prompt could have reached it; filing it as a Detection miss hides where the
    # fix belongs. Same reason `only_rejected` is pulled out: proposed-then-rejected
    # is Classification (FRAMEWORK §1.2, Lesson 30).
    survived = [r for r in rows if r['survived_triage']]
    triage_lost_all = [r for r in rows if not r['survived_triage']]
    missed, triage_lost, kept_missed = cause_buckets(rows)
    log.info('TRIAGE recall: %d/%d = %.1f%%  while examining %d/%d pages (%.0f%%); %d lost outright',
             len(survived), len(rows), 100 * len(survived) / len(rows),
             len(triage.examined), pages, 100 * len(triage.examined) / pages, len(triage_lost_all))
    log.info('DETECTION recall given the page survived triage: %d/%d = %.1f%%',
             len(survived) - len(kept_missed), len(survived),
             100 * (len(survived) - len(kept_missed)) / len(survived) if survived else 0.0)
    log.info('CAUSE of the %d misses: %d triage discarded the page, %d page examined and '
             'nothing proposed in range', len(missed), len(triage_lost), len(kept_missed))

    # A found story on a page flagged unexamined means this file's skip flags and its
    # proposals describe different runs. Warn and name it: the Triage/Detection split
    # above then describes the SHIPPED skip decision, not the file in front of you.
    contradicting = flags_disagreeing_with_proposals(rows)
    if contradicting:
        log.warning('%d story/stories are FOUND on pages this file still flags '
                    'skipped_by_triage (e.g. %s). Expected for the merged artifacts in '
                    'results/v11/triage_recall/, which override the skip decision on '
                    'purpose. While it holds, the TRIAGE and DETECTION lines above '
                    'describe the SHIPPED skip decision, not this run; the RECALL line '
                    'is unaffected.',
                    len(contradicting),
                    ', '.join(r['ref'] for r in contradicting[:3]))
    only_rejected = [r for r in found if r['only_rejected']]
    log.info('CLASSIFICATION, reported apart: %d located stories are covered ONLY by a span '
             'this run classified NOT_A_STORY — counted as FOUND above, because Detection '
             'proposes and does not judge', len(only_rejected))
    for r in only_rejected:
        log.info('  REJECTED %s: %s', r['ref'], r['text'][:80])
    for r in triage_lost_all:
        log.info('  TRIAGE-LOST %s (pages %s): %s', r['ref'], ','.join(r['pages_touched']), r['text'][:70])
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
