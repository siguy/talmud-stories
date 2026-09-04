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
                                      published database. One record per story
                                      the run processed, labelled or not, so the
                                      file is a complete account of the run.
  results/v11/wave5b/<name>.json      the boundary output, scoreable by
                                      scripts/score_boundary_targets.py and
                                      scripts/audit_text_spans.py

Story descriptions come from story_summary() in src/story_detector_v11.py — shared
with the Wave 5 span prompt, which had the same bug (story['summary'] is present on
0 of 262 stories; the detector writes 'one_sentence_summary').

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

from src.model_config import default_model, default_thinking_level

from src.clause_roles import (PROMPT_VERSION, assemble, build_prompt,  # noqa: E402
                              cross_language_disagreement, parse_labels,
                              speech_profile, split_english_sentences)
from src.story_detector_v11 import (V7StoryDetector, _assert_word_boundary,  # noqa: E402
                                    _clause_text_for_display, _split_into_clauses,
                                    story_summary)

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s [wave5b] %(message)s',
                    handlers=[logging.FileHandler(PROJECT_ROOT / 'project.log'),
                              logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)

# Per-story outcomes. Mutually exclusive and exhaustive: every story the run
# processes lands in exactly one, and they must sum to stories_labelled.
#   clause_roles      the model labelled the clauses and we narrowed a boundary
#   clause_kept_full  the model labelled the clauses and judged all of them in-story
#   no_clause_split   every side is a single clause; nothing to choose between
#   skipped           the model never answered. NOT a judgment (Lesson 21)
OUTCOMES = ('clause_roles', 'clause_kept_full', 'no_clause_split', 'skipped')

# A side's labelling status. 'clause_roles' is the only one carrying labels.
SIDE_STATUSES = ('clause_roles', 'no_clause_split', 'skipped')


def new_counts():
    return {k: 0 for k in OUTCOMES}


def load_env():
    env = PROJECT_ROOT / '.env'
    if env.exists():
        for line in env.read_text().splitlines():
            if line.strip() and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


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


# ---------------------------------------------------------------------------
# The shared write path. main() and reassemble() go through these and nothing
# else, so the two cannot drift apart (review §3.1).
# ---------------------------------------------------------------------------

def emit_span(story, side, hebrew, ranges, span, ref, seg_idx):
    """Write one side's text span onto `story`. True if it narrowed the boundary.

    The only place a span is written. Every offset comes from a clause range
    derived from the real string, and _assert_word_boundary makes that guarantee
    checkable rather than assumed (Lesson 16).
    """
    if side == 'start':
        if span['first'] <= 0:
            return False
        clause, offset, key = span['first'], ranges[span['first']][0], 'text_span_start'
    else:
        if span['last'] >= len(ranges) - 1:
            return False
        clause, offset, key = span['last'], ranges[span['last']][1], 'text_span_end'
    _assert_word_boundary(hebrew, offset, ref, seg_idx, side)
    story[key] = {'segment': seg_idx, 'char_offset': offset, 'clause_index': clause,
                  'clause_count': len(ranges), 'source': 'clause_roles'}
    return True


def aggregate_speech(sides, complete):
    """Speech composition over the story's labelled segments, each counted once.

    Only the first and last segments are labelled, so on a multi-segment story
    this covers the edges and not the middle — `complete` says which. Never
    called without labels: a profile computed from nothing is fabricated data,
    and `all_speech: False` reads as a finding (Lesson 21).
    """
    per_segment = {}
    for s in sides:
        per_segment.setdefault(s['segment'], speech_profile(s['labels']))
    in_story = sum(p['in_story_clauses'] for p in per_segment.values())
    spoken = sum(p['speech_clauses'] for p in per_segment.values())
    return {'in_story_clauses': in_story, 'speech_clauses': spoken,
            'speech_ratio': round(spoken / in_story, 3) if in_story else None,
            'all_speech': (spoken == in_story) if in_story else None,
            'complete': complete}


