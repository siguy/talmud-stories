#!/usr/bin/env python3
"""
Generate review_ui.html with embedded JSON data.
Features:
- Full page text with highlighted story boundaries
- Multiple reviewer support (not just Jeff)
- Page ordering (a before b, chronological)
- Too Short / Too Long / Correct Length feedback
- Context lines displayed in gray
"""

import json
import re
import os

# Read the JSON file
input_file = 'test_full_page_results.json'
if not os.path.exists(input_file):
    print(f"Error: {input_file} not found. Run test_full_page_approach.py first.")
    exit(1)

with open(input_file, 'r') as f:
    data = json.load(f)

# Convert to embedded JSON
stories_json = json.dumps(data, ensure_ascii=False)

html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Talmud Story Review</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; padding: 20px; line-height: 1.6; }
        .container { max-width: 1400px; margin: 0 auto; }
        .header { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 30px; }
        .header h1 { color: #2c3e50; margin-bottom: 10px; }
        .header p { color: #7f8c8d; font-size: 16px; }

        /* Reviewer selection */
        .reviewer-section { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin: 20px 0; }
        .reviewer-section label { font-weight: bold; margin-right: 10px; }
        .reviewer-section input { padding: 8px 15px; border-radius: 6px; border: none; font-size: 16px; width: 200px; }

        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-top: 20px; }
        .stat-box { background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }
        .stat-box .number { font-size: 28px; font-weight: bold; color: #3498db; }
        .stat-box .label { color: #7f8c8d; font-size: 13px; margin-top: 5px; }

        .controls { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .filters { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }
        .control-group { margin-bottom: 15px; }
        .control-group label { display: block; font-weight: 600; color: #2c3e50; margin-bottom: 8px; }
        select, input[type="text"] { width: 100%; padding: 10px; border: 2px solid #e0e0e0; border-radius: 6px; font-size: 14px; }

        /* Story cards */
        .story-card { background: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 20px; overflow: hidden; }
        .story-header { padding: 20px; background: #f8f9fa; border-bottom: 2px solid #e0e0e0; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px; }
        .story-ref { font-size: 20px; font-weight: bold; color: #2c3e50; }
        .story-meta { display: flex; gap: 10px; flex-wrap: wrap; }

        .badge { padding: 6px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; text-transform: uppercase; }
        .confidence-high { background: #d4edda; color: #155724; }
        .confidence-medium { background: #fff3cd; color: #856404; }
        .type-full_narrative { background: #cfe2ff; color: #084298; }
        .type-dialogue_vignette { background: #e7d6f5; color: #6f42c1; }
        .type-brief_anecdote { background: #d1e7dd; color: #0f5132; }

        .story-content { padding: 20px; }
        .summary { background: #f0f7ff; padding: 15px; border-left: 4px solid #3498db; margin-bottom: 20px; font-style: italic; }

        /* Text display with context */
        .text-section { margin-bottom: 20px; }
        .text-section h3 { color: #2c3e50; margin-bottom: 10px; font-size: 16px; display: flex; justify-content: space-between; align-items: center; }
        .text-content { padding: 15px; background: #f8f9fa; border-radius: 8px; line-height: 1.8; font-size: 15px; max-height: 500px; overflow-y: auto; }
        .hebrew { direction: rtl; text-align: right; font-family: 'Times New Roman', serif; font-size: 18px; }

        /* Story highlighting */
        .context-before, .context-after { color: #999; font-size: 14px; }
        .story-highlight { background: #fff3cd; border-left: 3px solid #f39c12; padding-left: 10px; margin: 5px 0; }
        .highlight-start { border-top: 2px solid #27ae60; }
        .highlight-end { border-bottom: 2px solid #e74c3c; }

        .text-container { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        @media (max-width: 1024px) { .text-container { grid-template-columns: 1fr; } }

        /* Length feedback buttons */
        .length-feedback { display: flex; gap: 10px; margin-top: 15px; padding: 15px; background: #f8f9fa; border-radius: 8px; align-items: center; flex-wrap: wrap; }
        .length-feedback label { font-weight: 600; color: #2c3e50; margin-right: 15px; }
        .length-btn { padding: 8px 16px; border: 2px solid; border-radius: 6px; font-size: 14px; font-weight: 600; cursor: pointer; background: white; }
        .length-btn.too-short { border-color: #e74c3c; color: #e74c3c; }
        .length-btn.too-short:hover, .length-btn.too-short.active { background: #e74c3c; color: white; }
        .length-btn.correct { border-color: #27ae60; color: #27ae60; }
        .length-btn.correct:hover, .length-btn.correct.active { background: #27ae60; color: white; }
        .length-btn.too-long { border-color: #f39c12; color: #f39c12; }
        .length-btn.too-long:hover, .length-btn.too-long.active { background: #f39c12; color: white; }

        /* Main feedback section */
        .feedback-section { padding: 20px; background: #f8f9fa; border-top: 2px solid #e0e0e0; }
        .feedback-row { display: flex; gap: 15px; align-items: center; flex-wrap: wrap; margin-bottom: 15px; }
        .feedback-btn { padding: 10px 24px; border: 2px solid; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; background: white; }
        .feedback-btn.is-story { border-color: #27ae60; color: #27ae60; }
        .feedback-btn.is-story:hover, .feedback-btn.is-story.active { background: #27ae60; color: white; }
        .feedback-btn.not-story { border-color: #e74c3c; color: #e74c3c; }
        .feedback-btn.not-story:hover, .feedback-btn.not-story.active { background: #e74c3c; color: white; }
        .feedback-note { flex: 1; min-width: 250px; }
        .feedback-note input { width: 100%; padding: 10px; border: 2px solid #e0e0e0; border-radius: 6px; }

        .export-section { text-align: center; margin-top: 30px; padding: 30px; background: white; border-radius: 12px; }
        .export-btn { padding: 15px 40px; background: #3498db; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; margin: 5px; }
        .export-btn:hover { background: #2980b9; }
        .no-results { text-align: center; padding: 60px 20px; color: #7f8c8d; font-size: 18px; }

        .reasoning { margin-top: 15px; padding: 15px; background: #fff9e6; border-left: 4px solid #f39c12; font-size: 14px; }
        .char-info { font-size: 12px; color: #999; margin-top: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Talmud Story Review Interface</h1>
            <p>Full page context with highlighted story boundaries</p>

            <div class="reviewer-section">
                <label for="reviewerName">Reviewer Name:</label>
                <input type="text" id="reviewerName" placeholder="Enter your name" value="">
            </div>

            <div class="stats" id="stats"></div>
        </div>

        <div class="controls">
            <div class="filters">
                <div class="control-group">
                    <label>Filter by Page</label>
                    <select id="filterPage">
                        <option value="all">All Pages</option>
                    </select>
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
                    <label>Sort By</label>
                    <select id="sortBy">
                        <option value="page">Page Order (a→b, 2→112)</option>
                        <option value="confidence">Confidence (High→Low)</option>
                        <option value="type">Story Type</option>
                    </select>
                </div>
            </div>
        </div>

        <div id="storiesContainer"><div class="no-results">Loading stories...</div></div>

        <div class="export-section">
            <h2>Export Feedback</h2>
            <p style="margin: 15px 0; color: #7f8c8d;">Feedback auto-saves to browser storage</p>
            <button class="export-btn" onclick="exportFeedback()">Download Feedback JSON</button>
            <button class="export-btn" onclick="clearFeedback()" style="background: #e74c3c;">Clear All</button>
        </div>
    </div>

    <script id="storiesData" type="application/json">
''' + stories_json + '''
    </script>

    <script>
        // Parse embedded data
        const rawData = JSON.parse(document.getElementById('storiesData').textContent);

        // Flatten stories with page context
        let allStories = [];
        rawData.pages.forEach(page => {
            const stories = page.analysis?.stories || [];
            stories.forEach((story, idx) => {
                allStories.push({
                    ...story,
                    ref: page.ref,
                    pageIndex: idx,
                    fullEnglish: page.full_english,
                    fullHebrew: page.full_hebrew,
                    englishLength: page.english_length,
                    hebrewLength: page.hebrew_length
                });
            });
        });

        // Feedback storage
        let feedback = JSON.parse(localStorage.getItem('talmud_story_feedback') || '{}');

        // Sort pages properly (a before b, then by number)
        function sortPageRef(a, b) {
            const parseRef = (ref) => {
                const match = ref.match(/(\\d+)([ab])?/);
                if (!match) return { num: 0, side: 'a' };
                return { num: parseInt(match[1]), side: match[2] || 'a' };
            };
            const pa = parseRef(a);
            const pb = parseRef(b);
            if (pa.num !== pb.num) return pa.num - pb.num;
            return pa.side.localeCompare(pb.side);
        }

        // Get unique pages sorted
        const uniquePages = [...new Set(allStories.map(s => s.ref))].sort(sortPageRef);

        // Populate page filter
        const pageFilter = document.getElementById('filterPage');
        uniquePages.forEach(ref => {
            const opt = document.createElement('option');
            opt.value = ref;
            opt.textContent = ref;
            pageFilter.appendChild(opt);
        });

        // Render stats
        function renderStats() {
            const reviewed = Object.keys(feedback).length;
            const isStory = Object.values(feedback).filter(f => f.verdict === 'is_story').length;
            const notStory = Object.values(feedback).filter(f => f.verdict === 'not_story').length;

            document.getElementById('stats').innerHTML = `
                <div class="stat-box"><div class="number">${allStories.length}</div><div class="label">Total Stories</div></div>
                <div class="stat-box"><div class="number">${rawData.pages.length}</div><div class="label">Pages</div></div>
                <div class="stat-box"><div class="number">${reviewed}</div><div class="label">Reviewed</div></div>
                <div class="stat-box"><div class="number">${isStory}</div><div class="label">Confirmed</div></div>
                <div class="stat-box"><div class="number">${notStory}</div><div class="label">Rejected</div></div>
            `;
        }

        // Extract text with context highlighting
        function getTextWithContext(fullText, startChar, endChar, contextChars = 150) {
            if (startChar < 0 || endChar < 0) return { before: '', story: fullText.slice(0, 500) + '...', after: '' };

            const beforeStart = Math.max(0, startChar - contextChars);
            const afterEnd = Math.min(fullText.length, endChar + contextChars);

            return {
                before: fullText.slice(beforeStart, startChar),
                story: fullText.slice(startChar, endChar),
                after: fullText.slice(endChar, afterEnd)
            };
        }

        // Render a single story card
        function renderStoryCard(story) {
            const storyId = `${story.ref}_${story.story_number}`;
            const fb = feedback[storyId] || {};

            const confClass = story.confidence >= 90 ? 'confidence-high' : 'confidence-medium';
            const typeClass = `type-${story.story_type}`;

            // Get text with context
            const englishText = getTextWithContext(
                story.fullEnglish,
                story.story_start_char_english,
                story.story_end_char_english
            );
            const hebrewText = getTextWithContext(
                story.fullHebrew,
                story.story_start_char_hebrew,
                story.story_end_char_hebrew
            );

            return `
                <div class="story-card" id="card-${storyId}">
                    <div class="story-header">
                        <div class="story-ref">${story.ref} - Story ${story.story_number}</div>
                        <div class="story-meta">
                            <span class="badge ${confClass}">${story.confidence}% confidence</span>
                            <span class="badge ${typeClass}">${story.story_type.replace('_', ' ')}</span>
                        </div>
                    </div>
                    <div class="story-content">
                        <div class="summary">${story.one_sentence_summary}</div>

                        <div class="text-container">
                            <div class="text-section">
                                <h3>English Translation
                                    <span class="char-info">chars ${story.story_start_char_english}-${story.story_end_char_english}</span>
                                </h3>
                                <div class="text-content">
                                    <span class="context-before">${englishText.before}</span><span class="story-highlight">${englishText.story}</span><span class="context-after">${englishText.after}</span>
                                </div>
                            </div>
                            <div class="text-section">
                                <h3>Hebrew/Aramaic Original
                                    <span class="char-info">chars ${story.story_start_char_hebrew}-${story.story_end_char_hebrew}</span>
                                </h3>
                                <div class="text-content hebrew">
                                    <span class="context-before">${hebrewText.before}</span><span class="story-highlight">${hebrewText.story}</span><span class="context-after">${hebrewText.after}</span>
                                </div>
                            </div>
                        </div>

                        <div class="reasoning">
                            <strong>AI Reasoning:</strong> ${story.reasoning || 'No reasoning provided'}
                        </div>

                        <div class="length-feedback">
                            <label>Story Boundaries:</label>
                            <button class="length-btn too-short ${fb.length === 'too_short' ? 'active' : ''}" onclick="setLength('${storyId}', 'too_short')">Too Short</button>
                            <button class="length-btn correct ${fb.length === 'correct' ? 'active' : ''}" onclick="setLength('${storyId}', 'correct')">Correct Length</button>
                            <button class="length-btn too-long ${fb.length === 'too_long' ? 'active' : ''}" onclick="setLength('${storyId}', 'too_long')">Too Long</button>
                        </div>
                    </div>

                    <div class="feedback-section">
                        <div class="feedback-row">
                            <button class="feedback-btn is-story ${fb.verdict === 'is_story' ? 'active' : ''}" onclick="setVerdict('${storyId}', 'is_story')">✓ Is a Story</button>
                            <button class="feedback-btn not-story ${fb.verdict === 'not_story' ? 'active' : ''}" onclick="setVerdict('${storyId}', 'not_story')">✗ Not a Story</button>
                            <div class="feedback-note">
                                <input type="text" placeholder="Optional notes..." value="${fb.note || ''}" onchange="setNote('${storyId}', this.value)">
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }

        // Filter and sort stories
        function getFilteredStories() {
            let stories = [...allStories];

            const pageFilter = document.getElementById('filterPage').value;
            const typeFilter = document.getElementById('filterType').value;
            const sortBy = document.getElementById('sortBy').value;

            if (pageFilter !== 'all') {
                stories = stories.filter(s => s.ref === pageFilter);
            }
            if (typeFilter !== 'all') {
                stories = stories.filter(s => s.story_type === typeFilter);
            }

            // Sort
            if (sortBy === 'page') {
                stories.sort((a, b) => {
                    const refCmp = sortPageRef(a.ref, b.ref);
                    return refCmp !== 0 ? refCmp : a.story_number - b.story_number;
                });
            } else if (sortBy === 'confidence') {
                stories.sort((a, b) => b.confidence - a.confidence);
            } else if (sortBy === 'type') {
                stories.sort((a, b) => a.story_type.localeCompare(b.story_type));
            }

            return stories;
        }

        // Render all story cards
        function renderStories() {
            const container = document.getElementById('storiesContainer');
            const stories = getFilteredStories();

            if (stories.length === 0) {
                container.innerHTML = '<div class="no-results">No stories match your filters</div>';
                return;
            }

            container.innerHTML = stories.map(renderStoryCard).join('');
        }

        // Feedback functions
        function setVerdict(storyId, verdict) {
            feedback[storyId] = feedback[storyId] || {};
            feedback[storyId].verdict = verdict;
            feedback[storyId].reviewer = document.getElementById('reviewerName').value;
            feedback[storyId].timestamp = new Date().toISOString();
            saveFeedback();
            renderStories();
            renderStats();
        }

        function setLength(storyId, length) {
            feedback[storyId] = feedback[storyId] || {};
            feedback[storyId].length = length;
            feedback[storyId].reviewer = document.getElementById('reviewerName').value;
            feedback[storyId].timestamp = new Date().toISOString();
            saveFeedback();
            renderStories();
        }

        function setNote(storyId, note) {
            feedback[storyId] = feedback[storyId] || {};
            feedback[storyId].note = note;
            feedback[storyId].reviewer = document.getElementById('reviewerName').value;
            saveFeedback();
        }

        function saveFeedback() {
            localStorage.setItem('talmud_story_feedback', JSON.stringify(feedback));
        }

        function exportFeedback() {
            const reviewer = document.getElementById('reviewerName').value || 'anonymous';
            const data = {
                reviewer: reviewer,
                exportDate: new Date().toISOString(),
                totalStories: allStories.length,
                reviewed: Object.keys(feedback).length,
                feedback: feedback
            };

            const blob = new Blob([JSON.stringify(data, null, 2)], {type: 'application/json'});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `story_feedback_${reviewer}_${new Date().toISOString().slice(0,10)}.json`;
            a.click();
        }

        function clearFeedback() {
            if (confirm('Clear all feedback? This cannot be undone.')) {
                feedback = {};
                localStorage.removeItem('talmud_story_feedback');
                renderStories();
                renderStats();
            }
        }

        // Event listeners
        document.getElementById('filterPage').addEventListener('change', renderStories);
        document.getElementById('filterType').addEventListener('change', renderStories);
        document.getElementById('sortBy').addEventListener('change', renderStories);

        // Initial render
        renderStats();
        renderStories();
    </script>
</body>
</html>
'''

# Write the HTML file
output_file = 'review_ui.html'
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(html_template)

print(f"Generated {output_file}")
print(f"Total pages: {len(data['pages'])}")
total_stories = sum(len(p['analysis'].get('stories', [])) for p in data['pages'])
print(f"Total stories: {total_stories}")
