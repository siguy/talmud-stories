#!/usr/bin/env python3
"""
Ground Truth DB: Jeff Rubenstein's 128 expert labels, structured with error types
and passage patterns for few-shot example generation.

Increment 1 of v7 hybrid pipeline.
"""

import json
import re
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class ErrorType(Enum):
    """Why the detector got this entry wrong (from Jeff's notes)."""
    LEGAL_MISIDENTIFICATION = "legal_misidentification"  # Legal discussion mistaken for story
    MISSED_STORY = "missed_story"                        # Real story missed
    BOUNDARY_ERROR = "boundary_error"                    # Story found but boundaries wrong
    CROSS_PAGE_BLEED = "cross_page_bleed"                # Cross-page merge pulled in non-story
    SELF_CHECK_PROMOTION = "self_check_promotion"        # Self-check promoted a weak passage
    NONE = "none"                                        # No error (Jeff said correct)


class PassagePattern(Enum):
    """What kind of passage this is (from text features)."""
    LEGAL_WITH_SETTING = "legal_with_setting"    # Legal debate with a narrative setting
    PURE_LEGAL = "pure_legal"                    # Pure legal discussion
    SHORT_DIALOGUE = "short_dialogue"            # Brief dialogue, few events
    EXTENDED_NARRATIVE = "extended_narrative"     # Multi-event story with causality
    CROSS_PAGE = "cross_page"                    # Story that spans page boundary
    FORMULAIC_STATEMENT = "formulaic_statement"  # Single formulaic statement


class EventType(Enum):
    """Segment-level event classification for Stage 1 triage."""
    NARRATIVE_EVENT = "NARRATIVE_EVENT"    # Something happens in the world
    VERBAL_ACT = "VERBAL_ACT"            # Speech act (saying, commanding)
    DELIBERATION = "DELIBERATION"        # Legal reasoning, hypothetical
    HABITUAL = "HABITUAL"                # Recurring practice, not specific event


class GroundTruthEntry:
    """A single entry in the ground truth database."""
    def __init__(self, key: str, verdict: Optional[str], note: str,
                 v5_cls: str, jeff_wants: str, error_type: ErrorType,
                 passage_pattern: Optional[PassagePattern] = None):
        self.key = key
        self.verdict = verdict
        self.note = note
        self.v5_cls = v5_cls
        self.jeff_wants = jeff_wants  # 'STORY', 'NOT_A_STORY', or 'SKIP'
        self.error_type = error_type
        self.passage_pattern = passage_pattern
        self.page_ref = None
        self.start_seg = None
        self.end_seg = None
        self._parse_key(key)

    def _parse_key(self, key: str):
        match = re.match(r'Ketubot (\d+[ab])_(\d+)-(\d+)', key)
        if match:
            self.page_ref = f'Ketubot {match.group(1)}'
            self.start_seg = int(match.group(2))
            self.end_seg = int(match.group(3))


def _is_story_positive(cls: str) -> bool:
    """Is this a positive story classification?"""
    return cls in ('YES', 'HIGH_CONFIDENCE', 'LOW_CONFIDENCE')


def _jeff_wanted(verdict: Optional[str], note: str, v5_cls: str) -> str:
    """Determine what Jeff wanted the classification to be."""
    if verdict == 'correct':
        return 'STORY' if _is_story_positive(v5_cls) else 'NOT_A_STORY'
    elif verdict == 'incorrect':
        return 'NOT_A_STORY' if _is_story_positive(v5_cls) else 'STORY'
    elif verdict is None:
        note_lower = (note or '').lower()
        if 'definitely a story' in note_lower or 'high confidence story' in note_lower:
            return 'STORY'
        return 'SKIP'
    return 'SKIP'


# --- Keyword sets for error tagging ---

_LEGAL_KEYWORDS = [
    'legal debate', 'legal discussion', 'legal ruling', 'legal case',
    'theoretical discussion', 'legal argument', 'legal reasoning',
    'not events', 'no events', 'no real events', 'not really an event',
    'just parts of a legal', 'not a story at all',
]

_BOUNDARY_KEYWORDS = [
    'boundaries', 'boundary', 'should end with', 'should start',
    'not part of the story', 'is not part of', 'same story as',
    'second half of the story', 'one long story',
    'should not be included', 'should not have the last',
]

_CROSS_PAGE_KEYWORDS = [
    'continues on the next page', 'next page of talmud',
    'previous page of talmud', 'continuation', 'begins with',
    'beginning of a story that continues',
    'story that continues on the next page',
    'finished on the next page',
]

