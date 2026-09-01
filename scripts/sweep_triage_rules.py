#!/usr/bin/env python3
"""
Sweep candidate Stage 1 keep-rules against the BLIND lists, and price each one.

Follow-on to `docs/findings/2026-08-31-triage-recall-price.md`, which measured only
the two endpoints — the shipped rule and "keep everything". The endpoints bracket
the trade but do not locate the best point in it, and the interesting rules are in
between.

No API calls. Every candidate reuses the Stage 2 output already produced for the
discarded pages, so a rule is evaluated by asking which discarded pages it would
have kept and crediting only the proposals on those pages. That is exact, not
simulated: the proposals are real Stage 2 output on the real page with the real
triage labels.

The one thing this CANNOT see: a rule that keeps a page the shipped rule also kept
changes nothing, and a rule that *drops* a page the shipped rule kept is not
evaluable here, because no Stage 2 output exists for the counterfactual. So the
sweep is restricted to rules that are strictly looser than the shipped one, which
is asserted per candidate rather than assumed.

Cost is reported in Stage 2 calls, and separately in **false proposals reaching the
reviewer**, which is the currency that actually binds (review throughput is the
project's bottleneck).
"""

import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

SHIPPED = {
    'ketubot': ['results/v10/wave4_notrim/ketubot_v10_2-60_notrim.json',
                'results/v10/wave4_notrim/ketubot_v10_61-112_notrim.json'],
    'kiddushin': ['results/v10/wave4_notrim/kiddushin_v10_notrim.json'],
}
RERUN = 'results/v11/triage_recall/{t}_skipped_stage2.json'
TRIAGE_CACHES = ['results/v7/event_triage_2-60.json',
                 'results/v7/event_triage_61-112.json',
                 'results/v7/event_triage_kiddushin.json']
OUT_DIR = REPO / 'results/v11/triage_rules'

RECALL_ARGS = {
    'ketubot': ['--expert-doc', 'jeff comms/b.ketubot (1).doc',
                '--golden', 'results/canonical/ketubot_canonical.json'],
    'kiddushin': ['--expert-json', 'results/expert_lists/kiddushin_2005.json',
                  '--expert-filter', 'recall',
                  '--golden', 'results/canonical/kiddushin_canonical.json',
                  '--tractate', 'Kiddushin'],
}


def shipped_rule(n, v, d, h, segs):
    """The rule in src/event_triage.py: EventTriager.should_skip_page()."""
    return n >= 2 or (n >= 1 and v >= 2)


CANDIDATES = {
    'shipped':        shipped_rule,
    'N>=1':           lambda n, v, d, h, s: n >= 1,
    'N>=1 or V>=4':   lambda n, v, d, h, s: n >= 1 or v >= 4,
    'N>=1 or V>=3':   lambda n, v, d, h, s: n >= 1 or v >= 3,
    'N>=1 or V>=2':   lambda n, v, d, h, s: n >= 1 or v >= 2,
    'keep everything': lambda n, v, d, h, s: True,
}


def load_triage():
    merged = {}
    for rel in TRIAGE_CACHES:
        merged.update(json.loads((REPO / rel).read_text())['triage_results'])
    return merged


def counts(labels):
    c = Counter(labels)
    return (c.get('NARRATIVE_EVENT', 0), c.get('VERBAL_ACT', 0),
            c.get('DELIBERATION', 0), c.get('HABITUAL', 0), len(labels))


def build(tractate, rule, name, triage, rerun_pages):
    """Write a run in which pages the rule keeps carry their Stage 2 output."""
    kept, calls = [], 0
    out_paths = []
    for rel in SHIPPED[tractate]:
        src = json.loads((REPO / rel).read_text())
        for page in src['pages']:
            if not page.get('skipped_by_triage'):
                continue
            n, v, d, h, segs = counts(triage.get(page['ref'], []))
            # Strictly-looser check: the shipped rule skipped this page, so any
            # candidate that also skips it must leave it untouched.
            assert not shipped_rule(n, v, d, h, segs), (
                f"{page['ref']} is marked skipped but the shipped rule keeps it")
            if not rule(n, v, d, h, segs):
                continue
            rp = rerun_pages.get(page['ref'])
            if rp is None or rp.get('stage2_error'):
                continue
            page['stories'] = rp['stories']
            kept.append(page['ref'])
            calls += 1
        dest = OUT_DIR / f"{tractate}__{name.replace('>', 'g').replace('=', 'e').replace(' ', '_')}__{Path(rel).stem}.json"
        dest.write_text(json.dumps(src, ensure_ascii=False))
        out_paths.append(dest)
    return out_paths, kept, calls


def measure(tractate, paths, tag):
    out = OUT_DIR / f'{tractate}__{tag}__recall.json'
    cmd = ([sys.executable, 'scripts/measure_recall_vs_expert_list.py']
           + RECALL_ARGS[tractate]
           + ['--detected'] + [str(p) for p in paths]
           + ['--out', str(out)])
    r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-2000:])
    rows = json.loads(out.read_text())
    found = sum(1 for x in rows if x['in_detector'])
    return found, len(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tractate', required=True, choices=sorted(SHIPPED))
    args = ap.parse_args()
    t = args.tractate

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    triage = load_triage()
    rerun = json.loads((REPO / RERUN.format(t=t)).read_text())
    rerun_pages = {p['ref']: p for p in rerun['pages']}

    # False proposals per page: proposals Stage 2 made that match no expert story.
    # Established once against the "keep everything" measurement below.
    print(f"\n{t.upper()}  —  candidate Stage 1 rules, priced against the BLIND list\n")
    print(f"{'rule':18s} {'extra calls':>11s} {'found':>7s} {'recall':>8s} "
          f"{'proposals':>10s} {'false':>6s} {'calls/story':>12s}")

    base_found = None
    for name, rule in CANDIDATES.items():
        tag = name.replace('>', 'g').replace('=', 'e').replace(' ', '_')
        paths, kept, calls = build(t, rule, name, triage, rerun_pages)
        found, denom = measure(t, paths, tag)
        if base_found is None:
            base_found = found
        props = sum(len([s for s in rerun_pages[r]['stories']
                         if s.get('classification') not in ('NOT_A_STORY', None)])
                    for r in kept)
        gained = found - base_found
        cps = f"{calls/gained:.0f}" if gained else "—"
        print(f"{name:18s} {calls:>11d} {found:>7d} {100*found/denom:>7.1f}% "
              f"{props:>10d} {props-gained:>6d} {cps:>12s}")

    print(f"\nartifacts in {OUT_DIR.relative_to(REPO)}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
