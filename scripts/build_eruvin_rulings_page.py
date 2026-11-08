#!/usr/bin/env python3
"""Build the page that shows Jeff the 20 Eruvin passages in context, for his verdicts.

Not a detector run: each passage is one of HIS 2005 list entries (see the finding
docs/findings/2026-11-08-eruvin-v11-run.md for why these 20). This script wraps
them as a synthetic run -- one "story" per list entry, in the email's group order -- and
hands it to the shared per-axis review UI (generate_axis_review_ui.py), so the display
code is the tested one and Hebrew/English can never disagree (Lesson 25).

The classification label on each card reads FROM YOUR 2005 LIST, so nothing implies the
detector produced these. Answer = the page's required question (story / borderline / no).
"""
import json, re, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent

# email item number -> (list id, group)
ITEMS = [('eruvin_007', 1), ('eruvin_013', 1), ('eruvin_034', 1), ('eruvin_050', 1), ('eruvin_055', 1),
         ('eruvin_063', 1), ('eruvin_064', 1), ('eruvin_008', 2), ('eruvin_014', 2), ('eruvin_019', 2),
         ('eruvin_021', 2), ('eruvin_035', 2), ('eruvin_052', 2), ('eruvin_054', 2), ('eruvin_073', 2),
         ('eruvin_026', 3), ('eruvin_037', 4), ('eruvin_040', 4), ('eruvin_041', 4), ('eruvin_042', 4)]
GROUPS = {1: 'Group 1: one event, then a challenge, a ruling or a discussion',
          2: 'Group 2: scholars talking or sitting, with little or no event',
          3: 'Group 3: one act cited as precedent',
          4: 'Group 4: how a person speaks (wise or precise speech)'}

# One plain line per passage, checked against the Sefaria text (2026-11-08).
DESCRIPTIONS = {
    1: 'Eruvin 13b, the elders of Beit Shammai and Beit Hillel visit R. Yohanan ben HaHoranit and find him sitting in the sukkah with his table inside the house. Beit Shammai ask "is that proof?" and Beit Hillel say he has never kept the sukkah mitzvah.',
    2: 'Eruvin 24a, Mar Yehuda comes to the house of Rav Huna bar Yehuda, sees people carrying among trees not planted in rows, and asks whether he does not hold like Avimi; Rav Huna replies that he holds like Rav Nahman.',
    3: 'Eruvin 47a, R. Eliezer does not go into the study house, meets R. Asi standing outside and asks what was said inside; then a halakhic discussion.',
    4: "Eruvin 59b, R. Zeira made an eiruv for R. Hiyya's city and left no section out; Abaye asks why, and an answer follows.",
    5: 'Eruvin 63a, Ravina visits Mehoza and his host shows him a slaughtering knife; Ravina tells him to take it to Rava, and the host objects that Rava allows a scholar to check it himself.',
    6: "Eruvin 67a, a child's hot water spilled; Rabba proposes a solution, Abaye objects, Rabba changes it.",
    7: "Eruvin 68a, a child's hot water spilled; Rava proposes asking the mother, Mesharshiya objects.",
    8: 'Eruvin 14b, Rav says the halakha is not like R. Yose, then denies saying it; Rava swears he heard it.',
    9: 'Eruvin 24a, Hezekiah asks about a hole that is plugged and reopened, followed by a scholarly exchange.',
    10: 'Eruvin 32b, R. Hiyya bar Abba, R. Asi and Rava bar Natan sit and work through the status of a tree, and Rav Nahman joins in.',
    11: 'Eruvin 37b, Rava questions Rav Nahman about a baraita and Rav Nahman is silent.',
    12: 'Eruvin 51a, Rabba and Rav Yosef travel together and agree on a place to stay for Shabbat; the frame leads into a legal discussion.',
    13: 'Eruvin 60a, R. Yitzhak gives a ruling; Abaye asks Rav Yosef whether it is tradition or reasoning.',
    14: "Eruvin 63a, Ravina and Rav Ashi discuss whether Rav Hamnuna issued rulings in his teacher's lifetime, which Ravina uses to justify his own practice.",
    15: 'Eruvin 103a, Abaye is teaching and Rav Safra objects from a mishna.',
    16: 'Eruvin 41a, R. Yehuda recalls that the Ninth of Av once fell on Shabbat eve while they sat before R. Akiva, and R. Akiva swallowed a lightly cooked egg without salt to show the students they need not complete the fast.',
    17: 'Eruvin 53b, a man of Judea says "I have a cloak to sell" and is asked what colour; shows precise speech.',
    18: 'Eruvin 53b, the maidservant in Rabbi\'s house speaks in riddles and says "the ladle is knocking against the jug".',
    19: 'Eruvin 53b, R. Yose bar Asyan, when speaking in the language of the sages, says "prepare for me an ox in judgment on a poor mountain".',
    20: 'Eruvin 53b, R. Abbahu, when speaking in the language of the sages, says "make the coals the colour of an etrog..." and the rabbis ask him where R. Ilai is hidden.',
}
desc = DESCRIPTIONS
assert sorted(desc) == list(range(1, 21))

