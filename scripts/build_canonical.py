#!/usr/bin/env python3
"""
Build Canonical Ketubot Stories File.

Merges v7 (pages 2-60) and v9 (pages 61-112) base results, then applies
Jeff Rubenstein's expert corrections from 3 segment-level feedback rounds.

WARNING (2026-08-30): the golden has moved on without this script — a 2026-06-03
round, and five stories added from Jeff's blind 2005 list that the detector has
never proposed and this script cannot regenerate. It therefore REFUSES to
overwrite results/canonical/ketubot_canonical.json unless explicitly forced.
Treat it as a historical reconstruction of the 2026-03 state, not a build step.

Corrections are categorized as:
  - auto: Unambiguous changes applied automatically
  - needs_review: Ambiguous changes flagged for Jeff's confirmation

Output: results/canonical/ketubot_canonical.json

Usage:
  python3 scripts/build_canonical.py
"""

import copy
import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

# Input paths
V7_PATH = PROJECT_ROOT / 'results' / 'v7' / 'ketubot_v7_2-60.json'
V9_PATH = PROJECT_ROOT / 'results' / 'v7' / 'ketubot_v9_61-112.json'
FEEDBACK_FILES = [
    # Ordered by timestamp (earliest first) — later files override earlier ones
    {
        'path': PROJECT_ROOT / 'validation' / 'feedback' / 'v5_1_feedback_anonymous_2026-02-05 (1).json',
        'source': 'v5.1_2026-02-05',
        'default_timestamp': '2026-02-05T00:00:00Z',
    },
    {
        'path': PROJECT_ROOT / 'validation' / 'feedback' / 'v5_1_feedback_anonymous_2026-02-20.json',
        'source': 'v5.1_2026-02-20',
        'default_timestamp': '2026-02-20T00:00:00Z',
    },
    {
        'path': PROJECT_ROOT / 'validation' / 'feedback' / 'v8_delta_feedback_anonymous_2026-02-26.json',
        'source': 'v8_delta_2026-02-26',
        'default_timestamp': '2026-02-26T00:00:00Z',
    },
]
CANONICAL_REVIEW_PATH = PROJECT_ROOT / 'validation' / 'feedback' / 'canonical_review_anonymous_2026-03-17.json'
OUTPUT_PATH = PROJECT_ROOT / 'results' / 'canonical' / 'ketubot_canonical.json'


# ---------- Step 1a: Load and merge base results ----------

def load_and_merge_base():
    """Load v7 (2-60) + v9 (61-112) and merge into one page list."""
    print("--- Loading base results ---")

    with open(V7_PATH) as f:
        v7 = json.load(f)
    print(f"  v7 (2-60): {len(v7['pages'])} pages")

    with open(V9_PATH) as f:
        v9 = json.load(f)
    print(f"  v9 (61-112): {len(v9['pages'])} pages")

    # Deep copy to avoid modifying originals
    pages = copy.deepcopy(v7['pages']) + copy.deepcopy(v9['pages'])
    print(f"  Combined: {len(pages)} pages")

    return pages


