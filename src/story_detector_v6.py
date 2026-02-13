#!/usr/bin/env python3
"""
Talmud Story Detection v6: Comprehensive Revision from Jeff Rubenstein's v5.1 Validation

Key changes from v5.1 (based on 128 expert-reviewed passages):

CRITERIA CHANGES:
- RENAMED: named_characters → identifiable_characters (anonymous "a certain man" counts FULLY)
- NEW GUIDANCE: What constitutes a "narrative event" vs legal/intellectual activity
  - Thinking/deliberation ≠ event
  - Legal difficulty/resolution ≠ event
  - Verbal statements/objections ≠ events
  - Ordering someone to act ≠ event
  - Traveling to participate in legal debate ≠ narrative event
  - Legal debate between academies ≠ story (place names ≠ characters)

CLASSIFICATION CHANGES:
- BORDERLINE CALIBRATION: One real event + discussion = LOW_CONFIDENCE (not NOT_A_STORY)
- REMOVED: biblical_narrative disqualifier (Jeff validated biblical stories as correct)
- NEW DISQUALIFIER: legal_deliberation (thinking about acting, legal difficulty)

BOUNDARY CHANGES:
- Story starts at first narrative event, NOT preceding legal ruling
- Story ends at final narrative action, NOT following Talmudic commentary
- Exception: Rabbi who directly references/comments on story events IS part of story
- Talmudic questions (beginning with וְהָא) are NOT part of story

STRUCTURAL CHANGES:
- Cross-page story merging: Detect and combine stories split by page boundaries
- Within-page story merging: Guidance to not split continuous stories
- Continuation detection: Flag incomplete stories at page boundaries
- Duplicate detection: Same story quoted on multiple pages

NEW EXAMPLES: 12+ from Jeff's v5.1 validation with exact notes
"""

import requests
import json
import time
import os
import re
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

# Import Google Generative AI for Gemini support
try:
    from google import genai
    from google.genai import types
    GOOGLE_AI_AVAILABLE = True
except ImportError:
    GOOGLE_AI_AVAILABLE = False
    print("google-genai not installed. Run: pip install google-genai")


# ============================================================
# JEFF'S VALIDATED EXAMPLES - v5.1 FEEDBACK (EXPANDED)
# ============================================================

