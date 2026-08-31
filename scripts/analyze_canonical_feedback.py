#!/usr/bin/env python3
"""
Analyze ALL of Jeff Rubenstein's canonical review feedback.

Produces a comprehensive machine-readable analysis that:
1. Catalogues every one of Jeff's 187 reviews
2. Cross-references against prior feedback rounds (v5.1, v8_delta)
3. Identifies consistency/contradictions between feedback rounds
4. Classifies each correction by type and error pattern
5. Extracts generalizable lessons for other tractates
6. Maps boundary corrections to specific Hebrew text markers

Output: docs/golden/v7/canonical_feedback_analysis.json

This analysis is the FOUNDATION for:
- Building the golden Ketubot dataset
- Creating the autoresearch evaluation metric
- Generating few-shot examples for the detector
- Training better boundary detection
"""

import json
import re
from pathlib import Path
from collections import Counter

PROJECT_ROOT = Path(__file__).parent.parent

# Input paths
CANONICAL_REVIEW = PROJECT_ROOT / 'validation' / 'feedback' / 'canonical_review_anonymous_2026-03-17.json'
CANONICAL_FILE = PROJECT_ROOT / 'results' / 'canonical' / 'ketubot_canonical.json'
PRIOR_FEEDBACK_FILES = [
    PROJECT_ROOT / 'validation' / 'feedback' / 'v5_1_feedback_anonymous_2026-02-05 (1).json',
    PROJECT_ROOT / 'validation' / 'feedback' / 'v5_1_feedback_anonymous_2026-02-20.json',
    PROJECT_ROOT / 'validation' / 'feedback' / 'v8_delta_feedback_anonymous_2026-02-26.json',
]
OUTPUT_PATH = PROJECT_ROOT / 'docs' / 'golden' / 'canonical_feedback_analysis.json'


# ---------- Error Pattern Classification ----------

# These are the systematic error patterns Jeff's feedback reveals.
# Each maps to specific detector improvements.

