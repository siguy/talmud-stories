#!/usr/bin/env python3
"""
Build Canonical Kiddushin Stories File from Jeff Rubenstein's 2026-04-23 review.

Strategy:
  - Use v7 Kiddushin detector output as the base (96 real stories — all the
    stories Jeff actually saw in the review UI).
  - For each story, apply Jeff's verdict from the review JSON:
      * verdict=correct → keep detector classification (story remains).
      * verdict=incorrect → apply note-based reclassification:
          - "not a story", "biblical story", "in the Mishnah",
            "reference to the Mishnah", "just a report/reference" → NOT_A_STORY
          - "yes ... story", "high confidence" → upgrade to YES
          - "low confidence" (only) → downgrade to LOW_CONFIDENCE
          - boundary-only complaint → keep story, leave segments alone
            (Jeff's boundary corrections are textual Hebrew markers; not
             automatable here. Wave 2's deterministic boundary snap/trim is
             the response to these.)
  - Segment indices come from v7 verbatim. Boundary IoU scoring tolerates
    small Wave-2 boundary shifts via the matcher's IoU >= 0.3 threshold.
  - 5 missed stories Jeff flagged are NOT included as golden labels here:
      * 45a, 53a were triage-recovered in Wave 1 (no Jeff segments given).
      * 71a 2nd-story, 33a baraita-embedded, 81b objection-embedded are
        Wave 3 work and Jeff hasn't given segment indices.
    They penalize Wave 1 and Wave 2 equally, so omitting them does not
    affect the Wave 2 vs Wave 1 gate.

Output: results/canonical/kiddushin_canonical.json
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
V7_PATH = ROOT / 'results' / 'v7' / 'kiddushin_v7.json'
FEEDBACK_PATH = ROOT / 'validation' / 'feedback' / 'kiddushin_review_2026-04-23.json'
OUTPUT_PATH = ROOT / 'results' / 'canonical' / 'kiddushin_canonical.json'


def reclassify(detected_cls: str, verdict: str, notes: str) -> str:
    """Map (detector classification, Jeff's verdict, Jeff's notes) → canonical."""
    if verdict == 'correct':
        return detected_cls
    n = (notes or '').lower().strip()

    # "Not a story" family — explicit reject.
    if (n.startswith('not a story')
            or n.startswith('not even')
            or 'biblical story' in n
            or 'biblical character' in n
            or 'this is a biblical' in n
            or 'in the mishnah' in n
            or 'reference to the mishnah' in n
            or "reference to the mishnah'" in n
            or 'just a report' in n
            or 'just a reference' in n
            or 'just legal' in n
            or 'not enough for a story' in n):
        return 'NOT_A_STORY'

    # Upgrade
    if n.startswith('yes') and 'story' in n[:120]:
        return 'YES'
    if 'high confidence' in n[:60]:
        return 'YES'

    # Downgrade / classification correction (still a story)
    if 'low confidence' in n[:60]:
        return 'LOW_CONFIDENCE'

    # Boundary-only or other: keep detector classification (still a story).
    return detected_cls


def main():
    with open(V7_PATH) as f:
        v7 = json.load(f)
    with open(FEEDBACK_PATH) as f:
        fb = json.load(f)

    # Build index: (page_ref, start, end) → review entry
    rev_idx = {}
    for k, r in fb['reviews'].items():
        suffix = k.rsplit('_', 1)[-1]
        m = re.match(r'(\d+)-(\d+)$', suffix)
        if not m:
            continue
        start, end = int(m.group(1)), int(m.group(2))
        rev_idx[(r['page_ref'], start, end)] = (k, r)

    pages_out = []
    matched = 0
    unmatched_reviews = set(rev_idx.keys())
    stats = {'YES': 0, 'HIGH_CONFIDENCE': 0, 'LOW_CONFIDENCE': 0,
             'NOT_A_STORY': 0, 'other': 0}

    for page in v7['pages']:
        ref = page['ref']
        out_stories = []
        for s in page.get('stories', []):
            # v7 may have NOT_A_STORY internal stories; drop them — only
            # real detector outputs are in Jeff's review UI.
            if s.get('classification') == 'NOT_A_STORY':
                continue
            key = (ref, s['start_segment'], s['end_segment'])
            review = rev_idx.get(key)
            new_s = {
                'start_segment': s['start_segment'],
                'end_segment': s['end_segment'],
                'classification': s.get('classification', ''),
                'spans_pages': s.get('spans_pages'),
                'start_segment_page2': s.get('start_segment_page2'),
                'end_segment_page2': s.get('end_segment_page2'),
                'one_sentence_summary': s.get('one_sentence_summary', ''),
            }
            if review:
                rev_key, rev = review
                new_s['classification'] = reclassify(
                    s.get('classification', ''), rev.get('verdict', ''),
                    rev.get('notes', '')
                )
                new_s['review_verdict'] = rev.get('verdict')
                new_s['review_notes'] = rev.get('notes', '')
                new_s['review_key'] = rev_key
                # Honor Jeff's spans_pages confirmation
                if rev.get('spans_pages') is not None:
                    new_s['spans_pages'] = rev.get('spans_pages')
                matched += 1
                unmatched_reviews.discard(key)
            stats[new_s['classification']] = stats.get(new_s['classification'], 0) + 1
            out_stories.append(new_s)

        pages_out.append({
            'ref': ref,
            'segments': page.get('segments', []),
            'stories': out_stories,
            'skipped_by_triage': page.get('skipped_by_triage', False),
        })

    canonical = {
        'tractate': 'Kiddushin',
        'version': 'kiddushin_canonical_v1',
        'source_run': str(V7_PATH.relative_to(ROOT)),
        'feedback_source': str(FEEDBACK_PATH.relative_to(ROOT)),
        'feedback_date': fb.get('date'),
        'reviews_matched': matched,
        'reviews_total': len(fb['reviews']),
        'reviews_unmatched': sorted([
            f"{r}_{s}-{e}" for (r, s, e) in unmatched_reviews
        ]),
        'classification_distribution': stats,
        'known_missing_stories': [
            'Kiddushin 45a — recovered in Wave 1 (no Jeff segment indices)',
            'Kiddushin 53a — recovered in Wave 1 (no Jeff segment indices)',
            'Kiddushin 71a — second story missed; Wave 3 work',
            'Kiddushin 33a — baraita-embedded; Wave 3 work',
            'Kiddushin 81b — objection-embedded; Wave 3 work',
        ],
        'pages': pages_out,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(canonical, f, indent=2, ensure_ascii=False)

    total_real = sum(
        1 for p in pages_out for s in p['stories']
        if s['classification'] not in ('NOT_A_STORY', 'NEEDS_REVIEW')
    )
    total_notstory = sum(
        1 for p in pages_out for s in p['stories']
        if s['classification'] == 'NOT_A_STORY'
    )
    print(f"Wrote {OUTPUT_PATH.relative_to(ROOT)}")
    print(f"  pages: {len(pages_out)}")
    print(f"  reviews matched: {matched}/{len(fb['reviews'])}")
    if unmatched_reviews:
        print(f"  unmatched (first 5): {sorted(unmatched_reviews)[:5]}")
    print(f"  canonical real stories: {total_real}")
    print(f"  canonical NOT_A_STORY: {total_notstory}")
    print(f"  classification distribution: {stats}")


if __name__ == '__main__':
    main()