CURATED_EXAMPLES = {
    "yes_examples": [
        {
            "ref": "Ketubot 62b",
            "name": "Rav Reḥumi's Death",
            "hebrew": "אמר רב רחומי הוה שכיח קמיה דרבא במחוזא הוה רגיל דהוה אתי לביתיה כל מעלי יומא דכפורי יומא חד משכיה שמעתא נפקא דעתה דביתהו השתא אתי השתא אתי לא אתא חלש דעתה אחית דמעתא מעינה הוה יתיב באיגרא אפחית איגרא מתותיה ונח נפשיה",
            "english": "Rav Reḥumi would commonly study before Rava in Meḥoza. He was accustomed to come home every year on the eve of Yom Kippur. One day he was engrossed in the halakha. His wife was expecting him: Now he is coming, now he is coming. He did not come. She was distressed. A tear fell from her eye. He was sitting on the roof. The roof collapsed under him and he died.",
            "criteria": {
                "identifiable_characters": "Rav Reḥumi, his wife, Rava",
                "multiple_events": "studying, didn't return, wife distressed, tear fell, roof collapsed, died",
                "causal_chain": "engrossed in study → missed return → wife distressed → tear → supernatural death",
                "temporal_progression": "יומא חד (one day), sequence of events",
                "descriptive": "narrates what happened",
                "change_outcome": "alive studying → dead"
            },
            "classification": "YES",
            "jeff_notes": "Classic aggadic narrative with clear arc and tragic outcome"
        },
        {
            "ref": "Ketubot 8b",
            "name": "Comforting a Mourner",
            "hebrew": "כי הא דריש לקיש הוה ליה בן קמיה יומא חד הוה יתיב ריש לקיש קמי רבי יוחנן ועייל רבי יהודה בר נחמני ורב יצחק בר אמי",
            "english": "This is as the incident where Reish Lakish had a son who died. One day Reish Lakish was sitting before Rabbi Yoḥanan, and Yehuda bar Naḥmani and Rabbi Yitzḥak bar Ami entered to comfort him.",
            "criteria": {
                "identifiable_characters": "Reish Lakish, Rabbi Yoḥanan, Yehuda bar Naḥmani, Rabbi Yitzḥak bar Ami",
                "multiple_events": "son died, sitting before rabbi, others entered to comfort",
                "causal_chain": "death → mourning → comforting visit",
                "temporal_progression": "יומא חד (one day)",
                "descriptive": "describes what happened",
                "change_outcome": "mourning → receiving comfort"
            },
            "classification": "YES",
            "jeff_notes": "Clear narrative with multiple characters and events"
        },
        {
            "ref": "Ketubot 17a",
            "name": "Rabban Gamliel's Burial",
            "hebrew": "בראשונה היתה הוצאת המת קשה לקרוביו יותר ממיתתו עד שהיו מניחין אותו ובורחין עד שבא רבן גמליאל ונהג קלות ראש בעצמו ויצא בכלי פשתן ונהגו העם אחריו",
            "english": "Initially, funeral expenditures for the deceased were more taxing than his death, until people would abandon the deceased and flee. This continued until Rabban Gamliel came and conducted himself in self-deprecatory manner, instructing that they take him for burial in plain linen garments. And all the people conducted themselves following his example.",
            "criteria": {
                "identifiable_characters": "Rabban Gamliel",
                "multiple_events": "expensive burials → abandonment → Gamliel's example → change in practice",
                "causal_chain": "Gamliel's action caused societal change",
                "temporal_progression": "בראשונה (initially) → עד שבא (until came)",
                "descriptive": "describes historical change",
                "change_outcome": "expensive burials → simple burials"
            },
            "classification": "YES",
            "jeff_notes": "Narrative of social change with clear before/after"
        },
        {
            "ref": "Ketubot 10b",
            "name": "Woman Before Rabban Gamliel (Anonymous Characters)",
            "hebrew": "ההיא דאתאי לקמיה דרבן גמליאל אמרה ליה רבי בעלתי ולא מצא לי בתולים",
            "english": "A certain woman came before Rabban Gamliel. She said to him: My master, my husband had intercourse with me and did not find blood of virginity.",
            "criteria": {
                "identifiable_characters": "Rabban Gamliel, the woman (anonymous but specific), her husband",
                "multiple_events": "came before rabbi, made claim, testimony given, judgment rendered",
                "causal_chain": "claim → inquiry → evidence → ruling",
                "temporal_progression": "sequence of legal encounter",
                "descriptive": "describes actual case",
                "change_outcome": "dispute → resolution"
            },
            "classification": "YES",
            "jeff_notes": "Jeff validated: anonymous characters ('a certain woman') ARE valid characters. 'Stories can be about unnamed people.' The anonymous character does NOT weaken confidence."
        },
        {
            "ref": "Ketubot 10b (second case)",
            "name": "Rabban Gamliel's Investigation",
            "hebrew": "",
            "english": "After the woman and man come to Rabban Gamliel, he checks about her family. He takes them to a bathhouse and feeds them, and then checks the woman again.",
            "criteria": {
                "identifiable_characters": "Rabban Gamliel, the woman, the man (anonymous but specific)",
                "multiple_events": "come before rabbi, he checks family, takes to bathhouse, feeds them, checks again",
                "causal_chain": "claim → investigation → physical test → outcome",
                "temporal_progression": "after the woman speaks → he takes them → then checks",
                "descriptive": "describes what happened",
                "change_outcome": "uncertainty → resolution"
            },
            "classification": "YES",
            "jeff_notes": "Jeff: 'There is causality and temporal progression. The outcome is a change too.' Anonymous characters fully valid."
        }
    ],

    "high_confidence_examples": [
        {
            "ref": "Ketubot 62b (second story)",
            "name": "Rabbi Akiva and Wife",
            "hebrew": "רבי עקיבא רעיא דבן כלבא שבוע הוה חזיתיה ברתיה דהוה צניע ומעלי",
            "english": "Rabbi Akiva was a shepherd of ben Kalba Savua. His daughter saw that he was modest and noble.",
            "criteria": {
                "identifiable_characters": "Rabbi Akiva, daughter of Kalba Savua",
                "multiple_events": "shepherd → noticed → married → studied",
                "causal_chain": "present but spans many segments",
                "temporal_progression": "implied through life stages",
                "descriptive": "describes what happened",
                "change_outcome": "shepherd → great sage"
            },
            "weakeners": ["continues across multiple pages", "embedded in larger discussion"],
            "classification": "HIGH_CONFIDENCE",
            "jeff_notes": "borderline - story continues beyond visible text"
        },
        {
            "ref": "Ketubot 23a",
            "name": "Rabbi Ami's Case",
            "hebrew": "אתא לקמיה דרבי אמי לא קבליה אתא לקמיה דרבי יצחק נפחא קבליה",
            "english": "He came before Rabbi Ami; he did not accept him. He came before Rabbi Yitzḥak Nappaḥa; he accepted him.",
            "criteria": {
                "identifiable_characters": "Rabbi Ami, Rabbi Yitzḥak Nappaḥa",
                "multiple_events": "approached first rabbi, rejected, approached second, accepted",
                "causal_chain": "rejection → sought alternative → acceptance",
                "temporal_progression": "sequence implied",
                "descriptive": "describes what happened",
                "change_outcome": "rejected → accepted"
            },
            "weakeners": ["short (2 segments)", "embedded in legal discussion"],
            "classification": "HIGH_CONFIDENCE",
            "jeff_notes": "borderline - legal discussion but named characters, events with change"
        }
    ],

    "low_confidence_borderline_examples": [
        {
            "ref": "Ketubot 49b_6-6",
            "name": "Forcing Charity (One Event + Discussion)",
            "english": "A rabbi forced a man to give charity. Followed by legal discussion.",
            "criteria_met": 3,
            "why_borderline": "Basically one event, though two verbs are used. He forced a man to give charity. One real event followed by legal discussion.",
            "classification": "LOW_CONFIDENCE",
            "jeff_notes": "Jeff: 'This is a borderline story. It is basically one event, though two verbs are used.'"
        },
        {
            "ref": "Ketubot 50b_9-10",
            "name": "One Event Then Discussion",
            "english": "One real event occurred, followed by rabbinic discussion about it.",
            "criteria_met": 3,
            "why_borderline": "Just one real event and then discussion. Not enough for a full story, but something did happen.",
            "classification": "LOW_CONFIDENCE",
            "jeff_notes": "Jeff: 'should be marked a borderline story, since it is just one real event and then discussion'"
        },
        {
            "ref": "Ketubot 51a_1-2",
            "name": "Single Event With Legal Discussion",
            "english": "One event, then a legal discussion about it.",
            "criteria_met": 3,
            "why_borderline": "Really just one event, then a legal discussion. Borderline because something happened.",
            "classification": "LOW_CONFIDENCE",
            "jeff_notes": "Jeff: 'should be marked a borderline story, since there is really just one event, then a legal discussion.'"
        },
        {
            "ref": "Ketubot 54a_13-14",
            "name": "One Event Then Ruling",
            "english": "Basically one event and then a legal ruling and discussion.",
            "criteria_met": 3,
            "why_borderline": "One event triggers legal discussion. Borderline.",
            "classification": "LOW_CONFIDENCE",
            "jeff_notes": "Jeff: 'should be marked a borderline story, since there is basically one event and then a legal ruling and discussion'"
        },
        {
            "ref": "Ketubot 10a_9-10",
            "name": "Mainly Speech Acts",
            "english": "Anonymous character involved, but mainly speech acts rather than events.",
            "criteria_met": 3,
            "why_borderline": "Mainly speech acts, not really events. But something did happen.",
            "classification": "LOW_CONFIDENCE",
            "jeff_notes": "Jeff: 'it is perfectly fine to have an anonymous character. This is a borderline story since it is mainly speech acts, not really events.'"
        }
    ],

    "not_a_story_examples": [
        {
            "ref": "Ketubot 2a",
            "name": "Virgin Marriage Day",
            "hebrew": "בתולה נשאת ליום הרביעי ואלמנה ליום החמישי",
            "english": "A virgin is married on Wednesday and a widow on Thursday.",
            "disqualifier": "prescriptive_legal_rule",
            "why_not": "This is a RULE about what SHOULD happen, not what DID happen. Prescriptive, not descriptive.",
            "classification": "NOT_A_STORY"
        },
        {
            "ref": "Ketubot 3a",
            "name": "Hypothetical Divorce",
            "hebrew": "האומר לשלוחו צא וקדש לי אשה סתם",
            "english": "If a man said to his agents: Go and betroth a woman for me, and he did not specify which woman...",
            "disqualifier": "hypothetical_case",
            "why_not": "Hypothetical legal scenario ('If X, then Y'). No actual event occurred.",
            "classification": "NOT_A_STORY"
        },
        {
            "ref": "Ketubot 5a",
            "name": "Habitual Practice",
            "hebrew": "רב ספרא הוה רגיל",
            "english": "Rav Safra was accustomed to...",
            "disqualifier": "habitual_action",
            "why_not": "היה רגיל (was accustomed) signals habitual action, not one-time event.",
            "classification": "NOT_A_STORY"
        },
        {
            "ref": "Ketubot 7b",
            "name": "Blessing Recitation Report",
            "hebrew": "רב אסי איקלע לבי רב אשי ובריך שית",
            "english": "Rav Asi happened to come to the house of Rav Ashi and recited six blessings.",
            "disqualifier": "report_without_causality",
            "why_not": "Just a report of events. No causal chain, no change, no story arc.",
            "classification": "NOT_A_STORY",
            "jeff_notes": "Just the recitation of blessings. No story."
        },
        {
            "ref": "Ketubot 17a",
            "name": "Rabbi Stating Legal Opinion",
            "english": "Rabbi Shmuel bar Naḥmani quotes Rabbi Yonatan as saying it is permitted to look at the face of a bride.",
            "disqualifier": "rabbi_legal_opinion",
            "why_not": "Rabbi name appears to ATTRIBUTE legal ruling, not as character in narrative.",
            "classification": "NOT_A_STORY",
            "jeff_notes": "Rabbi stating legal opinion, not character in story"
        },
        {
            "ref": "Ketubot 40b",
            "name": "Rabbi Traveling to Debate (NOT an event)",
            "english": "One rabbi went to the place of another rabbi to recite his tradition.",
            "disqualifier": "legal_debate_setting",
            "why_not": "The events here are rabbis making legal arguments. A rabbi traveling to another rabbi to recite a legal tradition is NOT a narrative event - it is the logistics of legal discourse.",
            "classification": "NOT_A_STORY",
            "jeff_notes": "Jeff: 'True, one rabbi went to the place of another rabbi to recite his tradition. But that is not really an event that makes for a story.'"
        },
        {
            "ref": "Ketubot 42b",
            "name": "Legal Difficulty Resolution (NOT events)",
            "english": "A rabbi experienced difficulty resolving a legal issue.",
            "disqualifier": "legal_deliberation",
            "why_not": "Experiencing difficulty and 'resolving' a difficult legal issue are NOT events - they are parts of a legal discussion.",
            "classification": "NOT_A_STORY",
            "jeff_notes": "Jeff: 'The main actions, experiencing difficulty and resolving a difficult legal issue, are not events, but just parts of a legal discussion.'"
        },
        {
            "ref": "Ketubot 52a",
            "name": "Thinking About Acting (NOT an event)",
            "english": "Levi thought about acting according to a certain opinion. But Rav told him otherwise.",
            "disqualifier": "legal_deliberation",
            "why_not": "Thinking about acting is NOT an event. Mental deliberation or consideration of a legal opinion does not constitute a narrative event.",
            "classification": "NOT_A_STORY",
            "jeff_notes": "Jeff: 'There are no real events. Levi thought about acting according to a certain opinion. But Rav told him otherwise. No events.'"
        },
        {
            "ref": "Ketubot 55a",
            "name": "Legal Debate Between Academies",
            "english": "A legal debate between Pumbedita and Matta Mehasia.",
            "disqualifier": "legal_debate_setting",
            "why_not": "A legal debate between two academies (cities) is NOT a story. Place names are NOT characters.",
            "classification": "NOT_A_STORY",
            "jeff_notes": "Jeff: 'Not a story at all. This is a legal debate between Pumbedita and Matta Mehasia.'"
        },
        {
            "ref": "Ketubot 56a",
            "name": "Debate Setting (NOT a story)",
            "english": "One sage sitting before another sage, having a legal debate.",
            "disqualifier": "legal_debate_setting",
            "why_not": "The physical setting of a legal debate does NOT make it a story. A sage sitting before another sage and debating is legal discourse, not narrative.",
            "classification": "NOT_A_STORY",
            "jeff_notes": "Jeff: 'There is a setting for the debate of one sage sitting before another. But it is just a debate.'"
        },
        {
            "ref": "Ketubot 51b",
            "name": "Theoretical Discussion",
            "english": "Shmuel discusses a legal case theoretically.",
            "disqualifier": "hypothetical_case",
            "why_not": "Shmuel is not talking about an event that happened, but a theoretical legal case.",
            "classification": "NOT_A_STORY",
            "jeff_notes": "Jeff: 'This is just a theoretical discussion. Shmuel is not talking about an event that happened, but a legal case.'"
        }
    ]
}


