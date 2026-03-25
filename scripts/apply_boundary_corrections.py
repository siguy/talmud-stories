#!/usr/bin/env python3
"""
Apply Boundary and Merge Corrections to the Canonical Dataset.

Implements all boundary/merge corrections from Jeff's canonical review
(2026-03-17) that were deferred from the classification phase (Phase 2).

This script modifies results/canonical/ketubot_canonical.json in place.
Each correction is explicitly defined based on analysis of Jeff's notes,
Hebrew markers, and segment text verification.

Usage:
  python3 scripts/apply_boundary_corrections.py
"""

import copy
import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
CANONICAL_PATH = PROJECT_ROOT / 'results' / 'canonical' / 'ketubot_canonical.json'


def get_page(pages, ref):
    for p in pages:
        if p['ref'] == ref:
            return p
    return None


def find_story(page, start, end):
    """Find story by exact or overlap match. Returns (index, story)."""
    for i, s in enumerate(page.get('stories', [])):
        if s['start_segment'] == start and s['end_segment'] == end:
            return i, s
    # Overlap match
    for i, s in enumerate(page.get('stories', [])):
        s_range = set(range(s['start_segment'], s['end_segment'] + 1))
        f_range = set(range(start, end + 1))
        if len(s_range & f_range) > 0:
            return i, s
    return None, None


def seg_preview(page, start, end, max_chars=120):
    """Get English text preview for segment range."""
    segs = page.get('segments', [])
    texts = []
    for i in range(start, min(end + 1, len(segs))):
        t = segs[i].get('english', segs[i].get('en', ''))
        t = re.sub(r'<[^>]+>', '', t)  # Strip HTML
        texts.append(t[:80])
    return ' | '.join(texts)[:max_chars]


def remove_needs_review(page, start, end, reason=''):
    """Remove needs_review flags from a story."""
    _, story = find_story(page, start, end)
    if not story:
        return False
    changed = False
    for field in ['needs_review', 'review_reason', 'jeff_note', 'proposed_change']:
        if field in story:
            del story[field]
            changed = True
    if changed:
        if 'corrections' not in story:
            story['corrections'] = []
        story['corrections'].append({
            'action': 'confirmed_correct',
            'reason': reason or 'Jeff confirmed boundaries/merge are correct',
            'source': 'canonical_review_2026-03-17',
            'auto_applied': True,
        })
    return changed


def trim_story_end(page, start, end, new_end, reason=''):
    """Trim a story's end segment."""
    _, story = find_story(page, start, end)
    if not story:
        return False
    old_end = story['end_segment']
    story['end_segment'] = new_end
    if 'corrections' not in story:
        story['corrections'] = []
    story['corrections'].append({
        'action': f'trim_end_{old_end}_to_{new_end}',
        'reason': reason,
        'source': 'canonical_review_2026-03-17',
        'auto_applied': True,
    })
    return True


def extend_story_start(page, start, end, new_start, reason=''):
    """Extend a story's start segment earlier."""
    _, story = find_story(page, start, end)
    if not story:
        return False
    old_start = story['start_segment']
    story['start_segment'] = new_start
    if 'corrections' not in story:
        story['corrections'] = []
    story['corrections'].append({
        'action': f'extend_start_{old_start}_to_{new_start}',
        'reason': reason,
        'source': 'canonical_review_2026-03-17',
        'auto_applied': True,
    })
    return True


def extend_story_end(page, start, end, new_end, reason=''):
    """Extend a story's end segment later."""
    _, story = find_story(page, start, end)
    if not story:
        return False
    old_end = story['end_segment']
    story['end_segment'] = new_end
    if 'corrections' not in story:
        story['corrections'] = []
    story['corrections'].append({
        'action': f'extend_end_{old_end}_to_{new_end}',
        'reason': reason,
        'source': 'canonical_review_2026-03-17',
        'auto_applied': True,
    })
    return True


