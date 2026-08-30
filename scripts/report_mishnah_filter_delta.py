#!/usr/bin/env python3
"""
Report what the Mishnah-only filter costs against the golden dataset.

`filter_mishnah_only_stories()` (Wave 1 Issue #7) moves any story lying entirely
inside a Mishnah block out of `stories` and into `mishnah_stories`. Neither
measurement harness reads that key, so a moved story is indistinguishable from a
story the detector never found: it lands in the golden evaluation as a false
negative, and in recall as a miss, with no trace.

`scripts/evaluate_golden.py` is IMMUTABLE and is NOT modified. This script
imports it read-only and scores the same runs twice — as they stand, and with
`mishnah_stories` folded back into `stories` — then reports the delta. Nothing
is written to the harness's default output path.

Usage:
  python3 scripts/report_mishnah_filter_delta.py \
      --detected results/v10/wave4_notrim/ketubot_v10_2-60_notrim.json \
                 results/v10/wave4_notrim/ketubot_v10_61-112_notrim.json

  --golden defaults to results/canonical/ketubot_canonical.json
  --out    optional path for the machine-readable report
"""

import argparse
import json
import logging
import re
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

# Read-only import. evaluate_golden.py is immutable; we reuse its loaders,
# its IoU matching rule and its scorer so the two sides are apples-to-apples.
import evaluate_golden as harness  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [mishnah-delta] %(message)s',
    handlers=[logging.FileHandler(PROJECT_ROOT / 'project.log'), logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)

NIKUD = re.compile(r'[֑-ׇ]')
HTML = re.compile(r'<[^>]+>')
IOU_THRESHOLD = 0.3  # same threshold harness.match_stories uses


def incipit(page, start_segment, width=70):
    """First few words of the story's opening segment, unvocalised."""
    for seg in page.get('segments', []):
        if seg.get('index') == start_segment:
            txt = NIKUD.sub('', HTML.sub('', seg.get('hebrew', '')))
            txt = re.sub(r'\s+', ' ', txt).strip()
            return txt[:width]
    return ''


def golden_status(golden_stories, start, end):
    """How the golden treats the span, using the harness's own IoU rule."""
    best, best_iou = None, 0.0
    for g in golden_stories:
        iou = harness.segment_iou(g['start'], g['end'], start, end)
        if iou > best_iou:
            best, best_iou = g, iou
    if not best or best_iou < IOU_THRESHOLD:
        return 'absent', None, 0.0
    return ('accepted' if best['is_story'] else 'rejected',
            best, round(best_iou, 3))


def inventory(paths, golden):
    """Every withheld story, with its standing in the golden."""
    rows = []
    for path in paths:
        data = json.loads(Path(path).read_text())
        for page in data.get('pages', []):
            for story in page.get('mishnah_stories', []):
                start = story['start_segment']
                end = story.get('end_segment', start)
                status, match, iou = golden_status(golden.get(page['ref'], []), start, end)
                rows.append({
                    'run': Path(path).name,
                    'ref': page['ref'],
                    'segments': f'{start}-{end}',
                    'detector_classification': story.get('classification'),
                    'golden_status': status,
                    'golden_segments': f"{match['start']}-{match['end']}" if match else None,
                    'golden_classification': match['classification'] if match else None,
                    'iou': iou,
                    'incipit': incipit(page, start),
                })
    return rows


def fold(paths, out_dir):
    """Copy each run with `mishnah_stories` merged back into `stories`."""
    folded, moved = [], 0
    for i, path in enumerate(paths):
        data = json.loads(Path(path).read_text())
        for page in data.get('pages', []):
            withheld = page.get('mishnah_stories', [])
            if not withheld:
                continue
            page['stories'] = sorted(page.get('stories', []) + withheld,
                                     key=lambda s: (s['start_segment'], s.get('end_segment', 0)))
            moved += len(withheld)
        dest = Path(out_dir) / f'folded_{i}_{Path(path).name}'
        dest.write_text(json.dumps(data, ensure_ascii=False))
        folded.append(dest)
    return folded, moved


