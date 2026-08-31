#!/usr/bin/env python3
"""
Parse Jeff Rubenstein's Kiddushin story list into a defensible ground-truth JSON.

WHY THIS EXISTS (see tasks/NEXT/05_kiddushin_list_parse.md)
----------------------------------------------------------
`scripts/measure_recall_vs_expert_list.py::parse_expert_doc` reads the .doc as
flat lines produced by `textutil`. That works on the Ketubot list, which is
clean, but on Kiddushin it silently corrupts the data:

  * Word *comments* (annotations) live in a separate text range in the .doc
    binary, so textutil dumps them at the END of the file. Line-based parsing
    then attributes all nine of Jeff's English review notes to whatever daf
    header happened to precede them -- which is why Kiddushin 81b appeared to
    hold eleven stories.
  * The parallels column (mekbilot) is separated from the story column only by
    a heuristic on citation words, so a story that quotes a parallel can be
    dropped and a parallels line that reads like prose can be kept.

This parser reads the OLE compound document directly instead. Legacy .doc
stores the table structure inline -- 0x07 terminates every cell and, again, the
row -- so the four columns (mikom | tekst | mekbilot | he'arot) can be recovered
exactly rather than guessed. Comments come from PlcfandTxt/PlcfandRef with their
true anchor character positions, so each one attaches to the story Jeff was
actually looking at.

Validation: run with --tractate Ketubot on `jeff comms/b.ketubot (1).doc` and it
must return 149 stories -- the count the existing pipeline established. That is
the regression check for this parser; it is asserted by --self-test.

BLINDNESS (FRAMEWORK.md sec.3)
------------------------------
The document was created 2005-02-04 and last saved 2026-08-30, so it is not
purely blind. Two provenance flags are emitted on every story:

  blind: false             -- Jeff marked this himself with `hosafti--y.r.`
                              ("I added -- J.R."). Never counts toward recall.
  in_appendix: true        -- the story is one of the five in
                              `Kiddushin missed stories.docx`, the appendix Jeff
                              merged into his list after reviewing our output.
                              None of the five is blind.
  counts_for_recall: bool  -- whether the entry belongs in the recall
                              denominator, which is a SEPARATE question from
                              blindness. Four appendix cases we proposed
                              ourselves, so counting them could only flatter us;
                              they are excluded. One (81b) we never proposed --
                              Jeff found it in page text our UI displayed -- so
                              it can only count against us and stays in.
                              Dropping a story we missed is what inflates recall.
                              See APPENDIX_DETECTION; re-derive it with
                              `scripts/check_appendix_coverage.py`.

Usage:
  python3 scripts/parse_kiddushin_list.py                       # writes the JSON
  python3 scripts/parse_kiddushin_list.py --self-test           # Ketubot == 149
  python3 scripts/parse_kiddushin_list.py --report              # human-readable dump
"""
import argparse
import json
import logging
import re
import struct
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree

import olefile

PROJECT_ROOT = Path(__file__).parent.parent
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [kiddushin-list] %(message)s',
    handlers=[logging.FileHandler(PROJECT_ROOT / 'project.log'), logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)

CELL = '\x07'          # .doc cell terminator (the last one in a row is the row mark)
ATN_REF = '\x05'       # annotation reference character, sits where the comment anchors
COLUMNS = 5            # mikom | tekst | mekbilot | he'arot | (row mark)
MIN_STORY_WORDS = 8    # verified: the docs contain no story paragraph of 3-7 words

