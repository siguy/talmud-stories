#!/usr/bin/env python3
"""Correct an over-broad negative claim on two golden entries. One-shot, idempotent.

`scripts/add_expert_list_stories_2026-08-30.py` stamped all five expert-list additions
with "Never proposed by any detector run through v10", having checked only
`results/v10/wave4_notrim/`. A text search across all 53 run files on 2026-08-30 found
two of them proposed by earlier configurations and classified NOT_A_STORY:

    Ketubot 20a segs 2-3   results/v5/pages_2-39.json              NOT_A_STORY
    Ketubot 53a seg 11     results/v7/ablation_v6_triage_merge.json NOT_A_STORY

Both verified at 100% Hebrew character-4-gram coverage of Jeff's own text, so they are
the same passages and not segment-index collisions. For these two the failure is
Classification, not Detection -- the same re-diagnosis commit abdc4af made for 77a.

WHAT THIS DOES NOT DO. It does not remove a story, change a classification, or touch
any of Jeff's judgments. It corrects a provenance note we wrote about our own runs,
and it PRESERVES the superseded claim in the entry's `corrections` list -- the golden's
own convention -- so the record shows what we believed and why it changed.

Usage:  python3 scripts/correct_detector_status_2026-08-30.py [--apply]
Without --apply it prints the diff and writes nothing.
"""
import argparse
import json
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
GOLDEN = PROJECT_ROOT / 'results' / 'canonical' / 'ketubot_canonical.json'
CORRECTION_SOURCE = 'detector_status_scope_correction_2026-08-30'

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s [%(name)s] %(message)s')
log = logging.getLogger('correct-detector-status')

CORRECTIONS = {
    ('Ketubot 20a', 2, 3): {
        'never_detected': False,
        'proposed_by_detector': True,
        'detector_status': (
            "Proposed at segments 2-3 by results/v5/pages_2-39.json and classified "
            "NOT_A_STORY (100% Hebrew 4-gram coverage of Jeff's text, verified 2026-08-30). "
            "Not proposed by any run from v7 on, where Stage 1 triage discards the page "
            "before Stage 2 sees it."),
        'loss_detail': (
            "Under the current pipeline, Stage 1 event triage discards both Ketubot 19b and "
            "20a, so the story detector never sees this page. But v5 -- which predates Stage 1 "
            "(added in v7, commit 84c9f43) -- DID examine it and DID propose exactly segments "
            "2-3, then classified them NOT_A_STORY. So the passage has been both found and "
            "rejected by this project; the current loss is triage, the earlier one was "
            "Classification."),
        'evidence': 'results/v5/pages_2-39.json',
    },
    ('Ketubot 53a', 11, 11): {
        'never_detected': False,
        'proposed_by_detector': True,
        'detector_status': (
            "Proposed at segment 11 by results/v7/ablation_v6_triage_merge.json and classified "
            "NOT_A_STORY (100% Hebrew 4-gram coverage of Jeff's text, verified 2026-08-30). "
            "That is an ablation configuration, not a production run; no production run has "
            "proposed it."),
        'loss_detail': (
            "In the current pipeline the page survives triage and is examined; Stage 2 proposes "
            "one span on it (segments 12-12, which is in the golden) and nothing at segment 11. "
            "But the v6-triage+merge ablation DID propose exactly segment 11 and classified it "
            "NOT_A_STORY, so the passage has been found and rejected here too."),
        'evidence': 'results/v7/ablation_v6_triage_merge.json',
    },
}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--apply', action='store_true', help='write the change (default: dry run)')
    args = ap.parse_args()

    doc = json.loads(GOLDEN.read_text(encoding='utf-8'))
    before_stories = sum(len(p.get('stories', [])) for p in doc['pages'])
    touched = 0

    for page in doc['pages']:
        for story in page.get('stories', []):
            key = (page['ref'], story.get('start_segment'), story.get('end_segment'))
            fix = CORRECTIONS.get(key)
            if not fix:
                continue
            prov = story.get('provenance') or {}
            if any(c.get('source') == CORRECTION_SOURCE for c in (story.get('corrections') or [])):
                log.info('%s seg %s-%s: already corrected, skipping', *key)
                continue

            log.info('%s seg %s-%s', *key)
            log.info('    never_detected  %s -> %s', story.get('never_detected'),
                     fix['never_detected'])
            log.info('    proposed_by_detector  %s -> %s', prov.get('proposed_by_detector'),
                     fix['proposed_by_detector'])
            log.info('    detector_status was: %s', prov.get('detector_status', '')[:88])
            log.info('    detector_status now: %s', fix['detector_status'][:88])

            # Preserve what we superseded, in the golden's own corrections convention.
            story.setdefault('corrections', []).append({
                'action': 'correct_detector_status_scope',
                'reason': (
                    'The original note claimed "Never proposed by any detector run through v10" '
                    'but only checked results/v10/wave4_notrim/. A text search of all 53 run '
                    'files found this passage proposed by ' + fix['evidence'] + ' and classified '
                    'NOT_A_STORY, at 100% Hebrew 4-gram coverage. For this entry the failure is '
                    'Classification, not Detection.'),
                'source': CORRECTION_SOURCE,
                'superseded': {
                    'never_detected': story.get('never_detected'),
                    'proposed_by_detector': prov.get('proposed_by_detector'),
                    'detector_status': prov.get('detector_status'),
                    'loss_detail': prov.get('loss_detail'),
                },
                'auto_applied': True,
            })

            story['never_detected'] = fix['never_detected']
            prov['never_detected'] = fix['never_detected']
            prov['proposed_by_detector'] = fix['proposed_by_detector']
            prov['detector_status'] = fix['detector_status']
            prov['loss_detail'] = fix['loss_detail']
            story['provenance'] = prov
            touched += 1

    after_stories = sum(len(p.get('stories', [])) for p in doc['pages'])
    if after_stories != before_stories:
        sys.exit(f'REFUSING: story count moved {before_stories} -> {after_stories}')
    if touched not in (0, len(CORRECTIONS)):
        sys.exit(f'REFUSING: expected to touch {len(CORRECTIONS)} entries, touched {touched}')

    log.info('%d entries corrected; story count unchanged at %d', touched, after_stories)
    if not args.apply:
        log.info('DRY RUN -- nothing written. Re-run with --apply.')
        return
    GOLDEN.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding='utf-8')
    log.info('wrote %s', GOLDEN.relative_to(PROJECT_ROOT))


if __name__ == '__main__':
    main()