def fix_bad_merge_2_60(pages):
    """
    Undo the one bad cross-page merge in 2-60: 54a→54b (start_p2=1).

    Same logic as remerge_v9.py undo_merge() — strip merge fields from
    page N's story, recreate the popped story on page N+1.
    """
    print("\n--- Fixing bad merge in 2-60 (54a→54b) ---")

    page_54a = None
    page_54b = None
    for p in pages:
        if p['ref'] == 'Ketubot 54a':
            page_54a = p
        elif p['ref'] == 'Ketubot 54b':
            page_54b = p

    if not page_54a or not page_54b:
        print("  WARNING: Could not find pages 54a/54b")
        return False

    # Find the merged story on 54a
    merged_story = None
    for story in page_54a.get('stories', []):
        if (story.get('spans_pages') and
            len(story['spans_pages']) == 2 and
            story['spans_pages'][1] == 'Ketubot 54b'):
            merged_story = story
            break

    if not merged_story:
        print("  No merged story found on 54a→54b (may already be fixed)")
        return False

    start_p2 = merged_story.get('start_segment_page2')
    end_p2 = merged_story.get('end_segment_page2')
    original_cls = merged_story.get('classification', 'LOW_CONFIDENCE')

    # Only fix if start_p2 >= 1 (the bad merge pattern)
    if start_p2 is None or start_p2 < 1:
        print("  Merge on 54a→54b has start_p2=0, not a bad merge")
        return False

    # Recreate the popped story on 54b
    restored_story = {
        'start_segment': start_p2,
        'end_segment': end_p2,
        'classification': original_cls,
        'one_sentence_summary': f'[Restored from Ketubot 54a merge]',
        'continuation': {
            'continues_from_previous_page': False,
            'continues_to_next_page': False,
        },
        'restored_from_merge': True,
    }

    if 'stories' not in page_54b:
        page_54b['stories'] = []
    page_54b['stories'].insert(0, restored_story)

    # Strip merge fields from 54a's story
    for field in ['spans_pages', 'start_segment_page2', 'end_segment_page2',
                  'cross_page_merge_v7', 'cross_page_stitched']:
        merged_story.pop(field, None)

    print(f"  Fixed: restored seg {start_p2}-{end_p2} on 54b, "
          f"stripped merge from 54a")
    return True


# ---------- Step 1b: Load and normalize feedback ----------

def parse_story_key(feedback_key):
    """
    Parse feedback key like 'Ketubot 62a_4-4' into components.

    Returns: (page_ref, start_seg, end_seg) or None if unparseable.
    Example: 'Ketubot 62a_4-4' → ('Ketubot 62a', 4, 4)
    """
    m = re.match(r'^(Ketubot \d+[ab])_(\d+)-(\d+)$', feedback_key)
    if m:
        return m.group(1), int(m.group(2)), int(m.group(3))
    return None


def load_all_feedback():
    """
    Load all 3 feedback files into a unified dict.

    Key: 'Ketubot 62a_4-4' (original feedback key)
    Value: {verdict, note, source, timestamp}

    When same story appears in multiple files, the latest wins.
    """
    print("\n--- Loading feedback ---")
    unified = {}

    for fb_info in FEEDBACK_FILES:
        path = fb_info['path']
        source = fb_info['source']

        with open(path) as f:
            data = json.load(f)

        entries = data.get('feedback', {})
        count = 0
        overrides = 0

        for key, entry in entries.items():
            timestamp = entry.get('timestamp', fb_info['default_timestamp'])

            new_entry = {
                'verdict': entry.get('verdict'),
                'note': entry.get('note', ''),
                'source': source,
                'timestamp': timestamp,
            }

            # If key already exists, keep the one with the later timestamp
            if key in unified:
                if timestamp > unified[key]['timestamp']:
                    unified[key] = new_entry
                    overrides += 1
            else:
                unified[key] = new_entry
            count += 1

        print(f"  {source}: {count} entries"
              f"{f' ({overrides} overrides)' if overrides else ''}")

    print(f"  Total unified: {len(unified)} unique story reviews")
    return unified


# ---------- Step 1c/1d: Categorize and apply corrections ----------

def find_story_on_page(page, start_seg, end_seg):
    """
    Find a story on a page matching the given segment range.

    Tries exact match first, then falls back to overlap match
    (feedback keys sometimes have slightly different boundaries than base data).
    """
    # Exact match
    for i, story in enumerate(page.get('stories', [])):
        if (story['start_segment'] == start_seg and
            story['end_segment'] == end_seg):
            return i, story

    # Overlap match — find story with best overlap to the feedback range
    fb_range = set(range(start_seg, end_seg + 1))
    best_idx = None
    best_story = None
    best_overlap = 0
    for i, story in enumerate(page.get('stories', [])):
        s_range = set(range(story['start_segment'], story['end_segment'] + 1))
        overlap = len(fb_range & s_range)
        if overlap > best_overlap:
            best_overlap = overlap
            best_idx = i
            best_story = story

    if best_story and best_overlap > 0:
        return best_idx, best_story

    return None, None


def find_page(pages, page_ref):
    """Find a page by reference."""
    for p in pages:
        if p['ref'] == page_ref:
            return p
    return None