NIKUD = re.compile(r'[֑-ׇ]')
HEBREW_ONLY = re.compile(r'[^א-ת ]')
ADDED_BY_JEFF = re.compile(r'הוספתי')          # "I added"
# `khet ayin-bet`, `khet ayin-bet - tet ayin-alef`, `kaf-vav ayin-alef - ayin-bet`
DAF = re.compile(r'([א-ת]{1,4})?\s*ע["״\']?([אב])(?![א-ת])')
# The one row whose location cell carries several daf labels (mem-he ayin-alef /
# mem-he ayin-bet / mem-vav ayin-bet) so the document alone cannot say which story
# belongs to which. Resolved by anchoring each story's text against Sefaria's
# Kiddushin and reading off the daf -- an objective fact about where a passage sits
# in the Talmud, not a judgement about what counts as a story, so it does not make
# the list any less blind. Keyed by the story's opening words; `ref_source` records
# which entries came through here. Verified 2026-08-30, all matches >= 0.92 coverage.
# Keys are matched against normalize()d opening words, so the vocalised paste and
# the unvocalised original of the same story resolve through one entry. Applied
# only inside a row that carries more than one label.
REF_OVERRIDES = {
    'הנהו בי תרי דהוו קא שתו חמרא':  'Kiddushin 45a',   # 45a seg 5
    'ההוא גברא דקדיש בכישא דירקא':  'Kiddushin 45b',   # 45b seg 1
    'ההוא דאמר לקריבאי':            'Kiddushin 45b',   # 45b seg 3, twice over
}

GEMATRIA = {'א':1,'ב':2,'ג':3,'ד':4,'ה':5,'ו':6,'ז':7,'ח':8,'ט':9,'י':10,'כ':20,'ך':20,
            'ל':30,'מ':40,'ם':40,'נ':50,'ן':50,'ס':60,'ע':70,'פ':80,'ף':80,'צ':90,'ץ':90,
            'ק':100,'ר':200,'ש':300,'ת':400}


# --------------------------------------------------------------------------- .doc


