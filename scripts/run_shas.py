#!/usr/bin/env python3
"""Run the Shas pipeline: a loop over tractates, a gate after every step (plan §2.1).

    python3 scripts/run_shas.py --dry-run                       # show the plan, run nothing
    python3 scripts/run_shas.py --through triage                # fetch + triage only
    python3 scripts/run_shas.py                                 # everything up to the Claude judge
    python3 scripts/run_shas.py --tractates bava_batra sanhedrin
    python3 scripts/run_shas.py --retry-failed                  # re-run steps a gate turned red

STEPS, per tractate, in order:
    fetch  -> g1    triage -> g2    run1, run2 (side by side) -> g3 each    pair -> g4 + g5
    units  ->       gemini -> g6    export (Claude subset only: Gemini's out_of_scope units)
The Claude judge (subagents, import, g6 claude) is run by a person in a Claude Code session; the
driver reports it as 'waiting' and checks g6 for it once claude.json exists.

RULES
  * Longest tractate first; at most 8 processes at a time (fetch 3, Gemini judge 2).
  * A step whose output exists and passed its gate is SKIPPED. One whose output exists and failed
    its gate is red: that tractate stops, the others carry on (CLAUDE.md: one source failing never
    stops the run). `--retry-failed` runs it again.
  * A run resumed from a checkpoint is AMBER, never green (its failure counters cover only the
    part after the crash).
  * Writes results/shas_run/status.json after every event and logs to project.log:
    tractate, step, counts, cost. Per-step output goes to results/shas_run/logs/.
  * Refuses to start on a dirty worktree (pin the code first); `--allow-dirty` overrides.
No detection logic lives here. It calls the scripts that already exist.
"""
import argparse
import json
import logging
import os
import re
import subprocess
import sys
import threading
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))
import check_tractate_run as C  # noqa: E402
import tractates as T  # noqa: E402

log = logging.getLogger('run-shas')

STEPS = ['fetch', 'triage', 'run1', 'run2', 'pair', 'units', 'gemini', 'export']
DEPENDS = {'fetch': [], 'triage': ['fetch'], 'run1': ['triage'], 'run2': ['triage'],
           'pair': ['run1', 'run2'], 'units': ['pair'], 'gemini': ['units'], 'export': ['gemini']}
LIMITS = {'fetch': 3, 'gemini': 1}   # per step; others share MAX_PARALLEL. gemini 1: two judges beside 8 runs hit 3M input tokens/min (2026-11-10)
MAX_PARALLEL = 8
# Already done or held: the 31 tractates of the run are the table minus these (plan §0).
ALREADY_RUN = ('berakhot', 'yevamot', 'ketubot', 'kiddushin', 'gittin')
HELD = ()      # Eruvin was held for Jeff until Simon's 2026-11-09 decision: it goes on the site with the rest
JUDGE_PROMPT = 'src/prompts/judge_register_v2.md'
PRICE = {'input': 0.50, 'cached_input': 0.05, 'output': 3.00}   # $ per million tokens, standard tier
JUDGE_EXPORT_SEED = 1


def default_tractates():
    return [s for s in T.SLUGS if s not in ALREADY_RUN + HELD]


def by_size(root, slugs):
    """Longest first: real page count if the text is already fetched, else the estimate."""
    def size(s):
        P = T.Paths(s, root)
        try:
            return len(json.loads(P.text.read_text())['pages'])
        except (OSError, json.JSONDecodeError, KeyError):
            return T.approx_pages(s)
    return sorted(slugs, key=lambda s: (-size(s), s))


def cost_usd(tokens):
    """Standard-tier dollars from a run_meta.tokens-style dict {stage: {input, output, cached_input}}."""
    usd = 0.0
    for t in (tokens or {}).values():
        cached = t.get('cached_input', 0)
        usd += ((t.get('input', 0) - cached) * PRICE['input'] + cached * PRICE['cached_input']
                + (t.get('output', 0) + t.get('thinking', 0)) * PRICE['output']) / 1e6
    return round(usd, 4)


def triage_complete(P):
    """Triage is done only when every fetched page has a label. A partial cache (the 2-page smoke test left one for
    Taanit) is work to resume, not a finished step (2026-11-10)."""
    if not (P.triage.exists() and P.text.exists()):
        return False
    labels = json.loads(P.triage.read_text()).get('triage_results', {})
    return all(p['ref'] in labels for p in json.loads(P.text.read_text())['pages'])


def triage_tokens_from_log(path):
    """Stage 1's meter tally, from the `triage tokens: {...}` line the runner logs."""
    try:
        for line in reversed(Path(path).read_text().splitlines()):
            m = re.search(r'triage tokens: (\{.*\})', line)
            if m:
                return json.loads(m.group(1))
    except (OSError, json.JSONDecodeError):
        pass
    return None