def find_preceding_story(page, start_seg):
    """Find the story that ends just before start_seg on the same page."""
    best = None
    best_end = -1
    for story in page.get('stories', []):
        if story['end_segment'] < start_seg and story['end_segment'] > best_end:
            best = story
            best_end = story['end_segment']
    return best


def categorize_correction(key, fb, pages):
    """
    Categorize a single feedback entry as auto-apply or needs-review.

    Returns: (action_type, details_dict) where action_type is one of:
      - 'no_change': correct with no actionable note
      - 'auto_not_a_story': clearly not a story
      - 'auto_yes': clearly should be YES
      - 'auto_low_confidence': should be LOW_CONFIDENCE
      - 'auto_remove': confirm_remove verdict
      - 'auto_keep': reject_remove verdict (no change needed)
      - 'review_boundary': boundary adjustment needed
      - 'review_merge': merge with another story needed
      - 'review_cross_page': cross-page continuation issue
      - 'review_other': other ambiguous correction
      - 'skip_null': null verdict, skip
    """
    verdict = fb['verdict']
    note = (fb.get('note') or '').strip()
    note_lower = note.lower()
    source = fb['source']

    if verdict is None:
        return 'skip_null', {'reason': 'null verdict'}

    # ----- Auto-apply patterns -----

    # confirm_remove → remove the story
    if verdict == 'confirm_remove':
        return 'auto_remove', {'reason': 'Jeff confirmed removal'}

    # reject_remove → keep the story (no change)
    if verdict == 'reject_remove':
        return 'auto_keep', {'reason': 'Jeff rejected removal, keep story'}

    # ---- correct verdicts ----
    if verdict == 'correct':
        if note_lower:
            # "borderline" or "low confidence" → reclassify
            if ('borderline' in note_lower or 'low confidence' in note_lower or
                'low-confidence' in note_lower):
                return 'auto_low_confidence', {
                    'reason': f'Jeff noted borderline/low confidence: {note}',
                }
            # "include with previous story" → merge suggestion (correct but wants merge)
            if ('include' in note_lower and 'previous' in note_lower):
                return 'review_merge', {
                    'reason': f'Jeff suggested merge with previous: {note}',
                }
            # "include with" generally → merge
            if 'include with' in note_lower or 'include this with' in note_lower:
                return 'review_merge', {
                    'reason': f'Jeff suggested merging: {note}',
                }
            # "next paragraph should also be included" / "top line should be highlighted"
            if ('should also be included' in note_lower or
                'should not be included' in note_lower or
                'should not be highlighted' in note_lower or
                'next paragraph' in note_lower or
                'should be highlighted' in note_lower):
                return 'review_boundary', {
                    'reason': f'Jeff noted boundary issue: {note}',
                }
            # "merge was not done correctly" / "part of the story was skipped"
            if ('not done correctly' in note_lower or
                'skipped' in note_lower or
                'top line' in note_lower):
                return 'review_cross_page', {
                    'reason': f'Jeff noted merge issue: {note}',
                }
            # "classification has an error" → informational, no auto-change
            # Otherwise, correct with informational note — no change
            return 'no_change', {'reason': 'correct with informational note'}

        return 'no_change', {'reason': 'correct, no actionable note'}

    # ---- incorrect verdicts ----
    if verdict == 'incorrect':
        # v8_delta "incorrect" with no note — these mark stories that should
        # be independent (were wrongly part of a cross-page merge in v8).
        # In v9 base data these are already separate, so no change needed.
        if not note_lower:
            if source == 'v8_delta_2026-02-26':
                return 'no_change', {
                    'reason': 'v8_delta incorrect with no note — marks story as '
                              'independent (already separate in v9 base)',
                }
            return 'review_other', {
                'reason': 'Incorrect verdict with no note',
            }

        # --- NOT A STORY patterns ---
        # "not a story" / "not even a story"
        if ('not a story' in note_lower or 'not even a story' in note_lower):
            return 'auto_not_a_story', {
                'reason': f'Jeff says not a story: {note}',
            }
        # "not a story at all" / "just a theoretical discussion" / "just a legal debate"
        if ('not a story at all' in note_lower or
            'just a theoretical discussion' in note_lower or
            'just a legal debate' in note_lower or
            'just a debate' in note_lower or
            'is a legal debate' in note_lower):
            return 'auto_not_a_story', {
                'reason': f'Jeff says not a story: {note}',
            }
        # "no real events" / "not really an event" / "are not events"
        if ('no real events' in note_lower or
            'not really an event' in note_lower or
            'are not events' in note_lower):
            return 'auto_not_a_story', {
                'reason': f'Jeff says no real events: {note}',
            }
        # "just one event" / "just the report"
        if ('just one event' in note_lower or
            'just the report' in note_lower):
            return 'auto_not_a_story', {
                'reason': f'Jeff says insufficient for a story: {note}',
            }

        # --- YES patterns ---
        # "definitely a story" / "this too is a story" / "clearly a story"
        if ('definitely a story' in note_lower or
            'this too is a story' in note_lower or
            'clearly a story' in note_lower):
            return 'auto_yes', {
                'reason': f'Jeff says clearly a story: {note}',
            }
        # "keep as yes" / 'keep as a "yes"'
        if 'keep as' in note_lower and 'yes' in note_lower:
            return 'auto_yes', {
                'reason': f'Jeff says keep as YES: {note}',
            }
        # "could be high confidence" / "should be high"
        if ('could be high confidence' in note_lower or
            'should be high' in note_lower):
            return 'auto_yes', {
                'reason': f'Jeff says higher confidence: {note}',
            }

        # --- LOW_CONFIDENCE patterns ---
        # "borderline story" / "low confidence" / "borderline"
        if ('borderline' in note_lower or
            'low confidence' in note_lower or
            'low-confidence' in note_lower):
            return 'auto_low_confidence', {
                'reason': f'Jeff says borderline/low confidence: {note}',
            }

        # --- Cross-page issues ---
        # "merge is not correct" / "merge is incorrect" / "top lines of the next page"
        if ('merge is not correct' in note_lower or
            'merge is incorrect' in note_lower or
            'top line' in note_lower or
            'continues on the next page' in note_lower or
            'continues with the first line' in note_lower or
            'top of' in note_lower and ('should' in note_lower or 'included' in note_lower)):
            return 'review_cross_page', {
                'reason': f'Jeff noted cross-page issue: {note}',
            }
        # "beginning of a story that continues on the next page"
        if ('continues on the next page' in note_lower or
            'continues on' in note_lower and 'next page' in note_lower):
            return 'review_cross_page', {
                'reason': f'Jeff says story continues on next page: {note}',
            }

        # --- Merge patterns ---
        # "second part of" / "should go with" / "one long story"
        if ('second part' in note_lower or
            'should go with' in note_lower or
            'one long story' in note_lower):
            return 'review_merge', {
                'reason': f'Jeff says merge needed: {note}',
            }
        # "same story as"
        if 'same story' in note_lower:
            return 'review_merge', {
                'reason': f'Jeff says same story: {note}',
            }

        # --- Boundary patterns ---
        # "story ends with" / "boundaries" / "should not be highlighted"
        # "last line should not be included" / "rest should not"
        if ('story ends' in note_lower or
            'boundaries' in note_lower or
            'should not be highlighted' in note_lower or
            'should not be included' in note_lower or
            'last line' in note_lower and 'should not' in note_lower):
            return 'review_boundary', {
                'reason': f'Jeff noted boundary issue: {note}',
            }

        # Fallback for incorrect with note
        return 'review_other', {
            'reason': f'Incorrect — needs interpretation: {note}',
        }

    # Unknown verdict
    return 'review_other', {'reason': f'Unknown verdict: {verdict}'}


