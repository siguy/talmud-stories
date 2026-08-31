#!/usr/bin/env python3
"""Add the 5 blind-expert-list Ketubot stories that were absent from the golden.

Brief: work/done/2026-08-30-ketubot-golden-additions.md   Capability: 2 (Detection / ground truth).

Five stories on Jeff Rubenstein's detector-blind 2005 Ketubot list
(`jeff comms/b.ketubot (1).doc`, written 2005-02-02, twenty years before this
detector existed) are a DOUBLE miss: the detector never proposed them AND they
were never in our labels. That made them invisible to every metric we had --
`scripts/evaluate_golden.py` cannot score a false negative for a story that is
not in the golden. They surfaced only because Jeff's list is blind.

Adding them makes the golden honest and the recorded recall DROP. That is the
point of the change, not a regression (lessons/ Lesson 13).

Every added story carries explicit provenance -- `source: "jeff_2005_list"`,
`blind: true`, `never_detected: true` -- so no future reader can mistake these
for stories the pipeline found, or for boundaries Jeff confirmed. He asserted
that each IS a story; he never reviewed our segment ranges for them.

Segment ranges reuse the alignment in
`scripts/measure_recall_vs_expert_list.py` (Hebrew character 4-gram coverage
against Sefaria segments). That script's locator returns a deliberately coarse
window of up to 14 segments because it maximises coverage; each window here was
tightened to the minimal contiguous segment range that preserves the coverage.

Idempotent: re-running detects the existing entries and makes no change.

Usage:
  python3 scripts/add_expert_list_stories_2026-08-30.py
"""

import json
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
CANONICAL = PROJECT_ROOT / 'results' / 'canonical' / 'ketubot_canonical.json'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [golden-additions] %(message)s',
    handlers=[logging.FileHandler(PROJECT_ROOT / 'project.log'), logging.StreamHandler(sys.stdout)])
log = logging.getLogger(__name__)

ADDED_ON = '2026-08-30'
EXPERT_DOC = 'jeff comms/b.ketubot (1).doc'
EXPERT_DOC_DATE = '2005-02-02'
DETECTOR_RUN = 'results/v10/wave4_notrim/ketubot_v10_{2-60,61-112}_notrim.json'

# Shared provenance text, written once so every entry says the same thing.
WHY_BLIND = ('Jeff wrote this list in 2005, twenty years before this detector existed, '
             'so nothing we produced could have influenced it. It is the only ground '
             'truth we hold that can measure recall.')
ALIGNMENT_METHOD = ('Hebrew character 4-gram coverage against Sefaria segments, per '
                    'scripts/measure_recall_vs_expert_list.py; the locator\'s coarse '
                    'window (up to 14 segments) tightened to the minimal contiguous '
                    'range preserving coverage.')
CLASSIFICATION_BASIS = ('Derived, not graded. Jeff placed the passage on a list whose every '
                        'entry is a story, so it is is_story=True for the harness. He did not '
                        'assign it a confidence tier; "YES" is our positive label, not his word.')
BOUNDARY_CAVEAT = ('Segment-level only, and NOT expert-confirmed. Jeff quoted the passage but '
                   'never reviewed our segment range for it. Do not feed these into the '
                   'boundary test set as expert targets.')

# ---------------------------------------------------------------------------
# The five stories. `loss_cause` was read off the detector run's own page
# records (skipped_by_triage flags and proposed spans), not inferred from prose.
# ---------------------------------------------------------------------------
DEFAULT_DETECTOR_STATUS = (
    'Never proposed by any run on disk. Searched every run file for the passage TEXT '
    '(Hebrew character 4-grams over the consonantal skeleton), not for its page '
    'reference, on 2026-08-30.')

# CORRECTION 2026-08-30. The original version of this script asserted, for all five,
# "Never proposed by any detector run through v10" -- but only checked
# results/v10/wave4_notrim/. A text search across all 53 run files found two of them
# proposed by earlier configurations and REJECTED as NOT_A_STORY. For those two the
# failure is Classification, not Detection: the same re-diagnosis commit abdc4af made
# for Ketubot 77a. The scope of a negative claim has to match the scope of the check.

