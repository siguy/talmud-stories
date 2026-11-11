"""Stories the Bavli tells in more than one tractate: near-verbatim retellings, and the same story told differently.

Jeff's 2005 lists carry a "parallels" column (מקבילות) for exactly this. Nothing here feeds the site; it is a finding
and a page to browse.

What is compared: every story the site ships, PLUS every story v14 proposed in run 1 of an unreviewed tractate
(YES, HIGH, BORDERLINE or LOW; never NOT_A_STORY or mishnah_stories) -- the site is definite-only, but a parallel is
interesting whatever its grade. Hebrew is stripped of vowels, cantillation and punctuation; each story becomes a set
of 5-word shingles; two stories in DIFFERENT tractates are a pair when they share at least 30% of the smaller one's
shingles. No model calls.

    near-verbatim     >= 80% shared
    different framing 30-80% shared  (the same core told with other words around it)

    python3 scripts/find_cross_tractate_parallels.py   # -> results/parallels/{pairs.json, parallels.html}
"""
import html
import json
import logging
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
import tractates as T  # noqa: E402

OUT = ROOT / 'results/parallels'
STRIP = re.compile(r'[֑-ׇ]|<[^>]+>|[^א-ת\s]')
N, MIN_SHINGLES, PAIR, VERBATIM = 5, 8, 0.30, 0.80
MAX_DF, MIN_SHARED = 4, 8      # a shingle in more than 4 stories is a formula; a pair shares at least 8 shingles
GRADES = ('YES', 'HIGH_CONFIDENCE', 'BORDERLINE', 'LOW_CONFIDENCE')
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s [parallels] %(message)s',
                    handlers=[logging.StreamHandler(), logging.FileHandler(ROOT / 'project.log')])
log = logging.getLogger('parallels')


def shingles(text):
    w = STRIP.sub(' ', text or '').split()
    return {' '.join(w[i:i + N]) for i in range(len(w) - N + 1)}


def site_stories():
    out = []
    for row in json.loads((ROOT / 'site/data/index.json').read_text())['tractates']:
        for s in json.loads((ROOT / f"site/data/{row['tractate']}.json").read_text())['stories']:
            out.append({'id': s['id'], 'tractate': row['tractate'], 'on_site': True, 'grade': s.get('classification'),
                        'summary': s.get('summary', ''),
                        'segments': [{'ref': g['ref'], 'i': g['i'], 'he': g['he'], 'en': g['en']} for g in s['segments']]})
    return out


def run_stories(slug, seen):
    """Proposed stories in run 1 that the site does not already carry (same id)."""
    P = T.Paths(slug, ROOT)
    if not P.run(1).exists():
        return []
    from build_site_data import pieces          # the site's own reading of a (cross-page) story
    pages = json.loads(P.run(1).read_text())['pages']
    out = []
    for i, p in enumerate(pages):
        for s in p.get('stories', []):       # never mishnah_stories[]: withheld by Stage 4g
            if s.get('classification') not in GRADES:
                continue
            sid = f"{slug}-{p['ref'].split()[-1]}-{s['start_segment']}-{s['end_segment']}"
            if sid in seen:
                continue
            out.append({'id': sid, 'tractate': slug, 'on_site': False, 'grade': s.get('classification'),
                        'summary': s.get('one_sentence_summary', ''),
                        'segments': [{'ref': r, 'i': g.get('index'), 'he': g.get('hebrew'), 'en': g.get('english')}
                                     for r, gs in pieces(pages, i, s) for g in gs]})
    return out


