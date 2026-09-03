"""The exact-anchor matcher: what it must keep true.

`locate` finds an expert's story by comparing SETS of 4-grams, so a window can only grow
and never be penalised for reaching a neighbour. `locate_exact` anchors on phrases that
are unique corpus-wide and extends only over phrases that sit where the story says they
should. These tests pin the three properties that make it safe to read a recall number
off it — they use a synthetic corpus, so they run without any tractate artifact.
"""
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
_spec = importlib.util.spec_from_file_location(
    'recall', ROOT / 'scripts' / 'measure_recall_vs_expert_list.py')
recall = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(recall)

# Three segments of a story, a neighbour that shares the commonest formula in the corpus,
# and filler. Only Hebrew letters survive `normalize`, so the text must be Hebrew.
STORY = ['רבי אבא הוה צייר זוזי בסודריה ושדי ליה לאחוריה',
         'וממצי נפשיה לבי עניי ומצלי עיניה מן רמאי',
         'אמר ליה רבא לרב נחמן האי מאן דבעי למהוי חסידא']
NEIGHBOUR = 'אמר ליה רבא לרב נחמן מילתא אחריתי לגמרי בעלמא הכא'
FILLER = ['תנו רבנן ברייתא דלא שייכא הכא כלל ועיקר מידי דהוה',
          'איבעיא להו מהו למימר הכי ותיקו בעיא דלא איפשיטא כלל']


def corpus_of(segments):
    """`word_corpus`'s input shape, without touching disk: units + a page JSON on a tmp
    file is more machinery than the property needs, so build the Corpus directly."""
    tokens, owner, shingles = [], [], recall.defaultdict(list)
    for i, seg in enumerate(segments):
        ws = recall.normalize(seg).split()
        tokens += ws
        owner += [i] * len(ws)
    for i in range(len(tokens) - recall.SHINGLE + 1):
        shingles[' '.join(tokens[i:i + recall.SHINGLE])].append(i)
    return recall.Corpus(tokens, owner, shingles)


def test_locates_the_story_and_stops_at_its_own_segments():
    """The neighbour sits directly after the story and repeats its opening formula. A
    gram-set window has no way to reject it; the positional test does."""
    corpus = corpus_of(FILLER + STORY + [NEIGHBOUR] + FILLER)
    cov, lo, hi = recall.locate_exact(' '.join(STORY), corpus)
    assert (lo, hi) == (2, 4), 'located span must be the story, not the story + neighbour'
    assert cov > 0.9


def test_extends_over_a_story_whose_middle_alone_is_unique():
    """Boundary scoring reads these locations, so a story anchored only in its middle must
    still be located to its full extent — an anchor is where to look, not how far."""
    corpus = corpus_of(FILLER + STORY + FILLER)
    # The outer segments' phrases also occur elsewhere; only the middle is one of a kind.
    duplicated = corpus_of(FILLER + STORY + FILLER + [STORY[0], STORY[2]])
    cov, lo, hi = recall.locate_exact(' '.join(STORY), duplicated)
    assert (lo, hi) == (2, 4), 'extension must recover the extent the anchor does not cover'
    assert recall.locate_exact(' '.join(STORY), corpus)[1:] == (2, 4)


def test_returns_none_when_nothing_anchors_so_the_caller_can_fall_back():
    """`--matcher exact` means 'exact where it anchors', never 'exact or nothing'. A list
    whose text is not verbatim must reach the 4-gram aligner, not a silent zero."""
    corpus = corpus_of(FILLER)
    assert recall.locate_exact('טקסט שאיננו נמצא בקורפוס הזה כלל ועיקר בשום פנים', corpus) is None
    assert recall.locate_exact('שלוש מילים בלבד', corpus) is None, 'shorter than one phrase'


def test_make_locator_falls_back_per_story_and_names_what_fell_back():
    """Absence is quiet (Lesson 38): a story the exact matcher could not anchor is counted
    and named, never dropped into the fuzzy number unremarked."""
    segments = FILLER + STORY + FILLER
    units = [('X 2a', i, recall.grams(seg)) for i, seg in enumerate(segments)]
    corpus = corpus_of(segments)
    locate, fell_back = recall.make_locator('exact', units, recall.gram_index(units), corpus)
    assert locate({'id': 'a', 'ref': 'X 2a', 'text': ' '.join(STORY)})[1:] == (2, 4)
    assert not fell_back
    locate({'id': 'b', 'ref': 'X 2a', 'text': 'הא לא כתיבא הכא ולא מידי דדמי לה כלל'})
    assert list(fell_back) == ['b']


def test_coverage_is_the_same_quantity_both_matchers_report():
    """`main` calls a story unlocated below 0.6. That floor is only meaningful if the two
    matchers report the same thing — phrase-placement fractions are much lower than gram
    coverage, and reporting them here would have called a quarter of Ketubot unlocated."""
    segments = FILLER + STORY + FILLER
    units = [('X 2a', i, recall.grams(seg)) for i, seg in enumerate(segments)]
    corpus = corpus_of(segments)
    exact, _ = recall.make_locator('exact', units, recall.gram_index(units), corpus)
    fuzzy, _ = recall.make_locator('fuzzy', units, recall.gram_index(units), corpus)
    story = {'id': 'a', 'ref': 'X 2a', 'text': ' '.join(STORY)}
    # Not equal: the fuzzy window is wider, and a wider window can only cover more grams.
    # Same scale is the property — a tight, correct span must not score as unlocated.
    assert exact(story)[0] > 0.9 and fuzzy(story)[0] >= exact(story)[0]
