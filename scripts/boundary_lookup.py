#!/usr/bin/env python3
"""
Boundary Lookup Tool: Map Jeff's Hebrew text markers to segment indices.

For each boundary/merge correction in the canonical feedback analysis,
this script:
1. Loads the page's segments (English + Hebrew text)
2. Strips nikud (vowel marks) for fuzzy matching
3. Searches segments for Jeff's Hebrew markers
4. Outputs proposed boundary corrections with before/after diffs

Output: docs/golden/boundary_corrections.json

Usage:
  python3 scripts/boundary_lookup.py
"""

import json
import re
import unicodedata
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

ANALYSIS_PATH = PROJECT_ROOT / 'docs' / 'golden' / 'canonical_feedback_analysis.json'
CANONICAL_PATH = PROJECT_ROOT / 'results' / 'canonical' / 'ketubot_canonical.json'
OUTPUT_PATH = PROJECT_ROOT / 'docs' / 'golden' / 'boundary_corrections.json'


def strip_nikud(text):
    """Remove Hebrew vowel marks (nikud) and cantillation for fuzzy matching."""
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) not in ('Mn', 'Me')  # nonspacing/enclosing marks
    )


def strip_html(text):
    """Remove HTML tags from English text."""
    return re.sub(r'<[^>]+>', '', text)


def get_segment_text(seg, lang='hebrew'):
    """Get text from a segment, handling key variations."""
    if lang == 'hebrew':
        return seg.get('hebrew', seg.get('he', ''))
    return strip_html(seg.get('english', seg.get('en', '')))


def find_marker_in_segments(segments, marker_text, start_search=0, end_search=None):
    """
    Find which segment contains a Hebrew text marker.

    Returns: list of (segment_index, char_offset, context) matches
    """
    if end_search is None:
        end_search = len(segments)

    marker_clean = strip_nikud(marker_text).strip()
    if len(marker_clean) < 3:
        return []

    matches = []
    for i in range(start_search, min(end_search, len(segments))):
        seg_text = get_segment_text(segments[i], 'hebrew')
        seg_clean = strip_nikud(seg_text)

        # Try exact match first
        pos = seg_clean.find(marker_clean)
        if pos >= 0:
            context = seg_text[max(0, pos - 20):pos + len(marker_text) + 20]
            matches.append({
                'segment_index': i,
                'char_offset': pos,
                'match_type': 'exact',
                'context': context,
            })
            continue

        # Try partial match (first 20+ chars of marker)
        partial = marker_clean[:min(30, len(marker_clean))]
        if len(partial) >= 10:
            pos = seg_clean.find(partial)
            if pos >= 0:
                matches.append({
                    'segment_index': i,
                    'char_offset': pos,
                    'match_type': 'partial',
                    'context': seg_text[max(0, pos - 20):pos + 50],
                })

    return matches


def get_page(canonical, page_ref):
    """Find a page by reference."""
    for p in canonical.get('pages', []):
        if p['ref'] == page_ref:
            return p
    return None


def get_story(page, start_seg, end_seg):
    """Find a story on a page by segment range."""
    for i, story in enumerate(page.get('stories', [])):
        if story['start_segment'] == start_seg and story['end_segment'] == end_seg:
            return i, story
        # Overlap match
        s_range = set(range(story['start_segment'], story['end_segment'] + 1))
        f_range = set(range(start_seg, end_seg + 1))
        if len(s_range & f_range) > 0:
            return i, story
    return None, None


def get_adjacent_page_ref(page_ref, direction):
    """Get the ref for the previous or next Talmud page."""
    m = re.match(r'^(Ketubot )(\d+)([ab])$', page_ref)
    if not m:
        return None
    prefix, num, side = m.group(1), int(m.group(2)), m.group(3)
    if direction == 'next':
        if side == 'a':
            return f'{prefix}{num}b'
        else:
            return f'{prefix}{num + 1}a'
    elif direction == 'prev':
        if side == 'b':
            return f'{prefix}{num}a'
        else:
            return f'{prefix}{num - 1}b'
    return None


def text_preview(segments, start_seg, end_seg, lang='english', max_chars=150):
    """Get a text preview for a segment range."""
    texts = []
    for i in range(start_seg, min(end_seg + 1, len(segments))):
        texts.append(get_segment_text(segments[i], lang))
    full = ' '.join(texts)
    if len(full) > max_chars:
        return full[:max_chars] + '...'
    return full


