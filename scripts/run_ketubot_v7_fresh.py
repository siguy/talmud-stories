#!/usr/bin/env python3
"""
Run v7 detector fresh on Ketubot to establish an apples-to-apples baseline
for the Wave 1 regression test (controls for LLM nondeterminism).
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
from dotenv import load_dotenv
load_dotenv(ROOT / '.env')

from src.ground_truth import GroundTruthDB, EventType
from src.story_detector_v7 import V7StoryDetector

V7_DIR = ROOT / 'results' / 'v7'
OUT_DIR = ROOT / 'results' / 'v7_fresh'
OUT_DIR.mkdir(parents=True, exist_ok=True)

SEGMENTS = [
    {'pages': V7_DIR / 'ketubot_v7_2-60.json',
     'triage': V7_DIR / 'event_triage_2-60.json',
     'out': OUT_DIR / 'ketubot_v7_2-60.json'},
    {'pages': V7_DIR / 'ketubot_pages_61-112.json',
     'triage': V7_DIR / 'event_triage_61-112.json',
     'out': OUT_DIR / 'ketubot_v7_61-112.json'},
]


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


def main():
    fb = ROOT / 'validation' / 'feedback' / 'v5_1_feedback_anonymous_2026-02-05 (1).json'
    v5_paths = [str(ROOT / 'results' / 'ketubot' / 'v5' / 'pages_2-39.json'),
                str(ROOT / 'results' / 'ketubot' / 'v5' / 'pages_40-60.json')]
    db = GroundTruthDB()
    if fb.exists():
        db.load_from_feedback(str(fb), v5_paths)
    detector = V7StoryDetector(ground_truth_db=db, model_name='gemini-3-flash-preview')
    if not detector.client:
        sys.exit("No API key")
    for seg in SEGMENTS:
        print(f"\n=== {seg['out'].name} ===")
        pages = load_pages(seg['pages'])
        triage = load_triage(seg['triage'])
        results = detector.run_pipeline(pages, triage_results=triage,
                                         delay=0.5, tractate='Ketubot')
        with open(seg['out'], 'w') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"Saved {seg['out']}")


if __name__ == '__main__':
    main()
