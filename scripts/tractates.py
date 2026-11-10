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


def slug_of(english):
    return english.strip().lower().replace(' ', '_')


SLUGS = {slug_of(e): {'english': e, 'hebrew': h} for e, h in TABLE}


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