ERROR_PATTERNS = {
    'LEGAL_FALSE_POSITIVE': {
        'description': 'Legal discussion/hypothetical scenario incorrectly classified as a story',
        'subtypes': {
            'pure_legal_discussion': 'Pure legal debate with no narrative events',
            'hypothetical_case': 'Hypothetical legal scenario, not a real event',
            'legal_with_setting': 'Legal debate that has a narrative setting but is still not a story',
            'reference_to_story': 'Reference to a story that happened elsewhere, not a story itself',
            'single_action_plus_ruling': 'One action followed by a legal ruling — insufficient for story',
            'dialogue_only': 'Dialogue/speech acts only — asking, objecting, explaining are not events',
        },
        'jeff_language_markers': [
            'just a legal discussion', 'not a story', 'hypothetical',
            'legal debate', 'no real events', 'not really an event',
            'dialogue, not really an action', 'legal case', 'just one event',
            'just the report', 'not even a story', 'legal ruling',
        ],
        'detector_fix': 'Strengthen legal discussion disqualifier in Stage 2 prompt; add few-shot examples of legal-with-setting false positives',
    },
    'BOUNDARY_OVEREXTENSION': {
        'description': 'Story boundary includes Talmud meta-commentary that is not part of the story',
        'subtypes': {
            'gemara_comment': "Gemara's analytical comment on the story included in boundary",
            'gemara_question': "Gemara's follow-up question about the story included",
            'legal_discussion_after_story': "Legal discussion triggered by the story but not part of it",
            'talmud_rejection': "Talmud's rejection of a proof from the story included",
        },
        'jeff_language_markers': [
            "Talmud's comment", "Talmud's question", "not part of the story",
            "should not be included", "should be omitted", "legal discussion following",
            "need not be quoted", "Gemara's comment", "follow-up question",
        ],
        'detector_fix': 'Add boundary trimming rule: after narrative arc resolves, trim Talmud analytical commentary. Look for structural markers (הֵיכִי, מַאי, questions about the story).',
    },
    'BOUNDARY_UNDEREXTENSION': {
        'description': 'Story starts earlier or ends later than detected',
        'subtypes': {
            'missing_start_previous_page': 'Story begins on the prior Talmud page',
            'missing_start_same_page': 'Story begins earlier in the same page than detected',
            'missing_end_same_page': 'Story continues further on the same page',
            'missing_end_next_page': 'Story continues onto the next Talmud page',
        },
        'jeff_language_markers': [
            'first line is missing', 'should start with', 'begins with the previous',
            'continues on the next page', 'continuation', 'next paragraph should be included',
            'should also be included', 'first half of the story is not quoted',
        ],
        'detector_fix': 'Improve cross-page continuation detection; check segment 0 of next page and last segments of previous page for narrative continuity.',
    },
    'CONFIDENCE_MISCALIBRATION': {
        'description': 'Classification confidence level is wrong (HIGH should be LOW or vice versa)',
        'subtypes': {
            'habitual_as_high': 'Habitual/repeated actions classified as HIGH instead of LOW',
            'minimal_causality': 'Events without causality classified too high',
            'should_promote': 'Story with sufficient narrative elements classified too low',
        },
        'jeff_language_markers': [
            'low confidence', 'borderline', 'should be high',
            'no causality', 'no real causality', 'would do, repeatedly',
            'one event', 'mainly dialogue',
        ],
        'detector_fix': 'Calibrate confidence thresholds: require causality for HIGH_CONFIDENCE; habitual/repeated actions default to LOW_CONFIDENCE.',
    },
    'MERGE_NEEDED': {
        'description': 'Separate story entries should be combined into one',
        'subtypes': {
            'same_page_continuation': 'Two entries on the same page are one story',
            'cross_page_continuation': 'Story spans a page boundary and needs merging',
            'part_of_longer_narrative': 'Story is part of a larger narrative cycle',
        },
        'jeff_language_markers': [
            'should be merged', 'continuation of', 'second part of',
            'one long story', 'same story', 'part of a longer story',
            'should go with',
        ],
        'detector_fix': 'Improve cross-page stitching; check if adjacent stories share characters and narrative arc.',
    },
    'MERGE_INCORRECT': {
        'description': 'Cross-page merge was done but included wrong segments',
        'subtypes': {
            'wrong_segments_on_next_page': 'Merged with wrong portion of next page',
            'missed_continuation': 'Merge skipped intermediate text',
            'separate_stories_merged': 'Two independent stories incorrectly combined',
        },
        'jeff_language_markers': [
            'merge is not correct', 'merge is incorrect', 'not accurate',
            'was skipped', 'top lines', 'should have been included',
            'is a separate story', 'independent story',
        ],
        'detector_fix': 'Fix cross-page merge logic to include continuation text at top of next page before the first independent story.',
    },
}


def parse_story_key(key):
    """Parse 'Ketubot 62a_4-4' → ('Ketubot 62a', 4, 4)"""
    m = re.match(r'^(Ketubot \d+[ab])_(\d+)-(\d+)$', key)
    if m:
        return m.group(1), int(m.group(2)), int(m.group(3))
    return None, None, None


def load_canonical_review():
    """Load Jeff's canonical review (March 2026)."""
    with open(CANONICAL_REVIEW) as f:
        data = json.load(f)
    return data.get('feedback', {})


def load_canonical_file():
    """Load the current canonical dataset."""
    with open(CANONICAL_FILE) as f:
        return json.load(f)


def load_prior_feedback():
    """Load all prior feedback into a unified dict keyed by story key."""
    unified = {}
    sources = ['v5.1_2026-02-05', 'v5.1_2026-02-20', 'v8_delta_2026-02-26']
    for path, source in zip(PRIOR_FEEDBACK_FILES, sources):
        if not path.exists():
            print(f"  WARNING: {path} not found")
            continue
        with open(path) as f:
            data = json.load(f)
        for key, entry in data.get('feedback', {}).items():
            unified[key] = {
                'verdict': entry.get('verdict'),
                'note': entry.get('note', ''),
                'source': source,
            }
    return unified


def get_current_classification(canonical, page_ref, start_seg, end_seg):
    """Look up the current classification for a story in the canonical file."""
    for page in canonical.get('pages', []):
        if page['ref'] != page_ref:
            continue
        for story in page.get('stories', []):
            if story['start_segment'] == start_seg and story['end_segment'] == end_seg:
                return story.get('classification', 'UNKNOWN')
            # Overlap match
            s_range = set(range(story['start_segment'], story['end_segment'] + 1))
            f_range = set(range(start_seg, end_seg + 1))
            if len(s_range & f_range) > 0:
                return story.get('classification', 'UNKNOWN')
    return 'NOT_FOUND'


