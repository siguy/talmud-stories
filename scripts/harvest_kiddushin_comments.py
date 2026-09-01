#!/usr/bin/env python3
"""
Sort Jeff's 10 anchored Kiddushin remarks onto the axes they actually indict, and
join each to what our detector did with the passage it points at.

Per `work/2026-08-30-kiddushin-comments-harvest.md`, the sort is at the
**sentence** level, not the comment level: `c_02` carries two remarks in one
annotation (a boundary instruction plus an attribution note), so 10 comments
yield 11 remarks.

The classification is hand-assigned and recorded here to be auditable and
arguable — not to look computed. Jeff's words are stored verbatim; anything
that is our reading is in `our_reading`, never folded into his text.

These remarks are CIRCULAR: they are comments on his own list, which we then
compared against our output. Usable for precision, criteria and boundaries;
never for recall (FRAMEWORK §3).

Output: results/expert_lists/kiddushin_comments_harvested.json
"""

import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / 'results/expert_lists/kiddushin_2005.json'
RECALL = REPO / 'results/v11/triage_recall/kiddushin_baseline_today.json'
RUN = REPO / 'results/v10/wave4_notrim/kiddushin_v10_notrim.json'
DEST = REPO / 'results/expert_lists/kiddushin_comments_harvested.json'

# axis: boundary | classification | borderline | attribution | provenance | open_question
# quote_polarity: CUT (quoted Hebrew is text to remove) | ADD (text to include) | None
REMARKS = {
    'c_01': dict(axis='boundary', quote_polarity='CUT',
                 our_reading="Jeff names text to REMOVE from the end: the Talmud's own "
                             "comment on the alternative story. Polarity matters — read "
                             "as ADD this anchors the target one clause off."),
    'c_02#a': dict(axis='boundary', quote_polarity='ADD',
                   our_reading='Jeff gives the Hebrew to INCLUDE, verbatim. A directly '
                               'usable boundary target.'),
    'c_02#b': dict(axis='attribution', quote_polarity=None,
                   our_reading='A source-critical attribution note, not a boundary or '
                               'classification instruction. Carries no target.'),
    'c_03': dict(axis='classification', quote_polarity=None,
                 our_reading='"report/tradition" as a category distinct from story — a '
                             'distinction our criteria doc does not currently make.'),
    'c_04': dict(axis='classification', quote_polarity=None,
                 our_reading='Halakhic question-and-answer excluded even though it '
                             '"related what happened". Narration of an event is not '
                             'sufficient.'),
    'c_05': dict(axis='classification', quote_polarity=None,
                 our_reading='A teirutz is dialectical argumentation, not narrative. '
                             'Same shape as c_04.'),
    'c_00': dict(axis='borderline', quote_polarity=None,
                 our_reading='"if at all" — explicitly contested, not a clean No. '
                             'Exactly the case the proposed `borderline` status is for.'),
    'c_07': dict(axis='borderline', quote_polarity=None,
                 our_reading='"Not sure" — contested, on a story he nonetheless listed.'),
    'c_08': dict(axis='borderline', quote_polarity=None,
                 our_reading='"Not sure ... Very minimal" — contested, on a story he '
                             'nonetheless listed.'),
    'c_06': dict(axis='provenance', quote_polarity=None,
                 our_reading='The הוספתי--י.ר. marker: Jeff recording that HE added this '
                             'entry. Already reflected in blind=false for kiddushin_049.'),
    'c_note_28': dict(axis='open_question', quote_polarity=None,
                      our_reading='A question addressed to us ("Check parallel"), not a '
                                  'verdict. Owed an answer; carries no target.'),
}

SENTENCE_SPLIT = {
    'c_02': {
        'c_02#a': 'A few more words should be included in the story:',
        'c_02#b': 'These seem to be the words of Rav Hisda.',
    },
}


