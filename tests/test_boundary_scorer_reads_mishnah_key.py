#!/usr/bin/env python3
"""
A story Stage 4g withheld is not a story we failed to find.

THE DEFECT. `filter_mishnah_only_stories()` moves a story lying entirely inside a
Mishnah block out of `stories` and into `mishnah_stories`. Lesson 27 is the standing
rule about that key: move output somewhere no harness reads and an invisible deletion
reads as a model failure. The recall harness and the axis review UI were taught to read
it; `score_boundary_targets.py` was not.

So a boundary target sitting on a withheld story scored `N/A`, whose own docstring
defines it as "this run has no story covering that segment (a detection gap)". It is
not a detection gap. The story was found, bounded, and then set aside on a scope
judgment that is still an open question with Jeff (`jeff:mishnah-scope`). Two different
facts, one bucket.

Nothing on Ketubot or Kiddushin lands there today — the five withheld stories carry no
boundary target — which is exactly why this had to be fixed before a new tractate, where
there is no prior run to diff against and no reason the coincidence would hold.

Written first and watched fail. No API key, no network, no model.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import importlib.util                                                  # noqa: E402

spec = importlib.util.spec_from_file_location(
    'score_boundary_targets',
    Path(__file__).resolve().parent.parent / 'scripts' / 'score_boundary_targets.py')
sbt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sbt)

HEB = "אָמַר רַב. מַעֲשֶׂה בְּאֶחָד. וְכֵן הֲלָכָה."


def run_file(tmp_path, *, withheld: bool):
    """One page, one story on segment 1 — in `stories`, or withheld by Stage 4g."""
    story = {'start_segment': 1, 'end_segment': 1, 'classification': 'HIGH_CONFIDENCE'}
    page = {
        'ref': 'Ketubot 77a',
        'segments': [{'index': i, 'hebrew': HEB} for i in range(3)],
        'stories': [] if withheld else [story],
        'mishnah_stories': [story] if withheld else [],
    }
    p = tmp_path / f"run_{'withheld' if withheld else 'kept'}.json"
    p.write_text(json.dumps({'pages': [page]}))
    return str(p)


TARGET = [{'ref': 'Ketubot 77a', 'segment': 1, 'clause': 0, 'direction': 'start',
           'source_round': 'jeff_2005_ketubot', 'target_file': 't.json'}]


def test_a_kept_story_scores_normally(tmp_path):
    counts, _ = sbt.score(run_file(tmp_path, withheld=False), TARGET)
    assert counts['HIT'] == 1
    assert counts['WITHHELD'] == 0


def test_a_withheld_story_is_not_reported_as_a_detection_gap(tmp_path):
    counts, rows = sbt.score(run_file(tmp_path, withheld=True), TARGET)
    assert counts['WITHHELD'] == 1
    assert counts['N/A'] == 0, "a withheld story is not a page we found nothing on"
    assert rows[0][5] == 'WITHHELD'


def test_withheld_is_never_folded_into_the_score(tmp_path):
    """It must not be counted as a hit either — the boundary was not published."""
    counts, _ = sbt.score(run_file(tmp_path, withheld=True), TARGET)
    assert counts['HIT'] == counts['NEAR'] == counts['MISS'] == 0


def test_a_page_with_no_story_at_all_is_still_na(tmp_path):
    p = tmp_path / 'empty.json'
    p.write_text(json.dumps({'pages': [{
        'ref': 'Ketubot 77a',
        'segments': [{'index': i, 'hebrew': HEB} for i in range(3)],
        'stories': [], 'mishnah_stories': []}]}))
    counts, _ = sbt.score(str(p), TARGET)
    assert counts['N/A'] == 1 and counts['WITHHELD'] == 0
