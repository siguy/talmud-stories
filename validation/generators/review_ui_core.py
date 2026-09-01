"""The review UI's display core — one segment, one row, both languages.

Shared by every review UI generator. Extracted from
`generate_wave4_review_ui.py` on 2026-08-31 unchanged, so that a second
generator inherits the display guarantee **by construction** rather than by
re-implementing it. The extraction is proved safe by
`tests/test_review_ui_symmetry.py`, which executes this JavaScript under Node
and still passes against the wave 4 page.

THE INVARIANT, and why it is structural rather than careful
-----------------------------------------------------------
A segment is rendered ONCE, into a single row that holds BOTH its English and
its Hebrew. No code path can emit one language without the other, and none
hides, fades, trims or strikes through text in either. A narrower proposed
span is an ANNOTATION (`<mark>`) layered on top, never a cut.

Both display bugs this replaces cost Jeff Rubenstein real attention in the
2026-07-06 round — he wrote "the Hebrew doesn't match" notes about defects in
our own renderer rather than about detector output (Lesson 25). 3 of his
verdicts across two rounds were spent that way. A display bug does not merely
waste a reviewer's time: it manufactures expert feedback that then has to be
disbelieved.

`buildGrid` takes a `spanRangeFn` hook so a generator that has no spans to
annotate (anything reading `results/v10/wave4_notrim/`) passes `null` and gets
plain full text, without a second copy of the row builder existing anywhere.

The strings below are plain Python strings with SINGLE braces: they are spliced
into the generated page by `.replace()`, never through an f-string, so brace
doubling cannot creep back in.
"""
from __future__ import annotations

DISPLAY_JS = r'''
// Sefaria markup we keep (it carries meaning: bold = the Talmud's own words in
// the English, <big><strong> = the mishnah opening in the Hebrew).  Anything
// else is escaped rather than executed.
const INLINE_OK = { B: 1, STRONG: 1, I: 1, EM: 1, BIG: 1, SMALL: 1, BR: 1 };

function esc(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// Split raw Sefaria markup into tag / text tokens, remembering each token's
// offset in the RAW string -- the detector's char_offsets index the raw string
// (tags included), and scripts/audit_text_spans.py reads them the same way.
function tokenize(raw) {
  const out = [];
  const re = /<[^>]*>/g;
  let last = 0, m;
  while ((m = re.exec(raw)) !== null) {
    if (m.index > last) out.push({ tag: false, v: raw.slice(last, m.index), at: last });
    out.push({ tag: true, v: m[0], at: m.index });
    last = re.lastIndex;
  }
  if (last < raw.length) out.push({ tag: false, v: raw.slice(last), at: last });
  return out;
}

// Render raw markup in full.  If [lo,hi) is given, the characters inside that
// raw-offset range are wrapped in <mark> -- an annotation, never a cut.
// Tags are never split, and <mark> is closed before any tag so nesting stays
// valid.
function renderMarkup(raw, lo, hi) {
  raw = raw || '';
  const marking = (lo !== null && lo !== undefined && hi !== null && hi !== undefined);
  let html = '', open = false;
  const openMark = () => { if (!open) { html += '<mark class="span-in">'; open = true; } };
  const closeMark = () => { if (open) { html += '</mark>'; open = false; } };
  tokenize(raw).forEach(tok => {
    if (tok.tag) {
      closeMark();
      const name = (tok.v.match(/^<\/?\s*([a-zA-Z0-9]+)/) || [])[1];
      html += (name && INLINE_OK[name.toUpperCase()]) ? tok.v : esc(tok.v);
      return;
    }
    if (!marking) { html += esc(tok.v); return; }
    for (let k = 0; k < tok.v.length; k++) {
      const abs = tok.at + k;
      if (abs >= lo && abs < hi) openMark(); else closeMark();
      html += esc(tok.v[k]);
    }
  });
  closeMark();
  return html;
}

// Same word-boundary test as scripts/audit_text_spans.py, so the UI agrees
// with the structural gate about what counts as a mid-word cut.
const BREAKERS = '.:?!,״׳()[]–—';
function midWord(heb, off) {
  if (!heb || off <= 0 || off >= heb.length) return false;
  const a = heb[off - 1], b = heb[off];
  if (/\s/.test(a) || /\s/.test(b)) return false;
  return BREAKERS.indexOf(a) === -1 && BREAKERS.indexOf(b) === -1;
}

// One block of paired rows.  English and Hebrew are emitted together, from the
// same loop iteration, over the same segment range.
function buildGrid(segs, start, end, story, spanRangeFn) {
  if (!segs || !segs.length) return '';
  const maxIdx = segs.reduce((m, s) => Math.max(m, s.index), 0);
  const showStart = Math.max(0, start - 2);
  const showEnd = Math.min(maxIdx, end + 2);
  let rows = '';
  for (let i = showStart; i <= showEnd; i++) {
    const seg = segs.find(s => s.index === i);
    if (!seg) continue;
    const inStory = (i >= start && i <= end);
    const cls = ['seg-row', inStory ? 'story' : 'context'];
    if (i === start) cls.push('story-first');
    if (i === end) cls.push('story-last');
    const heb = seg.hebrew || '';
    const r = (inStory && spanRangeFn) ? spanRangeFn(story, i, heb) : [null, null];
    rows += '<div class="' + cls.join(' ') + '">'
          +   '<div class="seg-num">' + i + '</div>'
          +   '<div class="seg-en">' + renderMarkup(seg.english || '', null, null) + '</div>'
          +   '<div class="seg-he">' + renderMarkup(heb, r[0], r[1]) + '</div>'
          + '</div>';
  }
  return '<div class="text-block">'
       +   '<div class="seg-head"><div class="seg-num">#</div>'
       +     '<div class="seg-en">English</div><div class="seg-he">Hebrew</div></div>'
       +   rows
       + '</div>';
}


// Cross-page continuation, built by the SAME grid builder, so the continuation
// carries both languages too.  Previously only English continued, which is what
// Jeff saw on Kiddushin 8b seg 14 ("English right but Hebrew cut off").
function buildContinuation(story) {
  if (!(story.spans_pages && story.page2_segments)) return '';
  return '<div class="cont-head">Continues on <b>' + story.spans_pages[1] + '</b></div>'
       + buildGrid(story.page2_segments,
                   story.start_segment_page2 || 0,
                   story.end_segment_page2 || 0,
                   {}, null);
}

'''