def read_doc(path):
    """Return (main_text, comments) from a legacy Word .doc.

    Word keeps the main document, footnotes, headers and annotations in one
    character stream addressed by CP (character position); the FIB's ccp* fields
    say how long each sub-document is. The piece table (Clx) maps CP ranges onto
    file offsets and says whether each piece is cp1252 or UTF-16.
    """
    ole = olefile.OleFileIO(str(path))
    wd = ole.openstream('WordDocument').read()
    fib_flags = struct.unpack_from('<H', wd, 0x0A)[0]
    table = ole.openstream('1Table' if (fib_flags >> 9) & 1 else '0Table').read()

    ccp_text, ccp_ftn, ccp_hdd, ccp_mcr, ccp_atn = struct.unpack_from('<5i', wd, 0x4C)
    rg = 0x9A                                    # FibRgFcLcb97
    fc_clx, lcb_clx = struct.unpack_from('<Ii', wd, rg + 33 * 8)

    clx = table[fc_clx:fc_clx + lcb_clx]
    i = 0
    while clx[i] == 1:                           # skip any Prc entries
        i += 3 + struct.unpack_from('<h', clx, i + 1)[0]
    cb_pcd = struct.unpack_from('<i', clx, i + 1)[0]
    pcd = clx[i + 5:i + 5 + cb_pcd]
    n_pieces = (cb_pcd - 4) // 12
    cps = struct.unpack_from(f'<{n_pieces + 1}i', pcd, 0)

    pieces = []
    for k in range(n_pieces):
        fc = struct.unpack_from('<I', pcd, 4 * (n_pieces + 1) + k * 8 + 2)[0]
        compressed = bool(fc & 0x40000000)
        fc &= 0x3FFFFFFF
        length = cps[k + 1] - cps[k]
        pieces.append(wd[fc // 2:fc // 2 + length].decode('cp1252', 'replace') if compressed
                      else wd[fc:fc + 2 * length].decode('utf-16-le', 'replace'))
    full = ''.join(pieces)

    comments = []
    if ccp_atn:
        atn = full[ccp_text + ccp_ftn + ccp_hdd + ccp_mcr:][:ccp_atn]
        fc_txt, lcb_txt = struct.unpack_from('<Ii', wd, rg + 5 * 8)
        txt_cps = struct.unpack_from(f'<{lcb_txt // 4}i', table, fc_txt)
        fc_ref, lcb_ref = struct.unpack_from('<Ii', wd, rg + 4 * 8)
        n_ref = (lcb_ref - 4) // 34               # PLC of CPs + 30-byte ATRD records
        ref_cps = struct.unpack_from(f'<{n_ref + 1}i', table, fc_ref)
        for k in range(n_ref):
            body = atn[txt_cps[k]:txt_cps[k + 1]].replace(ATN_REF, '').strip()
            comments.append({'anchor_cp': ref_cps[k], 'text': body})
    return full[:ccp_text], comments


def table_rows(main):
    """Split the flat text into rows of cells, keeping each cell's start CP."""
    cells, start = [], 0
    for i, ch in enumerate(main):
        if ch == CELL:
            cells.append({'cp': start, 'text': main[start:i]})
            start = i + 1
    if len(cells) % COLUMNS:
        log.warning('cell count %d is not a multiple of %d - table shape may differ',
                    len(cells), COLUMNS)
    return [cells[i:i + COLUMNS] for i in range(0, len(cells) // COLUMNS * COLUMNS, COLUMNS)]


def paragraphs(cell):
    """Cell text split into paragraphs, each with its absolute CP.

    The annotation-reference character is dropped from the returned text -- it
    marks where a comment hangs, it is not part of what Jeff wrote -- but it is
    still counted in the CP arithmetic, which is what the anchors are stated in.
    """
    out, cp = [], cell['cp']
    for para in cell['text'].split('\r'):
        out.append({'cp': cp, 'text': para.replace(ATN_REF, '')})
        cp += len(para) + 1
    return out


# ------------------------------------------------------------------------ refs


def gematria(letters):
    letters = re.sub(r'["״\']', '', letters or '')
    return sum(GEMATRIA[c] for c in letters) if letters and all(c in GEMATRIA for c in letters) else None


def parse_daf_label(label, tractate):
    """`khet ayin-bet - tet ayin-alef` -> ['Ketubot 8b', 'Ketubot 9a'].

    A side with no letters before it (`kaf-vav ayin-alef - ayin-bet`) repeats the
    previous daf number.
    """
    refs, number = [], None
    for m in DAF.finditer(label):
        n = gematria(m.group(1)) if m.group(1) else None
        number = n if n is not None else number
        if number is None:
            continue
        refs.append(f"{tractate} {number}{'a' if m.group(2) == 'א' else 'b'}")
    return refs


# --------------------------------------------------------------------- matching


def normalize(text):
    return re.sub(r'\s+', ' ', HEBREW_ONLY.sub(' ', NIKUD.sub('', text))).strip()


def grams(text, n=4):
    flat = normalize(text).replace(' ', '')
    return {flat[i:i + n] for i in range(len(flat) - n + 1)}


def overlap(a, b):
    return len(a & b) / len(a) if a else 0.0


# Which appendix cases our own runs actually proposed, measured 2026-08-30 by
# searching every Kiddushin run for the passage TEXT (not its page reference):
# scripts/check_appendix_coverage.py re-derives this.
#
# It matters because "in the appendix" and "excluded from recall" are not the same
# judgment. An entry that is in Jeff's list BECAUSE we proposed it can only flatter
# our recall, so it must come out of the denominator. An entry he added because he
# saw, on a page we showed him, a story we had MISSED cannot flatter us -- leaving
# it out is what inflates the number. Both are non-blind; only the first is circular
# in the dangerous direction.
APPENDIX_DETECTION = {
    'Kiddushin 33a': (True,  'proposed in every run; seg 6 partial in v7/v8, full at seg 5 from Wave 3 on'),
    'Kiddushin 45a': (True,  'proposed in full from Wave 1 on (absent in v7) -- a genuine Wave 1 win'),
    'Kiddushin 53a': (True,  'proposed but truncated: seg 8 of the segs 8-9 the story occupies'),
    'Kiddushin 71a': (True,  'proposed but truncated: segs 4-5, the tail of the segs 2-5 it occupies'),
    'Kiddushin 81b': (False, 'NEVER proposed by any run. The story is seg 9; we proposed segs 1-3 '
                             'and 14. Jeff found it in the page text our review UI displayed.'),
}


def read_missed_stories(path):
    """`Kiddushin missed stories.docx` -> [{ref, verdict, text}]."""
    ns = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
    with zipfile.ZipFile(path) as z:
        root = ElementTree.fromstring(z.read('word/document.xml'))
    lines = [''.join(t.text or '' for t in p.iter(f'{ns}t')).strip() for p in root.iter(f'{ns}p')]
    entries, pending = [], None
    for line in lines:
        head = re.match(r'^(\d+[ab])\s+(Yes|Low confidence)$', line)
        if head:
            pending = head.groups()
        elif pending and len(line.split()) >= MIN_STORY_WORDS:
            entries.append({'ref': pending[0], 'verdict': pending[1], 'text': line})
            pending = None
    return entries


# ----------------------------------------------------------------------- parse


def parse(doc_path, tractate, missed_path=None):
    main, raw_comments = read_doc(doc_path)
    rows = table_rows(main)

    stories, comments, last_refs = [], [], []
    for r, row in enumerate(rows):
        loc_paras, text_paras = paragraphs(row[0]), paragraphs(row[1])
        labels = [p['text'].strip() for p in loc_paras if DAF.search(p['text'])]
        parallels = ' '.join(p['text'].strip() for p in paragraphs(row[2]) if p['text'].strip())
        note = ' '.join(p['text'].strip() for p in paragraphs(row[3]) if p['text'].strip())

        refs, inherited = [], False
        for label in labels:
            refs += parse_daf_label(label, tractate)
        if not refs and last_refs:
            refs, inherited = last_refs, True
        if refs and labels:
            last_refs = refs

        row_stories = [p for p in text_paras if len(p['text'].split()) >= MIN_STORY_WORDS]
        if row_stories and not refs:
            log.warning('row %d has %d stories but no resolvable daf reference', r, len(row_stories))

        # Header row: no daf reference has been seen yet and none is in this row.
        if not refs:
            continue

        for p in row_stories:
            text = p['text'].strip()
            flat = normalize(text)
            override = next((r for k, r in REF_OVERRIDES.items()
                             if len(labels) > 1 and flat.startswith(normalize(k))), None)
            stories.append({
                'id': f'{tractate.lower()}_{len(stories) + 1:03d}',
                'ref': override or refs[0],
                'ref_source': 'text_anchored' if override else
                              'row_label_inherited' if inherited else 'row_label',
                'ref_candidates': refs,
                'ref_ambiguous': len(labels) > 1,
                'ref_inherited': inherited,
                'ref_hebrew': ' / '.join(labels) if labels else None,
                'row': r,
                'cp': p['cp'],
                'text': p['text'].strip(),
                'words': len(p['text'].split()),
                'parallels': parallels or None,
                'vocalized': bool(NIKUD.search(p['text'])),
                'blind': True,
                'counts_for_recall': True,
                'blind_basis': 'in Jeff\'s list with no marker of later addition; '
                               'never present in detector output he had seen',
                'in_appendix': False,
                'duplicate_of': None,
                'comment_ids': [],
            })

        if note:
            comments.append({'id': f'c_note_{r}', 'kind': 'notes_column', 'row': r,
                             'anchor_cp': row[3]['cp'], 'anchor_column': 3, 'text': note,
                             'ref': refs[0],
                             'attached_story_id': stories[-1]['id'] if row_stories else None,
                             'marks_addition': bool(ADDED_BY_JEFF.search(note))})

    # ---- Word comments: locate each anchor exactly, then attach it -------------
    for k, c in enumerate(raw_comments):
        cp = c['anchor_cp']
        row_index = column = None
        for r, row in enumerate(rows):
            for col, cell in enumerate(row):
                if cell['cp'] <= cp < cell['cp'] + len(cell['text']) + 1:
                    row_index, column = r, col
        in_row = [s for s in stories if s['row'] == row_index]
        # An anchor in the text column sits at the end of the story it comments on;
        # one in the location column labels the row, so fall back to its first story.
        prior = [s for s in in_row if s['cp'] <= cp]
        target = (prior[-1] if prior and column == 1 else in_row[0] if in_row else None)
        comments.append({
            'id': f'c_{k:02d}', 'kind': 'word_comment', 'row': row_index,
            'anchor_cp': cp, 'anchor_column': column, 'text': c['text'],
            'ref': target['ref'] if target else None,
            'attached_story_id': target['id'] if target else None,
            'marks_addition': bool(ADDED_BY_JEFF.search(c['text'])),
        })

    for c in comments:
        if c.get('attached_story_id'):
            next(s for s in stories if s['id'] == c['attached_story_id'])['comment_ids'].append(c['id'])

    # ---- provenance ----------------------------------------------------------
    # Jeff marked exactly what he added. The story he added is the vocalised one
    # (pasted from Sefaria) in the row his marker anchors to.
    for c in comments:
        if not c.get('marks_addition'):
            continue
        candidates = [s for s in stories if s['row'] == c['row'] and s['vocalized']] \
                     or [s for s in stories if s['id'] == c['attached_story_id']]
        for s in candidates:
            s['blind'] = False
            s['blind_basis'] = f"marked `hosafti--y.r.` (I added -- J.R.) by comment {c['id']}"
            c['added_story_id'] = s['id']

    # Duplicates: the same story entered twice (Jeff's 2026 paste beside his 2005 typing).
    # Test containment in both directions -- his paste is a shorter, boundary-trimmed form
    # of the entry he already had, so a symmetric measure misses it. Mark the entry Jeff
    # added as the duplicate so the blind original stays in the recall denominator.
    for i, s in enumerate(stories):
        gs = grams(s['text'])
        for t in stories[:i]:
            gt = grams(t['text'])
            if max(overlap(gs, gt), overlap(gt, gs)) > 0.85:
                dup, keep = (t, s) if (not t['blind'] and s['blind']) else (s, t)
                dup['duplicate_of'] = keep['id']
                break

    if missed_path and Path(missed_path).exists():
        for entry in read_missed_stories(missed_path):
            g = grams(entry['text'])
            best = max(stories, key=lambda s: overlap(g, grams(s['text'])))
            if overlap(g, grams(best['text'])) > 0.6:
                best['in_appendix'] = True
                best['appendix_verdict'] = entry['verdict']
                proposed, evidence = APPENDIX_DETECTION.get(
                    best['ref'], (True, 'not individually checked; assumed ours'))
                best['appendix_detection'] = evidence
                best['blind'] = False
                best['blind_basis'] = (
                    'in `Kiddushin missed stories.docx`, the appendix Jeff merged into his '
                    'list. Not blind: it is there because we put the page in front of him.')
                # Whether it counts toward RECALL is a separate question from whether it
                # is blind -- see APPENDIX_DETECTION.
                best['counts_for_recall'] = not proposed
                best['counts_for_recall_basis'] = (
                    'excluded: we proposed it, so counting it could only flatter recall'
                    if proposed else
                    'INCLUDED: we never proposed it, so it can only count against us. '
                    'Dropping a story we missed is what inflates recall.')
    return stories, comments


# ---------------------------------------------------------------------- output


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--doc', default='jeff comms/8-30-2026/kidushin.doc')
    ap.add_argument('--tractate', default='Kiddushin')
    ap.add_argument('--missed', default='jeff comms/8-30-2026/Kiddushin missed stories.docx')
    ap.add_argument('--out', default='results/expert_lists/kiddushin_2005.json')
    ap.add_argument('--report', action='store_true', help='print a human-readable dump')
    ap.add_argument('--self-test', action='store_true',
                    help='assert the Ketubot list still parses to its established 149')
    args = ap.parse_args()

    if args.self_test:
        ket, ket_comments = parse(PROJECT_ROOT / 'jeff comms/b.ketubot (1).doc', 'Ketubot')
        assert len(ket) == 149, f'Ketubot regression: expected 149 stories, got {len(ket)}'
        assert not ket_comments, f'Ketubot should have no comments, got {len(ket_comments)}'
        log.info('SELF-TEST PASS: Ketubot parses to 149 stories, 0 comments')
        return

    stories, comments = parse(PROJECT_ROOT / args.doc, args.tractate,
                              PROJECT_ROOT / args.missed if args.missed else None)
    blind = [s for s in stories if s['blind']]
    counted = [s for s in stories if s.get('counts_for_recall', s['blind'])]
    flagged = [s for s in stories if s['in_appendix']]
    dupes = [s for s in stories if s['duplicate_of']]
    blind_unique = [s for s in blind if not s['duplicate_of']]
    counted_unique = [s for s in counted if not s['duplicate_of']]

    payload = {
        'tractate': args.tractate,
        'source_document': args.doc,
        'source_created': '2005-02-04',
        'source_last_saved': '2026-08-30',
        'parser': 'scripts/parse_kiddushin_list.py',
        'counts': {
            'table_rows': max(s['row'] for s in stories) + 1,
            'stories': len(stories),
            'blind': len(blind),
            'not_blind': len(stories) - len(blind),
            'duplicates': len(dupes),
            'in_appendix': len(flagged),
            'recall_denominator': len(counted_unique),
            'strictly_blind': len(blind_unique),
            'comments': len(comments),
        },
        'notes': [
            'blind=false means Jeff marked the entry as his own 2026 addition; exclude from recall.',
'in_appendix=true marks the five entries from "Kiddushin missed stories.docx" -- the '
            'appendix Jeff merged into his list. None of the five is BLIND: they are there '
            'because we put the page in front of him. But blindness and the recall '
            'denominator are different questions. Four (33a, 45a, 53a, 71a) we proposed '
            'ourselves, so counting them could only flatter recall -- excluded. One (81b) we '
            'never proposed; Jeff found it in page text our UI displayed. It can only count '
            'AGAINST us, so it stays in the denominator: dropping a story we missed is what '
            'inflates recall. Use recall_denominator.',
            'duplicate_of is set where the same story appears twice; count it once.',
            'ref_ambiguous=true means the row carried more than one daf label and the '
            'per-story reference could not be resolved from the document alone.',
        ],
        'stories': stories,
        'comments': comments,
    }
    out = PROJECT_ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=1))
    log.info('%s: %d stories (%d blind, %d not blind, %d duplicate, %d expert-flagged), '
             '%d comments -> %s', args.tractate, len(stories), len(blind),
             len(stories) - len(blind), len(dupes), len(flagged), len(comments), args.out)
    log.info('recall denominator: %d (%d strictly blind, plus %d appendix case(s) we never proposed)', payload['counts']['recall_denominator'], payload['counts']['strictly_blind'], payload['counts']['recall_denominator'] - payload['counts']['strictly_blind'])

    if args.report:
        print(f"\n{'='*78}\nSTORIES ({len(stories)})\n{'='*78}")
        for s in stories:
            tags = ' '.join(filter(None, [
                '' if s['blind'] else '[NOT BLIND]',
                '[APPENDIX]' if s['in_appendix'] else '',
                f"[DUP of {s['duplicate_of']}]" if s['duplicate_of'] else '',
                '[REF?]' if s['ref_ambiguous'] else '',
                '[VOCALIZED]' if s['vocalized'] else '']))
            print(f"{s['id']}  {s['ref']:16} r{s['row']:<3} {s['words']:3}w {tags}")
            print(f"    {s['text'][:100]}")
        print(f"\n{'='*78}\nCOMMENTS ({len(comments)})\n{'='*78}")
        for c in comments:
            print(f"{c['id']}  {c['kind']:13} row {c['row']:<3} -> {c['attached_story_id']} "
                  f"({c['ref']})")
            print(f"    {c['text'][:160]}")


if __name__ == '__main__':
    main()
