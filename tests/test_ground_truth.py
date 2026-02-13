#!/usr/bin/env python3
"""
Tests for Ground Truth DB (Increment 1).

Verifies:
- All 128 entries loaded
- Error type distribution matches analysis
- Known entries have correct error types
- Few-shot example generation works
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ground_truth import (
    GroundTruthDB, ErrorType, PassagePattern, EventType,
    tag_error_type, _is_story_positive,
)


def get_db() -> GroundTruthDB:
    """Load the ground truth DB with real data."""
    project_root = Path(__file__).parent.parent
    feedback_path = str(project_root / 'validation' / 'feedback' /
                        'v5_1_feedback_anonymous_2026-02-05 (1).json')
    v5_paths = [
        str(project_root / 'results' / 'ketubot' / 'v5' / 'pages_2-39.json'),
        str(project_root / 'results' / 'ketubot' / 'v5' / 'pages_40-60.json'),
    ]
    db = GroundTruthDB()
    db.load_from_feedback(feedback_path, v5_paths)
    return db


def test_total_entries():
    """128 total entries loaded."""
    db = get_db()
    assert len(db.entries) == 128, f"Expected 128 entries, got {len(db.entries)}"
    print("PASS: 128 total entries loaded")


def test_verdict_distribution():
    """107 correct, 18 incorrect, 3 null."""
    db = get_db()
    correct = db.get_entries_by_verdict('correct')
    incorrect = db.get_entries_by_verdict('incorrect')
    null_entries = db.get_entries_by_verdict(None)

    assert len(correct) == 107, f"Expected 107 correct, got {len(correct)}"
    assert len(incorrect) == 18, f"Expected 18 incorrect, got {len(incorrect)}"
    assert len(null_entries) == 3, f"Expected 3 null, got {len(null_entries)}"
    print("PASS: Verdict distribution correct (107/18/3)")


def test_non_skip_count():
    """127 non-skip entries (128 total - 1 skip with no actionable note)."""
    db = get_db()
    non_skip = [e for e in db.entries.values() if e.jeff_wants != 'SKIP']
    assert len(non_skip) == 127, f"Expected 127 non-skip, got {len(non_skip)}"
    print("PASS: 127 non-skip entries")


def test_legal_misidentification_count():
    """At least 6 LEGAL_MISIDENTIFICATION errors (the dominant error type)."""
    db = get_db()
    legal_errors = db.get_entries_by_error_type(ErrorType.LEGAL_MISIDENTIFICATION)
    assert len(legal_errors) >= 6, (
        f"Expected ≥6 LEGAL_MISIDENTIFICATION, got {len(legal_errors)}"
    )
    print(f"PASS: {len(legal_errors)} LEGAL_MISIDENTIFICATION errors (≥6)")


def test_known_legal_misidentification():
    """Known legal misidentification entries tagged correctly."""
    db = get_db()

    known_legal = [
        'Ketubot 40b_11-11',  # "rabbis making legal arguments"
        'Ketubot 42b_8-8',    # "legal difficulty/resolution"
        'Ketubot 55a_7-7',    # "legal debate between academies"
        'Ketubot 56a_2-2',    # "legal debate with setting"
        'Ketubot 51b_7-9',    # "theoretical discussion"
        'Ketubot 52a_13-14',  # "no real events, legal"
    ]

    for key in known_legal:
        entry = db.entries.get(key)
        assert entry is not None, f"Entry {key} not found"
        assert entry.error_type == ErrorType.LEGAL_MISIDENTIFICATION, (
            f"{key}: expected LEGAL_MISIDENTIFICATION, got {entry.error_type}"
        )
    print(f"PASS: {len(known_legal)} known legal misidentification entries tagged correctly")


def test_known_missed_stories():
    """Known missed story entries tagged correctly."""
    db = get_db()

    known_missed = [
        'Ketubot 10b_1-1',   # "definitely a story, multiple events"
        'Ketubot 10b_3-3',   # "definitely a story, temporal progression"
        'Ketubot 10b_6-6',   # "causality and temporal progression"
        'Ketubot 50b_6-6',   # "borderline story, some change"
    ]

    for key in known_missed:
        entry = db.entries.get(key)
        assert entry is not None, f"Entry {key} not found"
        assert entry.error_type == ErrorType.MISSED_STORY, (
            f"{key}: expected MISSED_STORY, got {entry.error_type}"
        )
    print(f"PASS: {len(known_missed)} known missed story entries tagged correctly")


def test_null_with_story():
    """Null entries with 'definitely a story' tagged as MISSED_STORY."""
    db = get_db()

    entry = db.entries.get('Ketubot 10a_11-11')
    assert entry is not None
    assert entry.jeff_wants == 'STORY'
    assert entry.error_type == ErrorType.MISSED_STORY

    entry = db.entries.get('Ketubot 54a_20-20')
    assert entry is not None
    assert entry.jeff_wants == 'STORY'
    assert entry.error_type == ErrorType.MISSED_STORY

    print("PASS: Null entries with story notes tagged correctly")


def test_correct_entries_have_no_error():
    """All 'correct' entries have error_type NONE."""
    db = get_db()
    correct = db.get_entries_by_verdict('correct')
    for entry in correct:
        assert entry.error_type == ErrorType.NONE, (
            f"{entry.key}: correct entry has error_type {entry.error_type}"
        )
    print("PASS: All correct entries have error_type NONE")


def test_few_shot_event_triage():
    """generate_few_shot_examples('event_triage') returns formatted strings."""
    db = get_db()
    examples = db.generate_few_shot_examples('event_triage', n=3)
    assert len(examples) > 0, "Expected at least 1 event triage example"
    for ex in examples:
        assert isinstance(ex, str), f"Expected string, got {type(ex)}"
        assert len(ex) > 20, f"Example too short: {ex[:50]}"
    print(f"PASS: {len(examples)} event triage examples generated")


def test_few_shot_detection():
    """generate_few_shot_examples('story_detection') returns formatted strings."""
    db = get_db()
    examples = db.generate_few_shot_examples('story_detection', n=3)
    assert len(examples) > 0, "Expected at least 1 detection example"
    for ex in examples:
        assert isinstance(ex, str)
        assert 'LEGAL' in ex.upper() or 'STORY' in ex.upper() or 'EXAMPLE' in ex.upper()
    print(f"PASS: {len(examples)} detection examples generated")


def test_few_shot_adversarial():
    """generate_few_shot_examples('adversarial') returns formatted strings."""
    db = get_db()
    examples = db.generate_few_shot_examples('adversarial', n=3)
    assert len(examples) > 0, "Expected at least 1 adversarial example"
    print(f"PASS: {len(examples)} adversarial examples generated")


def test_summary():
    """summary() returns correct structure."""
    db = get_db()
    s = db.summary()
    assert s['total_entries'] == 128
    assert s['non_skip'] == 127
    assert s['stories'] + s['not_stories'] == s['non_skip']
    assert 'error_type_counts' in s
    assert 'passage_pattern_counts' in s
    print(f"PASS: Summary correct — {s['stories']} stories, {s['not_stories']} not_stories")


def test_error_type_distribution():
    """Print error type distribution for verification."""
    db = get_db()
    s = db.summary()
    print("\nError type distribution:")
    for et, count in sorted(s['error_type_counts'].items()):
        print(f"  {et}: {count}")
    print("\nPassage pattern distribution:")
    for pp, count in sorted(s['passage_pattern_counts'].items()):
        print(f"  {pp}: {count}")


if __name__ == '__main__':
    tests = [
        test_total_entries,
        test_verdict_distribution,
        test_non_skip_count,
        test_legal_misidentification_count,
        test_known_legal_misidentification,
        test_known_missed_stories,
        test_null_with_story,
        test_correct_entries_have_no_error,
        test_few_shot_event_triage,
        test_few_shot_detection,
        test_few_shot_adversarial,
        test_summary,
        test_error_type_distribution,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"FAIL: {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"ERROR: {test.__name__}: {e}")
            failed += 1

    print(f"\n{'=' * 50}")
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)}")
    if failed:
        sys.exit(1)
