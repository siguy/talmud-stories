#!/usr/bin/env python3
"""Simon's review page for the low-pool promotions -- is each one really a story?

work/2026-11-13-low-pool-grader-calibration.md: the calibrated Claude grader read the 1,259 low-confidence
passages the Septimus site does not ship, twice. 80 were called `story` by both passes
(results/shas_run/low_pool/pool/promotions.json). `grade_low_pool.py sample` drew a seeded 60 of them
(review_sample.json). Nothing ships unless at least 54 of those 60 are real stories -- this page is how
that is read.

Layout and verdict buttons are the precision-sample page's (validation/ui/shas_precision_sample.html, built by
generate_axis_review_ui.py, which Simon used on 2026-11-12): its stylesheet is taken from that generator, not
copied, and the text comes from review_ui_core.py -- one segment per row, Hebrew and English together, guarded
by tests/test_review_ui_symmetry.py. What differs, and why:
  * only "Is it a story?" (yes / borderline / no) plus a note -- there is no extent or confidence to grade;
  * the 60 sampled passages first, in sample order, labelled as counting toward the bar; the other 20 after,
    labelled optional;
  * the grader's reasons sit behind a closed disclosure, so they do not lead the answer.

Highlighted rows are the passage; the cells the grader pointed to (either pass) are <mark>ed inside them.
Two cells of context either side come from the same text the grader read (grade_low_pool.text_for), and the
grader's segment numbers are resolved against the same [1], [2], ... window it was shown (bracket_cells), so a
pass that pointed at context would be visible -- on this pool none does (checked when built).

    python3 validation/generators/generate_low_pool_review_ui.py
    #  -> validation/ui/low_pool_promotions_review.html

No model calls.
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / 'scripts'))
from review_ui_core import DISPLAY_CSS, DISPLAY_JS  # noqa: E402
import generate_axis_review_ui as axis  # noqa: E402  (the stylesheet Simon's last page used)
import grade_low_pool as g  # noqa: E402

POOL = ROOT / 'results/shas_run/low_pool/pool'
OUT = ROOT / 'validation/ui/low_pool_promotions_review.html'
CONTEXT = 2                    # cells either side of the passage
DETECTOR_VERSION = 'v14'       # the pool is v14 units (grade_low_pool.py docstring)
BAR = 54                       # of the sample, real stories needed before anything ships

log = logging.getLogger('low-pool-review-ui')


def build_items():
    promos = json.loads((POOL / 'promotions.json').read_text())['promotions']
    sample = json.loads((POOL / 'review_sample.json').read_text())
    by_id = {p['id']: p for p in promos}
    sample_ids = [r['id'] for r in sample['rows']]
    missing = [i for i in sample_ids if i not in by_id]
    if missing:
        raise SystemExit(f'sample names {len(missing)} ids not in promotions.json: {missing[:3]}')
    order = [(i, 'sample') for i in sample_ids] + [(p['id'], 'extra') for p in promos if p['id'] not in set(sample_ids)]

    texts, items, outside = {}, [], 0
    for n, (pid, stratum) in enumerate(order, 1):
        p = by_id[pid]
        text = texts.get(p['slug']) or texts.setdefault(p['slug'], g.text_for(p['slug']))
        cells = [tuple(c) for c in p['cells']]
        numbered = g.bracket_cells(p['cells'], text)
        chose = {ps: sorted({tuple(numbered[k - 1]) for k in p['grader'][ps]['segments'] if 0 < k <= len(numbered)},
                            key=lambda c: text.pos[c]) for ps in g.PASSES}
        outside += sum(1 for ps in g.PASSES for c in chose[ps] if c not in set(cells))
        a, b = text.pos[cells[0]], text.pos[cells[-1]]
        window = text.cells[max(a - CONTEXT, 0):b + CONTEXT + 1]
        groups = []
        for ref, i in window:
            if not groups or groups[-1]['ref'] != ref:
                groups.append({'ref': ref, 'segs': []})
            seg = text.seg[(ref, i)]
            groups[-1]['segs'].append({'index': i, 'hebrew': (seg.get('hebrew') or '').strip(),
                                       'english': (seg.get('english') or '').strip()})
        for grp in groups:
            inside = [i for r, i in cells if r == grp['ref']]
            grp['start'], grp['end'] = (min(inside), max(inside)) if inside else (None, None)
        items.append({
            'key': pid, 'index': n, 'stratum': stratum, 'ref': p['ref'], 'tractate': p['tractate'],
            'pool': p['pool'], 'run1': p['run1'], 'run2': p['run2'], 'summary': p.get('summary') or '',
            'cells': [list(c) for c in cells], 'groups': groups,
            'chosen': sorted({f'{r}|{i}' for ps in g.PASSES for r, i in chose[ps]}),
            'grader': {ps: {'reason': p['grader'][ps]['reason'], 'rules': p['grader'][ps]['rules'],
                            'cells': [f'{r}:{i}' for r, i in chose[ps]]} for ps in g.PASSES},
        })
    return items, len(sample_ids), outside


PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Low-pool promotions — Story Review</title>
<style>
__AXIS_CSS__
  .badge.sample { background: #dcf3e6; color: #1d5b3a; }
  .badge.extra { background: #edf2f7; color: #4a5568; }
  .section-head { font-size: 13px; font-weight: 700; letter-spacing: .05em; text-transform: uppercase;
                  color: #48606f; margin: 26px 0 10px; }
  details.grader { margin-top: 12px; font-size: 13px; color: #475569; }
  details.grader summary { cursor: pointer; color: #6c7a89; }
  details.grader .pass { margin-top: 6px; padding: 8px 12px; background: #f7fafc;
                         border: 1px solid #e2e8f0; border-radius: 6px; }
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>Low-pool promotions — Story Review</h1>
    <p><b>Passages the site does not show today, which the Claude grader called a story twice. For each: is it a story?</b></p>
    <p>Hebrew and English are shown side by side, one row per segment, so the two always cover the <b>same extent</b>. Nothing is cut in either language — the passage is highlighted inside two segments of context either side.</p>
    <div class="howto">
      <b>The first __N_SAMPLE__ are the random sample: nothing ships unless at least __BAR__ of them are real stories.</b> The last __N_EXTRA__ are extra and optional.<br>
      <b>Highlighted rows</b> are the passage. Where the Hebrew is also <mark class="span-in">marked like this</mark>, that is the part the grader pointed to.<br>
      The grader's reasons are under <b>“Grader's reasons”</b>, closed — open them only after you have answered, if at all.<br>
      <b>Keyboard</b> (when not typing in a box): <b>j</b> jumps to the next unreviewed entry, then <b>y</b> / <b>b</b> / <b>n</b> answer Yes / Borderline / No for it.<br>
      If the <b>page itself</b> is broken — text missing, Hebrew not matching — click <b>⚠ Display problem</b>. That is our bug, not a judgement about the passage.
    </div>
    <div class="stats">
      <div class="stat"><strong>__N_TOTAL__</strong> entries</div>
      <div class="stat">sample: <strong>__N_SAMPLE__</strong> (bar: __BAR__ real)</div>
      <div class="stat">detector: <strong>__DETECTOR_VERSION__</strong></div>
      <div class="stat" id="tally">sample so far: 0 yes · 0 borderline · 0 no</div>
      <div class="stat" id="savedCount" title="Kept in this browser as you go; Save Review still makes the file to send">0 saved locally</div>
    </div>
  </div>

  <div class="controls">
    <strong style="font-size: 12px; color: #6c7a89;">FILTER</strong>
    <button class="active" onclick="setFilter('all', this)">all</button>
    <button onclick="setFilter('unreviewed', this)">unreviewed</button>
    <button onclick="setFilter('sample', this)">sample</button>
    <button onclick="setFilter('extra', this)">extra</button>
    <button class="save-btn" onclick="saveResults()">Save Review</button>
  </div>

  <p class="progress-text" id="progressText"></p>
  <div class="progress-bar"><div class="progress-fill" id="progressFill" style="width: 0%;"></div></div>

  <div id="storiesContainer"></div>

  <div id="exportArea" class="hidden" style="background: white; padding: 20px; border-radius: 10px; margin-top: 20px;">
    <h3>Review Export</h3>
    <p id="exportWarning" style="color:#9b2c2c; font-weight:600; margin-top:8px;"></p>
    <textarea class="export-box" id="exportData" readonly></textarea>
    <button class="save-btn" onclick="downloadJSON()" style="margin-top: 10px;">Download JSON</button>
  </div>
</div>
<script>
const STORIES = __STORIES__;
const DETECTOR_VERSION = "__DETECTOR_VERSION__";
const SCHEMA_VERSION = "__SCHEMA_VERSION__";
const N_SAMPLE = __N_SAMPLE__, BAR = __BAR__;
const HEBREW_FIRST = true;   // the Hebrew is the text; the English translates it
const STORAGE_KEY = 'low-pool-promotions-review:' + DETECTOR_VERSION;
const verdicts = {};
let activeFilter = 'all';
let currentIdx = null;

__DISPLAY_JS__

// The grader's cells, as a <mark> over the whole Hebrew cell, inside the highlighted rows.
function chosenSpan(grp, i, heb) {
  return grp.chosen.indexOf(grp.ref + '|' + i) >= 0 ? [0, heb.length] : [null, null];
}

// One grid per daf the window touches, all from buildGrid. A daf with no passage cell is context
// (the axis page's edge rows): a synthetic start past its last row, or -1 before its first, puts
// every row outside the highlight.
function buildTextDisplay(story) {
  let out = '', seen = false;
  story.groups.forEach(grp => {
    const g = Object.assign({ chosen: story.chosen }, grp);
    if (grp.start === null) {
      const last = grp.segs.reduce((m, s) => Math.max(m, s.index), 0);
      const label = seen ? grp.ref + ' begins' : 'end of ' + grp.ref;
      out += '<div class="edge-note">' + label + '</div>'
           + buildGrid(grp.segs, seen ? -1 : last + 1, seen ? -1 : last + 1, {}, null);
      return;
    }
    if (seen) out += '<div class="cont-head">Continues on <b>' + grp.ref + '</b></div>';
    out += buildGrid(grp.segs, grp.start, grp.end, g, chosenSpan);
    seen = true;
  });
  return out;
}

function isComplete(v) { return !!(v && v.is_story); }

function persist() {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(verdicts)); } catch (e) {}
  showSaved();
}
function restore() {
  try { const raw = localStorage.getItem(STORAGE_KEY); if (raw) Object.assign(verdicts, JSON.parse(raw)); } catch (e) {}
}
function showSaved() {
  const n = Object.keys(verdicts).filter(k => isComplete(verdicts[k])).length;
  const el = document.getElementById('savedCount');
  if (el) el.textContent = n + ' saved locally';
}
function changed(key) { ensure(key).answered_at = new Date().toISOString(); persist(); }

function init() { restore(); showSaved(); render(); }

function setFilter(f, btn) {
  activeFilter = f;
  document.querySelectorAll('.controls button').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');
  render();
}
function passesFilter(story) {
  if (activeFilter === 'unreviewed') return !isComplete(verdicts[story.key]);
  if (activeFilter === 'sample' || activeFilter === 'extra') return story.stratum === activeFilter;
  return true;
}

const KEY_ANSWERS = { y: 'yes', b: 'borderline', n: 'no' };
function setCurrent(idx) {
  if (currentIdx !== null) { const old = document.getElementById('card-' + currentIdx); if (old) old.classList.remove('current'); }
  currentIdx = idx;
  const card = document.getElementById('card-' + idx);
  if (card) { card.classList.add('current'); if (card.scrollIntoView) card.scrollIntoView({ behavior: 'smooth', block: 'center' }); }
}
function nextUnreviewed() {
  const from = currentIdx === null ? -1 : currentIdx;
  for (let step = 1; step <= STORIES.length; step++) {
    const i = (from + step) % STORIES.length;
    if (passesFilter(STORIES[i]) && !isComplete(verdicts[STORIES[i].key])) return i;
  }
  return null;
}
function onKey(e) {
  const tag = (e.target && e.target.tagName || '').toUpperCase();
  if (tag === 'TEXTAREA' || tag === 'INPUT' || tag === 'SELECT') return;
  if (e.metaKey || e.ctrlKey || e.altKey) return;
  const k = (e.key || '').toLowerCase();
  if (k === 'j') { const i = nextUnreviewed(); if (i !== null) setCurrent(i); e.preventDefault(); }
  else if (KEY_ANSWERS[k] && currentIdx !== null) {
    const st = STORIES[currentIdx];
    if ((verdicts[st.key] || {}).is_story !== KEY_ANSWERS[k]) setAxis(st.key, 'is_story', KEY_ANSWERS[k], currentIdx);
    e.preventDefault();
  }
}
document.addEventListener('keydown', onKey);

function render() {
  const container = document.getElementById('storiesContainer');
  container.innerHTML = '';
  let lastStratum = null;
  STORIES.forEach((story, idx) => {
    if (!passesFilter(story)) return;
    if (story.stratum !== lastStratum) {
      const h = document.createElement('div');
      h.className = 'section-head';
      h.textContent = story.stratum === 'sample'
        ? 'Sample — ' + N_SAMPLE + ' passages, counts toward the ' + BAR + '/' + N_SAMPLE + ' bar'
        : 'Extra — ' + (STORIES.length - N_SAMPLE) + ' passages, optional';
      container.appendChild(h);
      lastStratum = story.stratum;
    }
    const card = buildCard(story, idx);
    if (idx === currentIdx) card.classList.add('current');
    container.appendChild(card);
  });
  updateProgress();
}

function graderBlock(story) {
  const pass = (name, p) => '<div class="pass"><b>' + name + '</b> (' + esc(p.rules.join(', ')) + '; pointed to '
    + esc(p.cells.join(', ')) + ')<br>' + esc(p.reason) + '</div>';
  return '<details class="grader"><summary>Grader\'s reasons (open after you answer)</summary>'
    + pass('Pass 1', story.grader.pass1) + pass('Pass 2', story.grader.pass2) + '</details>';
}

function buildCard(story, idx) {
  const card = document.createElement('div');
  const v = verdicts[story.key] || {};
  card.className = 'story-card cls-LOW_CONFIDENCE' + (isComplete(v) ? ' reviewed' : '');
  card.id = 'card-' + idx;
  const sel = val => v.is_story === val ? 'selected' : '';
  const btn = (val, cls, label) => '<button class="axis-btn ' + cls + ' ' + sel(val) + '" data-axis="is_story" data-value="' + val
    + '" onclick="setAxis(\'' + story.key + '\', \'is_story\', \'' + val + '\', ' + idx + ')">' + label + '</button>';
  card.innerHTML =
      '<div class="story-header">'
    +   '<span class="story-title">' + story.index + '. ' + esc(story.key) + '</span>'
    +   (story.stratum === 'sample'
          ? '<span class="badge sample">sample (counts toward the ' + BAR + '/' + N_SAMPLE + ' bar)</span>'
          : '<span class="badge extra">extra (optional)</span>')
    +   (story.groups.filter(gr => gr.start !== null).length > 1 ? '<span class="badge cross">crosses a daf</span>' : '')
    +   '<span style="font-size:12px;color:#94a3b8;">' + story.run1 + ' / ' + story.run2 + '</span>'
    + '</div>'
    + (story.summary ? '<div style="font-size:13px;color:#475569;margin-bottom:8px;">' + esc(story.summary) + '</div>' : '')
    + buildTextDisplay(story)
    + '<div class="axis-row">'
    +   '<span class="axis-label">Is it a story?</span>'
    +   btn('yes', 'v-yes', 'Yes') + btn('borderline', 'v-borderline', 'Borderline') + btn('no', 'v-no', 'No')
    +   '<button class="axis-btn flag-btn ' + (v.display_problem ? 'selected' : '') + '" data-axis="display_problem" onclick="toggleDisplay(\'' + story.key + '\', ' + idx + ')">&#9888; Display problem</button>'
    + '</div>'
    + '<textarea class="notes-input" rows="2" placeholder="Note (optional)"'
    +   ' oninput="setNotes(\'' + story.key + '\', this.value)">' + esc(String(v.notes || '')) + '</textarea>'
    + graderBlock(story);
  return card;
}

function ensure(key) {
  if (!verdicts[key]) verdicts[key] = { is_story: null, display_problem: false, notes: '' };
  return verdicts[key];
}
function setAxis(key, axis, value, idx) {
  const v = ensure(key);
  v[axis] = (v[axis] === value) ? null : value;   // clicking again clears it
  const card = document.getElementById('card-' + idx);
  if (card) {
    card.querySelectorAll('.axis-btn[data-axis="' + axis + '"]').forEach(b => b.classList.toggle('selected', b.dataset.value === v[axis]));
    card.classList.toggle('reviewed', isComplete(v));
  }
  updateProgress();
  changed(key);
}
function toggleDisplay(key, idx) {
  const v = ensure(key);
  v.display_problem = !v.display_problem;
  changed(key);
  const card = document.getElementById('card-' + idx);
  const b = card && card.querySelector('.axis-btn[data-axis="display_problem"]');
  if (b) b.classList.toggle('selected', v.display_problem);
}
function setNotes(key, notes) { ensure(key).notes = notes; changed(key); }

function sampleTally() {
  const t = { yes: 0, borderline: 0, no: 0 };
  STORIES.forEach(s => { const v = verdicts[s.key]; if (s.stratum === 'sample' && isComplete(v)) t[v.is_story]++; });
  return t;
}
function updateProgress() {
  const done = Object.keys(verdicts).filter(k => isComplete(verdicts[k])).length;
  const t = sampleTally(), sdone = t.yes + t.borderline + t.no;
  document.getElementById('progressFill').style.width = (done / STORIES.length * 100) + '%';
  document.getElementById('progressText').textContent = done + ' of ' + STORIES.length + ' reviewed — sample '
    + sdone + ' of ' + N_SAMPLE + ', extra ' + (done - sdone) + ' of ' + (STORIES.length - N_SAMPLE);
  document.getElementById('tally').textContent = 'sample so far: ' + t.yes + ' yes · ' + t.borderline + ' borderline · ' + t.no + ' no';
}

// The precision pre-read's export shape (validation/feedback/2026-11-simon-precision-sample.json): file-level
// reviewer fields, then `reviews` keyed by id. Axes this page does not ask are exported null -- "not asked",
// never "right".
function buildExport() {
  const reviews = {};
  STORIES.forEach(story => {
    const v = verdicts[story.key];
    if (!isComplete(v)) return;      // an unanswered card is absent, not a null verdict
    const c = story.cells;
    reviews[story.key] = {
      index: story.index, id: story.key, ref: story.ref, page_ref: story.ref,
      start_segment: c[0][1], end_segment: c[c.length - 1][1], cells: c,
      classification_shown: story.run1 + ' / ' + story.run2, pool: story.pool,
      detector_version: DETECTOR_VERSION, applies_to: 'base',
      is_story: v.is_story, extent: null, confidence: null, grouping: null,
      display_problem: !!v.display_problem, notes: v.notes || '',
      schema_version: SCHEMA_VERSION, answered_at: v.answered_at || null,
      stratum: story.stratum
    };
  });
  return {
    reviewer: 'Simon Brief',
    reviewer_role: 'project owner -- NOT the expert. These are NOT Jeff Rubenstein\'s verdicts and are not ground truth.',
    evidence_grade: 'indicated',
    purpose: 'Owner\'s read of the low-pool promotions (both grader passes said story); nothing ships unless >= '
             + BAR + ' of the ' + N_SAMPLE + ' sampled are real stories',
    tractate: 'Low-pool promotions',
    schema_version: SCHEMA_VERSION, detector_version: DETECTOR_VERSION, applies_to: 'base',
    date: new Date().toISOString().split('T')[0],
    source: 'validation/ui/low_pool_promotions_review.html',
    sample: 'results/shas_run/low_pool/pool/review_sample.json',
    promotions: 'results/shas_run/low_pool/pool/promotions.json',
    total_stories: STORIES.length, sample_n: N_SAMPLE, bar: BAR,
    sample_tally: sampleTally(),
    reviewed: Object.keys(reviews).length,
    reviews: reviews
  };
}
function saveResults() {
  const missing = STORIES.filter(s => !isComplete(verdicts[s.key]) && verdicts[s.key]
                                     && ((verdicts[s.key].notes || '').trim() || verdicts[s.key].display_problem)).map(s => s.key);
  document.getElementById('exportWarning').textContent = missing.length
    ? missing.length + ' with a note or flag but no Yes / Borderline / No, so NOT in this export: ' + missing.join('; ') : '';
  document.getElementById('exportData').value = JSON.stringify(buildExport(), null, 2);
  document.getElementById('exportArea').classList.remove('hidden');
  document.getElementById('exportArea').scrollIntoView({ behavior: 'smooth' });
}
function downloadJSON() {
  const blob = new Blob([document.getElementById('exportData').value], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'low_pool_promotions_review_simon_' + new Date().toISOString().split('T')[0] + '.json';
  a.click();
  URL.revokeObjectURL(url);
}

init();
</script>
</body>
</html>"""