def finalize_story(story, ref, sides, counts, rule):
    """Write one story's spans, speech profile, provenance and counter.

    `sides` is one dict per side examined:
      {'side', 'segment', 'hebrew', 'ranges', 'labels', 'status'}

    Increments EXACTLY ONE counter, and a failed call gets a provenance that
    cannot be mistaken for a judgment: 'clause_kept_full' means the model read
    the segment and kept all of it; 'skipped' means it never answered.

    Returns (outcome, {side: assembled span}).
    """
    for s in sides:
        # reassemble() takes these from a file on disk, so check the contract.
        assert s['status'] in SIDE_STATUSES, f"unknown side status: {s['status']!r}"
        assert (s['labels'] is not None) == (s['status'] == 'clause_roles'), (
            f"{ref}: side {s['side']} says {s['status']!r} but "
            f"{'has' if s['labels'] else 'has no'} labels")

    if any(s['status'] == 'skipped' for s in sides):
        # A half-judged story's span is derived from partial input. Drop it and
        # keep the segment-level boundary — the safe, under-trimming direction.
        story.pop('text_span_start', None)
        story.pop('text_span_end', None)
        story['text_span_source'] = 'skipped'
        story['needs_review'] = True
        counts['skipped'] += 1
        return 'skipped', {}

    labelled = [s for s in sides if s['labels']]
    if not labelled:
        # Every side is one clause: nothing to choose. A named, logged outcome,
        # never a silent accident (docs/history/2026-08-28-PLAN-wave5.md).
        story['text_span_source'] = 'no_clause_split'
        counts['no_clause_split'] += 1
        return 'no_clause_split', {}

    spans, emitted = {}, False
    for s in labelled:
        span = assemble(s['labels'], len(s['ranges']), rule)
        spans[s['side']] = span
        if span.get('needs_review'):
            story['needs_review'] = True
        if emit_span(story, s['side'], s['hebrew'], s['ranges'], span, ref, s['segment']):
            emitted = True

    story['speech_profile'] = aggregate_speech(
        labelled, complete=story.get('start_segment') == story.get('end_segment'))
    outcome = 'clause_roles' if emitted else 'clause_kept_full'
    story['text_span_source'] = outcome
    counts[outcome] += 1
    return outcome, spans


def write_span_artifact(data, stats, name):
    """Stamp and write the boundary output. Both paths produce the same shape."""
    assert sum(stats['counts'].values()) == stats['stories_labelled'], (
        f"outcome buckets are not a partition: {stats['counts']} "
        f"sums to {sum(stats['counts'].values())} for "
        f"{stats['stories_labelled']} stories (Lesson 21)")
    data['version'] = f"{data.get('version', '?')}-wave5b"
    data['wave5b_stats'] = stats
    data.pop('text_span_policy', None)
    out = PROJECT_ROOT / 'results/v11/wave5b' / f'{name}.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=1))
    return out


def eligible_stories(data):
    """Yield (page, segs, story, start, end) for every story worth labelling."""
    for page in data['pages']:
        segs = {s.get('index', i): s for i, s in enumerate(page.get('segments', []))}
        for story in page.get('stories', []):
            if story.get('classification') == 'NOT_A_STORY':
                continue
            start, end = story.get('start_segment'), story.get('end_segment')
            if start is None or end is None or start not in segs or end not in segs:
                continue
            yield page, segs, story, start, end


# ---------------------------------------------------------------------------


