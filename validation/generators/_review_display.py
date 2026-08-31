"""The paired English/Hebrew segment display, shared by every review UI.

There is one copy of this code because there was very nearly two. The Wave 4 page shipped
a display that cut the Hebrew at the detector's char-offsets while showing the English in
full, and gave cross-page stories an English-only continuation block. Both made the page
manufacture its own errors, and both cost Jeff Rubenstein verdicts in the 2026-07-06
round -- one of them sat misfiled as a detector defect for seven weeks (Lesson 25). The
fix was structural: a segment is rendered ONCE, into a single row carrying both its
English and its Hebrew, so no code path can emit one language without the other.

A second generator with its own copy of that code is the same bug waiting. So the CSS and
the JS live here, both pages import them, and `tests/test_review_ui_symmetry.py` runs this
JS under Node against a real fixture -- once per generator that uses it.

Two invariants this module exists to hold:

  * Both languages come from ONE loop iteration over ONE segment range.
  * A proposed span is HIGHLIGHTED inside the full text, never trimmed to (Lesson 25).
    Nothing is hidden, faded or struck through in either language.

`buildTextDisplay` calls two optional hooks, `spanNotice(story)` and `v9Notice(story)`, if
the including page defines them. Wave 4 does; the verdict-axes page does not, because
`results/v10/wave4_notrim/` carries no char-offset spans.

Insert with a placeholder replace rather than an f-string field, so the braces in the CSS
and the JS are never touched by Python's formatter:

    html.replace('__DISPLAY_CSS__', DISPLAY_CSS).replace('__DISPLAY_JS__', DISPLAY_JS)
"""

# --- CSS -------------------------------------------------------------------
DISPLAY_CSS = r"""

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
"""

# --- JS --------------------------------------------------------------------
DISPLAY_JS = r"""
// ---------------------------------------------------------------------------
// TEXT DISPLAY
//
// Invariant: a segment is rendered ONCE, into a single row that carries both
// its English and its Hebrew.  There is no code path that can emit one
// language without the other, and no code path that hides text in either.
//
// This replaces the 2026-07-06 behaviour, which (a) applied the detector's
// Hebrew char-offsets as a visible CUT on the Hebrew while showing the English
// in full, and (b) rendered an "English (continued)" block for cross-page
// stories with no Hebrew counterpart.  Both made the Hebrew look like it
// stopped early next to an English passage that did not.
// ---------------------------------------------------------------------------

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

// The proposed narrower Hebrew range for one segment, or [null,null].
function spanRange(story, segIndex, heb) {
  const ts = story.v10_text_span_start, te = story.v10_text_span_end;
  let lo = 0, hi = heb.length, any = false;
  if (ts && ts.segment === segIndex && ts.char_offset > 0) { lo = ts.char_offset; any = true; }
  if (te && te.segment === segIndex && te.char_offset > 0 && te.char_offset < heb.length) {
    hi = te.char_offset; any = true;
  }
  return any ? [lo, hi] : [null, null];
}

// One block of paired rows.  English and Hebrew are emitted together, from the
// same loop iteration, over the same segment range.
function buildGrid(segs, start, end, story) {
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
    const r = inStory ? spanRange(story, i, heb) : [null, null];
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

// Explain any Hebrew-only annotation in words, so a reviewer is never left
// inferring why one column carries a mark the other does not.
function spanNotice(story) {
  const segs = story.page_segments || [];
  const hebOf = i => { const s = segs.find(x => x.index === i); return s ? (s.hebrew || '') : ''; };
  const parts = [], warns = [];
  [['start', story.v10_text_span_start], ['end', story.v10_text_span_end]].forEach(([which, sp]) => {
    if (!sp) return;
    parts.push(which + ' at seg ' + sp.segment + ', char ' + sp.char_offset);
    if (midWord(hebOf(sp.segment), sp.char_offset)) warns.push(which);
  });
  if (!parts.length) return '';
  let html = '<div class="span-note">The detector proposed a narrower <b>Hebrew</b> span ('
           + parts.join('; ') + '), shaded below. '
           + 'These are Hebrew character offsets with no English counterpart, so the shading '
           + 'appears in the Hebrew column only. '
           + '<b>Both columns show the full text &mdash; nothing is trimmed.</b>';
  if (warns.length) {
    html += ' <span class="warn">&#9888; the ' + warns.join(' and ')
          + ' offset falls mid-word</span> (Wave 4 offsets do this in 55% of cases and were '
          + 'reverted &mdash; treat the shading as unreliable).';
  }
  return html + '</div>';
}

function v9Notice(story) {
  const notes = [];
  const ts = story.v9_text_span_start, te = story.v9_text_span_end;
  if (ts) notes.push('start at seg ' + ts.segment + ', char ' + ts.char_offset
                     + ' (intro: ' + (ts.introducer || '?') + ')');
  if (te) notes.push('end at seg ' + te.segment + ', char ' + te.char_offset
                     + ' (marker: ' + (te.marker || '?') + ')');
  if (!notes.length) return '';
  return '<div class="v9-note">v9 regex span for reference: ' + notes.join('; ')
       + '. Not shaded &mdash; shown as text so it cannot be confused with the displayed extent.</div>';
}

function buildTextDisplay(story) {
  // Optional hooks. A page with no span data defines neither, and the grid below is
  // unaffected -- there is still exactly one path emitting both languages, which is
  // the invariant that matters.
  let html = (typeof spanNotice === 'function') ? spanNotice(story) : '';
  html += buildGrid(story.page_segments || [], story.start_segment, story.end_segment, story);
  html += (typeof v9Notice === 'function') ? v9Notice(story) : '';

  // Cross-page continuation: the SAME builder, so the continuation carries
  // both languages too.  Previously only English continued, which is what
  // Jeff saw on Kiddushin 8b seg 14 ("English right but Hebrew cut off").
  if (story.spans_pages && story.page2_segments) {
    html += '<div class="cont-head">Continues on <b>' + story.spans_pages[1] + '</b></div>';
    html += buildGrid(story.page2_segments,
                      story.start_segment_page2 || 0,
                      story.end_segment_page2 || 0,
                      {});
  }
  return html;
}
"""
