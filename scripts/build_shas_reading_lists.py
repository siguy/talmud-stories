"""Simon's targeted reading lists for the Shas run (plan §2.3), and Jeff's two-run disagreement list.

Reads only what is on disk -- no model calls. For every tractate the driver ran:

  1. THE BIBLICAL LIST. Passages definite (YES/HIGH) in both v14 runs -- the ones the site would ship -- where
       a. exactly one judge called the passage out_of_scope (the judges disagree on whether it is biblical), or
       b. Simon ruled that Claude decides alone (results/shas_run/decisions.json: Gemini answered invalidly twice), or
       c. the unit's summary names a figure on the detector's biblical-name list and no rabbinic signal
          (Stage 4j's own name lists, applied to the summary; the detector applied them to its actor evidence).
     Each entry says whether the site DROPS it (both judges out_of_scope, or Claude alone under the ruling) or SHIPS it.
  2. TEN RANDOM SHIPPED STORIES from every tractate whose G5 density gate is amber (seeded, so it reproduces).
     A G5 amber on the out-of-scope RATE alone is read through list 1, not by random sampling (plan §2.3: targeted).
  3. FOR JEFF, not Simon: passages definite in exactly one run (G4's disagreements), as JSON.

    python3 scripts/build_shas_reading_lists.py        # -> results/shas_run/reading/
"""
import html
import json
import logging
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT))
import check_tractate_run as C  # noqa: E402
import run_shas as R  # noqa: E402
import tractates as T  # noqa: E402
from src.story_detector_v14 import _BIBLICAL_ACTORS, _RABBINIC_SIGNAL, _names_token  # noqa: E402

OUT = ROOT / 'results/shas_run/reading'
RUNS = ('v14_r1', 'v14_r2')
SEED = 20261110
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s [reading-lists] %(message)s',
                    handlers=[logging.StreamHandler(), logging.FileHandler(ROOT / 'project.log')])
log = logging.getLogger('reading-lists')


def verdicts(P, who):
    p = Path(P.consensus) / f'{who}.json'
    if not p.exists():
        return {}
    return {r['id']: r['answer'].get('verdict') for r in json.loads(p.read_text())['rows']
            if r['answer'].get('outcome') == 'ok'}


def names_biblical(summary):
    low = (summary or '').lower()
    if any(_names_token(s, low) for s in _RABBINIC_SIGNAL):
        return []
    return sorted(n for n in _BIBLICAL_ACTORS if _names_token(n, low))


def segments(text, cells):
    """[(ref:index, hebrew, english)] for a unit's cells, from the fetched Sefaria text."""
    out = []
    for ref, i in cells:
        seg = text.get(ref, {}).get(i)
        out.append((f'{ref}:{i}', seg['hebrew'] if seg else '(missing)', seg['english'] if seg else '(missing)'))
    return out


def collect(slug):
    P = T.Paths(slug, ROOT)
    units = json.loads((Path(P.consensus) / 'units.json').read_text())['units']
    g, c = verdicts(P, 'gemini'), verdicts(P, 'claude')
    alone = C.claude_alone(P)
    text = {p['ref']: {s['index']: s for s in p['segments']} for p in json.loads(P.text.read_text())['pages']}
    biblical, shipped, one_run = [], [], []
    for u in units:
        calls = [(u['calls'].get(r) or {}).get('call') for r in RUNS]
        both = all(x == 'story' for x in calls)
        if calls.count('story') == 1:
            one_run.append({'tractate': slug, 'id': u['id'], 'calls': dict(zip(RUNS, calls)), 'summary': u.get('summary'),
                            'cells': u['cells']})
        if not both:
            continue
        gv, cv = g.get(u['id']), c.get(u['id'])
        flagged = gv == 'out_of_scope' or u['id'] in alone
        drops = flagged and cv == 'not'                      # the site's one judge narrowing (Simon 2026-11-10)
        biblical_flag = flagged and cv == 'out_of_scope'      # ships, left out of Jeff's catalogue
        why = []
        if (gv == 'out_of_scope') != (cv == 'out_of_scope') and u['id'] not in alone:
            why.append(f'judges disagree (Gemini {gv}, Claude {cv or "not asked"})')
        if u['id'] in alone:
            why.append(f'Claude decides alone (Simon 2026-11-10): Claude {cv}')
        hits = names_biblical(u.get('summary'))
        if hits:
            why.append('biblical name in summary: ' + ', '.join(hits))
        entry = {'tractate': slug, 'id': u['id'], 'summary': u.get('summary'), 'gemini': gv, 'claude': cv,
                 'site': 'DROPPED' if drops else ('SHIPS, BIBLICAL' if biblical_flag else 'SHIPS'), 'why': why, 'segments': segments(text, u['cells'])}
        if why:
            biblical.append(entry)
        if not drops:
            shipped.append(entry)
    return biblical, shipped, one_run


