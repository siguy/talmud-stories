"""The Shas driver (scripts/run_shas.py) with a fake executor: no process is started, no API is called.

Failure injection (Lesson 21): a step that exits 0 but writes nothing, a run that writes errors, a
fetch that exits non-zero, a resumed run -- none may end as a green tractate.
"""
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT))

import run_shas as R  # noqa: E402
import tractates as T  # noqa: E402
from tests.test_check_tractate_run import build  # noqa: E402

A, B = 'tamid', 'niddah'          # Tamid is the smaller, so Niddah must be started first


class Fake:
    """Pretends to be the scripts: copies the files a real step would have written."""

    def __init__(self, src_root, dst_root, mutate=None, rc=None, silent=()):
        self.src, self.dst, self.calls = Path(src_root), Path(dst_root), []
        self.mutate, self.rc, self.silent = mutate or {}, rc or {}, set(silent)

    def __call__(self, cmd, env, logfile):
        script = Path(cmd[1]).name
        arg = lambda k: cmd[cmd.index(k) + 1]
        if script == 'fetch_tractate_pages.py':
            slug, step, files = arg('--tractates').lower(), 'fetch', ['results/sefaria/{s}.json']
        elif script == 'run_new_tractate.py' and '--triage-only' in cmd:
            slug, step, files = arg('--tractate'), 'triage', ['results/triage/{s}.json']
        elif script == 'run_new_tractate.py':
            slug, out = arg('--tractate'), arg('--output')
            step, files = 'run' + out[-6], [out]
        else:
            slug = env['JUDGE_TRACTATE']
            sub = cmd[2]
            step, files = sub, {'units': ['results/consensus/{s}/units.json'], 'gemini': ['results/consensus/{s}/gemini.json'],
                                'export': ['results/consensus/{s}/subagent/manifest.json']}[sub]
        self.calls.append((slug, step))
        logfile.parent.mkdir(parents=True, exist_ok=True)
        logfile.write_text('triage tokens: {"stage1": {"input": 1000000, "output": 100000, "thinking": 0, "cached_input": 0}}\n')
        if (slug, step) in self.silent:
            return 0
        for f in files:
            rel = f.format(s=slug)
            dst = self.dst / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            if rel.endswith('manifest.json'):
                dst.write_text('{}')
                continue
            data = json.loads((self.src / rel).read_text())
            if (slug, step) in self.mutate:
                self.mutate[(slug, step)](data)
            dst.write_text(json.dumps(data, ensure_ascii=False, indent=2) if '/triage/' in rel
                           else json.dumps(data, ensure_ascii=False))
        return self.rc.get((slug, step), 0)


def setup(tmp, **kw):
    src = tmp / 'src'
    for s in (A, B):
        build(src, slug=s)
    dst = tmp / 'repo'
    dst.mkdir()
    return Fake(src, dst, **kw), dst


def drive(dst, fake, slugs=(A, B), **kw):
    d = R.Driver(dst, list(slugs), execute=fake, max_parallel=4, **kw)
    d.run()
    return d, json.loads((dst / 'results/shas_run/status.json').read_text())


def test_everything_green_and_longest_first(tmp_path):
    fake, dst = setup(tmp_path)
    d, st = drive(dst, fake)
    assert st['counts']['green'] + st['counts']['amber'] == 2, st['counts']
    assert all(v['state'] in ('done', 'skipped') for s in (A, B) for v in st['tractates'][s]['steps'].values())
    assert (dst / 'results/consensus/niddah/subagent/manifest.json').exists()
    assert fake.calls[0] == (B, 'fetch')                     # Niddah (146 pages) before Tamid (17)
    assert st['tractates'][A]['steps']['triage']['cost_usd'] == 0.8     # 1M in at $0.50 + 0.1M out at $3.00


def test_g3_failure_stops_that_tractate_and_the_other_carries_on(tmp_path):
    fake, dst = setup(tmp_path, mutate={(B, 'run1'): lambda d: d['run_meta'].update(stage2_errors=['Niddah 25a: boom'])})
    d, st = drive(dst, fake)
    b, a = st['tractates'][B], st['tractates'][A]
    assert b['overall'] == 'red' and b['steps']['run1']['color'] == 'red'
    assert b['steps']['pair']['state'] == 'pending' and b['steps']['gemini']['state'] == 'pending'   # stopped
    assert a['overall'] in ('green', 'amber') and a['steps']['export']['state'] in ('done', 'skipped')
    assert (B, 'gemini') not in fake.calls


def test_exit_zero_with_no_output_is_not_a_pass(tmp_path):
    fake, dst = setup(tmp_path, silent=[(B, 'run2')])
    d, st = drive(dst, fake)
    assert st['tractates'][B]['steps']['run2']['color'] == 'red'
    assert st['tractates'][B]['overall'] == 'red'


def test_nonzero_exit_is_failed_and_stops(tmp_path):
    fake, dst = setup(tmp_path, rc={(B, 'fetch'): 1})
    d, st = drive(dst, fake)
    assert st['tractates'][B]['steps']['fetch']['state'] == 'failed'
    assert st['tractates'][B]['steps']['triage']['state'] == 'pending'
    assert st['tractates'][A]['overall'] != 'red'


