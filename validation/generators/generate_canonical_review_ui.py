#!/usr/bin/env python3
"""
Generate the canonical review UI showing ALL 192 stories in 3 sections.

Section 1: Needs Review (~19) — expanded by default, Approve/Adjust/Reject
Section 2: Auto-Applied (~30) — collapsed, full cards with old→new, Correct/Incorrect
Section 3: All Other Stories (~143) — collapsed, full cards, Correct/Incorrect

Usage:
  python3 validation/generators/generate_canonical_review_ui.py
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
CANONICAL_PATH = PROJECT_ROOT / 'results' / 'canonical' / 'ketubot_canonical.json'
OUTPUT_PATH = PROJECT_ROOT / 'validation' / 'ui' / 'ketubot_canonical_review.html'


def load_canonical():
    """Load the canonical file."""
    with open(CANONICAL_PATH) as f:
        return json.load(f)


def build_story_item(page, story, page_lookup):
    """Build a standard story item dict from a page and story."""
    ref = page['ref']
    item = {
        'page_ref': ref,
        'start_segment': story['start_segment'],
        'end_segment': story['end_segment'],
        'classification': story.get('classification', 'UNKNOWN'),
        'one_sentence_summary': story.get('one_sentence_summary', ''),
        'classification_reasoning': story.get('classification_reasoning', ''),
        'criteria': story.get('criteria', {}),
        'criteria_met_count': story.get('criteria_met_count', 0),
        'page_segments': page.get('segments', []),
        'spans_pages': story.get('spans_pages'),
        'start_segment_page2': story.get('start_segment_page2'),
        'end_segment_page2': story.get('end_segment_page2'),
        'key': f"{ref}_{story['start_segment']}-{story['end_segment']}",
    }
    # Add page2 segments for cross-page stories
    if story.get('spans_pages') and len(story['spans_pages']) >= 2:
        p2_ref = story['spans_pages'][1]
        p2 = page_lookup.get(p2_ref)
        if p2:
            item['page2_segments'] = p2.get('segments', [])
    return item


def build_review_data(canonical):
    """Build the data structure for the HTML template — all 3 groups."""
    pages = canonical['pages']
    page_lookup = {p['ref']: p for p in pages}

    # Build a set of auto-applied story keys with their log data
    auto_log = {}
    for record in canonical.get('auto_applied_log', []):
        auto_log[record['key']] = record

    review_items = []
    auto_items = []
    unchanged_items = []

    for page in pages:
        for story in page.get('stories', []):
            key = f"{page['ref']}_{story['start_segment']}-{story['end_segment']}"
            item = build_story_item(page, story, page_lookup)

            if story.get('needs_review'):
                # Section 1: Needs Review
                item['review_reason'] = story.get('review_reason', '')
                item['jeff_note'] = story.get('jeff_note', '')
                item['proposed_change'] = story.get('proposed_change', '')
                review_items.append(item)
            elif key in auto_log:
                # Section 2: Auto-Applied (matched by key from the log)
                log = auto_log[key]
                item['old_classification'] = log.get('old_classification', '')
                item['new_classification'] = log.get('new_classification', '')
                item['action'] = log.get('action', '')
                item['correction_reason'] = log.get('reason', '')
                item['correction_source'] = log.get('source', '')
                auto_items.append(item)
            elif story.get('corrections'):
                # Story has corrections but wasn't in auto_log — still treat as auto
                corr = story['corrections'][0] if story['corrections'] else {}
                item['old_classification'] = ''
                item['new_classification'] = story.get('classification', '')
                item['action'] = corr.get('action', '')
                item['correction_reason'] = corr.get('reason', '')
                item['correction_source'] = corr.get('source', '')
                auto_items.append(item)
            else:
                # Section 3: Unchanged
                unchanged_items.append(item)

    return {
        'review_items': review_items,
        'auto_items': auto_items,
        'unchanged_items': unchanged_items,
        'counts': {
            'review': len(review_items),
            'auto': len(auto_items),
            'unchanged': len(unchanged_items),
            'total_stories': canonical['corrections_summary']['total_stories'],
        },
    }


def generate_html(review_data, output_path):
    """Generate the canonical review HTML with 3 sections."""
    data_json = json.dumps(review_data, ensure_ascii=False, indent=2)
    counts = review_data['counts']

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Canonical Review — Ketubot (All {counts['total_stories']} Stories)</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; padding: 20px; line-height: 1.6; }}
        .container {{ max-width: 1600px; margin: 0 auto; }}

        .header {{ background: white; padding: 30px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 30px; }}
        .header h1 {{ color: #2c3e50; margin-bottom: 10px; }}
        .version-badge {{ display: inline-block; padding: 6px 12px; background: linear-gradient(135deg, #8e44ad 0%, #6c3483 100%); color: white; border-radius: 6px; font-size: 14px; font-weight: 600; margin-left: 15px; }}
        .header p {{ color: #7f8c8d; font-size: 16px; margin-top: 10px; }}

        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 15px; margin-top: 20px; }}
        .stat-box {{ background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }}
        .stat-box .number {{ font-size: 28px; font-weight: bold; }}
        .stat-box .label {{ color: #7f8c8d; font-size: 13px; margin-top: 5px; }}
        .stat-review .number {{ color: #e74c3c; }}
        .stat-auto .number {{ color: #27ae60; }}
        .stat-unchanged .number {{ color: #3498db; }}
        .stat-total .number {{ color: #8e44ad; }}
        .stat-progress .number {{ color: #f39c12; }}

        .controls {{ background: white; padding: 25px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        .filters {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }}
        .control-group label {{ display: block; font-weight: 600; color: #2c3e50; margin-bottom: 8px; }}
        select, input[type="text"] {{ width: 100%; padding: 10px; border: 2px solid #e0e0e0; border-radius: 6px; font-size: 14px; }}

        /* Section headers */
        .section-header {{ background: white; padding: 20px 25px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin: 30px 0 15px 0; cursor: pointer; user-select: none; }}
        .section-header h2 {{ color: #2c3e50; margin-bottom: 8px; font-size: 22px; }}
        .section-header p {{ color: #7f8c8d; font-size: 15px; }}
        .section-header.review {{ border-left: 5px solid #e74c3c; }}
        .section-header.auto {{ border-left: 5px solid #27ae60; }}
        .section-header.unchanged {{ border-left: 5px solid #3498db; }}
        .collapse-icon {{ float: right; font-size: 20px; color: #7f8c8d; }}

        /* Story Cards */
        .story-card {{ background: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 20px; overflow: hidden; }}
        .story-card.type-review_cross_page {{ border-left: 5px solid #e74c3c; }}
        .story-card.type-review_merge {{ border-left: 5px solid #f39c12; }}
        .story-card.type-review_boundary {{ border-left: 5px solid #3498db; }}
        .story-card.type-review_other {{ border-left: 5px solid #95a5a6; }}
        .story-card.type-auto {{ border-left: 5px solid #27ae60; }}
        .story-card.type-unchanged {{ border-left: 5px solid #bdc3c7; }}

        .story-header {{ padding: 20px; background: #f8f9fa; border-bottom: 2px solid #e0e0e0; }}
        .story-ref {{ font-size: 20px; font-weight: bold; color: #2c3e50; margin-bottom: 10px; }}
        .story-meta {{ display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }}

        .badge {{ padding: 6px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; text-transform: uppercase; }}
        .class-YES-badge {{ background: #d4edda; color: #155724; }}
        .class-HIGH_CONFIDENCE-badge {{ background: #cfe2ff; color: #084298; }}
        .class-LOW_CONFIDENCE-badge {{ background: #fff3cd; color: #856404; }}
        .class-NOT_A_STORY-badge {{ background: #f8d7da; color: #721c24; }}
        .class-NEEDS_REVIEW-badge {{ background: #e8daef; color: #6c3483; }}
        .class-UNKNOWN-badge {{ background: #e0e0e0; color: #555; }}
        .reason-badge {{ background: #f0e6ff; color: #6f42c1; font-weight: 700; }}
        .criteria-badge {{ background: #e7f3ff; color: #0066cc; }}
        .spans-badge {{ background: #e74c3c; color: white; }}
        .change-badge {{ background: #e8f5e9; color: #2e7d32; font-weight: 700; }}

        /* Jeff's note */
        .jeff-note {{ background: #fff3e0; padding: 15px; border-left: 4px solid #ff9800; margin-bottom: 20px; }}
        .jeff-note strong {{ color: #e65100; }}

        /* Proposed change */
        .proposed-change {{ background: #e8f5e9; padding: 15px; border-left: 4px solid #4caf50; margin-bottom: 20px; }}
        .proposed-change strong {{ color: #2e7d32; }}

        /* Correction info */
        .correction-info {{ background: #e8f5e9; padding: 15px; border-left: 4px solid #27ae60; margin-bottom: 20px; }}
        .correction-info strong {{ color: #1b5e20; }}

        .story-content {{ padding: 20px; }}
        .summary {{ background: #f0f7ff; padding: 15px; border-left: 4px solid #3498db; margin-bottom: 20px; font-style: italic; }}

        .text-container {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }}
        @media (max-width: 1024px) {{ .text-container {{ grid-template-columns: 1fr; }} }}
        .text-section h3 {{ color: #2c3e50; margin-bottom: 10px; font-size: 16px; }}
        .text-content {{ padding: 15px; background: #f8f9fa; border-radius: 8px; line-height: 1.8; font-size: 15px; max-height: 500px; overflow-y: auto; }}
        .text-content div {{ margin: 5px 0; }}
        .hebrew {{ direction: rtl; text-align: right; font-family: 'Times New Roman', serif; font-size: 18px; }}
        .story-text {{ background: #fff3cd; padding: 8px; border-left: 3px solid #f39c12; margin: 5px 0; }}
        .page-break {{ background: #e8e8e8; padding: 6px 12px; margin: 12px 0; font-size: 12px; font-weight: 600; color: #666; text-align: center; border-radius: 4px; }}

        .criteria-breakdown {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .criteria-breakdown h3 {{ color: #2c3e50; margin-bottom: 15px; font-size: 16px; }}
        .criterion {{ display: flex; align-items: center; padding: 8px 0; }}
        .criterion-icon {{ width: 20px; margin-right: 10px; font-size: 16px; }}
        .criterion-met {{ color: #27ae60; }}
        .criterion-unmet {{ color: #e74c3c; }}
        .criterion-name {{ font-weight: 600; color: #2c3e50; flex: 1; }}

        .reasoning {{ margin-bottom: 15px; padding: 15px; background: #f0f7ff; border-left: 4px solid #3498db; font-size: 14px; }}

        /* Feedback section */
        .feedback-section {{ padding: 20px; background: #f8f9fa; border-top: 2px solid #e0e0e0; }}
        .feedback-row {{ display: flex; gap: 15px; align-items: center; flex-wrap: wrap; }}
        .feedback-btn {{ padding: 10px 24px; border: 2px solid; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; background: white; }}
        .feedback-btn.approve {{ border-color: #27ae60; color: #27ae60; }}
        .feedback-btn.approve:hover, .feedback-btn.approve.active {{ background: #27ae60; color: white; }}
        .feedback-btn.adjust {{ border-color: #f39c12; color: #f39c12; }}
        .feedback-btn.adjust:hover, .feedback-btn.adjust.active {{ background: #f39c12; color: white; }}
        .feedback-btn.reject {{ border-color: #e74c3c; color: #e74c3c; }}
        .feedback-btn.reject:hover, .feedback-btn.reject.active {{ background: #e74c3c; color: white; }}
        .feedback-btn.correct {{ border-color: #27ae60; color: #27ae60; }}
        .feedback-btn.correct:hover, .feedback-btn.correct.active {{ background: #27ae60; color: white; }}
        .feedback-btn.incorrect {{ border-color: #e74c3c; color: #e74c3c; }}
        .feedback-btn.incorrect:hover, .feedback-btn.incorrect.active {{ background: #e74c3c; color: white; }}
        .feedback-note {{ flex: 1; min-width: 250px; }}
        .feedback-note input {{ width: 100%; padding: 10px; border: 2px solid #e0e0e0; border-radius: 6px; }}

        .export-section {{ text-align: center; margin-top: 30px; padding: 30px; background: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .export-btn {{ padding: 15px 40px; background: #3498db; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; margin: 5px; }}
        .export-btn:hover {{ background: #2980b9; }}

        .no-results {{ text-align: center; padding: 60px 20px; color: #7f8c8d; font-size: 18px; }}
        .hidden {{ display: none; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Canonical Review <span class="version-badge">All {counts['total_stories']} Stories</span></h1>
            <p>
                {counts['review']} stories need your review.
                {counts['auto']} corrections were auto-applied.
                {counts['unchanged']} stories unchanged.
            </p>
            <div class="stats" id="stats"></div>
        </div>

        <div class="controls">
            <div class="filters">
                <div class="control-group">
                    <label>Review Type</label>
                    <select id="filterType">
                        <option value="all">All Types</option>
                        <option value="review_cross_page">Cross-Page Fix</option>
                        <option value="review_merge">Merge Stories</option>
                        <option value="review_boundary">Boundary Adjustment</option>
                        <option value="review_other">Needs Clarification</option>
                    </select>
                </div>
                <div class="control-group">
                    <label>Classification</label>
                    <select id="filterClassification">
                        <option value="all">All Classifications</option>
                        <option value="YES">YES</option>
                        <option value="HIGH_CONFIDENCE">HIGH_CONFIDENCE</option>
                        <option value="LOW_CONFIDENCE">LOW_CONFIDENCE</option>
                        <option value="NOT_A_STORY">NOT_A_STORY</option>
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

        <div class="section-header review" onclick="toggleSection('reviewSection')">
            <span class="collapse-icon" id="reviewIcon">&#x25BC;</span>
            <h2>Needs Your Review (<span id="reviewCount">{counts['review']}</span> stories)</h2>
            <p>These corrections need your confirmation or adjustment. Each shows your original note and our proposed interpretation.</p>
        </div>
        <div id="reviewSection"></div>

        <div class="section-header auto" onclick="toggleSection('autoSection')">
            <span class="collapse-icon" id="autoIcon">&#x25B6;</span>
            <h2>Auto-Applied Changes (<span id="autoCount">{counts['auto']}</span> stories)</h2>
            <p>Click to expand. Full story cards showing old and new classification. Spot-check if desired.</p>
        </div>
        <div id="autoSection" class="hidden"></div>

        <div class="section-header unchanged" onclick="toggleSection('unchangedSection')">
            <span class="collapse-icon" id="unchangedIcon">&#x25B6;</span>
            <h2>All Other Stories (<span id="unchangedCount">{counts['unchanged']}</span> stories)</h2>
            <p>Click to expand. Stories confirmed correct or not yet reviewed. Flag anything that needs attention.</p>
        </div>
        <div id="unchangedSection" class="hidden"></div>

        <div class="export-section">
            <h2>Export Canonical Review Feedback</h2>
            <p style="margin: 15px 0; color: #7f8c8d;">Feedback auto-saves to browser storage</p>
            <button class="export-btn" onclick="exportFeedback()">Download Feedback JSON</button>
            <button class="export-btn" onclick="clearFeedback()" style="background: #e74c3c;">Clear All</button>
        </div>
    </div>

    <script id="reviewData" type="application/json">
{data_json}
    </script>

    <script>
        const reviewData = JSON.parse(document.getElementById('reviewData').textContent);
        let feedback = JSON.parse(localStorage.getItem('canonical_review_feedback') || '{{}}'  );

        const REASON_LABELS = {{
            review_cross_page: 'Cross-Page Fix',
            review_merge: 'Merge Stories',
            review_boundary: 'Boundary Adjustment',
            review_other: 'Needs Clarification',
        }};

        function getStoryText(item) {{
            const start = item.start_segment;
            const end = item.end_segment;
            const segments = item.page_segments || [];

            const contextStart = Math.max(0, start - 1);
            const contextEnd = Math.min(segments.length - 1, end + 1);

            let englishParts = [];
            let hebrewParts = [];

            for (let i = contextStart; i <= contextEnd; i++) {{
                const seg = segments[i];
                if (!seg) continue;
                const isStory = i >= start && i <= end;
                const cls = isStory ? 'story-text' : '';
                if (seg.english) englishParts.push('<div class="' + cls + '"><small style="color:#999">[' + i + ']</small> ' + seg.english + '</div>');
                if (seg.hebrew) hebrewParts.push('<div class="' + cls + '">' + seg.hebrew + ' <small style="color:#999">[' + i + ']</small></div>');
            }}

            // Page 2 segments for cross-page stories
            if (item.spans_pages && item.page2_segments && item.page2_segments.length > 0) {{
                const p2Start = item.start_segment_page2;
                const p2End = item.end_segment_page2;
                if (p2Start != null && p2End != null) {{
                    const p2ContextStart = Math.max(0, p2Start - 1);
                    const p2ContextEnd = Math.min(item.page2_segments.length - 1, p2End + 1);

                    englishParts.push('<div class="page-break">&mdash; ' + item.spans_pages[1] + ' (continued) &mdash;</div>');
                    hebrewParts.push('<div class="page-break">&mdash; ' + item.spans_pages[1] + ' (continued) &mdash;</div>');

                    for (let i = p2ContextStart; i <= p2ContextEnd; i++) {{
                        const seg = item.page2_segments[i];
                        if (!seg) continue;
                        const isStory = i >= p2Start && i <= p2End;
                        const cls = isStory ? 'story-text' : '';
                        if (seg.english) englishParts.push('<div class="' + cls + '"><small style="color:#999">[' + i + ']</small> ' + seg.english + '</div>');
                        if (seg.hebrew) hebrewParts.push('<div class="' + cls + '">' + seg.hebrew + ' <small style="color:#999">[' + i + ']</small></div>');
                    }}
                }}
            }}

            return {{ english: englishParts.join(''), hebrew: hebrewParts.join('') }};
        }}

        function renderStats() {{
            const reviewed = Object.keys(feedback).length;
            document.getElementById('stats').innerHTML = `
                <div class="stat-box stat-review"><div class="number">${{reviewData.counts.review}}</div><div class="label">Needs Review</div></div>
                <div class="stat-box stat-auto"><div class="number">${{reviewData.counts.auto}}</div><div class="label">Auto-Applied</div></div>
                <div class="stat-box stat-unchanged"><div class="number">${{reviewData.counts.unchanged}}</div><div class="label">Unchanged</div></div>
                <div class="stat-box stat-total"><div class="number">${{reviewData.counts.total_stories}}</div><div class="label">Total Stories</div></div>
                <div class="stat-box stat-progress"><div class="number">${{reviewed}}</div><div class="label">Reviewed</div></div>
            `;
        }}

        // --- Shared card parts ---

        function renderCardHeader(item, extraBadges) {{
            let metaBadges = '<span class="badge class-' + item.classification + '-badge">' + item.classification.replace(/_/g, ' ') + '</span>';
            if (extraBadges) metaBadges += extraBadges;
            if (item.criteria_met_count) {{
                metaBadges += '<span class="badge criteria-badge">' + item.criteria_met_count + '/6 Criteria</span>';
            }}
            if (item.spans_pages) {{
                metaBadges += '<span class="badge spans-badge">Spans ' + item.spans_pages.join(' + ') + '</span>';
            }}
            return `
                <div class="story-header">
                    <div class="story-ref">${{item.page_ref}} (Segments ${{item.start_segment}}-${{item.end_segment}})</div>
                    <div class="story-meta">${{metaBadges}}</div>
                </div>`;
        }}

        function renderCardBody(item) {{
            const texts = getStoryText(item);
            const criteria = item.criteria || {{}};
            let html = '<div class="story-content">';

            // Text display
            html += `
                <div class="text-container">
                    <div class="text-section">
                        <h3>English Translation</h3>
                        <div class="text-content">${{texts.english || '<em>No text available</em>'}}</div>
                    </div>
                    <div class="text-section">
                        <h3>Hebrew/Aramaic Original</h3>
                        <div class="text-content hebrew">${{texts.hebrew || '<em>No text available</em>'}}</div>
                    </div>
                </div>`;

            // Summary
            if (item.one_sentence_summary && !item.one_sentence_summary.startsWith('[')) {{
                html += '<div class="summary">' + item.one_sentence_summary + '</div>';
            }}

            // Criteria
            if (Object.keys(criteria).length > 0) {{
                html += '<div class="criteria-breakdown"><h3>Criteria Assessment (' + (item.criteria_met_count || 0) + '/6)</h3>';
                for (const [name, data] of Object.entries(criteria)) {{
                    html += '<div class="criterion">';
                    html += '<span class="criterion-icon ' + (data.met ? 'criterion-met' : 'criterion-unmet') + '">' + (data.met ? '\\u2713' : '\\u2717') + '</span>';
                    html += '<span class="criterion-name">' + name.replace(/_/g, ' ') + '</span>';
                    html += '</div>';
                }}
                html += '</div>';
            }}

            // Reasoning
            if (item.classification_reasoning) {{
                html += '<div class="reasoning"><strong>Classification Reasoning:</strong> ' + item.classification_reasoning + '</div>';
            }}

            html += '</div>';
            return html;
        }}

        // --- Section 1: Needs Review ---

        function renderReviewItem(item) {{
            const storyId = item.key;
            const fb = feedback[storyId] || {{}};
            const reason = item.review_reason || 'review_other';
            const reasonLabel = REASON_LABELS[reason] || reason;
            const extraBadges = '<span class="badge reason-badge">' + reasonLabel + '</span>';

            let html = '<div class="story-card type-' + reason + '">';
            html += renderCardHeader(item, extraBadges);

            // Jeff's note and proposed change before the body
            html += '<div class="story-content">';
            if (item.jeff_note) {{
                html += '<div class="jeff-note"><strong>Your previous note:</strong> ' + item.jeff_note + '</div>';
            }}
            if (item.proposed_change) {{
                html += '<div class="proposed-change"><strong>Our interpretation:</strong> ' + item.proposed_change + '</div>';
            }}
            html += '</div>';

            html += renderCardBody(item);

            // Feedback: Approve / Adjust / Reject
            html += `
                <div class="feedback-section">
                    <div class="feedback-row">
                        <button class="feedback-btn approve ${{fb.verdict === 'approve' ? 'active' : ''}}"
                                onclick="setVerdict('${{storyId}}', 'approve')">\\u2713 Approve Change</button>
                        <button class="feedback-btn adjust ${{fb.verdict === 'adjust' ? 'active' : ''}}"
                                onclick="setVerdict('${{storyId}}', 'adjust')">\\u270E Adjust</button>
                        <button class="feedback-btn reject ${{fb.verdict === 'reject' ? 'active' : ''}}"
                                onclick="setVerdict('${{storyId}}', 'reject')">\\u2717 Reject</button>
                        <div class="feedback-note">
                            <input type="text" placeholder="Correction details or segment numbers..."
                                   value="${{(fb.note || '').replace(/"/g, '&quot;')}}"
                                   onchange="setNote('${{storyId}}', this.value)">
                        </div>
                    </div>
                </div>`;

            html += '</div>';
            return html;
        }}

        // --- Section 2: Auto-Applied ---

        function renderAutoItem(item) {{
            const storyId = item.key;
            const fb = feedback[storyId] || {{}};
            const action = item.action || '';

            let changeText = '';
            if (action === 'auto_remove') {{
                changeText = 'REMOVED';
            }} else if (action === 'auto_keep') {{
                changeText = 'KEPT (no change)';
            }} else if (item.old_classification && item.new_classification) {{
                changeText = item.old_classification + ' \\u2192 ' + item.new_classification;
            }} else {{
                changeText = item.classification;
            }}

            const extraBadges = '<span class="badge change-badge">' + changeText + '</span>';

            let html = '<div class="story-card type-auto">';
            html += renderCardHeader(item, extraBadges);

            // Correction info
            if (item.correction_reason) {{
                html += '<div class="story-content"><div class="correction-info"><strong>Reason for change:</strong> ' + item.correction_reason + '</div></div>';
            }}

            html += renderCardBody(item);

            // Feedback: Correct / Incorrect
            html += `
                <div class="feedback-section">
                    <div class="feedback-row">
                        <button class="feedback-btn correct ${{fb.verdict === 'correct' ? 'active' : ''}}"
                                onclick="setVerdict('${{storyId}}', 'correct')">\\u2713 Correct</button>
                        <button class="feedback-btn incorrect ${{fb.verdict === 'incorrect' ? 'active' : ''}}"
                                onclick="setVerdict('${{storyId}}', 'incorrect')">\\u2717 Incorrect</button>
                        <div class="feedback-note">
                            <input type="text" placeholder="Notes..."
                                   value="${{(fb.note || '').replace(/"/g, '&quot;')}}"
                                   onchange="setNote('${{storyId}}', this.value)">
                        </div>
                    </div>
                </div>`;

            html += '</div>';
            return html;
        }}

        // --- Section 3: Unchanged ---

        function renderUnchangedItem(item) {{
            const storyId = item.key;
            const fb = feedback[storyId] || {{}};

            let html = '<div class="story-card type-unchanged">';
            html += renderCardHeader(item, '');
            html += renderCardBody(item);

            // Feedback: Correct / Incorrect
            html += `
                <div class="feedback-section">
                    <div class="feedback-row">
                        <button class="feedback-btn correct ${{fb.verdict === 'correct' ? 'active' : ''}}"
                                onclick="setVerdict('${{storyId}}', 'correct')">\\u2713 Correct</button>
                        <button class="feedback-btn incorrect ${{fb.verdict === 'incorrect' ? 'active' : ''}}"
                                onclick="setVerdict('${{storyId}}', 'incorrect')">\\u2717 Incorrect</button>
                        <div class="feedback-note">
                            <input type="text" placeholder="Notes..."
                                   value="${{(fb.note || '').replace(/"/g, '&quot;')}}"
                                   onchange="setNote('${{storyId}}', this.value)">
                        </div>
                    </div>
                </div>`;

            html += '</div>';
            return html;
        }}

        // --- Filtering ---

        function applyFilters(items) {{
            const typeFilter = document.getElementById('filterType').value;
            const classFilter = document.getElementById('filterClassification').value;
            const pageSearch = document.getElementById('searchPage').value.toLowerCase();

            let filtered = items;
            if (typeFilter !== 'all') {{
                filtered = filtered.filter(item => item.review_reason === typeFilter);
            }}
            if (classFilter !== 'all') {{
                filtered = filtered.filter(item => item.classification === classFilter);
            }}
            if (pageSearch) {{
                filtered = filtered.filter(item => item.page_ref.toLowerCase().includes(pageSearch));
            }}
            return filtered;
        }}

        // --- Render all sections ---

        function renderAll() {{
            // Section 1: Needs Review
            const reviewItems = applyFilters(reviewData.review_items);
            const reviewContainer = document.getElementById('reviewSection');
            document.getElementById('reviewCount').textContent = reviewItems.length;
            if (reviewItems.length === 0) {{
                reviewContainer.innerHTML = '<div class="no-results">No stories match your filters</div>';
            }} else {{
                reviewContainer.innerHTML = reviewItems.map(renderReviewItem).join('');
            }}

            // Section 2: Auto-Applied
            const autoItems = applyFilters(reviewData.auto_items);
            const autoContainer = document.getElementById('autoSection');
            document.getElementById('autoCount').textContent = autoItems.length;
            if (autoItems.length === 0) {{
                autoContainer.innerHTML = '<div class="no-results">No stories match your filters</div>';
            }} else {{
                autoContainer.innerHTML = autoItems.map(renderAutoItem).join('');
            }}

            // Section 3: Unchanged
            const unchangedItems = applyFilters(reviewData.unchanged_items);
            const unchangedContainer = document.getElementById('unchangedSection');
            document.getElementById('unchangedCount').textContent = unchangedItems.length;
            if (unchangedItems.length === 0) {{
                unchangedContainer.innerHTML = '<div class="no-results">No stories match your filters</div>';
            }} else {{
                unchangedContainer.innerHTML = unchangedItems.map(renderUnchangedItem).join('');
            }}

            renderStats();
        }}

        function toggleSection(sectionId) {{
            const section = document.getElementById(sectionId);
            const iconMap = {{
                reviewSection: 'reviewIcon',
                autoSection: 'autoIcon',
                unchangedSection: 'unchangedIcon',
            }};
            const icon = document.getElementById(iconMap[sectionId]);
            if (section.classList.contains('hidden')) {{
                section.classList.remove('hidden');
                icon.innerHTML = '&#x25BC;';
            }} else {{
                section.classList.add('hidden');
                icon.innerHTML = '&#x25B6;';
            }}
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
            localStorage.setItem('canonical_review_feedback', JSON.stringify(feedback));
        }}

        function exportFeedback() {{
            const reviewer = document.getElementById('reviewerName').value || 'anonymous';
            const data = {{
                reviewer: reviewer,
                version: 'canonical_review_full',
                exportDate: new Date().toISOString(),
                totalStories: reviewData.counts.total_stories,
                reviewed: Object.keys(feedback).length,
                feedback: feedback
            }};

            const blob = new Blob([JSON.stringify(data, null, 2)], {{type: 'application/json'}});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'canonical_review_' + reviewer + '_' + new Date().toISOString().slice(0,10) + '.json';
            a.click();
        }}

        function clearFeedback() {{
            if (confirm('Clear all feedback? This cannot be undone.')) {{
                feedback = {{}};
                localStorage.removeItem('canonical_review_feedback');
                renderAll();
            }}
        }}

        // Event listeners
        document.getElementById('filterType').addEventListener('change', renderAll);
        document.getElementById('filterClassification').addEventListener('change', renderAll);
        document.getElementById('searchPage').addEventListener('input', renderAll);

        // Initial render
        renderAll();
    </script>
</body>
</html>
'''
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)


def main():
    print("Loading canonical file...")
    canonical = load_canonical()

    print("Building review data...")
    review_data = build_review_data(canonical)
    print(f"  Needs review: {review_data['counts']['review']}")
    print(f"  Auto-applied: {review_data['counts']['auto']}")
    print(f"  Unchanged:    {review_data['counts']['unchanged']}")
    print(f"  Total:        {review_data['counts']['total_stories']}")

    print(f"Generating HTML: {OUTPUT_PATH}")
    generate_html(review_data, OUTPUT_PATH)

    print(f"\nDone! Open: {OUTPUT_PATH}")


if __name__ == '__main__':
    main()
