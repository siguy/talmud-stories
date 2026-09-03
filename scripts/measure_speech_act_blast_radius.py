#!/usr/bin/env python3
"""
Phase 6a — how many golden entries would Jeff's 2026-07-06 rule demote?

The problem in one line: **two of Jeff's own rulings disagree, and nobody has measured
how much of the golden sits between them.**

  2026-03-17, over 187 reviews:  "The actions mentioned in the reasoning -- stating,
                                  objecting, asking questions -- are all part of a
                                  dialogue, and not really events."
  2026-07-06, as a general rule:  "speech-acts don't count... minimally there must be
                                  some action beyond the speech."

Both are his. Neither is wrong. The golden was built on the first; the second would
demote every entry where nothing happens but speech -- and the candidate bucket is the
110 LOW_CONFIDENCE entries across Ketubot and Kiddushin, 44% of the accepted golden.

So the argument about the contradiction has been running without its size. This measures
it, and NOTHING ELSE. One axis, one question per entry:

    does anything non-speech happen here?

Not "is it a story" -- that is Jeff's to answer, and answering it here is exactly the
mistake this phase exists to avoid. The output is a count he can rule on:
"N of the entries in your golden would be demoted by your newer rule; here are four."

**Nothing in any golden changes.** This writes one file to results/criteria/ and touches
no dataset.

Emotional and internal reactions COUNT as action -- his 2026-07-06 rule says so
explicitly, and a screen that missed that would over-report the blast radius in the
direction that makes our problem look bigger.

Abstract criteria only in the prompt; never the passages themselves (Lesson 8).

Usage:
  python3 scripts/measure_speech_act_blast_radius.py --dry-run     # no API calls
  python3 scripts/measure_speech_act_blast_radius.py --out results/criteria/speech_act_blast_radius.json
"""

import argparse
import json
import logging
import os
import re
import sys
import time
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s [6a] %(message)s',
                    handlers=[logging.FileHandler(PROJECT_ROOT / 'project.log'),
                              logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)

GOLDENS = {'Ketubot': 'results/canonical/ketubot_canonical.json',
           'Kiddushin': 'results/canonical/kiddushin_canonical.json'}
TAGS = re.compile(r'<[^>]+>')

PROMPT = """You are helping catalogue rabbinic narrative. Answer ONE factual question
about the passage below. Do not judge whether it is a "story" — that is not the question
and not your call.

QUESTION: does anything happen in this passage OTHER than people speaking?

Counts as something happening:
- a physical action (someone goes, gives, strikes, buys, dies, builds)
- movement or a change of place
- a change of state or circumstance (someone becomes poor, falls ill, is appointed)
- an emotional or internal reaction (someone weeps, is ashamed, is astonished, relents)

Does NOT count:
- saying, asking, objecting, answering, ruling, teaching, citing, reasoning
- a hypothetical or conditional case ("if a man were to...")
- an action that is only described inside a rule rather than performed by someone

Reply with JSON only:
{"non_speech": true|false, "what_happens": "<four words or fewer, or empty>"}

PASSAGE:
"""


def entries():
    out = []
    for tractate, path in GOLDENS.items():
        p = PROJECT_ROOT / path
        if not p.exists():
            log.warning('%s: %s missing — SKIPPED, not counted as zero', tractate, path)
            continue
        data = json.loads(p.read_text())
        for page in data['pages']:
            segs = {s.get('index'): s for s in page.get('segments', [])}
            for st in page.get('stories', []):
                if st.get('classification') != 'LOW_CONFIDENCE':
                    continue
                a, b = st.get('start_segment'), st.get('end_segment')
                if a is None or b is None:
                    continue
                text = ' '.join(TAGS.sub('', (segs[i].get('english') or ''))
                                for i in range(a, b + 1) if i in segs).strip()
                if not text:
                    continue
                out.append({'tractate': tractate, 'ref': page['ref'],
                            'start_segment': a, 'end_segment': b, 'text': text})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--out', default='results/criteria/speech_act_blast_radius.json')
    ap.add_argument('--model', default=os.getenv('GEMINI_MODEL', 'gemini-2.5-flash'))
    args = ap.parse_args()

    rows = entries()
    log.info('%d LOW_CONFIDENCE golden entries — %s',
             len(rows), dict(Counter(r['tractate'] for r in rows)))
    if args.dry_run:
        log.info('dry run: no API calls. One call per entry, model %s.', args.model)
        log.info('The question asked is factual — "does anything non-speech happen" — '
                 'never "is it a story".')
        return 0

    key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
    if not key:
        log.error('no GOOGLE_API_KEY. Refusing to run — a partial pass scored as a full '
                  'one is worse than no measurement.')
        return 1

    from google import genai
    client = genai.Client(api_key=key)

    results, failed = [], 0
    for i, r in enumerate(rows, 1):
        try:
            resp = client.models.generate_content(
                model=args.model, contents=PROMPT + r['text'][:4000])
            raw = (resp.text or '').strip()
            m = re.search(r'\{.*\}', raw, re.S)
            verdict = json.loads(m.group(0)) if m else None
        except Exception as exc:                       # noqa: BLE001
            log.warning('%s %s: %s', r['ref'], r['start_segment'], exc)
            verdict = None
        if verdict is None:
            # A failed call must never be stamped as a judgement (Lesson 21).
            failed += 1
            results.append({**r, 'non_speech': None, 'what_happens': None,
                            'error': 'no verdict'})
        else:
            results.append({**r, 'non_speech': bool(verdict.get('non_speech')),
                            'what_happens': verdict.get('what_happens', '')})
        if i % 20 == 0:
            log.info('  %d/%d', i, len(rows))
        time.sleep(0.2)

    judged = [r for r in results if r['non_speech'] is not None]
    speech_only = [r for r in judged if not r['non_speech']]
    by_t = Counter(r['tractate'] for r in speech_only)

    log.info('')
    log.info('=== BLAST RADIUS')
    log.info('  LOW_CONFIDENCE golden entries examined : %d', len(rows))
    log.info('  judged                                 : %d  (failed %d)', len(judged), failed)
    log.info('  SPEECH ONLY — his 2026-07-06 rule demotes these : %d  (%.0f%% of judged)',
             len(speech_only), 100 * len(speech_only) / len(judged) if judged else 0)
    log.info('  by tractate: %s', dict(by_t))
    log.info('')
    log.info('  This is a COUNT, not a relabeling. Nothing in any golden changed.')
    log.info('  Whether these stop being stories is Jeff\'s ruling (phase 6b).')
    log.info('')
    log.info('  four examples for the email:')
    for r in speech_only[:4]:
        log.info('    %-16s %s', f"{r['ref']} {r['start_segment']}-{r['end_segment']}",
                 r['text'][:100])

    out = PROJECT_ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        'measured': '2026-09-03', 'model': args.model, 'phase': '6a',
        'question': 'does anything non-speech happen in this passage?',
        'examined': len(rows), 'judged': len(judged), 'failed': failed,
        'speech_only': len(speech_only), 'by_tractate': dict(by_t),
        'note': ('A COUNT of what Jeff\'s 2026-07-06 rule would demote. Not a relabeling '
                 'and not a story judgement — that is 6b, and it is his.'),
        'entries': results}, indent=2, ensure_ascii=False) + '\n')
    log.info('wrote %s', out)
    return 0


if __name__ == '__main__':
    sys.exit(main())