def apply_corrections(pages, feedback):
    """
    Apply all corrections to the pages.

    Returns: (auto_applied, needs_review, skipped) lists of correction records.
    """
    print("\n--- Categorizing corrections ---")

    auto_applied = []
    needs_review = []
    skipped = []
    no_change = []

    for key, fb in sorted(feedback.items()):
        parsed = parse_story_key(key)
        if not parsed:
            print(f"  WARNING: Could not parse key '{key}', skipping")
            skipped.append({'key': key, 'reason': 'unparseable key'})
            continue

        page_ref, start_seg, end_seg = parsed
        action, details = categorize_correction(key, fb, pages)

        record = {
            'key': key,
            'page_ref': page_ref,
            'start_segment': start_seg,
            'end_segment': end_seg,
            'action': action,
            'verdict': fb['verdict'],
            'note': fb.get('note', ''),
            'source': fb['source'],
            **details,
        }

        if action == 'skip_null':
            skipped.append(record)
            continue

        if action == 'no_change':
            no_change.append(record)
            continue

        # ----- Auto-apply actions -----

        if action == 'auto_not_a_story':
            page = find_page(pages, page_ref)
            if page:
                idx, story = find_story_on_page(page, start_seg, end_seg)
                if story:
                    old_cls = story['classification']
                    story['classification'] = 'NOT_A_STORY'
                    record['old_classification'] = old_cls
                    record['new_classification'] = 'NOT_A_STORY'
                    auto_applied.append(record)
                else:
                    record['warning'] = f'Story not found on {page_ref} seg {start_seg}-{end_seg}'
                    skipped.append(record)
            else:
                record['warning'] = f'Page not found: {page_ref}'
                skipped.append(record)
            continue

        if action == 'auto_yes':
            page = find_page(pages, page_ref)
            if page:
                idx, story = find_story_on_page(page, start_seg, end_seg)
                if story:
                    old_cls = story['classification']
                    if old_cls != 'YES':
                        story['classification'] = 'YES'
                        record['old_classification'] = old_cls
                        record['new_classification'] = 'YES'
                        auto_applied.append(record)
                    else:
                        no_change.append(record)
                else:
                    record['warning'] = f'Story not found on {page_ref} seg {start_seg}-{end_seg}'
                    skipped.append(record)
            else:
                record['warning'] = f'Page not found: {page_ref}'
                skipped.append(record)
            continue

        if action == 'auto_low_confidence':
            page = find_page(pages, page_ref)
            if page:
                idx, story = find_story_on_page(page, start_seg, end_seg)
                if story:
                    old_cls = story['classification']
                    if old_cls != 'LOW_CONFIDENCE':
                        story['classification'] = 'LOW_CONFIDENCE'
                        record['old_classification'] = old_cls
                        record['new_classification'] = 'LOW_CONFIDENCE'
                        auto_applied.append(record)
                    else:
                        no_change.append(record)
                else:
                    record['warning'] = f'Story not found on {page_ref} seg {start_seg}-{end_seg}'
                    skipped.append(record)
            else:
                record['warning'] = f'Page not found: {page_ref}'
                skipped.append(record)
            continue

        if action == 'auto_remove':
            page = find_page(pages, page_ref)
            if page:
                idx, story = find_story_on_page(page, start_seg, end_seg)
                if story is not None:
                    page['stories'].pop(idx)
                    record['removed'] = True
                    auto_applied.append(record)
                else:
                    record['warning'] = f'Story not found on {page_ref} seg {start_seg}-{end_seg}'
                    skipped.append(record)
            else:
                record['warning'] = f'Page not found: {page_ref}'
                skipped.append(record)
            continue

        if action == 'auto_keep':
            # reject_remove — story stays as-is, just log it
            auto_applied.append(record)
            continue

        # ----- Needs-review actions -----
        if action.startswith('review_'):
            needs_review.append(record)
            continue

        # Should not reach here
        skipped.append(record)

    print(f"\n  Auto-applied: {len(auto_applied)}")
    print(f"  Needs review: {len(needs_review)}")
    print(f"  No change:    {len(no_change)}")
    print(f"  Skipped:      {len(skipped)}")

    return auto_applied, needs_review, skipped, no_change