def main():
    data = json.loads(SRC.read_text())
    stories = {s['id']: s for s in data['stories']}

    # STRICT coverage only. The recall artifact's `in_detector` uses the loose
    # window test, which credits a proposal anywhere near the story — on these
    # remarks it credits a DIFFERENT passage on the same daf three times out of
    # six. Asking "did Jeff doubt a passage we assert is a story" demands that
    # our span actually contain his text, so the join is rebuilt from the
    # located segments against real spans.
    recall = {}
    if RECALL.exists():
        for r in json.loads(RECALL.read_text()):
            recall.setdefault((r['ref'], r['text'][:60]), r)

    spans = {}
    if RUN.exists():
        for pg in json.loads(RUN.read_text())['pages']:
            for st in (pg.get('stories') or []) + (pg.get('mishnah_stories') or []):
                a, b = st.get('start_segment'), st.get('end_segment')
                if a is None or b is None:
                    continue
                spans.setdefault(pg['ref'], []).append((a, b, st.get('classification')))

    def covering(row):
        """Spans in the shipped run that actually contain Jeff's located text."""
        hits = []
        for pref, idx in (row.get('located') or []):
            for a, b, cls in spans.get(pref, []):
                if a <= idx <= b:
                    hits.append({'ref': pref, 'start': a, 'end': b, 'classification': cls})
        return [dict(t) for t in {tuple(sorted(h.items())) for h in hits}]

    rows = []
    for c in data['comments']:
        cid = c['id']
        pieces = {cid: c['text']}
        if cid in SENTENCE_SPLIT:
            text = c['text']
            pieces = {}
            for sub, marker in SENTENCE_SPLIT[cid].items():
                i = text.find(marker)
                assert i >= 0, f"{sub}: marker not found in {cid}"
                pieces[sub] = marker if sub.endswith('#b') else text[i:].split('\r')[0]
        for key, verbatim in pieces.items():
            spec = REMARKS.get(key)
            assert spec, f"no hand-assigned axis for remark {key}"
            story = stories.get(c['attached_story_id'], {})
            rrow = recall.get((story.get('ref'), story.get('text', '')[:60]))
            cov = covering(rrow) if rrow else []
            calls = sorted({c['classification'] for c in cov})
            rows.append({
                'remark_id': key,
                'comment_id': cid,
                'anchor_cp': c.get('anchor_cp'),
                'story_id': c['attached_story_id'],
                'ref': story.get('ref'),
                'expert_blind': story.get('blind'),
                'counts_for_recall': story.get('counts_for_recall'),
                'jeff_verbatim': verbatim,
                'axis': spec['axis'],
                'quote_polarity': spec['quote_polarity'],
                'our_reading': spec['our_reading'],
                'detector_spans_covering': cov,
                'detector_calls_strict': calls,
                'detector_asserts_story': bool(
                    [c for c in calls if c in ('YES', 'HIGH_CONFIDENCE', 'LOW_CONFIDENCE')]),
                'recall_credits_loose': (rrow or {}).get('in_detector'),
                'story_text': story.get('text', '')[:200],
            })

    assert len(rows) == 11, f"expected 11 sentence-level remarks, got {len(rows)}"
    counts = Counter(r['axis'] for r in rows)

    # Where a borderline/classification doubt of Jeff's meets our own verdict.
    doubted = [r for r in rows if r['axis'] in ('borderline', 'classification')]
    disagree = [r for r in doubted if r['detector_asserts_story']]
    silent = [r for r in doubted if not r['detector_spans_covering']]
    overcredited = [r for r in doubted
                    if not r['detector_spans_covering'] and r['recall_credits_loose']]

    out = {
        'built_by': 'scripts/harvest_kiddushin_comments.py',
        'source': str(SRC.relative_to(REPO)),
        'kind': 'CIRCULAR — comments on his own list, compared against our output. '
                'Never usable for recall (FRAMEWORK §3).',
        'comments': len(data['comments']),
        'remarks_sentence_level': len(rows),
        'axes': dict(counts),
        'jeff_doubts_and_we_assert_story': [
            [r['remark_id'], r['ref'], r['detector_calls_strict']] for r in disagree],
        'jeff_doubts_and_we_propose_nothing_there': [
            [r['remark_id'], r['ref']] for r in silent],
        'loose_recall_credits_us_with_a_passage_we_do_not_cover': [
            [r['remark_id'], r['ref']] for r in overcredited],
        'remarks': rows,
    }
    DEST.write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print(f"comments: {len(data['comments'])} -> sentence-level remarks: {len(rows)}")
    for axis, n in counts.most_common():
        print(f"  {axis:16s} {n}")
    print(f"\nboundary targets available: "
          f"{[r['remark_id'] for r in rows if r['axis'] == 'boundary']}")
    print("\nJeff doubts it AND we assert it IS a story (real disagreement):")
    for r in disagree:
        print(f"  {r['remark_id']:8s} {r['ref']:16s} {r['detector_calls_strict']}")
    print("Jeff doubts it AND we propose nothing covering it (agreement by silence):")
    for r in silent:
        print(f"  {r['remark_id']:8s} {r['ref']:16s}")
    print("Loose recall credits us for a passage we do not actually cover:")
    for r in overcredited:
        print(f"  {r['remark_id']:8s} {r['ref']:16s}")
    print(f"\nWrote {DEST.relative_to(REPO)}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
