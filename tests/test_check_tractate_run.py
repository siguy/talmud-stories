"""The Shas-run gates (scripts/check_tractate_run.py), tested on a tiny made-up tractate.

Each test breaks ONE thing and asserts the gate goes red for that reason. The point is Lesson 21 /
38: a failed call, a missing page or a missing answer must never read as 'no stories' or 'all fine'.
"""
import copy
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT))

import check_tractate_run as C  # noqa: E402
from tractates import Paths, resolve, english, hebrew, SLUGS  # noqa: E402

SLUG = 'tamid'
HE = 'אֲמַר לֵיהּ'


def _page(ref, n=3):
    return {'ref': ref, 'segments': [{'index': i, 'hebrew': HE, 'english': f'text {i}'} for i in range(n)]}


def _story(a, b, cls='YES'):
    return {'start_segment': a, 'end_segment': b, 'classification': cls}


def _run(refs, tokens=True, **meta):
    pages = []
    for k, r in enumerate(refs):
        p = _page(r)
        p['stories'] = [_story(0, 1)] if k % 2 == 0 else []
        p['mishnah_stories'] = []
        if k % 2 == 1:
            p['skipped_by_triage'] = True
        pages.append(p)
    m = {'model': 'gemini-3-flash-preview', 'thinking_level': None, 'detector_module': 'src.story_detector_v14',
         'twin_trigger': 'all', 'stage2_fingerprint': 'abc', 'detector_sha1': 'd' * 40, 'triage_sha1': None,
         'stage2_errors': [], 'truncated_responses': 0, 'empty_responses': 0, 'twin_failures': [],
         'pass2_failures': [], 'resumed_pages': 0, 'triage_failed': {'count': 0, 'refs': []},
         'tokens': {'stage2_and_4': {'calls': 10, 'unmetered': 0, 'input': 1, 'output': 1, 'thinking': 0,
                                     'retries': 0, 'retries_exhausted': 0}} if tokens else {}}
    m.update(meta)
    return {'tractate': 'Tamid', 'version': 'v14', 'pages': pages, 'span_repairs': [],
            'stage4_call_failures': [], 'run_meta': m}


def build(tmp, mutate=None, slug='tamid'):
    """A tractate that passes every gate; `mutate(files)` edits the dict of json files first."""
    nm = slug.title()
    refs = [f'{nm} {n}{a}' for n in range(25, 28) for a in 'ab']
    files = {
        f'results/sefaria/{slug}.json': {'tractate': nm, 'sefaria_shape': {r: 3 for r in refs}, 'pages': [_page(r) for r in refs]},
        f'results/triage/{slug}.json': {'tractate': nm, 'triage_results': {r: ['DELIBERATION'] for r in refs}},
    }
    tri = json.dumps(files[f'results/triage/{slug}.json'], indent=2, ensure_ascii=False)
    sha = hashlib.sha1(tri.encode()).hexdigest()
    for n in (1, 2):
        files[f'results/v14/{slug}/run{n}.json'] = _run(refs, triage_sha1=sha)
    units = [{'id': f'{nm} 25a:0-1', 'cells': [[f'{nm} 25a', 0], [f'{nm} 25a', 1]]},
             {'id': f'{nm} 26a:0-1', 'cells': [[f'{nm} 26a', 0], [f'{nm} 26a', 1]]}]
    files[f'results/consensus/{slug}/units.json'] = {'meta': {}, 'units': units}
    ans = lambda v, o='ok': {'outcome': o, 'verdict': v if o == 'ok' else None}
    for who in ('gemini', 'claude'):
        files[f'results/consensus/{slug}/{who}.json'] = {
            'meta': {'prompt_sha': C.JUDGE_PROMPT_SHA, 'missing_batches': []},
            'rows': [{'id': units[0]['id'], 'answer': ans('out_of_scope')}, {'id': units[1]['id'], 'answer': ans('story')}]}
    if mutate:
        mutate(files)
    for rel, obj in files.items():
        p = Path(tmp) / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        # the triage file is written with the exact text its sha was taken of
        p.write_text(json.dumps(obj, indent=2, ensure_ascii=False) if '/triage/' in rel else json.dumps(obj, ensure_ascii=False))
    return Paths(slug, tmp)


def statuses(P):
    return {r.gate: r.status for r in C.run_all(P)}


def test_a_clean_tractate_is_green_everywhere(tmp_path):
    P = build(tmp_path)
    got = C.run_all(P)
    assert all(r.status in ('green', 'amber') for r in got), [(r.gate, r.failures) for r in got if r.status == 'red']
    assert statuses(P)['g3:run1'] == 'green' and statuses(P)['g4'] == 'green'