def process_trim_boundary(entry, canonical):
    """Process a trim_boundary correction (BOUNDARY_OVEREXTENSION)."""
    key = entry['story_key']
    page_ref = entry['page_ref']
    start_seg = entry['start_segment']
    end_seg = entry['end_segment']
    note = entry['jeff_canonical_note']
    markers = entry.get('hebrew_boundary_markers', [])

    page = get_page(canonical, page_ref)
    if not page:
        return {'story_key': key, 'status': 'error', 'error': f'Page not found: {page_ref}'}

    _, story = get_story(page, start_seg, end_seg)
    if not story:
        return {'story_key': key, 'status': 'error', 'error': f'Story not found: {key}'}

    actual_start = story['start_segment']
    actual_end = story['end_segment']
    segments = page['segments']

    result = {
        'story_key': key,
        'correction_type': 'trim_boundary',
        'current_start': actual_start,
        'current_end': actual_end,
        'jeff_note': note,
        'markers_searched': markers,
    }

    # Try to find the marker that indicates where the story should end
    note_lower = note.lower()
    for marker in markers:
        matches = find_marker_in_segments(segments, marker, actual_start, actual_end + 2)
        if matches:
            best = matches[0]
            seg_idx = best['segment_index']

            # If the marker is found AND the note says "should end with" or
            # "story ends with", the marker text IS the endpoint
            if any(p in note_lower for p in ['story ends with', 'ends with', 'story ends at']):
                # The story should end AT this marker — find which segment
                result['proposed_end'] = seg_idx
                result['end_text_marker'] = marker
            elif any(p in note_lower for p in [
                'should not be included', 'need not be quoted',
                'should be omitted', 'not part of the story',
                "talmud's comment", "gemara's comment",
            ]):
                # The marker text is the START of what should be excluded
                # So the story ends at or before this marker's segment
                if best['char_offset'] < 30:
                    # Marker is near start of segment → exclude this segment
                    result['proposed_end'] = seg_idx - 1
                else:
                    # Marker is mid-segment → end at this segment but note sub-segment
                    result['proposed_end'] = seg_idx
                    result['end_text_marker'] = marker
            else:
                result['proposed_end'] = seg_idx
                result['end_text_marker'] = marker

            result['marker_match'] = best
            result['status'] = 'resolved'
            result['proposed_start'] = actual_start
            break
    else:
        # No marker found — try to infer from note
        if 'last few words' in note_lower or 'last line' in note_lower:
            result['proposed_start'] = actual_start
            result['proposed_end'] = actual_end - 1
            result['status'] = 'inferred'
            result['inference'] = 'Trimmed last segment based on note'
        else:
            result['status'] = 'needs_manual_review'
            result['reason'] = 'Could not locate boundary marker'

    # Add text previews
    if 'proposed_end' in result:
        result['before_text_preview'] = text_preview(
            segments, actual_start, actual_end)
        result['after_text_preview'] = text_preview(
            segments, actual_start, result['proposed_end'])

    return result