def extract_hebrew_markers(note):
    """Extract Hebrew text fragments from Jeff's notes as boundary markers."""
    # Match Hebrew/Aramaic text (Unicode Hebrew block + common punctuation)
    hebrew_pattern = r'[\u0590-\u05FF\uFB1D-\uFB4F][\u0590-\u05FF\uFB1D-\uFB4F\s\u0027\u05F3\u05F4\u05BE\u200E\u200F:,;.!?\-״׳—–\(\)]*[\u0590-\u05FF\uFB1D-\uFB4F]'
    matches = re.findall(hebrew_pattern, note)
    # Filter out very short matches (likely just a word reference, not a boundary marker)
    return [m.strip() for m in matches if len(m.strip()) > 10]


def classify_error_pattern(verdict, note, current_cls):
    """Classify the error pattern based on Jeff's verdict and note."""
    if verdict == 'correct' and not note:
        return 'NONE', 'no_error', None

    note_lower = (note or '').lower()

    # Check for boundary issues (even in 'correct' verdicts with notes)
    has_boundary_issue = any(marker in note_lower for marker in [
        'boundaries', 'boundary', 'should start with', 'should end with',
        'should not be included', 'should also be included', 'should be omitted',
        'first half', 'first line', 'next paragraph', 'not part of the story',
        'need not be quoted', 'not quoted', 'last line', 'last few words',
        "talmud's comment", "gemara's comment", "talmud's question",
        'follow-up question', 'legal discussion following',
    ])

    has_merge_issue = any(marker in note_lower for marker in [
        'merge', 'continuation', 'continues on', 'continues with',
        'part of a longer', 'same story', 'second part', 'should go with',
        'one long story', 'merged', 'top of',
    ])

    has_classification_issue = False
    target_classification = None

    if verdict == 'incorrect':
        # Check what Jeff wants
        if any(marker in note_lower for marker in [
            'not a story', 'not even a story', 'hypothetical',
            'legal discussion', 'legal debate', 'no real events',
            'not really an event', 'just one event', 'just the report',
            'just a reference',
        ]):
            has_classification_issue = True
            target_classification = 'NOT_A_STORY'
        elif any(marker in note_lower for marker in [
            'low confidence', 'borderline', 'low-confidence',
        ]):
            has_classification_issue = True
            target_classification = 'LOW_CONFIDENCE'
        elif any(marker in note_lower for marker in [
            'high confidence', 'should be high', 'definitely a story',
            'clearly a story', 'keep as yes',
        ]):
            has_classification_issue = True
            target_classification = 'YES'
        elif not note_lower:
            # Incorrect with no note — could be many things
            has_classification_issue = True

    # Determine primary error pattern
    if has_classification_issue and target_classification == 'NOT_A_STORY':
        # Determine subtype
        if 'hypothetical' in note_lower:
            return 'LEGAL_FALSE_POSITIVE', 'hypothetical_case', target_classification
        elif 'legal discussion' in note_lower or 'legal debate' in note_lower:
            return 'LEGAL_FALSE_POSITIVE', 'pure_legal_discussion', target_classification
        elif 'reference' in note_lower:
            return 'LEGAL_FALSE_POSITIVE', 'reference_to_story', target_classification
        elif 'dialogue' in note_lower:
            return 'LEGAL_FALSE_POSITIVE', 'dialogue_only', target_classification
        elif 'just one event' in note_lower or 'just the report' in note_lower:
            return 'LEGAL_FALSE_POSITIVE', 'single_action_plus_ruling', target_classification
        else:
            return 'LEGAL_FALSE_POSITIVE', 'pure_legal_discussion', target_classification

    if has_classification_issue and target_classification in ('LOW_CONFIDENCE', 'YES'):
        if 'habitual' in note_lower or 'would do' in note_lower or 'repeatedly' in note_lower:
            return 'CONFIDENCE_MISCALIBRATION', 'habitual_as_high', target_classification
        elif 'no causality' in note_lower or 'no real causality' in note_lower:
            return 'CONFIDENCE_MISCALIBRATION', 'minimal_causality', target_classification
        elif target_classification == 'YES':
            return 'CONFIDENCE_MISCALIBRATION', 'should_promote', target_classification
        else:
            return 'CONFIDENCE_MISCALIBRATION', 'minimal_causality', target_classification

    if has_merge_issue and 'not correct' in note_lower or 'incorrect' in note_lower and has_merge_issue:
        return 'MERGE_INCORRECT', 'wrong_segments_on_next_page', None

    if has_merge_issue:
        if 'next page' in note_lower or 'cross' in note_lower or 'top of' in note_lower:
            return 'MERGE_NEEDED', 'cross_page_continuation', None
        elif 'same story' in note_lower or 'second part' in note_lower or 'continuation of' in note_lower:
            return 'MERGE_NEEDED', 'same_page_continuation', None
        elif 'longer story' in note_lower or 'longer narrative' in note_lower:
            return 'MERGE_NEEDED', 'part_of_longer_narrative', None
        else:
            return 'MERGE_NEEDED', 'cross_page_continuation', None

    if has_boundary_issue:
        # Determine if overextension or underextension
        if any(marker in note_lower for marker in [
            'should not be included', 'should be omitted', 'need not be quoted',
            'not part of the story', "talmud's comment", "gemara's comment",
            'last line', 'last few words', 'follow-up question',
        ]):
            if 'question' in note_lower:
                return 'BOUNDARY_OVEREXTENSION', 'gemara_question', None
            elif "talmud" in note_lower or "gemara" in note_lower or 'comment' in note_lower:
                return 'BOUNDARY_OVEREXTENSION', 'gemara_comment', None
            elif 'legal discussion' in note_lower:
                return 'BOUNDARY_OVEREXTENSION', 'legal_discussion_after_story', None
            else:
                return 'BOUNDARY_OVEREXTENSION', 'gemara_comment', None
        elif any(marker in note_lower for marker in [
            'should start with', 'first half', 'first line',
            'should also be included', 'next paragraph',
            'begins with the previous', 'not quoted',
        ]):
            if 'previous page' in note_lower or 'prior page' in note_lower or '12a' in note_lower:
                return 'BOUNDARY_UNDEREXTENSION', 'missing_start_previous_page', None
            elif 'next page' in note_lower or 'next paragraph' in note_lower:
                return 'BOUNDARY_UNDEREXTENSION', 'missing_end_same_page', None
            elif 'start with' in note_lower or 'first' in note_lower:
                return 'BOUNDARY_UNDEREXTENSION', 'missing_start_same_page', None
            else:
                return 'BOUNDARY_UNDEREXTENSION', 'missing_end_same_page', None
        else:
            return 'BOUNDARY_UNDEREXTENSION', 'missing_end_same_page', None

    if verdict == 'correct' and note:
        # Correct with informational note — check for soft suggestions
        if any(marker in note_lower for marker in ['could be', 'could also', 'i think']):
            return 'NONE', 'soft_suggestion', None
        return 'NONE', 'informational_note', None

    return 'NONE', 'no_error', None


