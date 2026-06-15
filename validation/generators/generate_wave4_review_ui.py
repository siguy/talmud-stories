#!/usr/bin/env python3
"""
Generate Wave 4 review UI showing v10 (LLM) text spans alongside v9 (regex)
spans for direct comparison.

Per story the page shows:
  - The full Hebrew text with v10 trims applied (gray strikethrough on
    trimmed text, dark on kept text)
  - A toggle to show v9's regex trim for the same story (red strikethrough
    if v9 cut different bytes)
  - A category badge: recovered_text / new_trim / different_trim /
    identical_trim / both_full

Usage:
  python3 validation/generators/generate_wave4_review_ui.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

V9_DIR = ROOT / 'results' / 'v9' / 'wave3'
V10_DIR = ROOT / 'results' / 'v10' / 'wave4'
OUT_DIR = ROOT / 'validation' / 'ui'

TRACTATES = {
    'kiddushin': {
        'title': 'Kiddushin',
        'v9_files': ['kiddushin_v9.json'],
        'v10_files': ['kiddushin_v10.json'],
        'out': 'wave4_kiddushin_review.html',
    },
    'ketubot': {
        'title': 'Ketubot',
        'v9_files': ['ketubot_v9_2-60.json', 'ketubot_v9_61-112.json'],
        'v10_files': ['ketubot_v10_2-60.json', 'ketubot_v10_61-112.json'],
        'out': 'wave4_ketubot_review.html',
    },
}


def _story_key(ref: str, story: Dict) -> str:
    return f"{ref}_{story.get('start_segment')}-{story.get('end_segment')}"


def _categorize(v9_ts, v9_te, v10_ts, v10_te) -> str:
    v9_has = bool(v9_ts) or bool(v9_te)
    v10_has = bool(v10_ts) or bool(v10_te)
    if not v9_has and not v10_has:
        return 'both_full'
    if v9_has and not v10_has:
        return 'recovered_text'
    if not v9_has and v10_has:
        return 'new_trim'
    o = lambda s: s.get('char_offset') if s else None
    if o(v9_ts) == o(v10_ts) and o(v9_te) == o(v10_te):
        return 'identical_trim'
    return 'different_trim'


def build_data(v9_paths: List[Path], v10_paths: List[Path]) -> List[Dict]:
    # Load all v9 stories into index
    v9_index: Dict[str, Dict] = {}
    for p in v9_paths:
        with p.open() as f:
            data = json.load(f)
        for page in data['pages']:
            ref = page.get('ref', '')
            for s in page.get('stories', []):
                if s.get('classification') == 'NOT_A_STORY':
                    continue
                v9_index[_story_key(ref, s)] = s

    stories: List[Dict] = []
    for p in v10_paths:
        with p.open() as f:
            data = json.load(f)
        page_lookup = {pg['ref']: pg for pg in data['pages']}
        for page in data['pages']:
            ref = page.get('ref', '')
            for s in page.get('stories', []):
                if s.get('classification') == 'NOT_A_STORY':
                    continue
                key = _story_key(ref, s)
                v9_story = v9_index.get(key, {})
                v9_ts = v9_story.get('text_span_start')
                v9_te = v9_story.get('text_span_end')
                v10_ts = s.get('text_span_start')
                v10_te = s.get('text_span_end')
                cat = _categorize(v9_ts, v9_te, v10_ts, v10_te)

                item = {
                    'page_ref': ref,
                    'start_segment': s['start_segment'],
                    'end_segment': s['end_segment'],
                    'classification': s.get('classification', 'UNKNOWN'),
                    'one_sentence_summary': s.get('one_sentence_summary', ''),
                    'criteria': s.get('criteria', {}),
                    'page_segments': page.get('segments', []),
                    'v10_text_span_start': v10_ts,
                    'v10_text_span_end': v10_te,
                    'v10_text_span_source': s.get('text_span_source'),
                    'v9_text_span_start': v9_ts,
                    'v9_text_span_end': v9_te,
                    'category': cat,
                    'spans_pages': s.get('spans_pages'),
                    'key': key,
                }
                if s.get('spans_pages') and len(s['spans_pages']) >= 2:
                    p2 = page_lookup.get(s['spans_pages'][1])
                    if p2:
                        item['page2_segments'] = p2.get('segments', [])
                        item['start_segment_page2'] = s.get('start_segment_page2', 0)
                        item['end_segment_page2'] = s.get('end_segment_page2', 0)
                stories.append(item)
    return stories


def generate_html(tractate_title: str, stories: List[Dict]) -> str:
    n_total = len(stories)
    from collections import Counter
    cat_counts = Counter(s['category'] for s in stories)
    src_counts = Counter(s['v10_text_span_source'] for s in stories)

    data_json = json.dumps(stories, ensure_ascii=True).replace('</', '<\\/')

    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
<meta charset=\"UTF-8\">
<title>Wave 4 — {tractate_title} Story Review</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: #f4f6f8; color: #222; padding: 20px; line-height: 1.55; }}
  .container {{ max-width: 1200px; margin: 0 auto; }}
  .header {{ background: white; padding: 28px 30px; border-radius: 12px;
             box-shadow: 0 2px 8px rgba(0,0,0,0.06); margin-bottom: 24px; }}
  .header h1 {{ font-size: 26px; color: #2c3e50; margin-bottom: 8px; }}
  .header p {{ color: #6c7a89; }}
  .stats {{ display: flex; gap: 12px; margin-top: 16px; flex-wrap: wrap; }}
  .stat {{ background: #f0f3f6; padding: 8px 14px; border-radius: 6px; font-size: 13px; }}
  .stat strong {{ font-size: 16px; }}
  .controls {{ background: white; padding: 14px 20px; border-radius: 10px;
               margin-bottom: 18px; box-shadow: 0 1px 4px rgba(0,0,0,0.05);
               display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }}
  .controls button {{ padding: 6px 14px; border: 1px solid #d4dae0; border-radius: 6px;
                     background: white; cursor: pointer; font-size: 13px; }}
  .controls button.active {{ background: #2c7a7b; color: white; border-color: #2c7a7b; }}
  .controls .save-btn {{ background: #2c7a7b; color: white; border-color: #2c7a7b;
                       font-weight: 600; padding: 8px 18px; margin-left: auto; }}

  .story-card {{ background: white; border-radius: 10px; padding: 20px 22px;
                margin-bottom: 14px; box-shadow: 0 1px 4px rgba(0,0,0,0.06);
                border-left: 4px solid #bbb; }}
  .story-card.cls-YES {{ border-left-color: #2c7a7b; }}
  .story-card.cls-HIGH_CONFIDENCE {{ border-left-color: #3182ce; }}
  .story-card.cls-LOW_CONFIDENCE {{ border-left-color: #d69e2e; }}
  .story-card.reviewed {{ opacity: 0.55; }}
  .story-header {{ display: flex; align-items: center; gap: 10px;
                   flex-wrap: wrap; margin-bottom: 12px; }}
  .story-title {{ font-weight: 600; font-size: 15px; }}
  .badge {{ font-size: 11px; padding: 3px 8px; border-radius: 4px; font-weight: 600; }}
  .badge.cat-recovered_text {{ background: #c6f6d5; color: #22543d; }}
  .badge.cat-new_trim {{ background: #fed7aa; color: #7c2d12; }}
  .badge.cat-different_trim {{ background: #fef3c7; color: #78350f; }}
  .badge.cat-identical_trim {{ background: #e2e8f0; color: #475569; }}
  .badge.cat-both_full {{ background: #f1f5f9; color: #64748b; }}
  .badge.src-llm {{ background: #dbeafe; color: #1e3a8a; }}
  .badge.src-llm_kept_full {{ background: #ecfccb; color: #365314; }}
  .badge.src-skipped {{ background: #fee2e2; color: #7f1d1d; }}

  .text-block {{ background: #fafbfc; padding: 12px 14px; border-radius: 8px;
                 margin-top: 10px; border: 1px solid #e5e8ec; }}
  .text-block h4 {{ font-size: 12px; text-transform: uppercase; letter-spacing: 0.6px;
                   color: #6c7a89; margin-bottom: 8px; font-weight: 600; }}
  .segment {{ margin-bottom: 4px; padding-left: 36px; position: relative;
              font-size: 14px; }}
  .segment.hebrew {{ direction: rtl; font-size: 18px; font-family: 'SBL Hebrew', 'Times New Roman', serif;
                    padding-left: 0; padding-right: 36px; }}
  .segment.highlighted {{ background: #fffbe6; border-left: 3px solid #d4a017; padding-left: 12px; }}
  .segment.hebrew.highlighted {{ border-left: none; border-right: 3px solid #d4a017;
                                padding-right: 12px; padding-left: 0; }}
  .seg-num {{ position: absolute; left: 8px; color: #94a3b8; font-size: 12px;
              font-family: monospace; }}
  .segment.hebrew .seg-num {{ left: auto; right: 8px; }}
  .v10-trim {{ color: #c53030; text-decoration: line-through;
               text-decoration-color: #c53030; opacity: 0.55; }}
  .v10-kept {{ color: #1a202c; font-weight: 500; }}
  .v9-trim {{ background: rgba(252, 165, 165, 0.35); border-bottom: 1px dashed #c53030; }}
  .compare-toggle {{ font-size: 12px; color: #2c7a7b; cursor: pointer;
                    margin-top: 6px; display: inline-block; }}
  .v9-note {{ background: #fef3c7; padding: 6px 10px; margin-top: 6px;
              border-radius: 4px; font-size: 12px; color: #78350f; }}

  .review-row {{ display: flex; gap: 8px; margin-top: 14px; align-items: center; flex-wrap: wrap; }}
  .verdict-btn {{ padding: 6px 16px; border: 1px solid #d4dae0; border-radius: 6px;
                 background: white; cursor: pointer; font-size: 13px; }}
  .verdict-btn.correct.selected {{ background: #2c7a7b; color: white; border-color: #2c7a7b; }}
  .verdict-btn.incorrect.selected {{ background: #c53030; color: white; border-color: #c53030; }}
  .notes-input {{ flex: 1; min-width: 250px; padding: 6px 10px;
                 border: 1px solid #d4dae0; border-radius: 6px; font-size: 13px; }}
  .progress-bar {{ background: #e2e8f0; height: 6px; border-radius: 3px; margin-bottom: 18px; }}
  .progress-fill {{ background: #2c7a7b; height: 100%; border-radius: 3px; transition: width 0.3s; }}
  .hidden {{ display: none; }}
  textarea.export-box {{ width: 100%; height: 200px; font-family: monospace; font-size: 11px;
                      padding: 10px; border: 1px solid #d4dae0; border-radius: 6px; margin-top: 10px; }}
</style>
</head>
<body>
<div class=\"container\">
  <div class=\"header\">
    <h1>Wave 4 — {tractate_title} Story Review</h1>
    <p>v10 detector (LLM-emitted text spans, replacing v9 regex). Compare v10 trims (red strikethrough) with v9 regex trims (pink underline, click "Compare v9" to toggle).</p>
    <div class=\"stats\">
      <div class=\"stat\"><strong>{n_total}</strong> stories</div>
      <div class=\"stat\">recovered_text: <strong>{cat_counts.get('recovered_text', 0)}</strong></div>
      <div class=\"stat\">new_trim: <strong>{cat_counts.get('new_trim', 0)}</strong></div>
      <div class=\"stat\">different_trim: <strong>{cat_counts.get('different_trim', 0)}</strong></div>
      <div class=\"stat\">identical_trim: <strong>{cat_counts.get('identical_trim', 0)}</strong></div>
      <div class=\"stat\">both_full: <strong>{cat_counts.get('both_full', 0)}</strong></div>
    </div>
  </div>

  <div class=\"controls\">
    <strong style=\"font-size: 12px; color: #6c7a89;\">FILTER</strong>
    <button class=\"active\" onclick=\"setFilter('all', this)\">all</button>
    <button onclick=\"setFilter('recovered_text', this)\">recovered_text</button>
    <button onclick=\"setFilter('new_trim', this)\">new_trim</button>
    <button onclick=\"setFilter('different_trim', this)\">different_trim</button>
    <button onclick=\"setFilter('identical_trim', this)\">identical_trim</button>
    <button onclick=\"setFilter('both_full', this)\">both_full</button>
    <button class=\"save-btn\" onclick=\"saveResults()\">Save Review</button>
  </div>

  <div class=\"progress-bar\"><div class=\"progress-fill\" id=\"progressFill\" style=\"width: 0%;\"></div></div>

  <div id=\"storiesContainer\"></div>

  <div id=\"exportArea\" class=\"hidden\" style=\"background: white; padding: 20px; border-radius: 10px; margin-top: 20px;\">
    <h3>Review Export</h3>
    <textarea class=\"export-box\" id=\"exportData\" readonly></textarea>
    <button class=\"save-btn\" onclick=\"downloadJSON()\" style=\"margin-top: 10px;\">Download JSON</button>
  </div>
</div>
<script>
const STORIES = __STORIES_PLACEHOLDER__;
const verdicts = {{}};
let activeFilter = 'all';

function init() {{
  render();
}}

function setFilter(cat, btn) {{
  activeFilter = cat;
  document.querySelectorAll('.controls button').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');
  render();
}}

function render() {{
  const container = document.getElementById('storiesContainer');
  container.innerHTML = '';
  STORIES.forEach((story, idx) => {{
    if (activeFilter !== 'all' && story.category !== activeFilter) return;
    container.appendChild(buildCard(story, idx));
  }});
  updateProgress();
}}

function buildCard(story, idx) {{
  const card = document.createElement('div');
  card.className = `story-card cls-${{story.classification}}`;
  card.id = `card-${{idx}}`;
  const v = verdicts[story.key] || {{}};
  const correctSel = v.verdict === 'correct' ? 'selected' : '';
  const incorrectSel = v.verdict === 'incorrect' ? 'selected' : '';
  const notesVal = v.notes || '';

  card.innerHTML = `
    <div class=\"story-header\">
      <span class=\"story-title\">${{story.page_ref}} :: seg ${{story.start_segment}}-${{story.end_segment}}</span>
      <span class=\"badge cat-${{story.category}}\">${{story.category}}</span>
      <span class=\"badge src-${{story.v10_text_span_source}}\">v10: ${{story.v10_text_span_source}}</span>
      <span style=\"font-size: 12px; color: #94a3b8;\">${{story.classification}}</span>
    </div>
    ${{story.one_sentence_summary ? `<div style=\"font-size:13px;color:#475569;margin-bottom:8px;\">${{story.one_sentence_summary}}</div>` : ''}}
    ${{buildTextDisplay(story)}}
    <div class=\"review-row\">
      <button class=\"verdict-btn correct ${{correctSel}}\" onclick=\"setVerdict('${{story.key}}', 'correct', ${{idx}})\">Correct</button>
      <button class=\"verdict-btn incorrect ${{incorrectSel}}\" onclick=\"setVerdict('${{story.key}}', 'incorrect', ${{idx}})\">Incorrect</button>
      <input class=\"notes-input\" placeholder=\"Notes (boundary issues, what to trim/keep...)\" value=\"${{notesVal.replace(/\"/g, '&quot;')}}\" onchange=\"setNotes('${{story.key}}', this.value)\">
    </div>
  `;
  return card;
}}

function renderHebrew(seg, story, isPage2) {{
  let heb = seg.hebrew || '';
  const i = seg.index;
  let lo = 0, hi = heb.length;
  const v10ts = story.v10_text_span_start;
  const v10te = story.v10_text_span_end;
  if (v10ts && v10ts.segment === i && v10ts.char_offset > 0) lo = v10ts.char_offset;
  if (v10te && v10te.segment === i && v10te.char_offset > 0 && v10te.char_offset < heb.length) hi = v10te.char_offset;
  let html = '';
  if (lo > 0 || hi < heb.length) {{
    if (lo > 0) html += `<span class=\"v10-trim\" title=\"v10 trimmed (LLM)\">${{heb.slice(0, lo)}}</span>`;
    html += `<span class=\"v10-kept\">${{heb.slice(lo, hi)}}</span>`;
    if (hi < heb.length) html += `<span class=\"v10-trim\" title=\"v10 trimmed (LLM)\">${{heb.slice(hi)}}</span>`;
  }} else {{
    html += `<span class=\"v10-kept\">${{heb}}</span>`;
  }}
  // v9 comparison note
  const v9ts = story.v9_text_span_start;
  const v9te = story.v9_text_span_end;
  const v9Notes = [];
  if (v9ts && v9ts.segment === i) v9Notes.push(`v9 trimmed start @${{v9ts.char_offset}} (intro: ${{v9ts.introducer||'?'}})`);
  if (v9te && v9te.segment === i) v9Notes.push(`v9 trimmed end @${{v9te.char_offset}} (marker: ${{v9te.marker||'?'}})`);
  if (v9Notes.length) {{
    html += `<div class=\"v9-note\">${{v9Notes.join(' · ')}}</div>`;
  }}
  return html;
}}

function buildTextDisplay(story) {{
  const segs = story.page_segments || [];
  const start = story.start_segment;
  const end = story.end_segment;
  const showStart = Math.max(0, start - 2);
  const showEnd = Math.min(segs.length - 1, end + 2);

  let html = '<div class=\"text-block\"><h4>English</h4>';
  for (let i = showStart; i <= showEnd; i++) {{
    const seg = segs.find(s => s.index === i);
    if (!seg) continue;
    const hl = (i >= start && i <= end) ? 'highlighted' : '';
    const text = (seg.english || '').replace(/<[^>]+>/g, '');
    html += `<div class=\"segment ${{hl}}\"><span class=\"seg-num\">${{i}}</span>${{text}}</div>`;
  }}
  html += '</div>';

  html += '<div class=\"text-block\"><h4>Hebrew (v10 trims shown)</h4>';
  for (let i = showStart; i <= showEnd; i++) {{
    const seg = segs.find(s => s.index === i);
    if (!seg) continue;
    const hl = (i >= start && i <= end) ? 'highlighted' : '';
    let inner = (i >= start && i <= end) ? renderHebrew(seg, story, false) : (seg.hebrew || '');
    html += `<div class=\"segment hebrew ${{hl}}\"><span class=\"seg-num\">${{i}}</span>${{inner}}</div>`;
  }}
  html += '</div>';

  if (story.spans_pages && story.page2_segments) {{
    const p2 = story.page2_segments;
    const s2 = story.start_segment_page2 || 0;
    const e2 = story.end_segment_page2 || 0;
    html += `<div style=\"margin-top:14px; padding-top:10px; border-top:1px dashed #cbd5e1; font-size:12px; color:#64748b;\">Continues on ${{story.spans_pages[1]}}</div>`;
    html += '<div class=\"text-block\"><h4>English (continued)</h4>';
    p2.filter(s => s.index <= e2 + 1).forEach(seg => {{
      const hl = (seg.index >= s2 && seg.index <= e2) ? 'highlighted' : '';
      html += `<div class=\"segment ${{hl}}\"><span class=\"seg-num\">${{seg.index}}</span>${{(seg.english||'').replace(/<[^>]+>/g, '')}}</div>`;
    }});
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
    const sel = card.querySelector(`.verdict-btn.${{verdict}}`);
    if (sel) sel.classList.add('selected');
  }}
  updateProgress();
}}

function setNotes(key, notes) {{
  if (!verdicts[key]) verdicts[key] = {{}};
  verdicts[key].notes = notes;
}}

function updateProgress() {{
  const reviewed = Object.keys(verdicts).filter(k => verdicts[k].verdict).length;
  document.getElementById('progressFill').style.width = (reviewed / STORIES.length * 100) + '%';
}}

function saveResults() {{
  const results = {{
    tractate: '{tractate_title}',
    wave: 4,
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
      category: story.category,
      v10_source: story.v10_text_span_source,
      v10_text_span_start: story.v10_text_span_start,
      v10_text_span_end: story.v10_text_span_end,
      v9_text_span_start: story.v9_text_span_start,
      v9_text_span_end: story.v9_text_span_end,
      verdict: v.verdict || null,
      notes: v.notes || '',
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
  a.download = `wave4_{tractate_title.lower()}_review_${{new Date().toISOString().split('T')[0]}}.json`;
  a.click();
  URL.revokeObjectURL(url);
}}

init();
</script>
</body>
</html>""".replace('__STORIES_PLACEHOLDER__', data_json)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for slug, cfg in TRACTATES.items():
        v9_paths = [V9_DIR / n for n in cfg['v9_files']]
        v10_paths = [V10_DIR / n for n in cfg['v10_files']]
        missing = [p for p in v9_paths + v10_paths if not p.exists()]
        if missing:
            print(f"  SKIP {slug}: missing {[str(m.relative_to(ROOT)) for m in missing]}")
            continue
        stories = build_data(v9_paths, v10_paths)
        html = generate_html(cfg['title'], stories)
        out_path = OUT_DIR / cfg['out']
        out_path.write_text(html, encoding='utf-8')
        print(f"  {slug}: {len(stories)} stories → {out_path.relative_to(ROOT)}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
