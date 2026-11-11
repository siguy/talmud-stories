"""A random sample of shipped, unreviewed stories for an expert to grade: the measurement that would turn the site's
precision from INDICATED into MEASURED (docs/findings/2026-11-10-shas-accuracy.md §4.1).

Stratified, because one stratum would not generalise (Lesson 18): 20 stories from each of
  aggadic  -- tractates dense with narrative (Sanhedrin, Megillah, Taanit, Sotah, Berakhot, Chagigah)
  kodashim -- Seder Kodashim and Niddah: few stories, the shape least like what the rules were built on
  halakhic -- every other unreviewed tractate on the site
Seeded, so it reproduces. Reads site/data only (what actually ships); no model calls.

    python3 scripts/build_precision_sample.py     # -> results/shas_run/precision_sample/ + the review page
"""
import json
import logging
import random
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
import tractates as T  # noqa: E402

SEED, PER_STRATUM = 20261110, 20
AGGADIC = ('sanhedrin', 'megillah', 'taanit', 'sotah', 'berakhot', 'chagigah')
KODASHIM = ('zevachim', 'menachot', 'chullin', 'bekhorot', 'arakhin', 'temurah', 'keritot', 'meilah', 'tamid', 'niddah')
OUT = ROOT / 'results/shas_run/precision_sample'
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s [precision-sample] %(message)s',
                    handlers=[logging.StreamHandler(), logging.FileHandler(ROOT / 'project.log')])
log = logging.getLogger('precision-sample')


def stratum(slug):
    return 'aggadic' if slug in AGGADIC else 'kodashim' if slug in KODASHIM else 'halakhic'


def main():
    index = json.loads((ROOT / 'site/data/index.json').read_text())
    pools = {'aggadic': [], 'kodashim': [], 'halakhic': []}
    for row in index['tractates']:
        t = row['tractate']
        for s in json.loads((ROOT / f'site/data/{t}.json').read_text())['stories']:
            if s['reviewed']:
                continue                       # only what no expert has graded
            end = int(s['id'].rsplit('-', 1)[1])
            pools[stratum(t)].append({'tractate': t, 'id': s['id'], 'ref': s['ref'],
                                      'start_segment': s['start_segment'], 'end_segment': end,
                                      'biblical': s.get('biblical', False)})
    rng = random.Random(SEED)
    sample = []
    for name, pool in pools.items():
        pick = rng.sample(pool, min(PER_STRATUM, len(pool)))
        for p in pick:
            p['stratum'] = name
        sample += pick
        log.info('%s: %d of %d shipped stories', name, len(pick), len(pool))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'sample.json').write_text(json.dumps(sample, ensure_ascii=False, indent=1))
    # The review page reads a run's current grade, so a story Stage 4j demoted for biblical-only actors -- which the site
    # ships under its pre-filter grade (septimus-story-filter.md) -- would be silently left out (Sanhedrin 99b:3-4 in
    # this seed, 2026-11-10). The page gets temporary copies carrying the grade the site reads; the runs on disk are
    # never edited.
    import tempfile
    tmp = Path(tempfile.mkdtemp(prefix='precision_sample_'))
    runs = []
    for t in sorted({s['tractate'] for s in sample}):
        run = json.loads(T.Paths(t, ROOT).run(1).read_text())
        for p in run['pages']:
            for st in p.get('stories', []):
                if st.get('filtered_as_biblical'):
                    st['classification'] = st.get('classification_pre_biblical_filter')
        (tmp / f'{t}_run1.json').write_text(json.dumps(run, ensure_ascii=False))
        runs.append(str(tmp / f'{t}_run1.json'))
    only = OUT / 'only.json'
    only.write_text(json.dumps([{k: s[k] for k in ('ref', 'start_segment', 'end_segment')} for s in sample]))
    cmd = [sys.executable, 'validation/generators/generate_axis_review_ui.py', '--run', *runs,
           '--only', str(only.relative_to(ROOT)), '--out', 'shas_precision_sample.html',
           '--title', 'Talmud stories: a random sample to grade',
           '--note', 'Stories chosen at random from what the site shows, from every kind of tractate. '
                     'For each: is it a story?']
    rc = subprocess.run(cmd, cwd=ROOT).returncode
    log.info('sample of %d written; review page rc=%d', len(sample), rc)
    return rc


if __name__ == '__main__':
    sys.exit(main())