# ============================================================
# DISQUALIFIERS AND WEAKENERS
# ============================================================

DISQUALIFIERS = {
    "mishna_section": {
        "hebrew_markers": ["מתני׳", "מתניתין"],
        "english_markers": ["MISHNA", "mishna:"],
        "reason": "MISHNA sections are legal codifications, not narratives"
    },
    "hypothetical_case": {
        "hebrew_markers": ["אם היה", "אילו"],
        "english_markers": ["If he were", "If she were", "What if", "were to"],
        "reason": "Hypothetical legal scenarios are not actual events"
    },
    "habitual_action": {
        "hebrew_markers": ["היה רגיל", "רגיל ד", "הוה רגיל"],
        "english_markers": ["was accustomed", "would always", "used to regularly"],
        "reason": "Habitual actions are not one-time events"
    },
    "pure_legal_ruling": {
        "hebrew_markers": ["הלכה כ", "הלכתא"],
        "english_markers": ["The halakha is", "the law is that"],
        "reason": "Legal rulings without narrative are not stories"
    },
    "rabbi_legal_opinion": {
        "english_markers": [
            "said that it is permitted",
            "said that it is prohibited",
            "said that one who",
            "said that the halakha",
            "quotes",
            "as saying it is",
            "discusses a case of",
            "discusses the number",
            "The Gemara questions"
        ],
        "reason": "Rabbi name appears to ATTRIBUTE legal ruling, not as character in narrative"
    },
    "legal_deliberation": {
        "english_markers": [
            "thought about acting",
            "considered ruling",
            "experienced difficulty",
            "had difficulty resolving"
        ],
        "reason": "Mental deliberation, legal difficulty, or considering an opinion are NOT narrative events"
    },
    "legal_debate_setting": {
        "english_markers": [
            "debate between",
            "they disagree about",
            "sitting before him and they discussed"
        ],
        "reason": "Physical setting of legal debate does not make it a story. Place names are not characters."
    }
}

WEAKENERS = {
    "embedded_in_legal": "Story is embedded within legal discussion, boundaries unclear",
    "short_narrative": "Very brief (2 segments or less)",
    "implied_causality": "Causal chain implied but not explicitly stated",
    "ambiguous_outcome": "Change/outcome implied but not stated",
    "incomplete_view": "Story continues from/to another page",
    "single_source": "Only one rabbi mentioned acting alone",
    "simple_report": "Simple report of action without causality or change (e.g., 'X came and did Y')",
    "minimal_causality": "Causality present but MINIMAL - barely meets threshold",
    "minimal_change": "Change present but MINIMAL - barely transformative",
    "mainly_speech_acts": "Narrative exists but is mainly dialogue/speech rather than physical events"
}

# NOTE: "partial_naming" REMOVED as weakener per Jeff's feedback.
# Anonymous characters ("a certain man") are FULLY valid characters.

# Talmud commentary boundary markers (exclude from stories)
TALMUD_COMMENTARY_MARKERS = {
    "hebrew": [
        "וְלֵית הִלְכְתָא",  # and the law is not...
        "טַעְמָא דְּ",  # the reason is...
        "מַאי טַעְמָא",  # what is the reason...
        "הָא גּוּפָא קַשְׁיָא",  # this itself is difficult
        "וְהָא",  # but isn't it... (Talmud's question after story)
    ],
    "english": [
        "And the halakha is not in accordance",
        "The reason that",
        "The Gemara explains",
        "This is not in accordance with",
        "The Gemara questions",
        "The Gemara asks",
    ]
}

# Story continuation markers (connect to previous segment)
CONTINUATION_MARKERS = {
    "hebrew": ["זִמְנָא אַחֲרִינָא", "פַּעַם אַחֶרֶת"],
    "english": ["On another occasion", "Another time", "Once again"]
}

# Legal markers that indicate text is NOT part of a story
LEGAL_BOUNDARY_MARKERS = {
    "hebrew": [
        "הלכה כ",  # the halakha is according to...
        "אמר עולא הלכה",  # Ulla said: the halakha is...
    ],
    "english": [
        "The halakha is in accordance",
        "said: The halakha is",
    ]
}


# ============================================================
# SEGMENT PROCESSING
# ============================================================

