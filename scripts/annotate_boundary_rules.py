#!/usr/bin/env python3
"""
Mark which convention each 2005 boundary target expresses. NEVER move a target.

THE PROBLEM. Jeff's 2005 lists are the neutral ruler, and on one point they are
internally inconsistent: a story introduced by `תניא` / `אמר רב יהודה אמר רב` starts
*at* the formula in some entries and *after* it in others. He settled it on
2026-09-01 — "these opening formulae... are important... we should include them" —
and added that the lists "were sloppy and preliminary, and we had not worked this
out."

So the same detector output scores +10/-11 against those targets, where all 11
losses are entries whose start excludes a formula. Reading that as a regression is
wrong; reading it as licence to edit his boundaries is worse.

WHAT THIS DOES. Adds to each start target:

    rule            : 'R-B1'  when an opening formula is in play
    rule_clause     : the clause index the 2026 standard puts the start at
    rule_relation   : 'included' (his start already at the formula)
                    | 'excluded' (his start after it — the 2026 rule moves it)

`clause` — the extent HE chose — is never touched, so the file still grades the
question "do we match Jeff-2005". `score_boundary_targets.py --standard jeff-2026`
grades "do we match the rule he stated in 2026". Both are real questions and the
answer differs; that is Lesson 24, and the fix is to name the standard, not to
rewrite the data.

    python3 scripts/annotate_boundary_rules.py --targets tests/expert_boundary_targets_2005_gittin.json
"""
import argparse
import json
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s [rules] %(message)s',
                    handlers=[logging.FileHandler(PROJECT_ROOT / 'project.log'),
                              logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)

from src.story_detector_v11 import _split_into_clauses, _is_opening_formula  # noqa: E402


def load_units():
    """Every segment we hold, from detector output and from raw Sefaria alike."""
    segs = {}
    for pat in ('results/v11/**/*.json', 'results/v10/wave4_notrim/*.json', 'results/sefaria/*.json'):
        for path in sorted(PROJECT_ROOT.glob(pat)):
            try:
                data = json.loads(path.read_text())
            except Exception:
                continue
            if not isinstance(data, dict):
                continue
            pages = data.get('pages')
            if not isinstance(pages, list):
                continue
            for page in pages:
                if not isinstance(page, dict):
                    continue
                for s in page.get('segments') or []:
                    if isinstance(s, dict):
                        segs.setdefault((page.get('ref'), s.get('index')), s.get('hebrew', ''))
    return segs


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--targets', nargs='+', required=True)
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    segs = load_units()
    for spec in args.targets:
        path = PROJECT_ROOT / spec
        data = json.loads(path.read_text())
        inc = exc = 0
        for t in data['targets']:
            t.pop('rule', None); t.pop('rule_clause', None); t.pop('rule_relation', None)
            if t.get('direction') != 'start':
                continue
            heb = segs.get((t.get('located_on') or t['ref'], t['segment']))
            if not heb:
                continue
            clauses = _split_into_clauses(heb)
            if not clauses:
                continue
            texts = [heb[a:b] for a, b in clauses]
            i = t['clause']
            if i < len(texts) and _is_opening_formula(texts[i]):
                t.update(rule='R-B1', rule_clause=i, rule_relation='included'); inc += 1
            elif 0 < i <= len(texts) and _is_opening_formula(texts[i - 1]):
                t.update(rule='R-B1', rule_clause=i - 1, rule_relation='excluded'); exc += 1
        log.info('%s: %d start targets already AT a formula, %d that exclude one '
                 '(the 2026 rule moves those)', path.name, inc, exc)
        if not args.dry_run:
            path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
