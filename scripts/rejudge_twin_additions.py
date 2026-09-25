#!/usr/bin/env python3
"""
Re-ask the twin question for every twin-pass addition already on disk.

The twin pass adds a story only on a `separate_incident` verdict about one segment
beside one found story. Both inputs are recorded on each addition (`start_segment`,
`twin_of`), so a change to the question's WORDING can be measured without re-running
Stage 2: the candidates are identical, the page-level prompt is identical, and the
prompt is the only variable.

Two arms, same model, same day (Lesson 11, Lesson 22):
  old  — the question as it stood at `--old-rev` (default HEAD), loaded from git
  new  — the question in the working tree

It can only see additions that were MADE. A candidate the old wording rejected and
the new one would accept is invisible here — so this measures what the new wording
drops, not what it adds. Read it that way.

Labels, where we have them (read from the verdict files, never typed here):
  his 2005 list      -> keep     (the matcher is the harness's own, strict)
  Jeff's axis verdict yes/no, Simon's pre-screen yes/no -> keep / drop

    python3 scripts/rejudge_twin_additions.py --out results/v11/twin_pass/rejudge_2026-09-25.json
"""
import argparse
import importlib.util
import json
import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s [twin-rejudge] %(message)s',
                    handlers=[logging.FileHandler(PROJECT_ROOT / 'project.log'),
                              logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)

from dotenv import load_dotenv  # noqa: E402

RUNS = {
    'yevamot': PROJECT_ROOT / 'results/v11/twin_pass/yevamot_full_twinall.json',
    'kiddushin': PROJECT_ROOT / 'results/v11/twin_pass/kiddushin_full_twinall.json',
}
EXPERT = {
    'yevamot': PROJECT_ROOT / 'results/expert_lists/yevamot_2005.json',
    'kiddushin': PROJECT_ROOT / 'results/expert_lists/kiddushin_2005.json',
}
VERDICT_FILES = [
    ('jeff', PROJECT_ROOT / 'validation/feedback/review_2026-09-16_bundle_jeff_2026-09-23.json'),
    ('simon', PROJECT_ROOT / 'validation/feedback/review_2026-09-15_bundle_simon_prescreen_2026-09-16.json'),
]


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def old_detector_module(rev: str):
    src = subprocess.run(['git', 'show', f'{rev}:src/story_detector_v11.py'],
                         cwd=PROJECT_ROOT, capture_output=True, text=True, check=True).stdout
    tmp = Path(tempfile.mkdtemp()) / 'story_detector_v11_old.py'
    tmp.write_text(src)
    return load_module(tmp, 'story_detector_v11_old')


def old_prompt(det, ref, segments, a, b, idx):
    """The old module had no _twin_prompt; capture the prompt its loop builds."""
    if hasattr(det, '_twin_prompt'):
        return det._twin_prompt(ref, segments, a, b, idx)
    seen = []
    det._call_google = lambda prompt, **k: seen.append(prompt) or '{"verdict": "same_story"}'
    from src.event_triage import EventType
    # TWIN_TRIGGER=all (set in main) asks about every neighbour; the labels are unread.
    det._find_adjacent_twins(ref, segments, [EventType.NARRATIVE_EVENT] * len(segments),
                             [{'start_segment': a, 'end_segment': b}])
    for p in seen:
        if f'(segment {idx})' in p:
            return p
    raise RuntimeError(f'old prompt for {ref} seg {idx} not captured')


def labels():
    """(ref, seg) -> (label, source) from the verdict files."""
    out = {}
    for who, path in VERDICT_FILES:
        d = json.loads(path.read_text())
        for v in d['reviews'].values():
            if v['start_segment'] != v['end_segment'] or not v['page_ref'].startswith(('Yevamot', 'Kiddushin')):
                continue
            ans = v.get('is_story')
            if ans in ('yes', 'no'):
                key = (v['page_ref'], v['start_segment'])
                if key not in out or who == 'jeff':     # Jeff wins over the pre-screen
                    out[key] = ('keep' if ans == 'yes' else 'drop', f'{who} {d["date"]}')
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out', required=True)
    ap.add_argument('--old-rev', default='HEAD')
    args = ap.parse_args()

    load_dotenv(PROJECT_ROOT / '.env')
    load_dotenv(PROJECT_ROOT.parents[2] / '.env')   # the main checkout, from a worktree
    if not os.getenv('GOOGLE_API_KEY'):
        log.error('GOOGLE_API_KEY not set -- refusing to run')
        return 2
    os.environ['TWIN_TRIGGER'] = 'all'

    recall = load_module(PROJECT_ROOT / 'scripts/measure_recall_vs_expert_list.py', 'recall')
    global golden_builder
    golden_builder = load_module(PROJECT_ROOT / 'scripts/build_gittin_golden.py', 'golden_builder')
    new_mod = load_module(PROJECT_ROOT / 'src/story_detector_v11.py', 'story_detector_v11_new')
    old_mod = old_detector_module(args.old_rev)
    lab = labels()

    rows = []
    for tractate, run_path in RUNS.items():
        run = json.loads(run_path.read_text())
        model = run['run_meta']['model']
        new_det = new_mod.V7StoryDetector(model_name=model)
        old_det = old_mod.V7StoryDetector(model_name=model)
        expert = recall.load_expert_json(str(EXPERT[tractate]), 'recall')
        # The golden builder's own strict matcher, so "on his list" means here what it
        # means in every golden and recall figure.
        listed = {k for hits in golden_builder.strict_matches(run['pages'], expert, run_path).values()
                  for k in hits}
        adds = [(p, s) for p in run['pages'] for s in p['stories'] if s.get('source') == 'twin_pass']
        log.info('%s: %d twin-pass additions on disk (model %s)', tractate, len(adds), model)
        for page, st in adds:
            ref, idx = page['ref'], st['start_segment']
            a, b = st['twin_of']
            row = {'tractate': tractate, 'ref': ref, 'segment': idx, 'beside': [a, b]}
            for arm, det in (('old', old_det), ('new', new_det)):
                prompt = (det._twin_prompt(ref, page['segments'], a, b, idx) if arm == 'new'
                          else old_prompt(old_mod.V7StoryDetector(model_name=model),
                                          ref, page['segments'], a, b, idx))
                try:
                    res = det._parse_json_response(det._call_google(prompt, max_tokens=512, json_mode=True))
                except Exception as e:  # noqa: BLE001 - counted, never read as a verdict
                    log.warning('%s seg %d %s arm failed: %s', ref, idx, arm, e)
                    res = None
                row[arm] = (res or {}).get('verdict', 'FAILED')
                row[f'{arm}_reason'] = (res or {}).get('reason', '')
            row['label'], row['label_source'] = lab.get((ref, idx), (None, None))
            if (ref, idx, idx) in listed:
                row['label'], row['label_source'] = 'keep', 'his 2005 list (strict)'

            rows.append(row)
            log.info('%-14s seg %-3d old=%-17s new=%-17s label=%s',
                     ref, idx, row['old'], row['new'], row['label'])

    out = Path(args.out)
    out.write_text(json.dumps({'old_rev': args.old_rev, 'rows': rows}, indent=2, ensure_ascii=False) + '\n')
    log.info('wrote %s (%d rows)', out, len(rows))
    return 0


if __name__ == '__main__':
    sys.exit(main())