class Driver:
    def __init__(self, root, slugs, execute=None, max_parallel=MAX_PARALLEL, through='export',
                 retry_failed=False, dry_run=False):
        self.root, self.slugs = Path(root), by_size(root, slugs)
        self.through = through
        self.retry_failed, self.dry_run, self.max_parallel = retry_failed, dry_run, max_parallel
        self.execute = execute or self.run_subprocess
        self.lock = threading.Lock()
        self.status_path = self.root / 'results/shas_run/status.json'
        self.state = {s: {st: {'state': 'pending'} for st in STEPS} for s in self.slugs}
        self.wanted = STEPS[:STEPS.index(through) + 1]
        self.rev = None

    # ---- commands -----------------------------------------------------------------
    def command(self, slug, step):
        py, P, name = sys.executable, T.Paths(slug, self.root), T.english(slug)
        out = lambda n: str(P.run(n).relative_to(self.root))
        env = {}
        if step == 'fetch':
            cmd = [py, 'scripts/fetch_tractate_pages.py', '--tractates', name]
        elif step == 'triage':
            cmd = [py, 'scripts/run_new_tractate.py', '--tractate', slug, '--triage-only']
        elif step in ('run1', 'run2'):
            cmd = [py, 'scripts/run_new_tractate.py', '--tractate', slug, '--output', out(int(step[-1]))]
        else:
            sub = {'units': ['units'], 'gemini': ['gemini', '--workers', '6'],
                   'export': ['export', '--seed', str(JUDGE_EXPORT_SEED), '--batch', '20', '--only-gemini-out-of-scope']}[step]
            cmd = [py, 'scripts/judge_detector_spans.py'] + sub
            env = {'JUDGE_TRACTATE': slug, 'JUDGE_PROMPT': JUDGE_PROMPT}
        return cmd, env

    def run_subprocess(self, cmd, env, logfile):
        logfile.parent.mkdir(parents=True, exist_ok=True)
        with open(logfile, 'ab') as fh:
            fh.write(f'\n=== {time.strftime("%Y-%m-%d %H:%M:%S")} {" ".join(cmd)}\n'.encode())
            fh.flush()
            return subprocess.run(cmd, cwd=self.root, env={**os.environ, **env}, stdout=fh,
                                  stderr=subprocess.STDOUT).returncode

    # ---- outputs and gates --------------------------------------------------------
    def output_exists(self, slug, step):
        P = T.Paths(slug, self.root)
        return {'fetch': lambda: P.text.exists(), 'triage': lambda: triage_complete(P),
                'run1': lambda: P.run(1).exists(), 'run2': lambda: P.run(2).exists(),
                'pair': lambda: False,                                       # computed, never skipped
                'units': lambda: (P.consensus / 'units.json').exists(),
                'gemini': lambda: (P.consensus / 'gemini.json').exists(),
                'export': lambda: (P.consensus / 'subagent/manifest.json').exists()}[step]()

    def gate(self, slug, step):
        """List of Result for the step's gate, [] when the step has none."""
        P = T.Paths(slug, self.root)
        if step == 'fetch':
            return [C.g1_text(P)]
        if step == 'triage':
            return [C.g2_triage(P)]
        if step in ('run1', 'run2'):
            return [C.g3_run(P, int(step[-1]))]
        if step == 'pair':
            return [C.g4_pair(P), C.g5_density(P)]
        if step == 'gemini':
            return [C.g6_judge(P, 'gemini'), C.g5_density(P)]
        return []

    def record_gate(self, slug, step, results):
        st = self.state[slug][step]
        st['gates'] = {r.gate: {'status': r.status, 'failures': r.failures, 'warnings': r.warnings,
                                'notes': r.notes, 'measured': {k: v for k, v in r.measured.items() if k != 'tokens'}}
                       for r in results}
        statuses = [r.status for r in results]
        return 'red' if 'red' in statuses else 'amber' if 'amber' in statuses else 'green'

    # ---- readiness ------------------------------------------------------------------
    def settle(self, slug):
        """Mark steps done/red from what is on disk, without running anything. Idempotent."""
        for step in STEPS:
            st = self.state[slug][step]
            if st['state'] not in ('pending', 'skipped'):
                continue
            if step == 'pair' or not self.output_exists(slug, step):
                continue
            if step in ('units', 'export'):
                st.update(state='skipped', color='green')
                continue
            colour = self.record_gate(slug, step, self.gate(slug, step))
            if colour == 'red' and not self.retry_failed:
                st.update(state='red', color='red')
            elif colour == 'red':
                st.update(state='pending', color=None)            # run it again
            else:
                st.update(state='skipped', color=colour)

    def ready(self, slug):
        out = []
        for step in self.wanted:
            st = self.state[slug][step]
            if st['state'] != 'pending':
                continue
            if all(self.state[slug][d]['state'] in ('done', 'skipped') and self.state[slug][d].get('color') != 'red'
                   for d in DEPENDS[step]):
                out.append(step)
        return out

    # ---- running one step --------------------------------------------------------------
    def do_step(self, slug, step):
        st = self.state[slug][step]
        P = T.Paths(slug, self.root)
        t0 = time.time()
        if step == 'pair':
            colour = self.record_gate(slug, step, self.gate(slug, step))
            return dict(state='done', color=colour, rc=0, seconds=0)
        cmd, env = self.command(slug, step)
        if step in ('run1', 'run2') and Path(str(P.run(int(step[-1]))) + '.partial.json').exists():
            st['resumed'] = True               # the runner will resume from its checkpoint: amber, never green
        logfile = self.root / f'results/shas_run/logs/{slug}-{step}.log'
        attempts = st.get('attempts', 0) + 1
        rc = self.execute(cmd, env, logfile)
        info = dict(rc=rc, attempts=attempts, seconds=round(time.time() - t0), log=str(logfile.relative_to(self.root)))
        if rc != 0:
            return dict(info, state='failed', color='red')
        if step == 'triage':
            tok = triage_tokens_from_log(logfile)
            if tok:
                info['tokens'] = tok
                info['cost_usd'] = cost_usd(tok)
        gates = self.gate(slug, step)
        colour = self.record_gate(slug, step, gates) if gates else 'green'
        if step in ('run1', 'run2') and colour != 'red':
            run = json.loads(P.run(int(step[-1])).read_text())
            tok = (run.get('run_meta') or {}).get('tokens')
            info['cost_usd'] = cost_usd(tok)
            info['tokens'] = tok
            if st.get('resumed') and colour == 'green':
                colour = 'amber'
        if step == 'gemini':
            # Charged even when red: Google bills a call whatever its answer was (2026-11-10, ~$15 unseen).
            log_ = (json.loads((P.consensus / 'gemini.json').read_text()).get('meta') or {}).get('token_log') or []
            if log_:
                info['tokens'] = log_[-1]
                info['cost_usd'] = cost_usd(log_[-1])
            if colour != 'red':
                info['note'] = 'Claude judge waits for a person (subagents): then import and g6 claude'
        return dict(info, state='done', color=colour)

    # ---- the loop ------------------------------------------------------------------------
    def overall(self, slug):
        sts = [self.state[slug][s] for s in self.wanted]
        if any(x['state'] in ('failed', 'red') or x.get('color') == 'red' for x in sts):
            return 'red'
        if any(x['state'] == 'running' for x in sts):
            return 'running'
        if all(x['state'] in ('done', 'skipped') for x in sts):
            return 'amber' if any(x.get('color') == 'amber' or x.get('resumed') for x in sts) else 'green'
        return 'pending'

    def write_status(self):
        for _ in range(5):                     # a worker may be updating a step as we copy it: try again
            try:
                return self._write_status()
            except RuntimeError:
                time.sleep(0.05)
        return self._write_status()

    def _write_status(self):
        with self.lock:
            # Merge into what is on disk: a run over some tractates must not erase the others' record, and a step
            # skipped this time (its output already there) keeps the cost it was charged when it ran (2026-11-10).
            try:
                prior = json.loads(self.status_path.read_text()).get('tractates', {})
            except (FileNotFoundError, json.JSONDecodeError):
                prior = {}
            tr = dict(prior)
            for s in self.slugs:
                old = (prior.get(s) or {}).get('steps', {})
                steps = {k: v for k, v in self.state[s].items() if k in self.wanted}
                for k, v in steps.items():
                    if v.get('state') == 'skipped' and 'cost_usd' not in v and old.get(k, {}).get('cost_usd'):
                        v['cost_usd'] = old[k]['cost_usd']
                tr[s] = {'overall': self.overall(s), 'steps': {**old, **steps}}
                tr[s]['cost_usd'] = round(sum(v.get('cost_usd', 0) for v in tr[s]['steps'].values()), 4)
            doc = {'updated': time.strftime('%Y-%m-%dT%H:%M:%S'), 'git_rev': self.rev, 'through': self.through,
                   'cost_usd': round(sum(t['cost_usd'] for t in tr.values()), 2), 'tractates': tr,
                   'counts': {c: sum(1 for t in tr.values() if t['overall'] == c)
                              for c in ('green', 'amber', 'red', 'running', 'pending')}}
            self.status_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.status_path.with_suffix('.json.tmp')
            tmp.write_text(json.dumps(doc, indent=1, ensure_ascii=False))
            os.replace(tmp, self.status_path)
            return doc

    def log_event(self, slug, step, st):
        gates = {g: v['status'] for g, v in (st.get('gates') or {}).items()}
        log.info('%s %s -> %s/%s rc=%s %ss gates=%s cost=$%s', slug, step, st['state'], st.get('color'),
                 st.get('rc'), st.get('seconds'), gates, st.get('cost_usd', 0))
        for g, v in (st.get('gates') or {}).items():
            for f in v['failures']:
                log.error('%s %s %s RED: %s', slug, step, g, f)
            for w in v['warnings']:
                log.warning('%s %s %s AMBER: %s', slug, step, g, w)

    def plan(self):
        for s in self.slugs:
            self.settle(s)
        return {s: self.ready(s) for s in self.slugs}

    def run(self):
        for s in self.slugs:
            self.settle(s)
        if self.dry_run:                       # shows the plan; writes nothing
            for s in self.slugs:
                todo = [st for st in self.wanted if self.state[s][st]['state'] == 'pending']
                print(f'{s:16s} {self.overall(s):8s} to do: {" ".join(todo) or "-"}')
            return 0
        self.write_status()
        running = {}
        with ThreadPoolExecutor(max_workers=self.max_parallel) as pool:
            while True:
                for s in self.slugs:                           # longest first
                    for step in self.ready(s):
                        n_step = sum(1 for (_, k) in running.values() if k == step)
                        if len(running) >= self.max_parallel or n_step >= LIMITS.get(step, self.max_parallel):
                            continue
                        self.state[s][step]['state'] = 'running'
                        self.state[s][step]['started'] = time.strftime('%H:%M:%S')
                        fut = pool.submit(self.do_step, s, step)
                        running[fut] = (s, step)
                        log.info('%s %s started', s, step)
                if not running:
                    break
                self.write_status()
                done, _ = wait(list(running), return_when=FIRST_COMPLETED)
                for fut in done:
                    s, step = running.pop(fut)
                    try:
                        res = fut.result()
                    except Exception as e:  # noqa: BLE001 - a crash in one step must not stop the others
                        res = dict(state='failed', color='red', error=f'{type(e).__name__}: {e}')
                    self.state[s][step].update(res)
                    self.log_event(s, step, self.state[s][step])
                    if step == 'gemini':       # g5's out-of-scope rate needs the judge: refresh the density gate
                        self.settle_density(s)
                    self.write_status()
        doc = self.write_status()
        log.info('run_shas finished: %s, cost so far $%s', doc['counts'], doc['cost_usd'])
        return 0 if not doc['counts']['red'] else 1

    def settle_density(self, slug):
        pair = self.state[slug]['pair']
        g5 = C.g5_density(T.Paths(slug, self.root))
        pair.setdefault('gates', {})['g5'] = {'status': g5.status, 'failures': g5.failures, 'warnings': g5.warnings,
                                             'notes': g5.notes, 'measured': g5.measured}
        if g5.status == 'amber' and pair.get('color') == 'green':
            pair['color'] = 'amber'


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--tractates', nargs='+', help='slugs (default: the 31 of the run)')
    ap.add_argument('--through', default='export', choices=STEPS, help='last step to run')
    ap.add_argument('--parallel', type=int, default=MAX_PARALLEL)
    ap.add_argument('--retry-failed', action='store_true')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--allow-dirty', action='store_true')
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s [run-shas] %(message)s',
                        handlers=[logging.FileHandler(PROJECT_ROOT / 'project.log'), logging.StreamHandler(sys.stdout)])
    slugs = [T.resolve(t) for t in args.tractates] if args.tractates else default_tractates()
    rev = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=PROJECT_ROOT, capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(['git', 'status', '--porcelain', '--', 'src', 'scripts'], cwd=PROJECT_ROOT,
                           capture_output=True, text=True).stdout.strip()
    if dirty and not args.allow_dirty and not args.dry_run:
        print('Uncommitted changes under src/ or scripts/: pin the code to a commit first (or --allow-dirty).')
        print(dirty)
        return 2
    d = Driver(PROJECT_ROOT, slugs, max_parallel=args.parallel, through=args.through,
               retry_failed=args.retry_failed, dry_run=args.dry_run)
    d.rev = rev
    log.info('run_shas: %d tractates, through %s, rev %s', len(slugs), args.through, rev[:10])
    return d.run()


if __name__ == '__main__':
    sys.exit(main())
