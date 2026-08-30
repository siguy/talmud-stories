#!/usr/bin/env python3
"""
Wave 5b: clause-role labelling and deterministic boundary assembly.

The model labels REAL UNITS (Hebrew clauses, English sentences) and never emits a
boundary or a character position. We compute the boundary from the labels. See
tasks/PLAN_wave5b_clause_roles.md for why, and src/prompts/clause_roles_v2.md for
the prompt and its provenance in Jeff Rubenstein's own language.
"""
import json
import re
from pathlib import Path
from typing import Dict, List, Optional

PROMPT_VERSION = 'clause_roles_v2'
PROMPT_PATH = Path(__file__).parent / 'prompts' / f'{PROMPT_VERSION}.md'

ROLES = ('narrative', 'variant', 'parallel', 'framing', 'comment', 'legal', 'source', 'unclear')
IN_STORY = frozenset({'narrative', 'variant'})   # Jeff keeps "some say" variants
ASSEMBLY_RULES = ('first_last', 'longest_run')

_SENT_SPLIT = re.compile(r'(?<=[.!?])\s+')
_HTML = re.compile(r'<[^>]+>')


def split_english_sentences(english: str) -> List[str]:
    """Sentence-split the English, keeping Sefaria's bold markup out of the text.

    Bold marks literal Talmud text vs the editor's added explanation. It is useful
    EVIDENCE but never a rule: 'The Gemara comments:' precedes a correct cut on
    Kiddushin 12b seg 4 and a wrong one on 22b seg 18 (Lesson 15, in English).
    """
    text = re.sub(r'\s+', ' ', _HTML.sub('', english or '')).strip()
    return [s.strip() for s in _SENT_SPLIT.split(text) if s.strip()]


def build_prompt(summary: str, hebrew_clauses: List[str], english_sentences: List[str]) -> str:
    """Render the versioned prompt. The prompt text lives in the .md so it is
    reviewable and diffable on its own, not buried in code."""
    body = PROMPT_PATH.read_text()
    template = body.split('## PROMPT', 1)[1].split('---', 1)[0].strip()
    return (template
            .replace('{summary}', summary or '(no summary available)')
            .replace('{hebrew_clauses}', '\n'.join(f'  [{i}] {c}' for i, c in enumerate(hebrew_clauses)))
            .replace('{english_sentences}', '\n'.join(f'  ({i}) {s}' for i, s in enumerate(english_sentences)))
            .replace('{{', '{').replace('}}', '}'))


def parse_labels(parsed: Optional[Dict], n_heb: int, n_eng: int) -> Optional[Dict]:
    """Validate and normalise the model's JSON. Returns None if unusable."""
    if not isinstance(parsed, dict):
        return None
    heb = {}
    for item in parsed.get('hebrew') or []:
        try:
            i = int(item['i'])
        except (KeyError, TypeError, ValueError):
            continue
        if 0 <= i < n_heb:
            role = item.get('role')
            heb[i] = {'role': role if role in ROLES else 'unclear',
                      'speech': bool(item.get('speech', False))}
    if not heb:
        return None
    eng = {}
    for item in parsed.get('english') or []:
        try:
            i = int(item['i'])
        except (KeyError, TypeError, ValueError):
            continue
        if 0 <= i < n_eng:
            role = item.get('role')
            covers = [c for c in (item.get('covers') or []) if isinstance(c, int) and 0 <= c < n_heb]
            eng[i] = {'role': role if role in ROLES else 'unclear',
                      'speech': bool(item.get('speech', False)), 'covers': covers}
    # any clause the model skipped is unclear, not silently narrative
    for i in range(n_heb):
        heb.setdefault(i, {'role': 'unclear', 'speech': False})
    return {'hebrew': heb, 'english': eng}


def assemble(labels: Dict, n_clauses: int, rule: str = 'first_last') -> Dict:
    """Turn per-clause labels into a boundary. Deterministic; no model involved."""
    if rule not in ASSEMBLY_RULES:
        raise ValueError(f'unknown assembly rule: {rule}')
    heb = labels['hebrew']
    in_story = [i for i in range(n_clauses) if heb.get(i, {}).get('role') in IN_STORY]
    if not in_story:
        # Never trim to nothing — keep the whole segment and say so.
        return {'first': 0, 'last': n_clauses - 1, 'kept_full': True,
                'reason': 'no_in_story_clause', 'needs_review': True}
    if rule == 'first_last':
        first, last = in_story[0], in_story[-1]
    else:
        best = run = [in_story[0]]
        for prev, cur in zip(in_story, in_story[1:]):
            run = run + [cur] if cur == prev + 1 else [cur]
            if len(run) > len(best):
                best = run
        first, last = best[0], best[-1]
    edge_unclear = any(heb.get(i, {}).get('role') == 'unclear'
                       for i in (first - 1, first, last, last + 1) if 0 <= i < n_clauses)
    return {'first': first, 'last': last, 'kept_full': (first == 0 and last == n_clauses - 1),
            'reason': rule, 'needs_review': edge_unclear}


def cross_language_disagreement(labels: Dict) -> Dict:
    """Compare each Hebrew clause's role against the English sentence covering it.

    English sentences nest over Hebrew clauses, so the two views must agree on
    in-story vs not. Where they disagree, something is wrong — a free error signal
    with no second model and no expert time.
    """
    heb, eng = labels['hebrew'], labels['english']
    covered, disagree = 0, []
    for ei, e in eng.items():
        e_in = e['role'] in IN_STORY
        for hi in e.get('covers', []):
            h = heb.get(hi)
            if not h:
                continue
            covered += 1
            if (h['role'] in IN_STORY) != e_in:
                disagree.append({'hebrew_clause': hi, 'hebrew_role': h['role'],
                                 'english_sentence': ei, 'english_role': e['role']})
    return {'clauses_covered': covered, 'n_disagree': len(disagree),
            'rate': (len(disagree) / covered) if covered else None, 'cases': disagree}


def speech_profile(labels: Dict) -> Dict:
    """Composition of the in-story clauses — speech vs non-speech.

    This is the field that makes Jeff's speech-act question a query instead of a
    judgment call: 'how many stories are nothing but speech?' See PLAN_wave6.
    """
    heb = labels['hebrew']
    story = [v for v in heb.values() if v['role'] in IN_STORY]
    if not story:
        return {'in_story_clauses': 0, 'speech_clauses': 0, 'speech_ratio': None,
                'all_speech': None}
    sp = sum(1 for v in story if v['speech'])
    return {'in_story_clauses': len(story), 'speech_clauses': sp,
            'speech_ratio': round(sp / len(story), 3), 'all_speech': sp == len(story)}