def test_missing_inputs_are_pending_under_all_but_red_when_asked(tmp_path):
    P = Paths(SLUG, tmp_path)
    assert all(r.status == 'pending' for r in C.run_all(P))
    assert C.g3_run(P, 1).status == 'red'


# ---- G1
def test_g1_missing_page_gap_is_red(tmp_path):
    def m(f):
        f['results/sefaria/tamid.json']['pages'].pop(2)
    r = C.g1_text(build(tmp_path, m))
    assert r.status == 'red' and any('contiguous' in x for x in r.failures)
    assert any('differ from the Sefaria index' in x for x in r.failures)


def test_g1_hebrew_missing_and_vowels(tmp_path):
    def m(f):
        f['results/sefaria/tamid.json']['pages'][0]['segments'][0]['hebrew'] = ''
        for p in f['results/sefaria/tamid.json']['pages']:
            for g in p['segments']:
                g['hebrew'] = g['hebrew'] and 'אמר ליה'      # no vowel points
    r = C.g1_text(build(tmp_path, m))
    assert any('no Hebrew' in x for x in r.failures) and any('vowel' in x for x in r.failures)


def test_g1_empty_english_is_counted_not_failed(tmp_path):
    def m(f):
        f['results/sefaria/tamid.json']['pages'][1]['segments'][2]['english'] = ''
    r = C.g1_text(build(tmp_path, m))
    assert r.status == 'green' and r.measured['empty_english'] == 1 and any('empty English' in n for n in r.notes)


def test_g1_amud_blank_in_source_is_noted_not_red(tmp_path):
    """Nazir 33b (2026-11-09): Sefaria's own index counts 0 segments there. Its absence is
    expected and named; a real missing page beside it is still red."""
    def m(f):
        d = f['results/sefaria/tamid.json']
        gone = d['pages'].pop(2)['ref']
        d['sefaria_shape'][gone] = 0
    r = C.g1_text(build(tmp_path, m))
    assert r.status == 'green', r.failures
    assert any('blank in the source' in n for n in r.notes)

    def m2(f):
        m(f)
        f['results/sefaria/tamid.json']['pages'].pop(4)
    r = C.g1_text(build(tmp_path / 'b', m2))
    assert r.status == 'red' and any('differ from the Sefaria index' in x for x in r.failures)


# ---- G2
def test_g2_all_failed_page_and_unlabelled_page_are_red(tmp_path):
    def m(f):
        t = f['results/triage/tamid.json']['triage_results']
        t['Tamid 25a'] = ['TRIAGE_FAILED', 'TRIAGE_FAILED']
        del t['Tamid 26b']
    r = C.g2_triage(build(tmp_path, m))
    assert r.status == 'red' and len(r.failures) == 2


# ---- G3: every injected failure must be red, never a quiet pass
def _g3(tmp_path, **meta):
    def m(f):
        f['results/v14/tamid/run1.json']['run_meta'].update(meta)
    return C.g3_run(build(tmp_path, m), 1)


def test_g3_stage2_error_truncation_empty_are_red(tmp_path):
    assert _g3(tmp_path / 'a', stage2_errors=['Tamid 25a: boom']).status == 'red'
    assert _g3(tmp_path / 'b', truncated_responses=1).status == 'red'
    assert _g3(tmp_path / 'c', empty_responses=3).status == 'red'


def test_g3_unmetered_and_missing_meter_are_red(tmp_path):
    bad = {'stage2_and_4': {'calls': 5, 'unmetered': 1, 'input': 0, 'output': 0, 'thinking': 0}}
    assert _g3(tmp_path / 'a', tokens=bad).status == 'red'
    assert _g3(tmp_path / 'b', tokens={}).status == 'red'


def test_g3_addition_failures_listed_up_to_three_then_red(tmp_path):
    r = _g3(tmp_path / 'a', pass2_failures=['Tamid 25a'])
    assert r.status == 'green' and any('pass2_failures' in n for n in r.notes)
    assert _g3(tmp_path / 'b', pass2_failures=['a', 'b', 'c', 'd']).status == 'red'


def test_g3_wrong_configuration_is_red(tmp_path):
    assert _g3(tmp_path / 'a', model='gemini-2.5-flash').status == 'red'
    assert _g3(tmp_path / 'b', thinking_level='high').status == 'red'
    assert _g3(tmp_path / 'c', twin_trigger='gated').status == 'red'
    assert _g3(tmp_path / 'd', detector_module='src.story_detector_v11').status == 'red'