def score(paths, golden):
    return harness.evaluate(harness.load_detected([Path(p) for p in paths]), golden)


def fn_keys(results):
    return {(s['page'], s['golden']) for s in results['per_story'] if s['result'] == 'FN'}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--detected', nargs='+', required=True, help='Detector run JSON(s)')
    ap.add_argument('--golden', default=str(harness.DEFAULT_GOLDEN))
    ap.add_argument('--out', help='Write the machine-readable report here')
    args = ap.parse_args()

    golden = harness.load_golden(args.golden)
    log.info('golden %s: %d pages, %d entries',
             Path(args.golden).name, len(golden), sum(len(v) for v in golden.values()))

    rows = inventory(args.detected, golden)
    log.info('withheld by the Mishnah filter: %d stories across %d run(s)', len(rows), len(args.detected))

    print('\n' + '=' * 78)
    print('  STORIES WITHHELD BY filter_mishnah_only_stories()')
    print('=' * 78)
    for r in rows:
        print(f"\n  {r['ref']} segs {r['segments']}  [detector: {r['detector_classification']}]")
        print(f"    golden: {r['golden_status']}"
              + (f" as {r['golden_classification']} at segs {r['golden_segments']} (IoU {r['iou']})"
                 if r['golden_segments'] else ''))
        print(f"    {r['incipit']}")

    contested = [r for r in rows if r['golden_status'] == 'accepted']
    print(f"\n  {len(contested)} of {len(rows)} are stories the golden ACCEPTS.")

    with tempfile.TemporaryDirectory() as tmp:
        folded_paths, moved = fold(args.detected, tmp)
        if not moved:
            log.info('no run holds any mishnah_stories — nothing withheld, nothing to report')
            return
        log.info('folded %d withheld stories back into `stories` for the second scoring', moved)
        as_is = score(args.detected, golden)
        folded = score([str(p) for p in folded_paths], golden)

    lost = sorted(fn_keys(as_is) - fn_keys(folded))

    print('\n' + '=' * 78)
    print('  DELTA — scored twice by the IMMUTABLE harness, unmodified')
    print('=' * 78)
    print(f"\n  {'metric':<26}{'as-is':>12}{'folded back':>14}{'delta':>10}")
    rowspec = [('classification precision', as_is['classification']['precision'], folded['classification']['precision']),
               ('classification recall', as_is['classification']['recall'], folded['classification']['recall']),
               ('classification F1', as_is['classification']['f1'], folded['classification']['f1']),
               ('true positives', as_is['classification']['tp'], folded['classification']['tp']),
               ('false negatives', as_is['classification']['fn'], folded['classification']['fn']),
               ('false positives', as_is['classification']['fp'], folded['classification']['fp']),
               ('boundary mean IoU', as_is['boundary']['mean_iou'], folded['boundary']['mean_iou']),
               ('composite', as_is['composite'], folded['composite'])]
    for name, a, b in rowspec:
        d = round(b - a, 4)
        print(f"  {name:<26}{a:>12}{b:>14}{('+' if d > 0 else '') + str(d):>10}")

    total_fn = as_is['classification']['fn']
    share = f" ({100 * len(lost) / total_fn:.0f}% of them)" if total_fn else ''
    print(f"\n  Golden false negatives the filter alone accounts for: "
          f"{len(lost)} of {total_fn}{share}")
    for page, segs in lost:
        print(f"    {page} seg {segs}")

    report = {
        'golden': args.golden,
        'detected': list(args.detected),
        'withheld': rows,
        'withheld_accepted_by_golden': len(contested),
        'as_is': {k: v for k, v in as_is.items() if k != 'per_story'},
        'folded': {k: v for k, v in folded.items() if k != 'per_story'},
        'false_negatives_caused_by_filter': [{'page': p, 'segments': s} for p, s in lost],
    }
    if args.out:
        Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=1))
        log.info('wrote %s', args.out)
    log.info('filter accounts for %d of %d golden false negatives', len(lost), total_fn)


if __name__ == '__main__':
    main()
