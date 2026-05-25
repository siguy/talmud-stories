#!/usr/bin/env python3
"""
Wave 3 verification: concrete pass/fail for each of the four items.

Assumes Wave 3 outputs at:
  results/v9/wave3/kiddushin_v9.json          (with item 4 already applied)
  results/v9/wave3/ketubot_v9_2-60.json       (with item 4 already applied)
  results/v9/wave3/ketubot_v9_61-112.json     (with item 4 already applied)

And today's Wave 2 baselines at:
  docs/golden/v8/baselines/kiddushin_wave2_baseline_today.json
  docs/golden/v8/baselines/ketubot_wave2_baseline_today.json

Checks:
  Item 1: Kiddushin 71a has ≥2 stories.
  Item 2: Kiddushin 33a has objection-embedded story (seg 5-6);
          Kiddushin 81b has baraita-embedded story (seg 9).
  Item 3: Kiddushin false-positive count ≤4 (was 10).
  Item 4: ≥10/17 Jeff-flagged boundary cases have correct text_span slices.
  Gate:   Kiddushin composite ≥ today-Wave-2;
          Ketubot composite ≥ today-Wave-2.
"""

import json
import re
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent
WAVE3 = ROOT / 'results' / 'v9' / 'wave3'
BASELINES = ROOT / 'docs' / 'golden' / 'v8' / 'baselines'

KID_W3 = WAVE3 / 'kiddushin_v9.json'
KET_W3 = [WAVE3 / 'ketubot_v9_2-60.json', WAVE3 / 'ketubot_v9_61-112.json']
KID_GOLD = ROOT / 'results' / 'canonical' / 'kiddushin_canonical.json'
KET_GOLD = ROOT / 'results' / 'canonical' / 'ketubot_canonical.json'


def _check(name, ok, detail=''):
    icon = '✓' if ok else '✗'
    print(f"  [{icon}] {name}{(': ' + detail) if detail else ''}")
    return ok


def real_stories(page):
    return [s for s in page.get('stories', [])
            if s.get('classification') not in ('NOT_A_STORY', None)]


def find_page(data, ref):
    for p in data['pages']:
        if p['ref'] == ref:
            return p
    return None


def has_story_overlapping(page, lo, hi):
    for s in real_stories(page):
        a, b = s.get('start_segment'), s.get('end_segment')
        if a is None or b is None:
            continue
        if a <= hi and b >= lo:
            return s
    return None


def score(detected_paths, golden_path, out_path):
    cmd = ['python3', str(ROOT / 'scripts' / 'evaluate_golden.py'),
           '--detected'] + [str(p) for p in detected_paths] + [
           '--golden', str(golden_path),
           '--output', str(out_path), '--quiet']
    subprocess.run(cmd, check=True, cwd=str(ROOT),
                   env={'PYTHONPATH': str(ROOT), 'PATH': '/usr/bin:/usr/local/bin:/opt/homebrew/bin'})
    return json.load(open(out_path))


def main():
    print("=" * 60)
    print("  Wave 3 verification")
    print("=" * 60)

    for p in [KID_W3, *KET_W3]:
        if not p.exists():
            sys.exit(f"ERROR: missing {p}")

    kid = json.load(open(KID_W3))
    print("\n[ITEM 1] Multi-story per page")
    page_71a = find_page(kid, 'Kiddushin 71a')
    n_71a = len(real_stories(page_71a)) if page_71a else 0
    item1_ok = _check("Kiddushin 71a has ≥2 stories", n_71a >= 2, f"{n_71a} stories")

    print("\n[ITEM 2] Embedded-story detection")
    page_33a = find_page(kid, 'Kiddushin 33a')
    page_81b = find_page(kid, 'Kiddushin 81b')
    # 33a objection-embedded: Jeff flagged a story around seg 5-6 (R. Chiyya bathhouse)
    s_33a = has_story_overlapping(page_33a, 5, 6) if page_33a else None
    # 81b baraita-embedded: Jeff flagged seg 9 (R. Tarfon daughter-in-law)
    s_81b = has_story_overlapping(page_81b, 9, 9) if page_81b else None
    item2a_ok = _check("Kiddushin 33a detects story at segs 5-6",
                       s_33a is not None,
                       f"{s_33a['start_segment']}-{s_33a['end_segment']}" if s_33a else 'missing')
    item2b_ok = _check("Kiddushin 81b detects story at seg 9",
                       s_81b is not None,
                       f"{s_81b['start_segment']}-{s_81b['end_segment']}" if s_81b else 'missing')

    print("\n[ITEM 3] Kiddushin false-positive count ≤4 (was 10)")
    kid_eval = score([KID_W3], KID_GOLD, Path('/tmp/kid_w3_eval.json'))
    fp = kid_eval['classification']['fp']
    item3_ok = _check("Kiddushin FP count ≤4", fp <= 4, f"FP={fp}")

    print("\n[ITEM 4] Jeff-flagged text-internal boundary cases")
    audit_out = subprocess.run(
        ['python3', str(ROOT / 'scripts' / 'audit_wave3_item4.py')],
        capture_output=True, text=True, cwd=str(ROOT),
        env={'PYTHONPATH': str(ROOT),
             'PATH': '/usr/bin:/usr/local/bin:/opt/homebrew/bin',
             'AUDIT_INPUT': str(KID_W3)})
    print(audit_out.stdout[-400:] if audit_out.stdout else audit_out.stderr[-400:])
    m = re.search(r'Cases fully matching .+?: (\d+)/(\d+)', audit_out.stdout or '')
    if m:
        ok, tot = int(m.group(1)), int(m.group(2))
        item4_ok = _check("Item 4 hit ≥10 cases", ok >= 10, f"{ok}/{tot}")
    else:
        item4_ok = _check("Item 4 audit ran", False, "audit output not parsed")

    print("\n[GATE] Composite must not regress vs today-Wave-2")
    kid_base = json.load(open(BASELINES / 'kiddushin_wave2_baseline_today.json'))
    ket_base = json.load(open(BASELINES / 'ketubot_wave2_baseline_today.json'))
    ket_eval = score(KET_W3, KET_GOLD, Path('/tmp/ket_w3_eval.json'))
    kid_w3_comp = kid_eval['composite']
    ket_w3_comp = ket_eval['composite']
    gate_kid_ok = _check(f"Kiddushin composite ≥ {kid_base['composite']:.4f}",
                         kid_w3_comp >= kid_base['composite'],
                         f"{kid_w3_comp:.4f} (Δ {kid_w3_comp-kid_base['composite']:+.4f})")
    gate_ket_ok = _check(f"Ketubot composite ≥ {ket_base['composite']:.4f}",
                         ket_w3_comp >= ket_base['composite'],
                         f"{ket_w3_comp:.4f} (Δ {ket_w3_comp-ket_base['composite']:+.4f})")

    print("\n" + "=" * 60)
    items = [item1_ok, item2a_ok, item2b_ok, item3_ok, item4_ok,
             gate_kid_ok, gate_ket_ok]
    passed = sum(items)
    print(f"  Wave 3: {passed}/{len(items)} checks passed")
    print("=" * 60)
    sys.exit(0 if all([gate_kid_ok, gate_ket_ok, item4_ok]) else 1)


if __name__ == '__main__':
    main()
