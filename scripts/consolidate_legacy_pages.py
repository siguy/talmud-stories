#!/usr/bin/env python3
"""
Put a legacy tractate's pages and cached triage labels where the v11 runner looks.

Ketubot and Kiddushin predate the `results/sefaria/<tractate>.json` layout, so their
pages sit in files from earlier waves — Ketubot's 222 dapim across three, Kiddushin's
162 in one — and their triage caches likewise. This script merges them into the current
layout so `scripts/run_new_tractate.py --tractate <t>` can read them like any other.

**It never calls Sefaria.** Every page already on disk is copied verbatim; the golden's
segment indices are anchored to that text, and a re-fetch can renumber them silently.
The only fields carried over are `ref` and `segments` — `results/v5/*` also holds a
`stories` key, which is v5 *detector output* and has no business in a text cache.

Idempotent. `--check` verifies what is on disk and writes nothing; it is what the test
suite calls.

Usage:
  python3 scripts/consolidate_legacy_pages.py --tractate ketubot
  python3 scripts/consolidate_legacy_pages.py --tractate kiddushin --check
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

# Per tractate: where the pages are, where the triage is, and how many dapim there
# must be. `pages` entries are (path, key holding the list, or None if the file IS a list).
# EXPECTED is asserted, not inferred — a source file quietly losing a page would otherwise
# consolidate cleanly and show up later as a recall miss.
SOURCES = {
    'ketubot': {
        'name': 'Ketubot',
        'daf_range': '2a-112b',
        'pages': [('results/v5/pages_2-39.json', 'pages'),        # 76
                  ('results/v5/pages_40-60.json', 'pages'),       # 42
                  ('results/v7/ketubot_pages_61-112.json', None)],  # 104
        'triage': ['results/v7/event_triage_2-60.json',
                   'results/v7/event_triage_61-112.json'],
        'expected': 222,
    },
    'kiddushin': {
        'name': 'Kiddushin',
        'daf_range': '2a-82b',
        'pages': [('results/v7/kiddushin_pages.json', None)],
        'triage': ['results/v7/event_triage_kiddushin.json'],
        'expected': 162,
    },
}


def _load(rel, key):
    data = json.loads((PROJECT_ROOT / rel).read_text())
    return data[key] if key else data


def segment_digest(pages):
    """Hash of the text only, so a metadata change cannot mask a text change."""
    h = hashlib.sha256()
    for p in pages:
        h.update(p['ref'].encode())
        for s in p['segments']:
            h.update((s.get('hebrew') or '').encode())
            h.update((s.get('english') or '').encode())
    return h.hexdigest()


def collect_pages(spec):
    """Ordered, de-duplicated {ref, segments} across this tractate's sources."""
    pages, seen = [], {}
    for rel, key in spec['pages']:
        for p in _load(rel, key):
            ref = p['ref']
            if ref in seen:
                raise SystemExit(f'duplicate ref {ref!r}: {rel} and {seen[ref]}')
            seen[ref] = rel
            # ref + segments only. `stories` in the v5 files is detector output.
            pages.append({'ref': ref, 'segments': p['segments']})
    return pages


def collect_triage(spec):
    labels, seen = {}, {}
    for rel in spec['triage']:
        for ref, types in _load(rel, 'triage_results').items():
            if ref in seen:
                raise SystemExit(f'duplicate triage ref {ref!r}: {rel} and {seen[ref]}')
            seen[ref] = rel
            labels[ref] = types
    return labels


def build(tractate):
    spec = SOURCES[tractate]
    pages = collect_pages(spec)
    if len(pages) != spec['expected']:
        raise SystemExit(f'expected {spec["expected"]} pages, collected {len(pages)}')

    triage = collect_triage(spec)
    missing = [p['ref'] for p in pages if p['ref'] not in triage]
    extra = [r for r in triage if r not in {p['ref'] for p in pages}]
    if missing or extra:
        raise SystemExit(f'triage/page ref mismatch: {len(missing)} pages without '
                         f'labels {missing[:5]}, {len(extra)} labels without a page {extra[:5]}')

    # A label list longer than the page is a cache built against different text —
    # exactly the renumbering this script exists to avoid. Name it, never trim it.
    for p in pages:
        if len(triage[p['ref']]) > len(p['segments']):
            raise SystemExit(f'{p["ref"]}: {len(triage[p["ref"]])} triage labels for '
                             f'{len(p["segments"])} segments — caches disagree about the text')

    origins = ', '.join(rel for rel, _ in spec['pages'])
    pages_doc = {
        'tractate': spec['name'],
        'source': f'consolidated from {origins} — never re-fetched',
        'daf_range': spec['daf_range'],
        'note': ('Text only. Assembled by scripts/consolidate_legacy_pages.py from the '
                 'pages already on disk, because the golden\'s segment indices are '
                 'anchored to them. Do not replace this with a fresh Sefaria fetch.'),
        'segment_digest': segment_digest(pages),
        'pages': pages,
    }
    triage_doc = {
        'tractate': spec['name'],
        'model': 'v7_event_triage (cached; see the files named in `source`)',
        'source': ', '.join(spec['triage']),
        'note': 'Consolidated, not re-run. Labels are reused as-is.',
        'triage_results': triage,
    }
    return pages_doc, triage_doc


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--tractate', required=True, choices=sorted(SOURCES))
    ap.add_argument('--check', action='store_true',
                    help='verify what is on disk; write nothing')
    args = ap.parse_args()

    pages_doc, triage_doc = build(args.tractate)
    pages_path = PROJECT_ROOT / 'results' / 'sefaria' / f'{args.tractate}.json'
    triage_path = PROJECT_ROOT / 'results' / 'triage' / f'{args.tractate}.json'

    if args.check:
        problems = []
        for path, built in ((pages_path, pages_doc), (triage_path, triage_doc)):
            if not path.exists():
                problems.append(f'{path.relative_to(PROJECT_ROOT)} missing')
                continue
            on_disk = json.loads(path.read_text())
            if path == pages_path:
                if on_disk.get('segment_digest') != built['segment_digest']:
                    problems.append(f'{path.name}: segment digest differs from sources')
                if len(on_disk.get('pages', [])) != len(built['pages']):
                    problems.append(f'{path.name}: {len(on_disk.get("pages", []))} pages, '
                                    f'sources have {len(built["pages"])}')
            elif on_disk.get('triage_results') != built['triage_results']:
                problems.append(f'{path.name}: triage labels differ from sources')
        if problems:
            print('\n'.join(problems), file=sys.stderr)
            return 1
        print(f'ok — {len(pages_doc["pages"])} pages, '
              f'{len(triage_doc["triage_results"])} triage entries, '
              f'digest {pages_doc["segment_digest"][:12]}')
        return 0

    for path, doc in ((pages_path, pages_doc), (triage_path, triage_doc)):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(doc, ensure_ascii=False, indent=2))
        print(f'wrote {path.relative_to(PROJECT_ROOT)}')
    print(f'{len(pages_doc["pages"])} pages, digest {pages_doc["segment_digest"][:12]}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