def g5_density_amber(slug):
    """G5's density warning (pinned to the Berakhot/Yevamot baselines since 2026-11-10, so it cannot drift)."""
    return any('per examined page' in w for w in C.g5_density(T.Paths(slug, ROOT)).warnings)


def card(e):
    segs = ''.join(f'<tr><td class=ref>{html.escape(r)}</td><td class=he dir=rtl>{h}</td><td class=en>{en}</td></tr>'
                   for r, h, en in e['segments'])
    why = ''.join(f'<li>{html.escape(w)}</li>' for w in e.get('why', []))
    return (f'<section class="card {e["site"].split(",")[0].lower()}"><h3>{html.escape(e["id"])} <span class=tag>{e["site"]}</span></h3>'
            f'<p class=sum>{html.escape(e.get("summary") or "")}</p><ul>{why}</ul>'
            f'<p class=j>Gemini: {e.get("gemini")} · Claude: {e.get("claude") or "not asked"}</p>'
            f'<table>{segs}</table></section>')


def page(biblical, samples):
    css = """:root{--bg:#fff;--fg:#1a1a1a;--mute:#666;--line:#ddd;--drop:#b3261e;--ship:#1b6e3a}
@media (prefers-color-scheme:dark){:root{--bg:#161616;--fg:#eee;--mute:#aaa;--line:#333;--drop:#f2847a;--ship:#7fd49b}}
body{background:var(--bg);color:var(--fg);font:16px/1.5 system-ui,sans-serif;margin:0 auto;max-width:1100px;padding:16px}
.card{border:1px solid var(--line);border-radius:8px;padding:12px;margin:12px 0}.tag{font-size:12px;padding:2px 6px;border-radius:4px;border:1px solid}
.dropped .tag{color:var(--drop)}.ships .tag{color:var(--ship)}.sum,.j{color:var(--mute);margin:4px 0}
table{border-collapse:collapse;width:100%}td{border-top:1px solid var(--line);padding:6px;vertical-align:top}
.ref{white-space:nowrap;color:var(--mute);font-size:13px}.he{font-family:'SBL Hebrew','Times New Roman',serif;font-size:19px;width:45%}
@media (max-width:700px){td{display:block;width:auto!important}.ref{border:0}}"""
    by_t = {}
    for e in biblical:
        by_t.setdefault(e['tractate'], []).append(e)
    parts = [f'<h1>Shas run: reading lists</h1><p>{len(biblical)} passages on the biblical list; '
             f'{sum(len(v) for v in samples.values())} spot-check stories from the sparsest tractates. '
             'Every passage below is definite in both runs. SHIPS = on the site; SHIPS, BIBLICAL = on the site, flagged and left out of Jeff&#39;s catalogue; DROPPED = Gemini says biblical and Claude says not a story.</p>',
             '<h2>1. The biblical list</h2><p>Is each one flagged right? A biblical story stays on the site either way; '
             'the flag only keeps it out of Jeff&#39;s catalogue.</p>']
    for t, es in by_t.items():
        es = sorted(es, key=lambda e: e['site'] != 'SHIPS')      # what ships first: that is what a reader sees
        parts.append(f'<h3>{T.SLUGS[t]["english"]} ({len(es)})</h3>' + ''.join(card(e) for e in es))
    parts.append('<h2>2. Spot-check: the sparsest tractates</h2><p>These four tractates have far fewer stories per page '
                 'than the rest, so up to ten of the stories the site shows from each were picked at random. All are '
                 'on the site. The question for each: <b>is this really a story?</b> If most are, the low count is the '
                 'tractate (mostly law), not the detector failing.</p>')
    for t, es in samples.items():
        parts.append(f'<h3>{T.SLUGS[t]["english"]}</h3>' + ''.join(card(e) for e in es))
    return (f'<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">'
            f'<title>Shas reading lists</title><style>{css}</style>' + ''.join(parts))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    biblical, samples, jeff = [], {}, []
    for slug in R.default_tractates():
        try:
            b, shipped, one = collect(slug)
        except FileNotFoundError as e:
            log.warning('%s: skipped, input missing (%s)', slug, e)
            continue
        biblical += b
        jeff += one
        if g5_density_amber(slug):
            samples[slug] = random.Random(f'{SEED}-{slug}').sample(shipped, min(10, len(shipped)))
        log.info('%s: %d biblical-list, %d shipped, %d one-run', slug, len(b), len(shipped), len(one))
    (OUT / 'reading_lists.html').write_text(page(biblical, samples))
    (OUT / 'biblical_list.json').write_text(json.dumps(biblical, ensure_ascii=False, indent=1))
    (OUT / 'jeff_two_run_disagreements.json').write_text(json.dumps(jeff, ensure_ascii=False, indent=1))
    log.info('biblical list %d (%d dropped), samples %s, Jeff one-run list %d', len(biblical),
             sum(e['site'] == 'DROPPED' for e in biblical), {k: len(v) for k, v in samples.items()}, len(jeff))


if __name__ == '__main__':
    main()