def determine_consistency(key, canonical_verdict, canonical_note, prior_feedback):
    """Determine whether Jeff's canonical review is consistent with prior feedback."""
    prior = prior_feedback.get(key)
    if not prior:
        return 'new_finding', None

    prior_verdict = prior.get('verdict')
    prior_note = prior.get('note', '')

    boundary_words = ['boundary', 'boundaries', 'start with', 'should not',
                     'first half', 'first line', 'next page', 'continuation',
                     'merge', 'should be included', 'not quoted', 'not part of',
                     'continues', 'next paragraph', 'previous page', 'top of',
                     'omitted', 'last line', 'first half']
    prior_note_lower = prior_note.lower()
    canonical_note_lower = (canonical_note or '').lower()
    prior_had_boundary = any(w in prior_note_lower for w in boundary_words)
    canonical_has_boundary = any(w in canonical_note_lower for w in boundary_words)

    # Check if the canonical review is confirming prior corrections
    if canonical_verdict == 'correct':
        if prior_verdict == 'incorrect' or prior_verdict == 'correct':
            if prior_had_boundary and canonical_has_boundary:
                return 'repeated_boundary_issue', prior
            return 'confirmed_prior_correction', prior

    if canonical_verdict == 'incorrect':
        if prior_verdict == 'incorrect':
            return 'repeated_finding_not_fixed', prior
        elif prior_verdict == 'correct':
            # Prior was "correct" with a boundary note we ignored,
            # now Jeff says "incorrect" because boundary is STILL wrong
            if prior_had_boundary and canonical_has_boundary:
                return 'repeated_boundary_issue', prior
            # Prior had no boundary note — this is genuinely new
            if not prior_note.strip():
                return 'new_finding', prior
            return 'new_issue_on_prior_correct', prior
        else:
            return 'new_finding', prior

    if canonical_verdict == 'approve':
        return 'approves_proposed_change', prior

    if canonical_verdict == 'adjust':
        return 'adjusts_proposed_change', prior

    return 'unclear', prior