def detect_hebrew_markers(hebrew_text: str) -> Dict[str, List]:
    """Detect Hebrew narrative markers in a segment."""
    markers = {
        'story': [],
        'dialogue': [],
        'temporal': [],
        'outcome': [],
        'legal': [],
        'hypothetical': [],
        'habitual': [],
        'anonymous_character': []
    }

    h = hebrew_text

    # STORY MARKERS
    if 'מעשה' in h:
        markers['story'].append('מעשה')
    if 'כי הא ד' in h:
        markers['story'].append('כי_הא_ד')
    if 'פעם אחת' in h:
        markers['story'].append('פעם_אחת')
    if 'יומא חד' in h:
        markers['story'].append('יומא_חד')
    if 'זמנא חדא' in h:
        markers['story'].append('זמנא_חדא')

    # DIALOGUE MARKERS
    if 'אמר ליה' in h or 'א"ל' in h:
        markers['dialogue'].append('אמר_ליה')
    if 'אמר לה' in h:
        markers['dialogue'].append('אמר_לה')
    if 'אמרה ליה' in h:
        markers['dialogue'].append('אמרה_ליה')

    # TEMPORAL MARKERS
    if 'לסוף' in h or 'לבסוף' in h:
        markers['temporal'].append('לסוף')
    if 'למחר' in h:
        markers['temporal'].append('למחר')
    if 'באותה שעה' in h:
        markers['temporal'].append('באותה_שעה')
    if 'בראשונה' in h:
        markers['temporal'].append('בראשונה')

    # OUTCOME MARKERS
    if 'נח נפשיה' in h:
        markers['outcome'].append('נח_נפשיה')
    if 'נפטר' in h:
        markers['outcome'].append('נפטר')
    if 'נתרפא' in h:
        markers['outcome'].append('נתרפא')

    # LEGAL MARKERS (negative)
    if 'מתני' in h:
        markers['legal'].append('mishna')
    if 'הלכה' in h:
        markers['legal'].append('halakha')
    if 'תנו רבנן' in h:
        markers['legal'].append('tanu_rabanan')

    # HABITUAL MARKERS (disqualifier)
    if 'היה רגיל' in h or 'הוה רגיל' in h:
        markers['habitual'].append('היה_רגיל')
    if 'רגיל ד' in h:
        markers['habitual'].append('רגיל')

    # ANONYMOUS CHARACTER MARKERS
    if 'ההוא' in h or 'ההיא' in h:
        markers['anonymous_character'].append('ההוא/ההיא')  # that certain man/woman
    if 'חד' in h and 'גברא' in h:
        markers['anonymous_character'].append('חד_גברא')  # a certain man

    return markers


def detect_disqualifiers(hebrew_text: str, english_text: str) -> List[Dict]:
    """Check for disqualifying patterns."""
    found = []

    for name, config in DISQUALIFIERS.items():
        # Check Hebrew markers
        for marker in config.get("hebrew_markers", []):
            if marker in hebrew_text:
                found.append({
                    "type": name,
                    "marker": marker,
                    "language": "hebrew",
                    "reason": config["reason"]
                })
                break

        # Check English markers
        for marker in config.get("english_markers", []):
            if marker.lower() in english_text.lower():
                found.append({
                    "type": name,
                    "marker": marker,
                    "language": "english",
                    "reason": config["reason"]
                })
                break

    return found


def detect_page_boundary_continuation(page_segments: List[Dict]) -> Dict[str, bool]:
    """Detect if a story might continue at page boundaries."""
    if not page_segments:
        return {"starts_mid_story": False, "ends_mid_story": False}

    first_seg = page_segments[0]
    last_seg = page_segments[-1]

    # Check if first segment seems to continue from previous page
    first_eng = first_seg.get('english', '')
    starts_mid = (
        first_eng.startswith('And ') or
        first_eng.startswith('He ') or
        first_eng.startswith('She ') or
        first_eng.startswith('They ') or
        not first_eng[0:1].isupper() if first_eng else False
    )

    # Check if last segment seems incomplete
    last_eng = last_seg.get('english', '')
    ends_mid = (
        last_eng.rstrip().endswith(',') or
        last_eng.rstrip().endswith(':') or
        'and then' in last_eng.lower()[-30:] if last_eng else False
    )

    return {"starts_mid_story": starts_mid, "ends_mid_story": ends_mid}


# ============================================================
# CATEGORICAL CLASSIFIER v6
# ============================================================

class CategoricalStoryClassifier:
    """
    Classifies Talmud passages using categorical system:
    YES, HIGH_CONFIDENCE, LOW_CONFIDENCE, NOT_A_STORY

    v6: Comprehensive revision from Jeff Rubenstein's v5.1 validation feedback.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.model_name = "gemini-2.0-flash"

        if self.api_key and GOOGLE_AI_AVAILABLE:
            self.client = genai.Client(api_key=self.api_key)
            print(f"✓ Gemini API configured (model: {self.model_name})")
        else:
            self.client = None
            if not self.api_key:
                print(f"✗ GOOGLE_API_KEY not set")
            if not GOOGLE_AI_AVAILABLE:
                print(f"✗ Google AI library not available")

    def build_classification_prompt(self, ref: str, segments: List[Dict],
                                     prev_page_last_segments: Optional[List[Dict]] = None,
                                     next_page_first_segments: Optional[List[Dict]] = None) -> str:
        """Build the prompt for categorical classification with cross-page awareness."""

        # Build segment display
        segment_text = []
        for seg in segments:
            eng_preview = seg.get('english', '')[:200]
            heb_preview = seg.get('hebrew', '')[:200]
            segment_text.append(f"[Seg {seg['index']}]\nEnglish: {eng_preview}\nHebrew: {heb_preview}\n")

        # Build cross-page context
        cross_page_context = ""
        if prev_page_last_segments:
            cross_page_context += "\n--- CONTEXT: Last segments from PREVIOUS page ---\n"
            for seg in prev_page_last_segments:
                cross_page_context += f"[Prev page Seg {seg['index']}] {seg.get('english', '')[:150]}\n"
            cross_page_context += "--- END previous page context ---\n\n"

        if next_page_first_segments:
            cross_page_context += "\n--- CONTEXT: First segments from NEXT page ---\n"
            for seg in next_page_first_segments:
                cross_page_context += f"[Next page Seg {seg['index']}] {seg.get('english', '')[:150]}\n"
            cross_page_context += "--- END next page context ---\n\n"

        # Build examples
        yes_examples = "\n\n".join([
            f"""EXAMPLE: {ex['name']} ({ex['ref']})
Hebrew: {ex.get('hebrew', '')[:150]}...
English: {ex['english'][:150]}...
Criteria met:
- Characters: {ex['criteria']['identifiable_characters']}
- Events: {ex['criteria']['multiple_events']}
- Causality: {ex['criteria']['causal_chain']}
- Temporal: {ex['criteria']['temporal_progression']}
- Descriptive: {ex['criteria']['descriptive']}
- Change: {ex['criteria']['change_outcome']}
Classification: YES"""
            for ex in CURATED_EXAMPLES['yes_examples'][:4]
        ])

        high_conf_examples = "\n\n".join([
            f"""EXAMPLE: {ex['name']} ({ex['ref']})
Hebrew: {ex.get('hebrew', '')[:100]}...
Criteria met: 5/6
Weakeners: {', '.join(ex.get('weakeners', []))}
Jeff's note: "{ex['jeff_notes']}"
Classification: HIGH_CONFIDENCE"""
            for ex in CURATED_EXAMPLES['high_confidence_examples']
        ])

        borderline_examples = "\n\n".join([
            f"""EXAMPLE: {ex['name']} ({ex['ref']})
Why borderline: {ex['why_borderline']}
Jeff's note: "{ex['jeff_notes']}"
Classification: LOW_CONFIDENCE (borderline story)"""
            for ex in CURATED_EXAMPLES['low_confidence_borderline_examples'][:3]
        ])

        not_story_examples = "\n\n".join([
            f"""EXAMPLE: {ex['name']} ({ex['ref']})
Hebrew: {ex.get('hebrew', '')[:80]}
Disqualifier: {ex['disqualifier']}
Why not a story: {ex['why_not']}
Classification: NOT_A_STORY"""
            for ex in CURATED_EXAMPLES['not_a_story_examples']
        ])

        prompt = f"""Analyze this Talmudic page and classify each potential story using CATEGORICAL classification.

