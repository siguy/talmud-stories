#!/usr/bin/env python3
"""
Fetch a tractate's full text from Sefaria and cache it — fetch only, no detector.

Prerequisite for measuring anything on a new tractate: an expert story list is
worth nothing until there is text to match it against.

Reuses the Sefaria client from `src/story_detector_v6.py` (byte-identical to the
copies in `scripts/run_kiddushin.py` and `scripts/run_ketubot_61_112.py`, but
importable without pulling in the detector or needing a Gemini key).

The daf range is DERIVED from Sefaria's own `/api/shape/` index, never guessed.
Getting the range wrong is the failure mode this task exists to prevent, so the
script also verifies that every reference in the expert's story list resolves to
a page that was actually fetched.

Output shape matches `results/v10/wave4_notrim/*.json`:
    {"tractate": ..., "pages": [{"ref": ..., "segments": [{index, english, hebrew}]}]}

Usage:
  python3 scripts/fetch_tractate_pages.py                      # all three new tractates
  python3 scripts/fetch_tractate_pages.py --tractates Gittin   # one
  python3 scripts/fetch_tractate_pages.py --verify-only        # re-run checks on cache
"""
import argparse
import json
import logging
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.story_detector_v6 import get_page_with_segments  # noqa: E402  (the existing client)
from scripts.measure_recall_vs_expert_list import (DAF_HEADER, gematria,  # noqa: E402
                                                   parse_expert_doc)

# `parse_expert_doc` only recognises single-amud headers ("סה ע\"ב"), so a story Jeff
# headed with a two-amud span ("סה ע\"ב-סו ע\"א") is silently attributed to the PREVIOUS
# daf. Checking coverage against the parser alone would therefore be partly vacuous —
# it cannot report a daf it never saw. This second pattern catches those spans so the
# range check sees every daf the document actually cites.
# A header for THIS tractate starts with the numeral; a parallel in another tractate is
# prefixed with its name ('ב"מ יח ע"ב'), so requiring a numeral at ^ excludes them.
SPAN_HEADER = re.compile(
    r'^([א-ת]{1,4})\s*ע["״]([אבגד])\s*[-–]\s*(?:([א-ת]{1,4})\s*)?ע["״]([אבגד])\s*$')

