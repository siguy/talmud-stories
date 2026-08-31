#!/usr/bin/env python3
"""
Generate the Wave 4 story review UI.

DISPLAY SYMMETRY (fixed 2026-08-30, work/2026-08-30-review-verdict-axes.md)
--------------------------------------------------
Every segment is rendered as ONE row holding BOTH languages, so the English
and the Hebrew always show the same extent. Nothing is hidden, faded or struck
through in either language; the story is HIGHLIGHTED inside the full text
rather than trimmed to.

This replaces two asymmetries that made the display manufacture its own errors:

  1. The Hebrew was cut at the detector's char-offsets (struck through and
     faded) while the English was shown in full. A reviewer saw a Hebrew
     passage stopping early beside an English one that did not.
     -> caused Jeff's "English right, Hebrew doesn't match" (Kiddushin 9a seg 2)
  2. Cross-page stories got an "English (continued)" block with no Hebrew
     counterpart, so the Hebrew appeared to stop at the page break.
     -> caused Jeff's "English right but Hebrew cut off; continues to seg 0 of
        the next page" (Kiddushin 8b seg 14). 35 stories were affected.

The detector's proposed narrower Hebrew span is still shown, but as a labelled
ANNOTATION (shaded, with a note saying it is Hebrew-only and that nothing is
trimmed), never as a cut. Offsets that sever a Hebrew word are flagged as such
using the same test as scripts/audit_text_spans.py.

This is a display change only. It does not alter detector output.

Per story the page shows:
  - Paired English/Hebrew rows over the story plus two segments of context
  - Any v10 proposed span as a shaded annotation on the Hebrew, explained
  - The v9 regex span as text, for reference
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

from validation.generators._review_display import DISPLAY_CSS, DISPLAY_JS  # noqa: E402

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
__DISPLAY_CSS__
  .v9-note {{ background: #f7fafc; border: 1px solid #e2e8f0; padding: 6px 10px;
              margin-top: 6px; border-radius: 4px; font-size: 12px; color: #4a5568; }}
  .cont-head {{ margin-top: 14px; padding-top: 10px; border-top: 1px dashed #cbd5e1;
                font-size: 12px; color: #64748b; }}
  .legend {{ font-size: 12px; color: #6c7a89; margin-top: 14px; line-height: 1.6; }}
  .legend .sw {{ display: inline-block; width: 12px; height: 12px; vertical-align: -2px;
                 border-radius: 3px; margin-right: 4px; }}

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
    <p>English and Hebrew are shown side by side, one row per segment, so the two always cover the <b>same extent</b>. Nothing is cut in either language &mdash; the story is highlighted inside the full text.</p>
    <div class=\"legend\">
      <span class=\"sw\" style=\"background:#fffbe6;border:1px solid #d4a017;\"></span> the story &nbsp;·&nbsp;
      <span class=\"sw\" style=\"background:#fbfcfd;border:1px solid #dde3e9;\"></span> surrounding context (2 segments either side) &nbsp;·&nbsp;
      <span class=\"sw\" style=\"background:#fde68a;box-shadow:inset 0 -2px 0 #d97706;\"></span> the detector's proposed narrower <b>Hebrew</b> span &mdash; an annotation with no English counterpart, not a cut<br>
      Cross-page stories continue in <b>both</b> languages below the dashed rule.
    </div>
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

__DISPLAY_JS__

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
</html>""".replace('__DISPLAY_CSS__', DISPLAY_CSS)\
     .replace('__DISPLAY_JS__', DISPLAY_JS)\
     .replace('__STORIES_PLACEHOLDER__', data_json)


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