STORIES = [
    {
        'page_ref': 'Ketubot 20a',
        'start_segment': 2,
        'end_segment': 3,
        'coverage': 0.965,
        'coarse_window': 'Ketubot 19b seg 7 -> Ketubot 20a seg 8 (13 segments)',
        'expert_words': 30,
        'expert_text': ('בר שטיא זבין נכסי, אתו בי תרי אמרי כשהוא שוטה זבין, ואתו בי תרי ואמרי '
                        'כשהוא חלים זבין, אמר רב אשי: אוקי תרי להדי תרי ואוקי ממונא בחזקת בר שטיא.'),
        'summary': ('Bar Shatya, who suffered periodic bouts of insanity, sold his property; one pair '
                    'of witnesses testified he sold it while insane and another that he sold it while '
                    'sane, and Rav Ashi ruled that the pairs cancel each other so the property stays '
                    'in bar Shatya\'s possession.'),
        'loss_cause': 'stage_1_triage_discarded_page',
        'loss_detail': ('Under the current pipeline, Stage 1 event triage discards both Ketubot 19b '
                        'and 20a, so the story detector never sees this page. But v5 -- which predates '
                        'Stage 1 (added in v7, commit 84c9f43) -- DID examine it and DID propose exactly '
                        'segments 2-3, then classified them NOT_A_STORY. So the passage has been both '
                        'found and rejected by this project; the current loss is triage, the earlier one '
                        'was Classification.'),
        'never_detected': False,
        'proposed_by_detector': True,
        'detector_status': ('Proposed at segments 2-3 by results/v5/pages_2-39.json and classified '
                            'NOT_A_STORY (100% Hebrew 4-gram coverage of Jeff\'s text, verified '
                            '2026-08-30). Not proposed by any run from v7 on, where Stage 1 triage '
                            'discards the page before Stage 2 sees it.'),
        'continuation_note': ('Jeff\'s quotation begins mid-segment 2 (after Rav Nahman\'s ruling) and ends '
                              'with Rav Ashi\'s ruling in the first sentence of segment 3. Segments 2-3 are '
                              'the minimal segment-level cover.'),
    },
    {
        'page_ref': 'Ketubot 53a',
        'start_segment': 11,
        'end_segment': 11,
        'coverage': 1.0,
        'coarse_window': 'Ketubot 53a seg 5 -> seg 11 (7 segments)',
        'expert_words': 39,
        'expert_text': ('יתיב רבין בר חנינא קמיה דרב חסדא, ויתיב וקאמר משמיה דרבי אלעזר: מוחלת כתובתה '
                        'לבעלה - אין לה מזונות. אמר ליה: אי לאו דקאמרת לי משמיה דגברא רבא, הוה אמינא '
                        'לך: משיב רעה תחת טובה לא תמוש רעה מביתו.'),
        'summary': ('Ravin bar Hanina sat before Rav Hisda and reported in Rabbi Elazar\'s name that a '
                    'woman who forgoes her marriage contract loses her sustenance; Rav Hisda replied that '
                    'had it not come to him in a great man\'s name he would have called it rewarding evil '
                    'for good.'),
        'loss_cause': 'examined_but_never_proposed',
        'loss_detail': ('In the current pipeline the page survives triage and is examined; Stage 2 '
                        'proposes one span on it (segments 12-12, which is in the golden) and nothing at '
                        'segment 11. But the v6-triage+merge ablation DID propose exactly segment 11 and '
                        'classified it NOT_A_STORY, so the passage has been found and rejected here too.'),
        'never_detected': False,
        'proposed_by_detector': True,
        'detector_status': ('Proposed at segment 11 by results/v7/ablation_v6_triage_merge.json and '
                            'classified NOT_A_STORY (100% Hebrew 4-gram coverage of Jeff\'s text, '
                            'verified 2026-08-30). That is an ablation configuration, not a production '
                            'run; no production run has proposed it.'),
        'continuation_note': 'Contained entirely within segment 11 (4-gram coverage 1.00).',
    },
    {
        'page_ref': 'Ketubot 67b',
        'start_segment': 2,
        'end_segment': 2,
        'coverage': 1.0,
        'coarse_window': 'Ketubot 67a seg 9 -> Ketubot 67b seg 2 (7 segments)',
        'expert_words': 27,
        'expert_text': ('אמרו עליו על הלל הזקן, שלקח לעני בן טובים אחד סוס לרכוב עליו ועבד לרוץ לפניו; '
                        'פעם אחת לא מצא עבד לרוץ לפניו, ורץ לפניו שלשה מילין.'),
        'summary': ('They said of Hillel the Elder that he bought a poor man of noble descent a horse to '
                    'ride and a servant to run before him, and when once no servant could be found Hillel '
                    'himself ran before him three mil.'),
        'loss_cause': 'examined_but_never_proposed',
        'loss_detail': ('The page survived triage and was examined. Stage 2 proposed seven spans on it '
                        '(3-3, 4-4, 4-6, 11-12, 14-14, 15-15, 17-17) -- none covering segment 2. The '
                        'Hillel passage sits in the tail of a segment whose head is halakhic exposition '
                        'of "sufficient for his deficiency".'),
        'continuation_note': ('Contained entirely in the tail of segment 2 (4-gram coverage 1.00). The '
                              'golden\'s existing 67b 3-3 entry is the separate Upper Galilee story in the '
                              'same charity sequence, not a continuation of this one.'),
    },
    {
        'page_ref': 'Ketubot 72b',
        'start_segment': 3,
        'end_segment': 3,
        'coverage': 1.0,
        'coarse_window': 'Ketubot 72a seg 16 -> Ketubot 72b seg 3 (7 segments)',
        'expert_words': 57,
        'expert_text': ('אמר רבה בר בר חנה: זימנא חדא הוה קאזילנא בתריה דרב עוקבא, חזיתיה לההיא ערביא '
                        'דהוה יתבה קא שדיא פילכה וטווה ורד כנגד פניה, כיון דחזיתינן פסיקתיה לפילכה '
                        'שדיתיה, אמרה לי: עולם, הב לי פלך, אמר בה רב עוקבא מילתא. מאי אמר בה? רבינא '
                        'אמר: טווה בשוק אמר בה, רבנן אמרי: מדברת עם כל אדם אמר בה.'),
        'summary': ('Rabba bar bar Hanna, walking behind Rav Ukva, saw an Arab woman spinning in the open '
                    'who tore her spindle away when she noticed them and asked him to return it; Rav Ukva '
                    'remarked on her, and the Sages dispute which form of immodesty he meant.'),
        'loss_cause': 'stage_1_triage_discarded_page',
        'loss_detail': ('Stage 1 event triage discarded both Ketubot 72a and 72b, so the story detector '
                        'never saw this page.'),
        'continuation_note': 'Contained entirely within segment 3 (4-gram coverage 1.00).',
    },
    {
        'page_ref': 'Ketubot 82b',
        'start_segment': 9,
        'end_segment': 12,
        'coverage': 0.967,
        'coarse_window': 'Ketubot 82b seg 5 -> Ketubot 83a seg 4 (14 segments)',
        'expert_words': 97,
        'expert_text': ('בראשונה היו כותבין לבתולה מאתים ולאלמנה מנה, והיו מזקינין ולא היו נושאין נשים, '
                        'עד שבא שמעון בן שטח ותיקן: כל נכסיו אחראין לכתובתה. תניא נמי הכי: בראשונה היו '
                        'כותבין לבתולה מאתים ולאלמנה מנה, והיו מזקינין ולא היו נושאין נשים, התקינו שיהיו '
                        'מניחין אותה בבית אביה; ועדיין כשהוא כועס עליה, אומר לה לכי אצל כתובתיך.'),
        'summary': ('Rav Yehuda traces the history of the marriage contract: men grew old unmarried '
                    'because the sum had to be held in cash, successive ordinances moved the money to the '
                    'father\'s house and then the father-in-law\'s, until Shimon ben Shatah instituted '
                    'that all the husband\'s property is guaranteed for it.'),
        'loss_cause': 'stage_1_triage_discarded_page',
        'loss_detail': ('Stage 1 event triage discarded both Ketubot 82b and 83a, so the story detector '
                        'never saw this page.'),
        'continuation_note': ('Jeff\'s quotation runs from Rav Yehuda\'s statement through the parallel '
                              'baraita. Segments 9-12 are the minimal segment-level cover (coverage 0.967); '
                              'the coarse locator window spilled into 83a, which the per-segment overlap '
                              'shows carries none of the passage.'),
    },
]