def main():
    stories = site_stories()
    seen = {s['id'] for s in stories}
    for slug in T.SLUGS:
        stories += run_stories(slug, seen)
    sh = [shingles(' '.join(g['he'] or '' for g in s['segments'])) for s in stories]
    # A five-word run found in more than MAX_DF stories is a formula ("Rabbi X said in the name of Rabbi Y"), a
    # stock legal phrase or a verse -- not evidence that two stories are one. A real retelling recurs 2-4 times.
    df = {}
    for s_ in sh:
        for x in s_:
            df[x] = df.get(x, 0) + 1
    sh = [{x for x in s_ if df[x] <= MAX_DF} for s_ in sh]
    keep = [k for k in range(len(stories)) if len(sh[k]) >= MIN_SHINGLES]
    index = {}
    for k in keep:
        for x in sh[k]:
            index.setdefault(x, []).append(k)
    pairs = []
    for k in keep:
        shared = {}
        for x in sh[k]:
            for j in index[x]:
                if j > k and stories[j]['tractate'] != stories[k]['tractate']:
                    shared[j] = shared.get(j, 0) + 1
        for j, n in shared.items():
            ov = n / min(len(sh[k]), len(sh[j]))
            if ov >= PAIR and n >= MIN_SHARED:
                pairs.append({'a': k, 'b': j, 'shared': round(ov, 3),
                              'kind': 'near-verbatim' if ov >= VERBATIM else 'different framing'})
    pairs.sort(key=lambda p: -p['shared'])
    OUT.mkdir(parents=True, exist_ok=True)
    slim = lambda s: {k: s[k] for k in ('id', 'tractate', 'on_site', 'grade', 'summary')}
    (OUT / 'pairs.json').write_text(json.dumps(
        [{**{k: p[k] for k in ('shared', 'kind')}, 'a': slim(stories[p['a']]), 'b': slim(stories[p['b']])}
         for p in pairs], ensure_ascii=False, indent=1))
    (OUT / 'parallels.html').write_text(page(stories, pairs))
    n_v = sum(p['kind'] == 'near-verbatim' for p in pairs)
    both_site = sum(stories[p['a']]['on_site'] and stories[p['b']]['on_site'] for p in pairs)
    log.info('%d stories compared (%d on the site); %d pairs: %d near-verbatim, %d different framing; %d with both '
             'sides on the site', len(keep), sum(s['on_site'] for s in stories), len(pairs), n_v, len(pairs) - n_v,
             both_site)


def side(s):
    rows = ''.join(f'<p class=he dir=rtl>{g["he"] or ""}</p>' for g in s['segments'])
    en = ''.join(f'<p class=en>{g["en"] or ""}</p>' for g in s['segments'])
    tag = 'on the site' if s['on_site'] else f'not on the site ({s["grade"]})'
    return (f'<div class=side><h4>{T.SLUGS[s["tractate"]]["english"]} · {html.escape(s["segments"][0]["ref"])} '
            f'<span class=tag>{tag}</span></h4><p class=sum>{html.escape(s["summary"] or "")}</p>'
            f'<details><summary>Hebrew and English</summary>{rows}{en}</details></div>')


def page(stories, pairs):
    css = """:root{--bg:#fff;--fg:#1a1a1a;--mute:#666;--line:#ddd;--acc:#1b4f8a}
@media (prefers-color-scheme:dark){:root{--bg:#161616;--fg:#eee;--mute:#aaa;--line:#333;--acc:#8fb8ea}}
body{background:var(--bg);color:var(--fg);font:16px/1.5 system-ui,sans-serif;margin:0 auto;max-width:1150px;padding:16px}
.pair{border:1px solid var(--line);border-radius:8px;padding:12px;margin:14px 0}.pair>h3{margin:0 0 8px;font-size:15px;color:var(--acc)}
.sides{display:grid;grid-template-columns:1fr 1fr;gap:16px}@media (max-width:760px){.sides{grid-template-columns:1fr}}
h4{margin:0;font-size:15px}.tag{font-weight:400;font-size:12px;color:var(--mute)}.sum{color:var(--mute);margin:4px 0}
.he{font-family:'SBL Hebrew','Times New Roman',serif;font-size:18px;margin:4px 0}.en{font-size:14px;margin:4px 0}"""
    groups = {'near-verbatim': [], 'different framing': []}
    for p in pairs:
        groups[p['kind']].append(p)
    blurb = {'near-verbatim': 'The same story, told in nearly the same words, in two tractates (80% or more of the '
                              'Hebrew shared).',
             'different framing': 'The same core told with other words around it: a different setting, a longer '
                                  'or shorter telling, another rabbi named (30–80% shared). This is where the '
                                  'interesting differences are.'}
    parts = [f'<h1>Stories told twice</h1><p>{len(pairs)} pairs of stories in different tractates that share Hebrew, '
             'found by matching five-word sequences. Includes stories the family site does not show.</p>']
    for kind, ps in groups.items():
        parts.append(f'<h2>{kind.capitalize()} ({len(ps)})</h2><p>{blurb[kind]}</p>')
        for p in ps:
            parts.append(f'<section class=pair><h3>{round(100 * p["shared"])}% shared</h3><div class=sides>'
                         f'{side(stories[p["a"]])}{side(stories[p["b"]])}</div></section>')
    return (f'<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">'
            f'<title>Stories told twice</title><style>{css}</style>' + ''.join(parts))


if __name__ == '__main__':
    main()
