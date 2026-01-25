#!/usr/bin/env python3
"""
Generate jeff_review_v5_1.html with embedded v5.1 JSON data.
Shows Jeff's previous validations alongside new v5.1 results for comparison.
Features:
- v5.1 categorical classifications
- Highlights Jeff's previously validated pages
- Shows improvements from v4.1 to v5.1
- Special attention to pages Jeff marked as FALSE positives in v4.1
"""

import json
import os
import sys

def load_v5_1_results(filepath='results/v5/ketubot_v5.1_full_validation_2-39.json'):
    """Load v5.1 results"""
    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found.")
        sys.exit(1)
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_jeff_validation(filepath='validation_results.json'):
    """Load Jeff's previous validation data"""
    if not os.path.exists(filepath):
        print(f"Warning: {filepath} not found. Proceeding without Jeff's validation data.")
        return {'details': []}
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_html(v5_1_data, jeff_data, output_file):
    """Generate HTML with both datasets"""

    v5_1_json = json.dumps(v5_1_data, ensure_ascii=False, indent=2)
    jeff_json = json.dumps(jeff_data, ensure_ascii=False, indent=2)

    html_template = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jeff's v5.1 Validation Review</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; padding: 20px; line-height: 1.6; }}
        .container {{ max-width: 1600px; margin: 0 auto; }}

        /* Header */
        .header {{ background: white; padding: 30px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 30px; }}
        .header h1 {{ color: #2c3e50; margin-bottom: 10px; }}
        .version-badge {{ display: inline-block; padding: 6px 12px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 6px; font-size: 14px; font-weight: 600; margin-left: 15px; }}
        .expert-info {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin: 20px 0; }}
        .expert-info h2 {{ margin-bottom: 5px; }}
        .expert-info p {{ color: rgba(255,255,255,0.9); font-size: 14px; }}

        /* Stats */
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-top: 20px; }}
        .stat-box {{ background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }}
        .stat-box .number {{ font-size: 28px; font-weight: bold; }}
        .stat-box .label {{ color: #7f8c8d; font-size: 13px; margin-top: 5px; }}
        .stat-yes .number {{ color: #27ae60; }}
        .stat-high .number {{ color: #3498db; }}
        .stat-low .number {{ color: #f39c12; }}
        .stat-validated .number {{ color: #764ba2; }}

        /* Controls */
        .controls {{ background: white; padding: 25px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        .filters {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; }}
        .control-group label {{ display: block; font-weight: 600; color: #2c3e50; margin-bottom: 8px; }}
        select, input[type="text"] {{ width: 100%; padding: 10px; border: 2px solid #e0e0e0; border-radius: 6px; font-size: 14px; }}

        /* Story Cards */
        .story-card {{ background: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 20px; overflow: hidden; }}
        .story-card.jeff-validated {{ border-left: 5px solid #764ba2; background: linear-gradient(to right, #e7d6f5 0%, white 10%); }}
        .story-card.jeff-false-positive {{ border-left: 5px solid #e74c3c; background: linear-gradient(to right, #f8d7da 0%, white 10%); }}
        .story-card.class-YES {{ border-left: 5px solid #27ae60; }}
        .story-card.class-HIGH_CONFIDENCE {{ border-left: 5px solid #3498db; }}
        .story-card.class-LOW_CONFIDENCE {{ border-left: 5px solid #f39c12; }}

        .story-header {{ padding: 20px; background: #f8f9fa; border-bottom: 2px solid #e0e0e0; }}
        .story-ref {{ font-size: 20px; font-weight: bold; color: #2c3e50; margin-bottom: 10px; }}
        .story-meta {{ display: flex; gap: 10px; flex-wrap: wrap; }}

        .badge {{ padding: 6px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; text-transform: uppercase; }}
        .badge.jeff-true {{ background: #764ba2; color: white; }}
        .badge.jeff-false {{ background: #e74c3c; color: white; }}
        .class-YES-badge {{ background: #d4edda; color: #155724; }}
        .class-HIGH_CONFIDENCE-badge {{ background: #cfe2ff; color: #084298; }}
        .class-LOW_CONFIDENCE-badge {{ background: #fff3cd; color: #856404; }}
        .criteria-badge {{ background: #e7f3ff; color: #0066cc; }}

        /* Content sections */
        .story-content {{ padding: 20px; }}
        .summary {{ background: #f0f7ff; padding: 15px; border-left: 4px solid #3498db; margin-bottom: 20px; font-style: italic; }}

        /* Jeff's feedback */
        .jeff-feedback {{ background: linear-gradient(135deg, #e7d6f5 0%, #d9c3ed 100%); border: 2px solid #764ba2; border-radius: 10px; padding: 20px; margin-bottom: 20px; }}
        .jeff-feedback h4 {{ color: #6f42c1; margin-bottom: 15px; }}
        .jeff-verdict {{ font-size: 18px; font-weight: bold; padding: 10px 15px; border-radius: 8px; display: inline-block; margin-bottom: 15px; }}
        .verdict-true {{ background: #27ae60; color: white; }}
        .verdict-false {{ background: #e74c3c; color: white; }}
        .jeff-notes {{ background: white; padding: 15px; border-radius: 8px; margin-top: 10px; }}

        /* v5.1 comparison */
        .comparison-section {{ background: #fff9e6; padding: 15px; border-left: 4px solid #f39c12; margin-bottom: 20px; }}
        .comparison-section h4 {{ color: #856404; margin-bottom: 10px; }}
        .comparison-item {{ margin: 5px 0; }}

        /* Criteria breakdown */
        .criteria-breakdown {{ background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
        .criteria-breakdown h3 {{ color: #2c3e50; margin-bottom: 10px; font-size: 16px; }}
        .criterion {{ display: flex; align-items: center; padding: 6px 0; font-size: 14px; }}
        .criterion-icon {{ width: 20px; margin-right: 8px; }}
        .criterion-met {{ color: #27ae60; }}
        .criterion-unmet {{ color: #e74c3c; }}

        /* Disqualifiers/Weakeners */
        .flags-section {{ background: #fff9e6; padding: 15px; border-left: 4px solid #f39c12; margin-bottom: 15px; }}
        .flags-section.disqualifiers {{ background: #f8d7da; border-left-color: #e74c3c; }}
        .flags-section h4 {{ color: #2c3e50; margin-bottom: 8px; font-size: 14px; }}
        .flag-item {{ display: inline-block; padding: 4px 10px; background: white; border-radius: 4px; margin: 3px; font-size: 12px; }}

        .reasoning {{ padding: 15px; background: #f0f7ff; border-left: 4px solid #3498db; font-size: 14px; margin-bottom: 15px; }}

        /* Text Display */
        .text-container {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }}
        .text-section {{ background: white; border-radius: 8px; overflow: hidden; }}
        .text-section h3 {{ background: #2c3e50; color: white; padding: 12px 15px; margin: 0; font-size: 14px; }}
        .text-content {{ padding: 15px; background: #f8f9fa; border-radius: 8px; line-height: 1.8; font-size: 15px; max-height: 400px; overflow-y: auto; }}
        .text-content div {{ margin: 5px 0; }}
        .hebrew {{ direction: rtl; text-align: right; font-family: 'Times New Roman', serif; font-size: 18px; }}
        .story-text {{ background: #fff3cd; padding: 8px; border-left: 3px solid #f39c12; margin: 5px 0; }}

        /* Feedback */
        .feedback-section {{ padding: 20px; background: #f8f9fa; border-top: 2px solid #e0e0e0; }}
        .feedback-row {{ display: flex; gap: 15px; align-items: center; flex-wrap: wrap; }}
        .feedback-btn {{ padding: 10px 24px; border: 2px solid; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; background: white; }}
        .feedback-btn.correct {{ border-color: #27ae60; color: #27ae60; }}
        .feedback-btn.correct:hover, .feedback-btn.correct.active {{ background: #27ae60; color: white; }}
        .feedback-btn.incorrect {{ border-color: #e74c3c; color: #e74c3c; }}
        .feedback-btn.incorrect:hover, .feedback-btn.incorrect.active {{ background: #e74c3c; color: white; }}
        .feedback-note {{ flex: 1; min-width: 250px; }}
        .feedback-note input {{ width: 100%; padding: 10px; border: 2px solid #e0e0e0; border-radius: 6px; }}

        .export-section {{ text-align: center; margin-top: 30px; padding: 30px; background: white; border-radius: 12px; }}
        .export-btn {{ padding: 15px 40px; background: #3498db; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; margin: 5px; }}
        .export-btn:hover {{ background: #2980b9; }}

        .no-results {{ text-align: center; padding: 60px 20px; color: #7f8c8d; font-size: 18px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Expert Validation Review <span class="version-badge">v5.1</span></h1>
            <p>Comparing v5.1 results with Jeff Rubenstein's previous validation</p>

            <div class="expert-info">
                <h2>Reviewer: Jeffrey Rubenstein</h2>
                <p>Talmud Scholar - v4.1 validation data loaded for comparison</p>
            </div>

            <div class="stats" id="stats"></div>
        </div>

        <div class="controls">
            <div class="filters">
                <div class="control-group">
                    <label>Classification Filter</label>
                    <select id="filterClass">
                        <option value="all">All Stories</option>
                        <option value="YES">YES Only</option>
                        <option value="HIGH_CONFIDENCE">HIGH Only</option>
                        <option value="LOW_CONFIDENCE">LOW Only</option>
                    </select>
                </div>
                <div class="control-group">
                    <label>Jeff's Validation Status</label>
                    <select id="filterJeff">
                        <option value="all">All Stories</option>
                        <option value="validated_true">Jeff: TRUE stories</option>
                        <option value="validated_false">Jeff: FALSE positives</option>
                        <option value="new">New (not validated by Jeff)</option>
                    </select>
                </div>
                <div class="control-group">
                    <label>Page Reference</label>
                    <input type="text" id="searchPage" placeholder="e.g., 8b, 27b">
                </div>
                <div class="control-group">
                    <label>Reviewer Name</label>
                    <input type="text" id="reviewerName" placeholder="Jeff" value="Jeff">
                </div>
            </div>
        </div>

        <div id="storiesContainer"><div class="no-results">Loading stories...</div></div>

        <div class="export-section">
            <h2>Export Your v5.1 Validation</h2>
            <p style="margin: 15px 0; color: #7f8c8d;">Download your expert review comparing v5.1 with v4.1</p>
            <button class="export-btn" onclick="exportFeedback()">Download Feedback JSON</button>
            <button class="export-btn" onclick="clearFeedback()" style="background: #e74c3c;">Clear All</button>
        </div>
    </div>

    <script id="v5_1Data" type="application/json">
{v5_1_json}
    </script>

    <script id="jeffData" type="application/json">
{jeff_json}
    </script>

    <script>
        const v5_1 = JSON.parse(document.getElementById('v5_1Data').textContent);
        const jeffValidation = JSON.parse(document.getElementById('jeffData').textContent);
        let allStories = [];
        let feedback = JSON.parse(localStorage.getItem('jeff_v5_1_feedback') || '{{}}');

        // Build Jeff's validation lookup
        const jeffLookup = {{}};
        jeffValidation.details.forEach(item => {{
            jeffLookup[item.ref] = item;
        }});

        // Flatten v5.1 stories
        v5_1.pages.forEach(page => {{
            page.stories.forEach(story => {{
                if (story.classification !== 'NOT_A_STORY') {{
                    allStories.push({{
                        ...story,
                        page_ref: page.ref,
                        page_segments: page.segments,
                        storyId: `${{page.ref}}_${{story.start_segment}}-${{story.end_segment}}`,
                        jeffData: jeffLookup[page.ref] || null
                    }});
                }}
            }});
        }});

        function getStoryText(story) {{
            // Extract text segments for this story (with 1 segment before/after for context)
            const start = story.start_segment;
            const end = story.end_segment;
            const segments = story.page_segments || [];

            // Show 1 segment before and 1 segment after for context
            const contextStart = Math.max(0, start - 1);
            const contextEnd = Math.min(segments.length - 1, end + 1);

            let englishParts = [];
            let hebrewParts = [];

            for (let i = contextStart; i <= contextEnd; i++) {{
                const seg = segments[i];
                const isStorySegment = i >= start && i <= end;
                const className = isStorySegment ? 'story-text' : '';

                if (seg.english) {{
                    englishParts.push(`<div class="${{className}}">${{seg.english}}</div>`);
                }}
                if (seg.hebrew) {{
                    hebrewParts.push(`<div class="${{className}}">${{seg.hebrew}}</div>`);
                }}
            }}

            return {{
                english: englishParts.join(''),
                hebrew: hebrewParts.join('')
            }};
        }}

        function renderStats() {{
            const yes = allStories.filter(s => s.classification === 'YES').length;
            const high = allStories.filter(s => s.classification === 'HIGH_CONFIDENCE').length;
            const low = allStories.filter(s => s.classification === 'LOW_CONFIDENCE').length;
            const jeffTrue = allStories.filter(s => s.jeffData && s.jeffData.expected === true).length;
            const reviewed = Object.keys(feedback).length;

            document.getElementById('stats').innerHTML = `
                <div class="stat-box stat-yes"><div class="number">${{yes}}</div><div class="label">YES</div></div>
                <div class="stat-box stat-high"><div class="number">${{high}}</div><div class="label">HIGH</div></div>
                <div class="stat-box stat-low"><div class="number">${{low}}</div><div class="label">LOW</div></div>
                <div class="stat-box stat-validated"><div class="number">${{jeffTrue}}</div><div class="label">Jeff Validated (TRUE)</div></div>
                <div class="stat-box"><div class="number">${{reviewed}}</div><div class="label">Your Reviews</div></div>
            `;
        }}

        function renderStory(story) {{
            const fb = feedback[story.storyId] || {{}};
            const jeff = story.jeffData;
            const criteria = story.criteria || {{}};
            const disqs = story.disqualifiers_found || [];
            const weaks = story.weakeners_found || [];
            const texts = getStoryText(story);

            let cardClass = `story-card class-${{story.classification}}`;
            if (jeff && jeff.expected === true) cardClass += ' jeff-validated';
            if (jeff && jeff.expected === false) cardClass += ' jeff-false-positive';

            let html = `
                <div class="${{cardClass}}">
                    <div class="story-header">
                        <div class="story-ref">${{story.page_ref}} (Segs ${{story.start_segment}}-${{story.end_segment}})</div>
                        <div class="story-meta">
                            <span class="badge class-${{story.classification}}-badge">${{story.classification.replace('_', ' ')}}</span>
                            <span class="badge criteria-badge">${{story.criteria_met_count}}/6</span>
                            ${{jeff && jeff.expected === true ? '<span class="badge jeff-true">Jeff: TRUE ✓</span>' : ''}}
                            ${{jeff && jeff.expected === false ? '<span class="badge jeff-false">Jeff: FALSE ✗</span>' : ''}}
                        </div>
                    </div>
                    <div class="story-content">
                        <div class="text-container">
                            <div class="text-section">
                                <h3>English Translation</h3>
                                <div class="text-content">${{texts.english}}</div>
                            </div>
                            <div class="text-section">
                                <h3>Hebrew/Aramaic Original</h3>
                                <div class="text-content hebrew">${{texts.hebrew}}</div>
                            </div>
                        </div>

                        ${{story.one_sentence_summary ? `<div class="summary">${{story.one_sentence_summary}}</div>` : ''}}

                        ${{jeff ? `
                            <div class="jeff-feedback">
                                <h4>Jeff's Previous v4.1 Validation</h4>
                                <div class="jeff-verdict ${{jeff.expected ? 'verdict-true' : 'verdict-false'}}">
                                    ${{jeff.expected ? 'TRUE STORY ✓' : 'FALSE POSITIVE ✗'}}
                                </div>
                                ${{jeff.validation_notes ? `<div class="jeff-notes"><strong>Jeff's Notes:</strong><br>${{jeff.validation_notes}}</div>` : ''}}
                                ${{jeff.reasoning ? `<div class="jeff-notes"><strong>Jeff's Reasoning:</strong><br>${{jeff.reasoning}}</div>` : ''}}
                            </div>
                        ` : ''}}

                        <div class="criteria-breakdown">
                            <h3>v5.1 Criteria Assessment (${{story.criteria_met_count}}/6)</h3>
                            ${{Object.entries(criteria).map(([name, data]) => `
                                <div class="criterion">
                                    <span class="criterion-icon ${{data.met ? 'criterion-met' : 'criterion-unmet'}}">${{data.met ? '✓' : '✗'}}</span>
                                    <span>${{name.replace('_', ' ')}}${{data.reasoning ? ` - ${{data.reasoning}}` : ''}}</span>
                                </div>
                            `).join('')}}
                        </div>

                        ${{disqs.length > 0 ? `
                            <div class="flags-section disqualifiers">
                                <h4>🚫 Disqualifiers (${{disqs.length}})</h4>
                                ${{disqs.map(d => `<span class="flag-item">${{d.replace('_', ' ')}}</span>`).join('')}}
                            </div>
                        ` : ''}}

                        ${{weaks.length > 0 ? `
                            <div class="flags-section">
                                <h4>⚠️ Weakeners (${{weaks.length}})</h4>
                                ${{weaks.map(w => `<span class="flag-item">${{w.replace('_', ' ')}}</span>`).join('')}}
                            </div>
                        ` : ''}}

                        <div class="reasoning">
                            <strong>v5.1 Reasoning:</strong> ${{story.classification_reasoning || 'No reasoning provided'}}
                        </div>
                    </div>

                    <div class="feedback-section">
                        <div class="feedback-row">
                            <button class="feedback-btn correct ${{fb.verdict === 'correct' ? 'active' : ''}}"
                                    onclick="setVerdict('${{story.storyId}}', 'correct')">✓ Correct</button>
                            <button class="feedback-btn incorrect ${{fb.verdict === 'incorrect' ? 'active' : ''}}"
                                    onclick="setVerdict('${{story.storyId}}', 'incorrect')">✗ Incorrect</button>
                            <div class="feedback-note">
                                <input type="text" placeholder="Notes on v5.1 classification..." value="${{fb.note || ''}}"
                                       onchange="setNote('${{story.storyId}}', this.value)">
                            </div>
                        </div>
                    </div>
                </div>
            `;
            return html;
        }}

        function renderStories() {{
            const classFilter = document.getElementById('filterClass').value;
            const jeffFilter = document.getElementById('filterJeff').value;
            const pageSearch = document.getElementById('searchPage').value.toLowerCase();

            let filtered = allStories.filter(story => {{
                if (classFilter !== 'all' && story.classification !== classFilter) return false;
                if (pageSearch && !story.page_ref.toLowerCase().includes(pageSearch)) return false;

                if (jeffFilter === 'validated_true' && (!story.jeffData || story.jeffData.expected !== true)) return false;
                if (jeffFilter === 'validated_false' && (!story.jeffData || story.jeffData.expected !== false)) return false;
                if (jeffFilter === 'new' && story.jeffData) return false;

                return true;
            }});

            const container = document.getElementById('storiesContainer');
            if (filtered.length === 0) {{
                container.innerHTML = '<div class="no-results">No stories match your filters</div>';
                return;
            }}

            container.innerHTML = filtered.map(renderStory).join('');
        }}

        function setVerdict(storyId, verdict) {{
            feedback[storyId] = feedback[storyId] || {{}};
            feedback[storyId].verdict = feedback[storyId].verdict === verdict ? null : verdict;
            feedback[storyId].reviewer = document.getElementById('reviewerName').value;
            feedback[storyId].timestamp = new Date().toISOString();
            saveFeedback();
            renderStories();
        }}

        function setNote(storyId, note) {{
            feedback[storyId] = feedback[storyId] || {{}};
            feedback[storyId].note = note;
            feedback[storyId].reviewer = document.getElementById('reviewerName').value;
            saveFeedback();
        }}

        function saveFeedback() {{
            localStorage.setItem('jeff_v5_1_feedback', JSON.stringify(feedback));
        }}

        function exportFeedback() {{
            const reviewer = document.getElementById('reviewerName').value || 'Jeff';
            const data = {{
                reviewer: reviewer,
                version: 'v5.1_validation',
                exportDate: new Date().toISOString(),
                totalStories: allStories.length,
                reviewed: Object.keys(feedback).length,
                feedback: feedback,
                notes: 'Comparing v5.1 results with Jeff\\'s v4.1 validation'
            }};

            const blob = new Blob([JSON.stringify(data, null, 2)], {{type: 'application/json'}});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `jeff_v5_1_validation_${{new Date().toISOString().slice(0,10)}}.json`;
            a.click();
        }}

        function clearFeedback() {{
            if (confirm('Clear all feedback? This cannot be undone.')) {{
                feedback = {{}};
                localStorage.removeItem('jeff_v5_1_feedback');
                renderStories();
            }}
        }}

        // Event listeners
        document.getElementById('filterClass').addEventListener('change', renderStories);
        document.getElementById('filterJeff').addEventListener('change', renderStories);
        document.getElementById('searchPage').addEventListener('input', renderStories);

        // Initial render
        renderStats();
        renderStories();
    </script>
</body>
</html>
'''

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_template)

def main():
    v5_1_file = 'results/v5/ketubot_v5.1_full_validation_2-39.json'
    jeff_file = 'validation_results.json'
    output_file = 'jeff_review_v5_1.html'

    if len(sys.argv) > 1:
        v5_1_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]

    print(f"Loading v5.1 results from: {v5_1_file}")
    v5_1_data = load_v5_1_results(v5_1_file)

    print(f"Loading Jeff's validation from: {jeff_file}")
    jeff_data = load_jeff_validation(jeff_file)

    print(f"Generating Jeff's review UI: {output_file}")
    generate_html(v5_1_data, jeff_data, output_file)

    # Stats
    total_stories = sum(
        1 for p in v5_1_data['pages']
        for s in p['stories']
        if s['classification'] != 'NOT_A_STORY'
    )

    print(f"\n✓ Generated {output_file}")
    print(f"  v5.1 Stories (non-NOT_A_STORY): {total_stories}")
    print(f"  Jeff's previous validations: {len(jeff_data['details'])}")
    print(f"  YES: {v5_1_data['summary']['yes']}")
    print(f"  HIGH: {v5_1_data['summary']['high_confidence']}")
    print(f"  LOW: {v5_1_data['summary']['low_confidence']}")

if __name__ == '__main__':
    main()