def reassemble(data, args):
    """Rebuild boundaries from stored labels without calling the API.

    Labels are the expensive artifact; the assembly rule is one line of code. This
    makes comparing first_last vs longest_run free instead of a second full run —
    and correct, because the model is nondeterministic (Lesson 11), so a second
    run would confound the assembly rule with fresh labels.
    """
    store = json.loads(Path(args.from_labels).read_text())
    by_key = {(s['ref'], s['story']): s for s in store['stories']}
    counts = new_counts()
    processed, missing = 0, 0

    for page, segs, story, start, end in eligible_stories(data):
        rec = by_key.get((page['ref'], f'{start}-{end}'))
        if rec is None:
            missing += 1
            continue
        sides = []
        for side, seg_idx in (('start', start), ('end', end)):
            status = (rec.get('status') or {}).get(side)
            if status is None:
                continue
            blk = rec.get(side)
            if blk and blk['segment'] != seg_idx:
                raise ValueError(
                    f"{args.from_labels} has {page['ref']} story {start}-{end} "
                    f"{side} on segment {blk['segment']}, but {args.inp} has it on "
                    f"segment {seg_idx} — the labels came from a different input.")
            hebrew = segs[seg_idx].get('hebrew', '') or ''
            labels = None
            if blk:
                labels = {'hebrew': {int(k): v for k, v in blk['labels'].items()},
                          'english': {int(k): v for k, v in blk['english'].items()}}
            sides.append({'side': side, 'segment': seg_idx, 'hebrew': hebrew,
                          'ranges': _split_into_clauses(hebrew),
                          'labels': labels, 'status': status})
        processed += 1
        finalize_story(story, page['ref'], sides, counts, args.assembly)

    if missing:
        log.warning('%d stories in --in have no record in %s and were left untouched',
                    missing, Path(args.from_labels).name)
    stats = dict(store['_stats'])
    stats.update({'counts': counts, 'assembly_rule': args.assembly,
                  'stories_labelled': processed,
                  'stories_without_labels': missing,
                  'reassembled_from': Path(args.from_labels).name})
    out = write_span_artifact(data, stats, args.name)
    log.info('re-assembled with %s | %s -> %s',
             args.assembly, counts, out.relative_to(PROJECT_ROOT))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--in', dest='inp', required=True)
    ap.add_argument('--name', required=True, help='basename for both output artifacts')
    ap.add_argument('--model', default=default_model())
    ap.add_argument('--thinking', default=default_thinking_level())
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
    counts = new_counts()
    label_store, disagreements, speech_rows = [], [], []
    done, t0 = 0, time.time()

    for page, segs, story, start, end in eligible_stories(data):
        if args.limit and done >= args.limit:
            continue
        done += 1
        summary = story_summary(story)

        # A single-segment story has start_segment == end_segment. Labelling it
        # once and reusing the result halves the calls on the common case.
        sides, cache = [], {}
        for side, seg_idx in (('start', start), ('end', end)):
            hebrew = segs[seg_idx].get('hebrew', '') or ''
            if seg_idx not in cache:
                cache[seg_idx] = label_segment(
                    detector, summary, hebrew, segs[seg_idx].get('english', '') or '')
            ranges, labels, status = cache[seg_idx]
            sides.append({'side': side, 'segment': seg_idx, 'hebrew': hebrew,
                          'ranges': ranges, 'labels': labels, 'status': status})

        outcome, spans = finalize_story(story, page['ref'], sides, counts, args.assembly)

        # One record per processed story — labelled or not — so the labels file
        # is a complete account of the run and reassemble() reproduces it exactly.
        rec = {'ref': page['ref'], 'story': f'{start}-{end}', 'summary': summary,
               'outcome': outcome, 'status': {s['side']: s['status'] for s in sides}}
        for s in sides:
            if not s['labels']:
                continue
            rec[s['side']] = {
                'segment': s['segment'], 'n_clauses': len(s['ranges']),
                'span': spans[s['side']],
                'labels': {str(k): v for k, v in s['labels']['hebrew'].items()},
                'english': {str(k): v for k, v in s['labels']['english'].items()},
            }
        label_store.append(rec)

        if 'speech_profile' in story:
            speech_rows.append({'ref': page['ref'], 'story': f'{start}-{end}',
                                **story['speech_profile']})
        for seg_idx, labels in {s['segment']: s['labels'] for s in sides if s['labels']}.items():
            xl = cross_language_disagreement(labels)
            if xl['n_disagree']:
                disagreements.append({'ref': page['ref'], 'segment': seg_idx, **xl})

        if done % 20 == 0:
            log.info('  %d stories labelled (%.0fs)', done, time.time() - t0)

    elapsed = time.time() - t0
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

    out_path = write_span_artifact(data, stats, args.name)

    log.info('%s | %s | %.0fs', args.model, counts, elapsed)
    log.info('labels -> %s', labels_path.relative_to(PROJECT_ROOT))
    log.info('spans  -> %s', out_path.relative_to(PROJECT_ROOT))
    return 0


if __name__ == '__main__':
    sys.exit(main())