=== CLASSIFICATION SYSTEM ===

Categories (in order of certainty):
1. YES - Definitively a story (all 6 criteria met, no disqualifiers)
2. HIGH_CONFIDENCE - Likely a story (5-6 criteria met, minor weakeners)
3. LOW_CONFIDENCE - Borderline story (3-4 criteria met, or 1 event + discussion)
4. NOT_A_STORY - Rejected (disqualifier present OR <3 criteria met)

=== THE 6 REQUIRED CRITERIA ===

For each potential story, evaluate these criteria as TRUE or FALSE:

1. IDENTIFIABLE_CHARACTERS: Any specific, identifiable actors in the passage
   IMPORTANT: Anonymous characters COUNT FULLY as characters!
   - "a certain man" (ההוא גברא), "a certain woman" (ההיא איתתא) = TRUE
   - "A woman came before Rabbi X" = TRUE (both are identifiable characters)
   - Named rabbis WHO ACT IN THE NARRATIVE = TRUE
   - Named rabbis who only STATE LEGAL OPINIONS = does NOT count (see disqualifiers)
   - No identifiable actors at all = FALSE

2. MULTIPLE_EVENTS: At least 2 distinct NARRATIVE events described
   CRITICAL - These are NOT events:
   - Verbal statements, objections, or legal arguments ("it is all talk")
   - Ordering someone to do something (speech act, not event)
   - Thinking about acting or considering a legal opinion
   - Experiencing difficulty resolving a legal issue
   - Traveling to participate in a legal debate (logistics of discourse)
   - A legal debate between academies (place names are NOT characters)
   - "Instituting" a practice (legislative action, not narrative event)
   These ARE events:
   - Physical actions (came, went, took, gave, died, married)
   - Changes in state (became ill, was healed, was distressed)
   - Concrete outcomes (was flogged, was excommunicated, was permitted)
   Count the events explicitly. Single action = FALSE

3. CAUSAL_CHAIN: Events connected by cause and effect (STRICT)
   - REQUIRED: Event A CAUSED Event B, which CAUSED Event C
   - ✗ INSUFFICIENT: "Two events happened" (sequential without causation)
   - Example FAIL: "Girl drew water. Girl was raped." (2 events, NO causal link)
   - Example PASS: "Didn't return → wife distressed → tear → death" (each causes next)
   - TEST: Can you trace causation where each event CAUSES the next?

4. TEMPORAL_PROGRESSION: Time markers or clear sequence
   - יומא חד (one day), לסוף (eventually), בראשונה (initially)
   - "after" language showing sequence
   - No time reference = FALSE

5. DESCRIPTIVE: Describes what DID happen (not what SHOULD happen)
   - Past tense narration = TRUE
   - Legal rules, hypotheticals = FALSE

6. CHANGE_OUTCOME: Actual transformation, not just report (STRICT)
   - REQUIRED: Situation TRANSFORMED from beginning to end
   - ✗ INSUFFICIENT: Simple report ("He came and recited blessing")
   - ✗ INSUFFICIENT: Actions without change ("Was greeted with song")
   - ✓ REQUIRED: Actual transformation ("Friends close → friends distanced")
   - TEST: If I remove the events, what CHANGED? If "nothing", it's NOT a story

=== AUTOMATIC DISQUALIFIERS ===

If ANY of these are present, classify as NOT_A_STORY:

- MISHNA section (מתני׳)
- Hypothetical case ("If X were to...")
- Habitual action (היה רגיל = "was accustomed to")
- Pure legal ruling without narrative
- **RABBI STATING LEGAL OPINION**: Rabbi name appears to ATTRIBUTE legal ruling, NOT as character
  ✗ "Rabbi X said that it is permitted..." (legal opinion)
  ✗ "Rabbi X quotes Rabbi Y as saying..." (attribution)
  ✓ "A man came before Rabbi X and Rabbi X ruled..." (Rabbi IS character in story)
- **LEGAL DELIBERATION**: Thinking about acting, considering opinions, experiencing legal difficulty
  ✗ "Levi thought about acting according to opinion X" (deliberation, not event)
  ✗ "He experienced difficulty resolving the issue" (legal difficulty, not event)
- **LEGAL DEBATE SETTING**: Physical setting of debate does NOT make it a story
  ✗ "One sage sat before another and they debated" (debate with setting, not story)
  ✗ "Legal debate between Pumbedita and Matta Mehasia" (academies debating, not story)

=== BORDERLINE STORIES (LOW_CONFIDENCE) ===

IMPORTANT: When there is ONE real event followed by rabbinic discussion or rulings about
that event, classify as LOW_CONFIDENCE (borderline), NOT as NOT_A_STORY.

These are passages where something DID happen, but the narrative is minimal:
- One event + legal discussion about it
- Mainly dialogue/speech acts but with some real events mentioned
- Weak causality but some change
- Jeff calls these "borderline stories" - they deserve LOW_CONFIDENCE classification

=== WEAKENERS (push YES → HIGH_CONFIDENCE or HIGH → LOW) ===

- Embedded in legal discussion
- Short (≤2 segments)
- Implied causality (not explicit)
- Ambiguous outcome
- Continues to/from another page
- **Simple report**: "X came and did Y" without causality/change
- **Minimal causality**: Causality present but MINIMAL
- **Minimal change**: Change present but barely transformative
- **Mainly speech acts**: More dialogue than physical events

NOTE: Anonymous characters ("a certain man") are NOT a weakener.
They are fully valid identifiable characters.

=== STORY BOUNDARY RULES ===

CRITICAL: Get the story boundaries right.

1. A story STARTS with its first NARRATIVE event, NOT with the preceding legal ruling.
   ✗ DO NOT include: Legal rulings that precede and motivate the story
   ✗ DO NOT include: "The halakha is..." statements before the narrative
   ✓ START with: The first action/event ("A man came before...", "One day...", etc.)

