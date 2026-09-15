#!/usr/bin/env python3
"""
Put Ketubot's pages and cached triage labels where the v11 runner looks for them.

Ketubot predates the `results/sefaria/<tractate>.json` layout, so its 222 dapim sit
in three files from two earlier waves, and its triage cache in two more. This script
merges them into the current layout so `scripts/run_new_tractate.py --tractate ketubot`
can read them like any other tractate.

**It never calls Sefaria.** Every page already on disk is copied verbatim; the golden's
segment indices are anchored to that text, and a re-fetch can renumber them silently.
The only fields carried over are `ref` and `segments` — `results/v5/*` also holds a
`stories` key, which is v5 *detector output* and has no business in a text cache.

Idempotent. `--check` verifies what is on disk and writes nothing; it is what the test
suite calls.

Usage:
  python3 scripts/consolidate_ketubot_pages.py            # write both files
  python3 scripts/consolidate_ketubot_pages.py --check    # verify, exit 1 on mismatch
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

# (path, key holding the page list or None if the file IS the list)
PAGE_SOURCES = [
    ('results/v5/pages_2-39.json', 'pages'),
    ('results/v5/pages_40-60.json', 'pages'),
    ('results/v7/ketubot_pages_61-112.json', None),
]
TRIAGE_SOURCES = [
    'results/v7/event_triage_2-60.json',
    'results/v7/event_triage_61-112.json',
]

PAGES_OUT = 'results/sefaria/ketubot.json'
TRIAGE_OUT = 'results/triage/ketubot.json'

EXPECTED_PAGES = 222  # 76 + 42 + 104


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


def collect_pages():
    """Ordered, de-duplicated {ref, segments} across the three sources."""
    pages, seen = [], {}
    for rel, key in PAGE_SOURCES:
        for p in _load(rel, key):
            ref = p['ref']
            if ref in seen:
                raise SystemExit(f'duplicate ref {ref!r}: {rel} and {seen[ref]}')
            seen[ref] = rel
            # ref + segments only. `stories` in the v5 files is detector output.
            pages.append({'ref': ref, 'segments': p['segments']})
    return pages


def collect_triage():
    labels, seen = {}, {}
    for rel in TRIAGE_SOURCES:
        for ref, types in _load(rel, 'triage_results').items():
            if ref in seen:
                raise SystemExit(f'duplicate triage ref {ref!r}: {rel} and {seen[ref]}')
            seen[ref] = rel
            labels[ref] = types
    return labels


def build():
    pages = collect_pages()
    if len(pages) != EXPECTED_PAGES:
        raise SystemExit(f'expected {EXPECTED_PAGES} pages, collected {len(pages)}')

    triage = collect_triage()
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

    pages_doc = {
        'tractate': 'Ketubot',
        'source': 'consolidated from results/v5/ and results/v7/ — never re-fetched',
        'consolidated_at': '2026-09-15',
        'daf_range': '2a-112b',
        'note': ('Text only. Assembled by scripts/consolidate_ketubot_pages.py from the '
                 'pages already on disk, because the golden\'s segment indices are '
                 'anchored to them. Do not replace this with a fresh Sefaria fetch.'),
        'segment_digest': segment_digest(pages),
        'pages': pages,
    }
    triage_doc = {
        'tractate': 'Ketubot',
        'model': 'v7_event_triage (cached; see results/v7/event_triage_*.json)',
        'note': 'Consolidated, not re-run. Labels are reused as-is.',
        'triage_results': triage,
    }
    return pages_doc, triage_doc


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--check', action='store_true',
                    help='verify what is on disk; write nothing')
    args = ap.parse_args()

    pages_doc, triage_doc = build()
    pages_path = PROJECT_ROOT / PAGES_OUT
    triage_path = PROJECT_ROOT / TRIAGE_OUT

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
