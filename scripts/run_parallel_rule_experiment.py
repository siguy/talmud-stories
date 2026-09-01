#!/usr/bin/env python3
"""
Run and grade the parallel-practice rule change, end to end, in one command.

WHY THIS EXISTS. The prompt change in `src/story_detector_v11.py` (the parallel rule,
split in two) is written but UNRUN — the session that wrote it had no
`GOOGLE_API_KEY`. Everything needed to judge it is already decided and written down
in `work/2026-09-01-parallel-story-rule.md`: the runs, the rulers, the same-code
repeat, the pass conditions, and a prediction stated before the run. This script is
that plan made executable, so the measurement does not depend on whoever happens to
have the key rediscovering the method — or quietly skipping the parts that make the
result trustworthy.

    export GOOGLE_API_KEY=...        # or put it in .env at the project root
    python3 scripts/run_parallel_rule_experiment.py

Cost: 6 Wave 5 runs' worth of Gemini calls (3 arms + 3 repeats), pennies and a few
minutes. `--dry-run` prints the plan and verifies every input exists, with no calls.

WHAT IT REFUSES TO SKIP:
  * the SAME-CODE REPEAT (Lesson 22). A boundary score moves ~3% on identical code;
    without a repeat you cannot attribute a change to the change.
  * reporting the blind rulers APART from the corrections ruler (Lesson 24). They
    measure different things and pooling them is how this project got a Kiddushin
    figure that was wrong by 18 points and in the wrong order between tractates.
  * the DIRECTION SPLIT. Ketubot's whole deficit is ends; a pooled number hides
    exactly the axis this change moves.

WHAT IT DOES NOT DECIDE. It prints the gate's rows and a verdict, but a FAIL on the
end ruler is explicitly NOT the same as a wrong change — the prediction in the work
item says this change will probably cost end points because keeping a second story
ends later than Jeff's 2005 boundary. Read the work item's "prediction" section
before acting on a red row. The script says which rows moved; a human says why.
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

# The three shipped no-trim inputs. Spans ride existing segment boundaries, so each
# output is directly comparable to the wave5_summaryfix baseline beside it.
ARMS = [
    ('ketubot_2-60',   'results/v10/wave4_notrim/ketubot_v10_2-60_notrim.json',
     'results/v11/wave5_summaryfix/ketubot_2-60_v11_g37high.json'),
    ('ketubot_61-112', 'results/v10/wave4_notrim/ketubot_v10_61-112_notrim.json',
     'results/v11/wave5_summaryfix/ketubot_61-112_v11_g37high.json'),
    ('kiddushin',      'results/v10/wave4_notrim/kiddushin_v10_notrim.json',
     'results/v11/wave5_summaryfix/kiddushin_v11_g37high.json'),
]

KETUBOT_BLIND = 'tests/expert_boundary_targets_2005.json'
KIDDUSHIN_BLIND = 'tests/expert_boundary_targets_2005_kiddushin.json'
CORRECTIONS = 'tests/expert_boundary_targets_v2.json'

# The point of the change: these must keep their second story (depth -> 0 trim, or a
# trim that no longer discards the narrative). Measured on the frozen baseline as 6.
MUST_KEEP = [('Ketubot 62a', 7), ('Ketubot 105b', 9)]

# Must STAY trimmed. Amoraic legal debate — names and dialogue, no events. If these
# flip, the rule is keying on speech and the wording has failed (finding §2).
MUST_STAY_TRIMMED = [('Ketubot 67b', 3), ('Ketubot 77b', 11), ('Kiddushin 72a', 3)]


def have_key():
    if os.getenv('GOOGLE_API_KEY'):
        return True
    env = ROOT / '.env'
    return env.exists() and 'GOOGLE_API_KEY' in env.read_text()


def run(cmd, dry):
    print('  $ ' + ' '.join(str(c) for c in cmd))
    if dry:
        return ''
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-3000:]); print(r.stderr[-3000:], file=sys.stderr)
        raise SystemExit(f'FAILED: {" ".join(str(c) for c in cmd)}')
    return r.stdout


def trims_by_case(path):
    sys.path.insert(0, str(ROOT / 'scripts'))
    from screen_end_trim_depth import trims
    return {(t['ref'], t['segment']): t for t in trims(path)}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out-dir', default='results/v11/parallel_rule')
    ap.add_argument('--model', default='gemini-3.7-flash')
    ap.add_argument('--thinking', default='high')
    ap.add_argument('--dry-run', action='store_true',
                    help='print the plan and check every input exists; no API calls')
    args = ap.parse_args()

    missing = [p for _, p, b in ARMS for p in (p, b) if not (ROOT / p).exists()]
    if missing:
        raise SystemExit('missing input(s):\n  ' + '\n  '.join(missing))

    if not args.dry_run and not have_key():
        raise SystemExit(
            'No GOOGLE_API_KEY in the environment or in .env at the project root.\n'
            'That is the only thing standing between this change and a verdict.\n\n'
            '    export GOOGLE_API_KEY=...\n'
            '    python3 scripts/run_parallel_rule_experiment.py\n\n'
            'Use --dry-run to verify the plan and the inputs with no calls.')

    out = ROOT / args.out_dir
    out.mkdir(parents=True, exist_ok=True)
    print(f"\n=== 1. Wave 5 runs, 3 arms + 3 same-code repeats (Lesson 22) -> {args.out_dir}\n")
    produced = {}
    for name, inp, _base in ARMS:
        for tag in ('', '_repeat'):
            dest = f'{args.out_dir}/{name}_parallel{tag}.json'
            run(['python3', 'scripts/run_wave5_clause_spans.py', '--in', inp,
                 '--out', dest, '--model', args.model, '--thinking', args.thinking], args.dry_run)
            produced.setdefault(name, {})['repeat' if tag else 'new'] = dest

    print("\n=== 2. Structural gate — every boundary at a clause/word edge\n")
    for name in produced:
        run(['python3', 'scripts/audit_text_spans.py', '--strict',
             produced[name]['new']], args.dry_run)

    print("\n=== 3. Blind rulers, split by direction, reported APART from corrections "
          "(Lessons 22 and 24)\n")
    ket_new = [produced['ketubot_2-60']['new'], produced['ketubot_61-112']['new']]
    ket_rep = [produced['ketubot_2-60']['repeat'], produced['ketubot_61-112']['repeat']]
    ket_base = [b for n, _i, b in ARMS if n.startswith('ketubot')]
    for label, targets, runs in [
        ('KETUBOT  BLIND', KETUBOT_BLIND,
         [f'base={ket_base[0]}', f'new={ket_new[0]}', f'repeat={ket_rep[0]}']),
        ('KETUBOT2 BLIND', KETUBOT_BLIND,
         [f'base={ket_base[1]}', f'new={ket_new[1]}', f'repeat={ket_rep[1]}']),
        ('KIDDUSHIN BLIND', KIDDUSHIN_BLIND,
         [f'base={[b for n, _i, b in ARMS if n == "kiddushin"][0]}',
          f'new={produced["kiddushin"]["new"]}',
          f'repeat={produced["kiddushin"]["repeat"]}']),
        ('CORRECTIONS (CIRCULAR, biased — every target is a case he flagged wrong)',
         CORRECTIONS,
         [f'base={ket_base[0]}', f'new={ket_new[0]}']),
    ]:
        print(f'--- {label}')
        print(run(['python3', 'scripts/score_boundary_targets.py', '--targets', targets,
                   '--by-direction', '--runs'] + runs, args.dry_run))

    print("\n=== 4. The two cases this change exists for\n")
    if not args.dry_run:
        after = {}
        for name in ('ketubot_2-60', 'ketubot_61-112'):
            after.update(trims_by_case(ROOT / produced[name]['new']))
        ok = True
        for ref, seg in MUST_KEEP:
            t = after.get((ref, seg))
            d = t['depth'] if t else 0
            verdict = 'KEPT (no trim)' if not t else f'still trims {d} clause(s)'
            flag = 'PASS' if not t else 'CHECK BY EYE'
            ok &= not t
            print(f'  {ref:14s} seg {seg:<3d} {verdict:24s} {flag}')
        print("\n=== 5. The lookalikes that must STAY trimmed "
              "(if these flip, the rule keys on speech — finding §2)\n")
        for name in ('kiddushin',):
            after.update(trims_by_case(ROOT / produced[name]['new']))
        for ref, seg in MUST_STAY_TRIMMED:
            t = after.get((ref, seg))
            print(f'  {ref:14s} seg {seg:<3d} '
                  f'{"still trimmed  PASS" if t else "NO LONGER TRIMMED  FAIL"}')
        print('\n' + ('-' * 72))
        print('The two motivating cases: ' + ('PASS' if ok else 'not fully resolved'))
        print('Read work/2026-09-01-parallel-story-rule.md before acting on the end-ruler\n'
              'rows: a fall there was PREDICTED and is not by itself evidence the change\n'
              'is wrong. What decides it is whether the fall is confined to these cases.')
    else:
        print('  (dry run — would check 62a/105b keep their second story, and that\n'
              '   67b/77b/72a stay trimmed)')

    print("\n=== 6. Re-screen, to see the candidate list did not balloon\n")
    run(['python3', 'scripts/screen_end_trim_depth.py', '--runs'] +
        [produced[n]['new'] for n in produced] + ['--min-depth', '4'], args.dry_run)

    print('\nWhen the numbers are in: add an ## Outcome to '
          'work/2026-09-01-parallel-story-rule.md\nsaying what happened and WHY '
          '(especially for a revert), then `python3 scripts/board.py finish '
          '2026-09-01-parallel-story-rule`.')


if __name__ == '__main__':
    main()