def determine_actions(entry):
    """Determine what specific actions need to be taken for each entry."""
    actions = []
    verdict = entry['jeff_canonical_verdict']
    note = entry.get('jeff_canonical_note', '')
    note_lower = note.lower()
    error_pattern = entry['error_pattern']
    error_subtype = entry['error_subtype']
    target_cls = entry.get('target_classification')

    # Classification action
    if target_cls and target_cls != entry.get('current_classification'):
        actions.append({
            'type': 'reclassify',
            'from': entry.get('current_classification'),
            'to': target_cls,
            'auto_applicable': True,
            'confidence': 'high',
        })

    # Boundary actions
    hebrew_markers = extract_hebrew_markers(note)

    if error_pattern == 'BOUNDARY_OVEREXTENSION':
        actions.append({
            'type': 'trim_boundary',
            'direction': 'end' if any(w in note_lower for w in ['last line', 'last few', 'should be omitted', 'end with']) else 'start',
            'hebrew_markers': hebrew_markers,
            'jeff_instruction': note,
            'auto_applicable': False,
            'requires': 'segment_text_lookup',
        })
    elif error_pattern == 'BOUNDARY_UNDEREXTENSION':
        if error_subtype in ('missing_start_previous_page', 'missing_start_same_page'):
            actions.append({
                'type': 'extend_boundary',
                'direction': 'start',
                'hebrew_markers': hebrew_markers,
                'jeff_instruction': note,
                'auto_applicable': False,
                'requires': 'segment_text_lookup',
            })
        else:
            actions.append({
                'type': 'extend_boundary',
                'direction': 'end',
                'hebrew_markers': hebrew_markers,
                'jeff_instruction': note,
                'auto_applicable': False,
                'requires': 'segment_text_lookup',
            })

    # Merge actions
    if error_pattern in ('MERGE_NEEDED', 'MERGE_INCORRECT'):
        # Try to extract target merge info from note
        merge_target = None
        # Look for page references in note
        page_refs = re.findall(r'(\d+[ab])', note)
        if page_refs:
            merge_target = f'Ketubot {page_refs[-1]}'  # Last page ref is usually the target

        actions.append({
            'type': 'merge' if error_pattern == 'MERGE_NEEDED' else 'fix_merge',
            'merge_target_page': merge_target,
            'hebrew_markers': hebrew_markers,
            'jeff_instruction': note,
            'auto_applicable': False,
            'requires': 'cross_page_analysis',
        })

    # Approved changes (from needs_review)
    if verdict == 'approve':
        actions.append({
            'type': 'implement_approved_change',
            'jeff_instruction': note,
            'auto_applicable': False,  # Most need boundary/merge work
            'requires': 'review_needs_review_log',
        })

    # Adjust verdict
    if verdict == 'adjust':
        actions.append({
            'type': 'implement_adjustment',
            'jeff_instruction': note,
            'auto_applicable': False,
            'requires': 'manual_review',
        })

    # If correct with boundary note
    if verdict == 'correct' and note and any(w in note_lower for w in [
        'boundaries', 'boundary', 'should start', 'should not be included',
        'next paragraph', 'should also be included', 'merge', 'continuation',
        'first half', 'not quoted', 'not correct',
    ]):
        # Even though verdict is "correct" (classification is right),
        # there's boundary work to do
        if not any(a['type'] in ('trim_boundary', 'extend_boundary', 'merge', 'fix_merge') for a in actions):
            actions.append({
                'type': 'boundary_adjustment_from_note',
                'jeff_instruction': note,
                'hebrew_markers': hebrew_markers,
                'auto_applicable': False,
                'requires': 'segment_text_lookup',
            })

    if not actions:
        actions.append({
            'type': 'no_action',
            'auto_applicable': True,
        })

    return actions