def test_resumed_run_is_amber_never_green(tmp_path):
    fake, dst = setup(tmp_path)
    part = dst / 'results/v14/tamid/run1.json.partial.json'
    part.parent.mkdir(parents=True)
    part.write_text('{}')
    d, st = drive(dst, fake, slugs=[A])
    assert st['tractates'][A]['steps']['run1']['resumed'] is True
    assert st['tractates'][A]['steps']['run1']['color'] == 'amber'
    assert st['tractates'][A]['overall'] == 'amber'


def test_finished_steps_are_skipped_and_red_ones_stop_unless_retried(tmp_path):
    fake, dst = setup(tmp_path)
    drive(dst, fake, slugs=[A])
    first = len(fake.calls)
    d, st = drive(dst, fake, slugs=[A])                     # a second invocation: nothing to do
    assert len(fake.calls) == first and st['tractates'][A]['steps']['run1']['state'] == 'skipped'
    # break run 1 on disk: the gate now fails -> red, not re-run
    p = dst / 'results/v14/tamid/run1.json'
    run = json.loads(p.read_text())
    run['run_meta']['stage2_errors'] = ['x']
    p.write_text(json.dumps(run))
    d, st = drive(dst, fake, slugs=[A])
    assert len(fake.calls) == first and st['tractates'][A]['overall'] == 'red'
    # with --retry-failed it runs that step again (the fake writes a good one)
    d, st = drive(dst, fake, slugs=[A], retry_failed=True)
    assert (A, 'run1') in fake.calls[first:] and st['tractates'][A]['steps']['run1']['color'] != 'red'


def test_through_stops_early(tmp_path):
    fake, dst = setup(tmp_path)
    d, st = drive(dst, fake, through='triage')
    assert {s for _, s in fake.calls} == {'fetch', 'triage'} and 'run1' not in st['tractates'][A]['steps']


def test_dry_run_runs_and_writes_nothing(tmp_path, capsys):
    fake, dst = setup(tmp_path)
    R.Driver(dst, [A, B], execute=fake, dry_run=True).run()
    assert not fake.calls and not (dst / 'results/shas_run/status.json').exists()
    assert 'niddah' in capsys.readouterr().out


def test_default_set_is_the_32_remaining_tractates():   # 31 + Eruvin, unheld 2026-11-09
    s = R.default_tractates()
    assert len(s) == 32 and 'eruvin' in s and 'berakhot' not in s and 'bava_batra' in s
    assert R.by_size(ROOT, s)[0] == 'bava_batra'            # 350 pages, the longest


def test_cost_counts_cached_input_at_the_cached_price():
    t = {'x': {'input': 1_000_000, 'cached_input': 500_000, 'output': 0, 'thinking': 0}}
    assert R.cost_usd(t) == round(0.5 * 0.5 + 0.5 * 0.05, 4)


def test_running_one_tractate_keeps_the_others_record_and_skipped_steps_keep_their_cost(tmp_path):
    """2026-11-10: `--tractates makkot` rewrote status.json down to Makkot, and a re-settle reported cost $0."""
    fake, dst = setup(tmp_path)
    drive(dst, fake)
    _, st = drive(dst, fake, slugs=(A,))
    assert set(st['tractates']) == {A, B}
    assert st['tractates'][A]['steps']['triage']['cost_usd'] == 0.8          # skipped now, charged when it ran
    assert st['cost_usd'] == round(st['tractates'][A]['cost_usd'] + st['tractates'][B]['cost_usd'], 2) > 0


def test_the_gemini_judge_step_is_charged_from_its_token_log(tmp_path):
    """2026-11-10: the judge was unmetered, so the run report missed what AI Studio billed for it."""
    tally = {'judge': {'input': 1_000_000, 'output': 0, 'thinking': 0, 'cached_input': 0}}
    fake, dst = setup(tmp_path, mutate={(A, 'gemini'): lambda d: d['meta'].update(token_log=[tally])})
    _, st = drive(dst, fake, slugs=(A,))
    assert st['tractates'][A]['steps']['gemini']['cost_usd'] == 0.5


def test_a_partial_triage_cache_is_resumed_not_taken_as_done(tmp_path):
    """2026-11-10: a 2-page cache from the smoke test made Taanit's triage look finished."""
    fake, dst = setup(tmp_path)
    src_text = json.loads((fake.src / f'results/sefaria/{A}.json').read_text())
    (dst / 'results/sefaria').mkdir(parents=True)
    (dst / f'results/sefaria/{A}.json').write_text(json.dumps(src_text))
    one = src_text['pages'][0]['ref']
    (dst / 'results/triage').mkdir(parents=True)
    (dst / f'results/triage/{A}.json').write_text(json.dumps({'triage_results': {one: ['DELIBERATION']}}))
    P = T.Paths(A, dst)
    assert not R.triage_complete(P)
    drive(dst, fake, slugs=(A,), through='triage')
    assert (A, 'triage') in fake.calls and R.triage_complete(P)
