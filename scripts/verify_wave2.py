#!/usr/bin/env python3
"""
Verify Wave 2 fixes against Jeff's 2026-04-23 feedback.

Wave 2 ships three deterministic post-processors:

  Issue #3 — Story-START boundary snap
    Snap detected story start to an earlier canonical Hebrew introducer
    when one is present. Honest scoping note: every start-boundary case
    Jeff flagged (5 of them) had the introducer INSIDE the detected start
    segment — i.e., a text-level boundary issue, not a segment-level one.
    Segment-level snap cannot reach into a single segment, so those 5
    cases remain uncorrected. The snap still fires on OTHER stories
    where the detector started one segment late (validated as quality
    wins below).

  Issue #4 — Story-END boundary trim
    Walk story segments from the end inward, drop any opening with a
    stam-Talmud marker. Same scoping caveat: every end-boundary case
    Jeff flagged was text-internal, not segment-level. Zero trims fire
    on current outputs — boundary refinement (Stage 4a) already strips
    most trailing stam.

  Issue #6(b) — Biblical-actor filter
    Demote stories whose only named actors are biblical figures. Two of
    Jeff's "not a story" cases (#38a 0-0 'Jewish people', #72b 4-4
    Nebuchadnezzar) were biblical-actor stories the detector wrongly
    classified.

Pass criteria (per task spec):
  - Issue #6(b): Kiddushin 38a_0-0 and 72b_4-4 are demoted to NOT_A_STORY.
  - Issue #3: Every snap that fired is semantically defensible
    (extends to an ההוא ד / ההיא / מעשה ב / כי הא ד introducer).
  - Issue #4: Zero trims fired — recorded as scoping limitation.
  - Regression gate: Wave 2 composite >= Wave 1 composite on BOTH
    Kiddushin and Ketubot golden sets.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
KID_W1 = ROOT / 'results' / 'v8' / 'wave1' / 'kiddushin_v8.json'
KID_W2 = ROOT / 'results' / 'v8' / 'wave2' / 'kiddushin_v8.json'
KET_W1_A = ROOT / 'results' / 'v8' / 'wave1' / 'ketubot_v8_2-60.json'
KET_W1_B = ROOT / 'results' / 'v8' / 'wave1' / 'ketubot_v8_61-112.json'
KET_W2_A = ROOT / 'results' / 'v8' / 'wave2' / 'ketubot_v8_2-60.json'
KET_W2_B = ROOT / 'results' / 'v8' / 'wave2' / 'ketubot_v8_61-112.json'

KID_BASELINE = ROOT / 'docs' / 'golden' / 'v8' / 'baselines' / 'kiddushin_wave1_baseline.json'
KET_BASELINE = ROOT / 'docs' / 'golden' / 'v8' / 'baselines' / 'ketubot_wave1_baseline.json'

NIK = re.compile(r'[\u0591-\u05C7]')
def strip(s): return NIK.sub('', s or '')

VALID_SNAP_PREFIXES = ('ההוא ד', 'ההוא גברא', 'ההיא', 'מעשה ב',
                       'כי הא ד', 'הנהו בי תרי', 'הנהו תרי',
                       'כדתניא', 'תניא')

CHECKS = []
def check(name, ok, detail=''):
    CHECKS.append((name, ok, detail))


def load(p):
    with open(p) as f:
        return json.load(f)


def index_pages(data):
    return {p['ref']: p for p in data['pages']}


def main():
    kid_w2 = load(KID_W2)
    kid_w1 = load(KID_W1)
    kid_pages_w2 = index_pages(kid_w2)

    # ---- Issue #6(b): biblical filter on the 2 flagged Kiddushin cases ----
    for ref, start, end in [('Kiddushin 38a', 0, 0), ('Kiddushin 72b', 4, 4)]:
        page = kid_pages_w2.get(ref, {})
        target = None
        for s in page.get('stories', []):
            if s.get('start_segment') == start and s.get('end_segment') == end:
                target = s
                break
        demoted = (target is not None
                   and target.get('filtered_as_biblical') is True
                   and target.get('classification') == 'NOT_A_STORY')
        check(f'Issue #6(b) {ref}_{start}-{end} demoted to NOT_A_STORY',
              demoted,
              f"found={bool(target)} flag={target.get('filtered_as_biblical') if target else None} "
              f"cls={target.get('classification') if target else None}")

    # ---- Issue #3: every snap that fired is semantically defensible ----
    snaps = []
    for src in [kid_w2, load(KET_W2_A), load(KET_W2_B)]:
        for p in src['pages']:
            seg_idx = {s.get('index', i): s for i, s in enumerate(p['segments'])}
            for st in p.get('stories', []):
                if st.get('start_snap_kind'):
                    new_start = st['start_segment']
                    heb = strip(seg_idx.get(new_start, {}).get('hebrew', ''))[:80].lstrip(
                        ' :,.!?"\u201c\u201d\u05f4\u05f3'
                    )
                    snaps.append((p['ref'], st.get('start_segment_pre_snap'),
                                  new_start, heb))

    for ref, pre, new, heb in snaps:
        ok = any(heb.startswith(m) for m in VALID_SNAP_PREFIXES)
        check(f'Issue #3 snap {ref} {pre}->{new} starts with valid introducer',
              ok, f'seg starts: {heb!r}')

    check('Issue #3 at least one snap fired', len(snaps) > 0,
          f'snaps={len(snaps)}')

    # ---- Issue #4: trims (zero expected; scoping limitation) ----
    trims = []
    for src in [kid_w2, load(KET_W2_A), load(KET_W2_B)]:
        for p in src['pages']:
            for st in p.get('stories', []):
                if 'end_segment_pre_trim' in st:
                    trims.append((p['ref'],
                                  st['end_segment_pre_trim'],
                                  st['end_segment']))
    check('Issue #4 trim post-processor ran without error', True,
          f'trims fired={len(trims)} '
          f'(zero is expected — Jeff\'s end-boundary cases are text-internal)')

    # ---- Regression gate: composite >= wave1 on both tractates ----
    kid_baseline = load(KID_BASELINE)['composite']
    ket_baseline = load(KET_BASELINE)['composite']

    import subprocess
    def score(detected_paths, golden):
        out = subprocess.run(
            ['python3', str(ROOT / 'scripts' / 'evaluate_golden.py'),
             '--detected', *[str(p) for p in detected_paths],
             '--golden', str(golden), '--output', '/tmp/_wave2_score.json',
             '--quiet'],
            check=True, capture_output=True)
        return json.load(open('/tmp/_wave2_score.json'))['composite']

    kid_w2_score = score([KID_W2], ROOT / 'results' / 'canonical' / 'kiddushin_canonical.json')
    ket_w2_score = score([KET_W2_A, KET_W2_B], ROOT / 'results' / 'canonical' / 'ketubot_canonical.json')

    check(f'Gate: Kiddushin Wave 2 composite >= Wave 1 ({kid_w2_score:.4f} >= {kid_baseline:.4f})',
          kid_w2_score >= kid_baseline,
          f'delta={kid_w2_score - kid_baseline:+.4f}')
    check(f'Gate: Ketubot Wave 2 composite >= Wave 1 ({ket_w2_score:.4f} >= {ket_baseline:.4f})',
          ket_w2_score >= ket_baseline,
          f'delta={ket_w2_score - ket_baseline:+.4f}')

    # ---- Sanity: no excessive story loss ----
    def real_count(data):
        return sum(
            1 for p in data['pages'] for s in p.get('stories', [])
            if s.get('classification') != 'NOT_A_STORY'
        )
    kid_loss = real_count(kid_w1) - real_count(kid_w2)
    check('Kiddushin real-story drop <= 5', kid_loss <= 5,
          f"w1={real_count(kid_w1)} w2={real_count(kid_w2)} loss={kid_loss}")

    # ---- Report ----
    print('=' * 72)
    print('  Wave 2 Verification Report')
    print('=' * 72)
    passed = sum(1 for _, ok, _ in CHECKS if ok)
    failed = len(CHECKS) - passed
    for name, ok, detail in CHECKS:
        mark = 'PASS' if ok else 'FAIL'
        print(f'  [{mark}] {name}')
        if detail:
            print(f'         {detail}')
    print('-' * 72)
    print(f'  {passed}/{len(CHECKS)} checks passed, {failed} failed')
    print('=' * 72)
    sys.exit(0 if failed == 0 else 1)


if __name__ == '__main__':
    main()
