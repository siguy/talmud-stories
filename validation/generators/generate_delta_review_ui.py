#!/usr/bin/env python3
"""
Generate a focused delta review UI comparing v7 → v8 results.
Shows only what changed so Jeff can review ~49 stories instead of ~103.

Tiers:
  Tier 1: Stories that now span pages (cross-page merges) — verify merged version
  Tier 2: Status flips, new stories, truly removed — review from scratch
  Tier 3: Classification-only changes (same structure) — quick confirmation

Usage:
  python3 validation/generators/generate_delta_review_ui.py
"""

import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent


def load_v7_from_git():
    """Load v7 results from git history (before v8 changes)."""
    result = subprocess.run(
        ['git', 'show', 'HEAD~7:results/v7/ketubot_v7_61-112.json'],
        capture_output=True, text=True, cwd=PROJECT_ROOT
    )
    if result.returncode != 0:
        print(f"Error loading v7 from git: {result.stderr}")
        sys.exit(1)
    return json.loads(result.stdout)


def load_v8():
    """Load current v8 results."""
    path = PROJECT_ROOT / 'results' / 'v7' / 'ketubot_v7_61-112.json'
    with open(path) as f:
        return json.load(f)


def load_cached_pages():
    """Load cached pages with segment text."""
    path = PROJECT_ROOT / 'results' / 'v7' / 'ketubot_pages_61-112.json'
    with open(path) as f:
        pages = json.load(f)
    # Build lookup by ref
    return {p['ref']: p['segments'] for p in pages}


def flatten_stories(data):
    """Flatten pages/stories into a list with page_ref and segments attached."""
    stories = []
    for page in data.get('pages', []):
        ref = page.get('ref', '')
        for story in page.get('stories', []):
            key = f"{ref}_{story['start_segment']}-{story['end_segment']}"
            stories.append({
                **story,
                'page_ref': ref,
                'key': key,
                'page_segments': page.get('segments', []),
            })
    return stories


def build_lookup(stories):
    """Build a dict keyed by story key."""
    return {s['key']: s for s in stories}


def find_overlap_match(story, lookup, min_overlap=0.5):
    """Find a story in lookup that overlaps with this one on the same page."""
    ref = story['page_ref']
    s_range = set(range(story['start_segment'], story['end_segment'] + 1))
    for key, other in lookup.items():
        if other['page_ref'] != ref:
            continue
        o_range = set(range(other['start_segment'], other['end_segment'] + 1))
        union = s_range | o_range
        if not union:
            continue
        overlap = len(s_range & o_range) / len(union)
        if overlap >= min_overlap:
            return key, other
    return None, None


def categorize_delta(v7_stories, v8_stories):
    """
    Compare v7 and v8 stories and categorize into tiers.

    Tier 1: Cross-page merges — stories that now span pages
    Tier 2: Status flips (NOT_A_STORY <-> real), new stories, truly removed
    Tier 3: Absorbed into cross-page merges + classification-only changes
    Skip: Unchanged stories
    """
    v7_lookup = build_lookup(v7_stories)
    v8_lookup = build_lookup(v8_stories)

    tier1 = []  # Cross-page merges
    tier2 = []  # Status flips, new, truly removed
    tier3 = []  # Absorbed + classification-only changes
    skipped = []
    matched_v7_keys = set()

    # Build a set of page2 segment ranges from cross-page v8 stories
    # so we can detect absorbed v7 stories
    cross_page_page2 = []
    for v8s in v8_stories:
        spans = v8s.get('spans_pages')
        if spans and len(spans) >= 2:
            cross_page_page2.append({
                'page2_ref': spans[1],
                'p2_start': v8s.get('start_segment_page2', 0),
                'p2_end': v8s.get('end_segment_page2', 0),
                'v8_key': v8s['key'],
            })

    for v8s in v8_stories:
        key = v8s['key']

        # Try exact key match first, then overlap
        v7s = None
        v7_key = None
        if key in v7_lookup:
            v7s = v7_lookup[key]
            v7_key = key
        else:
            v7_key, v7s = find_overlap_match(v8s, v7_lookup)

        if v7s and v7_key:
            matched_v7_keys.add(v7_key)

            v7_cls = v7s['classification']
            v8_cls = v8s['classification']
            v7_spans = v7s.get('spans_pages')
            v8_spans = v8s.get('spans_pages')
            v7_p2 = (v7s.get('start_segment_page2'), v7s.get('end_segment_page2'))
            v8_p2 = (v8s.get('start_segment_page2'), v8s.get('end_segment_page2'))

            same_cls = v7_cls == v8_cls
            same_spans = v7_spans == v8_spans
            same_p2 = v7_p2 == v8_p2

            if same_cls and same_spans and same_p2:
                skipped.append(v8s)
                continue

            entry = {
                'v8_story': v8s,
                'v7_story': v7s,
                'v7_key': v7_key,
                'v7_cls': v7_cls,
                'v8_cls': v8_cls,
            }

            # Tier 1: Now spans pages (didn't before)
            if v8_spans and not v7_spans:
                entry['change_type'] = 'cross_page_merge'
                tier1.append(entry)
            # Tier 2: Status flip (NOT_A_STORY <-> real)
            elif (v7_cls == 'NOT_A_STORY') != (v8_cls == 'NOT_A_STORY'):
                entry['change_type'] = 'status_flip'
                tier2.append(entry)
            # Tier 3: Classification-only change
            else:
                entry['change_type'] = 'classification_change'
                tier3.append(entry)
        else:
            # New in v8
            tier2.append({
                'v8_story': v8s,
                'v7_story': None,
                'v7_key': None,
                'v7_cls': None,
                'v8_cls': v8s['classification'],
                'change_type': 'new_in_v8',
            })

    # Removed from v8 — check if absorbed into a cross-page merge or truly removed
    for v7s in v7_stories:
        if v7s['key'] in matched_v7_keys:
            continue

        ref = v7s['page_ref']
        s_range = set(range(v7s['start_segment'], v7s['end_segment'] + 1))

        absorbed_by = None
        for cp in cross_page_page2:
            if cp['page2_ref'] == ref:
                cp_range = set(range(cp['p2_start'], cp['p2_end'] + 1))
                if s_range & cp_range:
                    absorbed_by = cp['v8_key']
                    break

        entry = {
            'v8_story': None,
            'v7_story': v7s,
            'v7_key': v7s['key'],
            'v7_cls': v7s['classification'],
            'v8_cls': None,
        }

        if absorbed_by:
            entry['change_type'] = 'absorbed'
            entry['absorbed_by'] = absorbed_by
            tier3.append(entry)
        else:
            entry['change_type'] = 'removed_in_v8'
            tier2.append(entry)

    return tier1, tier2, tier3, skipped