def extract_generalization_lesson(error_pattern, error_subtype, note):
    """Extract a generalizable lesson from this correction."""
    if not note:
        return None

    lessons = {
        ('LEGAL_FALSE_POSITIVE', 'pure_legal_discussion'):
            'Legal discussions where rabbis state, object, or ask questions are dialogue, not narrative events. The presence of named rabbis in a legal debate does not make it a story.',
        ('LEGAL_FALSE_POSITIVE', 'hypothetical_case'):
            'Hypothetical legal scenarios (even with specific details) are not stories. They describe what COULD happen, not what DID happen.',
        ('LEGAL_FALSE_POSITIVE', 'reference_to_story'):
            'A reference to an incident or story mentioned elsewhere is not itself a story. A rabbi overlooking what another said about an incident is not a narrative.',
        ('LEGAL_FALSE_POSITIVE', 'dialogue_only'):
            'Dialogue alone does not constitute events. Asking, objecting, explaining, and ruling are verbal acts, not narrative events that make a story.',
        ('LEGAL_FALSE_POSITIVE', 'single_action_plus_ruling'):
            'A single action followed by a legal ruling is insufficient for a story. Stories require multiple events in causal relationship.',
        ('BOUNDARY_OVEREXTENSION', 'gemara_comment'):
            "The Talmud's analytical comment on a story is NOT part of the story itself. Look for structural shifts from narrative to analysis.",
        ('BOUNDARY_OVEREXTENSION', 'gemara_question'):
            "The Gemara's follow-up questions about a story are not part of the story. The story ends when the narrative arc resolves.",
        ('BOUNDARY_OVEREXTENSION', 'legal_discussion_after_story'):
            'Legal discussion triggered by a story should be excluded from the story boundaries, even if it directly follows.',
        ('BOUNDARY_UNDEREXTENSION', 'missing_start_previous_page'):
            'Stories often begin on the previous Talmud page. Always check the last segments of the prior page for narrative setup.',
        ('BOUNDARY_UNDEREXTENSION', 'missing_end_next_page'):
            'Stories often continue onto the next Talmud page. Check segment 0 (and sometimes 1-2) of the next page.',
        ('CONFIDENCE_MISCALIBRATION', 'habitual_as_high'):
            'Habitual actions (what rabbis "would" do repeatedly) are LOW_CONFIDENCE, not HIGH. One-time events are higher confidence.',
        ('CONFIDENCE_MISCALIBRATION', 'minimal_causality'):
            'Two events without causality between them is LOW_CONFIDENCE. High confidence requires causal chains.',
        ('MERGE_NEEDED', 'cross_page_continuation'):
            'Cross-page merges must include the continuation text at the top of the next page, not skip to the next independent story.',
        ('MERGE_NEEDED', 'same_page_continuation'):
            'Adjacent story entries on the same page may be one story split into two. Check if they share characters and narrative arc.',
    }

    return lessons.get((error_pattern, error_subtype))


