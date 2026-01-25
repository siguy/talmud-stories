#!/usr/bin/env python3
"""Generate jeff_review.html with embedded JSON data."""

import json

# Read the JSON files
with open('ketubot_stories.json', 'r') as f:
    stories_json = f.read()

with open('validation_results.json', 'r') as f:
    validation_json = f.read()

html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Expert Review - Jeffrey Rubenstein</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; padding: 20px; line-height: 1.6; }
        .container { max-width: 1400px; margin: 0 auto; }
        .header { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 30px; }
        .header h1 { color: #2c3e50; margin-bottom: 10px; }
        .header p { color: #7f8c8d; font-size: 16px; }
        .expert-info { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin: 20px 0; }
        .expert-info h2 { margin-bottom: 5px; }
        .expert-info p { color: rgba(255,255,255,0.9); font-size: 14px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; margin-top: 20px; }
        .stat-box { background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }
        .stat-box .number { font-size: 32px; font-weight: bold; color: #3498db; }
        .stat-box .label { color: #7f8c8d; font-size: 14px; margin-top: 5px; }
        .stat-box.validated { background: #d4edda; border-left: 4px solid #27ae60; }
        .stat-box.validated .number { color: #27ae60; }
        .stat-box.needs-review { background: #fff3cd; border-left: 4px solid #f39c12; }
        .stat-box.needs-review .number { color: #f39c12; }
        .controls { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .control-group { margin-bottom: 20px; }
        .control-group:last-child { margin-bottom: 0; }
        .control-group label { display: block; font-weight: 600; color: #2c3e50; margin-bottom: 8px; }
        .filters { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; }
        select, input[type="range"], input[type="text"] { width: 100%; padding: 10px; border: 2px solid #e0e0e0; border-radius: 6px; font-size: 14px; }
        .range-value { color: #3498db; font-weight: bold; margin-left: 10px; }
        .story-card { background: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 20px; overflow: hidden; }
        .story-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.15); }
        .story-card.validated-story { border-left: 5px solid #27ae60; background: linear-gradient(to right, #d4edda 0%, white 15%); }
        .story-card.needs-review { border-left: 5px solid #f39c12; }
        .story-header { padding: 20px; background: #f8f9fa; border-bottom: 2px solid #e0e0e0; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px; }
        .story-ref { font-size: 20px; font-weight: bold; color: #2c3e50; }
        .story-meta { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
        .badge { padding: 6px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; text-transform: uppercase; }
        .confidence-high { background: #d4edda; color: #155724; }
        .confidence-medium { background: #fff3cd; color: #856404; }
        .confidence-low { background: #f8d7da; color: #721c24; }
        .type-full_narrative { background: #cfe2ff; color: #084298; }
        .type-dialogue_vignette { background: #e7d6f5; color: #6f42c1; }
        .type-brief_anecdote { background: #d1e7dd; color: #0f5132; }
        .multi-page { background: #ff6b6b; color: white; }
        .badge.jeff-validated { background: #27ae60; color: white; }
        .badge.needs-review-badge { background: #f39c12; color: white; }
        .story-content { padding: 20px; }
        .summary { background: #f0f7ff; padding: 15px; border-left: 4px solid #3498db; margin-bottom: 20px; font-style: italic; color: #2c3e50; }
        .jeff-feedback { background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%); border: 2px solid #27ae60; border-radius: 10px; padding: 20px; margin-bottom: 20px; }
        .jeff-feedback h4 { color: #155724; margin-bottom: 15px; }
        .jeff-verdict { font-size: 18px; font-weight: bold; padding: 10px 15px; border-radius: 8px; display: inline-block; margin-bottom: 15px; background: #27ae60; color: white; }
        .jeff-notes, .jeff-reasoning { background: white; padding: 15px; border-radius: 8px; margin-top: 10px; }
        .jeff-notes strong, .jeff-reasoning strong { color: #155724; }
        .text-section { margin-bottom: 20px; }
        .text-section h3 { color: #2c3e50; margin-bottom: 10px; font-size: 16px; }
        .text-content { padding: 15px; background: #f8f9fa; border-radius: 8px; white-space: pre-wrap; line-height: 1.8; font-size: 15px; max-height: 400px; overflow-y: auto; }
        .hebrew { direction: rtl; text-align: right; font-family: 'Times New Roman', serif; font-size: 18px; }
        .text-container-sidebyside { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
        @media (max-width: 1024px) { .text-container-sidebyside { grid-template-columns: 1fr; } }
        .narrative-elements { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 15px; }
        .element { padding: 6px 12px; background: #e8f5e9; color: #2e7d32; border-radius: 6px; font-size: 13px; }
        .feedback-section { padding: 20px; background: #f8f9fa; border-top: 2px solid #e0e0e0; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px; }
        .feedback-buttons { display: flex; gap: 10px; }
        .feedback-btn { padding: 10px 24px; border: 2px solid; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; }
        .feedback-btn.correct { background: white; border-color: #27ae60; color: #27ae60; }
        .feedback-btn.correct:hover, .feedback-btn.correct.active { background: #27ae60; color: white; }
        .feedback-btn.false-positive { background: white; border-color: #e74c3c; color: #e74c3c; }
        .feedback-btn.false-positive:hover, .feedback-btn.false-positive.active { background: #e74c3c; color: white; }
        .feedback-note { flex: 1; min-width: 200px; }
        .feedback-note input { width: 100%; padding: 8px 12px; border: 2px solid #e0e0e0; border-radius: 6px; }
        .export-section { text-align: center; margin-top: 30px; padding: 30px; background: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        .export-btn { padding: 15px 40px; background: #3498db; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; margin: 5px; }
        .export-btn:hover { background: #2980b9; }
        .no-results { text-align: center; padding: 60px 20px; color: #7f8c8d; font-size: 18px; }
        .reasoning { margin-top: 15px; padding: 15px; background: #fff9e6; border-left: 4px solid #f39c12; font-size: 14px; color: #2c3e50; }
        .reasoning strong { color: #f39c12; }
        .validation-notes { margin-top: 15px; padding: 15px; background: #e8f5e9; border-left: 4px solid #27ae60; font-size: 14px; color: #2c3e50; }
        .validation-notes strong { color: #27ae60; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Expert Review: Ketubot Stories</h1>
            <p>258 AI-identified stories from Tractate Ketubot (analyzed with Gemini 2.0 Flash)</p>
            <div class="expert-info">
                <h2>Reviewer: Jeffrey Rubenstein</h2>
                <p>Talmud Scholar - Prior validations are highlighted below</p>
            </div>
            <div class="stats" id="stats"></div>
        </div>
        <div class="controls">
            <div class="filters">
                <div class="control-group">
                    <label>Validation Status</label>
                    <select id="filterValidation">
                        <option value="all">All Stories</option>
                        <option value="validated">Jeff Validated Only</option>
                        <option value="needs_review">Needs Review</option>
                    </select>
                </div>
                <div class="control-group">
                    <label>Search by Reference</label>
                    <input type="text" id="searchRef" placeholder="e.g., 8b, 10b, 20b">
                </div>
                <div class="control-group">
                    <label>Story Type</label>
                    <select id="filterType">
                        <option value="all">All Types</option>
                        <option value="full_narrative">Full Narratives</option>
                        <option value="dialogue_vignette">Dialogue Vignettes</option>
                        <option value="brief_anecdote">Brief Anecdotes</option>
                    </select>
                </div>
                <div class="control-group">
                    <label>Minimum Confidence: <span class="range-value" id="confValue">0%</span></label>
                    <input type="range" id="filterConfidence" min="0" max="100" value="0">
                </div>
            </div>
        </div>
        <div id="storiesContainer"><div class="no-results">Loading stories...</div></div>
        <div class="export-section">
            <h2>Export Your Feedback</h2>
            <p style="margin: 15px 0; color: #7f8c8d;">Download your expert review</p>
            <div style="margin: 20px 0; padding: 15px; background: #e8f5e9; border-radius: 8px;">
                <span id="autoSaveStatus" style="color: #27ae60; font-weight: 600;">Auto-saved</span>
                <div id="lastSavedTime" style="font-size: 14px; color: #7f8c8d; margin-top: 5px;"></div>
            </div>
            <button class="export-btn" onclick="exportFeedback()">Download Feedback JSON</button>
            <button class="export-btn" onclick="clearFeedback()" style="background: #e74c3c;">Clear All Feedback</button>
        </div>
    </div>
    <script id="storiesData" type="application/json">
''' + stories_json + '''
    </script>
    <script id="validationData" type="application/json">
''' + validation_json + '''
    </script>
    <script>
        const storiesData = JSON.parse(document.getElementById('storiesData').textContent);
        const validationJson = JSON.parse(document.getElementById('validationData').textContent);

        let stories = storiesData.stories || [];
        let validationData = {};
        let feedback = {};

        validationJson.details.forEach(v => { validationData[v.ref] = v; });

        function getValidationStatus(ref) {
            const baseRef = ref.split('-')[0].trim();
            const validation = validationData[baseRef];
            if (!validation) return { status: 'needs_review', validation: null };
            if (validation.expected === true) return { status: 'validated_story', validation: validation };
            return { status: 'needs_review', validation: null };
        }

        function initializeApp() {
            loadSavedFeedback();
            updateStats();
            renderStories();
            setupEventListeners();
            updateAutoSaveStatus();
        }

        function saveFeedback() {
            localStorage.setItem('jeff_talmud_feedback', JSON.stringify(feedback));
            localStorage.setItem('jeff_talmud_feedback_timestamp', new Date().toISOString());
            updateAutoSaveStatus();
        }

        function loadSavedFeedback() {
            try { const s = localStorage.getItem('jeff_talmud_feedback'); if (s) feedback = JSON.parse(s); } catch(e) { feedback = {}; }
        }

        function updateAutoSaveStatus() {
            const ts = localStorage.getItem('jeff_talmud_feedback_timestamp');
            const fc = Object.keys(feedback).length;
            const se = document.getElementById('autoSaveStatus');
            const te = document.getElementById('lastSavedTime');
            se.textContent = fc === 0 ? 'No feedback yet' : 'Auto-saved (' + fc + ' stories)';
            se.style.color = fc === 0 ? '#7f8c8d' : '#27ae60';
            if (ts && fc > 0) {
                const dm = Math.floor((new Date() - new Date(ts)) / 60000);
                te.textContent = dm < 1 ? 'Just now' : dm < 60 ? dm + ' min ago' : Math.floor(dm/60) + ' hr ago';
            } else { te.textContent = ''; }
        }

        function clearFeedback() {
            if (Object.keys(feedback).length === 0) { alert('No feedback'); return; }
            if (confirm('Clear all feedback?')) {
                feedback = {};
                localStorage.removeItem('jeff_talmud_feedback');
                localStorage.removeItem('jeff_talmud_feedback_timestamp');
                renderStories();
                updateAutoSaveStatus();
            }
        }

        function updateStats() {
            const vc = stories.filter(s => getValidationStatus(s.ref).status === 'validated_story').length;
            const nc = stories.length - vc;
            const mp = stories.filter(s => s.spans_multiple_pages).length;
            const ac = stories.reduce((sum, s) => sum + s.analysis.confidence, 0) / stories.length;
            document.getElementById('stats').innerHTML =
                '<div class="stat-box"><div class="number">' + stories.length + '</div><div class="label">Total Stories</div></div>' +
                '<div class="stat-box validated"><div class="number">' + vc + '</div><div class="label">Jeff Validated</div></div>' +
                '<div class="stat-box needs-review"><div class="number">' + nc + '</div><div class="label">Needs Review</div></div>' +
                '<div class="stat-box"><div class="number">' + ac.toFixed(0) + '%</div><div class="label">Avg Confidence</div></div>' +
                '<div class="stat-box"><div class="number">' + mp + '</div><div class="label">Multi-Page</div></div>';
        }

        function renderStories() {
            const st = document.getElementById('searchRef').value.toLowerCase();
            const tf = document.getElementById('filterType').value;
            const cf = parseInt(document.getElementById('filterConfidence').value);
            const vf = document.getElementById('filterValidation').value;

            const filtered = stories.filter(story => {
                const vs = getValidationStatus(story.ref);
                if (st && !story.ref.toLowerCase().includes(st)) return false;
                if (tf !== 'all' && story.analysis.story_type !== tf) return false;
                if (story.analysis.confidence < cf) return false;
                if (vf === 'validated' && vs.status !== 'validated_story') return false;
                if (vf === 'needs_review' && vs.status === 'validated_story') return false;
                return true;
            });

            if (filtered.length === 0) {
                document.getElementById('storiesContainer').innerHTML = '<div class="no-results">No stories match filters</div>';
                return;
            }

            document.getElementById('storiesContainer').innerHTML = filtered.map((story, i) => {
                const cc = story.analysis.confidence >= 90 ? 'high' : story.analysis.confidence >= 75 ? 'medium' : 'low';
                const el = Object.entries(story.analysis.narrative_elements).filter(([k,v]) => v).map(([k]) => k.replace('has_', '').replace('_', ' '));
                const sf = feedback[story.ref] || { type: null, note: '' };
                const vi = getValidationStatus(story.ref);
                const cls = vi.status === 'validated_story' ? 'validated-story' : 'needs-review';

                let html = '<div class="story-card ' + cls + '">';
                html += '<div class="story-header"><div class="story-ref">' + story.ref + '</div><div class="story-meta">';
                html += vi.status === 'validated_story' ? '<span class="badge jeff-validated">Jeff Validated</span>' : '<span class="badge needs-review-badge">Needs Review</span>';
                html += '<span class="badge confidence-' + cc + '">' + story.analysis.confidence + '%</span>';
                html += '<span class="badge type-' + story.analysis.story_type + '">' + story.analysis.story_type.replace('_', ' ') + '</span>';
                if (story.spans_multiple_pages) html += '<span class="badge multi-page">Multi-Page</span>';
                html += '</div></div><div class="story-content">';

                if (vi.validation) {
                    html += '<div class="jeff-feedback"><h4>Expert Validation (Jeffrey Rubenstein)</h4>';
                    html += '<div class="jeff-verdict">Confirmed as Story</div>';
                    if (vi.validation.validation_notes) html += '<div class="jeff-notes"><strong>Validation Notes:</strong><br>' + vi.validation.validation_notes + '</div>';
                    if (vi.validation.reasoning) html += '<div class="jeff-reasoning"><strong>Reasoning:</strong><br>' + vi.validation.reasoning + '</div>';
                    html += '</div>';
                }

                if (story.analysis.one_sentence_summary) html += '<div class="summary"><strong>Summary:</strong> ' + story.analysis.one_sentence_summary + '</div>';
                html += '<div class="text-container-sidebyside"><div class="text-section"><h3>English Translation</h3><div class="text-content">' + story.text + '</div></div>';
                if (story.hebrew_text) html += '<div class="text-section"><h3>Hebrew/Aramaic</h3><div class="text-content hebrew">' + story.hebrew_text + '</div></div>';
                html += '</div>';
                html += '<div class="reasoning"><strong>AI Reasoning:</strong> ' + story.analysis.reasoning + '</div>';
                if (story.analysis.validation_notes) html += '<div class="validation-notes"><strong>AI Validation:</strong> ' + story.analysis.validation_notes + '</div>';
                html += '<div class="narrative-elements">' + el.map(e => '<span class="element">' + e + '</span>').join('') + '</div></div>';

                html += '<div class="feedback-section"><div><strong>Is this correct?</strong></div><div class="feedback-buttons">';
                html += '<button class="feedback-btn correct ' + (sf.type === 'correct' ? 'active' : '') + '" onclick="markFeedback(\\'' + story.ref + '\\', \\'correct\\')">Correct</button>';
                html += '<button class="feedback-btn false-positive ' + (sf.type === 'false_positive' ? 'active' : '') + '" onclick="markFeedback(\\'' + story.ref + '\\', \\'false_positive\\')">False Positive</button>';
                html += '</div><div class="feedback-note"><input type="text" placeholder="Notes..." value="' + (sf.note || '') + '" onchange="updateNote(\\'' + story.ref + '\\', this.value)"></div></div></div>';
                return html;
            }).join('');
        }

        function setupEventListeners() {
            document.getElementById('searchRef').addEventListener('input', renderStories);
            document.getElementById('filterType').addEventListener('change', renderStories);
            document.getElementById('filterValidation').addEventListener('change', renderStories);
            document.getElementById('filterConfidence').addEventListener('input', function(e) {
                document.getElementById('confValue').textContent = e.target.value + '%';
                renderStories();
            });
        }

        function markFeedback(ref, type) {
            if (!feedback[ref]) feedback[ref] = { type: null, note: '' };
            feedback[ref].type = feedback[ref].type === type ? null : type;
            saveFeedback();
            renderStories();
        }

        function updateNote(ref, note) {
            if (!feedback[ref]) feedback[ref] = { type: null, note: '' };
            feedback[ref].note = note;
            saveFeedback();
        }

        function exportFeedback() {
            const data = {
                reviewer_name: 'Jeffrey Rubenstein',
                reviewed_at: new Date().toISOString(),
                tractate: 'Ketubot',
                total_stories: stories.length,
                reviewed_count: Object.keys(feedback).length,
                feedback: Object.entries(feedback).map(function(e) {
                    const s = stories.find(function(st) { return st.ref === e[0]; });
                    return { ref: e[0], feedback_type: e[1].type, notes: e[1].note, confidence: s ? s.analysis.confidence : null, story_type: s ? s.analysis.story_type : null };
                })
            };
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'ketubot_review_jeff_' + new Date().toISOString().split('T')[0] + '.json';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }

        initializeApp();
    </script>
</body>
</html>'''

# Write the final HTML file
with open('jeff_review.html', 'w') as f:
    f.write(html_template)

print("Generated jeff_review.html successfully!")
print(f"File size: {len(html_template):,} bytes")