def attach_page2_segments(stories, cached_pages):
    """For cross-page stories, attach page2 segments from cached pages."""
    for s in stories:
        spans = s.get('spans_pages')
        if spans and len(spans) >= 2:
            page2_ref = spans[1]
            if page2_ref in cached_pages:
                s['page2_segments'] = cached_pages[page2_ref]


def build_delta_data(tier1, tier2, tier3, skipped, cached_pages):
    """Build the data structure for the HTML template."""
    # Attach page2 segments to cross-page stories
    for entry in tier1:
        attach_page2_segments([entry['v8_story']], cached_pages)
    for entry in tier2 + tier3:
        if entry['v8_story']:
            attach_page2_segments([entry['v8_story']], cached_pages)

    # Also attach cached segments to removed stories (v7 only)
    for entry in tier2:
        if entry['change_type'] == 'removed_in_v8' and entry['v7_story']:
            v7s = entry['v7_story']
            ref = v7s['page_ref']
            if ref in cached_pages:
                v7s['page_segments'] = cached_pages[ref]

    return {
        'tier1': [serialize_entry(e) for e in tier1],
        'tier2': [serialize_entry(e) for e in tier2],
        'tier3': [serialize_entry(e) for e in tier3],
        'counts': {
            'tier1': len(tier1),
            'tier2': len(tier2),
            'tier3': len(tier3),
            'skipped': len(skipped),
            'total_review': len(tier1) + len(tier2) + len(tier3),
        },
    }


def serialize_entry(entry):
    """Convert a delta entry to JSON-serializable form."""
    v8s = entry['v8_story']
    v7s = entry['v7_story']

    result = {
        'change_type': entry['change_type'],
        'v7_cls': entry['v7_cls'],
        'v8_cls': entry['v8_cls'],
        'v7_key': entry['v7_key'],
    }

    if v8s:
        result['story'] = {
            'key': v8s['key'],
            'page_ref': v8s['page_ref'],
            'start_segment': v8s['start_segment'],
            'end_segment': v8s['end_segment'],
            'classification': v8s['classification'],
            'criteria': v8s.get('criteria', {}),
            'criteria_met_count': v8s.get('criteria_met_count', 0),
            'one_sentence_summary': v8s.get('one_sentence_summary', ''),
            'classification_reasoning': v8s.get('classification_reasoning', ''),
            'spans_pages': v8s.get('spans_pages'),
            'start_segment_page2': v8s.get('start_segment_page2'),
            'end_segment_page2': v8s.get('end_segment_page2'),
            'page_segments': v8s.get('page_segments', []),
            'page2_segments': v8s.get('page2_segments', []),
            'disqualifiers_found': v8s.get('disqualifiers_found', []),
            'weakeners_found': v8s.get('weakeners_found', []),
        }
    elif v7s:
        # Removed story — use v7 data
        result['story'] = {
            'key': v7s['key'],
            'page_ref': v7s['page_ref'],
            'start_segment': v7s['start_segment'],
            'end_segment': v7s['end_segment'],
            'classification': v7s['classification'],
            'criteria': v7s.get('criteria', {}),
            'criteria_met_count': v7s.get('criteria_met_count', 0),
            'one_sentence_summary': v7s.get('one_sentence_summary', ''),
            'classification_reasoning': v7s.get('classification_reasoning', ''),
            'spans_pages': v7s.get('spans_pages'),
            'start_segment_page2': v7s.get('start_segment_page2'),
            'end_segment_page2': v7s.get('end_segment_page2'),
            'page_segments': v7s.get('page_segments', []),
            'page2_segments': v7s.get('page2_segments', []),
            'disqualifiers_found': v7s.get('disqualifiers_found', []),
            'weakeners_found': v7s.get('weakeners_found', []),
        }

    # Attach v7 summary for comparison
    if v7s:
        result['v7_summary'] = v7s.get('one_sentence_summary', '')
        result['v7_segments'] = f"{v7s['start_segment']}-{v7s['end_segment']}"
    if v8s:
        result['v8_summary'] = v8s.get('one_sentence_summary', '')

    # For absorbed stories, note what they were absorbed into
    if entry.get('absorbed_by'):
        result['absorbed_by'] = entry['absorbed_by']

    return result