_MISSED_STORY_KEYWORDS = [
    'definitely a story', 'this is a story', 'this too is a story',
    'there is causality', 'temporal progression', 'causal relationship',
    'multiple events', 'should be marked a borderline',
]


def tag_error_type(key: str, verdict: Optional[str], note: str,
                   v5_cls: str) -> ErrorType:
    """
    Determine error type from Jeff's notes. Rule-based.

    Only entries where Jeff marked 'incorrect' or null-with-note have errors.
    """
    if verdict == 'correct':
        return ErrorType.NONE

    if verdict is None:
        note_lower = (note or '').lower()
        if 'definitely a story' in note_lower or 'high confidence story' in note_lower:
            return ErrorType.MISSED_STORY
        return ErrorType.NONE  # No actionable info

    # verdict == 'incorrect'
    note_lower = (note or '').lower()
    is_story_in_v5 = _is_story_positive(v5_cls)

    # Check cross-page first (more specific)
    if any(kw in note_lower for kw in _CROSS_PAGE_KEYWORDS):
        if is_story_in_v5:
            return ErrorType.BOUNDARY_ERROR
        else:
            return ErrorType.CROSS_PAGE_BLEED

    # Check boundary errors
    if any(kw in note_lower for kw in _BOUNDARY_KEYWORDS):
        return ErrorType.BOUNDARY_ERROR

    # v5.1 said story but Jeff says not → legal misidentification
    if is_story_in_v5:
        if any(kw in note_lower for kw in _LEGAL_KEYWORDS):
            return ErrorType.LEGAL_MISIDENTIFICATION
        # Default for story→not_story: legal misidentification
        return ErrorType.LEGAL_MISIDENTIFICATION

    # v5.1 said not story but Jeff says it is → missed story
    if not is_story_in_v5:
        return ErrorType.MISSED_STORY

    return ErrorType.NONE


def tag_passage_pattern(key: str, note: str, v5_cls: str,
                        jeff_wants: str,
                        segments: Optional[List[Dict]] = None) -> PassagePattern:
    """
    Determine passage pattern from text features and Jeff's notes.
    """
    note_lower = (note or '').lower()

    # Cross-page patterns
    if any(kw in note_lower for kw in _CROSS_PAGE_KEYWORDS):
        return PassagePattern.CROSS_PAGE

    # Legal patterns (Jeff says it's legal)
    if any(kw in note_lower for kw in ['setting for the debate', 'legal debate',
                                        'setting', 'but it is just a debate']):
        return PassagePattern.LEGAL_WITH_SETTING
    if any(kw in note_lower for kw in ['legal discussion', 'legal ruling',
                                        'theoretical discussion', 'hypothetical',
                                        'legal case', 'not a story at all']):
        return PassagePattern.PURE_LEGAL

    # Story patterns
    if any(kw in note_lower for kw in ['multiple events', 'causal relationship',
                                        'temporal progression', 'causality']):
        return PassagePattern.EXTENDED_NARRATIVE
    if any(kw in note_lower for kw in ['borderline', 'one event', 'mainly dialogue',
                                        'mainly talk', 'mainly speech']):
        return PassagePattern.SHORT_DIALOGUE

    # Infer from classification
    if jeff_wants == 'NOT_A_STORY' and _is_story_positive(v5_cls):
        return PassagePattern.LEGAL_WITH_SETTING  # Default for false positives
    if jeff_wants == 'STORY' and not _is_story_positive(v5_cls):
        return PassagePattern.EXTENDED_NARRATIVE  # Default for false negatives

    # For correct entries with no note, infer from v5 classification
    if _is_story_positive(v5_cls):
        return PassagePattern.EXTENDED_NARRATIVE
    return PassagePattern.PURE_LEGAL


