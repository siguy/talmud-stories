#!/usr/bin/env python3
"""
Wave 3 runner — re-runs the v9 detector on a tractate (or specific pages).

v9 = v8 + Stage 2 prompt changes (multi-story-per-page, embedded-story
few-shots, sharper not-a-story rules) + item 4 text-internal boundary
post-processor. Real LLM calls — gate per Lesson 11 applies.

Usage:
    # Full Kiddushin run
    python3 scripts/run_wave3.py --tractate kiddushin

    # Smoke test on specific pages (writes to a smoke output path)
    python3 scripts/run_wave3.py --tractate kiddushin --refs "Kiddushin 71a" \
        --output results/v9/smoke/kiddushin_71a.json

    # Full Ketubot 2-60
    python3 scripts/run_wave3.py --tractate ketubot --range 2-60

    # Full Ketubot 61-112
    python3 scripts/run_wave3.py --tractate ketubot --range 61-112
"""
import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / '.env')

from src.event_triage import EventTriager  # noqa
from src.ground_truth import GroundTruthDB, EventType
from src.story_detector_v9 import V7StoryDetector

MODEL = "gemini-3-flash-preview"
DELAY = 0.5

V7_DIR = PROJECT_ROOT / 'results' / 'v7'
V9_DIR = PROJECT_ROOT / 'results' / 'v9' / 'wave3'

TRACTATE_CONFIGS = {
    'kiddushin': {
        'pages_file': V7_DIR / 'kiddushin_pages.json',
        'triage_file': V7_DIR / 'event_triage_kiddushin.json',
        'default_out': V9_DIR / 'kiddushin_v9.json',
        'tractate_name': 'Kiddushin',
    },
    'ketubot-2-60': {
        'pages_file': V7_DIR / 'ketubot_v7_2-60.json',
        'triage_file': V7_DIR / 'event_triage_2-60.json',
        'default_out': V9_DIR / 'ketubot_v9_2-60.json',
        'tractate_name': 'Ketubot',
    },
    'ketubot-61-112': {
        'pages_file': V7_DIR / 'ketubot_pages_61-112.json',
        'triage_file': V7_DIR / 'event_triage_61-112.json',
        'default_out': V9_DIR / 'ketubot_v9_61-112.json',
        'tractate_name': 'Ketubot',
    },
}


def load_pages(path):
    with open(path) as f:
        data = json.load(f)
    pages = data['pages'] if isinstance(data, dict) and 'pages' in data else data
    return [{'ref': p['ref'], 'segments': p['segments']} for p in pages]


def load_triage(path):
    with open(path) as f:
        data = json.load(f)
    raw = data.get('triage_results', data)
    return {ref: [EventType(s) for s in evs] for ref, evs in raw.items()}


def build_db():
    feedback_path = PROJECT_ROOT / 'validation' / 'feedback' / \
        'v5_1_feedback_anonymous_2026-02-05 (1).json'
    v5_paths = [
        str(PROJECT_ROOT / 'results' / 'v5' / 'pages_2-39.json'),
        str(PROJECT_ROOT / 'results' / 'v5' / 'pages_40-60.json'),
    ]
    db = GroundTruthDB()
    if feedback_path.exists():
        db.load_from_feedback(str(feedback_path), v5_paths)
    return db


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tractate', required=True,
                    choices=['kiddushin', 'ketubot'])
    ap.add_argument('--range', help='Ketubot only: 2-60 or 61-112',
                    choices=['2-60', '61-112'])
    ap.add_argument('--refs', help='Comma-separated refs to filter to '
                    '(e.g. "Kiddushin 71a,Kiddushin 33a"). '
                    'For smoke tests.')
    ap.add_argument('--output', help='Override output path')
    args = ap.parse_args()

    if args.tractate == 'kiddushin':
        cfg_key = 'kiddushin'
    else:
        if not args.range:
            sys.exit("ERROR: --range required for Ketubot")
        cfg_key = f'ketubot-{args.range}'
    cfg = TRACTATE_CONFIGS[cfg_key]

    pages = load_pages(cfg['pages_file'])
    triage_results = load_triage(cfg['triage_file'])

    if args.refs:
        wanted = {r.strip() for r in args.refs.split(',')}
        pages = [p for p in pages if p['ref'] in wanted]
        triage_results = {k: v for k, v in triage_results.items() if k in wanted}
        missing = wanted - {p['ref'] for p in pages}
        if missing:
            sys.exit(f"ERROR: refs not in cache: {missing}")
        print(f"Smoke filter: {len(pages)} pages")

    out_path = Path(args.output) if args.output else cfg['default_out']
    out_path.parent.mkdir(parents=True, exist_ok=True)

    db = build_db()
    print(f"Ground truth: {len(db.entries)} entries")

    detector = V7StoryDetector(ground_truth_db=db, model_name=MODEL)
    if not detector.client:
        sys.exit("ERROR: No API key. Set GOOGLE_API_KEY.")

    print('=' * 60)
    print(f"  Wave 3 v9 run: {cfg['tractate_name']} ({len(pages)} pages)")
    print(f"  Detector: src.story_detector_v9")
    print(f"  Output: {out_path}")
    print('=' * 60)

    results = detector.run_pipeline(
        pages, triage_results=triage_results, delay=DELAY,
        tractate=cfg['tractate_name'],
    )

    with open(out_path, 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n  Saved: {out_path}")

    # Summary
    total = 0
    by_cls = {}
    cross = 0
    for p in results.get('pages', []):
        for s in p.get('stories', []):
            cls = s.get('classification', 'NOT_A_STORY')
            if cls == 'NOT_A_STORY':
                continue
            total += 1
            by_cls[cls] = by_cls.get(cls, 0) + 1
            if s.get('spans_pages'):
                cross += 1
    print(f"\n  Stories: {total} (cross-page: {cross})")
    for cls, n in sorted(by_cls.items()):
        print(f"    {cls}: {n}")


if __name__ == '__main__':
    main()
