#!/usr/bin/env python3
"""
Wave 5b: label every clause's role, then assemble boundaries deterministically.

Reads a no-trim detector output, and for each story labels the clauses of its first
and last segment (role + speech, Hebrew and English), then computes the text span
from those labels. The model never emits a boundary or a number.

Writes TWO artifacts:
  results/clause_labels/<name>.json   the labels — a reusable asset. They are
                                      features for the FP classifier (Lesson 7),
                                      the input to Wave 6's speech-act question,
                                      and the basis for English spans in the
                                      published database.
  results/v11/wave5b/<name>.json      the boundary output, scoreable by
                                      scripts/score_boundary_targets.py and
                                      scripts/audit_text_spans.py

Fixes a v10 bug carried into Wave 5: the span prompt read story['summary'], which
is present on 0 of 106 stories. The detector writes 'one_sentence_summary'.

Usage:
  python3 scripts/run_clause_labeling.py \
      --in results/v10/wave4_notrim/kiddushin_v10_notrim.json \
      --name kiddushin_v11_wave5b \
      --model gemini-3.7-flash --thinking high --assembly first_last
"""
import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.clause_roles import (PROMPT_VERSION, assemble, build_prompt,  # noqa: E402
                              cross_language_disagreement, parse_labels,
                              speech_profile, split_english_sentences)
from src.story_detector_v11 import (V7StoryDetector, _assert_word_boundary,  # noqa: E402
                                    _clause_text_for_display, _split_into_clauses)

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s [wave5b] %(message)s',
                    handlers=[logging.FileHandler(PROJECT_ROOT / 'project.log'),
                              logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)


def load_env():
    env = PROJECT_ROOT / '.env'
    if env.exists():
        for line in env.read_text().splitlines():
            if line.strip() and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def story_summary(story):
    """v10 wrote one_sentence_summary; the old span prompt read 'summary' (never present)."""
    for key in ('one_sentence_summary', 'summary', 'text'):
        val = story.get(key)
        if val:
            return str(val)[:400]
    crit = (story.get('criteria') or {}).get('multiple_events') or {}
    events = crit.get('events') or []
    return '; '.join(events)[:400] if events else '(no summary available)'


def label_segment(detector, summary, hebrew, english):
    """One call -> labels for one segment's clauses. None on any failure."""
    ranges = _split_into_clauses(hebrew)
    clauses = [_clause_text_for_display(hebrew, r) for r in ranges]
    sentences = split_english_sentences(english)
    if len(ranges) <= 1:
        return ranges, None, 'no_clause_split'
    prompt = build_prompt(summary, clauses, sentences)
    try:
        raw = detector._call_google(prompt, max_tokens=8192, json_mode=True)
    except Exception as exc:
        log.warning('API error: %s', exc)
        return ranges, None, 'skipped'
    labels = parse_labels(detector._parse_json_response(raw), len(ranges), len(sentences))
    return ranges, labels, ('clause_roles' if labels else 'skipped')


