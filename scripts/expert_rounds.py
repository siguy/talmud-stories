"""Whose verdicts count as ground truth. One copy, shared by every reader.

A review round is somebody's judgement; only the expert's is ground truth. Two identity
fields exist in the wild — `reviewer` (the axes-era rounds) and `reviewer_name` (the
January 2026 exports). A round that DECLARES a reviewer who is not the expert is not an
expert round. A round that declares nobody is kept: every legacy round is Jeff's by
provenance, and an allow-list that missed one would repeat the January round, whose 25
verdicts a loader dropped for eight months (Lesson 38).

Why this is a module and not a line in each reader: until 2026-09-25 the board excluded
non-expert rounds by FILENAME — `"Simon" in p.name`, case-sensitive — while the ruler did
not exclude them at all. Simon's pre-screen (`..._simon_prescreen_...`, lowercase, and
`reviewer: simon` inside) slipped past both: the ruler would have folded its 8 verdicts
into every expert figure on the next regeneration, and the board listed it as "a round
Jeff gave us" that no ruler reads. Two readers, two rules, both wrong in different ways.
CLAUDE.md: test the property, never the filename.

No dependencies beyond the standard library, so `board.py` can import it on a fresh clone.
"""

EXPERT_REVIEWER = ('anonymous', 'rubenstein', 'jeff')


def declared_non_expert(data):
    """The non-expert reviewer a round declares, or None if it is (or may be) Jeff's."""
    if not isinstance(data, dict):
        return None
    who = (data.get('reviewer') or data.get('reviewer_name') or '')
    who = who.strip() if isinstance(who, str) else ''
    if not who:
        return None
    return None if any(tok in who.lower() for tok in EXPERT_REVIEWER) else who