# force=True because the imported modules above call basicConfig first, which would
# otherwise tag this script's lines with their name in project.log.
logging.basicConfig(
    level=logging.INFO, force=True,
    format='%(asctime)s %(levelname)s [fetch] %(message)s',
    handlers=[logging.FileHandler(PROJECT_ROOT / 'project.log'), logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)

SEFARIA_SHAPE = "https://www.sefaria.org/api/shape"
OUT_DIR = PROJECT_ROOT / 'results' / 'sefaria'

# Jeff's detector-blind story lists, delivered 2026-08-30. Tractate -> doc path.
# Kept here rather than inferred: his filenames do not match Sefaria's spellings
# ("b. yebamot.doc" -> Yevamot), and that mapping is the whole point of the check.
EXPERT_DOCS = {
    'Gittin':  PROJECT_ROOT / 'jeff comms' / '8-30-2026' / 'b.gittin.doc',
    'Yevamot': PROJECT_ROOT / 'jeff comms' / '8-30-2026' / 'b. yebamot.doc',
    'Eruvin':  PROJECT_ROOT / 'jeff comms' / '8-30-2026' / 'eruvin.doc',
}
DEFAULT_TRACTATES = list(EXPERT_DOCS)


def cited_dapim(doc, tractate):
    """Every daf this document cites for `tractate`, including two-amud span headers.

    Returns (refs, span_headers). `refs` is what the range check must cover;
    `span_headers` are the lines `parse_expert_doc` mis-attributes, reported so the
    defect is visible rather than buried.
    """
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp:
        # Same conversion `parse_expert_doc` uses: macOS `textutil` reads legacy .doc.
        subprocess.run(['textutil', '-convert', 'txt', '-output', tmp.name, str(doc)], check=True)
        txt = Path(tmp.name)
    refs, spans = set(), []
    for line in (l.strip() for l in txt.read_text().split('\n')):
        plain = DAF_HEADER.match(line)
        if plain:
            daf = gematria(plain.group(1))
            if daf:
                refs.add(f"{tractate} {daf}{'a' if plain.group(2) == 'א' else 'b'}")
            continue
        span = SPAN_HEADER.match(line)
        if span:
            first, second = gematria(span.group(1)), gematria(span.group(3) or span.group(1))
            for daf, amud in ((first, span.group(2)), (second, span.group(4))):
                if daf:
                    # Amud gimel/dalet is a Yerushalmi convention with no Bavli equivalent;
                    # record the daf, and let the report flag the anomalous amud letter.
                    refs.add(f"{tractate} {daf}{'a' if amud in 'אג' else 'b'}")
            spans.append({'line': line, 'dapim': [first, second],
                          'anomalous_amud': span.group(2) in 'גד' or span.group(4) in 'גד'})
    return refs, spans


def amud_name(i):
    """Sefaria indexes Talmud amudim from 1a, so chapters[0] is '1a', [1] is '1b'."""
    return f"{i // 2 + 1}{'a' if i % 2 == 0 else 'b'}"


def get_shape(tractate):
    """Real daf range and per-amud segment counts, straight from Sefaria's index."""
    resp = requests.get(f"{SEFARIA_SHAPE}/{tractate}", timeout=15)
    resp.raise_for_status()
    chapters = resp.json()[0]['chapters']
    filled = [i for i, n in enumerate(chapters) if n]
    refs = [f"{tractate} {amud_name(i)}" for i in range(filled[0], filled[-1] + 1)]
    expected = {f"{tractate} {amud_name(i)}": chapters[i] for i in range(filled[0], filled[-1] + 1)}
    log.info('%s: Sefaria index gives %s to %s (%d amudim, %d segments expected)',
             tractate, amud_name(filled[0]), amud_name(filled[-1]), len(refs), sum(expected.values()))
    return refs, expected


def fetch(tractate, delay, force):
    """Fetch every amud, resuming from cache. Never re-fetches what is already cached."""
    out_path = OUT_DIR / f"{tractate.lower()}.json"
    refs, expected = get_shape(tractate)

    cached = {}
    if out_path.exists() and not force:
        for page in json.loads(out_path.read_text())['pages']:
            cached[page['ref']] = page
        log.info('%s: %d pages already cached in %s', tractate, len(cached), out_path.name)

    missing = [r for r in refs if r not in cached]
    if not missing:
        log.info('%s: cache complete, nothing to fetch', tractate)
    else:
        log.info('%s: fetching %d pages from Sefaria', tractate, len(missing))
        for n, ref in enumerate(missing, 1):
            page = get_page_with_segments(ref)
            if page and page['segments']:
                cached[ref] = page
            else:
                # A single bad page must not abort the tractate (CLAUDE.md code standards).
                log.warning('%s: EMPTY OR FAILED %s — continuing', tractate, ref)
            if n % 50 == 0:
                log.info('%s: %d/%d fetched', tractate, n, len(missing))
            time.sleep(delay)

    pages = [cached[r] for r in refs if r in cached]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({
        'tractate': tractate,
        'source': 'sefaria /api/texts',
        'fetched_at': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
        'daf_range': f"{refs[0].split()[-1]}-{refs[-1].split()[-1]}",
        'note': 'Text only — no detector has been run on this tractate.',
        'pages': pages,
    }, ensure_ascii=False), encoding='utf-8')

    n_segs = sum(len(p['segments']) for p in pages)
    log.info('%s: wrote %d pages / %d segments to %s', tractate, len(pages), n_segs, out_path)
    return pages, expected, out_path