def reassemble(data, args):
    """Rebuild boundaries from stored labels without calling the API.

    Labels are the expensive artifact; the assembly rule is one line of code. This
    makes comparing first_last vs longest_run free instead of a second full run.
    """
    store = json.loads(Path(args.from_labels).read_text())
    by_key = {(s['ref'], s['story']): s for s in store['stories']}
    counts = {'clause_roles': 0, 'clause_kept_full': 0, 'no_clause_split': 0, 'skipped': 0}
    for page in data['pages']:
        segs = {s.get('index', i): s for i, s in enumerate(page.get('segments', []))}
        for story in page.get('stories', []):
            if story.get('classification') == 'NOT_A_STORY':
                continue
            rec = by_key.get((page['ref'], f"{story.get('start_segment')}-{story.get('end_segment')}"))
            if not rec:
                continue
            story.pop('text_span_start', None)
            story.pop('text_span_end', None)
            emitted = False
            for side in ('start', 'end'):
                blk = rec.get(side)
                if not blk:
                    continue
                hebrew = segs[blk['segment']].get('hebrew', '') or ''
                ranges = _split_into_clauses(hebrew)
                labels = {'hebrew': {int(k): v for k, v in blk['labels'].items()},
                          'english': {int(k): v for k, v in blk['english'].items()}}
                span = assemble(labels, len(ranges), args.assembly)
                if side == 'start' and span['first'] > 0:
                    off = ranges[span['first']][0]
                    _assert_word_boundary(hebrew, off, page['ref'], blk['segment'], 'start')
                    story['text_span_start'] = {'segment': blk['segment'], 'char_offset': off,
                                                'clause_index': span['first'],
                                                'clause_count': len(ranges), 'source': 'clause_roles'}
                    emitted = True
                if side == 'end' and span['last'] < len(ranges) - 1:
                    off = ranges[span['last']][1]
                    _assert_word_boundary(hebrew, off, page['ref'], blk['segment'], 'end')
                    story['text_span_end'] = {'segment': blk['segment'], 'char_offset': off,
                                              'clause_index': span['last'],
                                              'clause_count': len(ranges), 'source': 'clause_roles'}
                    emitted = True
            story['text_span_source'] = 'clause_roles' if emitted else 'clause_kept_full'
            counts['clause_roles' if emitted else 'clause_kept_full'] += 1
    stats = dict(store['_stats'])
    stats['assembly_rule'] = args.assembly
    stats['reassembled_from'] = Path(args.from_labels).name
    stats['counts'] = counts
    data['wave5b_stats'] = stats
    out = PROJECT_ROOT / 'results/v11/wave5b' / f'{args.name}.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=1))
    log.info('re-assembled with %s | %s -> %s', args.assembly, counts, out.relative_to(PROJECT_ROOT))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--in', dest='inp', required=True)
    ap.add_argument('--name', required=True, help='basename for both output artifacts')
    ap.add_argument('--model', default='gemini-3.7-flash')
    ap.add_argument('--thinking', default='high')
    ap.add_argument('--assembly', default='first_last', choices=['first_last', 'longest_run'])
    ap.add_argument('--limit', type=int, help='label only the first N stories (smoke test)')
    ap.add_argument('--from-labels', help='re-assemble from an existing labels file with NO '
                                          'API calls — use to compare assembly rules for free')
    args = ap.parse_args()

    load_env()
    data = json.loads(Path(args.inp).read_text())

    if args.from_labels:
        return reassemble(data, args)

    detector = V7StoryDetector(model_name=args.model, thinking_level=args.thinking)
    if not detector.client:
        log.error('no Gemini client — check GOOGLE_API_KEY')
        return 1

    log.info('model=%s thinking=%s prompt=%s assembly=%s',
             args.model, args.thinking, PROMPT_VERSION, args.assembly)
    counts = {'clause_roles': 0, 'clause_kept_full': 0, 'no_clause_split': 0, 'skipped': 0}
    label_store, disagreements, speech_rows = [], [], []
    done, t0 = 0, time.time()

    for page in data['pages']:
        segs = {s.get('index', i): s for i, s in enumerate(page.get('segments', []))}
        for story in page.get('stories', []):
            if story.get('classification') == 'NOT_A_STORY':
                continue
            if args.limit and done >= args.limit:
                continue
            start, end = story.get('start_segment'), story.get('end_segment')
            if start is None or end is None or start not in segs or end not in segs:
                continue
            done += 1
            summary = story_summary(story)
            emitted = False
            seen_speech = []
            per_story = {'ref': page['ref'], 'story': f'{start}-{end}', 'summary': summary}

            # A single-segment story has start_segment == end_segment. Labelling it
            # once and reusing the result halves the calls on the common case.
            cache = {}
            for side, seg_idx in (('start', start), ('end', end)):
                seg = segs[seg_idx]
                hebrew = seg.get('hebrew', '') or ''
                if seg_idx in cache:
                    ranges, labels, status = cache[seg_idx]
                else:
                    ranges, labels, status = label_segment(
                        detector, summary, hebrew, seg.get('english', '') or '')
                    cache[seg_idx] = (ranges, labels, status)
                if labels is None:
                    if side == 'start' or start != end:
                        counts['no_clause_split' if status == 'no_clause_split' else 'skipped'] += 1
                    continue

                span = assemble(labels, len(ranges), args.assembly)
                per_story[side] = {
                    'segment': seg_idx, 'n_clauses': len(ranges), 'span': span,
                    'labels': {str(k): v for k, v in labels['hebrew'].items()},
                    'english': {str(k): v for k, v in labels['english'].items()},
                }
                xl = cross_language_disagreement(labels)
                if xl['n_disagree']:
                    disagreements.append({'ref': page['ref'], 'segment': seg_idx, **xl})
                if side == 'start' or start != end:
                    seen_speech.append(speech_profile(labels))

                if side == 'start' and span['first'] > 0:
                    off = ranges[span['first']][0]
                    _assert_word_boundary(hebrew, off, page['ref'], seg_idx, 'start')
                    story['text_span_start'] = {'segment': seg_idx, 'char_offset': off,
                                                'clause_index': span['first'],
                                                'clause_count': len(ranges),
                                                'source': 'clause_roles'}
                    emitted = True
                if side == 'end' and span['last'] < len(ranges) - 1:
                    off = ranges[span['last']][1]
                    _assert_word_boundary(hebrew, off, page['ref'], seg_idx, 'end')
                    story['text_span_end'] = {'segment': seg_idx, 'char_offset': off,
                                              'clause_index': span['last'],
                                              'clause_count': len(ranges),
                                              'source': 'clause_roles'}
                    emitted = True
                if span.get('needs_review'):
                    story['needs_review'] = True

            # Aggregate speech across the story's labelled segments.
            # NOTE: only the FIRST and LAST segments are labelled, so for a
            # multi-segment story this covers the edges, not the middle. Exact for
            # single-segment stories, which are the majority.
            in_story = sum(p['in_story_clauses'] for p in seen_speech)
            sp = sum(p['speech_clauses'] for p in seen_speech)
            story['speech_profile'] = {
                'in_story_clauses': in_story, 'speech_clauses': sp,
                'speech_ratio': round(sp / in_story, 3) if in_story else None,
                'all_speech': (in_story > 0 and sp == in_story),
                'complete': start == end,
            }
            speech_rows.append({'ref': page['ref'], 'story': f'{start}-{end}',
                                **story['speech_profile']})
            story['text_span_source'] = 'clause_roles' if emitted else 'clause_kept_full'
            counts['clause_roles' if emitted else 'clause_kept_full'] += 1
            label_store.append(per_story)
            if done % 20 == 0:
                log.info('  %d stories labelled (%.0fs)', done, time.time() - t0)

    elapsed = time.time() - t0
    covered = sum(d['clauses_covered'] for d in disagreements) or 0
    stats = {
        'counts': counts, 'model': args.model, 'thinking_level': args.thinking,
        'prompt_version': PROMPT_VERSION, 'assembly_rule': args.assembly,
        'stories_labelled': done, 'elapsed_seconds': round(elapsed, 1),
        'cross_language_disagreements': len(disagreements),
        'speech_only_stories': sum(1 for r in speech_rows if r.get('all_speech')),
        'speech_only_complete': sum(1 for r in speech_rows if r.get('all_speech') and r.get('complete')),
    }

    labels_path = PROJECT_ROOT / 'results/clause_labels' / f'{args.name}.json'
    labels_path.parent.mkdir(parents=True, exist_ok=True)
    labels_path.write_text(json.dumps(
        {'_stats': stats, 'stories': label_store,
         'cross_language_disagreements': disagreements, 'speech_profiles': speech_rows},
        ensure_ascii=False, indent=1))

    data['version'] = f"{data.get('version', '?')}-wave5b"
    data['wave5b_stats'] = stats
    data.pop('text_span_policy', None)
    out_path = PROJECT_ROOT / 'results/v11/wave5b' / f'{args.name}.json'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=1))

    log.info('%s | %s | %.0fs', args.model, counts, elapsed)
    log.info('labels -> %s', labels_path.relative_to(PROJECT_ROOT))
    log.info('spans  -> %s', out_path.relative_to(PROJECT_ROOT))
    return 0


if __name__ == '__main__':
    sys.exit(main())
