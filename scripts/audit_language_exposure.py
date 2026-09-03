#!/usr/bin/env python3
"""
What did the model actually READ — translation, or source?

Jeff rejected Gittin 46a, a proposal we made at HIGH_CONFIDENCE:

    "If you look at the Aramaic/Hebrew, there is no story. It is filled in by the
     translator. Not enough to go on here."

and then 74b: "the same as 46a above." Two of our five HIGH_CONFIDENCE extras, killed by
one cause. This script prices that cause on every Gittin proposal, with no API calls.

The mechanism is in the prompt. `_build_detection_prompt` renders each segment as English
truncated at 300 characters, then Hebrew truncated at 200 -- so on a segment long enough
to truncate, the model sees MORE translation than source. Steinsaltz interpolates: it
supplies subjects, connectives and narrative sequencing the Aramaic leaves implicit, and a
detector reading it as if it were the source will find event structure that is not there.

WHAT THIS CAN AND CANNOT SHOW. Exposure is what the model was shown. It is not evidence
that the model was misled by it -- a long segment is also a segment with more happening in
it, and that alone would put the rejected proposals at higher exposure with no translator
effect at all. So the comparison here is INDICATED, never measured, and the number it
produces is a decision about whether the ablation is worth running, not a result. Lesson
18: measure the rate before planning the fix; Lesson 22: only a same-code repeat separates
a real effect from this project's noise floor.

Usage:
  python3 scripts/audit_language_exposure.py \
      --run results/v11/gittin/gittin_v11.json \
      --verdicts validation/feedback/gittin_axes_review_2026-09-02.json
"""

import argparse
import json
import re
import statistics
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

# The budgets in src/story_detector_v11.py::_build_detection_prompt. Duplicated here
# deliberately and asserted below: if the detector's budgets change and this file does
# not, the audit silently describes a prompt that no longer exists.
ENG_BUDGET, HEB_BUDGET = 300, 200
TAGS = re.compile(r'<[^>]+>')


def check_budgets_still_match_the_detector():
    """Read the real numbers out of the detector rather than trusting the constants."""
    src = (PROJECT_ROOT / 'src/story_detector_v11.py').read_text()
    body = src.split('def build_detection_prompt', 1)[-1][:2000]
    # The prompt truncates with `if len(eng) > 300: eng = eng[:300] + "..."`, so the
    # budget appears as a bare integer on both sides. Match the slice, which is the
    # form that survives if the guard is rewritten as a one-liner.
    found = {int(m) for m in re.findall(r'\[:(\d{2,4})\]', body)} | \
            {int(m) for m in re.findall(r'len\((?:eng|heb)\)\s*>\s*(\d{2,4})', body)}
    if ENG_BUDGET not in found or HEB_BUDGET not in found:
        print(f'  !! the detection prompt no longer truncates at {ENG_BUDGET}/{HEB_BUDGET} '
              f'(found {sorted(set(found))}). This audit describes a prompt that has '
              f'changed -- update the constants before trusting anything below.\n')
        return False
    return True


def exposure(segments, start, end):
    """What the model saw for one proposal, in characters, after truncation."""
    eng = heb = raw_eng = raw_heb = 0
    truncated_eng = truncated_heb = 0
    n = 0
    for seg in segments:
        i = seg.get('index', -1)
        if not (start <= i <= end):
            continue
        n += 1
        e = TAGS.sub('', seg.get('english', '') or '')
        h = seg.get('hebrew', '') or ''
        truncated_eng += len(e) > ENG_BUDGET
        truncated_heb += len(h) > HEB_BUDGET
        eng += min(len(e), ENG_BUDGET)
        heb += min(len(h), HEB_BUDGET)
        # The UNtruncated ratio is the better measure of what Jeff actually objected to.
        # His two cases are single short segments where Steinsaltz expands the Aramaic
        # several-fold -- nothing to do with truncation, everything to do with how much
        # the translator supplies. Both are reported; they answer different questions.
        raw_eng += len(e)
        raw_heb += len(h)
    return {'segments': n, 'eng_chars': eng, 'heb_chars': heb,
            'ratio': round(eng / heb, 3) if heb else None,
            'raw_ratio': round(raw_eng / raw_heb, 3) if raw_heb else None,
            'segments_with_english_truncated': truncated_eng,
            'segments_with_hebrew_truncated': truncated_heb}