def main():
    print("=" * 60)
    print("  ANALYZE CANONICAL FEEDBACK — COMPREHENSIVE")
    print("=" * 60)

    # Load all data
    canonical_review = load_canonical_review()
    canonical_file = load_canonical_file()
    prior_feedback = load_prior_feedback()

    print(f"\n  Canonical review entries: {len(canonical_review)}")
    print(f"  Prior feedback entries: {len(prior_feedback)}")

    # Also load the auto_applied and needs_review logs
    auto_applied_log = {r['key']: r for r in canonical_file.get('auto_applied_log', [])}
    needs_review_log = {r['key']: r for r in canonical_file.get('needs_review_log', [])}

    print(f"  Auto-applied corrections: {len(auto_applied_log)}")
    print(f"  Needs-review items: {len(needs_review_log)}")

    # Process each entry
    entries = []

    for key, fb in sorted(canonical_review.items()):
        page_ref, start_seg, end_seg = parse_story_key(key)
        if page_ref is None:
            print(f"  WARNING: Could not parse key '{key}'")
            continue

        verdict = fb.get('verdict')
        note = fb.get('note', '')

        # Get current classification
        current_cls = get_current_classification(canonical_file, page_ref, start_seg, end_seg)

        # Classify error pattern
        error_pattern, error_subtype, target_cls = classify_error_pattern(verdict, note, current_cls)

        # Check consistency with prior feedback
        consistency, prior = determine_consistency(key, verdict, note, prior_feedback)

        # Check if this story had auto-applied or needs-review corrections
        was_auto_applied = key in auto_applied_log
        was_needs_review = key in needs_review_log

        entry = {
            'story_key': key,
            'page_ref': page_ref,
            'start_segment': start_seg,
            'end_segment': end_seg,
            'current_classification': current_cls,

            # Jeff's canonical review
            'jeff_canonical_verdict': verdict,
            'jeff_canonical_note': note,
            'jeff_canonical_timestamp': fb.get('timestamp'),

            # Error analysis
            'error_pattern': error_pattern,
            'error_subtype': error_subtype,
            'target_classification': target_cls,

            # Hebrew boundary markers extracted from Jeff's notes
            'hebrew_boundary_markers': extract_hebrew_markers(note),

            # Consistency with prior feedback
            'consistency_status': consistency,
            'had_prior_feedback': prior is not None,
            'prior_feedback_source': prior.get('source') if prior else None,
            'prior_feedback_verdict': prior.get('verdict') if prior else None,
            'prior_feedback_note': prior.get('note') if prior else None,

            # What corrections were already applied
            'was_auto_applied': was_auto_applied,
            'auto_applied_action': auto_applied_log[key].get('action') if was_auto_applied else None,
            'was_needs_review': was_needs_review,
            'needs_review_action': needs_review_log[key].get('action') if was_needs_review else None,

            # Generalization lesson
            'generalization_lesson': extract_generalization_lesson(error_pattern, error_subtype, note),

            # Implementation status
            'implemented': False,
        }

        # Determine specific actions
        entry['actions'] = determine_actions(entry)

        entries.append(entry)

    # ---------- Compute summary statistics ----------

    verdict_counts = Counter(e['jeff_canonical_verdict'] for e in entries)
    pattern_counts = Counter(e['error_pattern'] for e in entries)
    subtype_counts = Counter(f"{e['error_pattern']}/{e['error_subtype']}" for e in entries)
    consistency_counts = Counter(e['consistency_status'] for e in entries)

    # Count actionable items
    actionable = [e for e in entries if any(
        a['type'] != 'no_action' for a in e['actions']
    )]

    auto_applicable = [e for e in entries if any(
        a.get('auto_applicable') for a in e['actions']
        if a['type'] != 'no_action'
    )]

    needs_manual = [e for e in entries if any(
        not a.get('auto_applicable') and a['type'] != 'no_action'
        for a in e['actions']
    )]

    # Count by action type
    action_type_counts = Counter()
    for e in entries:
        for a in e['actions']:
            action_type_counts[a['type']] += 1

    # Identify repeated boundary issues (Jeff said it before, we didn't fix it)
    repeated_boundary = [e for e in entries if e['consistency_status'] == 'repeated_boundary_issue']
    repeated_not_fixed = [e for e in entries if e['consistency_status'] == 'repeated_finding_not_fixed']

    summary = {
        'total_reviewed': len(entries),
        'verdict_counts': dict(verdict_counts),
        'error_pattern_counts': dict(pattern_counts),
        'error_subtype_counts': dict(subtype_counts),
        'consistency_counts': dict(consistency_counts),
        'total_actionable': len(actionable),
        'auto_applicable_count': len(auto_applicable),
        'needs_manual_count': len(needs_manual),
        'action_type_counts': dict(action_type_counts),
        'repeated_boundary_issues': len(repeated_boundary),
        'repeated_findings_not_fixed': len(repeated_not_fixed),
        'key_finding': (
            f"Of {len(entries)} reviewed stories, {len(actionable)} need changes. "
            f"{len(auto_applicable)} can be auto-applied (classification changes), "
            f"{len(needs_manual)} need manual work (boundary/merge). "
            f"{len(repeated_boundary)} are boundary issues Jeff flagged before that we never fixed."
        ),
    }

    # ---------- Build error pattern details with examples ----------

    error_pattern_details = {}
    for pattern_name, pattern_def in ERROR_PATTERNS.items():
        examples = [e for e in entries if e['error_pattern'] == pattern_name]
        if not examples:
            continue
        error_pattern_details[pattern_name] = {
            **pattern_def,
            'count': len(examples),
            'examples': [
                {
                    'story_key': e['story_key'],
                    'current_classification': e['current_classification'],
                    'target_classification': e.get('target_classification'),
                    'jeff_note': e['jeff_canonical_note'],
                    'error_subtype': e['error_subtype'],
                }
                for e in examples[:10]  # Cap at 10 examples per pattern
            ],
        }

    # ---------- Build the output ----------

    output = {
        'version': 'canonical_feedback_analysis_v1',
        'analysis_date': '2026-03-25',
        'sources': {
            'canonical_review': str(CANONICAL_REVIEW),
            'canonical_file': str(CANONICAL_FILE),
            'prior_feedback_files': [str(p) for p in PRIOR_FEEDBACK_FILES],
        },
        'summary': summary,
        'error_patterns': error_pattern_details,
        'corrections': entries,
        'generalization_lessons': [
            {
                'pattern': e['error_pattern'],
                'subtype': e['error_subtype'],
                'lesson': e['generalization_lesson'],
                'example_key': e['story_key'],
                'example_note': e['jeff_canonical_note'],
            }
            for e in entries
            if e.get('generalization_lesson')
        ],
        'repeated_issues': {
            'description': "Issues Jeff flagged in prior rounds that we applied classification changes for but NEVER fixed the boundary/merge corrections",
            'entries': [
                {
                    'story_key': e['story_key'],
                    'prior_source': e['prior_feedback_source'],
                    'prior_note': e['prior_feedback_note'],
                    'canonical_note': e['jeff_canonical_note'],
                    'unfixed_issue': 'boundary/merge correction from prior feedback was not implemented',
                }
                for e in repeated_boundary + repeated_not_fixed
            ],
        },
    }

    # Save
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # Print summary
    print(f"\n{'=' * 60}")
    print(f"  ANALYSIS COMPLETE")
    print(f"{'=' * 60}")
    print(f"\n  Total reviewed: {summary['total_reviewed']}")
    print(f"  Total actionable: {summary['total_actionable']}")
    print(f"  Auto-applicable: {summary['auto_applicable_count']}")
    print(f"  Needs manual: {summary['needs_manual_count']}")
    print(f"\n  Verdict counts:")
    for k, v in sorted(verdict_counts.items(), key=lambda x: -(x[1] or 0)):
        print(f"    {k}: {v}")
    print(f"\n  Error pattern counts:")
    for k, v in sorted(pattern_counts.items(), key=lambda x: -x[1]):
        print(f"    {k}: {v}")
    print(f"\n  Consistency:")
    for k, v in sorted(consistency_counts.items(), key=lambda x: -x[1]):
        print(f"    {k}: {v}")
    print(f"\n  Action types needed:")
    for k, v in sorted(action_type_counts.items(), key=lambda x: -x[1]):
        print(f"    {k}: {v}")

    if repeated_boundary:
        print(f"\n  ⚠ REPEATED BOUNDARY ISSUES (Jeff said this before):")
        for e in repeated_boundary:
            print(f"    {e['story_key']}: {e['jeff_canonical_note'][:80]}...")

    if repeated_not_fixed:
        print(f"\n  ⚠ REPEATED FINDINGS NOT FIXED:")
        for e in repeated_not_fixed:
            print(f"    {e['story_key']}: {e['jeff_canonical_note'][:80]}...")

    print(f"\n  Saved to: {OUTPUT_PATH}")


if __name__ == '__main__':
    main()