2. A story ENDS with its final NARRATIVE action or dialogue.
   ✗ DO NOT include: Talmudic questions/objections AFTER the story (beginning with וְהָא)
   ✗ DO NOT include: Legal rulings made ABOUT the story after it ends
   ✗ DO NOT include: "The Gemara asks/questions..." commentary
   ✓ EXCEPTION: If a rabbi explicitly references the story events in a comment,
     that comment IS part of the story (e.g., "Abaye said: This matter that the
     rabbis said..." when referring back to the story directly)

3. DO NOT split one continuous story into two separate stories.
   If characters continue interacting in dialogue, it is ONE story.

=== CROSS-PAGE AWARENESS ===

The Talmud page boundary is ARBITRARY. Stories often continue across pages.

{cross_page_context}

If you see context from the previous/next page:
- A story that starts on the previous page and continues here should be noted
- A story that starts here and continues to the next page should be noted
- Mark these in the "continuation" field

=== VALIDATED EXAMPLES ===

--- YES Examples ---
{yes_examples}

--- HIGH_CONFIDENCE Examples ---
{high_conf_examples}

--- LOW_CONFIDENCE (Borderline) Examples ---
{borderline_examples}

--- NOT_A_STORY Examples ---
{not_story_examples}

=== PAGE TO ANALYZE ===

Reference: {ref}

{chr(10).join(segment_text)}

=== YOUR TASK ===

1. Scan for potential narratives
2. For each, evaluate all 6 criteria as TRUE/FALSE
3. Check for disqualifiers
4. Check for weakeners
5. Assign classification based on criteria count
6. Set precise story boundaries (exclude legal framing)
7. Check for cross-page continuations

Return JSON:
{{
  "page_ref": "{ref}",
  "stories": [
    {{
      "start_segment": <int>,
      "end_segment": <int>,
      "classification": "YES | HIGH_CONFIDENCE | LOW_CONFIDENCE | NOT_A_STORY",
      "criteria": {{
        "identifiable_characters": {{"met": true/false, "evidence": "...", "anonymous": true/false}},
        "multiple_events": {{"met": true/false, "count": <int>, "events": ["...", "..."]}},
        "causal_chain": {{"met": true/false, "chain": "A → B → C"}},
        "temporal_progression": {{"met": true/false, "markers": ["..."]}},
        "descriptive": {{"met": true/false, "evidence": "..."}},
        "change_outcome": {{"met": true/false, "before": "...", "after": "..."}}
      }},
      "criteria_met_count": <0-6>,
      "disqualifiers_found": ["..." or empty],
      "weakeners_found": ["..." or empty],
      "one_sentence_summary": "...",
      "classification_reasoning": "...",
      "continuation": {{
        "continues_from_previous_page": true/false,
        "continues_to_next_page": true/false,
        "note": "..."
      }}
    }}
  ]
}}

If no stories found: {{"page_ref": "{ref}", "stories": []}}
"""
        return prompt

    def build_self_check_prompt(self, ref: str, stories: List[Dict], segments: List[Dict]) -> str:
        """Jeff's domain-specific self-check questions - v6 expanded."""

        story_summaries = []
        for i, story in enumerate(stories):
            start = story.get('start_segment', 0)
            end = story.get('end_segment', 0)

            text_preview = ""
            for seg in segments:
                if seg['index'] >= start and seg['index'] <= end:
                    text_preview += seg.get('english', '')[:150] + "... "

            story_summaries.append(f"""
STORY {i+1}: Segments {start}-{end}
Classification: {story.get('classification', 'UNKNOWN')}
Summary: {story.get('one_sentence_summary', 'N/A')}
Text: {text_preview[:300]}...
""")

        prompt = f"""You classified the following as stories from {ref}.
Now apply Jeff Rubenstein's domain-specific validation questions:

{chr(10).join(story_summaries)}

=== JEFF'S SELF-CHECK QUESTIONS (v6 expanded) ===

For EACH story, answer these questions:

1. DESCRIPTIVE VS PRESCRIPTIVE TEST:
   "Is this describing what someone DID, or what the law SAYS should happen?"
   - If it's about what SHOULD happen → NOT_A_STORY

2. HABITUAL MARKER CHECK:
   "Does היה רגיל or רגיל appear in the Hebrew?"
   - If yes → NOT_A_STORY (habitual, not one-time)

3. MA'ASEH FOLLOW-THROUGH:
   "If מעשה appears, does an actual story follow, or just legal discussion?"
   - מעשה followed by legal analysis → NOT_A_STORY

4. EVENT COUNT TEST:
   "Can I list at least 2 distinct NARRATIVE events? What are they?"
   CRITICAL: These do NOT count as events:
   - Verbal statements or legal arguments ("it is all talk")
   - Thinking about acting or deliberating
   - Experiencing legal difficulty
   - Traveling to participate in a debate
   - Ordering someone to do something
   - If only 1 event → check if borderline (LOW_CONFIDENCE) or NOT_A_STORY

5. CAUSALITY TEST (STRICT):
   "Can I state the causal chain as: A CAUSED B, which CAUSED C?"
   - If no causation → NOT_A_STORY
   - If minimal causation → LOW_CONFIDENCE (borderline)

6. CHANGE TEST (STRICT):
   "What is different at the end compared to the beginning?"
   - Simple report → NOT_A_STORY
   - Minimal change → LOW_CONFIDENCE (borderline)

7. CHARACTER ROLE TEST:
   "Are the identified characters ACTING in a narrative, or just participating in legal discourse?"
   - Rabbi only stating opinions → NOT_A_STORY
   - Rabbi traveling to debate → NOT_A_STORY (logistics of discourse)
   - Debate between academies (place names) → NOT_A_STORY
   - "A man came before Rabbi X and Rabbi X ruled..." → Rabbi IS character
   - Anonymous character ("a certain man/woman") → VALID character (not weakener)

8. BOUNDARY CHECK:
   "Does the story start with a legal ruling that should be excluded?"
   "Does the story end with Talmudic commentary that should be excluded?"
   - Legal ruling before story → trim start_segment forward
   - Talmudic question/commentary after → trim end_segment back
   - Rabbi directly referencing story → KEEP as part of story

9. BORDERLINE CHECK:
   "Is there one real event followed by discussion?"
   - If yes → LOW_CONFIDENCE (borderline), not NOT_A_STORY
   - Jeff says: passages with minimal narrative deserve LOW_CONFIDENCE

=== VALIDATION OUTPUT ===

Return JSON:
{{
  "validations": [
    {{
      "story_number": 1,
      "original_classification": "...",
      "self_check_results": {{
        "descriptive_test": {{"passed": true/false, "note": "..."}},
        "habitual_check": {{"passed": true/false, "note": "..."}},
        "maaseh_followthrough": {{"passed": true/false, "note": "..."}},
        "event_count": {{"passed": true/false, "count": <int>, "events": ["..."]}},
        "causality_test": {{"passed": true/false, "causal_or_sequential": "causal|sequential", "chain": "..."}},
        "change_test": {{"passed": true/false, "change_type": "transformation|report", "before": "...", "after": "..."}},
        "character_role_test": {{"passed": true/false, "role": "narrative_actor|legal_discourse|anonymous_valid", "note": "..."}},
        "boundary_check": {{"needs_trim": true/false, "suggested_start": <int or null>, "suggested_end": <int or null>, "note": "..."}},
        "borderline_check": {{"is_borderline": true/false, "note": "..."}}
      }},
      "tests_passed": <0-9>,
      "final_classification": "YES | HIGH_CONFIDENCE | LOW_CONFIDENCE | NOT_A_STORY",
      "adjustment_reason": "..." or null if no change,
      "boundary_adjustment": {{
        "new_start_segment": <int or null>,
        "new_end_segment": <int or null>
      }}
    }}
  ]
}}
"""
        return prompt

    def _call_google(self, prompt: str) -> str:
        """Call Google Gemini API."""
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=8192,
                    temperature=0.1,
                )
            )

            if not response.candidates:
                return ""

            full_text = ""
            for part in response.candidates[0].content.parts:
                full_text += part.text

            return full_text
        except Exception as e:
            print(f"  Gemini API error: {e}")
            raise

    def _parse_json_response(self, content: str) -> Optional[Dict]:
        """Parse JSON from AI response, handling markdown code blocks."""
        cleaned = content
        if '```json' in cleaned:
            cleaned = cleaned.split('```json')[1].split('```')[0]
        elif '```' in cleaned:
            parts = cleaned.split('```')
            if len(parts) >= 2:
                cleaned = parts[1]

        json_start = cleaned.find('{')
        json_end = cleaned.rfind('}') + 1

        if json_start >= 0 and json_end > json_start:
            try:
                return json.loads(cleaned[json_start:json_end])
            except json.JSONDecodeError as e:
                print(f"  JSON parse error: {e}")
                return None
        return None

    def classify_page(self, ref: str, segments: List[Dict],
                      prev_page_last_segments: Optional[List[Dict]] = None,
                      next_page_first_segments: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Classify stories on a page using v6 categorical system.
        Now accepts cross-page context for boundary awareness.
        """
        if not self.client:
            return {"page_ref": ref, "stories": [], "error": "No API configured"}

        # Build and send classification prompt with cross-page context
        prompt = self.build_classification_prompt(
            ref, segments,
            prev_page_last_segments=prev_page_last_segments,
            next_page_first_segments=next_page_first_segments
        )
        print(f"  Prompt length: {len(prompt)} chars")

        try:
            content = self._call_google(prompt)
            print(f"  Response length: {len(content)} chars")
            if content:
                print(f"  Response preview: {content[:200]}...")
            result = self._parse_json_response(content)

            if not result:
                return {"page_ref": ref, "stories": [], "error": "Could not parse response"}

            # Run self-check on identified stories
            stories = result.get('stories', [])
            if stories:
                stories_to_check = [s for s in stories if s.get('classification') != 'NOT_A_STORY']

                if stories_to_check:
                    print(f"  Running Jeff's self-check on {len(stories_to_check)} candidates...")

                    self_check_prompt = self.build_self_check_prompt(ref, stories_to_check, segments)
                    self_check_content = self._call_google(self_check_prompt)
                    self_check_result = self._parse_json_response(self_check_content)

                    if self_check_result:
                        validations = self_check_result.get('validations', [])
                        for v in validations:
                            story_num = v.get('story_number', 0) - 1
                            if 0 <= story_num < len(stories_to_check):
                                original = stories_to_check[story_num].get('classification')
                                final = v.get('final_classification')

                                if original != final:
                                    print(f"    Self-check adjusted: {original} → {final}")
                                    stories_to_check[story_num]['classification'] = final
                                    stories_to_check[story_num]['self_check_adjustment'] = v.get('adjustment_reason')

                                # Apply boundary adjustments
                                boundary_adj = v.get('boundary_adjustment', {})
                                if boundary_adj:
                                    new_start = boundary_adj.get('new_start_segment')
                                    new_end = boundary_adj.get('new_end_segment')
                                    if new_start is not None:
                                        old_start = stories_to_check[story_num].get('start_segment')
                                        stories_to_check[story_num]['start_segment'] = new_start
                                        print(f"    Boundary adjusted: start {old_start} → {new_start}")
                                    if new_end is not None:
                                        old_end = stories_to_check[story_num].get('end_segment')
                                        stories_to_check[story_num]['end_segment'] = new_end
                                        print(f"    Boundary adjusted: end {old_end} → {new_end}")

                                stories_to_check[story_num]['self_check_results'] = v.get('self_check_results')

            return result

        except Exception as e:
            print(f"  Classification error: {e}")
            import traceback
            traceback.print_exc()
            return {"page_ref": ref, "stories": [], "error": str(e)}


# ============================================================
# CROSS-PAGE STORY MERGING
# ============================================================

def merge_cross_page_stories(pages: List[Dict]) -> List[Dict]:
    """
    Post-processing pass: detect and merge stories that span page boundaries.

    Looks for:
    1. Story at end of page N flagged with continues_to_next_page
    2. Story at start of page N+1 flagged with continues_from_previous_page
    3. Story at end of page N ending at the last segment + story at start of N+1 starting at segment 0

    When found, merges them into a single cross-page story attached to page N.
    """
    if len(pages) < 2:
        return pages

    merged_pages = list(pages)  # shallow copy
    pages_to_update = {}  # index -> updated page data

    for i in range(len(merged_pages) - 1):
        page_n = merged_pages[i]
        page_n1 = merged_pages[i + 1]

        stories_n = page_n.get('stories', [])
        stories_n1 = page_n1.get('stories', [])

        if not stories_n or not stories_n1:
            continue

        # Get last story on page N and first story on page N+1
        last_story_n = stories_n[-1]
        first_story_n1 = stories_n1[0]

        # Check if they should be merged
        should_merge = False
        merge_reason = ""

        # Check continuation flags
        cont_n = last_story_n.get('continuation', {})
        cont_n1 = first_story_n1.get('continuation', {})

        if cont_n.get('continues_to_next_page'):
            should_merge = True
            merge_reason = "Page N story flagged as continuing to next page"

        if cont_n1.get('continues_from_previous_page'):
            should_merge = True
            merge_reason = "Page N+1 story flagged as continuing from previous page"

        # Check if last story ends at/near last segment AND first story starts at/near segment 0
        segments_n = page_n.get('segments', [])
        if segments_n:
            last_seg_idx = segments_n[-1]['index']
            if (last_story_n.get('end_segment', -1) >= last_seg_idx - 1 and
                first_story_n1.get('start_segment', 999) <= 1):
                # Heuristic: stories at page boundary likely continue
                # Only merge if at least one is classified as a story
                cls_n = last_story_n.get('classification', 'NOT_A_STORY')
                cls_n1 = first_story_n1.get('classification', 'NOT_A_STORY')
                if cls_n != 'NOT_A_STORY' or cls_n1 != 'NOT_A_STORY':
                    should_merge = True
                    merge_reason = f"Stories at page boundary ({page_n['ref']} → {page_n1['ref']})"

        if should_merge:
            print(f"  ⚡ Merging cross-page story: {merge_reason}")

            # Create merged story
            merged_story = {
                "start_segment": last_story_n.get('start_segment', 0),
                "end_segment": last_story_n.get('end_segment', 0),
                "start_segment_page2": first_story_n1.get('start_segment', 0),
                "end_segment_page2": first_story_n1.get('end_segment', 0),
                "classification": _pick_higher_classification(
                    last_story_n.get('classification', 'NOT_A_STORY'),
                    first_story_n1.get('classification', 'NOT_A_STORY')
                ),
                "spans_pages": [page_n['ref'], page_n1['ref']],
                "one_sentence_summary": (
                    last_story_n.get('one_sentence_summary', '') +
                    " [continues] " +
                    first_story_n1.get('one_sentence_summary', '')
                ),
                "classification_reasoning": f"Cross-page merge: {merge_reason}",
                "criteria": last_story_n.get('criteria', {}),
                "criteria_met_count": max(
                    last_story_n.get('criteria_met_count', 0),
                    first_story_n1.get('criteria_met_count', 0)
                ),
                "disqualifiers_found": last_story_n.get('disqualifiers_found', []),
                "weakeners_found": list(set(
                    last_story_n.get('weakeners_found', []) +
                    first_story_n1.get('weakeners_found', [])
                )),
                "continuation": {
                    "continues_from_previous_page": cont_n.get('continues_from_previous_page', False),
                    "continues_to_next_page": cont_n1.get('continues_to_next_page', False),
                    "note": f"Merged from {page_n['ref']} and {page_n1['ref']}"
                },
                "merged_from": {
                    "page1_story": last_story_n,
                    "page2_story": first_story_n1
                }
            }

            # Update page N: replace last story with merged story
            idx_n = i if i not in pages_to_update else i
            updated_stories_n = list(stories_n[:-1]) + [merged_story]

            if i in pages_to_update:
                pages_to_update[i]['stories'] = updated_stories_n
            else:
                pages_to_update[i] = dict(page_n)
                pages_to_update[i]['stories'] = updated_stories_n

            # Update page N+1: remove first story (now part of merge)
            updated_stories_n1 = list(stories_n1[1:])
            if i + 1 in pages_to_update:
                pages_to_update[i + 1]['stories'] = updated_stories_n1
            else:
                pages_to_update[i + 1] = dict(page_n1)
                pages_to_update[i + 1]['stories'] = updated_stories_n1

    # Apply updates
    for idx, updated_page in pages_to_update.items():
        merged_pages[idx] = updated_page

    return merged_pages


def _pick_higher_classification(cls1: str, cls2: str) -> str:
    """Pick the higher confidence classification of two."""
    order = {'YES': 4, 'HIGH_CONFIDENCE': 3, 'LOW_CONFIDENCE': 2, 'NOT_A_STORY': 1}
    if order.get(cls1, 0) >= order.get(cls2, 0):
        return cls1
    return cls2


def detect_duplicate_stories(pages: List[Dict]) -> List[Dict]:
    """
    Detect and flag stories that appear to be the same passage quoted on multiple pages.
    Uses text similarity of the first 100 chars of English text.
    """
    story_fingerprints = {}  # fingerprint -> (page_idx, story_idx, ref)

    for page_idx, page in enumerate(pages):
        segments = page.get('segments', [])
        for story_idx, story in enumerate(page.get('stories', [])):
            if story.get('classification') == 'NOT_A_STORY':
                continue

            start = story.get('start_segment', 0)
            end = story.get('end_segment', 0)

            # Build fingerprint from story text
            story_text = ""
            for seg in segments:
                if seg['index'] >= start and seg['index'] <= end:
                    story_text += seg.get('english', '')

            fingerprint = story_text[:100].strip().lower()
            if len(fingerprint) < 20:
                continue

            if fingerprint in story_fingerprints:
                orig_ref = story_fingerprints[fingerprint][2]
                story['possible_duplicate_of'] = orig_ref
                print(f"  ⚠ Possible duplicate: {page['ref']} story matches {orig_ref}")
            else:
                story_fingerprints[fingerprint] = (page_idx, story_idx, page['ref'])

    return pages


# ============================================================
# SEFARIA API INTEGRATION
# ============================================================

SEFARIA_API = "https://www.sefaria.org/api"

def get_page_with_segments(ref: str) -> Optional[Dict]:
    """Fetch page from Sefaria with segments preserved."""
    url = f"{SEFARIA_API}/texts/{ref}"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()

        text_segments = data.get('text', [])
        hebrew_segments = data.get('he', [])

        # Handle nested lists
        if text_segments and isinstance(text_segments[0], list):
            text_segments = [item for sublist in text_segments for item in sublist]
            hebrew_segments = [item for sublist in hebrew_segments for item in sublist]

        min_len = min(len(text_segments), len(hebrew_segments))

        return {
            'ref': ref,
            'segments': [
                {
                    'index': i,
                    'english': str(text_segments[i]) if text_segments[i] else '',
                    'hebrew': str(hebrew_segments[i]) if hebrew_segments[i] else ''
                }
                for i in range(min_len)
            ]
        }
    except Exception as e:
        print(f"  Error fetching {ref}: {e}")
        return None


# ============================================================
# MAIN EXECUTION
# ============================================================

def analyze_tractate_v6(tractate: str, start_page: int = 2, end_page: int = 10):
    """
    Analyze a tractate using v6 categorical classification.
    Includes cross-page context and post-processing merge.
    """
    print("=" * 70)
    print(f"Talmud Story Detection v6 - Jeff's Comprehensive Feedback")
    print(f"Tractate: {tractate}, Pages: {start_page}-{end_page}")
    print("=" * 70)

    classifier = CategoricalStoryClassifier()

    # First pass: fetch all pages
    print("\n--- Phase 1: Fetching all pages ---")
    all_page_data = {}
    page_refs = []
    for page_num in range(start_page, end_page + 1):
        for side in ['a', 'b']:
            ref = f"{tractate} {page_num}{side}"
            page_refs.append(ref)
            page_data = get_page_with_segments(ref)
            if page_data:
                all_page_data[ref] = page_data
                print(f"  Fetched {ref}: {len(page_data['segments'])} segments")
            time.sleep(0.3)

    # Second pass: classify with cross-page context
    print("\n--- Phase 2: Classifying with cross-page context ---")
    results = {
        "tractate": tractate,
        "version": "v6",
        "pages": [],
        "summary": {
            "yes": 0,
            "high_confidence": 0,
            "low_confidence": 0,
            "not_a_story": 0,
            "cross_page_merges": 0
        }
    }

    for i, ref in enumerate(page_refs):
        if ref not in all_page_data:
            continue

        page_data = all_page_data[ref]
        print(f"\nAnalyzing {ref}...")

        # Get cross-page context (last 3 segments of prev, first 3 of next)
        prev_ref = page_refs[i - 1] if i > 0 else None
        next_ref = page_refs[i + 1] if i < len(page_refs) - 1 else None

        prev_last_segs = None
        if prev_ref and prev_ref in all_page_data:
            prev_segs = all_page_data[prev_ref]['segments']
            prev_last_segs = prev_segs[-3:] if len(prev_segs) >= 3 else prev_segs

        next_first_segs = None
        if next_ref and next_ref in all_page_data:
            next_segs = all_page_data[next_ref]['segments']
            next_first_segs = next_segs[:3] if len(next_segs) >= 3 else next_segs

        classification_result = classifier.classify_page(
            ref, page_data['segments'],
            prev_page_last_segments=prev_last_segs,
            next_page_first_segments=next_first_segs
        )

        stories = classification_result.get('stories', [])

        for story in stories:
            cls = story.get('classification', 'NOT_A_STORY')
            if cls == 'YES':
                print(f"  ✓ YES: {story.get('one_sentence_summary', 'Story found')[:60]}")
            elif cls == 'HIGH_CONFIDENCE':
                print(f"  ◎ HIGH: {story.get('one_sentence_summary', 'Likely story')[:60]}")
            elif cls == 'LOW_CONFIDENCE':
                print(f"  ○ LOW: {story.get('one_sentence_summary', 'Borderline')[:60]}")

        page_result = {
            "ref": ref,
            "segments": page_data['segments'],
            "stories": stories
        }
        results['pages'].append(page_result)

        time.sleep(1)  # Rate limiting

    # Third pass: cross-page merging
    print("\n--- Phase 3: Cross-page story merging ---")
    results['pages'] = merge_cross_page_stories(results['pages'])

    # Fourth pass: duplicate detection
    print("\n--- Phase 4: Duplicate detection ---")
    results['pages'] = detect_duplicate_stories(results['pages'])

    # Recount after merging
    for page in results['pages']:
        for story in page.get('stories', []):
            cls = story.get('classification', 'NOT_A_STORY')
            if cls == 'YES':
                results['summary']['yes'] += 1
            elif cls == 'HIGH_CONFIDENCE':
                results['summary']['high_confidence'] += 1
            elif cls == 'LOW_CONFIDENCE':
                results['summary']['low_confidence'] += 1
            else:
                results['summary']['not_a_story'] += 1

            if story.get('spans_pages'):
                results['summary']['cross_page_merges'] += 1

    # Print summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"YES (definitive stories): {results['summary']['yes']}")
    print(f"HIGH_CONFIDENCE (likely stories): {results['summary']['high_confidence']}")
    print(f"LOW_CONFIDENCE (borderline/needs review): {results['summary']['low_confidence']}")
    print(f"NOT_A_STORY (rejected): {results['summary']['not_a_story']}")
    print(f"Cross-page merges: {results['summary']['cross_page_merges']}")

    return results


def save_results(results: Dict, filename: str):
    """Save results to JSON file."""
    output_dir = Path("results/v6")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / filename
    output_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"\nResults saved to {output_path}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) >= 3:
        start_page = int(sys.argv[1])
        end_page = int(sys.argv[2])
        filename = f"ketubot_v6_{start_page}-{end_page}.json"
    else:
        start_page = 2
        end_page = 10
        filename = "ketubot_v6_test.json"

    results = analyze_tractate_v6("Ketubot", start_page=start_page, end_page=end_page)
    save_results(results, filename)
