"""The rule register as a decision table: nine feature answers -> one verdict.

work/2026-10-02-rule-panel-lenses.md. The model never decides "is it a story"; it answers
nine narrow questions (src/prompts/judges/panel_v1.md) and this table decides. Every row
cites the STORY_RULES rule it implements. Rows marked `ours=True` encode OUR proposals,
not his words -- a disagreement on one of those is a question for Jeff, not a model error.

The rows run in order; the first that fires decides, and its judge is the one that
"decided" the verdict. `blocking()` lists every row that would turn the passage away on
its own -- what one answer from him would have to change.
"""
from dataclasses import dataclass

FEATURES = ('actual', 'event_beyond_speech', 'conflict', 'response_or_consequence', 'custom',
            'event_after_custom', 'alluded_only', 'commentary', 'biblical_actors')
ANSWERS = ('yes', 'no', 'unsure', 'n_a')


@dataclass(frozen=True)
class Row:
    judge: str          # the feature that decides here
    when: str           # the answer that fires the row
    verdict: str
    rule: str
    ours: bool = False
    needs: tuple = ()   # (feature, answer) that must also hold for the row to apply


# Order matters only for attribution; every path below is a rule he stated or we proposed.
ROWS = (
    Row('commentary', 'yes', 'not', 'R-B4'),
    Row('actual', 'no', 'not', 'R-C0'),
    Row('alluded_only', 'yes', 'not', 'R-C5', ours=True),        # "an incident only alluded to"
    Row('event_after_custom', 'no', 'not', 'R-C3', ours=True,    # "a custom stays a custom"
        needs=(('custom', 'yes'),)),
    Row('conflict', 'yes', 'borderline', 'R-C2', needs=(('event_beyond_speech', 'no'),)),
    Row('conflict', 'no', 'not', 'R-C2', needs=(('event_beyond_speech', 'no'),)),
    Row('response_or_consequence', 'no', 'not', 'R-C5'),
)


def _applies(row, f):
    return all(f.get(k) == v for k, v in row.needs)


def decide(features):
    """features: {name: answer}. Returns (verdict, deciding_judge, rule, ours).

    `unsure` on a feature the path needs makes the verdict `unsure`, attributed to that
    feature -- never silently read as yes or no (Lesson 21's shape).
    """
    f = dict(features)
    for row in ROWS:
        # a row whose precondition is itself unsure cannot be passed over
        for k, v in row.needs:
            if f.get(k) == 'unsure':
                return 'unsure', k, row.rule, row.ours
        if not _applies(row, f):
            continue
        a = f.get(row.judge)
        if a == 'unsure':
            return 'unsure', row.judge, row.rule, row.ours
        if a == row.when:
            return row.verdict, row.judge, row.rule, row.ours
    # A story -- unless its actors are biblical (R-S1: a story, but outside the collection).
    if f.get('biblical_actors') == 'yes':
        return 'out_of_scope', 'biblical_actors', 'R-S1', False
    if f.get('biblical_actors') == 'unsure':
        return 'unsure', 'biblical_actors', 'R-S1', False
    return 'story', None, 'R-C0', False


def blocking(features):
    """Every row that, on its own, turns the passage away from `story`."""
    f = dict(features)
    return [(r.judge, r.rule, r.ours) for r in ROWS
            if r.verdict != 'story' and _applies(r, f) and f.get(r.judge) == r.when]
