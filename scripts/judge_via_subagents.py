"""The Claude arm of the consensus judge, answered by Claude Code subagents instead of the API.

Why this exists: on 2026-10-01 Simon declined to fund Anthropic API calls for phase 1b
(work/2026-09-28-consensus-1b-corrected-register.md). The second judge is instead a
Claude Code subagent, which reads the SAME system prompt and the SAME per-span user
prompt that judge_labelled_spans.py sends, and whose answers pass through the SAME
ask() validation. A failed or invalid answer is counted, never scored (Lesson 21).

What differs from the API arm -- recorded in the output's `meta`, and in the finding:
  * the model is the subagent's, not `claude-opus-5`;
  * one subagent judges a BATCH of spans in one context, not one call per span. Spans
    are shuffled into batches with a seed, so batch-mates are unrelated; the repeat uses
    a different seed, so the repeat also measures what batch-mates do to a verdict;
  * the judge prompt arrives as a file the subagent reads, not as the system prompt;
  * no structured-output constraint -- the JSON is checked by ask() exactly as Gemini's is.

    python3 scripts/judge_via_subagents.py export --run full_v2_claude --seed 1 --batch 25
    #  ... one subagent per batch file writes answers/<batch>.json ...
    python3 scripts/judge_via_subagents.py import --run full_v2_claude --model <what ran>

Eruvin is never read (labels.json carries none).
"""
import argparse
import json
import logging
import random
import sys
import time
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))
sys.path.insert(0, str(PROJECT_ROOT))
import judge_labelled_spans as j  # noqa: E402

log = logging.getLogger('consensus-subagent')
WORK_DIR = j.OUT_DIR / 'subagent'          # batch files + raw answers, kept as evidence


def export(run, seed, batch):
    labels = json.loads((j.OUT_DIR / 'labels.json').read_text())
    units = j.select('full', labels)
    texts = {t: j.Text(t) for t in {u['tractate'] for u in units}}
    order = list(units)
    random.Random(seed).shuffle(order)
    d = WORK_DIR / run
    (d / 'batches').mkdir(parents=True, exist_ok=True)   # what the agents read: text only
    (d / 'keys').mkdir(parents=True, exist_ok=True)      # span ids -- never shown to an agent
    (d / 'answers').mkdir(parents=True, exist_ok=True)
    (d / 'system_prompt.md').write_text(j.system_prompt())
    n = 0
    for i in range(0, len(order), batch):
        items = []
        for u in order[i:i + batch]:
            prompt, passage = j.user_prompt(u, texts[u['tractate']])
            items.append({'id': u['id'], 'prompt': prompt, 'passage': sorted(passage)})
        (d / 'keys' / f'{n:03d}.json').write_text(json.dumps(items, ensure_ascii=False, indent=1))
        # One plain-text file per span for the subagent to `cat`: the Read tool truncates
        # long lines, and a truncated passage would be judged as something it is not.
        sd = d / 'batches' / f'{n:03d}'
        sd.mkdir(exist_ok=True)
        for k, it in enumerate(items, start=1):
            # Named by number only: the span id says `list:` for a story on his list,
            # which is the label itself. The API arms never saw it; neither may this one.
            (sd / f'{k:02d}.txt').write_text(it['prompt'] + '\n')
        n += 1
    (d / 'manifest.json').write_text(json.dumps({
        'run': run, 'seed': seed, 'batch': batch, 'batches': n, 'units': len(order),
        'prompt_sha': j.prompt_sha(),
        'rules_sha': __import__('hashlib').sha256(j.RULES_PATH.read_bytes()).hexdigest()[:12],
        'exported': time.strftime('%Y-%m-%dT%H:%M:%S')}, indent=1))
    log.info('exported %d units into %d batches under %s (prompt %s)', len(order), n, d, j.prompt_sha())


