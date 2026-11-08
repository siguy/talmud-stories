#!/usr/bin/env python3
"""Build the page that shows Jeff the 20 Eruvin passages in context, for his verdicts.

Not a detector run: each passage is one of HIS 2005 list entries (see
comms/2026-11-08-email-jeff-eruvin-rulings-DRAFT.md for why these 20). This script wraps
them as a synthetic run -- one "story" per list entry, in the email's group order -- and
hands it to the shared per-axis review UI (generate_axis_review_ui.py), so the display
code is the tested one and Hebrew/English can never disagree (Lesson 25).

The classification label on each card reads FROM YOUR 2005 LIST, so nothing implies the
detector produced these. Answer = the page's required question (story / borderline / no).
"""
import json, re, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent

# email item number -> (list id, group)
ITEMS = [('eruvin_007', 1), ('eruvin_013', 1), ('eruvin_034', 1), ('eruvin_050', 1), ('eruvin_055', 1),
         ('eruvin_063', 1), ('eruvin_064', 1), ('eruvin_008', 2), ('eruvin_014', 2), ('eruvin_019', 2),
         ('eruvin_021', 2), ('eruvin_035', 2), ('eruvin_052', 2), ('eruvin_054', 2), ('eruvin_073', 2),
         ('eruvin_026', 3), ('eruvin_037', 4), ('eruvin_040', 4), ('eruvin_041', 4), ('eruvin_042', 4)]
GROUPS = {1: 'Group 1: one event, then a challenge, a ruling or a discussion',
          2: 'Group 2: scholars talking or sitting, with little or no event',
          3: 'Group 3: one act cited as precedent',
          4: 'Group 4: how a person speaks (wise or precise speech)'}

draft = (ROOT / 'comms/2026-11-08-email-jeff-eruvin-rulings-DRAFT.md').read_text()
desc = {int(m.group(1)): m.group(2) for m in re.finditer(r'^(\d+)\. (.*)$', draft, re.M)}
assert sorted(desc) == list(range(1, 21)), 'email must list items 1..20'

matches = json.loads((ROOT / 'results/recall/eruvin_jeff2005_matches.json').read_text())
rows = matches if isinstance(matches, list) else next(v for v in matches.values() if isinstance(v, list))
loc = {r['id']: r for r in rows}
pages = {p['ref']: p for p in json.loads((ROOT / 'results/sefaria/eruvin.json').read_text())['pages']}

def plain(text):
    """Strip the ref and any editorial aside: the page must not tell him what we think."""
    t = re.sub(r'^Eruvin [0-9]+[ab], ', '', text)
    t = re.sub(r'\s*\([^)]*\)\s*$', '', t)
    return t[0].upper() + t[1:]


out_pages = []
for n, (lid, grp) in enumerate(ITEMS, 1):
    r = loc[lid]
    segs = [i for ref, i in r['located'] if ref == r['located'][0][0]]
    assert len({ref for ref, _ in r['located']}) == 1, f'{lid} spans pages'
    ref = r['located'][0][0]
    out_pages.append({'ref': ref, 'segments': pages[ref]['segments'], 'stories': [{
        'start_segment': min(segs), 'end_segment': max(segs), 'classification': 'FROM YOUR 2005 LIST',
        'one_sentence_summary': f'{GROUPS[grp]}. Item {n} of 20. {plain(desc[n])}',
    }]})
run = ROOT / 'results/rulings_pages/eruvin_2005_rulings_run.json'
run.parent.mkdir(exist_ok=True)
run.write_text(json.dumps({'tractate': 'Eruvin', 'version': 'eruvin-2005-list', 'pages': out_pages},
                          ensure_ascii=False, indent=1))
note = ("These are 20 passages from your 2005 Eruvin list, shown in context. Your later rulings may "
        "disqualify some. For each, the one question that matters is the first one: story, borderline, "
        "or no. Everything else is optional. They are grouped by shape, and the highlighted rows are the "
        "passage as it sits on your list.")
sys.exit(subprocess.call([sys.executable, 'validation/generators/generate_axis_review_ui.py', '--run', str(run),
        '--title', 'Eruvin: 20 passages from your 2005 list', '--out', 'eruvin_2005_rulings.html',
        '--note', note], cwd=ROOT))