def build_story(spec):
    """Build one golden story record with its provenance block."""
    return {
        'start_segment': spec['start_segment'],
        'end_segment': spec['end_segment'],
        'classification': 'YES',
        'one_sentence_summary': spec['summary'],
        'continuation': {
            'continues_from_previous_page': False,
            'continues_to_next_page': False,
            'note': spec['continuation_note'],
        },
        # Flat flags so a grep or a naive reader cannot miss them.
        'source': 'jeff_2005_list',
        'blind': True,
        'never_detected': spec.get('never_detected', True),
        'provenance': {
            'source': 'jeff_2005_list',
            'blind': True,
            'never_detected': spec.get('never_detected', True),
            'added': ADDED_ON,
            'added_by': 'work/done/2026-08-30-ketubot-golden-additions.md (scripts/add_expert_list_stories_2026-08-30.py)',
            'source_document': EXPERT_DOC,
            'source_document_date': EXPERT_DOC_DATE,
            'why_blind': WHY_BLIND,
            'expert_ref': spec['page_ref'],
            'expert_text_hebrew': spec['expert_text'],
            'expert_word_count': spec['expert_words'],
            'in_golden_before_this_date': False,
            'proposed_by_detector': spec.get('proposed_by_detector', False),
            'detector_status': spec.get('detector_status', DEFAULT_DETECTOR_STATUS),
            'loss_cause': spec['loss_cause'],
            'loss_detail': spec['loss_detail'],
            'loss_diagnosis_doc': 'docs/findings/2026-08-30-recall-miss-diagnosis.md',
            'recall_match_record': 'results/recall/ketubot_jeff2005_matches.json',
            'alignment_method': ALIGNMENT_METHOD,
            'alignment_coverage': spec['coverage'],
            'alignment_coarse_window': spec['coarse_window'],
            'classification_basis': CLASSIFICATION_BASIS,
            'expert_confirmed_boundaries': False,
            'boundary_caveat': BOUNDARY_CAVEAT,
            'effect_on_metrics': (
                'Adds a false negative to scripts/evaluate_golden.py. The recorded recall '
                'falls because the ground truth got more honest, not because detection got '
                'worse (lessons/ Lesson 13).'),
        },
    }