def generate_html(delta_data, output_file):
    """Generate the delta review HTML."""
    data_json = json.dumps(delta_data, ensure_ascii=False, indent=2)
    counts = delta_data['counts']

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>v8 Delta Review — Ketubot 61-112</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; padding: 20px; line-height: 1.6; }}
        .container {{ max-width: 1600px; margin: 0 auto; }}

        /* Header */
        .header {{ background: white; padding: 30px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 30px; }}
        .header h1 {{ color: #2c3e50; margin-bottom: 10px; }}
        .version-badge {{ display: inline-block; padding: 6px 12px; background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%); color: white; border-radius: 6px; font-size: 14px; font-weight: 600; margin-left: 15px; }}
        .header p {{ color: #7f8c8d; font-size: 16px; margin-top: 10px; }}

        /* Stats */
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 15px; margin-top: 20px; }}
        .stat-box {{ background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }}
        .stat-box .number {{ font-size: 28px; font-weight: bold; }}
        .stat-box .label {{ color: #7f8c8d; font-size: 13px; margin-top: 5px; }}
        .stat-tier1 .number {{ color: #e74c3c; }}
        .stat-tier2 .number {{ color: #f39c12; }}
        .stat-tier3 .number {{ color: #3498db; }}
        .stat-skip .number {{ color: #95a5a6; }}
        .stat-reviewed .number {{ color: #27ae60; }}

        /* Controls */
        .controls {{ background: white; padding: 25px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        .filters {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; }}
        .control-group {{ margin-bottom: 15px; }}
        .control-group:last-child {{ margin-bottom: 0; }}
        .control-group label {{ display: block; font-weight: 600; color: #2c3e50; margin-bottom: 8px; }}
        select, input[type="text"] {{ width: 100%; padding: 10px; border: 2px solid #e0e0e0; border-radius: 6px; font-size: 14px; }}

        /* Tier headers */
        .tier-header {{ background: white; padding: 20px 25px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin: 30px 0 15px 0; }}
        .tier-header h2 {{ color: #2c3e50; margin-bottom: 8px; font-size: 22px; }}
        .tier-header p {{ color: #7f8c8d; font-size: 15px; }}
        .tier-header.tier1 {{ border-left: 5px solid #e74c3c; }}
        .tier-header.tier2 {{ border-left: 5px solid #f39c12; }}
        .tier-header.tier3 {{ border-left: 5px solid #3498db; }}

        /* Story Cards */
        .story-card {{ background: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 20px; overflow: hidden; }}
        .story-card.class-YES {{ border-left: 5px solid #27ae60; }}
        .story-card.class-HIGH_CONFIDENCE {{ border-left: 5px solid #3498db; }}
        .story-card.class-LOW_CONFIDENCE {{ border-left: 5px solid #f39c12; }}
        .story-card.class-NOT_A_STORY {{ border-left: 5px solid #95a5a6; }}
        .story-card.removed {{ border-left: 5px solid #e74c3c; background: #fff5f5; }}

        .story-header {{ padding: 20px; background: #f8f9fa; border-bottom: 2px solid #e0e0e0; }}
        .story-ref {{ font-size: 20px; font-weight: bold; color: #2c3e50; margin-bottom: 10px; }}
        .story-meta {{ display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }}

        .badge {{ padding: 6px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; text-transform: uppercase; }}
        .class-YES-badge {{ background: #d4edda; color: #155724; }}
        .class-HIGH_CONFIDENCE-badge {{ background: #cfe2ff; color: #084298; }}
        .class-LOW_CONFIDENCE-badge {{ background: #fff3cd; color: #856404; }}
        .class-NOT_A_STORY-badge {{ background: #f8d7da; color: #721c24; }}
        .criteria-badge {{ background: #e7f3ff; color: #0066cc; }}
        .change-badge {{ background: #f0e6ff; color: #6f42c1; font-weight: 700; }}
        .v7-badge {{ background: #e0e0e0; color: #555; font-size: 11px; text-decoration: line-through; }}
        .removed-badge {{ background: #e74c3c; color: white; }}
        .new-badge {{ background: #27ae60; color: white; }}
        .spans-badge {{ background: #e74c3c; color: white; }}
        .arrow {{ color: #7f8c8d; font-weight: bold; font-size: 14px; }}

        /* Story Content */
        .story-content {{ padding: 20px; }}
        .summary {{ background: #f0f7ff; padding: 15px; border-left: 4px solid #3498db; margin-bottom: 20px; font-style: italic; }}

        /* Change description */
        .change-description {{ background: #f0e6ff; padding: 15px; border-left: 4px solid #6f42c1; margin-bottom: 20px; font-size: 14px; }}
        .change-description strong {{ color: #6f42c1; }}

        /* Text display */
        .text-container {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }}
        @media (max-width: 1024px) {{ .text-container {{ grid-template-columns: 1fr; }} }}
        .text-section h3 {{ color: #2c3e50; margin-bottom: 10px; font-size: 16px; }}
        .text-content {{ padding: 15px; background: #f8f9fa; border-radius: 8px; line-height: 1.8; font-size: 15px; max-height: 500px; overflow-y: auto; }}
        .text-content div {{ margin: 5px 0; }}
        .hebrew {{ direction: rtl; text-align: right; font-family: 'Times New Roman', serif; font-size: 18px; }}
        .story-text {{ background: #fff3cd; padding: 8px; border-left: 3px solid #f39c12; margin: 5px 0; }}
        .page-break {{ background: #e8e8e8; padding: 6px 12px; margin: 12px 0; font-size: 12px; font-weight: 600; color: #666; text-align: center; border-radius: 4px; }}

        /* Criteria breakdown */
        .criteria-breakdown {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .criteria-breakdown h3 {{ color: #2c3e50; margin-bottom: 15px; font-size: 16px; }}
        .criterion {{ display: flex; align-items: center; padding: 8px 0; }}
        .criterion-icon {{ width: 20px; margin-right: 10px; font-size: 16px; }}
        .criterion-met {{ color: #27ae60; }}
        .criterion-unmet {{ color: #e74c3c; }}
        .criterion-name {{ font-weight: 600; color: #2c3e50; flex: 1; }}
        .criterion-detail {{ color: #7f8c8d; font-size: 13px; }}

        /* Disqualifiers/Weakeners */
        .flags-section {{ background: #fff9e6; padding: 15px; border-left: 4px solid #f39c12; margin-bottom: 20px; }}
        .flags-section.disqualifiers {{ background: #f8d7da; border-left-color: #e74c3c; }}
        .flags-section h4 {{ color: #2c3e50; margin-bottom: 10px; font-size: 14px; }}
        .flag-item {{ display: inline-block; padding: 4px 10px; background: white; border-radius: 4px; margin: 3px; font-size: 12px; }}

        /* Reasoning */
        .reasoning {{ margin-bottom: 15px; padding: 15px; background: #f0f7ff; border-left: 4px solid #3498db; font-size: 14px; }}

        /* Feedback section */
        .feedback-section {{ padding: 20px; background: #f8f9fa; border-top: 2px solid #e0e0e0; }}
        .feedback-row {{ display: flex; gap: 15px; align-items: center; flex-wrap: wrap; }}
        .feedback-btn {{ padding: 10px 24px; border: 2px solid; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; background: white; }}
        .feedback-btn.correct {{ border-color: #27ae60; color: #27ae60; }}
        .feedback-btn.correct:hover, .feedback-btn.correct.active {{ background: #27ae60; color: white; }}
        .feedback-btn.incorrect {{ border-color: #e74c3c; color: #e74c3c; }}
        .feedback-btn.incorrect:hover, .feedback-btn.incorrect.active {{ background: #e74c3c; color: white; }}
        .feedback-btn.confirm-remove {{ border-color: #6f42c1; color: #6f42c1; }}
        .feedback-btn.confirm-remove:hover, .feedback-btn.confirm-remove.active {{ background: #6f42c1; color: white; }}
        .feedback-btn.reject-remove {{ border-color: #e67e22; color: #e67e22; }}
        .feedback-btn.reject-remove:hover, .feedback-btn.reject-remove.active {{ background: #e67e22; color: white; }}
        .feedback-note {{ flex: 1; min-width: 250px; }}
        .feedback-note input {{ width: 100%; padding: 10px; border: 2px solid #e0e0e0; border-radius: 6px; }}

        /* Export */
        .export-section {{ text-align: center; margin-top: 30px; padding: 30px; background: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .export-btn {{ padding: 15px 40px; background: #3498db; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; margin: 5px; }}
        .export-btn:hover {{ background: #2980b9; }}

        .no-results {{ text-align: center; padding: 60px 20px; color: #7f8c8d; font-size: 18px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>v8 Delta Review <span class="version-badge">v7 &rarr; v8</span></h1>
            <p>{counts['total_review']} stories need attention ({counts['skipped']} unchanged from v7, skipped)</p>
            <div class="stats" id="stats"></div>
        </div>

        <div class="controls">
            <div class="filters">
                <div class="control-group">
                    <label>Tier Filter</label>
                    <select id="filterTier">
                        <option value="all">All Tiers</option>
                        <option value="tier1">Tier 1: Cross-Page Merges ({counts['tier1']})</option>
                        <option value="tier2">Tier 2: New / Status Changed / Removed ({counts['tier2']})</option>
                        <option value="tier3">Tier 3: Classification Changes ({counts['tier3']})</option>
                    </select>
                </div>
                <div class="control-group">
                    <label>Change Type</label>
                    <select id="filterChange">
                        <option value="all">All Change Types</option>
                        <option value="cross_page_merge">Cross-Page Merge</option>
                        <option value="status_flip">Status Flip</option>
                        <option value="new_in_v8">New in v8</option>
                        <option value="removed_in_v8">Removed in v8</option>
                        <option value="absorbed">Absorbed into Merge</option>
                        <option value="classification_change">Classification Change</option>
                    </select>
                </div>
                <div class="control-group">
                    <label>Page Reference</label>
                    <input type="text" id="searchPage" placeholder="e.g., 84b, 103a">
                </div>
                <div class="control-group">
                    <label>Reviewer Name</label>
                    <input type="text" id="reviewerName" placeholder="Your name">
                </div>
            </div>
        </div>

        <div id="storiesContainer"><div class="no-results">Loading stories...</div></div>

        <div class="export-section">
            <h2>Export Delta Review Feedback</h2>
            <p style="margin: 15px 0; color: #7f8c8d;">Feedback auto-saves to browser storage (separate from v7 feedback)</p>
            <button class="export-btn" onclick="exportFeedback()">Download Feedback JSON</button>
            <button class="export-btn" onclick="clearFeedback()" style="background: #e74c3c;">Clear All</button>
        </div>
    </div>

    <script id="deltaData" type="application/json">
{data_json}
    </script>

    <script>
        const deltaData = JSON.parse(document.getElementById('deltaData').textContent);
        let feedback = JSON.parse(localStorage.getItem('v8_delta_feedback') || '{{}}');

        const TIER_CONFIG = {{
            tier1: {{
                title: 'Tier 1: Cross-Page Stories',
                description: 'These stories now span two pages (were cut off in v7). Does the merged version cover the full narrative?',
                cssClass: 'tier1',
            }},
            tier2: {{
                title: 'Tier 2: New, Status-Changed, or Removed',
                description: 'Review from scratch. New stories, status flips (NOT_A_STORY \\u2194 real), and removed stories.',
                cssClass: 'tier2',
            }},
            tier3: {{
                title: 'Tier 3: Absorbed + Reclassified',
                description: 'Stories absorbed into cross-page merges (confirm merge is correct) and classification-only changes (e.g. YES \\u2192 HIGH). Quick confirmation.',
                cssClass: 'tier3',
            }},
        }};

        const CHANGE_LABELS = {{
            cross_page_merge: 'Cross-Page Merge',
            status_flip: 'Status Flip',
            new_in_v8: 'New in v8',
            removed_in_v8: 'Removed in v8',
            absorbed: 'Absorbed into Merge',
            classification_change: 'Classification Change',
        }};

        function getStoryText(story) {{
            const start = story.start_segment;
            const end = story.end_segment;
            const segments = story.page_segments || [];

            const contextStart = Math.max(0, start - 1);
            const contextEnd = Math.min(segments.length - 1, end + 1);

            let englishParts = [];
            let hebrewParts = [];

            // Page 1 segments
            for (let i = contextStart; i <= contextEnd; i++) {{
                const seg = segments[i];
                if (!seg) continue;
                const isStory = i >= start && i <= end;
                const cls = isStory ? 'story-text' : '';
                if (seg.english) englishParts.push('<div class="' + cls + '">' + seg.english + '</div>');
                if (seg.hebrew) hebrewParts.push('<div class="' + cls + '">' + seg.hebrew + '</div>');
            }}

            // Page 2 segments for cross-page stories
            if (story.spans_pages && story.page2_segments && story.page2_segments.length > 0) {{
                const p2Start = story.start_segment_page2;
                const p2End = story.end_segment_page2;
                if (p2Start != null && p2End != null) {{
                    const p2ContextStart = Math.max(0, p2Start - 1);
                    const p2ContextEnd = Math.min(story.page2_segments.length - 1, p2End + 1);

                    englishParts.push('<div class="page-break">&mdash; ' + story.spans_pages[1] + ' (continued) &mdash;</div>');
                    hebrewParts.push('<div class="page-break">&mdash; ' + story.spans_pages[1] + ' (continued) &mdash;</div>');

                    for (let i = p2ContextStart; i <= p2ContextEnd; i++) {{
                        const seg = story.page2_segments[i];
                        if (!seg) continue;
                        const isStory = i >= p2Start && i <= p2End;
                        const cls = isStory ? 'story-text' : '';
                        if (seg.english) englishParts.push('<div class="' + cls + '">' + seg.english + '</div>');
                        if (seg.hebrew) hebrewParts.push('<div class="' + cls + '">' + seg.hebrew + '</div>');
                    }}
                }}
            }}

            return {{ english: englishParts.join(''), hebrew: hebrewParts.join('') }};
        }}

        function renderStats() {{
            const reviewed = Object.keys(feedback).length;
            document.getElementById('stats').innerHTML = `
                <div class="stat-box stat-tier1"><div class="number">${{deltaData.counts.tier1}}</div><div class="label">Tier 1: Cross-Page</div></div>
                <div class="stat-box stat-tier2"><div class="number">${{deltaData.counts.tier2}}</div><div class="label">Tier 2: New/Flip/Removed</div></div>
                <div class="stat-box stat-tier3"><div class="number">${{deltaData.counts.tier3}}</div><div class="label">Tier 3: Reclassified</div></div>
                <div class="stat-box stat-skip"><div class="number">${{deltaData.counts.skipped}}</div><div class="label">Unchanged (skipped)</div></div>
                <div class="stat-box stat-reviewed"><div class="number">${{reviewed}}</div><div class="label">Reviewed</div></div>
            `;
        }}

        function renderChangeDescription(entry) {{
            const ct = entry.change_type;
            if (ct === 'cross_page_merge') {{
                const pages = entry.story.spans_pages || [];
                return '<div class="change-description"><strong>Cross-page merge:</strong> This story now spans ' +
                    pages.join(' \\u2192 ') + '. In v7 it was limited to one page. Verify the merged version covers the full narrative.</div>';
            }}
            if (ct === 'status_flip') {{
                return '<div class="change-description"><strong>Status flip:</strong> Changed from ' +
                    (entry.v7_cls || '?') + ' \\u2192 ' + (entry.v8_cls || '?') + '. Review from scratch.</div>';
            }}
            if (ct === 'new_in_v8') {{
                return '<div class="change-description"><strong>New in v8:</strong> This story was not detected in v7. Review from scratch.</div>';
            }}
            if (ct === 'removed_in_v8') {{
                return '<div class="change-description"><strong>Removed in v8:</strong> This story existed in v7 as ' +
                    (entry.v7_cls || '?') + ' but is no longer detected. Confirm removal is correct.</div>';
            }}
            if (ct === 'absorbed') {{
                return '<div class="change-description"><strong>Absorbed into merge:</strong> This v7 story (' +
                    (entry.v7_cls || '?') + ') was merged into cross-page story <em>' +
                    (entry.absorbed_by || '?') + '</em>. Quick confirm the merge is correct.</div>';
            }}
            if (ct === 'classification_change') {{
                return '<div class="change-description"><strong>Reclassified:</strong> ' +
                    (entry.v7_cls || '?') + ' \\u2192 ' + (entry.v8_cls || '?') + '. Quick confirmation.</div>';
            }}
            return '';
        }}

        function renderStory(entry, tier) {{
            const story = entry.story;
            if (!story) return '';

            const storyId = story.key;
            const fb = feedback[storyId] || {{}};
            const texts = getStoryText(story);
            const criteria = story.criteria || {{}};
            const disqs = story.disqualifiers_found || [];
            const weaks = story.weakeners_found || [];
            const isRemoved = entry.change_type === 'removed_in_v8';
            const isAbsorbed = entry.change_type === 'absorbed';
            const cardClass = isRemoved ? 'removed' : isAbsorbed ? 'class-' + story.classification : 'class-' + story.classification;

            // Build meta badges
            let metaBadges = '';
            if (entry.v7_cls && entry.v8_cls && entry.v7_cls !== entry.v8_cls) {{
                metaBadges += '<span class="badge v7-badge">' + entry.v7_cls.replace('_', ' ') + '</span>';
                metaBadges += '<span class="arrow">\\u2192</span>';
                metaBadges += '<span class="badge class-' + entry.v8_cls + '-badge">' + entry.v8_cls.replace('_', ' ') + '</span>';
            }} else if (isRemoved) {{
                metaBadges += '<span class="badge removed-badge">REMOVED</span>';
                metaBadges += '<span class="badge class-' + entry.v7_cls + '-badge">was ' + entry.v7_cls.replace('_', ' ') + '</span>';
            }} else if (isAbsorbed) {{
                metaBadges += '<span class="badge change-badge">ABSORBED</span>';
                metaBadges += '<span class="badge class-' + entry.v7_cls + '-badge">was ' + entry.v7_cls.replace('_', ' ') + '</span>';
            }} else if (entry.change_type === 'new_in_v8') {{
                metaBadges += '<span class="badge new-badge">NEW</span>';
                metaBadges += '<span class="badge class-' + entry.v8_cls + '-badge">' + entry.v8_cls.replace('_', ' ') + '</span>';
            }} else {{
                metaBadges += '<span class="badge class-' + story.classification + '-badge">' + story.classification.replace('_', ' ') + '</span>';
            }}

            if (story.spans_pages) {{
                metaBadges += '<span class="badge spans-badge">Spans ' + story.spans_pages.join(' + ') + '</span>';
            }}
            metaBadges += '<span class="badge criteria-badge">' + story.criteria_met_count + '/6 Criteria</span>';
            metaBadges += '<span class="badge change-badge">' + (CHANGE_LABELS[entry.change_type] || entry.change_type) + '</span>';

            // Feedback buttons
            let feedbackButtons = '';
            if (isRemoved) {{
                feedbackButtons = `
                    <button class="feedback-btn confirm-remove ${{fb.verdict === 'confirm_remove' ? 'active' : ''}}"
                            onclick="setVerdict('${{storyId}}', 'confirm_remove')">\\u2713 Removal Correct</button>
                    <button class="feedback-btn reject-remove ${{fb.verdict === 'reject_remove' ? 'active' : ''}}"
                            onclick="setVerdict('${{storyId}}', 'reject_remove')">\\u2717 Should Have Kept</button>
                `;
            }} else if (isAbsorbed) {{
                feedbackButtons = `
                    <button class="feedback-btn correct ${{fb.verdict === 'correct' ? 'active' : ''}}"
                            onclick="setVerdict('${{storyId}}', 'correct')">\\u2713 Merge Correct</button>
                    <button class="feedback-btn incorrect ${{fb.verdict === 'incorrect' ? 'active' : ''}}"
                            onclick="setVerdict('${{storyId}}', 'incorrect')">\\u2717 Should Be Separate</button>
                `;
            }} else {{
                feedbackButtons = `
                    <button class="feedback-btn correct ${{fb.verdict === 'correct' ? 'active' : ''}}"
                            onclick="setVerdict('${{storyId}}', 'correct')">\\u2713 Correct</button>
                    <button class="feedback-btn incorrect ${{fb.verdict === 'incorrect' ? 'active' : ''}}"
                            onclick="setVerdict('${{storyId}}', 'incorrect')">\\u2717 Incorrect</button>
                `;
            }}

            let html = `
                <div class="story-card ${{cardClass}}">
                    <div class="story-header">
                        <div class="story-ref">${{story.page_ref}} (Segments ${{story.start_segment}}-${{story.end_segment}})</div>
                        <div class="story-meta">${{metaBadges}}</div>
                    </div>
                    <div class="story-content">
                        ${{renderChangeDescription(entry)}}

                        <div class="text-container">
                            <div class="text-section">
                                <h3>English Translation</h3>
                                <div class="text-content">${{texts.english || '<em>No text available</em>'}}</div>
                            </div>
                            <div class="text-section">
                                <h3>Hebrew/Aramaic Original</h3>
                                <div class="text-content hebrew">${{texts.hebrew || '<em>No text available</em>'}}</div>
                            </div>
                        </div>

                        ${{story.one_sentence_summary ? '<div class="summary">' + story.one_sentence_summary + '</div>' : ''}}

                        <div class="criteria-breakdown">
                            <h3>Criteria Assessment (${{story.criteria_met_count}}/6)</h3>
                            ${{Object.entries(criteria).map(([name, data]) =>
                                '<div class="criterion">' +
                                    '<span class="criterion-icon ' + (data.met ? 'criterion-met' : 'criterion-unmet') + '">' + (data.met ? '\\u2713' : '\\u2717') + '</span>' +
                                    '<span class="criterion-name">' + name.replace(/_/g, ' ') + '</span>' +
                                    (data.reasoning ? '<span class="criterion-detail"> - ' + data.reasoning + '</span>' : '') +
                                '</div>'
                            ).join('')}}
                        </div>

                        ${{disqs.length > 0 ? '<div class="flags-section disqualifiers"><h4>Disqualifiers (' + disqs.length + ')</h4>' + disqs.map(d => '<span class="flag-item">' + d.replace(/_/g, ' ') + '</span>').join('') + '</div>' : ''}}
                        ${{weaks.length > 0 ? '<div class="flags-section"><h4>Weakeners (' + weaks.length + ')</h4>' + weaks.map(w => '<span class="flag-item">' + w.replace(/_/g, ' ') + '</span>').join('') + '</div>' : ''}}

                        <div class="reasoning">
                            <strong>Classification Reasoning:</strong> ${{story.classification_reasoning || 'No reasoning provided'}}
                        </div>
                    </div>

                    <div class="feedback-section">
                        <div class="feedback-row">
                            ${{feedbackButtons}}
                            <div class="feedback-note">
                                <input type="text" placeholder="Notes..." value="${{fb.note || ''}}"
                                       onchange="setNote('${{storyId}}', this.value)">
                            </div>
                        </div>
                    </div>
                </div>
            `;
            return html;
        }}

        function renderAll() {{
            const tierFilter = document.getElementById('filterTier').value;
            const changeFilter = document.getElementById('filterChange').value;
            const pageSearch = document.getElementById('searchPage').value.toLowerCase();

            const container = document.getElementById('storiesContainer');
            let html = '';
            let totalShown = 0;

            ['tier1', 'tier2', 'tier3'].forEach(tier => {{
                if (tierFilter !== 'all' && tierFilter !== tier) return;

                let entries = deltaData[tier] || [];

                // Apply change type filter
                if (changeFilter !== 'all') {{
                    entries = entries.filter(e => e.change_type === changeFilter);
                }}

                // Apply page search
                if (pageSearch) {{
                    entries = entries.filter(e => {{
                        const ref = (e.story && e.story.page_ref) || '';
                        return ref.toLowerCase().includes(pageSearch);
                    }});
                }}

                if (entries.length === 0) return;

                const cfg = TIER_CONFIG[tier];
                html += '<div class="tier-header ' + cfg.cssClass + '">';
                html += '<h2>' + cfg.title + ' (' + entries.length + ')</h2>';
                html += '<p>' + cfg.description + '</p>';
                html += '</div>';

                entries.forEach(entry => {{
                    html += renderStory(entry, tier);
                }});
                totalShown += entries.length;
            }});

            if (totalShown === 0) {{
                html = '<div class="no-results">No stories match your filters</div>';
            }}

            container.innerHTML = html;
            renderStats();
        }}

        function setVerdict(storyId, verdict) {{
            feedback[storyId] = feedback[storyId] || {{}};
            feedback[storyId].verdict = feedback[storyId].verdict === verdict ? null : verdict;
            feedback[storyId].reviewer = document.getElementById('reviewerName').value;
            feedback[storyId].timestamp = new Date().toISOString();
            saveFeedback();
            renderAll();
        }}

        function setNote(storyId, note) {{
            feedback[storyId] = feedback[storyId] || {{}};
            feedback[storyId].note = note;
            feedback[storyId].reviewer = document.getElementById('reviewerName').value;
            saveFeedback();
        }}

        function saveFeedback() {{
            localStorage.setItem('v8_delta_feedback', JSON.stringify(feedback));
        }}

        function exportFeedback() {{
            const reviewer = document.getElementById('reviewerName').value || 'anonymous';
            const data = {{
                reviewer: reviewer,
                version: 'v8_delta',
                exportDate: new Date().toISOString(),
                totalStories: deltaData.counts.total_review,
                reviewed: Object.keys(feedback).length,
                feedback: feedback
            }};

            const blob = new Blob([JSON.stringify(data, null, 2)], {{type: 'application/json'}});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'v8_delta_feedback_' + reviewer + '_' + new Date().toISOString().slice(0,10) + '.json';
            a.click();
        }}

        function clearFeedback() {{
            if (confirm('Clear all feedback? This cannot be undone.')) {{
                feedback = {{}};
                localStorage.removeItem('v8_delta_feedback');
                renderAll();
            }}
        }}

        // Event listeners
        document.getElementById('filterTier').addEventListener('change', renderAll);
        document.getElementById('filterChange').addEventListener('change', renderAll);
        document.getElementById('searchPage').addEventListener('input', renderAll);

        // Initial render
        renderAll();
    </script>
</body>
</html>
'''
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)


def main():
    output_file = PROJECT_ROOT / 'validation' / 'ui' / 'ketubot_61-112_v8_delta.html'

    print("Loading v7 results from git (HEAD~7)...")
    v7_data = load_v7_from_git()

    print("Loading v8 results (current)...")
    v8_data = load_v8()

    print("Loading cached pages for segment text...")
    cached_pages = load_cached_pages()

    print("Flattening stories...")
    v7_stories = flatten_stories(v7_data)
    v8_stories = flatten_stories(v8_data)
    print(f"  v7: {len(v7_stories)} stories")
    print(f"  v8: {len(v8_stories)} stories")

    print("Categorizing delta...")
    tier1, tier2, tier3, skipped = categorize_delta(v7_stories, v8_stories)
    print(f"  Tier 1 (cross-page merges): {len(tier1)}")
    print(f"  Tier 2 (new/status/removed): {len(tier2)}")
    print(f"  Tier 3 (reclassified): {len(tier3)}")
    print(f"  Skipped (unchanged): {len(skipped)}")

    print("Building delta data...")
    delta_data = build_delta_data(tier1, tier2, tier3, skipped, cached_pages)

    print(f"Generating HTML: {output_file}")
    generate_html(delta_data, output_file)

    total = delta_data['counts']['total_review']
    print(f"\nDone! {total} stories for Jeff to review (was {len(v8_stories)}).")
    print(f"Open: {output_file}")


if __name__ == '__main__':
    main()
