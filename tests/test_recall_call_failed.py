"""A list story on a page whose Stage 2 call FAILED is not a Detection miss.

Before 2026-11-07 neither recall scorer read `stage2_error`, so a story on a page
whose call failed scored "examined, nothing proposed" -- an API failure charged to
Detection (finding 4 of docs/findings/2026-11-07-pre-eruvin-code-review.md). Such a
row is now `call_failed: true` and leaves both denominators; the count is logged.
Run end to end through both scorers on a two-page fake run.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Distinct consonant words so each story has a corpus-unique phrase.
WORDS = 'אבג דהו זחט יכל מנס עפצ קרש תאב גדה וזח טיכ למנ סעפ צקר שתא'.split()


def seg(i):
    return {'index': i, 'english': 'x', 'hebrew': ' '.join(WORDS[i * 3:(i + 1) * 3] * 2)}


def _write(tmp_path):
    pages = [
        {'ref': 'Testtract 2a', 'segments': [seg(0), seg(1)],
         'stories': [{'start_segment': 0, 'end_segment': 0, 'classification': 'HIGH_CONFIDENCE'}]},
        {'ref': 'Testtract 2b', 'segments': [seg(2), seg(3)], 'stories': [],
         'stage2_error': 'EmptyStage2Response: Testtract 2b: no parseable response twice'},
    ]
    run = tmp_path / 'run.json'
    run.write_text(json.dumps({'pages': pages}, ensure_ascii=False))
    stories = [
        {'id': 'found', 'ref': 'Testtract 2a', 'text': seg(0)['hebrew']},   # found
        {'id': 'missed', 'ref': 'Testtract 2a', 'text': seg(1)['hebrew']},  # examined, missed
        {'id': 'failed', 'ref': 'Testtract 2b', 'text': seg(2)['hebrew']},  # call failed
    ]
    for s in stories:
        s.update(words=len(s['text'].split()), blind=True, in_appendix=False,
                 counts_for_recall=True, duplicate_of=None)
    expert = tmp_path / 'expert.json'
    expert.write_text(json.dumps({'stories': stories}, ensure_ascii=False))
    return run, expert


def _run(script, *args):
    p = subprocess.run([sys.executable, str(ROOT / 'scripts' / script), *map(str, args)],
                       capture_output=True, text=True, cwd=ROOT)
    assert p.returncode == 0, p.stderr
    return p.stdout + p.stderr


def test_recall_scorer_keeps_a_failed_call_out_of_both_denominators(tmp_path):
    run, expert = _write(tmp_path)
    out = tmp_path / 'matches.json'
    log = _run('measure_recall_vs_expert_list.py', '--expert-json', expert,
               '--tractate', 'Testtract', '--detected', run, '--out', out)
    rows = {r['id']: r for r in json.loads(out.read_text())}
    assert rows['failed'].get('call_failed') is True
    assert not rows['found'].get('call_failed') and not rows['missed'].get('call_failed')
    assert 'RECALL vs expert list: 1/2' in log
    assert 'DETECTION recall given the page survived triage: 1/2' in log
    assert 'CALL FAILED: 1' in log


def test_strict_scorer_keeps_a_failed_call_out_of_the_denominator(tmp_path):
    run, expert = _write(tmp_path)
    out = tmp_path / 'strict.json'
    _run('measure_strict_recall.py', '--expert-json', expert, '--tractate', 'Testtract',
         '--detected', run, '--out', out)
    blob = json.loads(out.read_text())
    assert blob['denominator'] == 2
    assert blob['call_failed'] == 1
    assert {r['id']: r.get('call_failed') for r in blob['stories']}['failed'] is True
