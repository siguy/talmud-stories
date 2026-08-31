#!/usr/bin/env python3
"""Generate the review UI that records WHICH thing is wrong.

Phase B of `work/2026-08-30-review-verdict-axes.md`.

THE PROBLEM THIS PAGE SOLVES
----------------------------
Every previous review UI recorded *that* the reviewer rejected an entry and never *what
he was rejecting*. Sorting eight rounds of rejections by the objection behind them
(`docs/findings/2026-08-30-detection-classification-ruler.md`, Lesson 30):

    most rejections are boundary, merge or confidence-level complaints -- three other
    capabilities, pooled into one figure and reported as Classification precision.

So the number could only ever be quoted as a range, and hand-reading every unreadable
note (Phase A, `docs/findings/2026-08-31-objection-axis-hand-sort.md`) narrowed that range
as far as reading can take it and no further. A point estimate needs the distinction
captured at entry. That is this page.

THE AXES
--------
Axis 1 is the only required question, and it is the only one that decides Classification:

    Is this a story?   Yes | Borderline | No

`Borderline` is Jeff's own request -- contested cases kept and flagged rather than
silently resolved (ledger 2026-07-06, Part 2(d)) -- and capability 6 needs the column
anyway.

Axes 2-4 default to `right` and are revealed only when the reviewer says something else
is wrong. Each indicts a different capability, so each is recorded separately:

    Extent      right | starts wrong | ends wrong | both      -> capability 4
    Confidence  right | too high | too low                    -> capability 3, calibration
    Grouping    right | should be split | should be merged    -> capability 2

Axis 5 is separate from all of them, and it is here because Phase A found a verdict spent
on our own renderer with nowhere to put it:

    Display     the page is showing this wrong                -> capability 5

A display bug can co-occur with any verdict, so it is never gated behind the others. Two
of the 15 verdicts in the 2026-07-06 round went on our rendering, and one sat misfiled as
a detector defect for seven weeks (Lesson 25).

THREE RULES THE SHAPE ENFORCES
------------------------------
1.  **A correct entry is one click.** Review is the project's bottleneck -- weeks per
    tractate against ~$0.30 of compute -- and it holds the only DERIVED gate in
    FRAMEWORK. `Yes` alone writes a complete record with every axis at `right`. Y/B/N
    keyboard shortcuts, because `batch_review.html` built exactly this in January 2026
    and it was never reused.
2.  **A verdict cannot contradict its own note.** Answering `No` hides and clears axes
    2-4, which presuppose the passage IS a story. Two of the 34 hand-sorted notes affirm
    and reject at once (`Ketubot 62a_4-4`: *"This is clearly a story. Keep as a 'Yes'"*);
    under this shape neither is expressible.
3.  **Direction is recorded, not reconstructed.** Every saved verdict carries
    `classification_shown` -- the label the reviewer was actually looking at. Phase A had
    to recover that by re-indexing five old runs, because `incorrect` has meant both
    "you wrongly called this a story" and "you wrongly called this NOT a story" and the
    two were pooled. `direction` is computed from the pair and written down.

The free-text note stays, deliberately supplementary: the axes are always recorded, so a
note can add colour but can never be the only signal (which is what recreated the original
problem inside every previous UI). The Extent axis gets a dedicated Hebrew quote box,
because quoting the correct extent is how Jeff actually gives a boundary correction --
5 of the 34 hand-sorted notes are exactly that shape.

WHAT IS SHOWN
-------------
Source is `results/v10/wave4_notrim/` -- the honest outputs, segment-level boundaries, no
char-offset spans (those were reverted; `2026-08-28-wave4-span-failure-audit.md`). The
Wave 4 page still reads `results/v10/wave4/` on purpose, so it stays comparable with what
Jeff saw; nothing new should go to him from that path.

`mishnah_stories` is included by default and badged. Stage 4g withholds those passages
into a key no harness and no UI reads (Lesson 27), so the one person who can settle
whether they belong in the database has never been shown them (`jeff:mishnah-scope`).

`--include-rejected` adds the entries we classified NOT_A_STORY. Off by default because it
costs reviewer time, but it is the ONLY way to measure this capability's invisible half --
real stories we reject. The four cases we know of all came from one February round whose
UI happened to show them.

Usage:
  python3 validation/generators/generate_verdict_axes_review_ui.py
  python3 validation/generators/generate_verdict_axes_review_ui.py --include-rejected
  python3 validation/generators/generate_verdict_axes_review_ui.py --tractate kiddushin
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from validation.generators._review_display import DISPLAY_CSS, DISPLAY_JS  # noqa: E402
from src.story_detector_v11 import _split_into_clauses  # noqa: E402

RUN_DIR = ROOT / 'results' / 'v10' / 'wave4_notrim'
OUT_DIR = ROOT / 'validation' / 'ui'

SCHEMA = 'verdict_axes_v1'

TRACTATES = {
    'kiddushin': {
        'title': 'Kiddushin',
        'files': ['kiddushin_v10_notrim.json'],
        'out': 'verdict_axes_kiddushin_review.html',
    },
    'ketubot': {
        'title': 'Ketubot',
        'files': ['ketubot_v10_2-60_notrim.json', 'ketubot_v10_61-112_notrim.json'],
        'out': 'verdict_axes_ketubot_review.html',
    },
}

STORY_LABELS = ('YES', 'HIGH_CONFIDENCE', 'LOW_CONFIDENCE')

# One story in BLIND_STRIDE is asked for its extent BEFORE our span is on screen.
# Deterministic on the key rather than the index, so regenerating the page -- or adding
# a story to the run -- does not reshuffle who was asked what.
BLIND_STRIDE = 7
BLIND_CONTEXT = 4          # wider window when hiding, so the window gives less away


def _is_blind_sample(key: str) -> bool:
    return int(hashlib.sha1(key.encode()).hexdigest(), 16) % BLIND_STRIDE == 0


def _clauses(segments, lo, hi):
    """{segment index: [[start, end], ...]} over the RAW Hebrew, for the rows shown.

    Computed here, in Python, by the detector's own `_split_into_clauses` -- the same
    function `scripts/score_boundary_targets.py` uses to decide which clause a boundary
    sits at. A JavaScript reimplementation would drift, and a boundary target that means
    something different to the page than to the scorer is worse than no target.
    """
    out = {}
    for seg in segments:
        i = seg.get('index')
        if i is None or not (lo <= i <= hi):
            continue
        ranges = _split_into_clauses(seg.get('hebrew') or '')
        if ranges:
            out[str(i)] = [[a, b] for a, b in ranges]
    return out


def _story_key(ref: str, story: Dict) -> str:
    return f"{ref}_{story.get('start_segment')}-{story.get('end_segment')}"


def build_data(paths: List[Path], include_rejected: bool = False) -> List[Dict]:
    """One record per entry we want a verdict on.

    `origin` says which bucket of the run it came from, and it is carried through to the
    saved verdict. A `mishnah_withheld` entry is one Stage 4g moved out of `stories[]`;
    scoring it as an ordinary proposal would be the Lesson 27 mistake in reverse.
    """
    out: List[Dict] = []
    for p in paths:
        data = json.loads(p.read_text())
        page_lookup = {pg['ref']: pg for pg in data['pages']}
        for page in data['pages']:
            ref = page.get('ref', '')
            buckets = [('stories', s) for s in page.get('stories', [])]
            buckets += [('mishnah_withheld', s) for s in page.get('mishnah_stories', [])]
            for origin, s in buckets:
                label = s.get('classification', 'UNKNOWN')
                rejected = label == 'NOT_A_STORY'
                if rejected and not include_rejected:
                    continue
                item = {
                    'key': _story_key(ref, s),
                    'page_ref': ref,
                    'start_segment': s['start_segment'],
                    'end_segment': s['end_segment'],
                    # The label under review. Written into every saved verdict so nobody
                    # ever has to reconstruct it from the run again (Phase A section 3).
                    'classification': label,
                    'origin': origin,
                    'one_sentence_summary': s.get('one_sentence_summary', ''),
                    'page_segments': page.get('segments', []),
                    'spans_pages': s.get('spans_pages'),
                    'source_file': p.name,
                }
                item['blind_sample'] = _is_blind_sample(item['key'])
                pad = BLIND_CONTEXT if item['blind_sample'] else 2
                item['clauses'] = _clauses(item['page_segments'],
                                           s['start_segment'] - pad, s['end_segment'] + pad)
                if s.get('spans_pages') and len(s['spans_pages']) >= 2:
                    p2 = page_lookup.get(s['spans_pages'][1])
                    if p2:
                        item['page2_segments'] = p2.get('segments', [])
                        item['start_segment_page2'] = s.get('start_segment_page2', 0)
                        item['end_segment_page2'] = s.get('end_segment_page2', 0)
                        item['clauses2'] = _clauses(
                            item['page2_segments'],
                            (s.get('start_segment_page2', 0)) - pad,
                            (s.get('end_segment_page2', 0)) + pad)
                out.append(item)
    return out


def generate_html(tractate_title: str, stories: List[Dict], source_files: List[str]) -> str:
    labels = Counter(s.get('classification', 'UNKNOWN') for s in stories)
    n_mishnah = sum(1 for s in stories if s.get('origin') == 'mishnah_withheld')
    n_rejected = sum(1 for s in stories if s.get('classification') == 'NOT_A_STORY')
    n_blind = sum(1 for s in stories if s.get('blind_sample'))
    data_json = json.dumps(stories, ensure_ascii=True).replace('</', '<\\/')

    mishnah_banner = '' if not n_mishnah else f"""
    <div class="ask">
      <b>{n_mishnah} passage{'s' if n_mishnah != 1 else ''} below {'are' if n_mishnah != 1 else 'is'} badged
      <span class="badge origin-mishnah_withheld">withheld: inside a Mishnah</span></b> &mdash;
      the pipeline currently removes these from the database. Your 2005 lists contain no
      Mishnah-only story, but you marked several of them <i>correct</i> in review, so we
      have never known which you meant. Should a story quoted inside a <b>Mishnah</b> be
      in this database at all, or does it begin at the Gemara?
    </div>"""

    rejected_banner = '' if not n_rejected else f"""
    <div class="ask">
      <b>{n_rejected} passage{'s' if n_rejected != 1 else ''} below {'are' if n_rejected != 1 else 'is'} badged
      <span class="badge cls-NOT_A_STORY">we said: not a story</span></b> &mdash;
      these are passages the detector <i>rejected</i>. They are here so that saying
      <b>Yes</b> to one tells us something no other round can: a real story we threw away.
      Skipping them costs nothing.
    </div>"""

    # RAW string: every backslash below is a JS-level escape (\' inside a JS string
    # literal). Python must not touch them.
    return (r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>__TITLE__ &mdash; Story Review</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: #f4f6f8; color: #222; padding: 20px; line-height: 1.55; }
  .container { max-width: 1200px; margin: 0 auto; }
  .header { background: white; padding: 28px 30px; border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06); margin-bottom: 24px; }
  .header h1 { font-size: 26px; color: #2c3e50; margin-bottom: 8px; }
  .header p { color: #6c7a89; }
  .how { background: #f0f7f7; border: 1px solid #b5d9d9; border-radius: 8px;
         padding: 14px 18px; margin-top: 16px; font-size: 13.5px; line-height: 1.65; }
  .how kbd { background: #fff; border: 1px solid #cbd5e1; border-bottom-width: 2px;
             border-radius: 4px; padding: 1px 6px; font-size: 12px; font-family: monospace; }
  .ask { background: #fffaf0; border: 1px solid #fbd38d; border-radius: 8px;
         padding: 14px 18px; margin-top: 12px; font-size: 13.5px; line-height: 1.65;
         color: #653b0e; }
  .stats { display: flex; gap: 12px; margin-top: 16px; flex-wrap: wrap; }
  .stat { background: #f0f3f6; padding: 8px 14px; border-radius: 6px; font-size: 13px; }
  .stat strong { font-size: 16px; }
  .controls { background: white; padding: 14px 20px; border-radius: 10px;
              margin-bottom: 18px; box-shadow: 0 1px 4px rgba(0,0,0,0.05);
              display: flex; flex-wrap: wrap; gap: 10px; align-items: center;
              position: sticky; top: 0; z-index: 20; }
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
  .story-card.cls-NOT_A_STORY { border-left-color: #a0aec0; }
  .story-card.answered { border-left-width: 8px; }
  .story-card.current { box-shadow: 0 0 0 3px #2c7a7b33, 0 1px 4px rgba(0,0,0,0.06); }
  .story-header { display: flex; align-items: center; gap: 10px;
                  flex-wrap: wrap; margin-bottom: 12px; }
  .story-title { font-weight: 600; font-size: 15px; }
  .badge { font-size: 11px; padding: 3px 8px; border-radius: 4px; font-weight: 600; }
  .badge.cls-YES { background: #c6f6d5; color: #22543d; }
  .badge.cls-HIGH_CONFIDENCE { background: #dbeafe; color: #1e3a8a; }
  .badge.cls-LOW_CONFIDENCE { background: #fef3c7; color: #78350f; }
  .badge.cls-NOT_A_STORY { background: #e2e8f0; color: #475569; }
  .badge.origin-mishnah_withheld { background: #fed7aa; color: #7c2d12; }

__DISPLAY_CSS__

  .v9-note { background: #f7fafc; border: 1px solid #e2e8f0; padding: 6px 10px;
             margin-top: 6px; border-radius: 4px; font-size: 12px; color: #4a5568; }
  .cont-head { margin-top: 14px; padding-top: 10px; border-top: 1px dashed #cbd5e1;
               font-size: 12px; color: #64748b; }
  .legend { font-size: 12px; color: #6c7a89; margin-top: 14px; line-height: 1.6; }
  .legend .sw { display: inline-block; width: 12px; height: 12px; vertical-align: -2px;
                border-radius: 3px; margin-right: 4px; }

  /* ------------------------------------------------------------------
     THE AXES.  Axis 1 is the only required question and the only one
     that decides Classification.  Axes 2-4 default to `right`, so a
     correct entry is ONE CLICK; they appear only when the reviewer says
     something else is wrong, and they are hidden and CLEARED when axis 1
     says this is not a story -- they presuppose that it is.
     ------------------------------------------------------------------ */
  .axis1 { display: flex; gap: 10px; margin-top: 16px; align-items: center;
           flex-wrap: wrap; padding-top: 14px; border-top: 2px solid #edf1f4; }
  .axis1 .q { font-weight: 600; font-size: 14px; margin-right: 4px; }
  .big-btn { padding: 9px 22px; border: 2px solid #d4dae0; border-radius: 8px;
             background: white; cursor: pointer; font-size: 14px; font-weight: 600; }
  .big-btn:hover { border-color: #94a3b8; }
  .big-btn .k { font-weight: 400; font-size: 11px; color: #94a3b8; margin-left: 5px; }
  .big-btn.yes.on { background: #2c7a7b; color: white; border-color: #2c7a7b; }
  .big-btn.borderline.on { background: #b7791f; color: white; border-color: #b7791f; }
  .big-btn.no.on { background: #c53030; color: white; border-color: #c53030; }
  .big-btn.on .k { color: #ffffffaa; }

  .more-link { background: none; border: none; color: #2c7a7b; cursor: pointer;
               font-size: 13px; padding: 4px 0; text-decoration: underline; }
  .axes-more { margin-top: 12px; padding: 14px 16px; background: #fafbfc;
               border: 1px solid #e5e8ec; border-radius: 8px; }
  .axis-row { display: flex; gap: 8px; align-items: center; flex-wrap: wrap;
              padding: 7px 0; }
  .axis-row + .axis-row { border-top: 1px solid #eef1f4; }
  .axis-label { flex: 0 0 108px; font-size: 13px; font-weight: 600; color: #475569; }
  .axis-cap { flex: 0 0 auto; font-size: 11px; color: #94a3b8; }
  .opt { padding: 5px 12px; border: 1px solid #d4dae0; border-radius: 6px;
         background: white; cursor: pointer; font-size: 12.5px; }
  .opt.on { background: #2c5282; color: white; border-color: #2c5282; }
  .opt.neutral.on { background: #718096; border-color: #718096; }
  .quote-box { width: 100%; margin-top: 8px; padding: 8px 10px; direction: rtl;
               text-align: right; font-size: 16px; line-height: 1.7;
               font-family: 'SBL Hebrew', 'Times New Roman', serif;
               border: 1px solid #d4dae0; border-radius: 6px; }
  .quote-hint { font-size: 11.5px; color: #94a3b8; margin-top: 6px; }

  .mark-row { margin-top: 8px; }
  .mark-btn { padding: 5px 12px; border: 1px solid #b5d9d9; border-radius: 6px;
              background: #f0f7f7; color: #22543d; cursor: pointer; font-size: 12.5px;
              margin-right: 6px; }
  .mark-btn.on { background: #2c7a7b; color: white; border-color: #2c7a7b; }
  .blind-ask { background: #f0f7f7; border: 1px solid #b5d9d9; border-radius: 8px;
               padding: 12px 16px; margin: 12px 0 4px; font-size: 13.5px; color: #22543d; }
  .skip-btn { background: none; border: none; color: #2c7a7b; cursor: pointer;
              font-size: 12.5px; text-decoration: underline; }
  .blind-done { margin-top: 10px; font-size: 12.5px; color: #4a5568;
                background: #f7fafc; border: 1px solid #e2e8f0; border-radius: 6px;
                padding: 7px 11px; }
  .display-row { margin-top: 12px; }
  .display-btn { padding: 5px 12px; border: 1px solid #e2b8b8; border-radius: 6px;
                 background: #fffafa; color: #9b2c2c; cursor: pointer; font-size: 12.5px; }
  .display-btn.on { background: #c53030; color: white; border-color: #c53030; }

  .notes-input { width: 100%; margin-top: 10px; padding: 7px 10px;
                 border: 1px solid #d4dae0; border-radius: 6px; font-size: 13px; }
  .progress-bar { background: #e2e8f0; height: 6px; border-radius: 3px; margin-bottom: 18px; }
  .progress-fill { background: #2c7a7b; height: 100%; border-radius: 3px; transition: width 0.3s; }
  .hidden { display: none; }
  textarea.export-box { width: 100%; height: 220px; font-family: monospace; font-size: 11px;
                        padding: 10px; border: 1px solid #d4dae0; border-radius: 6px; margin-top: 10px; }
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>__TITLE__ &mdash; Story Review</h1>
    <p>English and Hebrew are shown side by side, one row per segment, so the two always
       cover the <b>same extent</b>. Nothing is cut in either language &mdash; the story is
       highlighted inside the full text.</p>
    <div class="how">
      <b>One question is required: is this a story?</b> If it is, and we have it right,
      that is the only click &mdash; press <kbd>Y</kbd> and move on.<br>
      If something else is wrong &mdash; the extent, the confidence level, or whether this
      is one story or two &mdash; open <b>&ldquo;something else is wrong&rdquo;</b> and say
      which. We have been recording <i>that</i> you disagreed without recording
      <i>what with</i>, and it turns out most disagreements were never about whether the
      passage is a story at all.<br>
      <kbd>Y</kbd> yes &nbsp; <kbd>B</kbd> borderline &nbsp; <kbd>N</kbd> not a story
      &nbsp; <kbd>J</kbd>/<kbd>K</kbd> next/previous
    </div>__MISHNAH_BANNER____REJECTED_BANNER__
    <div class="legend">
      <span class="sw" style="background:#fffbe6;border:1px solid #d4a017;"></span> the story &nbsp;&middot;&nbsp;
      <span class="sw" style="background:#fbfcfd;border:1px solid #dde3e9;"></span> surrounding context (2 segments either side)<br>
      Cross-page stories continue in <b>both</b> languages below the dashed rule.
    </div>
    <div class="stats">
      <div class="stat"><strong>__N_TOTAL__</strong> passages</div>
      __BLIND_STAT__
      __LABEL_STATS__
    </div>
  </div>

  <div class="controls">
    <strong style="font-size: 12px; color: #6c7a89;">SHOW</strong>
    <button class="active" onclick="setFilter('all', this)">all</button>
    <button onclick="setFilter('unanswered', this)">unanswered</button>
    <button onclick="setFilter('answered', this)">answered</button>
    __FILTER_BUTTONS__
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
const STORIES = __STORIES_PLACEHOLDER__;
const TRACTATE = "__TITLE__";
const SOURCE_FILES = __SOURCE_FILES__;
const SCHEMA = "__SCHEMA__";

// A verdict is a record with every axis in it, never a single word. Axes 2-4 start at
// `right`, which is what makes a correct entry one click: pressing Yes writes a complete
// and accurate record with no further interaction.
const AXIS_DEFAULTS = { extent: 'right', confidence: 'right', grouping: 'right' };
const verdicts = {};
let activeFilter = 'all';
let cursor = 0;

function init() {
  render();
  document.addEventListener('keydown', onKey);
  document.addEventListener('click', onClauseClick);
}

// ---------------------------------------------------------------------------
// AXIS STATE
//
// answer() is the ONLY writer of axis 1, and it is where rule 2 lives: saying
// "not a story" clears axes 2-4 rather than leaving stale answers behind. Those
// axes presuppose the passage IS a story -- an extent complaint on something the
// reviewer just said is not a story is not a hard case to interpret, it is a
// contradiction, and the fix is to make it unrecordable.
// ---------------------------------------------------------------------------
function blank(story) {
  return Object.assign({ is_story: null, display_broken: false, note: '',
                         marks: {}, marking: null, blind_done: false },
                       AXIS_DEFAULTS);
}

// ---------------------------------------------------------------------------
// BOUNDARIES
//
// Boundary truth in this project is a CLAUSE: scripts/score_boundary_targets.py asks
// "is the run's boundary at the target clause" and scores HIT / NEAR / MISS on that.
// So the page captures a clause, not a quotation -- one click instead of pasting
// Hebrew, and in the shape the scorer already reads.
//
// Two ways a mark gets made, and the difference between them is the whole point:
//
//   CORRECTION -- he said the extent is wrong, our span is on screen, he points at
//                 the right clause. Circular: our span anchored his answer. Goes in
//                 the corrections set, which answers "did we fix known failures".
//
//   BLIND      -- on a sample, the page asks where the story runs BEFORE our span is
//                 shown at all. Our extent had no part in his answer, so the target
//                 is blind FOR THE BOUNDARY QUESTION even though we chose the passage.
//                 Choosing the passage biases which boundaries get measured; it cannot
//                 flatter the answer within one. Goes in the blind set, which is the
//                 only kind that can catch a regression (Lesson 24, Lesson 23).
//
// The two are recorded apart, per mark, and must never be pooled.
// ---------------------------------------------------------------------------
function nClauses(story, seg) {
  const c = story.clauses && story.clauses[seg];
  return c ? c.length : null;
}

// Which side a click would mark right now. DERIVED rather than stored: the blind pass
// walks start then end, so its state is already implied by which marks exist, and an
// explicit flag that has to be initialised somewhere is a flag that can be forgotten --
// it was, and the first blind card silently swallowed every click.
function markingSide(story, v) {
  if (v.marking) return v.marking;
  if (story.blind_sample && !v.blind_done) return v.marks.start ? 'end' : 'start';
  return null;
}

function pickClause(idx, seg, clause) {
  const story = STORIES[idx];
  const v = get(story);
  const side = markingSide(story, v);
  if (!side) return;
  // A click can only come from a rendered clause, so this cannot fire from the UI --
  // but a target pointing past the end of a segment would be scored as a MISS against
  // a boundary that does not exist, and that is worth making impossible.
  const n = nClauses(story, seg);
  if (n === null || clause < 0 || clause >= n) return;
  v.marks[side] = { segment: seg, clause: clause, n_clauses: nClauses(story, seg),
                    blind: !v.blind_done && !!story.blind_sample };
  // Blind first pass walks start -> end -> done. A correction marks one side only.
  if (!v.blind_done && story.blind_sample) {
    if (side === 'start') { v.marking = 'end'; }
    else { v.marking = null; v.blind_done = true; }
  } else {
    v.marking = null;
  }
  redraw(idx);
}

function skipBlind(idx) {
  const v = get(STORIES[idx]);
  v.blind_done = true; v.blind_skipped = true; v.marking = null;
  redraw(idx);
}

function startMarking(idx, side) {
  const v = get(STORIES[idx]);
  v.marking = (v.marking === side) ? null : side;
  redraw(idx);
}

// One delegated listener for every clause on the page.
function onClauseClick(e) {
  const cl = e.target.closest && e.target.closest('span.cl');
  if (!cl) return;
  const card = cl.closest('.story-card');
  if (!card) return;
  const idx = parseInt(card.id.replace('card-', ''), 10);
  if (!STORIES[idx] || !markingSide(STORIES[idx], get(STORIES[idx]))) return;
  pickClause(idx, parseInt(cl.dataset.s, 10), parseInt(cl.dataset.c, 10));
}

function get(story) {
  if (!verdicts[story.key]) verdicts[story.key] = blank(story);
  return verdicts[story.key];
}

function answer(key, value, idx) {
  const story = STORIES.find(s => s.key === key);
  const v = get(story);
  v.is_story = (v.is_story === value) ? null : value;
  if (v.is_story === 'no' || v.is_story === null) {
    Object.assign(v, AXIS_DEFAULTS);
    v.marking = null;
    // A CORRECTION mark presupposes the passage is a story, so it goes with the axes.
    // A BLIND mark does not -- he made it before knowing our verdict, and it stays.
    Object.keys(v.marks).forEach(k => { if (!v.marks[k].blind) delete v.marks[k]; });
  }
  cursor = idx;
  redraw(idx);
  updateProgress();
}

function setAxis(key, axis, value, idx) {
  const v = get(STORIES.find(s => s.key === key));
  v[axis] = value;
  redraw(idx);
}

function toggleDisplay(key, idx) {
  const v = get(STORIES.find(s => s.key === key));
  v.display_broken = !v.display_broken;
  redraw(idx);
}

function setNote(key, text) { get(STORIES.find(s => s.key === key)).note = text; }

// An entry counts as answered when axis 1 is answered. Nothing else is required.
function answered(story) {
  const v = verdicts[story.key];
  return !!(v && v.is_story);
}

// Anything the reviewer changed away from `right` -- what makes the extra axes worth
// opening automatically next time the card is drawn.
function hasDetail(v) {
  return v.extent !== 'right' || v.confidence !== 'right' || v.grouping !== 'right';
}

// ---------------------------------------------------------------------------
// DIRECTION
//
// `incorrect` used to mean two opposite things depending on what the reviewer was
// shown, and the two were pooled into one precision figure. The label under review is
// on the card, so the direction is not a reconstruction -- it is a lookup, and it is
// written into the saved file (docs/findings/2026-08-31-objection-axis-hand-sort.md).
// ---------------------------------------------------------------------------
function direction(story, v) {
  if (!v.is_story) return null;
  const weSaidStory = story.classification !== 'NOT_A_STORY';
  if (weSaidStory && v.is_story === 'no') return 'over_call';
  if (!weSaidStory && v.is_story === 'yes') return 'under_call';
  if (!weSaidStory && v.is_story === 'borderline') return 'under_call_borderline';
  return 'agrees';
}

// The four historical vocabularies are still what every harness reads, so each new
// verdict also projects onto one. `adjust` is the ruler's existing word for "the story
// is real and the boundary is wrong" and it counts as ACCEPTED -- which is exactly what
// an extent complaint should do, and exactly what the old UI could not say.
function legacyVerdict(v) {
  if (!v.is_story) return null;
  if (v.is_story === 'no') return 'incorrect';
  return (v.extent !== 'right') ? 'adjust' : 'correct';
}

__DISPLAY_JS__

// ---------------------------------------------------------------------------
// RENDER
// ---------------------------------------------------------------------------
function esc_attr(s) { return String(s || '').replace(/"/g, '&quot;'); }

function visible(story) {
  if (activeFilter === 'all') return true;
  if (activeFilter === 'answered') return answered(story);
  if (activeFilter === 'unanswered') return !answered(story);
  if (activeFilter === 'mishnah_withheld') return story.origin === 'mishnah_withheld';
  if (activeFilter === 'boundary_pass') return !!story.blind_sample;
  return story.classification === activeFilter;
}

function setFilter(f, btn) {
  activeFilter = f;
  document.querySelectorAll('.controls button').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');
  render();
}

function render() {
  const container = document.getElementById('storiesContainer');
  container.innerHTML = '';
  STORIES.forEach((story, idx) => {
    if (!visible(story)) return;
    const card = document.createElement('div');
    card.id = 'card-' + idx;
    container.appendChild(card);
    card.outerHTML = buildCard(story, idx);
  });
  updateProgress();
}

function redraw(idx) {
  const el = document.getElementById('card-' + idx);
  if (el) el.outerHTML = buildCard(STORIES[idx], idx);
}

function optRow(key, idx, axis, label, cap, options, current) {
  let html = '<div class="axis-row"><div class="axis-label">' + label + '</div>';
  options.forEach(([val, text]) => {
    const on = (current === val) ? ' on' : '';
    const neutral = (val === 'right') ? ' neutral' : '';
    html += '<button class="opt' + neutral + on + '" onclick="setAxis(\'' + key + '\', \''
          + axis + '\', \'' + val + '\', ' + idx + ')">' + text + '</button>';
  });
  return html + '<div class="axis-cap">' + cap + '</div></div>';
}

// The correction picker: which clause should the story start or end at.
function markRow(story, idx, v) {
  const sides = [];
  if (v.extent === 'starts_wrong' || v.extent === 'both_wrong') sides.push('start');
  if (v.extent === 'ends_wrong' || v.extent === 'both_wrong') sides.push('end');
  let html = '<div class="mark-row">';
  sides.forEach(side => {
    const m = v.marks[side];
    const on = (v.marking === side) ? ' on' : '';
    html += '<button class="mark-btn' + on + '" onclick="startMarking(' + idx + ', \'' + side
          + '\')">' + (m ? '&#10003; ' : '') + 'the story should ' + side
          + (m ? ' at seg ' + m.segment + ', clause ' + (m.clause + 1) : ' here \u2014 click a clause')
          + '</button>';
  });
  html += '<div class="quote-hint">Click the Hebrew clause the story should '
        + sides.join(' / ') + ' at. Clauses are underlined; the one you pick is the unit '
        + 'we measure against.</div></div>';
  return html;
}

// The blind pass: asked BEFORE our span is on screen, so the answer is ours-free.
function blindPrompt(story, idx, v) {
  const side = markingSide(story, v) || 'start';
  const done = v.marks.start ? ' &#10003; start marked.' : '';
  return '<div class="blind-ask">'
    + '<b>Before we show you ours \u2014 where does this story run?</b> '
    + 'Click the Hebrew clause it <b>' + (side === 'start' ? 'begins' : 'ends')
    + '</b> at.' + done
    + ' <button class="skip-btn" onclick="skipBlind(' + idx + ')">skip this</button>'
    + '<div class="quote-hint">You are seeing the passage without our answer marked, on '
    + 'about one story in seven. It is the only way we can tell whether our boundaries '
    + 'are right in general rather than merely fixable when you flag them.</div></div>';
}

function buildCard(story, idx) {
  const v = verdicts[story.key] || blank(story);
  // The blind pass runs BEFORE anything else on the card: no highlight, no verdict
  // buttons, nothing of ours to anchor the answer.
  const blindPass = story.blind_sample && !v.blind_done;
  const isStory = v.is_story;
  const on = x => (isStory === x) ? ' on' : '';
  const cls = ['story-card', 'cls-' + story.classification];
  if (isStory) cls.push('answered');
  if (idx === cursor) cls.push('current');

  // Axes 2-4 exist only while the passage is a story. Hidden AND cleared otherwise.
  let more = '';
  if (isStory === 'yes' || isStory === 'borderline') {
    const open = hasDetail(v);
    more = '<button class="more-link" onclick="document.getElementById(\'more-' + idx
         + '\').classList.toggle(\'hidden\')">'
         + (open ? '&#9662;' : '&#9656;') + ' something else is wrong'
         + (open ? '' : ' (extent, confidence, one story or two)') + '</button>'
         + '<div class="axes-more' + (open ? '' : ' hidden') + '" id="more-' + idx + '">'
         + optRow(story.key, idx, 'extent', 'Extent', 'capability 4 &mdash; boundaries', [
             ['right', 'right'], ['starts_wrong', 'starts wrong'],
             ['ends_wrong', 'ends wrong'], ['both_wrong', 'both']], v.extent)
         + ((v.extent !== 'right') ? markRow(story, idx, v) : '')
         + optRow(story.key, idx, 'confidence', 'Confidence', 'capability 3 &mdash; calibration', [
             ['right', 'right'], ['too_high', 'too high'], ['too_low', 'too low']], v.confidence)
         + optRow(story.key, idx, 'grouping', 'Grouping', 'capability 2 &mdash; detection', [
             ['right', 'right'], ['should_split', 'this is two stories'],
             ['should_merge', 'joins the one next to it']], v.grouping)
         + '</div>';
  }

  return '<div class="' + cls.join(' ') + '" id="card-' + idx + '">'
    + '<div class="story-header">'
    +   '<span class="story-title">' + story.page_ref + ' &nbsp;seg ' + story.start_segment
    +     '&ndash;' + story.end_segment + '</span>'
    +   '<span class="badge cls-' + story.classification + '">we said: '
    +     (story.classification === 'NOT_A_STORY' ? 'not a story'
         : story.classification.toLowerCase().replace('_', ' ')) + '</span>'
    +   (story.origin === 'mishnah_withheld'
        ? '<span class="badge origin-mishnah_withheld">withheld: inside a Mishnah</span>' : '')
    + '</div>'
    + (story.one_sentence_summary
       ? '<div style="font-size:13px;color:#475569;margin-bottom:8px;">'
         + story.one_sentence_summary + '</div>' : '')
    + (blindPass ? blindPrompt(story, idx, v) : '')
    + buildTextDisplay(story, {clauseMode: blindPass || !!markingSide(story, v),
                               hideStory: blindPass,
                               context: blindPass ? 4 : 2})
    // On the blind pass the card stops here. No verdict buttons, no axes, nothing of
    // ours -- so there is nothing on screen for his answer to be anchored on.
    + (blindPass ? '' :
         '<div class="axis1">'
       +   '<span class="q">Is this a story?</span>'
       +   '<button class="big-btn yes' + on('yes') + '" onclick="answer(\'' + story.key
       +     '\', \'yes\', ' + idx + ')">Yes<span class="k">Y</span></button>'
       +   '<button class="big-btn borderline' + on('borderline') + '" onclick="answer(\''
       +     story.key + '\', \'borderline\', ' + idx
       +     ')">Borderline<span class="k">B</span></button>'
       +   '<button class="big-btn no' + on('no') + '" onclick="answer(\'' + story.key
       +     '\', \'no\', ' + idx + ')">Not a story<span class="k">N</span></button>'
       + '</div>'
       + more
       + blindMarkNote(story, v)
       + '<div class="display-row"><button class="display-btn'
       +   (v.display_broken ? ' on' : '') + '" onclick="toggleDisplay(\'' + story.key
       +   '\', ' + idx + ')">&#9888; the page is showing this wrong</button></div>'
       + '<input class="notes-input" placeholder="Anything to add (optional)" value="'
       +   esc_attr(v.note) + '" onchange="setNote(\'' + story.key + '\', this.value)">')
    + '</div>';
}

// After a blind pass, show him what he marked beside what we proposed. He has already
// answered, so this cannot anchor anything -- and seeing the comparison is the part
// that makes the extra two clicks feel worth making.
function blindMarkNote(story, v) {
  const m = v.marks;
  if (!story.blind_sample || !v.blind_done) return '';
  if (v.blind_skipped) return '<div class="blind-done">Boundary pass skipped.</div>';
  const say = (side, fallback) => m[side]
    ? 'seg ' + m[side].segment + ', clause ' + (m[side].clause + 1)
    : fallback;
  return '<div class="blind-done">You marked this story as running from <b>'
       + say('start', '?') + '</b> to <b>' + say('end', '?') + '</b>. '
       + 'We proposed segments ' + story.start_segment + '&ndash;' + story.end_segment
       + '. Recorded as a blind boundary target.</div>';
}

// ---------------------------------------------------------------------------
// KEYBOARD.  batch_review.html built Y/N/S in January 2026 and it was never
// reused; review throughput is the only DERIVED gate this project has.
// ---------------------------------------------------------------------------
function onKey(e) {
  if (/^(INPUT|TEXTAREA)$/.test((e.target.tagName || '').toUpperCase())) return;
  if (e.metaKey || e.ctrlKey || e.altKey) return;
  const shown = STORIES.map((s, i) => [s, i]).filter(([s]) => visible(s));
  const pos = shown.findIndex(([, i]) => i === cursor);
  const k = e.key.toLowerCase();
  if (k === 'y' || k === 'b' || k === 'n') {
    const story = STORIES[cursor];
    if (!story || !visible(story)) return;
    // A card still in its blind boundary pass has no verdict buttons on screen, and a
    // keystroke must not answer a question the reviewer has not been shown.
    if (story.blind_sample && !get(story).blind_done) return;
    answer(story.key, k === 'y' ? 'yes' : k === 'b' ? 'borderline' : 'no', cursor);
    const next = shown[pos + 1];
    if (next) { cursor = next[1]; redraw(cursor); scrollTo_(cursor); }
    e.preventDefault();
  } else if (k === 'j' || k === 'k') {
    const step = shown[pos + (k === 'j' ? 1 : -1)];
    if (step) { const old = cursor; cursor = step[1]; redraw(old); redraw(cursor); scrollTo_(cursor); }
    e.preventDefault();
  }
}

function scrollTo_(idx) {
  const el = document.getElementById('card-' + idx);
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function updateProgress() {
  const n = STORIES.filter(answered).length;
  const bar = document.getElementById('progressFill');
  if (bar) bar.style.width = (n / STORIES.length * 100) + '%';
}

// ---------------------------------------------------------------------------
// SAVE
//
// Every record carries the label under review, the axes, the derived direction and a
// legacy verdict. The legacy field is not politeness -- a round saved in a shape no
// harness reads is a round that scores as if it never happened (Lesson 27).
// ---------------------------------------------------------------------------
function saveResults() {
  const results = {
    schema: SCHEMA,
    tractate: TRACTATE,
    date: new Date().toISOString().split('T')[0],
    source_files: SOURCE_FILES,
    total_stories: STORIES.length,
    reviewed: STORIES.filter(answered).length,
    axes: {
      is_story: ['yes', 'borderline', 'no'],
      extent: ['right', 'starts_wrong', 'ends_wrong', 'both_wrong'],
      confidence: ['right', 'too_high', 'too_low'],
      grouping: ['right', 'should_split', 'should_merge'],
      display_broken: [true, false]
    },
    reviews: {}
  };
  STORIES.forEach((story, idx) => {
    const v = verdicts[story.key];
    if (!v || !v.is_story) return;
    results.reviews[story.key] = {
      index: idx + 1,
      page_ref: story.page_ref,
      start_segment: story.start_segment,
      end_segment: story.end_segment,
      classification: story.classification,
      classification_shown: story.classification,
      origin: story.origin,
      source_file: story.source_file,
      is_story: v.is_story,
      extent: v.extent,
      confidence: v.confidence,
      grouping: v.grouping,
      display_broken: !!v.display_broken,
      direction: direction(story, v),
      verdict: legacyVerdict(v),
      note: v.note || '',
      // Boundary marks, in the unit scripts/score_boundary_targets.py scores.
      // `blind` says whether our span was on screen when he made it, and the two
      // kinds answer different questions -- never pool them (Lesson 24).
      boundary_marks: ['start', 'end'].filter(k => v.marks[k]).map(k => ({
        direction: k,
        segment: v.marks[k].segment,
        clause: v.marks[k].clause,
        n_clauses: v.marks[k].n_clauses,
        blind: !!v.marks[k].blind,
        blind_basis: v.marks[k].blind
          ? 'marked before our span was shown; we chose the passage, not the boundary'
          : 'correction: our span was on screen'
      })),
      blind_pass: !!story.blind_sample,
      blind_pass_skipped: !!v.blind_skipped
    };
  });
  const json = JSON.stringify(results, null, 2);
  document.getElementById('exportData').value = json;
  document.getElementById('exportArea').classList.remove('hidden');
  document.getElementById('exportArea').scrollIntoView({ behavior: 'smooth' });
}

function downloadJSON() {
  const blob = new Blob([document.getElementById('exportData').value],
                        { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = TRACTATE.toLowerCase() + '_review_axes_'
             + new Date().toISOString().split('T')[0] + '.json';
  a.click();
  URL.revokeObjectURL(url);
}

init();
</script>
</body>
</html>"""
            .replace('__DISPLAY_CSS__', DISPLAY_CSS)
            .replace('__DISPLAY_JS__', DISPLAY_JS)
            .replace('__MISHNAH_BANNER__', mishnah_banner)
            .replace('__REJECTED_BANNER__', rejected_banner)
            .replace('__LABEL_STATS__', ''.join(
                f'<div class="stat">{k.lower().replace("_", " ")}: <strong>{n}</strong></div>'
                for k, n in sorted(labels.items())))
            .replace('__FILTER_BUTTONS__', ''.join(
                f'<button onclick="setFilter(\'{k}\', this)">{k.lower().replace("_", " ")}</button>'
                for k in sorted(labels)) + (
                '<button onclick="setFilter(\'mishnah_withheld\', this)">withheld: mishnah</button>'
                if n_mishnah else '') + (
                '<button onclick="setFilter(\'boundary_pass\', this)">boundary pass</button>'
                if n_blind else ''))
            .replace('__N_TOTAL__', str(len(stories)))
            .replace('__BLIND_STAT__',
                     f'<div class="stat">boundary pass: <strong>{n_blind}</strong></div>'
                     if n_blind else '')
            .replace('__SOURCE_FILES__', json.dumps(source_files))
            .replace('__SCHEMA__', SCHEMA)
            .replace('__TITLE__', tractate_title)
            .replace('__STORIES_PLACEHOLDER__', data_json))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--tractate', choices=sorted(TRACTATES), action='append',
                    help='default: every tractate with a run on disk')
    ap.add_argument('--include-rejected', action='store_true',
                    help='also show entries we classified NOT_A_STORY -- the only way to '
                         'measure real stories we threw away')
    ap.add_argument('--out-dir', default=str(OUT_DIR))
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for slug in (args.tractate or sorted(TRACTATES)):
        cfg = TRACTATES[slug]
        paths = [RUN_DIR / n for n in cfg['files']]
        missing = [p for p in paths if not p.exists()]
        if missing:
            print(f'  SKIP {slug}: missing {[str(m.relative_to(ROOT)) for m in missing]}')
            continue
        stories = build_data(paths, include_rejected=args.include_rejected)
        html = generate_html(cfg['title'], stories, cfg['files'])
        out_path = out_dir / cfg['out']
        out_path.write_text(html, encoding='utf-8')
        n_mish = sum(1 for s in stories if s['origin'] == 'mishnah_withheld')
        n_rej = sum(1 for s in stories if s['classification'] == 'NOT_A_STORY')
        print(f'  {slug}: {len(stories)} passages '
              f'({n_mish} withheld-mishnah, {n_rej} we rejected) '
              f'-> {out_path.relative_to(ROOT) if out_path.is_relative_to(ROOT) else out_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