def process_extend_boundary(entry, canonical):
    """Process an extend_boundary correction (BOUNDARY_UNDEREXTENSION)."""
    key = entry['story_key']
    page_ref = entry['page_ref']
    start_seg = entry['start_segment']
    end_seg = entry['end_segment']
    note = entry['jeff_canonical_note']
    markers = entry.get('hebrew_boundary_markers', [])
    note_lower = note.lower()

    page = get_page(canonical, page_ref)
    if not page:
        return {'story_key': key, 'status': 'error', 'error': f'Page not found: {page_ref}'}

    _, story = get_story(page, start_seg, end_seg)
    if not story:
        return {'story_key': key, 'status': 'error', 'error': f'Story not found: {key}'}

    actual_start = story['start_segment']
    actual_end = story['end_segment']
    segments = page['segments']

    result = {
        'story_key': key,
        'correction_type': 'extend_boundary',
        'current_start': actual_start,
        'current_end': actual_end,
        'jeff_note': note,
        'markers_searched': markers,
    }

    # Determine direction (extend start or end?)
    extend_start = any(p in note_lower for p in [
        'first half', 'first line', 'begins with', 'should start',
        'previous page', 'prior page', 'story begins',
    ])
    extend_end = any(p in note_lower for p in [
        'next paragraph', 'should also be included', 'next line',
        'continuation', 'continues on', 'ends with the next',
    ])

    if extend_start:
        # Check if we need to look at the previous page
        if any(p in note_lower for p in ['previous page', 'prior page', '12a', '13a',
                                          'previous talmud page']):
            prev_ref = get_adjacent_page_ref(page_ref, 'prev')
            if prev_ref:
                prev_page = get_page(canonical, prev_ref)
                if prev_page:
                    prev_segs = prev_page['segments']
                    # Search for marker in previous page
                    for marker in markers:
                        matches = find_marker_in_segments(prev_segs, marker)
                        if matches:
                            result['extends_to_previous_page'] = prev_ref
                            result['previous_page_segment'] = matches[0]['segment_index']
                            result['marker_match'] = matches[0]
                            result['status'] = 'resolved_cross_page'
                            break
                    else:
                        # No marker found, but note says previous page
                        # Likely the last few segments of prev page
                        result['extends_to_previous_page'] = prev_ref
                        result['status'] = 'needs_manual_review'
                        result['reason'] = 'Need to check previous page segments'
        else:
            # Extend start on same page
            for marker in markers:
                matches = find_marker_in_segments(
                    segments, marker, 0, actual_start + 1)
                if matches:
                    result['proposed_start'] = matches[0]['segment_index']
                    result['proposed_end'] = actual_end
                    result['marker_match'] = matches[0]
                    result['status'] = 'resolved'
                    break
            else:
                # Try extending by one segment before
                if actual_start > 0:
                    result['proposed_start'] = actual_start - 1
                    result['proposed_end'] = actual_end
                    result['status'] = 'inferred'
                    result['inference'] = 'Extended start by one segment'
                else:
                    result['status'] = 'needs_manual_review'
                    result['reason'] = 'Cannot extend start — already at segment 0'

    elif extend_end:
        # Extend end on same page or next page
        if any(p in note_lower for p in ['next page', 'continues on the next']):
            next_ref = get_adjacent_page_ref(page_ref, 'next')
            if next_ref:
                result['extends_to_next_page'] = next_ref
                result['status'] = 'needs_merge'
                result['reason'] = 'Story continues on next page — needs cross-page merge'
        else:
            # Same page extension
            for marker in markers:
                matches = find_marker_in_segments(
                    segments, marker, actual_end, len(segments))
                if matches:
                    result['proposed_start'] = actual_start
                    result['proposed_end'] = matches[0]['segment_index']
                    result['marker_match'] = matches[0]
                    result['status'] = 'resolved'
                    break
            else:
                # Try extending by one segment
                if actual_end + 1 < len(segments):
                    result['proposed_start'] = actual_start
                    result['proposed_end'] = actual_end + 1
                    result['status'] = 'inferred'
                    result['inference'] = 'Extended end by one segment'
                else:
                    result['status'] = 'needs_merge'
                    result['reason'] = 'At page end — needs cross-page merge'
    else:
        # Unclear direction — use markers if available
        for marker in markers:
            # Search entire page
            matches = find_marker_in_segments(segments, marker)
            if matches:
                seg_idx = matches[0]['segment_index']
                if seg_idx < actual_start:
                    result['proposed_start'] = seg_idx
                    result['proposed_end'] = actual_end
                elif seg_idx > actual_end:
                    result['proposed_start'] = actual_start
                    result['proposed_end'] = seg_idx
                result['marker_match'] = matches[0]
                result['status'] = 'resolved'
                break
        else:
            result['status'] = 'needs_manual_review'
            result['reason'] = 'Could not determine extension direction'

    # Add text previews
    if 'proposed_start' in result and 'proposed_end' in result:
        result['before_text_preview'] = text_preview(
            segments, actual_start, actual_end)
        result['after_text_preview'] = text_preview(
            segments, result['proposed_start'], result['proposed_end'])

    return result


