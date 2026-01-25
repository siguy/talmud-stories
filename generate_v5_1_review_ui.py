#!/usr/bin/env python3
"""
Generate v5.1 review UI with embedded JSON data.
Features v5.1-specific improvements:
- Categorical classification (YES/HIGH/LOW/NOT_A_STORY)
- Disqualifiers and weakeners display
- Criteria breakdown (6 criteria with met/unmet)
- Self-check adjustments tracking
- Enhanced filtering and sorting
"""

import json
import os
import sys

def load_v5_1_results(filepath):
    """Load v5.1 results JSON"""
    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found.")
        sys.exit(1)

    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_html(data, output_file):
    """Generate HTML with embedded v5.1 data"""

    stories_json = json.dumps(data, ensure_ascii=False, indent=2)

    html_template = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>v5.1 Story Review - Categorical Classification</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; padding: 20px; line-height: 1.6; }}
        .container {{ max-width: 1600px; margin: 0 auto; }}

        /* Header */
        .header {{ background: white; padding: 30px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 30px; }}
        .header h1 {{ color: #2c3e50; margin-bottom: 10px; }}
        .version-badge {{ display: inline-block; padding: 6px 12px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 6px; font-size: 14px; font-weight: 600; margin-left: 15px; }}
        .header p {{ color: #7f8c8d; font-size: 16px; margin-top: 10px; }}

        /* Stats */
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-top: 20px; }}
        .stat-box {{ background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }}
        .stat-box .number {{ font-size: 28px; font-weight: bold; }}
        .stat-box .label {{ color: #7f8c8d; font-size: 13px; margin-top: 5px; }}
        .stat-yes .number {{ color: #27ae60; }}
        .stat-high .number {{ color: #3498db; }}
        .stat-low .number {{ color: #f39c12; }}
        .stat-not .number {{ color: #95a5a6; }}

        /* Filters */
        .controls {{ background: white; padding: 25px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        .filters {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; }}
        .control-group {{ margin-bottom: 15px; }}
        .control-group:last-child {{ margin-bottom: 0; }}
        .control-group label {{ display: block; font-weight: 600; color: #2c3e50; margin-bottom: 8px; }}
        select, input[type="text"] {{ width: 100%; padding: 10px; border: 2px solid #e0e0e0; border-radius: 6px; font-size: 14px; }}

        /* Story Cards */
        .story-card {{ background: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 20px; overflow: hidden; }}
        .story-card.class-YES {{ border-left: 5px solid #27ae60; }}
        .story-card.class-HIGH_CONFIDENCE {{ border-left: 5px solid #3498db; }}
        .story-card.class-LOW_CONFIDENCE {{ border-left: 5px solid #f39c12; }}
        .story-card.class-NOT_A_STORY {{ border-left: 5px solid #95a5a6; opacity: 0.7; }}

        .story-header {{ padding: 20px; background: #f8f9fa; border-bottom: 2px solid #e0e0e0; }}
        .story-ref {{ font-size: 20px; font-weight: bold; color: #2c3e50; margin-bottom: 10px; }}
        .story-meta {{ display: flex; gap: 10px; flex-wrap: wrap; }}

        .badge {{ padding: 6px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; text-transform: uppercase; }}
        .class-YES-badge {{ background: #d4edda; color: #155724; }}
        .class-HIGH_CONFIDENCE-badge {{ background: #cfe2ff; color: #084298; }}
        .class-LOW_CONFIDENCE-badge {{ background: #fff3cd; color: #856404; }}
        .class-NOT_A_STORY-badge {{ background: #f8d7da; color: #721c24; }}
        .criteria-badge {{ background: #e7f3ff; color: #0066cc; }}

        /* Story Content */
        .story-content {{ padding: 20px; }}
        .summary {{ background: #f0f7ff; padding: 15px; border-left: 4px solid #3498db; margin-bottom: 20px; font-style: italic; }}

        /* Text display */
        .text-container {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }}
        @media (max-width: 1024px) {{ .text-container {{ grid-template-columns: 1fr; }} }}
        .text-section h3 {{ color: #2c3e50; margin-bottom: 10px; font-size: 16px; }}
        .text-content {{ padding: 15px; background: #f8f9fa; border-radius: 8px; line-height: 1.8; font-size: 15px; max-height: 400px; overflow-y: auto; }}
        .text-content div {{ margin: 5px 0; }}
        .hebrew {{ direction: rtl; text-align: right; font-family: 'Times New Roman', serif; font-size: 18px; }}
        .story-text {{ background: #fff3cd; padding: 8px; border-left: 3px solid #f39c12; margin: 5px 0; }}

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

        /* Self-check */
        .self-check {{ background: #e8f5e9; padding: 15px; border-left: 4px solid #27ae60; margin-bottom: 20px; }}
        .self-check h4 {{ color: #2c3e50; margin-bottom: 8px; font-size: 14px; }}
        .adjustment {{ font-weight: 600; color: #27ae60; }}

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
        .feedback-note {{ flex: 1; min-width: 250px; }}
        .feedback-note input {{ width: 100%; padding: 10px; border: 2px solid #e0e0e0; border-radius: 6px; }}

        /* Export */
        .export-section {{ text-align: center; margin-top: 30px; padding: 30px; background: white; border-radius: 12px; }}
        .export-btn {{ padding: 15px 40px; background: #3498db; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; margin: 5px; }}
        .export-btn:hover {{ background: #2980b9; }}

        .no-results {{ text-align: center; padding: 60px 20px; color: #7f8c8d; font-size: 18px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Talmud Story Review <span class="version-badge">v5.1 Categorical</span></h1>
            <p>Enhanced with disqualifiers, weakeners, criteria breakdown, and self-check tracking</p>
            <div class="stats" id="stats"></div>
        </div>

        <div class="controls">
            <div class="filters">
                <div class="control-group">
                    <label>Classification Filter</label>
                    <select id="filterClass">
                        <option value="all">All Classifications</option>
                        <option value="YES">YES (Definitive)</option>
                        <option value="HIGH_CONFIDENCE">HIGH_CONFIDENCE</option>
                        <option value="LOW_CONFIDENCE">LOW_CONFIDENCE</option>
                        <option value="NOT_A_STORY">NOT_A_STORY</option>
                    </select>
                </div>
                <div class="control-group">
                    <label>Page Reference</label>
                    <input type="text" id="searchPage" placeholder="e.g., 8b, 27b">
                </div>
                <div class="control-group">
                    <label>Criteria Met</label>
                    <select id="filterCriteria">
                        <option value="all">Any Criteria Count</option>
                        <option value="6">6/6 (All)</option>
                        <option value="5">5/6</option>
                        <option value="4">4/6</option>
                        <option value="3">3/6</option>
                    </select>
                </div>
                <div class="control-group">
                    <label>Has Disqualifiers</label>
                    <select id="filterDisq">
                        <option value="all">All Stories</option>
                        <option value="yes">With Disqualifiers</option>
                        <option value="no">No Disqualifiers</option>
                    </select>
                </div>
                <div class="control-group">
                    <label>Reviewer Name</label>
                    <input type="text" id="reviewerName" placeholder="Your name">
                </div>
            </div>
        </div>

        <div id="storiesContainer"><div class="no-results">Loading stories...</div></div>

        <div class="export-section">
            <h2>Export Validation Feedback</h2>
            <p style="margin: 15px 0; color: #7f8c8d;">Feedback auto-saves to browser storage</p>
            <button class="export-btn" onclick="exportFeedback()">Download Feedback JSON</button>
            <button class="export-btn" onclick="clearFeedback()" style="background: #e74c3c;">Clear All</button>
        </div>
    </div>

    <script id="storiesData" type="application/json">
{stories_json}
    </script>

    <script>
        const rawData = JSON.parse(document.getElementById('storiesData').textContent);
        let allStories = [];
        let feedback = JSON.parse(localStorage.getItem('v5_1_story_feedback') || '{{}}');

        // Flatten stories from pages
        rawData.pages.forEach(page => {{
            page.stories.forEach(story => {{
                allStories.push({{
                    ...story,
                    page_ref: page.ref,
                    page_segments: page.segments,
                    storyId: `${{page.ref}}_${{story.start_segment}}-${{story.end_segment}}`
                }});
            }});
        }});

        function getStoryText(story) {{
            // Extract text segments for this story
            const start = story.start_segment;
            const end = story.end_segment;
            const segments = story.page_segments || [];

            let englishParts = [];
            let hebrewParts = [];

            for (let i = 0; i < segments.length; i++) {{
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
            const not = allStories.filter(s => s.classification === 'NOT_A_STORY').length;
            const reviewed = Object.keys(feedback).length;

            document.getElementById('stats').innerHTML = `
                <div class="stat-box stat-yes"><div class="number">${{yes}}</div><div class="label">YES</div></div>
                <div class="stat-box stat-high"><div class="number">${{high}}</div><div class="label">HIGH</div></div>
                <div class="stat-box stat-low"><div class="number">${{low}}</div><div class="label">LOW</div></div>
                <div class="stat-box stat-not"><div class="number">${{not}}</div><div class="label">NOT_A_STORY</div></div>
                <div class="stat-box"><div class="number">${{reviewed}}</div><div class="label">Reviewed</div></div>
            `;
        }}

        function renderStory(story) {{
            const fb = feedback[story.storyId] || {{}};
            const criteria = story.criteria || {{}};
            const disqs = story.disqualifiers_found || [];
            const weaks = story.weakeners_found || [];
            const texts = getStoryText(story);

            let html = `
                <div class="story-card class-${{story.classification}}">
                    <div class="story-header">
                        <div class="story-ref">${{story.page_ref}} (Segments ${{story.start_segment}}-${{story.end_segment}})</div>
                        <div class="story-meta">
                            <span class="badge class-${{story.classification}}-badge">${{story.classification.replace('_', ' ')}}</span>
                            <span class="badge criteria-badge">${{story.criteria_met_count}}/6 Criteria</span>
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

                        <div class="criteria-breakdown">
                            <h3>Criteria Assessment (${{story.criteria_met_count}}/6)</h3>
                            ${{Object.entries(criteria).map(([name, data]) => `
                                <div class="criterion">
                                    <span class="criterion-icon ${{data.met ? 'criterion-met' : 'criterion-unmet'}}">${{data.met ? '✓' : '✗'}}</span>
                                    <span class="criterion-name">${{name.replace('_', ' ')}}</span>
                                    ${{data.reasoning ? `<span class="criterion-detail"> - ${{data.reasoning}}</span>` : ''}}
                                </div>
                            `).join('')}}
                        </div>

                        ${{disqs.length > 0 ? `
                            <div class="flags-section disqualifiers">
                                <h4>🚫 Disqualifiers Applied (${{disqs.length}})</h4>
                                ${{disqs.map(d => `<span class="flag-item">${{d.replace('_', ' ')}}</span>`).join('')}}
                            </div>
                        ` : ''}}

                        ${{weaks.length > 0 ? `
                            <div class="flags-section">
                                <h4>⚠️ Weakeners Applied (${{weaks.length}})</h4>
                                ${{weaks.map(w => `<span class="flag-item">${{w.replace('_', ' ')}}</span>`).join('')}}
                            </div>
                        ` : ''}}

                        ${{story.self_check_adjustment ? `
                            <div class="self-check">
                                <h4>🔍 Self-Check Adjustment</h4>
                                <span class="adjustment">${{story.self_check_adjustment}}</span>
                            </div>
                        ` : ''}}

                        <div class="reasoning">
                            <strong>Classification Reasoning:</strong> ${{story.classification_reasoning || 'No reasoning provided'}}
                        </div>
                    </div>

                    <div class="feedback-section">
                        <div class="feedback-row">
                            <button class="feedback-btn correct ${{fb.verdict === 'correct' ? 'active' : ''}}"
                                    onclick="setVerdict('${{story.storyId}}', 'correct')">✓ Correct</button>
                            <button class="feedback-btn incorrect ${{fb.verdict === 'incorrect' ? 'active' : ''}}"
                                    onclick="setVerdict('${{story.storyId}}', 'incorrect')">✗ Incorrect</button>
                            <div class="feedback-note">
                                <input type="text" placeholder="Notes..." value="${{fb.note || ''}}"
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
            const pageSearch = document.getElementById('searchPage').value.toLowerCase();
            const criteriaFilter = document.getElementById('filterCriteria').value;
            const disqFilter = document.getElementById('filterDisq').value;

            let filtered = allStories.filter(story => {{
                if (classFilter !== 'all' && story.classification !== classFilter) return false;
                if (pageSearch && !story.page_ref.toLowerCase().includes(pageSearch)) return false;
                if (criteriaFilter !== 'all' && story.criteria_met_count !== parseInt(criteriaFilter)) return false;
                if (disqFilter === 'yes' && (story.disqualifiers_found || []).length === 0) return false;
                if (disqFilter === 'no' && (story.disqualifiers_found || []).length > 0) return false;
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
            localStorage.setItem('v5_1_story_feedback', JSON.stringify(feedback));
        }}

        function exportFeedback() {{
            const reviewer = document.getElementById('reviewerName').value || 'anonymous';
            const data = {{
                reviewer: reviewer,
                version: 'v5.1_categorical',
                exportDate: new Date().toISOString(),
                totalStories: allStories.length,
                reviewed: Object.keys(feedback).length,
                feedback: feedback
            }};

            const blob = new Blob([JSON.stringify(data, null, 2)], {{type: 'application/json'}});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `v5_1_feedback_${{reviewer}}_${{new Date().toISOString().slice(0,10)}}.json`;
            a.click();
        }}

        function clearFeedback() {{
            if (confirm('Clear all feedback? This cannot be undone.')) {{
                feedback = {{}};
                localStorage.removeItem('v5_1_story_feedback');
                renderStories();
            }}
        }}

        // Event listeners
        document.getElementById('filterClass').addEventListener('change', renderStories);
        document.getElementById('searchPage').addEventListener('input', renderStories);
        document.getElementById('filterCriteria').addEventListener('change', renderStories);
        document.getElementById('filterDisq').addEventListener('change', renderStories);

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
    # Default to v5.1 full validation results
    input_file = 'results/v5/ketubot_v5.1_full_validation_2-39.json'
    output_file = 'v5_1_review_ui.html'

    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]

    print(f"Loading v5.1 results from: {input_file}")
    data = load_v5_1_results(input_file)

    print(f"Generating review UI: {output_file}")
    generate_html(data, output_file)

    # Stats
    total_pages = len(data['pages'])
    total_stories = sum(len(p['stories']) for p in data['pages'])

    print(f"\n✓ Generated {output_file}")
    print(f"  Pages: {total_pages}")
    print(f"  Stories: {total_stories}")
    print(f"  YES: {data['summary']['yes']}")
    print(f"  HIGH_CONFIDENCE: {data['summary']['high_confidence']}")
    print(f"  LOW_CONFIDENCE: {data['summary']['low_confidence']}")
    print(f"  NOT_A_STORY: {data['summary']['not_a_story']}")

if __name__ == '__main__':
    main()