def merge_same_page(page, story1_start, story1_end, story2_start, story2_end,
                    include_gap=False, reason=''):
    """
    Merge two stories on the same page. Extends story1 to cover story2's range,
    then removes story2.
    """
    idx1, s1 = find_story(page, story1_start, story1_end)
    idx2, s2 = find_story(page, story2_start, story2_end)
    if s1 is None or s2 is None:
        return False

    # Extend story1 to cover story2
    new_end = max(s1['end_segment'], s2['end_segment'])
    new_start = min(s1['start_segment'], s2['start_segment'])
    s1['start_segment'] = new_start
    s1['end_segment'] = new_end

    # Keep the higher confidence classification
    cls_order = {'YES': 4, 'HIGH_CONFIDENCE': 3, 'LOW_CONFIDENCE': 2, 'NOT_A_STORY': 1}
    if cls_order.get(s2['classification'], 0) > cls_order.get(s1['classification'], 0):
        s1['classification'] = s2['classification']

    # Remove needs_review from merged story
    for field in ['needs_review', 'review_reason', 'jeff_note', 'proposed_change']:
        s1.pop(field, None)
        s2.pop(field, None)

    if 'corrections' not in s1:
        s1['corrections'] = []
    s1['corrections'].append({
        'action': f'merged_with_{story2_start}-{story2_end}',
        'reason': reason,
        'source': 'canonical_review_2026-03-17',
        'auto_applied': True,
    })

    # Remove story2 — find it again by index since indices may have shifted
    stories = page['stories']
    for i, s in enumerate(stories):
        if s is s2:
            stories.pop(i)
            break

    return True


def add_cross_page_merge(pages, page1_ref, story_start, story_end,
                         page2_ref, p2_start, p2_end, reason=''):
    """
    Add a cross-page merge to a story on page1, linking to segments on page2.
    Removes any independent story on page2 that overlaps the merged range.
    """
    page1 = get_page(pages, page1_ref)
    page2 = get_page(pages, page2_ref)
    if not page1 or not page2:
        return False

    _, story = find_story(page1, story_start, story_end)
    if not story:
        return False

    # Set cross-page merge fields
    story['spans_pages'] = [page1_ref, page2_ref]
    story['start_segment_page2'] = p2_start
    story['end_segment_page2'] = p2_end
    story['cross_page_merge_v10'] = True

    # Remove needs_review if present
    for field in ['needs_review', 'review_reason', 'jeff_note', 'proposed_change']:
        story.pop(field, None)

    if 'corrections' not in story:
        story['corrections'] = []
    story['corrections'].append({
        'action': f'cross_page_merge_to_{page2_ref}_seg_{p2_start}-{p2_end}',
        'reason': reason,
        'source': 'canonical_review_2026-03-17',
        'auto_applied': True,
    })

    # Remove overlapping stories from page2
    p2_merge_range = set(range(p2_start, p2_end + 1))
    page2['stories'] = [
        s for s in page2.get('stories', [])
        if not (set(range(s['start_segment'], s['end_segment'] + 1)) & p2_merge_range)
    ]

    return True


def strip_cross_page_merge(pages, page_ref, story_start, story_end, reason=''):
    """Remove cross-page merge fields from a story."""
    page = get_page(pages, page_ref)
    if not page:
        return False

    _, story = find_story(page, story_start, story_end)
    if not story:
        return False

    removed_fields = []
    for field in ['spans_pages', 'start_segment_page2', 'end_segment_page2',
                  'cross_page_merge_v7', 'cross_page_stitched',
                  'cross_page_merge_v10']:
        if field in story:
            del story[field]
            removed_fields.append(field)

    if removed_fields:
        if 'corrections' not in story:
            story['corrections'] = []
        story['corrections'].append({
            'action': f'strip_cross_page_merge',
            'removed_fields': removed_fields,
            'reason': reason,
            'source': 'canonical_review_2026-03-17',
            'auto_applied': True,
        })
    return bool(removed_fields)