def process_merge(entry, canonical):
    """Process a merge correction."""
    key = entry['story_key']
    page_ref = entry['page_ref']
    start_seg = entry['start_segment']
    end_seg = entry['end_segment']
    note = entry['jeff_canonical_note']
    markers = entry.get('hebrew_boundary_markers', [])
    note_lower = note.lower()

    page = get_page(canonical, page_ref)
    if not page:
        return {'story_key': key, 'status': 'error', 'error': f'Page not found: {page_ref}'}

    _, story = get_story(page, start_seg, end_seg)
    if not story:
        return {'story_key': key, 'status': 'error', 'error': f'Story not found: {key}'}

    actual_start = story['start_segment']
    actual_end = story['end_segment']

    result = {
        'story_key': key,
        'correction_type': 'merge',
        'current_start': actual_start,
        'current_end': actual_end,
        'jeff_note': note,
        'markers_searched': markers,
    }

    # Determine merge type
    if any(p in note_lower for p in [
        'next page', 'continues on', 'top of', 'top lines',
    ]):
        # Cross-page merge
        next_ref = get_adjacent_page_ref(page_ref, 'next')
        result['merge_type'] = 'cross_page'
        result['merge_target_page'] = next_ref

        if next_ref:
            next_page = get_page(canonical, next_ref)
            if next_page:
                next_segs = next_page['segments']
                # Search for markers on next page
                for marker in markers:
                    matches = find_marker_in_segments(next_segs, marker)
                    if matches:
                        # The marker might indicate where the continuation ENDS
                        result['continuation_end_segment'] = matches[0]['segment_index']
                        result['marker_match'] = matches[0]
                        break

                # Default: continuation starts at segment 0
                result['continuation_start_segment'] = 0
                if 'continuation_end_segment' not in result:
                    # Heuristic: take first few segments of next page
                    # Look for the first story on next page to set upper bound
                    for ns in next_page.get('stories', []):
                        if ns['start_segment'] > 0:
                            result['continuation_end_segment'] = ns['start_segment'] - 1
                            break
                    else:
                        result['continuation_end_segment'] = min(2, len(next_segs) - 1)

                result['status'] = 'resolved_cross_page'
            else:
                result['status'] = 'error'
                result['error'] = f'Next page not found: {next_ref}'
        else:
            result['status'] = 'error'
            result['error'] = f'Could not determine next page from {page_ref}'

    elif any(p in note_lower for p in [
        'previous story', 'should go with', 'should be merged',
        'same story', 'continuation of', 'second part',
        'part of a longer',
    ]):
        # Same-page merge
        result['merge_type'] = 'same_page'

        # Find adjacent stories on the same page
        stories = page.get('stories', [])
        for i, s in enumerate(stories):
            if s['start_segment'] == actual_start and s['end_segment'] == actual_end:
                # Found our story — look for merge target
                if i > 0:
                    prev_story = stories[i - 1]
                    result['merge_with'] = {
                        'start_segment': prev_story['start_segment'],
                        'end_segment': prev_story['end_segment'],
                    }
                    result['proposed_merged_start'] = prev_story['start_segment']
                    result['proposed_merged_end'] = actual_end
                    result['status'] = 'resolved_same_page'
                else:
                    result['status'] = 'needs_manual_review'
                    result['reason'] = 'No preceding story to merge with'
                break
        else:
            result['status'] = 'needs_manual_review'
            result['reason'] = 'Could not find story in page stories list'
    else:
        result['merge_type'] = 'unclear'
        result['status'] = 'needs_manual_review'
        result['reason'] = 'Could not determine merge type from note'

    return result


def process_fix_merge(entry, canonical):
    """Process a fix_merge correction (wrong cross-page merge segments)."""
    key = entry['story_key']
    page_ref = entry['page_ref']
    note = entry['jeff_canonical_note']
    markers = entry.get('hebrew_boundary_markers', [])

    result = {
        'story_key': key,
        'correction_type': 'fix_merge',
        'jeff_note': note,
        'markers_searched': markers,
        'status': 'needs_manual_review',
        'reason': 'Fix-merge requires undoing existing merge and re-merging with correct segments',
    }

    return result


def process_approved_change(entry, canonical):
    """Process an 'approve' verdict — implement the proposed change."""
    key = entry['story_key']
    note = entry['jeff_canonical_note']
    page_ref = entry['page_ref']
    note_lower = note.lower()

    result = {
        'story_key': key,
        'correction_type': 'implement_approved',
        'jeff_note': note,
    }

    # Many 'approve' entries say "boundaries/merge are now correct"
    # meaning our proposed change was accepted
    if any(p in note_lower for p in [
        'now correct', 'are correct', 'is correct',
    ]) and not any(p in note_lower for p in [
        'should', 'need', 'has to', 'must', 'but',
    ]):
        result['status'] = 'already_correct'
        result['reason'] = 'Jeff confirms boundaries/merge are already correct'
        return result

    # Otherwise, there's a specific change to implement
    # Check the needs_review_log in canonical for the proposed change
    result['status'] = 'needs_manual_review'
    result['reason'] = 'Check needs_review_log for the proposed change to implement'

    return result


def process_adjustment(entry, canonical):
    """Process an 'adjust' verdict."""
    key = entry['story_key']
    note = entry['jeff_canonical_note']
    markers = entry.get('hebrew_boundary_markers', [])
    note_lower = note.lower()

    result = {
        'story_key': key,
        'correction_type': 'adjustment',
        'jeff_note': note,
        'markers_searched': markers,
    }

    if 'no adjustment needed' in note_lower or 'does not need adjustment' in note_lower:
        result['status'] = 'no_change'
        result['reason'] = 'Jeff says no adjustment needed'
        return result

    result['status'] = 'needs_manual_review'
    result['reason'] = 'Adjust verdict requires manual interpretation'
    return result


