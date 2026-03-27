#!/usr/bin/env python3
"""
Generate review UI for Kiddushin first-pass detection results.

All stories in one section. Jeff reviews each as Correct/Incorrect with notes.
Shows English + Hebrew text with story segments highlighted.

Usage:
  python3 validation/generators/generate_kiddushin_review_ui.py
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
RESULTS_PATH = PROJECT_ROOT / 'results' / 'kiddushin' / 'kiddushin_v7.json'
OUTPUT_PATH = PROJECT_ROOT / 'validation' / 'ui' / 'kiddushin_review.html'


def load_results():
    with open(RESULTS_PATH) as f:
        return json.load(f)


def build_stories_data(results):
    """Extract all stories with their page text for the UI."""
    pages = results['pages']
    page_lookup = {p['ref']: p for p in pages}
    stories = []

    for page in pages:
        for story in page.get('stories', []):
            if story.get('classification') == 'NOT_A_STORY':
                continue

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
                'continuation_check_extended': story.get('continuation_check_extended', False),
                'cross_page_stitched': story.get('cross_page_stitched', False),
                'key': f"{ref}_{story['start_segment']}-{story['end_segment']}",
            }

            # Add page2 segments for cross-page stories
            if story.get('spans_pages') and len(story['spans_pages']) >= 2:
                p2_ref = story['spans_pages'][1]
                p2 = page_lookup.get(p2_ref)
                if p2:
                    item['page2_segments'] = p2.get('segments', [])

            stories.append(item)

    return stories


def generate_html(stories_data):
    """Generate the review HTML."""
    # Use ensure_ascii=True to prevent Hebrew chars from breaking JS
    # Escape </ to prevent closing script tag
    data_json = json.dumps(stories_data, ensure_ascii=True)
    data_json = data_json.replace('</', '<\\/')

    # Build HTML with placeholder, then insert data
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Kiddushin Story Review</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; padding: 20px; line-height: 1.6; }}
.container {{ max-width: 1200px; margin: 0 auto; }}

.header {{ background: white; padding: 30px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 30px; }}
.header h1 {{ color: #2c3e50; margin-bottom: 10px; }}
.header p {{ color: #7f8c8d; }}
.stats {{ display: flex; gap: 20px; margin-top: 15px; flex-wrap: wrap; }}
.stat {{ background: #f8f9fa; padding: 10px 15px; border-radius: 8px; text-align: center; }}
.stat .num {{ font-size: 24px; font-weight: bold; }}
.stat .label {{ font-size: 12px; color: #7f8c8d; }}

.controls {{ background: white; padding: 15px 20px; border-radius: 8px; margin-bottom: 20px; display: flex; gap: 10px; align-items: center; flex-wrap: wrap; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }}
.controls button {{ padding: 6px 14px; border: 1px solid #ddd; border-radius: 6px; background: white; cursor: pointer; font-size: 13px; }}
.controls button:hover {{ background: #f0f0f0; }}
.controls button.active {{ background: #3498db; color: white; border-color: #3498db; }}
.controls .spacer {{ flex: 1; }}
.controls .save-btn {{ background: #27ae60; color: white; border-color: #27ae60; font-weight: 600; padding: 8px 20px; }}
.controls .save-btn:hover {{ background: #219a52; }}

.progress-bar {{ background: #e0e0e0; height: 6px; border-radius: 3px; margin-bottom: 20px; }}
.progress-fill {{ background: #27ae60; height: 100%; border-radius: 3px; transition: width 0.3s; }}

.story-card {{ background: white; border-radius: 10px; padding: 20px; margin-bottom: 15px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); border-left: 4px solid #bbb; }}
.story-card.cls-YES {{ border-left-color: #27ae60; }}
.story-card.cls-HIGH_CONFIDENCE {{ border-left-color: #3498db; }}
.story-card.cls-LOW_CONFIDENCE {{ border-left-color: #f39c12; }}
.story-card.reviewed {{ opacity: 0.7; }}

.story-header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; }}
.story-title {{ font-weight: 600; font-size: 15px; }}
.story-meta {{ display: flex; gap: 8px; align-items: center; }}
.badge {{ padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; }}
.badge-YES {{ background: #d5f5e3; color: #1e8449; }}
.badge-HIGH {{ background: #d6eaf8; color: #2471a3; }}
.badge-LOW {{ background: #fdebd0; color: #ca6f1e; }}
.badge-cross {{ background: #f5eef8; color: #7d3c98; }}
.badge-4f {{ background: #fce4ec; color: #c0392b; }}

.summary {{ color: #555; font-style: italic; margin-bottom: 12px; font-size: 14px; }}

.text-block {{ margin-bottom: 12px; }}
.text-block h4 {{ font-size: 13px; color: #7f8c8d; margin-bottom: 6px; }}
.segment {{ padding: 4px 8px; margin: 2px 0; border-radius: 4px; font-size: 13px; line-height: 1.5; }}
.segment.highlighted {{ background: #fffde7; border-left: 3px solid #f9a825; }}
.segment .seg-num {{ color: #999; font-size: 11px; margin-right: 6px; }}
.hebrew {{ direction: rtl; text-align: right; font-family: 'SBL Hebrew', 'Noto Serif Hebrew', 'Times New Roman', serif; font-size: 15px; line-height: 1.8; }}

.page2-divider {{ border-top: 2px dashed #9b59b6; margin: 12px 0; padding-top: 8px; }}
.page2-label {{ color: #9b59b6; font-weight: 600; font-size: 12px; margin-bottom: 6px; }}

.verdict-row {{ display: flex; gap: 10px; align-items: center; margin-top: 15px; padding-top: 15px; border-top: 1px solid #eee; }}
.verdict-btn {{ padding: 6px 16px; border-radius: 6px; border: 2px solid #ddd; background: white; cursor: pointer; font-weight: 600; font-size: 13px; }}
.verdict-btn:hover {{ filter: brightness(0.95); }}
.verdict-btn.correct {{ border-color: #27ae60; color: #27ae60; }}
.verdict-btn.correct.selected {{ background: #27ae60; color: white; }}
.verdict-btn.incorrect {{ border-color: #e74c3c; color: #e74c3c; }}
.verdict-btn.incorrect.selected {{ background: #e74c3c; color: white; }}
.notes-input {{ flex: 1; padding: 6px 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 13px; }}
.notes-input::placeholder {{ color: #bbb; }}

.hidden {{ display: none; }}

.export-area {{ background: white; padding: 20px; border-radius: 10px; margin-top: 20px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }}
.export-area textarea {{ width: 100%; height: 200px; font-family: monospace; font-size: 12px; padding: 10px; border: 1px solid #ddd; border-radius: 6px; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>Kiddushin Story Review</h1>
    <p>First-pass detection on Kiddushin 2a-82b. Review each detected story as Correct or Incorrect.</p>
    <p style="margin-top:8px; font-size:13px; color:#888;">For incorrect stories: note if it's a false positive (not a real story), boundary issue (starts/ends wrong), or merge issue (should be combined with adjacent story). Your notes help us improve the detector.</p>
    <div class="stats" id="stats"></div>
  </div>

  <div class="controls">
    <button onclick="filterBy('all')" class="active" data-filter="all">All</button>
    <button onclick="filterBy('YES')" data-filter="YES">YES</button>
    <button onclick="filterBy('HIGH_CONFIDENCE')" data-filter="HIGH_CONFIDENCE">HIGH</button>
    <button onclick="filterBy('LOW_CONFIDENCE')" data-filter="LOW_CONFIDENCE">LOW</button>
    <button onclick="filterBy('cross')" data-filter="cross">Cross-page</button>
    <button onclick="filterBy('unreviewed')" data-filter="unreviewed">Unreviewed</button>
    <span class="spacer"></span>
    <button class="save-btn" onclick="saveResults()">Save Results</button>
  </div>

  <div class="progress-bar"><div class="progress-fill" id="progressFill"></div></div>

  <div id="stories"></div>

  <div class="export-area hidden" id="exportArea">
    <h3>Review Results</h3>
    <p style="margin:8px 0; font-size:13px; color:#666;">Copy this JSON and send it back, or click "Download JSON" below.</p>
    <textarea id="exportData" readonly></textarea>
    <button onclick="downloadJSON()" style="margin-top:10px; padding:8px 20px; background:#3498db; color:white; border:none; border-radius:6px; cursor:pointer;">Download JSON</button>
  </div>
</div>

<script>
const STORIES = __STORIES_PLACEHOLDER__;

const verdicts = {{}};
let currentFilter = 'all';

function init() {{
  renderStats();
  renderStories();
  updateProgress();
}}

function renderStats() {{
  const counts = {{ YES: 0, HIGH_CONFIDENCE: 0, LOW_CONFIDENCE: 0, cross: 0 }};
  STORIES.forEach(s => {{
    counts[s.classification] = (counts[s.classification] || 0) + 1;
    if (s.spans_pages) counts.cross++;
  }});
  document.getElementById('stats').innerHTML = `
    <div class="stat"><div class="num">${{STORIES.length}}</div><div class="label">Total Stories</div></div>
    <div class="stat"><div class="num">${{counts.YES}}</div><div class="label">YES</div></div>
    <div class="stat"><div class="num">${{counts.HIGH_CONFIDENCE}}</div><div class="label">HIGH</div></div>
    <div class="stat"><div class="num">${{counts.LOW_CONFIDENCE}}</div><div class="label">LOW</div></div>
    <div class="stat"><div class="num">${{counts.cross}}</div><div class="label">Cross-page</div></div>
  `;
}}

function renderStories() {{
  const container = document.getElementById('stories');
  container.innerHTML = '';
  STORIES.forEach((story, idx) => {{
    if (!matchesFilter(story)) return;
    container.appendChild(createCard(story, idx));
  }});
}}

function matchesFilter(story) {{
  if (currentFilter === 'all') return true;
  if (currentFilter === 'cross') return !!story.spans_pages;
  if (currentFilter === 'unreviewed') return !verdicts[story.key];
  return story.classification === currentFilter;
}}

function filterBy(f) {{
  currentFilter = f;
  document.querySelectorAll('.controls button[data-filter]').forEach(b => {{
    b.classList.toggle('active', b.dataset.filter === f);
  }});
  renderStories();
}}

function createCard(story, idx) {{
  const card = document.createElement('div');
  card.className = `story-card cls-${{story.classification}} ${{verdicts[story.key] ? 'reviewed' : ''}}`;
  card.id = `card-${{idx}}`;

  const clsBadge = story.classification === 'YES' ? 'badge-YES' :
                   story.classification === 'HIGH_CONFIDENCE' ? 'badge-HIGH' : 'badge-LOW';

  let crossBadge = '';
  if (story.spans_pages) {{
    const method = story.continuation_check_extended ? '4f' : story.cross_page_stitched ? 'stitch' : 'merge';
    crossBadge = `<span class="badge badge-cross">Cross-page (${{method}})</span>`;
  }}

  // Build text display
  const textHtml = buildTextDisplay(story);

  const v = verdicts[story.key] || {{}};
  const correctSel = v.verdict === 'correct' ? 'selected' : '';
  const incorrectSel = v.verdict === 'incorrect' ? 'selected' : '';
  const notesVal = v.notes || '';

  card.innerHTML = `
    <div class="story-header">
      <span class="story-title">#${{idx+1}} ${{story.page_ref}} (segs ${{story.start_segment}}-${{story.end_segment}})</span>
      <div class="story-meta">
        <span class="badge ${{clsBadge}}">${{story.classification}}</span>
        ${{crossBadge}}
      </div>
    </div>
    <div class="summary">${{story.one_sentence_summary}}</div>
    ${{textHtml}}
    <div class="verdict-row">
      <button class="verdict-btn correct ${{correctSel}}" onclick="setVerdict('${{story.key}}', 'correct', ${{idx}})">Correct</button>
      <button class="verdict-btn incorrect ${{incorrectSel}}" onclick="setVerdict('${{story.key}}', 'incorrect', ${{idx}})">Incorrect</button>
      <input class="notes-input" placeholder="Notes (boundary issues, merge issues, classification...)"
             value="${{notesVal.replace(/"/g, '&quot;')}}"
             onchange="setNotes('${{story.key}}', this.value)">
    </div>
  `;
  return card;
}}

function buildTextDisplay(story) {{
  let html = '<div class="text-block"><h4>English</h4>';
  const segs = story.page_segments || [];
  const start = story.start_segment;
  const end = story.end_segment;

  // Show segments around the story (2 before, all story, 2 after)
  const showStart = Math.max(0, start - 2);
  const showEnd = Math.min(segs.length - 1, end + 2);

  for (let i = showStart; i <= showEnd; i++) {{
    const seg = segs.find(s => s.index === i);
    if (!seg) continue;
    const hl = (i >= start && i <= end) ? 'highlighted' : '';
    const text = seg.english.replace(/<[^>]+>/g, '');
    html += `<div class="segment ${{hl}}"><span class="seg-num">${{i}}</span>${{text}}</div>`;
  }}
  html += '</div>';

  // Hebrew
  html += '<div class="text-block"><h4>Hebrew</h4>';
  for (let i = showStart; i <= showEnd; i++) {{
    const seg = segs.find(s => s.index === i);
    if (!seg) continue;
    const hl = (i >= start && i <= end) ? 'highlighted' : '';
    html += `<div class="segment hebrew ${{hl}}"><span class="seg-num">${{i}}</span>${{seg.hebrew}}</div>`;
  }}
  html += '</div>';

  // Page 2 for cross-page stories
  if (story.spans_pages && story.page2_segments) {{
    const p2Segs = story.page2_segments;
    const s2 = story.start_segment_page2 || 0;
    const e2 = story.end_segment_page2 || 0;
    const showEnd2 = Math.min(p2Segs.length - 1, e2 + 2);

    html += `<div class="page2-divider"></div>`;
    html += `<div class="page2-label">Continues on ${{story.spans_pages[1]}}</div>`;

    html += '<div class="text-block"><h4>English (continued)</h4>';
    for (let i = 0; i <= showEnd2; i++) {{
      const seg = p2Segs.find(s => s.index === i);
      if (!seg) continue;
      const hl = (i >= s2 && i <= e2) ? 'highlighted' : '';
      const text = seg.english.replace(/<[^>]+>/g, '');
      html += `<div class="segment ${{hl}}"><span class="seg-num">${{i}}</span>${{text}}</div>`;
    }}
    html += '</div>';

    html += '<div class="text-block"><h4>Hebrew (continued)</h4>';
    for (let i = 0; i <= showEnd2; i++) {{
      const seg = p2Segs.find(s => s.index === i);
      if (!seg) continue;
      const hl = (i >= s2 && i <= e2) ? 'highlighted' : '';
      html += `<div class="segment hebrew ${{hl}}"><span class="seg-num">${{i}}</span>${{seg.hebrew}}</div>`;
    }}
    html += '</div>';
  }}

  return html;
}}

function setVerdict(key, verdict, idx) {{
  if (!verdicts[key]) verdicts[key] = {{}};
  verdicts[key].verdict = verdict;
  const card = document.getElementById(`card-${{idx}}`);
  if (card) {{
    card.classList.add('reviewed');
    card.querySelectorAll('.verdict-btn').forEach(b => b.classList.remove('selected'));
    card.querySelector(`.verdict-btn.${{verdict}}`).classList.add('selected');
  }}
  updateProgress();
}}

function setNotes(key, notes) {{
  if (!verdicts[key]) verdicts[key] = {{}};
  verdicts[key].notes = notes;
}}

function updateProgress() {{
  const reviewed = Object.keys(verdicts).filter(k => verdicts[k].verdict).length;
  const pct = (reviewed / STORIES.length * 100);
  document.getElementById('progressFill').style.width = pct + '%';
}}

function saveResults() {{
  const results = {{
    tractate: 'Kiddushin',
    date: new Date().toISOString().split('T')[0],
    total_stories: STORIES.length,
    reviewed: Object.keys(verdicts).filter(k => verdicts[k].verdict).length,
    reviews: {{}}
  }};

  STORIES.forEach((story, idx) => {{
    const v = verdicts[story.key] || {{}};
    results.reviews[story.key] = {{
      index: idx + 1,
      page_ref: story.page_ref,
      classification: story.classification,
      summary: story.one_sentence_summary,
      verdict: v.verdict || null,
      notes: v.notes || '',
      spans_pages: story.spans_pages || null,
    }};
  }});

  const json = JSON.stringify(results, null, 2);
  document.getElementById('exportData').value = json;
  document.getElementById('exportArea').classList.remove('hidden');
  document.getElementById('exportArea').scrollIntoView({{ behavior: 'smooth' }});
}}

function downloadJSON() {{
  const data = document.getElementById('exportData').value;
  const blob = new Blob([data], {{ type: 'application/json' }});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `kiddushin_review_${{new Date().toISOString().split('T')[0]}}.json`;
  a.click();
  URL.revokeObjectURL(url);
}}

init();
</script>
</body>
</html>'''

    # Insert the JSON data safely (not through f-string to avoid escaping issues)
    html = html.replace('__STORIES_PLACEHOLDER__', data_json)
    return html


def main():
    print("Loading Kiddushin results...")
    results = load_results()

    print("Building story data...")
    stories = build_stories_data(results)
    print(f"  {len(stories)} stories for review")

    print("Generating HTML...")
    html = generate_html(stories)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, 'w') as f:
        f.write(html)
    print(f"  Saved to {OUTPUT_PATH}")


if __name__ == '__main__':
    main()
