#!/usr/bin/env python3
"""
Classification precision on Gittin, with the unknowns kept visible.

Why this is not `build_ruler.py --report`. The ruler reports precision over the
proposals that carry a VERDICT. On Ketubot and Kiddushin that was most of them, because
those rounds walked the whole tractate story by story. On Gittin the round covered ONLY
the 25 proposals his 2005 list does not name -- deliberately, because the rest were
already corroborated. So the ruler's Gittin figure is precision on the residue after his
list is removed, which is the hardest subset that exists, and quoting it as the
tractate's precision understates it by roughly seventy points.

This script reports the tractate figure instead, and it refuses to hide the part nobody
has judged. Three populations, never merged:

  corroborated  his 2005 list names a story our span overlaps (strict test)
  judged        he ruled on our span: yes / borderline / no
  unknown       no expert evidence of any kind

`unknown` is reported as a WIDTH, not distributed. A precision quoted as a single number
over a denominator containing 12 unjudged spans is a guess wearing a decimal point.

Usage:
  python3 scripts/report_classification_precision.py --golden results/canonical/gittin_canonical.json
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--golden', required=True)
    args = ap.parse_args()

    d = json.loads(Path(args.golden).read_text())
    entries = [s for pg in d['pages'] for s in pg.get('stories', [])]
    unlabelled = d['unlabelled_proposals']

    # The denominator is what the detector ASSERTS is a story. A span it labelled
    # NOT_A_STORY itself is not a claim, so it cannot be a false positive.
    asserted = [e for e in entries if e['detector_classification'] != 'NOT_A_STORY']
    asserted_unlabelled = [u for u in unlabelled
                           if u['detector_classification'] != 'NOT_A_STORY']
    denom = len(asserted) + len(asserted_unlabelled)

    corroborated = [e for e in asserted if e['label_source'] == 'expert_blind_list']
    judged = [e for e in asserted if e['label_source'] == 'expert_verdict']
    yes = [e for e in judged if e['classification'] == 'YES']
    border = [e for e in judged if e['classification'] == 'BORDERLINE']
    no = [e for e in judged if e['classification'] == 'NOT_A_STORY']

    right = len(corroborated) + len(yes)
    wrong = len(no)
    unknown = len(asserted_unlabelled)

    print(f'\nGittin — proposals the detector asserts are stories: {denom}\n')
    print(f'  corroborated by his 2005 list   {len(corroborated):4}')
    print(f'  judged YES                      {len(yes):4}')
    print(f'  judged BORDERLINE               {len(border):4}   <- neither, by his own request')
    print(f'  judged NOT_A_STORY              {len(no):4}')
    print(f'  no expert evidence at all       {unknown:4}   <- the width below\n')

    lo = right / denom
    hi = (right + len(border) + unknown) / denom
    labelled = right + wrong + len(border)
    print(f'  precision, everything unproven counted against us   {lo:.3f}')
    print(f'  precision, everything unproven counted for us       {hi:.3f}')
    print(f'  over the {labelled} spans that carry a label:')
    print(f'      borderline against us  {right / labelled:.3f}')
    print(f'      borderline for us      {(right + len(border)) / labelled:.3f}\n')

    print('  Read the corroborated column carefully: it says a story IS there. It does')
    print('  NOT say our extent is right -- that is capability 4, measured separately.\n')

    src = Counter(u['detector_classification'] for u in asserted_unlabelled)
    print(f'  the {unknown} unjudged, by our own confidence: {dict(src)}')
    for u in asserted_unlabelled:
        if u['detector_classification'] == 'YES':
            print(f"      !! YES-tier and unjudged: {u['ref']} {u['start_segment']}-{u['end_segment']}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
