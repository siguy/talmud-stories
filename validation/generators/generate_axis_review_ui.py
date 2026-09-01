#!/usr/bin/env python3
"""The per-axis review UI — make the reviewer say WHICH thing is wrong.

Phase B of `work/2026-08-30-review-verdict-axes.md`.

THE PROBLEM
-----------
The old UI recorded THAT an entry was rejected and never WHAT was being
rejected. One `incorrect` button pooled four capabilities, so Classification
could only ever be quoted as a range (Ketubot 87.9-94.8%, Kiddushin
67.4-92.1%) and the pooled figure sent the fix to the wrong place: most of
those errors were in the boundary code, not the classifier (Lesson 30).

THE AXES, read off the taxonomy the ruler already computes -- not invented
-----------------------------------------------------------------------
  1. Is it a story?   Yes / Borderline / No      <- required, and the ONLY
                                                    required question
  2. Extent           right / starts / ends / both
  3. Confidence       right / too high / too low
  4. Grouping         right / split / merge with neighbour

`Borderline` is Jeff's own request (2026-07-06 ledger, Part 2(d)) and is a
column the published database needs anyway (capability 6).

THE THROUGHPUT CONSTRAINT, and how the layout meets it
------------------------------------------------------
**A correct entry stays ONE CLICK.** Review is the bottleneck -- 2-6 weeks of
one scholar's calendar against ~$0.30 of compute -- and his last two rounds
returned 1 verdict and 15. So axes 2-4 do not exist on screen until the
reviewer opens them, and the disclosure is DELIBERATELY INDEPENDENT of axis 1:
a passage can be a story AND be mis-bounded. That is the common case (`adjust`
already meant exactly this), so gating the extent axis behind a `No` would
throw away the corrections that matter most.

`display_problem` is a first-class outcome, not a note (Lesson 25). 3 of Jeff's
verdicts across two rounds were spent telling us our renderer was broken; those
must never land in a precision figure again.

Every exported verdict carries the DETECTOR VERSION it judged (Lesson 36): a
round's precision is a property of the version reviewed, and of 8 notes where
the detector disagreed at review time, today it agrees with 7.

The text display is imported from `review_ui_core.py` -- the same code the
wave 4 page uses, guarded by `tests/test_review_ui_symmetry.py`. This page
therefore cannot show Hebrew and English at different extents unless that test
also fails.

Reads `results/v10/wave4_notrim/` -- the honest segment-level output. The
reverted char-offset spans of `results/v10/wave4/` are not shown at all.

Usage:  python3 validation/generators/generate_axis_review_ui.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from review_ui_core import DISPLAY_CSS, DISPLAY_JS  # noqa: E402

RUN_DIR = ROOT / 'results' / 'v10' / 'wave4_notrim'
OUT_DIR = ROOT / 'validation' / 'ui'

SCHEMA_VERSION = 'axes-2'

TRACTATES = {
    'kiddushin': dict(title='Kiddushin', files=['kiddushin_v10_notrim.json'],
                      out='axis_kiddushin_review.html'),
    'ketubot': dict(title='Ketubot',
                    files=['ketubot_v10_2-60_notrim.json',
                           'ketubot_v10_61-112_notrim.json'],
                    out='axis_ketubot_review.html'),
}


def build_data(paths: List[Path]) -> tuple[List[Dict], str]:
    """Stories for review, plus the detector version they came from.

    `mishnah_stories` is INCLUDED, badged, and filterable. CLAUDE.md requires
    any code reading a run for display to decide about that key explicitly:
    stage 4g withholds those passages from `stories[]`, no harness or UI has
    ever read them, and Jeff is the one person who can settle whether they
    belong in the database at all (`jeff:mishnah-scope`). Showing them costs
    him nothing extra and answers an open question.
    """
    stories: List[Dict] = []
    versions = set()
    for p in paths:
        data = json.loads(p.read_text())
        versions.add(data.get('version', 'unknown'))
        page_lookup = {pg['ref']: pg for pg in data['pages']}
        for page in data['pages']:
            ref = page.get('ref', '')
            for withheld, group in ((False, page.get('stories') or []),
                                    (True, page.get('mishnah_stories') or [])):
                for s in group:
                    if s.get('classification') == 'NOT_A_STORY':
                        continue
                    item = {
                        'key': f"{ref}_{s.get('start_segment')}-{s.get('end_segment')}",
                        'page_ref': ref,
                        'start_segment': s['start_segment'],
                        'end_segment': s['end_segment'],
                        'classification': s.get('classification', 'UNKNOWN'),
                        'one_sentence_summary': s.get('one_sentence_summary', ''),
                        'page_segments': page.get('segments', []),
                        'mishnah_withheld': withheld,
                        'spans_pages': s.get('spans_pages'),
                    }
                    if s.get('spans_pages') and len(s['spans_pages']) >= 2:
                        p2 = page_lookup.get(s['spans_pages'][1])
                        if p2:
                            item['page2_segments'] = p2.get('segments', [])
                            item['start_segment_page2'] = s.get('start_segment_page2', 0)
                            item['end_segment_page2'] = s.get('end_segment_page2', 0)
                    stories.append(item)
    return stories, '+'.join(sorted(versions))


PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>__TITLE__ — Story Review</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: #f4f6f8; color: #222; padding: 20px; line-height: 1.55; }
  .container { max-width: 1200px; margin: 0 auto; }
  .header { background: white; padding: 28px 30px; border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06); margin-bottom: 24px; }
  .header h1 { font-size: 26px; color: #2c3e50; margin-bottom: 8px; }
  .header p { color: #48606f; margin-top: 6px; }
  .howto { background: #f0f7f7; border: 1px solid #cfe3e3; border-radius: 8px;
           padding: 12px 16px; margin-top: 14px; font-size: 13.5px; color: #23484a; }
  .howto b { color: #14494b; }
  .stats { display: flex; gap: 12px; margin-top: 16px; flex-wrap: wrap; }
  .stat { background: #f0f3f6; padding: 8px 14px; border-radius: 6px; font-size: 13px; }
  .stat strong { font-size: 16px; }
  .controls { background: white; padding: 14px 20px; border-radius: 10px;
              margin-bottom: 18px; box-shadow: 0 1px 4px rgba(0,0,0,0.05);
              display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
  .controls button { padding: 6px 14px; border: 1px solid #d4dae0; border-radius: 6px;
                     background: white; cursor: pointer; font-size: 13px; }
  .controls button.active { background: #2c7a7b; color: white; border-color: #2c7a7b; }
  .controls .save-btn { background: #2c7a7b; color: white; border-color: #2c7a7b;
                        font-weight: 600; padding: 8px 18px; margin-left: auto; }

  .story-card { background: white; border-radius: 10px; padding: 20px 22px;
                margin-bottom: 14px; box-shadow: 0 1px 4px rgba(0,0,0,0.06);
                border-left: 4px solid #bbb; }
  .story-card.cls-YES { border-left-color: #2c7a7b; }
  .story-card.cls-HIGH_CONFIDENCE { border-left-color: #3182ce; }
  .story-card.cls-LOW_CONFIDENCE { border-left-color: #d69e2e; }
  .story-card.reviewed { opacity: 0.6; }
  .story-header { display: flex; align-items: center; gap: 10px;
                  flex-wrap: wrap; margin-bottom: 12px; }
  .story-title { font-weight: 600; font-size: 15px; }
  .badge { font-size: 11px; padding: 3px 8px; border-radius: 4px; font-weight: 600; }
  .badge.mishnah { background: #ede9fe; color: #4c1d95; }
  .badge.cross { background: #dbeafe; color: #1e3a8a; }

__DISPLAY_CSS__

  /* -------------------------------------------------------------------
     THE AXES.  Axis 1 is always present and is the only required answer;
     one click on it is a complete verdict.  Axes 2-4 live inside
     .more-axes, which is display:none until the reviewer opens it, and
     the opener is INDEPENDENT of axis 1 -- a passage can be a story and
     still be mis-bounded, which is the commonest correction there is.
     ------------------------------------------------------------------- */
  .axis-row { display: flex; gap: 8px; margin-top: 14px; align-items: center;
              flex-wrap: wrap; padding-top: 12px; border-top: 1px solid #eef1f4; }
  .axis-label { font-size: 12px; font-weight: 700; color: #48606f;
                text-transform: uppercase; letter-spacing: 0.5px; margin-right: 4px; }
  .axis-btn { padding: 6px 16px; border: 1px solid #d4dae0; border-radius: 6px;
              background: white; cursor: pointer; font-size: 13px; }
  .axis-btn:hover { background: #f5f7f9; }
  .axis-btn.selected { font-weight: 600; }
  .axis-btn.v-yes.selected { background: #2c7a7b; color: white; border-color: #2c7a7b; }
  .axis-btn.v-borderline.selected { background: #b7791f; color: white; border-color: #b7791f; }
  .axis-btn.v-no.selected { background: #c53030; color: white; border-color: #c53030; }
  .axis-btn.plain.selected { background: #4a5568; color: white; border-color: #4a5568; }
  .disclose { margin-left: auto; background: #f7fafc; color: #48606f;
              border: 1px dashed #cbd5e1 !important; }
  .disclose.open { background: #edf2f7; border-style: solid !important; }
  .flag-btn { border-color: #e2b1b1 !important; color: #9b2c2c; }
  .flag-btn.selected { background: #9b2c2c; color: white; border-color: #9b2c2c !important; }
  .more-axes { display: none; margin-top: 10px; padding: 12px 14px;
               background: #fafbfc; border: 1px solid #e5e8ec; border-radius: 8px; }
  .more-axes.open { display: block; }
  .more-axes .axis-row { border-top: none; padding-top: 0; margin-top: 8px; }
  .more-axes .axis-row:first-child { margin-top: 0; }
  /* The quote box. Appears only once the extent is said to be WRONG, so it
     costs nothing on the common path. `quote_polarity` is two buttons rather
     than a sentence because inferring it from prose is what leaves 16 of our
     70 boundary targets `mixed` or `unclear`. */
  .quote-box { display: none; margin-top: 10px; padding: 10px 12px;
               background: #fffbe6; border: 1px solid #f0d98c; border-radius: 6px; }
  .quote-box.open { display: block; }
  .quote-box .hint { font-size: 12.5px; color: #6b5a13; margin-bottom: 8px; }
  .quote-he { width: 100%; min-height: 58px; padding: 8px 10px; direction: rtl;
              text-align: right; font-size: 17px; line-height: 1.7;
              font-family: 'SBL Hebrew', 'Times New Roman', serif;
              border: 1px solid #e0cf8a; border-radius: 5px; background: white; }
  .quote-row { margin-bottom: 10px; }
  .quote-row .hint b { color: #6b4e00; }
  .quote-actions { display: flex; gap: 8px; margin-top: 8px; align-items: center; flex-wrap: wrap; }
  .grab-btn { background: #fff; border: 1px dashed #c9a227 !important; color: #7a5c05; }
  .notes-input { width: 100%; margin-top: 10px; padding: 7px 10px;
                 border: 1px solid #d4dae0; border-radius: 6px; font-size: 13px; }
  .progress-bar { background: #e2e8f0; height: 6px; border-radius: 3px; margin-bottom: 18px; }
  .progress-fill { background: #2c7a7b; height: 100%; border-radius: 3px; transition: width 0.3s; }
  .hidden { display: none; }
  textarea.export-box { width: 100%; height: 200px; font-family: monospace; font-size: 11px;
                        padding: 10px; border: 1px solid #d4dae0; border-radius: 6px; margin-top: 10px; }
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>__TITLE__ — Story Review</h1>
    __NOTE__
    <p>Hebrew and English are shown side by side, one row per segment, so the two always cover the <b>same extent</b>. Nothing is cut in either language — the story is highlighted inside the full text.</p>
    <div class="howto">
      <b>If an entry is right, click <span style="color:#2c7a7b">Yes</span> and move on — that is the whole review for it.</b><br>
      If something is off, use <b>“Something else is wrong”</b> to say <i>what</i>: the extent, the confidence level, or whether it should be split or merged. A passage can be a story <i>and</i> have the wrong extent — those are separate questions on purpose, because we have been unable to tell them apart and it has sent us fixing the wrong things.<br>
      If the <b>extent</b> is wrong, a box opens for the Hebrew: <b>highlight the words in the text above and press “Use highlighted text”</b> — no need to type them. There are two boxes, <b>where the story should start</b> and <b>where it should end</b>; fill either or both. Below them you can instead point at one passage and say whether it <i>belongs in the story</i> or <i>should be cut</i>.<br>
      If the <b>page itself</b> is broken — text missing, Hebrew not matching — click <b>⚠ Display problem</b>. That is our bug, not a judgement about the passage.
    </div>
    <div class="stats">
      <div class="stat"><strong>__N_TOTAL__</strong> entries</div>
      <div class="stat">detector: <strong>__DETECTOR_VERSION__</strong></div>
      <div class="stat">cross-page: <strong>__N_CROSS__</strong></div>
      <div class="stat">withheld from Mishnah: <strong>__N_MISHNAH__</strong></div>
    </div>
  </div>

  <div class="controls">
    <strong style="font-size: 12px; color: #6c7a89;">FILTER</strong>
    <button class="active" onclick="setFilter('all', this)">all</button>
    <button onclick="setFilter('unreviewed', this)">unreviewed</button>
    <button onclick="setFilter('cross', this)">cross-page</button>
    <button onclick="setFilter('mishnah', this)">in a Mishnah</button>
    <button class="save-btn" onclick="saveResults()">Save Review</button>
  </div>

  <div class="progress-bar"><div class="progress-fill" id="progressFill" style="width: 0%;"></div></div>

  <div id="storiesContainer"></div>

  <div id="exportArea" class="hidden" style="background: white; padding: 20px; border-radius: 10px; margin-top: 20px;">
    <h3>Review Export</h3>
    <textarea class="export-box" id="exportData" readonly></textarea>
    <button class="save-btn" onclick="downloadJSON()" style="margin-top: 10px;">Download JSON</button>
  </div>
</div>
<script>
const STORIES = __STORIES__;
const TRACTATE = "__TITLE__";
const DETECTOR_VERSION = "__DETECTOR_VERSION__";
const SCHEMA_VERSION = "__SCHEMA_VERSION__";
const HEBREW_FIRST = true;   // the Hebrew is the text; the English translates it
const verdicts = {};
let activeFilter = 'all';

__DISPLAY_JS__

// ---------------------------------------------------------------------------
// THE AXES
//
// Axis 1 alone completes a verdict: `isComplete` deliberately asks only about
// is_story, so a correct entry is one click.  Axes 2-4 default to null, which
// means "this round could not express it" -- distinct from "the reviewer said
// it was right".  That distinction is the whole point of the exercise; a null
// must never be exported as a `right`.
// ---------------------------------------------------------------------------
const AXES = {
  extent: ['right', 'starts_wrong', 'ends_wrong', 'both_wrong'],
  confidence: ['right', 'too_high', 'too_low'],
  grouping: ['right', 'split', 'merge']
};
const AXIS_LABELS = {
  extent: { right: 'Right', starts_wrong: 'Starts wrong', ends_wrong: 'Ends wrong', both_wrong: 'Both ends wrong' },
  confidence: { right: 'Right', too_high: 'Too high', too_low: 'Too low' },
  grouping: { right: 'Right', split: 'Should be split', merge: 'Merge with neighbour' }
};

// The shared core builds the text; this page passes NO span hook, because
// wave4_notrim carries segment-level boundaries only. The reverted char-offset
// spans are not shown here at all -- 55% of them cut mid-word.
function buildTextDisplay(story) {
  return buildGrid(story.page_segments || [], story.start_segment, story.end_segment, story, null)
       + buildContinuation(story);
}

function isComplete(v) { return !!(v && v.is_story); }

// 'right' is an answer, not a complaint: the quote box is for a wrong extent.
function isExtentWrong(extent) { return !!extent && extent !== 'right'; }

function init() { render(); }

function setFilter(f, btn) {
  activeFilter = f;
  document.querySelectorAll('.controls button').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');
  render();
}

function passesFilter(story) {
  if (activeFilter === 'all') return true;
  if (activeFilter === 'unreviewed') return !isComplete(verdicts[story.key]);
  if (activeFilter === 'cross') return !!story.spans_pages;
  if (activeFilter === 'mishnah') return !!story.mishnah_withheld;
  return true;
}

function render() {
  const container = document.getElementById('storiesContainer');
  container.innerHTML = '';
  STORIES.forEach((story, idx) => {
    if (!passesFilter(story)) return;
    container.appendChild(buildCard(story, idx));
  });
  updateProgress();
}

function axisButtons(key, idx, axis) {
  const v = verdicts[key] || {};
  return AXES[axis].map(val =>
    '<button class="axis-btn plain ' + (v[axis] === val ? 'selected' : '') + '"'
    + ' data-axis="' + axis + '" data-value="' + val + '"'
    + ' onclick="setAxis(\'' + key + '\', \'' + axis + '\', \'' + val + '\', ' + idx + ')">'
    + AXIS_LABELS[axis][val] + '</button>').join('');
}

// Where the story actually starts or ends, in his words rather than ours.
// Every Hebrew quote we hold was typed into a generic notes box and mined out
// with a regex afterwards; 16 of the 70 boundary targets built that way have a
// polarity we could not determine. Here he states it.
function quoteBox(key, idx) {
  const v = verdicts[key] || {};
  const open = isExtentWrong(v.extent) ? ' open' : '';
  const pol = p => v.quote_polarity === p ? 'selected' : '';
  const g = (field, label, ph) =>
        '<div class="quote-row" data-role="row-' + field + '">'
    +     '<div class="hint"><b>' + label + '</b></div>'
    +     '<textarea class="quote-he" data-role="' + field + '-text" placeholder="' + ph + '"'
    +       ' oninput="setField(\'' + key + '\', \'' + field + '\', this.value)">'
    +       esc(v[field] || '') + '</textarea>'
    +     '<div class="quote-actions">'
    +       '<button class="axis-btn grab-btn" data-role="grab-' + field + '"'
    +         ' onclick="grabInto(\'' + key + '\', \'' + field + '\', ' + idx + ')">'
    +         'Use highlighted text</button>'
    +     '</div>'
    +   '</div>';
  return '<div class="quote-box' + open + '" data-role="quote">'
    +   '<div class="hint">Give the story\'s real boundaries: highlight the Hebrew above and press '
    +     '<b>Use highlighted text</b>. Fill only the end that is wrong — both boxes are optional, '
    +     'and either one alone is a complete answer.</div>'
    +   g('quote_start', 'The story should START with these words',
        '\u05d4\u05d3\u05d1\u05e7 \u05d0\u05ea \u05ea\u05d7\u05d9\u05dc\u05ea \u05d4\u05e1\u05d9\u05e4\u05d5\u05e8')
    +   g('quote_end', 'The story should END with these words',
        '\u05d4\u05d3\u05d1\u05e7 \u05d0\u05ea \u05e1\u05d5\u05e3 \u05d4\u05e1\u05d9\u05e4\u05d5\u05e8')
    +   '<div class="hint" style="margin-top:12px;">Or point at one passage and say which way it goes:</div>'
    +   '<textarea class="quote-he" data-role="quote-text" placeholder="\u05d4\u05d3\u05d1\u05e7 \u05d0\u05ea \u05d4\u05d8\u05e7\u05e1\u05d8 \u05db\u05d0\u05df"'
    +     ' oninput="setQuote(\'' + key + '\', this.value)">' + esc(v.quote || '') + '</textarea>'
    +   '<div class="quote-actions">'
    +     '<button class="axis-btn grab-btn" data-role="grab" onclick="grabSelection(\'' + key + '\', ' + idx + ')">Use highlighted text</button>'
    +     '<span class="axis-label" style="margin-left:6px;">This text</span>'
    +     '<button class="axis-btn plain ' + pol('include') + '" data-axis="quote_polarity" data-value="include"'
    +       ' onclick="setAxis(\'' + key + '\', \'quote_polarity\', \'include\', ' + idx + ')">belongs in the story</button>'
    +     '<button class="axis-btn plain ' + pol('exclude') + '" data-axis="quote_polarity" data-value="exclude"'
    +       ' onclick="setAxis(\'' + key + '\', \'quote_polarity\', \'exclude\', ' + idx + ')">should be cut</button>'
    +   '</div>'
    + '</div>';
}

function buildCard(story, idx) {
  const card = document.createElement('div');
  const v = verdicts[story.key] || {};
  card.className = 'story-card cls-' + story.classification + (isComplete(v) ? ' reviewed' : '');
  card.id = 'card-' + idx;
  const sel = val => v.is_story === val ? 'selected' : '';

  card.innerHTML =
      '<div class="story-header">'
    +   '<span class="story-title">' + story.page_ref + ' :: seg ' + story.start_segment + '-' + story.end_segment + '</span>'
    +   (story.spans_pages ? '<span class="badge cross">continues on ' + story.spans_pages[1] + '</span>' : '')
    +   (story.mishnah_withheld ? '<span class="badge mishnah">inside a Mishnah — withheld from our output</span>' : '')
    +   '<span style="font-size:12px;color:#94a3b8;">' + story.classification + '</span>'
    + '</div>'
    + (story.one_sentence_summary ? '<div style="font-size:13px;color:#475569;margin-bottom:8px;">' + esc(story.one_sentence_summary) + '</div>' : '')
    + buildTextDisplay(story)
    + '<div class="axis-row">'
    +   '<span class="axis-label">Is it a story?</span>'
    +   '<button class="axis-btn v-yes ' + sel('yes') + '" data-axis="is_story" data-value="yes" onclick="setAxis(\'' + story.key + '\', \'is_story\', \'yes\', ' + idx + ')">Yes</button>'
    +   '<button class="axis-btn v-borderline ' + sel('borderline') + '" data-axis="is_story" data-value="borderline" onclick="setAxis(\'' + story.key + '\', \'is_story\', \'borderline\', ' + idx + ')">Borderline</button>'
    +   '<button class="axis-btn v-no ' + sel('no') + '" data-axis="is_story" data-value="no" onclick="setAxis(\'' + story.key + '\', \'is_story\', \'no\', ' + idx + ')">No</button>'
    +   '<button class="axis-btn flag-btn ' + (v.display_problem ? 'selected' : '') + '" data-axis="display_problem" onclick="toggleDisplay(\'' + story.key + '\', ' + idx + ')">&#9888; Display problem</button>'
    +   '<button class="axis-btn disclose" data-role="disclose" onclick="toggleAxes(' + idx + ', this)">Something else is wrong &#9662;</button>'
    + '</div>'
    + '<div class="more-axes" data-role="more-axes">'
    +   '<div class="axis-row"><span class="axis-label">Extent</span>' + axisButtons(story.key, idx, 'extent') + '</div>'
    +   quoteBox(story.key, idx)
    +   '<div class="axis-row"><span class="axis-label">Confidence</span>' + axisButtons(story.key, idx, 'confidence') + '</div>'
    +   '<div class="axis-row"><span class="axis-label">Grouping</span>' + axisButtons(story.key, idx, 'grouping') + '</div>'
    + '</div>'
    + '<input class="notes-input" placeholder="Anything else, in your own words (optional)"'
    +   ' value="' + String(v.notes || '').replace(/"/g, '&quot;') + '"'
    +   ' onchange="setNotes(\'' + story.key + '\', this.value)">';
  return card;
}

function ensure(key) {
  if (!verdicts[key]) {
    verdicts[key] = { is_story: null, extent: null, confidence: null,
                      grouping: null, display_problem: false,
                      quote: '', quote_polarity: null,
                      quote_start: '', quote_end: '', notes: '' };
  }
  return verdicts[key];
}

function setAxis(key, axis, value, idx) {
  const v = ensure(key);
  v[axis] = (v[axis] === value) ? null : value;   // clicking again clears it
  const card = document.getElementById('card-' + idx);
  if (card) {
    card.querySelectorAll('.axis-btn[data-axis="' + axis + '"]').forEach(b => {
      b.classList.toggle('selected', b.dataset.value === v[axis]);
    });
    card.classList.toggle('reviewed', isComplete(v));
    if (axis === 'extent') {
      const box = card.querySelector('[data-role="quote"]');
      if (box) box.classList.toggle('open', isExtentWrong(v.extent));
    }
  }
  updateProgress();
}

function setQuote(key, text) { ensure(key).quote = text; }
function setField(key, field, text) { ensure(key)[field] = text; }

// Same as grabSelection, but writes into a named field, so START and END are
// two separate statements rather than one quote whose direction we have to
// guess. `both_wrong` was expressible on the extent axis and NOT expressible in
// the box underneath it — one quote, one polarity — which is the same
// "we recorded that it was wrong, never what was wrong" failure the axes exist
// to end (Lesson 30).
function grabInto(key, field, idx) {
  const sel = (typeof window !== 'undefined' && window.getSelection)
              ? String(window.getSelection()) : '';
  if (!sel.trim()) return;
  const v = ensure(key);
  v[field] = sel.trim();
  const card = document.getElementById('card-' + idx);
  const box = card && card.querySelector('[data-role="' + field + '-text"]');
  if (box) box.value = v[field];
}

// Typing Hebrew is a transcription risk and a chore; the text is already on the
// page, so let him select it. Falls back to the textarea where there is no
// selection API.
function grabSelection(key, idx) {
  const sel = (typeof window !== 'undefined' && window.getSelection)
              ? String(window.getSelection()) : '';
  if (!sel.trim()) return;
  const v = ensure(key);
  v.quote = sel.trim();
  const card = document.getElementById('card-' + idx);
  const box = card && card.querySelector('[data-role="quote-text"]');
  if (box) box.value = v.quote;
}

function toggleDisplay(key, idx) {
  const v = ensure(key);
  v.display_problem = !v.display_problem;
  const card = document.getElementById('card-' + idx);
  if (card) {
    const btn = card.querySelector('.axis-btn[data-axis="display_problem"]');
    if (btn) btn.classList.toggle('selected', v.display_problem);
  }
}

// Independent of axis 1 on purpose: "it IS a story and the boundary is wrong"
// is the commonest correction we get, and the old UI had no way to say it.
function toggleAxes(idx, btn) {
  const card = document.getElementById('card-' + idx);
  if (!card) return;
  const more = card.querySelector('[data-role="more-axes"]');
  if (!more) return;
  const open = more.classList.toggle('open');
  if (btn) btn.classList.toggle('open', open);
}

function setNotes(key, notes) { ensure(key).notes = notes; }

function updateProgress() {
  const done = Object.keys(verdicts).filter(k => isComplete(verdicts[k])).length;
  const bar = document.getElementById('progressFill');
  if (bar) bar.style.width = (done / STORIES.length * 100) + '%';
}

function buildExport() {
  const reviews = {};
  STORIES.forEach((story, idx) => {
    const v = verdicts[story.key];
    if (!isComplete(v)) return;      // an unanswered card is absent, not a null verdict
    reviews[story.key] = {
      index: idx + 1,
      page_ref: story.page_ref,
      start_segment: story.start_segment,
      end_segment: story.end_segment,
      classification_shown: story.classification,
      mishnah_withheld: !!story.mishnah_withheld,
      // Lesson 36: a verdict belongs to the version that was reviewed.
      detector_version: DETECTOR_VERSION,
      applies_to: 'base',
      is_story: v.is_story,
      extent: v.extent,
      confidence: v.confidence,
      grouping: v.grouping,
      display_problem: !!v.display_problem,
      // Stated, not mined out of prose afterwards. `quote_polarity` is the
      // field whose absence leaves 16 of 70 harvested boundary targets
      // `mixed` or `unclear`.
      quote: v.quote || '',
      quote_polarity: v.quote_polarity,
      // The exact boundaries, in his own words. Two fields because a story can
      // start AND end in the wrong place, which `extent: both_wrong` could say
      // and the single quote box could not.
      quote_start: v.quote_start || '',
      quote_end: v.quote_end || '',
      notes: v.notes || ''
    };
  });
  return {
    tractate: TRACTATE,
    schema_version: SCHEMA_VERSION,
    detector_version: DETECTOR_VERSION,
    applies_to: 'base',
    date: new Date().toISOString().split('T')[0],
    total_stories: STORIES.length,
    reviewed: Object.keys(reviews).length,
    reviews: reviews
  };
}

function saveResults() {
  document.getElementById('exportData').value = JSON.stringify(buildExport(), null, 2);
  document.getElementById('exportArea').classList.remove('hidden');
  document.getElementById('exportArea').scrollIntoView({ behavior: 'smooth' });
}

function downloadJSON() {
  const blob = new Blob([document.getElementById('exportData').value], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'axis_' + TRACTATE.toLowerCase() + '_review_' + new Date().toISOString().split('T')[0] + '.json';
  a.click();
  URL.revokeObjectURL(url);
}

init();
</script>
</body>
</html>"""


