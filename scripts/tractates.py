#!/usr/bin/env python3
"""The one table of Bavli tractates, and where each tractate's files live (by convention).

Every script that used to hard-code tractate names reads this instead (Shas run, 2026-11-09):
the fetch, the runner, the judge, the site build, the site tests and the checker.

  slug     lower case, spaces become underscores: 'Bava Batra' -> 'bava_batra'. A one-word name
           is just lower case, so the five existing tractates' file names do not change.
  English  the name Sefaria uses (and the one in every ref: 'Bava Batra 2a').
  Hebrew   for the site.

37 tractates have Bavli Gemara (Middot and Kinnim have none; Shekalim is Yerushalmi).
`python3 scripts/tractates.py --write-site` is not needed: the site build copies the English and
Hebrew names into site/data/index.json, so the page never carries its own list.
"""
import sys
from pathlib import Path

# (English as Sefaria spells it, Hebrew) in the order of the Mishnah's orders.
TABLE = [
    ('Berakhot', 'ברכות'),
    ('Shabbat', 'שבת'), ('Eruvin', 'עירובין'), ('Pesachim', 'פסחים'), ('Rosh Hashanah', 'ראש השנה'),
    ('Yoma', 'יומא'), ('Sukkah', 'סוכה'), ('Beitzah', 'ביצה'), ('Taanit', 'תענית'),
    ('Megillah', 'מגילה'), ('Moed Katan', 'מועד קטן'), ('Chagigah', 'חגיגה'),
    ('Yevamot', 'יבמות'), ('Ketubot', 'כתובות'), ('Nedarim', 'נדרים'), ('Nazir', 'נזיר'),
    ('Sotah', 'סוטה'), ('Gittin', 'גיטין'), ('Kiddushin', 'קידושין'),
    ('Bava Kamma', 'בבא קמא'), ('Bava Metzia', 'בבא מציעא'), ('Bava Batra', 'בבא בתרא'),
    ('Sanhedrin', 'סנהדרין'), ('Makkot', 'מכות'), ('Shevuot', 'שבועות'),
    ('Avodah Zarah', 'עבודה זרה'), ('Horayot', 'הוריות'),
    ('Zevachim', 'זבחים'), ('Menachot', 'מנחות'), ('Chullin', 'חולין'), ('Bekhorot', 'בכורות'),
    ('Arakhin', 'ערכין'), ('Temurah', 'תמורה'), ('Keritot', 'כריתות'), ('Meilah', 'מעילה'),
    ('Tamid', 'תמיד'), ('Niddah', 'נדה'),
]


# Last daf of each tractate (Sefaria's index; the fetch itself reads the real range from it).
# Used ONLY to run the longest tractates first, before their text exists to count.
# Tamid's Gemara starts at 25b, so it is far shorter than its last daf says.
LAST_DAF = {
    'Berakhot': 64, 'Shabbat': 157, 'Eruvin': 105, 'Pesachim': 121, 'Rosh Hashanah': 35, 'Yoma': 88,
    'Sukkah': 56, 'Beitzah': 40, 'Taanit': 31, 'Megillah': 32, 'Moed Katan': 29, 'Chagigah': 27,
    'Yevamot': 122, 'Ketubot': 112, 'Nedarim': 91, 'Nazir': 66, 'Sotah': 49, 'Gittin': 90,
    'Kiddushin': 82, 'Bava Kamma': 119, 'Bava Metzia': 119, 'Bava Batra': 176, 'Sanhedrin': 113,
    'Makkot': 24, 'Shevuot': 49, 'Avodah Zarah': 76, 'Horayot': 14, 'Zevachim': 120, 'Menachot': 110,
    'Chullin': 142, 'Bekhorot': 61, 'Arakhin': 34, 'Temurah': 34, 'Keritot': 28, 'Meilah': 22,
    'Tamid': 33, 'Niddah': 73,
}


def slug_of(english):
    return english.strip().lower().replace(' ', '_')


SLUGS = {slug_of(e): {'english': e, 'hebrew': h} for e, h in TABLE}


def approx_pages(slug):
    """Rough page (amud) count, for ordering only."""
    if slug == 'tamid':
        return 17
    return 2 * (LAST_DAF[english(slug)] - 1)


def english(slug):
    return SLUGS[slug]['english']


def hebrew(slug):
    return SLUGS[slug]['hebrew']


def resolve(name):
    """Accept 'Bava Batra', 'bava batra' or 'bava_batra'; return the slug or raise."""
    s = slug_of(name.replace('_', ' '))
    if s not in SLUGS:
        raise KeyError(f'{name!r} is not a Bavli tractate in scripts/tractates.py')
    return s


def resolve_arg(name):
    """`resolve` for argparse: a bad name is a usage error listing the choices, not a traceback."""
    import argparse
    try:
        return resolve(name)
    except KeyError as e:
        raise argparse.ArgumentTypeError(f'{e.args[0]} (choices: {", ".join(SLUGS)})')


# Files that predate the convention. Their locations are history (committed, cited by findings
# and tests), so they are listed here rather than moved.
LEGACY = {
    'kiddushin': {'text': 'results/v7/kiddushin_pages.json', 'triage': 'results/v7/event_triage_kiddushin.json'},
    'yevamot': {'run1': 'results/v11/v14_yevamot/run1.json', 'run2': 'results/v11/v14_yevamot/run2.json'},
}
# Tractates with two v14 runs on disk before the Shas run; the baselines the gates compare to.
BASELINES = ('berakhot', 'yevamot')


class Paths:
    """Where one tractate's inputs and outputs are, under `root` (the repo, or a test's tmp dir)."""

    def __init__(self, slug, root):
        self.slug, self.root = resolve(slug), Path(root)
        leg = LEGACY.get(self.slug, {})
        self.text = self.root / leg.get('text', f'results/sefaria/{self.slug}.json')
        self.triage = self.root / leg.get('triage', f'results/triage/{self.slug}.json')
        self.consensus = self.root / f'results/consensus/{self.slug}'
        self._leg = leg

    def run(self, n):
        return self.root / self._leg.get(f'run{n}', f'results/v14/{self.slug}/run{n}.json')

    def sibling(self, slug):
        return Paths(slug, self.root)

    def others(self):
        """Every other tractate that has a run 1 on disk."""
        return [Paths(s, self.root) for s in SLUGS if s != self.slug and Paths(s, self.root).run(1).exists()]


if __name__ == '__main__':
    for s, v in SLUGS.items():
        print(f"{s:16s} {v['english']:16s} {v['hebrew']}")
    sys.exit(0)