def test_g3_run_missing_a_page_is_red(tmp_path):
    def m(f):
        f['results/v14/tamid/run1.json']['pages'].pop()
    assert C.g3_run(build(tmp_path, m), 1).status == 'red'


def test_g3_retriage_is_red_and_resume_is_amber(tmp_path):
    assert _g3(tmp_path / 'a', triage_sha1='0' * 40).status == 'red'
    assert _g3(tmp_path / 'b', resumed_pages=4).status == 'amber'


# ---- G4
def test_g4_different_fingerprint_detector_or_triage_is_red(tmp_path):
    for k, v in (('stage2_fingerprint', 'zzz'), ('detector_sha1', 'e' * 40), ('triage_sha1', 'f' * 40)):
        def m(f, k=k, v=v):
            f['results/v14/tamid/run2.json']['run_meta'][k] = v
        assert C.g4_pair(build(tmp_path / k, m)).status == 'red', k


def test_g4_kept_counts_and_agreement(tmp_path):
    def m(f):
        run = f['results/v14/tamid/run2.json']
        for p in run['pages']:
            p['stories'] = []                 # run 2 found nothing: counts differ, nothing in both
    r = C.g4_pair(build(tmp_path, m))
    assert r.status == 'red' and any('kept-story' in x for x in r.failures)


def test_g4_agreement_below_threshold_is_red(tmp_path):
    # 10 definite passages in run 1; run 2 agrees on 8 of them -> 8/12 passages in both
    refs = [f'Tamid {n}a' for n in range(25, 35)]

    def m(f):
        f['results/sefaria/tamid.json']['pages'] = [_page(r) for r in refs]
        a, b = _run(refs), _run(refs)
        for run in (a, b):
            for p in run['pages']:
                p['stories'] = [_story(0, 0)]
                p.pop('skipped_by_triage', None)
        b['pages'][0]['stories'] = [_story(2, 2)]
        b['pages'][1]['stories'] = [_story(2, 2)]
        f['results/v14/tamid/run1.json'], f['results/v14/tamid/run2.json'] = a, b
    r = C.g4_pair(build(tmp_path, m))
    assert r.measured['definite_in_both'] == 8 and r.measured['definite_passages'] == 12
    assert any('definite in both' in x for x in r.failures)


def test_definite_agreement_on_the_real_baselines_is_what_the_plan_says():
    """The G4 threshold was chosen after this measurement (Berakhot 116/126, Yevamot 83/90)."""
    for slug, want in (('berakhot', (126, 116)), ('yevamot', (90, 83))):
        P = Paths(slug, ROOT)
        a, b = json.loads(P.run(1).read_text()), json.loads(P.run(2).read_text())
        assert C.definite_agreement(a, b) == want
        assert want[1] / want[0] > C.DEFINITE_BOTH_MIN


# ---- G5
def test_g5_density_outside_the_range_is_amber_not_red(tmp_path):
    def m(f):
        run = f['results/v14/tamid/run1.json']
        for p in run['pages']:
            p['stories'] = [_story(0, 0)] * 30
            p.pop('skipped_by_triage', None)
        f['results/v14/berakhot/run1.json'] = _run([f'Berakhot {n}a' for n in range(2, 8)])   # something to compare with
    r = C.g5_density(build(tmp_path, m))
    assert r.status == 'amber'


def test_g5_without_the_judge_says_pending_in_a_note(tmp_path):
    P = build(tmp_path)
    (Path(P.consensus) / 'gemini.json').unlink()
    r = C.g5_density(P)
    assert any('pending' in n for n in r.notes)


# ---- G6: a missing answer must not read as 'not biblical'
def test_g6_claude_missing_an_out_of_scope_answer_is_red(tmp_path):
    def m(f):
        f['results/consensus/tamid/claude.json']['rows'].pop(0)
    r = C.g6_judge(build(tmp_path, m), 'claude')
    assert r.status == 'red' and any('out_of_scope' in x for x in r.failures)


def test_g6_claude_answer_that_is_not_ok_for_a_flagged_unit_is_red(tmp_path):
    def m(f):
        f['results/consensus/tamid/claude.json']['rows'][0]['answer'] = {'outcome': 'invalid', 'verdict': None}
    r = C.g6_judge(build(tmp_path, m), 'claude')
    assert r.status == 'red'