DISPLAY_CSS = r'''
  .text-block { background: #fafbfc; padding: 12px 14px; border-radius: 8px;
                 margin-top: 10px; border: 1px solid #e5e8ec; }
  .text-block h4 { font-size: 12px; text-transform: uppercase; letter-spacing: 0.6px;
                   color: #6c7a89; margin-bottom: 8px; font-weight: 600; }

  /* ---------------------------------------------------------------------
     PAIRED SEGMENT ROWS.  One segment = ONE row that holds BOTH languages.
     English and Hebrew for a given segment are siblings in the same DOM
     node, so the two columns cannot show different extents.  This is the
     structural fix for the 2026-07-06 asymmetry: previously the Hebrew was
     trimmed by char-offset while the English was shown in full, and
     cross-page stories got an English continuation block but no Hebrew one.
     Nothing is ever hidden, faded or struck through in either language.
     --------------------------------------------------------------------- */
  .seg-head { display: flex; gap: 10px; align-items: flex-start;
               padding: 0 10px 6px; font-size: 11px; font-weight: 600;
               text-transform: uppercase; letter-spacing: 0.6px; color: #6c7a89; }
  .seg-row { display: flex; gap: 10px; align-items: flex-start;
              padding: 7px 10px; border-top: 1px solid #eef1f4; }
  .seg-num { flex: 0 0 26px; font-family: monospace; font-size: 12px;
              color: #94a3b8; padding-top: 3px; text-align: right; }
  .seg-en { flex: 1 1 0; min-width: 0; font-size: 14px; }
  .seg-he { flex: 1 1 0; min-width: 0; direction: rtl; text-align: right;
             font-size: 18px; line-height: 1.75;
             font-family: 'SBL Hebrew', 'Times New Roman', serif; }
  .seg-row.context .seg-en, .seg-row.context .seg-he { color: #a3adb8; }
  .seg-row.context { background: #fbfcfd; }
  .seg-row.story { background: #fffbe6; }
  .seg-row.story .seg-num { color: #8a6d1f; font-weight: 700; }
  .seg-row.story-first { border-top: 2px solid #d4a017; }
  .seg-row.story-last { border-bottom: 2px solid #d4a017; }
  @media (max-width: 900px) {
    .seg-row { flex-wrap: wrap; }
    .seg-en, .seg-he { flex: 1 1 100%; }
  }

  /* A proposed narrower span is an ANNOTATION on the Hebrew, never a cut. */
  mark.span-in { background: #fde68a; color: inherit; border-radius: 2px;
                  box-shadow: inset 0 -2px 0 #d97706; padding: 0 1px; }
  .span-note { background: #fffaf0; border: 1px solid #fbd38d; color: #7c4a03;
                padding: 8px 12px; border-radius: 6px; font-size: 12.5px;
                margin-top: 10px; line-height: 1.5; }
  .span-note .warn { color: #9b2c2c; font-weight: 700; }
  .v9-note { background: #f7fafc; border: 1px solid #e2e8f0; padding: 6px 10px;
              margin-top: 6px; border-radius: 4px; font-size: 12px; color: #4a5568; }
  .cont-head { margin-top: 14px; padding-top: 10px; border-top: 1px dashed #cbd5e1;
                font-size: 12px; color: #64748b; }
  .legend { font-size: 12px; color: #6c7a89; margin-top: 14px; line-height: 1.6; }
  .legend .sw { display: inline-block; width: 12px; height: 12px; vertical-align: -2px;
                 border-radius: 3px; margin-right: 4px; }

'''
