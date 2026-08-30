#!/usr/bin/env python3
"""
Compare two Wave 5 clause-span runs (e.g. two different Gemini models).

Reports, for each arm:
  1. Structural invariant  — mid-word cuts (MUST be 0) and clause-edge rate
  2. Expert agreement      — vs Jeff's stated boundaries in
                             tests/wave5_expert_clause_fixture.json
  3. Trim behaviour        — how often the arm trims at all
and the per-story agreement between the two arms.

The expert fixture is a DEVELOPMENT signal for choosing between arms. It is NOT
a ship gate: 8 hand-picked cases cannot predict production behaviour
(Lessons 9, 18). Ship gates live in scripts/audit_text_spans.py and
scripts/evaluate_golden.py.

Usage:
  python3 scripts/compare_wave5_arms.py --arms A=results/... B=results/...
"""
import argparse
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


def load_arm(path):
    data = json.loads(Path(path).read_text())
    stories, segs = {}, {}
    for page in data['pages']:
        segs[page['ref']] = {s['index']: s['hebrew'] for s in page.get('segments', [])}
        for s in page.get('stories', []):
            key = f"{page['ref']}|{s['start_segment']}-{s['end_segment']}"
            stories[key] = s
    return data, stories, segs


def structural(stories, segs):
    import re
    brk = re.compile(r'(?<=[\.\:\?\!])\s+')
    cuts = midword = edge = 0
    for key, s in stories.items():
        ref = key.split('|')[0]
        for side in ('text_span_start', 'text_span_end'):
            sp = s.get(side)
            if not sp:
                continue
            h = segs.get(ref, {}).get(sp['segment'])
            off = sp.get('char_offset')
            if h is None or off is None:
                continue
            cuts += 1
            starts, ends = {0}, {len(h)}
            for m in brk.finditer(h):
                ends.add(m.start()); starts.add(m.end())
            if off in (starts if side.endswith('start') else ends):
                edge += 1
            if 0 < off < len(h):
                b, a = h[off - 1], h[off]
                if not (b.isspace() or a.isspace() or b in '.:?!,״׳()[]–' or a in '.:?!,״׳()[]–'):
                    midword += 1
    return cuts, midword, edge


def expert_score(stories, segs):
    """Score an arm against Jeff's stated boundaries.

    A story with no text_span_start starts at clause 0; one with no
    text_span_end ends at the LAST clause of its end segment. Both mean
    "no trim" — they must be resolved against the real clause count, not
    treated as clause 0.
    """
    import sys as _sys
    _sys.path.insert(0, str(PROJECT_ROOT))
    from src.story_detector_v11 import _split_into_clauses

    fx = json.loads((PROJECT_ROOT / 'tests' / 'wave5_expert_clause_fixture.json').read_text())
    rows, ok = [], 0
    for c in fx['cases']:
        s = stories.get(f"{c['ref']}|{c['story']}")
        if not s:
            rows.append((c['ref'], c['story'], 'MISSING', '')); continue
        end_seg = s['end_segment']
        n_end = len(_split_into_clauses(segs.get(c['ref'], {}).get(end_seg, '')))
        got_s = (s.get('text_span_start') or {}).get('clause_index', 0)
        end = s.get('text_span_end')
        got_e = end.get('clause_index') if end else (n_end - 1 if n_end else None)
        pass_s = got_s in c['start_clause']
        pass_e = got_e in c['end_clause'] if got_e is not None else False
        ok += bool(pass_s and pass_e)
        rows.append((c['ref'], c['story'],
                     f"start {got_s}{'OK' if pass_s else 'X '} want{c['start_clause']}",
                     f"end {got_e}{'OK' if pass_e else 'X '} want{c['end_clause']}"))
    return ok, len(fx['cases']), rows


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--arms', nargs='+', required=True, help='NAME=path ...')
    args = ap.parse_args()

    arms = {}
    for spec in args.arms:
        name, path = spec.split('=', 1)
        arms[name] = load_arm(path)

    print(f"{'arm':10s} {'model':22s} {'think':7s} {'trim':>6s} {'full':>6s} {'skip':>5s} "
          f"{'cuts':>5s} {'midword':>8s} {'edge':>6s} {'expert':>8s} {'sec':>6s}")
    for name, (data, stories, segs) in arms.items():
        st = data.get('wave5_stats', {})
        c = st.get('clause_span_counts', {})
        cuts, mw, edge = structural(stories, segs)
        ok, tot, _ = expert_score(stories, segs)
        print(f"{name:10s} {str(st.get('model')):22s} {str(st.get('thinking_level')):7s} "
              f"{c.get('clause_llm', 0):6d} {c.get('clause_kept_full', 0):6d} {c.get('skipped', 0):5d} "
              f"{cuts:5d} {mw:8d} {edge:6d} {ok:4d}/{tot:<3d} {st.get('elapsed_seconds', 0):6.0f}")

    names = list(arms)
    if len(names) == 2:
        a, b = arms[names[0]][1], arms[names[1]][1]
        both = set(a) & set(b)
        same = sum(1 for k in both
                   if (a[k].get('text_span_start') or {}).get('char_offset') == (b[k].get('text_span_start') or {}).get('char_offset')
                   and (a[k].get('text_span_end') or {}).get('char_offset') == (b[k].get('text_span_end') or {}).get('char_offset'))
        print(f"\nagreement between {names[0]} and {names[1]}: {same}/{len(both)} stories identical ({same/len(both):.0%})")

    for name, (_, stories, segs) in arms.items():
        ok, tot, rows = expert_score(stories, segs)
        print(f"\n--- {name}: expert cases {ok}/{tot} ---")
        for r in rows:
            print(f"  {r[0]:14s} {r[1]:7s} {r[2]:26s} {r[3]}")


if __name__ == '__main__':
    main()
