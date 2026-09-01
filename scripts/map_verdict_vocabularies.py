#!/usr/bin/env python3
"""Map every banked review verdict onto the per-axis shape — the Phase B gate.

`work/2026-08-30-review-verdict-axes.md` makes this a gate and puts it BEFORE
the UI: *assert every existing verdict maps to exactly one new shape.* Three
vocabularies exist, and the trap is Lesson 3's:

    a `correct` on ALREADY-CORRECTED data is not a `correct` on BASE data.

Treating them alike lets the canonical round's "the correction was right"
override the earlier round's "incorrect" that triggered the correction, silently
undoing it. So every round carries `applies_to`, and nothing in this module is
allowed to compare a verdict across that line.

What the mapping can and cannot recover
---------------------------------------
`adjust` is the one old token that already carries an axis: it means "this IS a
story and the boundary is wrong", and mapping it to `is_story=yes` +
`extent=wrong_unspecified` is a *recovery*. Everything else is lossy in one
direction: a bare `incorrect` pooled four capabilities into one button, and no
mapping table can un-pool it after the fact. Those rows are marked
`lossy=True` rather than guessed into an axis (FRAMEWORK §7) — the width of the
Classification range is exactly this loss, and Phase B stops it widening
GOING FORWARD, not backward.

An unknown verdict token RAISES. A loader that `continue`s past an input it does
not recognise is how a signed 25-verdict round stayed invisible for eight months
(Lesson 38); this one counts and names everything it drops.

Run:  python3 scripts/map_verdict_vocabularies.py
Writes results/rulers/verdict_vocabulary_map.json
"""
from __future__ import annotations

import importlib.util
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _round_sources():
    """The round -> detector-version map, imported rather than re-derived.

    CLAUDE.md: extend ROUND_SOURCES, do not re-derive it. A second copy is how
    two files come to disagree about which detector a verdict judged, which is
    the exact ambiguity Lesson 36 is about.
    """
    spec = importlib.util.spec_from_file_location(
        'resolve_unclassified_notes', REPO / 'scripts' / 'resolve_unclassified_notes.py')
    mod = importlib.util.module_from_spec(spec)
    sys.modules['resolve_unclassified_notes'] = mod
    spec.loader.exec_module(mod)
    return mod.ROUND_SOURCES


# Every review file on disk, with the vocabulary it speaks and the data it was
# applied to. `applies_to='corrected'` is the Lesson 3 line.
ROUND_VOCAB = {
    'validation/feedback/ketubot_review_Jeffrey_Rubenstein_2026-01-08.json':
        dict(vocab='january_typed', applies_to='base'),
    'validation/feedback/ketubot_review_Simon_-_Test_2026-01-05.json':
        dict(vocab='january_typed', applies_to='base'),
    'validation/feedback/v5_1_feedback_anonymous_2026-02-05 (1).json':
        dict(vocab='base_binary', applies_to='base'),
    'validation/feedback/v5_1_feedback_anonymous_2026-02-20.json':
        dict(vocab='base_binary', applies_to='base'),
    'validation/feedback/v8_delta_feedback_anonymous_2026-02-26.json':
        dict(vocab='delta_removal', applies_to='base'),
    'validation/feedback/canonical_review_anonymous_2026-03-17.json':
        dict(vocab='canonical', applies_to='corrected'),
    'validation/feedback/kiddushin_review_2026-04-23.json':
        dict(vocab='base_binary', applies_to='base'),
    'validation/feedback/kiddushin_review_2026-05-26 (1).json':
        dict(vocab='base_binary', applies_to='base'),
    'jeff comms/wave4_kiddushin_review_2026-07-06.json':
        dict(vocab='base_binary', applies_to='base'),
    # Two files carry no verdicts at all. They are listed rather than omitted:
    # naming an empty file as empty is what stops it reading as backlog, and
    # what stopped the January round from hiding among them (Lesson 38).
    'validation/feedback/jeff_v4.1_validation.json':
        dict(vocab='empty', applies_to='base'),
    'validation/feedback/validations_v4_2026-01-25.json':
        dict(vocab='empty', applies_to='base'),
}

# The axis shape. `None` on an axis means "this round could not express it",
# which is different from "the reviewer said it was right".
def _shape(is_story=None, extent=None, confidence=None, grouping=None,
           display_problem=False, lossy=False):
    return dict(is_story=is_story, extent=extent, confidence=confidence,
                grouping=grouping, display_problem=display_problem, lossy=lossy)


VOCAB_MAP = {
    # v5.1 / v7 / wave-4 rounds: one binary button, four capabilities pooled.
    ('base_binary', 'correct'): _shape(is_story='yes'),
    ('base_binary', 'incorrect'): _shape(is_story='no', lossy=True),
    # v8 delta round: the same binary plus two tokens about a PROPOSED REMOVAL.
    # confirm_remove = "yes, drop it" -> not a story. reject_remove = "no, keep
    # it" -> it IS a story. Getting these backwards inverts 4 verdicts.
    ('delta_removal', 'correct'): _shape(is_story='yes'),
    ('delta_removal', 'incorrect'): _shape(is_story='no', lossy=True),
    ('delta_removal', 'confirm_remove'): _shape(is_story='no'),
    ('delta_removal', 'reject_remove'): _shape(is_story='yes'),
    # Canonical round, applied to already-corrected data.
    ('canonical', 'correct'): _shape(is_story='yes'),
    ('canonical', 'incorrect'): _shape(is_story='no', lossy=True),
    ('canonical', 'approve'): _shape(is_story='yes'),
    # The one token that already carried an axis, and the whole reason the
    # design is "read off the taxonomy" rather than invented: `adjust` means
    # IT IS A STORY and the extent is wrong. Counting it against precision is
    # what turned a boundary failure into a fake classification problem.
    ('canonical', 'adjust'): _shape(is_story='yes', extent='wrong_unspecified'),
    # January 2026-01-08: typed fields, per daf. The round nothing read for
    # eight months, and the only one that ever recorded an extent complaint in
    # a STRUCTURED field -- 10 of its 25 verdicts carry length_adjustment.
    ('january_typed', 'correct'): _shape(is_story='yes'),
    ('january_typed', 'false_positive'): _shape(is_story='no', lossy=True),
}

