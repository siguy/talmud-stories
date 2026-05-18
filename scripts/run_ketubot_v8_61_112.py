#!/usr/bin/env python3
"""Resume v8 run on Ketubot 61-112 only."""
import json, sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
from dotenv import load_dotenv
load_dotenv(ROOT / '.env')

from src.ground_truth import GroundTruthDB, EventType
from src.story_detector_v8 import V7StoryDetector

PAGES_FILE = ROOT / 'results' / 'v7' / 'ketubot_pages_61-112.json'
TRIAGE_FILE = ROOT / 'results' / 'v7' / 'event_triage_61-112.json'
OUT_FILE = ROOT / 'results' / 'v8' / 'ketubot_v8_61-112.json'


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
    fb = ROOT / 'validation' / 'feedback' / 'v5_1_feedback_anonymous_2026-02-05 (1).json'
    v5_paths = [
        str(ROOT / 'results' / 'ketubot' / 'v5' / 'pages_2-39.json'),
        str(ROOT / 'results' / 'ketubot' / 'v5' / 'pages_40-60.json'),
    ]
    db = GroundTruthDB()
    if fb.exists():
        db.load_from_feedback(str(fb), v5_paths)
    return db


def main():
    pages = load_pages(PAGES_FILE)
    triage = load_triage(TRIAGE_FILE)
    db = build_db()
    detector = V7StoryDetector(ground_truth_db=db, model_name='gemini-3-flash-preview')
    if not detector.client:
        sys.exit("No API key")
    print(f"Ketubot 61-112: {len(pages)} pages, ground truth {len(db.entries)}")
    results = detector.run_pipeline(pages, triage_results=triage, delay=0.5, tractate='Ketubot')
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Saved: {OUT_FILE}")


if __name__ == '__main__':
    main()