def test_g6_claude_subset_is_fine_when_every_flagged_unit_is_answered(tmp_path):
    def m(f):
        f['results/consensus/tamid/claude.json']['rows'].pop(1)       # the unflagged unit
    r = C.g6_judge(build(tmp_path, m), 'claude')
    assert r.status == 'green' and any('subset' in n for n in r.notes)


def test_g6_gemini_failed_row_missing_unit_and_wrong_prompt_are_red(tmp_path):
    def m1(f):
        f['results/consensus/tamid/gemini.json']['rows'][1]['answer'] = {'outcome': 'failed', 'verdict': None}
    assert C.g6_judge(build(tmp_path / 'a', m1), 'gemini').status == 'red'

    def m2(f):
        f['results/consensus/tamid/gemini.json']['rows'].pop()
    assert any('no Gemini answer' in x for x in C.g6_judge(build(tmp_path / 'b', m2), 'gemini').failures)

    def m3(f):
        f['results/consensus/tamid/gemini.json']['meta']['prompt_sha'] = 'deadbeef0000'
    assert C.g6_judge(build(tmp_path / 'c', m3), 'gemini').status == 'red'


def _rulings(f, g4=(), alone=None):
    f['results/shas_run/decisions.json'] = {'g4_accepted': {'tractates': list(g4)},
                                            'claude_alone': {'units': alone or {}}}


def test_g4_below_threshold_is_amber_only_for_a_tractate_simon_ruled_on(tmp_path):
    refs = [f'Tamid {n}a' for n in range(25, 35)]

    def m(f, ruled):
        f['results/sefaria/tamid.json']['pages'] = [_page(r) for r in refs]
        a, b = _run(refs), _run(refs)
        for run in (a, b):
            for p in run['pages']:
                p['stories'] = [_story(0, 0)]
                p.pop('skipped_by_triage', None)
        b['pages'][0]['stories'] = [_story(2, 2)]
        f['results/v14/tamid/run1.json'], f['results/v14/tamid/run2.json'] = a, b
        _rulings(f, g4=['tamid'] if ruled else ['sotah'])
    assert C.g4_pair(build(tmp_path / 'no', lambda f: m(f, False))).status == 'red'
    r = C.g4_pair(build(tmp_path / 'yes', lambda f: m(f, True)))
    assert r.status == 'amber' and any('ruling' in w for w in r.warnings)


def test_g4_ruling_never_excuses_different_code(tmp_path):
    def m(f):
        f['results/v14/tamid/run2.json']['run_meta']['detector_sha1'] = 'other'
        _rulings(f, g4=['tamid'])
    assert C.g4_pair(build(tmp_path, m)).status == 'red'


def test_g6_invalid_gemini_row_is_amber_only_when_ruled_and_then_claude_must_answer_it(tmp_path):
    uid = 'Tamid 26a:0-1'

    def m(f, ruled, claude_ok=True):
        f['results/consensus/tamid/gemini.json']['rows'][1]['answer'] = {'outcome': 'invalid', 'verdict': None}
        if not claude_ok:
            f['results/consensus/tamid/claude.json']['rows'].pop(1)
        _rulings(f, alone={'tamid': [uid]} if ruled else {})
    assert C.g6_judge(build(tmp_path / 'a', lambda f: m(f, False)), 'gemini').status == 'red'
    assert C.g6_judge(build(tmp_path / 'b', lambda f: m(f, True)), 'gemini').status == 'amber'
    assert C.g6_judge(build(tmp_path / 'c', lambda f: m(f, True)), 'claude').status == 'green'
    assert C.g6_judge(build(tmp_path / 'd', lambda f: m(f, True, claude_ok=False)), 'claude').status == 'red'


# ---- the table
def test_slugs_follow_the_convention_and_keep_existing_names():
    assert resolve('Bava Batra') == 'bava_batra' == resolve('bava batra') == resolve('bava_batra')
    for old in ('berakhot', 'yevamot', 'ketubot', 'kiddushin', 'gittin', 'eruvin'):
        assert old in SLUGS
    assert len(SLUGS) == 37 and all(v['hebrew'] for v in SLUGS.values())
    assert english('bava_batra') == 'Bava Batra' and hebrew('berakhot') == 'ברכות'


def test_legacy_paths_are_kept(tmp_path):
    assert str(Paths('yevamot', ROOT).run(1)).endswith('results/v11/v14_yevamot/run1.json')
    assert str(Paths('kiddushin', ROOT).text).endswith('results/v7/kiddushin_pages.json')
    assert str(Paths('bava_batra', ROOT).run(2)).endswith('results/v14/bava_batra/run2.json')