def generate_html(title: str, stories: List[Dict], detector_version: str,
                  note: str | None = None) -> str:
    data_json = json.dumps(stories, ensure_ascii=True).replace('</', '<\\/')
    n_cross = sum(1 for s in stories if s.get('spans_pages'))
    n_mish = sum(1 for s in stories if s.get('mishnah_withheld'))
    return (PAGE
            .replace('__DISPLAY_CSS__', DISPLAY_CSS)
            .replace('__DISPLAY_JS__', DISPLAY_JS)
            .replace('__TITLE__', title)
            .replace('__DETECTOR_VERSION__', detector_version)
            .replace('__SCHEMA_VERSION__', SCHEMA_VERSION)
            .replace('__N_TOTAL__', str(len(stories)))
            .replace('__N_CROSS__', str(n_cross))
            .replace('__N_MISHNAH__', str(n_mish))
            # Whole line, newline included, so a page with no note is byte-identical
            # to the ones already banked (tests/test_review_ui_axes.py).
            .replace('    __NOTE__\n', f'    <p><b>{note}</b></p>\n' if note else '')
            .replace('__STORIES__', data_json))


def main(argv=None) -> int:
    """No arguments reproduces the two banked pages byte for byte.

    `--run/--title/--out` builds a page for a tractate with no banked config
    (Gittin, Yevamot, Eruvin), and `--only` restricts it to a list of
    `{ref, start_segment, end_segment}` — which is what turns a 147-entry
    tractate into a 30-entry ask. Review is the bottleneck, and the one round
    Jeff finished 100% of was the delta page that showed him only what was new
    (49/49, against 1 and 15 for the pages that showed him everything again).
    """
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--run', nargs='+', help='run file(s) to read instead of the banked set')
    ap.add_argument('--title')
    ap.add_argument('--out', help='file name under validation/ui/')
    ap.add_argument('--only', help='JSON list of {ref,start_segment,end_segment} to keep')
    ap.add_argument('--note', help='one line shown under the page title')
    args = ap.parse_args(argv)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if args.run:
        if not (args.title and args.out):
            ap.error('--run needs --title and --out')
        paths = [Path(r) if Path(r).is_absolute() else ROOT / r for r in args.run]
        stories, version = build_data(paths)
        if args.only:
            keep = {(o['ref'], o['start_segment'], o['end_segment'])
                    for o in json.loads(Path(args.only).read_text())}
            before = len(stories)
            stories = [s for s in stories
                       if (s['page_ref'], s['start_segment'], s['end_segment']) in keep]
            # Never drop silently: a filter that matches nothing, or half of what
            # it names, is the failure this line exists to make visible (Lesson 38).
            print(f"  --only kept {len(stories)} of {before} entries "
                  f"({len(keep)} named in {Path(args.only).name}; "
                  f"{len(keep) - len(stories)} named but not present in the run)")
            if not stories:
                print('  REFUSING to write an empty review page'); return 1
        html = generate_html(args.title, stories, version, note=args.note)
        out = OUT_DIR / args.out
        out.write_text(html, encoding='utf-8')
        cls = Counter(s['classification'] for s in stories)
        print(f"  {args.title}: {len(stories)} entries "
              f"({sum(1 for s in stories if s['mishnah_withheld'])} withheld from a Mishnah) "
              f"-> {out.relative_to(ROOT)}")
        print(f"      version={version}  {dict(cls)}")
        return 0

    for slug, cfg in TRACTATES.items():
        paths = [RUN_DIR / n for n in cfg['files']]
        missing = [p for p in paths if not p.exists()]
        if missing:
            print(f"  SKIP {slug}: missing {[str(m.relative_to(ROOT)) for m in missing]}")
            continue
        stories, version = build_data(paths)
        html = generate_html(cfg['title'], stories, version)
        out = OUT_DIR / cfg['out']
        out.write_text(html, encoding='utf-8')
        cls = Counter(s['classification'] for s in stories)
        print(f"  {slug}: {len(stories)} entries "
              f"({sum(1 for s in stories if s['mishnah_withheld'])} withheld from a Mishnah) "
              f"→ {out.relative_to(ROOT)}")
        print(f"      version={version}  {dict(cls)}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
