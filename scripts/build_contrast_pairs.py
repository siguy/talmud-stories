"""Contrast pairs for Jeff: one question per feature boundary, each with passages for him to rule on.

work/2026-10-02-jeff-feature-questions.md. The rule-panel diagnostic
(docs/findings/2026-10-02-rule-panel-lenses.md) showed which features carry the
disagreement. Each question here names one of them, says what he has already ruled, says
what OUR current reading is (marked as ours), and gives passages to rule on, each a span he
has labelled where that feature alone decides the verdict.

The passages are chosen by hand from the panel's output and every choice is checked here:
the span must exist in labels.json, and the panel's deciding feature on it must be the
question's feature in at least one arm. A choice that fails is an error, not a warning.
`reach` is how many labelled spans that feature decided in the panel run: roughly how far
one answer from him travels.

    python3 scripts/build_contrast_pairs.py      # writes results/consensus/contrast_pairs.json
"""
import json
import logging
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))
sys.path.insert(0, str(PROJECT_ROOT))
import judge_labelled_spans as j  # noqa: E402

log = logging.getLogger('contrast-pairs')
PANEL = PROJECT_ROOT / 'results/consensus/panel'
OUT = PROJECT_ROOT / 'results/consensus/contrast_pairs.json'

QUESTIONS = [
    {'slug': 'jeff:alluded-incident', 'feature': 'alluded_only',
     'question': 'An incident told in a line or two inside a legal argument, as evidence for one side: is it a story?',
     'his_words': None,
     'ours': 'Our draft line (not yours) says an incident only alluded to is not a story. Your 2005 lists keep such incidents, so we think our line is wrong.',
     'examples': [
         ('list:kiddushin_085', 'The Rabbis worry about temptation even in mourning, "like that incident": a widow at her husband\'s grave sleeps with the guard of an executed man\'s body, and when that body is stolen she has her husband dug up to replace it.'),
         ('list:yevamot_072', 'Beit Hillel cite the wife of Pishon the camel driver, who refused him in his absence; Beit Shammai answer that he cheated her, so the Sages cheated him.'),
     ]},
    {'slug': 'jeff:speech-conflict-line', 'feature': 'conflict',
     'question': 'In a scholarly exchange, when does a sharp remark make it conflict (borderline under R-C2) rather than just discussion (not a story)?',
     'his_words': 'R-C2 (2026-09-02): speech alone is borderline when there is conflict, and not a story when there is not.',
     'ours': 'Both are on your 2005 lists. The two AI judges split on exactly this point: sharp words, but is it conflict?',
     'examples': [
         ('list:ketubot_015', 'Ameimar praises a ruling. Rav Ashi: "Because your mother\'s father praised it, you praise it too? Rava already refuted it."'),
         ('list:ketubot_033', 'Ravin bar Ḥanina repeats a ruling in R. Elazar\'s name; Rav Ḥisda answers: "Had you not said it in the name of a great man, I would have called it an injustice."'),
     ]},
    {'slug': 'jeff:report-vs-incident', 'feature': 'response_or_consequence',
     'question': 'A case brought to a rabbi who rules: when is it a story (your July stolen-cow case), and when is it "a legal problem and answer"?',
     'his_words': 'You accepted Toviya (Ketubot 85b: a man leaves his property "to Toviya", Toviya comes, R. Yoḥanan rules). You rejected Gittin 80b (a question about a get sent by letter to Rabba, and his reply) as "a legal discussion at a distance", and Gittin 88a as "a legal problem and answer".',
     'ours': 'Our proposal: something happens to someone and a person responds = story; a question asked and answered = not. Both passages below are ones you marked "not a story" in February, before your July rule. Under our proposal both would now be stories.',
     'examples': [
         ('review:Ketubot 50b_4-5', 'Orphans\' property is held by R. Banai; the orphan daughters come before Shmuel, who tells him to support them from it. (The Gemara then analyses the ruling.)'),
         ('review:Ketubot 50a_10-10', 'R. Yitzḥak bar Yosef finds R. Abbahu in the assembly at Usha, asks who taught the Usha ordinance, and learns it from him forty times until it is "as if in his pocket".'),
     ]},
    {'slug': 'jeff:custom-without-event', 'feature': 'event_after_custom',
     'question': 'A rabbi\'s habit, with no single "one day…" event: is it a story?',
     'his_words': 'R-C3 (2026-09-01, Beitar): a habit can frame a story when a one-time event follows.',
     'ours': 'Our note (not yours) says a habit with no one-time event stays a habit, not a story. Your 2005 lists keep both passages below.',
     'examples': [
         ('list:ketubot_050', 'Two pious men: one fed the waiter before the meal, the other after it. Elijah spoke with the first and not with the second.'),
         ('list:ketubot_076', 'R. Abba would tie coins in his scarf and toss it over his shoulder to the poor, watching from the corner of his eye for swindlers.'),
     ]},
]


