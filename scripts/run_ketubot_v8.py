#!/usr/bin/env python3
"""
Run v8 detector on the full Ketubot tractate (2-112) for Wave 1 regression test.

Reuses cached pages + triage from results/v7/. Output split to mirror v7 files:
  results/v8/ketubot_v8_2-60.json
  results/v8/ketubot_v8_61-112.json

Then scores against the canonical golden dataset and compares to v7 baseline
(0.9308 composite).
"""
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / '.env')

from src.event_triage import EventTriager
from src.ground_truth import GroundTruthDB, EventType
from src.story_detector_v8 import V7StoryDetector

MODEL = "gemini-3-flash-preview"
DELAY = 0.5

V7_DIR = PROJECT_ROOT / 'results' / 'v7'
V8_DIR = PROJECT_ROOT / 'results' / 'v8'
V8_DIR.mkdir(parents=True, exist_ok=True)

SEGMENTS = [
    {
        'pages_file': V7_DIR / 'ketubot_v7_2-60.json',
        'triage_file': V7_DIR / 'event_triage_2-60.json',
        'out_file': V8_DIR / 'ketubot_v8_2-60.json',
        'label': '2-60',
    },
    {
        'pages_file': V7_DIR / 'ketubot_pages_61-112.json',
        'triage_file': V7_DIR / 'event_triage_61-112.json',
        'out_file': V8_DIR / 'ketubot_v8_61-112.json',
        'label': '61-112',
    },
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


def build_db():
    feedback_path = PROJECT_ROOT / 'validation' / 'feedback' / \
        'v5_1_feedback_anonymous_2026-02-05 (1).json'
    v5_paths = [
        str(PROJECT_ROOT / 'results' / 'ketubot' / 'v5' / 'pages_2-39.json'),
        str(PROJECT_ROOT / 'results' / 'ketubot' / 'v5' / 'pages_40-60.json'),
    ]
    db = GroundTruthDB()
    if feedback_path.exists():
        db.load_from_feedback(str(feedback_path), v5_paths)
    return db


def main():
    db = build_db()
    print(f"Ground truth: {len(db.entries)} entries")

    detector = V7StoryDetector(ground_truth_db=db, model_name=MODEL)
    if not detector.client:
        sys.exit("ERROR: No API key. Set GOOGLE_API_KEY.")

    for seg in SEGMENTS:
        print('\n' + '=' * 60)
        print(f"  Ketubot {seg['label']} via v8")
        print('=' * 60)
        pages = load_pages(seg['pages_file'])
        triage_results = load_triage(seg['triage_file'])
        print(f"  {len(pages)} pages, {len(triage_results)} triage records")

        results = detector.run_pipeline(
            pages, triage_results=triage_results, delay=DELAY, tractate='Ketubot',
        )
        with open(seg['out_file'], 'w') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"  Saved: {seg['out_file']}")


if __name__ == '__main__':
    main()