def remove_story(page, start, end):
    """Remove a story from a page."""
    stories = page.get('stories', [])
    for i, s in enumerate(stories):
        if s['start_segment'] == start and s['end_segment'] == end:
            stories.pop(i)
            return True
    return False


def main():
    print("=" * 60)
    print("  APPLY BOUNDARY & MERGE CORRECTIONS")
    print("=" * 60)

    with open(CANONICAL_PATH) as f:
        data = json.load(f)

    pages = data['pages']
    applied = []
    failed = []
    deferred = []

    def log_apply(key, desc):
        applied.append(f'{key}: {desc}')
        print(f'  ✓ {key}: {desc}')

    def log_fail(key, desc):
        failed.append(f'{key}: {desc}')
        print(f'  ✗ {key}: {desc}')

    def log_defer(key, desc):
        deferred.append(f'{key}: {desc}')
        print(f'  ⟳ {key}: {desc}')

    # ================================================================
    # A. Remove needs_review flags where Jeff confirmed correct (7 items)
    # ================================================================
    print('\n--- A. Confirming correct stories (removing needs_review) ---')

    confirmations = [
        ('Ketubot 105b', 14, 16, 'Jeff: merge and boundaries are now correct'),
        ('Ketubot 111b', 22, 22, 'Jeff: merge and boundaries are now correct'),
        ('Ketubot 62b', 14, 14, 'Jeff: highlight and boundaries are correct'),
        ('Ketubot 69a', 14, 16, 'Jeff: boundaries are correct now'),
        ('Ketubot 84b', 11, 11, 'Jeff: new boundaries and merge are now correct'),
        ('Ketubot 91a', 19, 20, 'Jeff: merge and boundaries are now correct'),
        ('Ketubot 94b', 6, 9, 'Jeff: All correct now'),
    ]

    for ref, start, end, reason in confirmations:
        page = get_page(pages, ref)
        if page and remove_needs_review(page, start, end, reason):
            log_apply(f'{ref}_{start}-{end}', 'confirmed correct')
        else:
            log_fail(f'{ref}_{start}-{end}', 'could not find story')

    # ================================================================
    # B. Boundary trims (story includes Talmud commentary — trim it)
    # ================================================================
    print('\n--- B. Trimming overextended boundaries ---')

    # 91b_2-7 → 2-3: Legal discussion follows after seg 3
    # Jeff: "boundaries not correct, legal discussion following need not be quoted"
    # Hebrew marker וְאִי לָא found at seg 3
    p91b = get_page(pages, 'Ketubot 91b')
    if p91b:
        if trim_story_end(p91b, 2, 7, 3, 'Jeff: story ends before legal discussion'):
            log_apply('91b_2-7', 'trimmed to 2-3')
        else:
            log_fail('91b_2-7', 'story not found')

    # 91b_8-10 → 8-9: Same pattern — legal discussion at end
    # Jeff: same instruction as 91b_2-7
    if p91b:
        if trim_story_end(p91b, 8, 10, 9, 'Jeff: same trim pattern as 91b_2-7'):
            log_apply('91b_8-10', 'trimmed to 8-9')
        else:
            log_fail('91b_8-10', 'story not found')

    # 91b_15-16 → 15-15: Story ends at seg 15
    # Jeff: "legal discussions that follow need not be quoted, story ends with וַאֲתָא אִיהוּ"
    if p91b:
        if trim_story_end(p91b, 15, 16, 15, 'Jeff: story ends at seg 15'):
            log_apply('91b_15-16', 'trimmed to 15-15')
        else:
            log_fail('91b_15-16', 'story not found')

    # 23a_13-16: Sub-segment trim at end of seg 16
    # Jeff: "last few words are not part of story (Talmud's comment)"
    # Hebrew marker found in seg 16 → can't change segment range, add text marker
    p23a = get_page(pages, 'Ketubot 23a')
    if p23a:
        _, s = find_story(p23a, 13, 16)
        if s:
            s['end_text_marker'] = 'טַעְמָא דְּלָא אֲתוֹ עֵדִים'
            s['end_trim_note'] = 'Text after this marker is Talmud commentary, not part of story'
            if 'corrections' not in s:
                s['corrections'] = []
            s['corrections'].append({
                'action': 'sub_segment_trim_end',
                'reason': 'Jeff: last few words are Talmud comment',
                'source': 'canonical_review_2026-03-17',
                'auto_applied': True,
            })
            log_apply('23a_13-16', 'added end_text_marker (sub-segment trim)')
        else:
            log_fail('23a_13-16', 'story not found')

    # 104b_7-15: Sub-segment trim at end of seg 15
    # Jeff: "last few words do not need to be included (Talmud's question)"
    p104b = get_page(pages, 'Ketubot 104b')
    if p104b:
        _, s = find_story(p104b, 7, 15)
        if s:
            s['end_text_marker'] = 'מֵעִיקָּרָא הוּא סְבַר הָנֵי וְקָא'
            s['end_trim_note'] = 'Text after this marker is Talmud question, not part of story'
            if 'corrections' not in s:
                s['corrections'] = []
            s['corrections'].append({
                'action': 'sub_segment_trim_end',
                'reason': "Jeff: last few words are Talmud's question",
                'source': 'canonical_review_2026-03-17',
                'auto_applied': True,
            })
            log_apply('104b_7-15', 'added end_text_marker (sub-segment trim)')
        else:
            log_fail('104b_7-15', 'story not found')

    # 60a_2-2: Sub-segment trim (follow-up question at end)
    # Jeff: "last line should not be included, follow-up question"
    p60a = get_page(pages, 'Ketubot 60a')
    if p60a:
        _, s = find_story(p60a, 2, 2)
        if s:
            s['end_trim_note'] = 'Follow-up question at end of segment should not be included'
            for field in ['needs_review', 'review_reason', 'jeff_note', 'proposed_change']:
                s.pop(field, None)
            if 'corrections' not in s:
                s['corrections'] = []
            s['corrections'].append({
                'action': 'sub_segment_trim_end',
                'reason': 'Jeff: follow-up question at end not part of story',
                'source': 'canonical_review_2026-03-17',
                'auto_applied': True,
            })
            log_apply('60a_2-2', 'marked sub-segment trim, removed needs_review')
        else:
            log_fail('60a_2-2', 'story not found')

    # 63b_8-8 → 64a_0-0: Jeff says trim Talmud's summary (last line)
    # Current: cross-page merge 63b_8 → 64a_0-0
    # Jeff: "last line is Talmud's summary, need not be included"
    # This means the 64a continuation should be trimmed
    p63b = get_page(pages, 'Ketubot 63b')
    if p63b:
        _, s = find_story(p63b, 8, 8)
        if s and s.get('spans_pages'):
            # Trim: don't include 64a content (Talmud's summary)
            # Remove the cross-page merge since the continuation is just summary
            for field in ['spans_pages', 'start_segment_page2', 'end_segment_page2',
                          'cross_page_merge_v7', 'cross_page_stitched']:
                s.pop(field, None)
            for field in ['needs_review', 'review_reason', 'jeff_note', 'proposed_change']:
                s.pop(field, None)
            if 'corrections' not in s:
                s['corrections'] = []
            s['corrections'].append({
                'action': 'strip_cross_page_merge_trim',
                'reason': "Jeff: 64a continuation is Talmud's summary, not part of story",
                'source': 'canonical_review_2026-03-17',
                'auto_applied': True,
            })
            log_apply('63b_8-8', 'removed cross-page merge to 64a (Talmud summary)')
        else:
            log_fail('63b_8-8', 'story not found or no cross-page merge')

    # 85b_9-9 → 86a: Jeff says "boundaries need adjustment, last line is Talmud's comment"
    # Hebrew marker: מֵעִיקָּרָא מַאי סְבַר, וּלְבַ
    # Jeff confirms merge is correct but boundaries need trim
    p85b = get_page(pages, 'Ketubot 85b')
    if p85b:
        _, s = find_story(p85b, 9, 9)
        if s:
            s['end_text_marker'] = "מֵעִיקָּרָא מַאי סְבַר, וּלְבַסּוֹף מַאי סְבַר"
            s['end_trim_note'] = "Text after this marker is Talmud's question, not part of story"
            for field in ['needs_review', 'review_reason', 'jeff_note', 'proposed_change']:
                s.pop(field, None)
            if 'corrections' not in s:
                s['corrections'] = []
            s['corrections'].append({
                'action': 'sub_segment_trim_end_with_merge',
                'reason': "Jeff: merge correct, but last portion is Talmud's comment",
                'source': 'canonical_review_2026-03-17',
                'auto_applied': True,
            })
            log_apply('85b_9-9', 'added end_text_marker, confirmed merge, removed needs_review')
        else:
            log_fail('85b_9-9', 'story not found')

    # ================================================================
    # C. Boundary extends (story starts/ends earlier/later)
    # ================================================================
    print('\n--- C. Extending boundaries ---')

    # 26a_1-1 → 0-1: Include first segment (story starts at seg 0)
    p26a = get_page(pages, 'Ketubot 26a')
    if p26a:
        if extend_story_start(p26a, 1, 1, 0, 'Jeff: first half of story not quoted'):
            log_apply('26a_1-1', 'extended start to seg 0')
        else:
            log_fail('26a_1-1', 'story not found')

    # 53a_2-3 → 1-3: Include seg 1 (story starts with Rav Pappa)
    p53a = get_page(pages, 'Ketubot 53a')
    if p53a:
        if extend_story_start(p53a, 2, 3, 1, 'Jeff: first half begins with Rav Pappa'):
            log_apply('53a_2-3', 'extended start to seg 1')
        else:
            log_fail('53a_2-3', 'story not found')

    # 77b_6-8 → 5-8: Include seg 5 (Rabbi Yehoshua ben Levi)
    p77b = get_page(pages, 'Ketubot 77b')
    if p77b:
        if extend_story_start(p77b, 6, 8, 5, 'Jeff: story begins with Rabbi Yehoshua ben Levi'):
            log_apply('77b_6-8', 'extended start to seg 5')
        else:
            log_fail('77b_6-8', 'story not found')

    # 56b_11-11: Extend end by 1 line (Shmuel's statement)
    # Jeff (adjust): "story ends with the next line"
    # Current: cross-page merge 56b_11 → 57a_0
    # Jeff says merge is correct but needs one more line
    p56b = get_page(pages, 'Ketubot 56b')
    if p56b:
        _, s = find_story(p56b, 11, 11)
        if s:
            if s.get('spans_pages'):
                # Already has cross-page merge — extend on page 2
                old_end = s.get('end_segment_page2', 0)
                s['end_segment_page2'] = old_end + 1
                for field in ['needs_review', 'review_reason', 'jeff_note', 'proposed_change']:
                    s.pop(field, None)
                if 'corrections' not in s:
                    s['corrections'] = []
                s['corrections'].append({
                    'action': f'extend_page2_end_{old_end}_to_{old_end+1}',
                    'reason': "Jeff: story ends with Shmuel's statement (next line)",
                    'source': 'canonical_review_2026-03-17',
                    'auto_applied': True,
                })
                log_apply('56b_11-11', f'extended p2 end from {old_end} to {old_end+1}')
            else:
                # Try extending on same page
                if extend_story_end(p56b, 11, 11, 12, "Jeff: story ends with Shmuel's statement"):
                    log_apply('56b_11-11', 'extended end to seg 12')
                else:
                    log_fail('56b_11-11', 'story not found')

    # 103a_24-32: Extend end (include next paragraph on 103b)
    # Jeff: "next paragraph should also be included: הָהוּא יוֹמָא דְּאַשְׁכָּבְתֵּיהּ"
    # Current: 103a_24-32 → 103b_0-2
    # Need to extend page2 end to include the next paragraph
    p103a = get_page(pages, 'Ketubot 103a')
    if p103a:
        _, s = find_story(p103a, 24, 32)
        if s and s.get('spans_pages'):
            old_end = s.get('end_segment_page2', 2)
            s['end_segment_page2'] = old_end + 1  # Include one more paragraph
            for field in ['needs_review', 'review_reason', 'jeff_note', 'proposed_change']:
                s.pop(field, None)
            if 'corrections' not in s:
                s['corrections'] = []
            s['corrections'].append({
                'action': f'extend_page2_end_{old_end}_to_{old_end+1}',
                'reason': 'Jeff: include next paragraph',
                'source': 'canonical_review_2026-03-17',
                'auto_applied': True,
            })
            log_apply('103a_24-32', f'extended 103b end from seg {old_end} to {old_end+1}')
        else:
            log_fail('103a_24-32', 'story not found or no cross-page merge')

    # ================================================================
    # D. Same-page merges
    # ================================================================
    print('\n--- D. Same-page merges ---')

    # 25b: merge 25b_4-4 + 25b_5-5 → 25b_4-5
    # Jeff: "25b_5-5 should be merged with previous, continuation of same story"
    p25b = get_page(pages, 'Ketubot 25b')
    if p25b:
        if merge_same_page(p25b, 4, 4, 5, 5,
                           reason='Jeff: 25b_5 is continuation of 25b_4'):
            log_apply('25b_4-4 + 25b_5-5', 'merged into 25b_4-5')
        else:
            log_fail('25b_4-4 + 25b_5-5', 'stories not found')

    # 85a: merge 85a_8-8 + 85a_9-10 → 85a_8-10
    # Jeff: "next paragraph is part of story, should be joined"
    p85a = get_page(pages, 'Ketubot 85a')
    if p85a:
        if merge_same_page(p85a, 8, 8, 9, 10,
                           reason='Jeff: 85a_9-10 is continuation of 85a_8'):
            log_apply('85a_8-8 + 85a_9-10', 'merged into 85a_8-10')
        else:
            log_fail('85a_8-8 + 85a_9-10', 'stories not found')

    # 8b: merge 8b_3-4 + 8b_6-10 → 8b_3-10
    # Jeff: "one long story"
    # Seg 5 is between them — it's narrative context, include it
    p8b = get_page(pages, 'Ketubot 8b')
    if p8b:
        if merge_same_page(p8b, 3, 4, 6, 10,
                           reason='Jeff: one long story (8b_3-5 + 6-10)'):
            log_apply('8b_3-4 + 8b_6-10', 'merged into 8b_3-10')
        else:
            log_fail('8b_3-4 + 8b_6-10', 'stories not found')

    # 62b: merge 62b_6-7 + 62b_9-9 → 62b_6-9
    # Jeff: "cut off in the middle, 62b_9-9 is second part"
    # Seg 8 is a proof text between them — include it
    p62b = get_page(pages, 'Ketubot 62b')
    if p62b:
        if merge_same_page(p62b, 6, 7, 9, 9,
                           reason='Jeff: 62b_9 is continuation of 62b_6-7'):
            log_apply('62b_6-7 + 62b_9-9', 'merged into 62b_6-9')
        else:
            log_fail('62b_6-7 + 62b_9-9', 'stories not found')

    # 103b_20-21: merge with previous death narrative (103a_24-32 → 103b)
    # Jeff: "include this with the previous story"
    # The 103a story already spans to 103b. Need to extend that merge.
    p103b = get_page(pages, 'Ketubot 103b')
    if p103a and p103b:
        _, death_story = find_story(p103a, 24, 32)
        if death_story and death_story.get('spans_pages'):
            # Extend the cross-page merge to include seg 20-21 on 103b
            old_p2_end = death_story.get('end_segment_page2', 2)
            # Need to extend from current end to 21
            if old_p2_end < 21:
                death_story['end_segment_page2'] = 21
                if 'corrections' not in death_story:
                    death_story['corrections'] = []
                death_story['corrections'].append({
                    'action': f'extend_page2_end_to_include_103b_20-21',
                    'reason': 'Jeff: include 103b_20-21 with death narrative',
                    'source': 'canonical_review_2026-03-17',
                    'auto_applied': True,
                })
                # Remove the independent 103b_20-21 story
                remove_story(p103b, 20, 21)
                log_apply('103b_20-21', 'absorbed into 103a death narrative')
            else:
                log_apply('103b_20-21', 'already included in death narrative')
        else:
            log_fail('103b_20-21', '103a death narrative not found')

    # ================================================================
    # E. New cross-page merges
    # ================================================================
    print('\n--- E. New cross-page merges ---')

    # 52b_17-17 → 53a: Story continues on next page
    # Jeff: "need continuation from next page (53a segments 2-3)"
    # But 53a_2-3 is already a separate story that we extended to 1-3
    # The continuation is likely seg 0-1 on 53a (before the existing story)
    # Actually, prior note says: "continues on next page, next selection here, 53a (segments 2-3)"
    # So 52b_17 continues into 53a_2-3 (now 1-3 after our extend)
    # Need to merge 52b_17 with 53a_1-3
    if add_cross_page_merge(pages, 'Ketubot 52b', 17, 17,
                            'Ketubot 53a', 0, 3,
                            'Jeff: story continues on 53a'):
        log_apply('52b_17-17 → 53a', 'cross-page merge to 53a seg 0-3')
    else:
        log_fail('52b_17-17 → 53a', 'could not create merge')

    # 54a_22-22 → 54b: Story continues on next page
    # Jeff: "continuation on next page should be included"
    # 54b has restored story from fix_bad_merge at seg 1-2
    # The continuation is at seg 0 on 54b
    if add_cross_page_merge(pages, 'Ketubot 54a', 22, 22,
                            'Ketubot 54b', 0, 0,
                            'Jeff: story continues on 54b'):
        log_apply('54a_22-22 → 54b', 'cross-page merge to 54b seg 0')
    else:
        log_fail('54a_22-22 → 54b', 'could not create merge')

    # 67b_17-17 → 68a: Story continues on next page
    # Jeff: "story continues, with a few words at the top of 68a"
    # Lookup found continuation ends at seg 15 on 68a — that seems too much
    # Conservative: merge with seg 0-1 on 68a
    p68a = get_page(pages, 'Ketubot 68a')
    if p68a:
        # Find first independent story on 68a to set upper bound
        first_story_start = None
        for s in p68a.get('stories', []):
            if s['start_segment'] > 0 and not s.get('restored_from_merge'):
                first_story_start = s['start_segment']
                break
        merge_end = (first_story_start - 1) if first_story_start and first_story_start > 0 else 1

        if add_cross_page_merge(pages, 'Ketubot 67b', 17, 17,
                                'Ketubot 68a', 0, merge_end,
                                'Jeff: story continues at top of 68a'):
            log_apply('67b_17-17 → 68a', f'cross-page merge to 68a seg 0-{merge_end}')
        else:
            log_fail('67b_17-17 → 68a', 'could not create merge')

    # 69b_10-12 → 70a: Story continues on next page
    # Jeff: "story continues with a few words on 70a"
    # Lookup: continuation ends at seg 2 on 70a
    p70a = get_page(pages, 'Ketubot 70a')
    if p70a:
        first_story_start = None
        for s in p70a.get('stories', []):
            if s['start_segment'] > 0:
                first_story_start = s['start_segment']
                break
        merge_end = (first_story_start - 1) if first_story_start and first_story_start > 0 else 2

        if add_cross_page_merge(pages, 'Ketubot 69b', 10, 12,
                                'Ketubot 70a', 0, min(merge_end, 2),
                                'Jeff: story continues at top of 70a'):
            log_apply('69b_10-12 → 70a', f'cross-page merge to 70a seg 0-{min(merge_end, 2)}')
        else:
            log_fail('69b_10-12 → 70a', 'could not create merge')

    # ================================================================
    # F. Special cases
    # ================================================================
    print('\n--- F. Special cases ---')

    # 111a_23-25: Strip cross-page merge fields (classification already fixed to LOW_CONFIDENCE)
    # Jeff: "111a portion is LOW_CONFIDENCE, 111b portion is NOT_A_STORY"
    # The 111b portion was part of the merge — just remove it
    if strip_cross_page_merge(pages, 'Ketubot 111a', 23, 25,
                              'Jeff: 111a is LOW_CONFIDENCE, 111b is NOT_A_STORY; un-merge'):
        log_apply('111a_23-25', 'stripped cross-page merge to 111b')
    else:
        log_fail('111a_23-25', 'could not strip merge')

    # 3a_9-9: Jeff says "no adjustment needed, boundaries correct"
    # Just an adjust verdict confirming no change needed
    p3a = get_page(pages, 'Ketubot 3a')
    if p3a:
        _, s = find_story(p3a, 9, 9)
        if not s:
            _, s = find_story(p3a, 9, 10)
        if s:
            for field in ['needs_review', 'review_reason', 'jeff_note', 'proposed_change']:
                s.pop(field, None)
            log_apply('3a_9-9', 'no adjustment needed (confirmed correct)')
        else:
            log_fail('3a_9-9', 'story not found')

    # 104a_1-5: Remove NEEDS_REVIEW placeholder
    # The actual merge is handled by 103b_24-25 → 104a on 103b page
    p104a = get_page(pages, 'Ketubot 104a')
    if p104a:
        _, s = find_story(p104a, 1, 5)
        if s:
            # This was a placeholder — the actual story is the 103b merge
            # Remove the placeholder
            remove_story(p104a, 1, 5)
            log_apply('104a_1-5', 'removed NEEDS_REVIEW placeholder (covered by 103b merge)')
        else:
            log_fail('104a_1-5', 'story not found')

    # ================================================================
    # G. Deferred corrections (need more investigation)
    # ================================================================
    print('\n--- G. Deferred (need further investigation) ---')

    deferred_list = [
        ('103b_3-3', 'Part of longer Rabbi Yehudah HaNasi narrative — needs grouping mechanism'),
        ('60b_2-3', 'Extend start to include Abaye reflection — need segment verification'),
        ('60b_5-9', 'Trim/extend — need to verify where story ends'),
        ('49b_12-12', 'Fix merge with 50a — need to undo and redo merge'),
        ('12b_0-0', 'Extend start from 12a — cross-page, need Sefaria text'),
    ]

    for key, reason in deferred_list:
        log_defer(key, reason)

    # ================================================================
    # Summary
    # ================================================================
    print(f'\n{"=" * 60}')
    print(f'  SUMMARY')
    print(f'{"=" * 60}')
    print(f'  Applied: {len(applied)}')
    print(f'  Failed: {len(failed)}')
    print(f'  Deferred: {len(deferred)}')

    # Count final stories
    total_stories = sum(len(p.get('stories', [])) for p in pages)
    review_count = sum(
        1 for p in pages
        for s in p.get('stories', [])
        if s.get('needs_review')
    )
    print(f'\n  Total stories: {total_stories}')
    print(f'  Still needs review: {review_count}')

    # Update corrections summary
    data['corrections_summary']['boundary_corrections_applied'] = len(applied)
    data['corrections_summary']['boundary_corrections_deferred'] = len(deferred)
    data['corrections_summary']['total_stories'] = total_stories
    data['corrections_summary']['review_count'] = review_count
    data['version'] = 'canonical_v10_golden'

    # Save
    with open(CANONICAL_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f'\n  Saved to: {CANONICAL_PATH}')


if __name__ == '__main__':
    main()