# ---------- Step 1e: Annotate stories with correction info ----------

def annotate_stories(pages, auto_applied, needs_review):
    """
    Add correction metadata to stories in pages.

    For auto-applied: adds 'corrections' field describing what changed.
    For needs_review: adds 'needs_review' flag + 'proposed_change' description.
    """
    # Build page lookup
    page_lookup = {p['ref']: p for p in pages}

    # Mark auto-applied corrections
    for record in auto_applied:
        page_ref = record['page_ref']
        page = page_lookup.get(page_ref)
        if not page:
            continue

        start_seg = record['start_segment']
        end_seg = record['end_segment']
        _, story = find_story_on_page(page, start_seg, end_seg)

        if story:
            if 'corrections' not in story:
                story['corrections'] = []
            story['corrections'].append({
                'action': record['action'],
                'reason': record['reason'],
                'source': record['source'],
                'auto_applied': True,
            })

    # Mark needs-review corrections
    for record in needs_review:
        page_ref = record['page_ref']
        page = page_lookup.get(page_ref)
        if not page:
            continue

        start_seg = record['start_segment']
        end_seg = record['end_segment']
        _, story = find_story_on_page(page, start_seg, end_seg)

        if story:
            story['needs_review'] = True
            story['review_reason'] = record['action']
            story['jeff_note'] = record.get('note', '')
            story['proposed_change'] = record.get('reason', '')
        else:
            # Story not found — might be on a different page or segment range
            # Create a placeholder entry for the review UI
            if 'stories' not in page:
                page['stories'] = []

            placeholder = {
                'start_segment': start_seg,
                'end_segment': end_seg,
                'classification': 'NEEDS_REVIEW',
                'one_sentence_summary': f'[Flagged for review: {record["action"]}]',
                'needs_review': True,
                'review_reason': record['action'],
                'jeff_note': record.get('note', ''),
                'proposed_change': record.get('reason', ''),
                'continuation': {
                    'continues_from_previous_page': False,
                    'continues_to_next_page': False,
                },
            }
            page['stories'].append(placeholder)