def main():
    print("=" * 60)
    print("  BOUNDARY LOOKUP TOOL")
    print("=" * 60)

    with open(ANALYSIS_PATH) as f:
        analysis = json.load(f)

    with open(CANONICAL_PATH) as f:
        canonical = json.load(f)

    corrections = []
    stats = {'resolved': 0, 'inferred': 0, 'needs_manual': 0,
             'already_correct': 0, 'no_change': 0, 'error': 0}

    for entry in analysis['corrections']:
        for action in entry['actions']:
            atype = action['type']

            if atype == 'no_action' or atype == 'reclassify':
                continue  # Classification changes handled in Phase 2

            if atype == 'trim_boundary':
                result = process_trim_boundary(entry, canonical)
            elif atype == 'extend_boundary':
                result = process_extend_boundary(entry, canonical)
            elif atype in ('merge', 'boundary_adjustment_from_note'):
                result = process_merge(entry, canonical)
            elif atype == 'fix_merge':
                result = process_fix_merge(entry, canonical)
            elif atype == 'implement_approved_change':
                result = process_approved_change(entry, canonical)
            elif atype == 'implement_adjustment':
                result = process_adjustment(entry, canonical)
            else:
                result = {
                    'story_key': entry['story_key'],
                    'correction_type': atype,
                    'status': 'unknown_type',
                }

            # Deduplicate by story_key + correction_type
            existing = next(
                (c for c in corrections
                 if c['story_key'] == result['story_key']
                 and c['correction_type'] == result['correction_type']),
                None
            )
            if existing:
                continue

            corrections.append(result)

            # Count status
            status = result.get('status', 'unknown')
            if status in ('resolved', 'resolved_cross_page', 'resolved_same_page'):
                stats['resolved'] += 1
            elif status == 'inferred':
                stats['inferred'] += 1
            elif status in ('already_correct', 'no_change'):
                stats['already_correct'] += 1
            elif 'error' in status:
                stats['error'] += 1
            else:
                stats['needs_manual'] += 1

    # Save output
    output = {
        'version': 'boundary_corrections_v1',
        'stats': stats,
        'total': len(corrections),
        'corrections': corrections,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # Print summary
    print(f"\nTotal corrections: {len(corrections)}")
    print(f"  Resolved: {stats['resolved']}")
    print(f"  Inferred: {stats['inferred']}")
    print(f"  Already correct: {stats['already_correct']}")
    print(f"  Needs manual review: {stats['needs_manual']}")
    print(f"  Errors: {stats['error']}")

    print(f"\n--- Resolved corrections ---")
    for c in corrections:
        s = c.get('status', '')
        if s in ('resolved', 'resolved_cross_page', 'resolved_same_page', 'inferred'):
            ctype = c.get('correction_type', '?')
            if 'proposed_start' in c and 'proposed_end' in c:
                print(f"  {c['story_key']} [{ctype}]: "
                      f"seg {c.get('current_start')}-{c.get('current_end')} → "
                      f"seg {c['proposed_start']}-{c['proposed_end']}")
            elif 'extends_to_previous_page' in c:
                print(f"  {c['story_key']} [{ctype}]: "
                      f"extends to {c['extends_to_previous_page']} seg {c.get('previous_page_segment', '?')}")
            elif 'merge_target_page' in c:
                print(f"  {c['story_key']} [{ctype}]: "
                      f"merge with {c['merge_target_page']} seg {c.get('continuation_start_segment', '?')}-{c.get('continuation_end_segment', '?')}")
            elif 'merge_with' in c:
                mw = c['merge_with']
                print(f"  {c['story_key']} [{ctype}]: "
                      f"merge with seg {mw['start_segment']}-{mw['end_segment']} "
                      f"→ combined {c.get('proposed_merged_start')}-{c.get('proposed_merged_end')}")
            else:
                print(f"  {c['story_key']} [{ctype}]: {s}")

    print(f"\n--- Needs manual review ---")
    for c in corrections:
        if c.get('status') in ('needs_manual_review', 'needs_merge'):
            print(f"  {c['story_key']}: {c.get('reason', 'unknown')}")
            note = c.get('jeff_note', '')[:100]
            if note:
                print(f"    Jeff: {note}")

    print(f"\n  Saved to: {OUTPUT_PATH}")


if __name__ == '__main__':
    main()
