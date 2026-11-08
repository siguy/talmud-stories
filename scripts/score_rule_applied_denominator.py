#!/usr/bin/env python3
"""Eruvin recall on the rule-applied denominator (a SENSITIVITY figure, not the headline).

Reads results/expert_lists/eruvin_rule_applied.json (two Claude judges re-applying Jeff's
later rules to his 2005 entries) and a recall matches file. Drops entries where BOTH judges
said NOT_A_STORY and reports recall on what is left, next to the unreduced figure.
Not Jeff's rulings -- those live in superseded_by_rule.json and stay the only thing the
board and the scorer treat as his.
"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).parent.parent
rule = {e['id']: e for e in json.loads((ROOT / 'results/expert_lists/eruvin_rule_applied.json').read_text())['entries']}
for path in sys.argv[1:] or ['results/recall/eruvin_jeff2005_matches.json', 'results/recall/eruvin_jeff2005_matches_r2.json']:
    m = json.loads((ROOT / path).read_text())
    rows = m if isinstance(m, list) else next(v for v in m.values() if isinstance(v, list))
    assert {r['id'] for r in rows} == set(rule), 'matches file and judged ids differ'
    keep = [r for r in rows if not rule[r['id']]['excluded']]
    f = lambda rs: sum(r['in_detector'] for r in rs)
    print(f"{Path(path).name}: as written {f(rows)}/{len(rows)} = {f(rows)/len(rows):.1%} | "
          f"rule-applied {f(keep)}/{len(keep)} = {f(keep)/len(keep):.1%} "
          f"({len(rows)-len(keep)} excluded, {sum(r['in_detector'] for r in rows if rule[r['id']]['excluded'])} of them found by the detector)")
    print('  still missed:', [(r['id'], r['ref']) for r in keep if not r['in_detector']])