def axis_css() -> str:
    """The precision-sample page's stylesheet, taken from its generator so the two cannot drift apart."""
    return axis.PAGE.split('<style>', 1)[1].split('</style>', 1)[0].replace('__DISPLAY_CSS__', DISPLAY_CSS)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s [low-pool-review-ui] %(message)s',
                        handlers=[logging.StreamHandler(), logging.FileHandler(ROOT / 'project.log')])
    items, n_sample, outside = build_items()
    if outside:
        log.warning('%d grader-chosen cells fall outside their passage; they show as context, unmarked', outside)
    html = (PAGE.replace('__AXIS_CSS__', axis_css())
                .replace('__DISPLAY_JS__', DISPLAY_JS)
                .replace('__DETECTOR_VERSION__', DETECTOR_VERSION)
                .replace('__SCHEMA_VERSION__', axis.SCHEMA_VERSION)
                .replace('__N_TOTAL__', str(len(items)))
                .replace('__N_SAMPLE__', str(n_sample))
                .replace('__N_EXTRA__', str(len(items) - n_sample))
                .replace('__BAR__', str(BAR))
                .replace('__STORIES__', json.dumps(items, ensure_ascii=True).replace('</', '<\\/')))
    OUT.write_text(html, encoding='utf-8')
    log.info('%d promotions (%d sample, %d extra) -> %s', len(items), n_sample, len(items) - n_sample,
             OUT.relative_to(ROOT))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
