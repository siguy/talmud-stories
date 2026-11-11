"""Detector v15's Stage 4j rule: an accurate biblical FLAG (docs/findings/2026-11-11-v15-biblical-flag.md).

Biblical stories ship on the Septimus site, flagged, and the flag keeps them out of Jeff's catalogue (R-S1). Every
evidence string below is copied from a v14 run on disk. The IN cases are Jeff's scope edges (comms/JEFF.md
`jeff:scope-edges`) and post-biblical people a name list mistook for biblical ones: flagging one of them would
exclude a story Jeff calls in scope (L-045), so they are pinned here.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.story_detector_v15 import biblical_flag, filter_biblical_actor_stories  # noqa: E402


@pytest.mark.parametrize('evidence', [
    # the two the 2026-11-10 accuracy review found unflagged
    'Esther and the Sages',                                   # Megillah 7a:2-3, a group beside a biblical name
    'Ahab, Elijah, Hiel',                                     # Sanhedrin 113a:10-13, a minor name not on v14's list
    # group actors, biblical peoples and places
    'King David, the Sages of Israel',
    'Ahasuerus, Sages of the Jewish people',
    'The spies, the Canaanites',
    'Eliezer; the people of Sodom',
    'Ahasuerus, Vashti, the men of Media and Persia',
    'Sisera, God, Kishon River',
    # names v14 lacked
    'Saul, David, Abner, Doeg',
    'Othniel son of Kenaz, Caleb, Achsah',
    'Joab, King Solomon, Benaiah son of Jehoiada',
    'Hananiah, Mishael, Azariah, and the nations of the world',
    'Yohana and Mamre, Moses',
    'Eli, Samuel',                                            # Samuel beside Eli is the prophet
    'The prophet (Joel) and the Jewish people',               # a parenthetical names a vague part
    'Hezekiah, king of Judea',
    'Eli, Samuel, Hannah, and the people bringing the offering',
])
def test_biblical_names_flag(evidence):
    assert biblical_flag(evidence) is True


@pytest.mark.parametrize('evidence', [
    'God and the Jewish people',
    'Ministering angels, The Holy One Blessed be He',
    'The Holy One Blessed be He, and groups of ministering angels',
    'The Moon (personified), The Holy One Blessed be He',
    'The tribes of Israel',
])
def test_god_and_people_with_no_rabbi_flag(evidence):
    """v14 read "God" as a non-biblical actor and so never flagged these."""
    assert biblical_flag(evidence) is True


@pytest.mark.parametrize('evidence', [
    # jeff:scope-edges (1): Elijah appearing to a rabbi or a post-biblical person
    'Elijah the Prophet and Rabbi Yosei',
    'Rabba bar Sheila, Elijah the Prophet',
    'A certain pious man and the prophet Elijah',             # Bava Batra 7b: v14 flagged it
    'Elijah the Prophet and a starving child',                # Sanhedrin 63b, Jerusalem after the Destruction
    # (2): a biblical figure cited inside a rabbinic story
    'Rabban Gamliel, Abraham',
    'Rabbi Akiva, Moses',
    # (3): post-biblical non-rabbis
    'Titus', 'King Yannai, the Queen, Shimon ben Shataḥ', 'King Agrippa, the High Priest',
    'Herod, Hasmonean girl, Bava ben Buta', 'Queen Helene, the Elders',
    # a group actor or God beside a post-biblical actor
    'The Roman kingdom, two military officials (sardeyotot), and the Sages of Israel',
    'The Romans, the Greeks, the Jewish people',
    'God, the Roman Empire, the Persian Empire',
    'Rabba bar bar Hana, the Arab, the Sages',
    # post-biblical people who share a biblical name
    'Elisha (Man of Wings), a Roman official',                # Shabbat 49a: v14 flagged it
    'Doeg ben Yosef and his mother',                          # Yoma 38b
    'Nahum of Gam Zo, the Jewish people, the emperor',        # Sanhedrin 108b
    'Miriam of Tarmod',                                       # Nazir 47a: v14 flagged it
    'A certain man, Joshua ben Levi',
    'Elazar ben Azariah',
    'Mordekhai, a certain man (gavra charsha)',               # Menachot 64b, Second Temple
    'Powerful people in Jericho, owners of sycamore trunks',  # Pesachim 57a
    'Onias and his followers (implied by \'They\')',
    # rabbis' names alone, and nothing at all
    'Levi', 'Samuel', 'Rav and Samuel', 'The Sages', 'a certain man', '',
])
def test_in_scope_not_flagged(evidence):
    assert biblical_flag(evidence) is False


def test_filter_keeps_v14_record_shape():
    """A match is recorded exactly as v14 recorded it, so every reader of these fields keeps working."""
    story = {'classification': 'YES', 'criteria': {'identifiable_characters': {'evidence': 'Esther and the Sages'}}}
    other = {'classification': 'YES', 'criteria': {'identifiable_characters': {'evidence': 'Elijah, Rabbi Yosei'}}}
    assert filter_biblical_actor_stories([{'stories': [story, other]}]) == 1
    assert story['classification'] == 'NOT_A_STORY' and story['classification_pre_biblical_filter'] == 'YES'
    assert story['filtered_as_biblical'] and story['out_of_scope'] and story['scope_reason'] == 'biblical_actors'
    assert other['classification'] == 'YES' and 'filtered_as_biblical' not in other


def test_site_flag_reads_v15_and_falls_back_without_evidence():
    sys.path.insert(0, str(ROOT / 'scripts'))
    from build_site_data import detector_biblical
    v14_flagged = {'filtered_as_biblical': True,
                   'criteria': {'identifiable_characters': {'evidence': 'A certain pious man and the prophet Elijah'}}}
    assert detector_biblical(v14_flagged) is False          # v15 overrules v14 where it has an actor list
    assert detector_biblical({'filtered_as_biblical': True}) is True    # no actor list: keep v14's record
    assert detector_biblical({}) is False