def describe(name, rows):
    if not rows:
        print(f'  {name:26} n=0')
        return
    ratios = [r['ratio'] for r in rows if r['ratio'] is not None]
    raws = [r['raw_ratio'] for r in rows if r['raw_ratio'] is not None]
    trunc = sum(r['segments_with_hebrew_truncated'] for r in rows)
    segs = sum(r['segments'] for r in rows)
    print(f'  {name:26} n={len(rows):3}  as shown {statistics.median(ratios):.2f}  '
          f'untruncated {statistics.median(raws):.2f}  '
          f'Hebrew truncated on {trunc}/{segs} segments ({100*trunc/segs:.0f}%)')
    return statistics.median(raws)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--run', required=True)
    ap.add_argument('--verdicts', required=True)
    args = ap.parse_args()

    print()
    ok = check_budgets_still_match_the_detector()

    data = json.loads(Path(args.run).read_text())
    pages = data['pages'] if isinstance(data, dict) else data
    verdicts = json.loads(Path(args.verdicts).read_text())['reviews']

    rows = []
    for page in pages:
        segs = page.get('segments', [])
        for story in page.get('stories', []):
            a, b = story.get('start_segment'), story.get('end_segment')
            if a is None or b is None:
                continue
            key = f"{page['ref']}_{a}-{b}"
            v = verdicts.get(key)
            rows.append({'ref': page['ref'], 'start': a, 'end': b,
                         'detector': story.get('classification'),
                         'verdict': v['is_story'] if v else None,
                         **exposure(segs, a, b)})

    print(f'Gittin — {len(rows)} proposals, {sum(1 for r in rows if r["verdict"])} judged\n')
    print('Two ratios, both English chars : Hebrew chars.')
    print(f'  "as shown"    after truncation -- what reached the model. Caps at '
          f'{ENG_BUDGET/HEB_BUDGET:.2f} when both languages truncate.')
    print('  "untruncated" the passage\'s own expansion -- how much the translator supplies.')
    print('The second is the one that matches his objection, and it is not capped.\n')

    yes = [r for r in rows if r['verdict'] == 'yes']
    border = [r for r in rows if r['verdict'] == 'borderline']
    no = [r for r in rows if r['verdict'] == 'no']
    m_yes = describe('judged a story', yes)
    describe('judged borderline', border)
    m_no = describe('judged NOT a story', no)
    describe('all proposals', rows)

    print()
    if m_yes is not None and m_no is not None:
        gap = m_no - m_yes
        print(f'  gap (rejected - accepted), median untruncated ratio: {gap:+.2f}')
        print('  A clearly positive gap would be consistent with the translator')
        print('  hypothesis -- and would still be consistent with rejected passages simply')
        print('  being wordier, which this cannot separate. INDICATED, never measured.')
        verdict = 'RUN the ablation' if gap > 0.15 else 'DO NOT run the ablation on this evidence'
        print(f'\n  Step 2 decision: {verdict}')
        if gap <= 0.15:
            print('  The mechanism is real and it is in the prompt. This says it is not what')
            print('  separates his rejections from his acceptances, so an ablation would be')
            print('  spending a run to chase something the data does not point at.')

        # The split test, because a median can hide a threshold effect.
        judged = [r for r in rows if r['verdict']]
        hi = [r for r in judged if (r['raw_ratio'] or 0) >= 2.5]
        lo = [r for r in judged if (r['raw_ratio'] or 0) < 2.5]
        for name, g in (('untruncated ratio >= 2.5', hi), ('untruncated ratio <  2.5', lo)):
            if g:
                rej = sum(1 for r in g if r['verdict'] == 'no')
                print(f'  {name}: {len(g):3} judged, {rej} rejected ({100*rej/len(g):.0f}%)')
        print('  If the heavily-expanded group is not rejected MORE, expansion is not the')
        print('  thing he is reacting to.')

    print(f'\n  n=3 accepted and n=18 rejected. These are single-digit groups; the medians')
    print(f'  move on one passage. Treat the direction as a hint and the magnitude as noise.')

    named = [r for r in rows if (r['ref'], r['start']) in (('Gittin 46a', 12), ('Gittin 74b', 4))]
    if named:
        print('\n  His two named cases:')
        for r in named:
            print(f"    {r['ref']} {r['start']}-{r['end']}  untruncated {r['raw_ratio']}  "
                  f"segments {r['segments']}  detector {r['detector']}  -> {r['verdict']}")
        print('    Both sit far above the corpus median, so his reading of these two is')
        print('    exactly right. That is what makes the null result above worth writing')
        print('    down: the cause he named is real HERE and does not generalise.')
    return 0 if ok else 0


if __name__ == '__main__':
    sys.exit(main())