def verify(tractate, pages, expected):
    """The point of the task: does every reference in Jeff's list resolve to a fetched page?"""
    fetched = {p['ref'] for p in pages}
    report = {'tractate': tractate, 'pages': len(pages),
              'segments': sum(len(p['segments']) for p in pages)}

    # 1. Every amud Sefaria says exists, we have.
    report['missing_amudim'] = sorted(set(expected) - fetched)

    # 2. Segment counts. A shortfall on a tractate-final page is the hadran (Hebrew-only
    #    closing formula, correctly dropped since it has no English). Anywhere else it
    #    would mean silent truncation, so both are surfaced rather than assumed benign.
    counts = {p['ref']: len(p['segments']) for p in pages}
    report['segment_count_diffs'] = {r: {'sefaria_index': expected[r], 'fetched': counts[r]}
                                     for r in counts if counts[r] != expected[r]}

    # 3. Expert-list coverage — the check the brief calls the point of the task.
    doc = EXPERT_DOCS.get(tractate)
    if doc and doc.exists():
        entries = parse_expert_doc(doc, tractate)
        parsed_refs = {e['ref'] for e in entries}
        # Union of what the parser saw and what it drops, so no cited daf escapes the check.
        all_refs, spans = cited_dapim(doc, tractate)
        all_refs |= parsed_refs
        order = lambda r: (int(re.search(r'(\d+)', r).group(1)), r[-1])
        unresolved = sorted((r for r in all_refs if r not in fetched), key=order)
        ordered = sorted(all_refs, key=order)
        report['expert_list'] = {
            'doc': doc.name, 'entries': len(entries), 'distinct_refs': len(ordered),
            'daf_span': f"{ordered[0].split()[-1]}-{ordered[-1].split()[-1]}" if ordered else None,
            'unresolved_refs': unresolved,
            'coverage': 'COMPLETE' if not unresolved else f'GAP: {len(unresolved)} refs not fetched',
            # Not a fetch problem, but a ground-truth problem the next brief must fix.
            'span_headers_misattributed_by_parser': spans,
        }
    else:
        report['expert_list'] = {'coverage': 'NO EXPERT DOC FOUND', 'doc': str(doc)}
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--tractates', nargs='+', default=DEFAULT_TRACTATES)
    ap.add_argument('--delay', type=float, default=0.3, help='seconds between Sefaria calls')
    ap.add_argument('--force', action='store_true', help='ignore cache and re-fetch')
    ap.add_argument('--verify-only', action='store_true', help='re-run checks against the cache')
    args = ap.parse_args()

    reports = []
    for tractate in args.tractates:
        if args.verify_only:
            path = OUT_DIR / f"{tractate.lower()}.json"
            pages = json.loads(path.read_text())['pages']
            _, expected = get_shape(tractate)
        else:
            pages, expected, _ = fetch(tractate, args.delay, args.force)
        reports.append(verify(tractate, pages, expected))

    print('\n' + '=' * 70)
    for r in reports:
        print(f"\n{r['tractate']}: {r['pages']} dapim, {r['segments']} segments")
        print(f"  missing amudim:      {r['missing_amudim'] or 'none'}")
        print(f"  segment count diffs: {r['segment_count_diffs'] or 'none'}")
        e = r['expert_list']
        print(f"  expert list ({e.get('doc')}): {e.get('entries')} entries / "
              f"{e.get('distinct_refs')} refs, span {e.get('daf_span')}")
        print(f"  REFERENCE COVERAGE:  {e['coverage']}")
        if e.get('unresolved_refs'):
            print(f"  UNRESOLVED:          {e['unresolved_refs']}")
        spans = e.get('span_headers_misattributed_by_parser') or []
        if spans:
            print(f"  caveat: {len(spans)} two-amud span headers are in range but "
                  f"parse_expert_doc attributes them to the preceding daf:")
            for s in spans:
                print(f"      {s['line']}{'   [amud gimel/dalet — not a Bavli form]' if s['anomalous_amud'] else ''}")
        log.info('%s verified: %d dapim, %d segments, coverage %s',
                 r['tractate'], r['pages'], r['segments'], e['coverage'])
    print('=' * 70)
    return 0 if all(not r['expert_list'].get('unresolved_refs') and not r['missing_amudim']
                    for r in reports) else 1


if __name__ == '__main__':
    sys.exit(main())