def main():
    data = json.loads(CANONICAL.read_text())
    pages = {p['ref']: p for p in data['pages']}

    before_total = sum(len(p.get('stories', [])) for p in data['pages'])
    log.info('golden before: %d stories across %d pages', before_total, len(data['pages']))

    added, skipped = [], []
    for spec in STORIES:
        page = pages.get(spec['page_ref'])
        if page is None:
            raise SystemExit(f"FATAL: {spec['page_ref']} not present in the golden -- refusing to invent a page.")

        # Guard: the range must exist on the page.
        indices = {s['index'] for s in page.get('segments', [])}
        missing = [i for i in range(spec['start_segment'], spec['end_segment'] + 1) if i not in indices]
        if missing:
            raise SystemExit(f"FATAL: {spec['page_ref']} has no segments {missing}; alignment is wrong.")

        stories = page.setdefault('stories', [])
        if any(s['start_segment'] == spec['start_segment'] and s['end_segment'] == spec['end_segment']
               for s in stories):
            skipped.append(f"{spec['page_ref']} {spec['start_segment']}-{spec['end_segment']}")
            continue

        # Guard: refuse to overlap an existing golden entry -- that would be a
        # duplicate label, not an addition.
        clash = [s for s in stories
                 if s['start_segment'] <= spec['end_segment'] and spec['start_segment'] <= s['end_segment']]
        if clash:
            raise SystemExit(
                f"FATAL: {spec['page_ref']} {spec['start_segment']}-{spec['end_segment']} overlaps existing "
                f"golden {[(c['start_segment'], c['end_segment']) for c in clash]}; resolve by hand.")

        stories.append(build_story(spec))
        stories.sort(key=lambda s: (s['start_segment'], s['end_segment']))
        added.append(f"{spec['page_ref']} {spec['start_segment']}-{spec['end_segment']}")
        log.info('added %s (%s, coverage %.3f)', added[-1], spec['loss_cause'], spec['coverage'])

    if not added:
        log.info('nothing to do -- all 5 already present (%s)', ', '.join(skipped))
        return

    after_total = sum(len(p.get('stories', [])) for p in data['pages'])

    # Keep the derived count honest, and say where the delta came from.
    data.setdefault('corrections_summary', {})['total_stories'] = after_total
    data['corrections_summary']['expert_list_additions'] = len(added)

    data['expert_list_additions_2026_08_30'] = {
        'date': ADDED_ON,
        'brief': 'work/done/2026-08-30-ketubot-golden-additions.md',
        'capability': '2 Detection (ground truth)',
        'script': 'scripts/add_expert_list_stories_2026-08-30.py',
        'source_document': EXPERT_DOC,
        'source_document_date': EXPERT_DOC_DATE,
        'blind': True,
        'why': ('These 5 stories were a double miss: never proposed by the detector AND never in '
                'the golden, so no metric could see them. They are visible only because Jeff\'s '
                '2005 list is detector-blind. Adding them makes the recorded recall fall -- that '
                'is the ground truth becoming honest, not detection getting worse.'),
        'expected_effect': ('scripts/evaluate_golden.py gains 5 false negatives; classification '
                            'recall and composite both fall. Precision is unchanged.'),
        'boundaries_are_not_expert_confirmed': BOUNDARY_CAVEAT,
        'stories_before': before_total,
        'stories_after': after_total,
        'added': added,
        'already_present': skipped,
    }

    CANONICAL.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    log.info('golden after: %d stories (+%d)', after_total, len(added))
    log.info('wrote %s', CANONICAL)


if __name__ == '__main__':
    main()