def sefaria(cells):
    """Sefaria numbers segments from 1; ours (Sefaria's API order) from 0."""
    a, b = cells[0], cells[-1]
    first = f"{a[0].replace(' ', '.')}.{a[1] + 1}"
    if a[0] == b[0]:
        return f'https://www.sefaria.org/{first}{"-" + str(b[1] + 1) if b[1] != a[1] else ""}?lang=bi'
    return f"https://www.sefaria.org/{first}-{b[0].split()[-1]}.{b[1] + 1}?lang=bi"


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s [contrast-pairs] %(message)s',
                        handlers=[logging.FileHandler(PROJECT_ROOT / 'project.log'), logging.StreamHandler(sys.stdout)])
    labels = {u['id']: u for u in json.loads((j.OUT_DIR / 'labels.json').read_text())['units']}
    panel = {m: {r['id']: r['answers'][m] for r in json.loads((PANEL / f'{m}.json').read_text())['rows']}
             for m in ('gemini', 'claude')}
    report = json.loads((PANEL / 'report.json').read_text())
    texts = {}
    out = []
    for q in QUESTIONS:
        reach = report['splits_deciding_feature'].get(q['feature'], 0)
        rejected = sum(report['attribution'][m]['his_yes_called_not'].get(k, 0)
                       for m in ('gemini', 'claude') for k in report['attribution'][m]['his_yes_called_not']
                       if k.split(' ')[0] == q['feature'])
        exs = []
        for uid, summary in q['examples']:
            u = labels[uid]                                    # KeyError = a bad choice, on purpose
            deciding = {m: panel[m][uid]['judge'] for m in panel}
            # report-vs-incident is checked differently: its examples are his `no`s that the panel
            # called `story`, so NO row fired -- every feature read as a story (finding §3).
            if q['slug'] == 'jeff:report-vs-incident':
                if any(panel[m][uid]['verdict'] != 'story' for m in panel):
                    raise ValueError(f'{uid}: expected both arms to read it as a story')
            elif q['feature'] not in deciding.values():
                raise ValueError(f'{uid}: panel decided on {deciding}, not {q["feature"]}')
            t = u['tractate']
            texts.setdefault(t, j.Text(t))
            cells = [tuple(c) for c in u['cells']]
            exs.append({'id': uid, 'refs': f'{cells[0][0]}:{cells[0][1] + 1}' + (f'–{cells[-1][1] + 1}' if len(cells) > 1 else ''),
                        'his_label': u['label'], 'summary': summary, 'sefaria': sefaria(cells),
                        'panel_deciding_feature': deciding,
                        'english': ' '.join(re.sub('<[^>]+>', '', texts[t].seg[c].get('english', '')) for c in cells),
                        'hebrew': ' '.join(texts[t].seg[c].get('hebrew', '') for c in cells)})
        out.append({**{k: q[k] for k in ('slug', 'feature', 'question', 'his_words', 'ours')},
                    'reach_splits': reach, 'reach_his_yes_rejected': rejected, 'examples': exs})
        log.info('%s: %d examples, reach %d splits / %d rejections', q['slug'], len(exs), reach, rejected)
    OUT.write_text(json.dumps({'built_from': ['results/consensus/panel/report.json', 'results/consensus/phase1/labels.json'],
                               'questions': out}, ensure_ascii=False, indent=1) + '\n')
    log.info('wrote %s', OUT)


if __name__ == '__main__':
    main()