# ---------- Step 2: Apply canonical review corrections ----------

def load_canonical_review():
    """Load Jeff's canonical review (March 2026) as a separate correction layer."""
    print("\n--- Loading canonical review (2026-03-17) ---")
    with open(CANONICAL_REVIEW_PATH) as f:
        data = json.load(f)
    entries = data.get('feedback', {})
    print(f"  {len(entries)} entries")
    return entries


def apply_canonical_classification_corrections(pages, canonical_review):
    """
    Apply classification corrections from Jeff's canonical review.

    Runs AFTER the prior 3 feedback rounds as a refinement layer.
    Only applies clear classification changes here. Boundary/merge
    corrections are handled separately by scripts/apply_boundary_corrections.py.
    """
    print("\n--- Applying canonical review classification corrections ---")

    applied = []
    deferred = []
    no_change_keys = []

    for key, entry in sorted(canonical_review.items()):
        verdict = entry.get('verdict')
        note = (entry.get('note') or '').strip()
        note_lower = note.lower()

        parsed = parse_story_key(key)
        if not parsed:
            continue
        page_ref, start_seg, end_seg = parsed

        if verdict is None:
            continue
        if verdict == 'correct':
            no_change_keys.append(key)
            continue

        # approve/adjust are boundary/merge changes → defer to Phase 3
        if verdict in ('approve', 'adjust'):
            deferred.append({'key': key, 'verdict': verdict, 'note': note})
            continue

        if verdict != 'incorrect':
            deferred.append({'key': key, 'verdict': verdict, 'note': note})
            continue

        # Handle "incorrect" verdicts — determine target classification
        target_cls = None

        # Special case: 111a_23-25 — split story, 111a portion is LOW_CONFIDENCE
        if key == 'Ketubot 111a_23-25':
            target_cls = 'LOW_CONFIDENCE'
        # NOT_A_STORY patterns (check BEFORE low confidence since some notes
        # contain both "not a story" and other text)
        elif any(p in note_lower for p in [
            'not a story', 'not even a story',
            'not really an event',
            'just one event', 'just the report',
            'just a reference', 'just one action',
        ]):
            target_cls = 'NOT_A_STORY'
        elif any(p in note_lower for p in [
            'hypothetical legal case', 'hypothetical scenario',
        ]) and 'story' not in note_lower.split('hypothetical')[0]:
            # "hypothetical legal case" but not "a story... hypothetical"
            target_cls = 'NOT_A_STORY'
        elif 'legal discussion' in note_lower and 'story' not in note_lower:
            target_cls = 'NOT_A_STORY'
        # LOW_CONFIDENCE patterns
        elif any(p in note_lower for p in [
            'low confidence', 'low-confidence', 'borderline',
        ]):
            target_cls = 'LOW_CONFIDENCE'
        # HIGH_CONFIDENCE patterns
        elif any(p in note_lower for p in [
            'high confidence', 'should be high',
        ]):
            target_cls = 'HIGH_CONFIDENCE'

        if target_cls:
            page = find_page(pages, page_ref)
            if page:
                idx, story = find_story_on_page(page, start_seg, end_seg)
                if story:
                    old_cls = story['classification']
                    if old_cls != target_cls:
                        story['classification'] = target_cls
                        record = {
                            'key': key,
                            'old_classification': old_cls,
                            'new_classification': target_cls,
                            'note': note,
                            'source': 'canonical_review_2026-03-17',
                        }
                        applied.append(record)
                        print(f"  {key}: {old_cls} → {target_cls}")

                        # Annotate the story
                        if 'corrections' not in story:
                            story['corrections'] = []
                        story['corrections'].append({
                            'action': f'canonical_reclassify_{target_cls.lower()}',
                            'reason': f"Jeff's canonical review: {note}",
                            'source': 'canonical_review_2026-03-17',
                            'auto_applied': True,
                        })
                    else:
                        no_change_keys.append(key)
                else:
                    print(f"  WARNING: Story not found: {key}")
            else:
                print(f"  WARNING: Page not found: {page_ref}")
        else:
            # Unclear classification target — defer
            deferred.append({'key': key, 'verdict': verdict, 'note': note})

    print(f"\n  Classification changes applied: {len(applied)}")
    print(f"  Deferred (boundary/merge): {len(deferred)}")
    print(f"  No change needed: {len(no_change_keys)}")

    return applied, deferred