matches = json.loads((ROOT / 'results/recall/eruvin_jeff2005_matches.json').read_text())
rows = matches if isinstance(matches, list) else next(v for v in matches.values() if isinstance(v, list))
loc = {r['id']: r for r in rows}
pages = {p['ref']: p for p in json.loads((ROOT / 'results/sefaria/eruvin.json').read_text())['pages']}

# His own recorded words per shape (docs/STORY_RULES.md), shown on the first card of each group.
RULINGS = {
    1: ('Your earlier rulings on this shape: Ketubot 50b, a case before a rabbi and a ruling: "there is not really '
        'another action or change that is narrated" (not a story). On the same shape you added: "these cases and '
        'similar ones are not a story rather than that they are borderline." Ketubot 65a, where the rabbi '
        '\'apportions\' wine: "it is a little more than a ruling. It is a courtroom drama... more change" '
        '(borderline). The cow case: "A man stole another man\'s cow and sold it. Rava ruled... you may have a story."'),
    2: ('Your earlier rulings on this shape: speech with conflict and implied change "would always be borderline." '
        'Ketubot 53a: "No conflict or change... standard rabbinic dialogue and not a story." Ketubot 21b: praise or '
        'rebuke between scholars "is not that exceptional in Talmudic dialogue." Yevamot 17a: "a description of '
        'rabbi\'s sitting in a certain arrangement. But then they just have a discussion."'),
    3: ('Your earlier rulings on this shape: Yevamot 15a: "There is no real story here, just a report of what R. Akiva '
        'did." Yevamot 106b: "just a description of what Mar Zutra did... the narrative ends there."'),
    4: ('Your earlier rulings on this shape: Gittin 57a: "After the custom you have the one time event" (a story). '
        'Ketubot 61a: "at least two actions and change." Yevamot 107b: "one thing Pishon\'s wife did... without '
        'change or causality" (not a story).'),
}
FIRST_OF_GROUP = {}
for _n, (_lid, _g) in enumerate(ITEMS, 1):
    FIRST_OF_GROUP.setdefault(_g, _n)


def plain(text):
    """Strip the ref and any editorial aside: the page must not tell him what we think."""
    t = re.sub(r'^Eruvin [0-9]+[ab], ', '', text)
    t = re.sub(r'\s*\([^)]*\)\s*$', '', t)
    return t[0].upper() + t[1:]


out_pages = []
for n, (lid, grp) in enumerate(ITEMS, 1):
    r = loc[lid]
    segs = [i for ref, i in r['located'] if ref == r['located'][0][0]]
    assert len({ref for ref, _ in r['located']}) == 1, f'{lid} spans pages'
    ref = r['located'][0][0]
    out_pages.append({'ref': ref, 'segments': pages[ref]['segments'], 'stories': [{
        'start_segment': min(segs), 'end_segment': max(segs), 'classification': 'FROM YOUR 2005 LIST',
        'one_sentence_summary': f'{GROUPS[grp]}. Item {n} of 20. {plain(desc[n])} '
                                f'[{RULINGS[grp] if FIRST_OF_GROUP[grp] == n else "Rulings for this group: see the first item of the group."}]',
    }]})
run = ROOT / 'results/rulings_pages/eruvin_2005_rulings_run.json'
run.parent.mkdir(exist_ok=True)
run.write_text(json.dumps({'tractate': 'Eruvin', 'version': 'eruvin-2005-list', 'pages': out_pages},
                          ensure_ascii=False, indent=1))
note = ("These are 20 passages from your 2005 Eruvin list, shown in context. Your later rulings may "
        "disqualify some. For each, the one question that matters is the first one: story, borderline, "
        "or no. Borderline keeps it on your list; only no removes it from our count. Everything else is optional; if "
        "you can, start your note with a tag: SPEECH ONLY, ONE EVENT, HABIT, SCHOLARLY, or OTHER. Passages are "
        "grouped by shape, and the first card of each group quotes your earlier rulings on it.")
sys.exit(subprocess.call([sys.executable, 'validation/generators/generate_axis_review_ui.py', '--run', str(run),
        '--title', 'Eruvin: 20 passages from your 2005 list', '--out', 'eruvin_2005_rulings.html',
        '--note', note], cwd=ROOT))