# January's second field, folded onto the extent axis.
LENGTH_ADJUSTMENT = {
    None: None,
    'shrink': 'wrong_unspecified',
    'grow': 'wrong_unspecified',
}


class UnknownVerdict(KeyError):
    """Raised rather than skipped. See Lesson 38."""


def map_verdict(vocab: str, verdict: str, extra: dict | None = None) -> dict:
    """One verdict -> exactly one axis shape. Unknown tokens raise."""
    key = (vocab, verdict)
    if key not in VOCAB_MAP:
        raise UnknownVerdict(f"no mapping for verdict {verdict!r} in vocabulary {vocab!r}")
    shape = dict(VOCAB_MAP[key])
    extra = extra or {}
    if 'length_adjustment' in extra:
        adj = extra.get('length_adjustment')
        if adj not in LENGTH_ADJUSTMENT:
            raise UnknownVerdict(f"no mapping for length_adjustment {adj!r}")
        if LENGTH_ADJUSTMENT[adj]:
            shape['extent'] = LENGTH_ADJUSTMENT[adj]
            shape['lossy'] = False  # the extent complaint survived in a field
    return shape


def _verdicts_in(path: Path, vocab: str):
    """Yield (key, verdict_token, extra) for one file. Counts what it drops."""
    data = json.loads(path.read_text())
    dropped = Counter()
    if vocab == 'january_typed':
        items = data.get('feedback')
        if not isinstance(items, list):
            dropped['not_a_list'] += 1
            return [], dropped
        out = []
        for i, e in enumerate(items):
            token = e.get('feedback_type')
            if not token:
                dropped['no_feedback_type'] += 1
                continue
            out.append((f"{e.get('ref')}#{i}", token, e))
        return out, dropped
    if vocab == 'empty':
        return [], dropped
    items = data.get('reviews') or data.get('feedback') or {}
    if not isinstance(items, dict):
        dropped['not_a_dict'] += 1
        return [], dropped
    out = []
    for k, v in items.items():
        if not isinstance(v, dict):
            dropped['not_a_dict_entry'] += 1
            continue
        if not v.get('verdict'):
            dropped['no_verdict'] += 1
            continue
        out.append((k, v['verdict'], v))
    return out, dropped


def main() -> int:
    sources = _round_sources()
    rows, per_round, unknown = [], {}, []
    for rel, cfg in sorted(ROUND_VOCAB.items()):
        path = REPO / rel
        if not path.exists():
            per_round[rel] = dict(error='file missing')
            continue
        version = sources.get(path.name, ('unmapped', []))[0]
        pairs, dropped = _verdicts_in(path, cfg['vocab'])
        counts, shapes = Counter(), Counter()
        for key, token, extra in pairs:
            try:
                shape = map_verdict(cfg['vocab'], token, extra)
            except UnknownVerdict as exc:
                unknown.append(dict(round=rel, key=key, verdict=token, error=str(exc)))
                continue
            counts[token] += 1
            shapes[shape['is_story']] += 1
            rows.append(dict(round=path.name, key=key, applies_to=cfg['applies_to'],
                             detector_version=version, old_verdict=token, **shape))
        per_round[rel] = dict(vocab=cfg['vocab'], applies_to=cfg['applies_to'],
                              detector_version=version, mapped=len(pairs),
                              verdicts=dict(counts), is_story=dict(shapes),
                              dropped=dict(dropped))

    lossy = sum(1 for r in rows if r['lossy'])
    out = dict(
        built_by='scripts/map_verdict_vocabularies.py',
        gate='every banked verdict maps to exactly one axis shape',
        total_mapped=len(rows),
        unmapped=unknown,
        lossy=lossy,
        lossy_note=('A bare `incorrect` pooled four capabilities into one button '
                    'and cannot be un-pooled after the fact. These rows are marked, '
                    'not guessed. Phase B stops the pooling going forward.'),
        recovered_extent=sum(1 for r in rows if r['extent']),
        by_round=per_round, rows=rows)
    dest = REPO / 'results' / 'rulers' / 'verdict_vocabulary_map.json'
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print(f"mapped {len(rows)} verdicts from {len(ROUND_VOCAB)} files\n")
    for rel, info in per_round.items():
        if 'error' in info:
            print(f"  {Path(rel).name[:52]:52s} {info['error']}")
            continue
        drop = f"  dropped={info['dropped']}" if info['dropped'] else ''
        print(f"  {Path(rel).name[:52]:52s} {info['vocab']:14s} "
              f"{info['applies_to']:9s} {info['detector_version']:17s} "
              f"n={info['mapped']:3d}{drop}")
    print(f"\nlossy (a bare `incorrect`, un-poolable): {lossy}")
    print(f"extent recovered from a structured field: {out['recovered_extent']}")
    if unknown:
        print(f"\nUNMAPPED VERDICTS ({len(unknown)}) — the gate fails:")
        for u in unknown:
            print(f"  {u['round']}  {u['key']}  {u['verdict']}")
        return 1
    print(f"\nwrote {dest.relative_to(REPO)}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