# ---------- Save ----------

def save_canonical(pages, auto_applied, needs_review, skipped, no_change,
                   canonical_applied=None, canonical_deferred=None):
    """Save the canonical file."""
    print(f"\n--- Saving canonical file ---")

    # Count stories
    total_stories = sum(len(p.get('stories', [])) for p in pages)
    review_count = sum(
        1 for p in pages
        for s in p.get('stories', [])
        if s.get('needs_review')
    )

    output = {
        'tractate': 'Ketubot',
        'version': 'canonical_v10_draft',
        'base_versions': {
            'pages_2_60': 'v7',
            'pages_61_112': 'v9',
        },
        'corrections_summary': {
            'prior_rounds_auto_applied': len(auto_applied),
            'prior_rounds_needs_review': len(needs_review),
            'prior_rounds_no_change': len(no_change),
            'prior_rounds_skipped': len(skipped),
            'canonical_review_applied': len(canonical_applied) if canonical_applied else 0,
            'canonical_review_deferred': len(canonical_deferred) if canonical_deferred else 0,
            'total_stories': total_stories,
            'review_count': review_count,
        },
        'auto_applied_log': auto_applied,
        'canonical_review_applied_log': canonical_applied or [],
        'canonical_review_deferred_log': canonical_deferred or [],
        'needs_review_log': needs_review,
        'pages': pages,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"  Saved: {OUTPUT_PATH}")
    print(f"  Total stories: {total_stories}")
    print(f"  Needs review: {review_count}")


# ---------- Main ----------