def import_(run, model):
    d = WORK_DIR / run
    man = json.loads((d / 'manifest.json').read_text())
    if man['prompt_sha'] != j.prompt_sha():
        raise RuntimeError('prompt changed since export -- re-export')
    labels = {u['id']: u for u in json.loads((j.OUT_DIR / 'labels.json').read_text())['units']}
    system = j.system_prompt()
    # Spans an agent did not see in full (its tool output was cut off -- found by auditing
    # the transcripts) were re-judged one file at a time by a fresh agent; those answers
    # replace the originals, and the row says so.
    redo = {}
    if (d / 'rejudge' / 'map.txt').exists():
        re_ans = json.loads((d / 'rejudge' / 'answers.json').read_text())
        for line in (d / 'rejudge' / 'map.txt').read_text().split('\n'):
            if line.strip():
                k, where = line.split()
                redo[where] = re_ans.get(k)
    rows, missing_batches = [], []
    for bf in sorted((d / 'keys').glob('*.json')):
        items = json.loads(bf.read_text())
        af = d / 'answers' / bf.name
        raw = {}
        if af.exists():
            try:
                raw = json.loads(af.read_text())
            except json.JSONDecodeError as e:
                log.warning('batch %s answers unreadable (%s) -- every item counted invalid', bf.name, e)
                raw = {f'{k:02d}': f'<<unreadable answers file: {e}>>' for k in range(1, len(items) + 1)}
        else:
            missing_batches.append(bf.name)
        for k, it in enumerate(items, start=1):
            u = labels[it['id']]
            key = f'{k:02d}'                  # answers are keyed by the file number the agent saw
            rejudged = f'{bf.stem}/{key}' in redo
            if rejudged and redo[f'{bf.stem}/{key}'] is not None:
                raw[key] = redo[f'{bf.stem}/{key}']
            if key in raw:
                ans_obj = raw[key]
                backend = lambda _s, _u, a=ans_obj: a if isinstance(a, str) else json.dumps(a, ensure_ascii=False)
            else:
                def backend(_s, _u):
                    raise RuntimeError('no answer from the subagent for this span')
            ans = j.ask(backend, system, it['prompt'], set(it['passage']))
            rows.append({**{k: u[k] for k in ('id', 'kind', 'tractate', 'key', 'label', 'evidence',
                                               'cited_in_rules', 'cells')},
                         'answers': {'claude': ans}, **({'rejudged': True} if rejudged else {})})
    meta = {'set': 'full', 'prompt': str(j.PROMPT_PATH.relative_to(PROJECT_ROOT)),
            'prompt_sha': j.prompt_sha(), 'rules_sha': man.get('rules_sha'),
            'backends': {'claude': {'model': model, 'via': 'Claude Code subagent (Agent tool), not the API',
                                    'batch': man['batch'], 'seed': man['seed']}},
            'claude_usd': 0.0, 'missing_batches': missing_batches, 'rejudged': sorted(redo),
            'imported': time.strftime('%Y-%m-%dT%H:%M:%S')}
    out = j.OUT_DIR / f'{run}.json'
    out.write_text(json.dumps({'meta': meta, 'rows': rows}, ensure_ascii=False, indent=1) + '\n')
    log.info('wrote %s: %s; missing batches %s', out,
             dict(Counter(r['answers']['claude']['outcome'] for r in rows)), missing_batches)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    e = sub.add_parser('export')
    e.add_argument('--run', required=True)
    e.add_argument('--seed', type=int, required=True)
    e.add_argument('--batch', type=int, default=25)
    i = sub.add_parser('import')
    i.add_argument('--run', required=True)
    i.add_argument('--model', required=True)
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s [consensus-subagent] %(message)s',
                        handlers=[logging.FileHandler(PROJECT_ROOT / 'project.log'),
                                  logging.StreamHandler(sys.stdout)])
    if args.cmd == 'export':
        export(args.run, args.seed, args.batch)
    else:
        import_(args.run, args.model)


if __name__ == '__main__':
    main()