class GroundTruthDB:
    """
    Queryable database of Jeff's 128 expert labels with error types
    and passage patterns.
    """

    def __init__(self):
        self.entries: Dict[str, GroundTruthEntry] = {}
        self._v5_pages: List[Dict] = []
        self._segments_by_page: Dict[str, List[Dict]] = {}

    def load_from_feedback(self, feedback_path: str,
                           v5_results_paths: Optional[List[str]] = None):
        """Load Jeff's feedback JSON and optionally v5.1 results."""
        with open(feedback_path) as f:
            feedback_data = json.load(f)

        # Load v5.1 results for classification lookup
        v5_lookup = {}
        if v5_results_paths:
            for path in v5_results_paths:
                with open(path) as f:
                    data = json.load(f)
                    for page in data.get('pages', []):
                        ref = page.get('ref', '')
                        # Store segments for few-shot generation
                        self._segments_by_page[ref] = page.get('segments', [])
                        for story in page.get('stories', []):
                            page_id = ref.replace('Ketubot ', '')
                            k = f'Ketubot {page_id}_{story["start_segment"]}-{story["end_segment"]}'
                            v5_lookup[k] = story.get('classification', 'UNKNOWN')

        feedback = feedback_data.get('feedback', {})
        for key, entry in feedback.items():
            verdict = entry.get('verdict')
            note = entry.get('note', '')
            v5_cls = v5_lookup.get(key, 'UNKNOWN')

            jeff_wants = _jeff_wanted(verdict, note, v5_cls)
            error_type = tag_error_type(key, verdict, note, v5_cls)
            passage_pattern = tag_passage_pattern(key, note, v5_cls, jeff_wants)

            gt_entry = GroundTruthEntry(
                key=key,
                verdict=verdict,
                note=note,
                v5_cls=v5_cls,
                jeff_wants=jeff_wants,
                error_type=error_type,
                passage_pattern=passage_pattern,
            )
            self.entries[key] = gt_entry

    def get_entries_by_error_type(self, error_type: ErrorType) -> List[GroundTruthEntry]:
        """Get all entries with a specific error type."""
        return [e for e in self.entries.values() if e.error_type == error_type]

    def get_entries_by_pattern(self, pattern: PassagePattern) -> List[GroundTruthEntry]:
        """Get all entries with a specific passage pattern."""
        return [e for e in self.entries.values() if e.passage_pattern == pattern]

    def get_entries_by_verdict(self, verdict: Optional[str]) -> List[GroundTruthEntry]:
        """Get all entries with a specific verdict."""
        return [e for e in self.entries.values() if e.verdict == verdict]

    def get_segments_for_entry(self, entry: GroundTruthEntry) -> List[Dict]:
        """Get the text segments for a ground truth entry."""
        if not entry.page_ref:
            return []
        page_segments = self._segments_by_page.get(entry.page_ref, [])
        return [s for s in page_segments
                if entry.start_seg <= s.get('index', -1) <= entry.end_seg]

    def generate_few_shot_examples(self, stage: str,
                                   error_type: Optional[ErrorType] = None,
                                   n: int = 3) -> List[str]:
        """
        Generate few-shot examples for a specific pipeline stage.

        Stages:
        - 'event_triage': Examples showing event type classification
        - 'story_detection': Examples showing story vs not-story with reasoning
        - 'adversarial': Examples showing borderline cases with defender/challenger

        If error_type is provided, prioritizes examples of that error type.
        """
        examples = []

        if stage == 'event_triage':
            examples = self._generate_event_triage_examples(n)
        elif stage == 'story_detection':
            examples = self._generate_detection_examples(error_type, n)
        elif stage == 'adversarial':
            examples = self._generate_adversarial_examples(n)

        return examples

    def _generate_event_triage_examples(self, n: int) -> List[str]:
        """Generate examples for event triage stage."""
        examples = []

        # Example 1: Pure legal page (should skip)
        legal_entries = self.get_entries_by_pattern(PassagePattern.PURE_LEGAL)
        for entry in legal_entries[:1]:
            segments = self.get_segments_for_entry(entry)
            if segments:
                seg_text = self._format_segments_brief(segments[:3])
                examples.append(
                    f"EXAMPLE (Legal Discussion → SKIP PAGE):\n"
                    f"Page: {entry.page_ref}\n"
                    f"Segments:\n{seg_text}\n"
                    f"Event types: All DELIBERATION\n"
                    f"Decision: <2 NARRATIVE_EVENT → SKIP\n"
                    f"Jeff's note: \"{entry.note[:100]}\"" if entry.note else ""
                )

        # Example 2: Story-rich page (should NOT skip)
        story_entries = self.get_entries_by_pattern(PassagePattern.EXTENDED_NARRATIVE)
        for entry in story_entries[:1]:
            segments = self.get_segments_for_entry(entry)
            if segments:
                seg_text = self._format_segments_brief(segments[:3])
                examples.append(
                    f"EXAMPLE (Narrative → KEEP PAGE):\n"
                    f"Page: {entry.page_ref}\n"
                    f"Segments:\n{seg_text}\n"
                    f"Event types: NARRATIVE_EVENT, VERBAL_ACT, NARRATIVE_EVENT\n"
                    f"Decision: ≥2 NARRATIVE_EVENT → KEEP\n"
                    f"Jeff's note: \"{entry.note[:100]}\"" if entry.note else ""
                )

        # Example 3: Legal with setting (tricky — should skip)
        legal_setting = self.get_entries_by_pattern(PassagePattern.LEGAL_WITH_SETTING)
        for entry in legal_setting[:1]:
            segments = self.get_segments_for_entry(entry)
            if segments:
                seg_text = self._format_segments_brief(segments[:3])
                examples.append(
                    f"EXAMPLE (Legal with Setting → SKIP):\n"
                    f"Page: {entry.page_ref}\n"
                    f"Segments:\n{seg_text}\n"
                    f"Event types: VERBAL_ACT, DELIBERATION, DELIBERATION\n"
                    f"Decision: <2 NARRATIVE_EVENT → SKIP\n"
                    f"Jeff's note: \"{entry.note[:100]}\"" if entry.note else ""
                )

        return examples[:n]

    def _generate_detection_examples(self, error_type: Optional[ErrorType],
                                     n: int) -> List[str]:
        """Generate examples for story detection stage."""
        examples = []

        # Prioritize legal misidentification examples (the #1 error)
        legal_errors = self.get_entries_by_error_type(ErrorType.LEGAL_MISIDENTIFICATION)
        for entry in legal_errors[:2]:
            segments = self.get_segments_for_entry(entry)
            seg_text = self._format_segments_brief(segments[:3]) if segments else "(no segments)"
            examples.append(
                f"EXAMPLE (FALSE POSITIVE — Legal misidentified as story):\n"
                f"Key: {entry.key}\n"
                f"Segments:\n{seg_text}\n"
                f"v5.1 said: {entry.v5_cls} — WRONG\n"
                f"Jeff says: NOT_A_STORY\n"
                f"Jeff's note: \"{entry.note[:150]}\"\n"
                f"Lesson: Legal discussions with settings (a rabbi going somewhere, "
                f"or sitting before another rabbi) are NOT stories."
            )

        # Add a confirmed story example
        confirmed = [e for e in self.entries.values()
                     if e.jeff_wants == 'STORY' and e.verdict == 'correct'
                     and e.note and 'story' in e.note.lower()]
        for entry in confirmed[:1]:
            segments = self.get_segments_for_entry(entry)
            seg_text = self._format_segments_brief(segments[:3]) if segments else "(no segments)"
            examples.append(
                f"EXAMPLE (TRUE STORY — Confirmed by expert):\n"
                f"Key: {entry.key}\n"
                f"Segments:\n{seg_text}\n"
                f"Classification: {entry.v5_cls} — CORRECT\n"
                f"Jeff's note: \"{entry.note[:150]}\""
            )

        return examples[:n]

    def _generate_adversarial_examples(self, n: int) -> List[str]:
        """Generate examples for adversarial validation stage."""
        examples = []

        # Borderline cases where Jeff gave detailed reasoning
        borderline = [e for e in self.entries.values()
                      if e.note and 'borderline' in e.note.lower()]
        for entry in borderline[:n]:
            examples.append(
                f"BORDERLINE CASE:\n"
                f"Key: {entry.key}\n"
                f"v5.1: {entry.v5_cls}, Jeff wants: {entry.jeff_wants}\n"
                f"Jeff's reasoning: \"{entry.note[:200]}\""
            )

        return examples[:n]

    def _format_segments_brief(self, segments: List[Dict], max_chars: int = 120) -> str:
        """Format segments for few-shot examples (brief)."""
        lines = []
        for seg in segments:
            eng = seg.get('english', '')
            # Strip HTML tags
            eng = re.sub(r'<[^>]+>', '', eng)
            if len(eng) > max_chars:
                eng = eng[:max_chars] + "..."
            lines.append(f"  Seg {seg.get('index', '?')}: \"{eng}\"")
        return '\n'.join(lines)

    def summary(self) -> Dict:
        """Return a summary of the ground truth database."""
        error_counts = {}
        for et in ErrorType:
            count = len(self.get_entries_by_error_type(et))
            if count > 0:
                error_counts[et.value] = count

        pattern_counts = {}
        for pp in PassagePattern:
            count = len(self.get_entries_by_pattern(pp))
            if count > 0:
                pattern_counts[pp.value] = count

        total = len(self.entries)
        non_skip = len([e for e in self.entries.values() if e.jeff_wants != 'SKIP'])
        stories = len([e for e in self.entries.values() if e.jeff_wants == 'STORY'])
        not_stories = len([e for e in self.entries.values() if e.jeff_wants == 'NOT_A_STORY'])
        skipped = len([e for e in self.entries.values() if e.jeff_wants == 'SKIP'])

        return {
            'total_entries': total,
            'non_skip': non_skip,
            'stories': stories,
            'not_stories': not_stories,
            'skipped': skipped,
            'error_type_counts': error_counts,
            'passage_pattern_counts': pattern_counts,
        }