def refuse_if_would_regress():
    """Stop if the live canonical holds work this script cannot reproduce.

    This script rebuilds the golden from the base runs plus three 2026-02
    feedback files and the 2026-03 canonical review. The golden has since moved
    on WITHOUT it — the 2026-06-03 round, and on 2026-08-30 five stories from
    Jeff's blind 2005 list that the detector has never proposed. Re-running
    would silently delete them, and the golden is the most valuable artifact in
    the project.

    So this is no longer a build step; it is a historical reconstruction. It
    refuses to overwrite unless the caller states that they mean it.
    """
    import sys
    if not OUTPUT_PATH.exists():
        return
    live = json.loads(OUTPUT_PATH.read_text())
    stories = [s for pg in live.get('pages', []) for s in pg.get('stories', [])]
    unreproducible = [s for s in stories if s.get('source') == 'jeff_2005_list']
    rounds = live.get('corrections_summary', {}) or {}
    later_round = any('2026-06' in str(k) or '2026-08' in str(k)
                      for k in list(rounds.keys()) + list(live.keys()))
    if not unreproducible and not later_round:
        return
    if '--i-know-this-discards-later-work' in sys.argv:
        print("WARNING: overwriting the canonical, discarding later work, as instructed.")
        return
    print("=" * 70)
    print("  REFUSING TO WRITE — this would regress the golden dataset")
    print("=" * 70)
    print(f"  {OUTPUT_PATH.relative_to(PROJECT_ROOT)} currently holds "
          f"{len(stories)} stories.")
    if unreproducible:
        print(f"  {len(unreproducible)} of them came from Jeff's blind 2005 list and were")
        print("  never proposed by the detector, so this script cannot regenerate them:")
        for s in unreproducible:
            ref = (s.get('provenance') or {}).get('expert_ref', '?')
            print(f"      {ref}")
    if later_round:
        print("  The golden also carries correction rounds later than the three")
        print("  2026-02 files and the 2026-03 review this script reads.")
    print()
    print("  This script is now a HISTORICAL RECONSTRUCTION, not a build step.")
    print("  To rebuild the 2026-03 state for inspection, write elsewhere:")
    print("      OUTPUT_PATH override, or copy the file first.")
    print("  To overwrite anyway and lose the above:")
    print("      python3 scripts/build_canonical.py --i-know-this-discards-later-work")
    sys.exit(1)


def main():
    print("=" * 60)
    print("  BUILD CANONICAL KETUBOT STORIES")
    print("=" * 60)
    refuse_if_would_regress()

    # Step 1a: Load and merge
    pages = load_and_merge_base()
    fix_bad_merge_2_60(pages)

    # Step 1b: Load prior feedback (3 rounds)
    feedback = load_all_feedback()

    # Step 1c/1d: Apply prior corrections
    auto_applied, needs_review, skipped, no_change = apply_corrections(pages, feedback)

    # Step 1e: Annotate stories
    annotate_stories(pages, auto_applied, needs_review)

    # Step 2: Apply canonical review classification corrections
    canonical_review = load_canonical_review()
    canonical_applied, canonical_deferred = apply_canonical_classification_corrections(
        pages, canonical_review
    )

    # Print summary of prior round changes
    print("\n--- Prior round auto-applied changes ---")
    for r in auto_applied:
        action = r['action']
        key = r['key']
        if action == 'auto_not_a_story':
            print(f"  {key}: {r.get('old_classification', '?')} → NOT_A_STORY")
        elif action == 'auto_yes':
            print(f"  {key}: {r.get('old_classification', '?')} → YES")
        elif action == 'auto_low_confidence':
            print(f"  {key}: {r.get('old_classification', '?')} → LOW_CONFIDENCE")
        elif action == 'auto_remove':
            print(f"  {key}: REMOVED")
        elif action == 'auto_keep':
            print(f"  {key}: KEPT (reject_remove)")

    print("\n--- Prior round flagged for review ---")
    for r in needs_review:
        action = r['action']
        key = r['key']
        print(f"  {key}: {action}")
        if r.get('note'):
            note_preview = r['note'][:100] + ('...' if len(r['note']) > 100 else '')
            print(f"    Note: {note_preview}")

    # Save
    save_canonical(pages, auto_applied, needs_review, skipped, no_change,
                   canonical_applied, canonical_deferred)

    print("\n" + "=" * 60)
    print(f"  Done! Prior: {len(auto_applied)} auto-applied, "
          f"{len(needs_review)} flagged for review")
    print(f"  Canonical: {len(canonical_applied)} classification changes, "
          f"{len(canonical_deferred)} deferred")
    print("=" * 60)


if __name__ == '__main__':
    main()
