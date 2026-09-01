#!/usr/bin/env python3
"""
Capture the 2026-01-08 Ketubot round — the earliest round Jeff signed by name, and
the only one no ruler has ever read.

`STATE.md` lists three feedback files as "expert verdicts on disk that no ruler
reads". Checked 2026-08-31, they are not equivalent:

  ketubot_review_Jeffrey_Rubenstein_2026-01-08.json  25 real expert verdicts  <- THIS
  validations_v4_2026-01-25.json                     `validations` is EMPTY ({})
  jeff_v4.1_validation.json                          an automated eval trace
                                                     (expected / ai_result / confidence),
                                                     not expert judgement at all

So the standing "three unread rounds" note overstates it: **one** file carries expert
verdicts. It is invisible for a mechanical reason — `build_ruler.load_reviews()` requires
`reviews`/`feedback` to be a **dict** keyed `"<ref>_<start>-<end>"`, and this round stores
a **list** of `{ref, feedback_type, notes, ...}` with no segment span. It is skipped by an
`isinstance(items, dict)` guard, silently, exactly like every other file that fails to
match the expected shape.

Two things make it worth recovering rather than writing off:

1. **9 of its 25 refs are cross-page** (`Ketubot 10b-11a`) and are covered by NO round any
   ruler reads. Cross-page stories are the project's known weak spot — every one of the 12
   Ketubot stories in the strict/loose recall gap is a cross-page story.
2. **24 of the 25 carry notes**, and they are the clearest statements of Jeff's criteria in
   the corpus, six months before the criteria doc was written:
   *"A story must be descriptive -- what did happen"*;
   *"Narrative elements in legal codes or rulings are not stories."*

This script normalises the round and reports what is recoverable. It deliberately does
**not** fold anything into the golden — that is `golden-completeness`'s job, and burying a
golden change inside a capture script is Lesson 1's failure.

Output: results/rulers/january_2026_round_captured.json
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / 'validation/feedback/ketubot_review_Jeffrey_Rubenstein_2026-01-08.json'
DEST = REPO / 'results/rulers/january_2026_round_captured.json'

# feedback_type -> the vocabulary build_ruler already understands.
VERDICT_MAP = {
    'false_positive': 'incorrect',
    'correct': 'correct',
    None: None,          # one item carries no type; it is reported, not guessed
}

CROSS_PAGE = re.compile(r'^(\S+)\s+(\d+[ab])-(\d+[ab])$')


def ruler_covered_refs():
    """Refs any round the ruler DOES read has a verdict for."""
    seen = set()
    for pat in ('validation/feedback/*.json', 'jeff comms/*.json'):
        for path in sorted(REPO.glob(pat)):
            try:
                data = json.loads(path.read_text())
            except Exception:
                continue
            if not isinstance(data, dict):
                continue
            items = data.get('reviews') or data.get('feedback')
            if not isinstance(items, dict):
                continue
            for key in items:
                seen.add(key.rsplit('_', 1)[0])
    return seen


def main():
    data = json.loads(SRC.read_text())
    covered = ruler_covered_refs()

    rows, unmapped = [], []
    for item in data['feedback']:
        ref = item['ref']
        ftype = item.get('feedback_type')
        if ftype not in VERDICT_MAP:
            unmapped.append((ref, ftype))
            continue
        rows.append({
            'ref': ref,
            'feedback_type': ftype,
            'verdict': VERDICT_MAP[ftype],
            'note': (item.get('notes') or '').strip(),
            'story_confidence': item.get('story_confidence'),
            'story_type': item.get('story_type'),
            # Boundary and merge signal this round carries and no other stores
            # in a structured field at all.
            'length_adjustment': item.get('length_adjustment'),
            'spans_multiple_pages': item.get('spans_multiple_pages'),
            'is_cross_page_ref': bool(CROSS_PAGE.match(ref)),
            'covered_by_a_ruler_read_round': ref in covered,
        })

    assert not unmapped, f"unmapped feedback_type values: {unmapped}"
    assert len(rows) == len(data['feedback']), "dropped a feedback item"

    uncovered = [r for r in rows if not r['covered_by_a_ruler_read_round']]
    cross = [r for r in rows if r['is_cross_page_ref']]
    with_notes = [r for r in rows if r['note']]
    with_len = [r for r in rows if r['length_adjustment'] not in (None, '', 'none')]
    spans = [r for r in rows if r['spans_multiple_pages']]

    out = {
        'built_by': 'scripts/capture_january_round.py',
        'source': str(SRC.relative_to(REPO)),
        'reviewer': data.get('reviewer_name'),
        'reviewed_at': data.get('reviewed_at'),
        'tractate': data.get('tractate'),
        'kind': 'CIRCULAR — verdicts on our own v4-era proposals. Precision and criteria '
                'only, never recall (FRAMEWORK §3).',
        'why_no_ruler_reads_it': (
            "build_ruler.load_reviews() requires reviews/feedback to be a dict keyed "
            "'<ref>_<start>-<end>'. This round is a list of {ref, feedback_type, notes} "
            "with no segment span, so an isinstance(items, dict) guard skips it silently."),
        'blocker_for_folding_in': (
            "No segment spans. Every other round names '<ref>_<start>-<end>'; this one "
            "names only the daf. The verdicts cannot be attached to a proposal without "
            "re-deriving which v4 story on that daf each refers to — and v4 output is "
            "not on disk. The NOTES are usable as criteria evidence regardless, and are "
            "the part worth recovering first."),
        'verdicts': len(rows),
        'verdict_counts': dict(Counter(r['verdict'] for r in rows)),
        'with_notes': len(with_notes),
        'cross_page_refs': len(cross),
        'not_covered_by_any_ruler_read_round': [r['ref'] for r in uncovered],
        'carry_length_adjustment': len(with_len),
        'flagged_spans_multiple_pages': len(spans),
        'rows': rows,
    }
    DEST.write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print(f"{data.get('reviewer_name')} — {data.get('tractate')} — {data.get('reviewed_at')[:10]}")
    print(f"  verdicts:                       {len(rows)}  {out['verdict_counts']}")
    print(f"  with notes:                     {len(with_notes)}")
    print(f"  cross-page refs:                {len(cross)}")
    print(f"  NOT covered by any read round:  {len(uncovered)}")
    print(f"  carry length_adjustment:        {len(with_len)}")
    print(f"  flagged spans_multiple_pages:   {len(spans)}")
    print(f"\n  uncovered refs: {[r['ref'] for r in uncovered]}")
    print(f"\nWrote {DEST.relative_to(REPO)}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
