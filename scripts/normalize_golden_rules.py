#!/usr/bin/env python3
"""
Apply the settled rules to the golden — by marking every entry, never by deleting one.

THE GOLDEN IS THE PRODUCT AND IT IS SUPPOSED TO CHANGE (docs/STORY_RULES.md). What it
must not do is change *silently*, or lose the expert judgment underneath. So each
entry gains provenance rather than moving:

    corpus : 'talmud' | 'mishnah'    which corpus it belongs to under R-C1
    rules  : ['R-C1', ...]           which settled rules were applied to it

**R-C1** (Jeff, 2026-09-01): a story lying inside a Mishnah belongs with the stories of
the Mishnah; the Talmud's quotation of it is a Talmudic story. Those entries are not
mistakes and they are not deletions — they are a second corpus we do not yet publish.
Ketubot 14b and 77a are the concrete cases: he marked both *correct* in review, and
they should stop being counted as Talmud false negatives.

Counts do not move: `stories[]` keeps every entry it had, and the Talmud tally is a
filter over `corpus`, which any consumer can apply. That keeps
tests/test_bookkeeping.py's GOLDEN_COUNTS meaningful instead of rewriting it to match.

    python3 scripts/normalize_golden_rules.py --golden results/canonical/ketubot_canonical.json
    python3 scripts/normalize_golden_rules.py --all --dry-run
"""
import argparse
import json
import logging
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s [golden-rules] %(message)s',
                    handlers=[logging.FileHandler(PROJECT_ROOT / 'project.log'),
                              logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)

from src.story_detector_v11 import _tag_mishnah_segments  # noqa: E402

GOLDENS = ['results/canonical/ketubot_canonical.json',
           'results/canonical/kiddushin_canonical.json']


def normalize(path: Path, dry_run: bool = False) -> Counter:
    data = json.loads(path.read_text())
    counts = Counter()
    for page in data['pages']:
        segments = page.get('segments') or []
        tags = _tag_mishnah_segments(segments) if segments else {}
        for story in page.get('stories') or []:
            start = story.get('start_segment', 0)
            end = story.get('end_segment', start)
            idx = list(range(start, end + 1))
            in_mishnah = bool(idx) and all(tags.get(i) for i in idx)
            story['corpus'] = 'mishnah' if in_mishnah else 'talmud'
            rules = [r for r in story.get('rules', []) if r != 'R-C1']
            story['rules'] = rules + ['R-C1']
            counts[story['corpus']] += 1
            if in_mishnah:
                log.info('  %s segs %s-%s -> Mishnah corpus (%s)', page['ref'], start, end,
                         (story.get('one_sentence_summary') or '')[:60])
    if not dry_run:
        data.setdefault('rules_applied', [])
        if 'R-C1' not in data['rules_applied']:
            data['rules_applied'].append('R-C1')
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    return counts


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--golden', nargs='+')
    ap.add_argument('--all', action='store_true')
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    paths = [PROJECT_ROOT / g for g in (GOLDENS if args.all else (args.golden or []))]
    if not paths:
        ap.error('pass --golden or --all')
    for p in paths:
        c = normalize(p, args.dry_run)
        log.info('%s: %d talmud, %d mishnah (entries unchanged at %d)',
                 p.name, c['talmud'], c['mishnah'], sum(c.values()))
    return 0


if __name__ == '__main__':
    sys.exit(main())
