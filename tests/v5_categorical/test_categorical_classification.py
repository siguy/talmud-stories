#!/usr/bin/env python3
"""
Talmud Story Detection v5: Categorical Classification

Key changes from v4:
- Replaces percentage confidence (0-100) with categorical: YES, HIGH_CONFIDENCE, LOW_CONFIDENCE, NOT_A_STORY
- Explicit boolean evaluation of 6 criteria
- Disqualifier and weakener detection
- Jeff's domain-specific self-check questions
- Curated examples with exact Hebrew text from validation data
"""

import requests
import json
import time
import os
import re
from typing import List, Dict, Any, Optional
from pathlib import Path

# Import Google Generative AI for Gemini support
try:
    import google.generativeai as genai
    GOOGLE_AI_AVAILABLE = True
except ImportError:
    GOOGLE_AI_AVAILABLE = False
    print("google-generativeai not installed. Run: pip install google-generativeai")


# ============================================================
# JEFF'S VALIDATED EXAMPLES WITH EXACT HEBREW TEXT
# ============================================================

CURATED_EXAMPLES = {
    "yes_examples": [
        {
            "ref": "Ketubot 62b",
            "name": "Rav Reḥumi's Death",
            "hebrew": "אמר רב רחומי הוה שכיח קמיה דרבא במחוזא הוה רגיל דהוה אתי לביתיה כל מעלי יומא דכפורי יומא חד משכיה שמעתא נפקא דעתה דביתהו השתא אתי השתא אתי לא אתא חלש דעתה אחית דמעתא מעינה הוה יתיב באיגרא אפחית איגרא מתותיה ונח נפשיה",
            "english": "Rav Reḥumi would commonly study before Rava in Meḥoza. He was accustomed to come home every year on the eve of Yom Kippur. One day he was engrossed in the halakha. His wife was expecting him: Now he is coming, now he is coming. He did not come. She was distressed. A tear fell from her eye. He was sitting on the roof. The roof collapsed under him and he died.",
            "criteria": {
                "named_characters": "Rav Reḥumi, his wife, Rava",
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
                "named_characters": "Reish Lakish, Rabbi Yoḥanan, Yehuda bar Naḥmani, Rabbi Yitzḥak bar Ami",
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
                "named_characters": "Rabban Gamliel",
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
            "name": "Woman Before Rabban Gamliel",
            "hebrew": "ההיא דאתאי לקמיה דרבן גמליאל אמרה ליה רבי בעלתי ולא מצא לי בתולים",
            "english": "A certain woman came before Rabban Gamliel. She said to him: My master, my husband had intercourse with me and did not find blood of virginity.",
            "criteria": {
                "named_characters": "Rabban Gamliel, the woman, her husband",
                "multiple_events": "came before rabbi, made claim, testimony given, judgment rendered",
                "causal_chain": "claim → inquiry → evidence → ruling",
                "temporal_progression": "sequence of legal encounter",
                "descriptive": "describes actual case",
                "change_outcome": "dispute → resolution"
            },
            "classification": "YES",
            "jeff_notes": "Legal case with narrative structure"
        }
    ],

    "high_confidence_examples": [
        {
            "ref": "Ketubot 62b (second story)",
            "name": "Rabbi Akiva and Wife",
            "hebrew": "רבי עקיבא רעיא דבן כלבא שבוע הוה חזיתיה ברתיה דהוה צניע ומעלי",
            "english": "Rabbi Akiva was a shepherd of ben Kalba Savua. His daughter saw that he was modest and noble.",
            "criteria": {
                "named_characters": "Rabbi Akiva, daughter of Kalba Savua",
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
                "named_characters": "Rabbi Ami, Rabbi Yitzḥak Nappaḥa",
                "multiple_events": "approached first rabbi, rejected, approached second, accepted",
                "causal_chain": "rejection → sought alternative → acceptance",
                "temporal_progression": "sequence implied",
                "descriptive": "describes what happened",
                "change_outcome": "rejected → accepted"
            },
            "weakeners": ["short (2 segments)", "embedded in legal discussion"],
            "classification": "HIGH_CONFIDENCE",
            "jeff_notes": "borderline - it's a legal discussion but it does have named characters and a series of events with change"
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
            "hebrew_marker": "היה רגיל",
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
    "biblical_narrative": {
        "english_markers": ["David", "Moses", "Abraham", "Isaac", "Jacob", "Solomon"],
        "reason": "Biblical narratives are excluded - focus is on rabbinic stories"
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
    }
}

WEAKENERS = {
    "embedded_in_legal": "Story is embedded within legal discussion, boundaries unclear",
    "short_narrative": "Very brief (2 segments or less)",
    "implied_causality": "Causal chain implied but not explicitly stated",
    "partial_naming": "Characters partially named ('a certain man' vs specific name)",
    "ambiguous_outcome": "Change/outcome implied but not stated",
    "incomplete_view": "Story continues from/to another page",
    "single_source": "Only one rabbi mentioned acting alone"
}


# ============================================================
# SEGMENT PROCESSING (from v4)
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
        'habitual': []
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
            if marker in english_text:
                found.append({
                    "type": name,
                    "marker": marker,
                    "language": "english",
                    "reason": config["reason"]
                })
                break

    return found


def extract_characters(english_text: str) -> List[str]:
    """Extract character names from English text."""
    characters = []

    patterns = [
        r'(?:Rabbi|Rav|Rabban|Mar)\s+[A-Z][a-z]+(?:\s+(?:bar|ben|son of)\s+[A-Z][a-z]+)?',
        r'Reish Lakish',
        r'Abaye',
        r'Rava(?!\s+in)',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, english_text)
        characters.extend(matches)

    # Deduplicate
    seen = set()
    unique = []
    for c in characters:
        c_clean = c.strip()
        if c_clean not in seen:
            seen.add(c_clean)
            unique.append(c_clean)

    return unique


# ============================================================
# CATEGORICAL CLASSIFIER
# ============================================================

class CategoricalStoryClassifier:
    """
    Classifies Talmud passages using categorical system:
    YES, HIGH_CONFIDENCE, LOW_CONFIDENCE, NOT_A_STORY
    """

    def __init__(self, api_key: Optional[str] = None, provider: str = "google"):
        self.provider = provider.lower()

        if self.provider == "google":
            self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
            if self.api_key and GOOGLE_AI_AVAILABLE:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel("gemini-2.0-flash-exp")
                print(f"✓ Gemini API configured")
            else:
                self.model = None
                if not self.api_key:
                    print(f"✗ GOOGLE_API_KEY not set")
                if not GOOGLE_AI_AVAILABLE:
                    print(f"✗ Google AI library not available")
        else:
            self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
            self.model = "claude-3-5-haiku-20241022"

    def build_classification_prompt(self, ref: str, segments: List[Dict]) -> str:
        """Build the prompt for categorical classification."""

        # Build segment display
        segment_text = []
        for seg in segments:
            eng_preview = seg.get('english', '')[:200]
            heb_preview = seg.get('hebrew', '')[:200]
            segment_text.append(f"[Seg {seg['index']}]\nEnglish: {eng_preview}\nHebrew: {heb_preview}\n")

        # Build examples section
        yes_examples = "\n\n".join([
            f"""EXAMPLE: {ex['name']} ({ex['ref']})
Hebrew: {ex['hebrew'][:150]}...
English: {ex['english'][:150]}...
Criteria met:
- Characters: {ex['criteria']['named_characters']}
- Events: {ex['criteria']['multiple_events']}
- Causality: {ex['criteria']['causal_chain']}
- Temporal: {ex['criteria']['temporal_progression']}
- Descriptive: {ex['criteria']['descriptive']}
- Change: {ex['criteria']['change_outcome']}
Classification: YES"""
            for ex in CURATED_EXAMPLES['yes_examples'][:3]
        ])

        high_conf_examples = "\n\n".join([
            f"""EXAMPLE: {ex['name']} ({ex['ref']})
Hebrew: {ex['hebrew'][:100]}...
Criteria met: 5/6
Weakeners: {', '.join(ex.get('weakeners', []))}
Jeff's note: "{ex['jeff_notes']}"
Classification: HIGH_CONFIDENCE"""
            for ex in CURATED_EXAMPLES['high_confidence_examples']
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
3. LOW_CONFIDENCE - May be a story (3-4 criteria met, needs human review)
4. NOT_A_STORY - Rejected (disqualifier present OR <3 criteria met)

=== THE 6 REQUIRED CRITERIA ===

For each potential story, evaluate these criteria as TRUE or FALSE:

1. NAMED_CHARACTERS: Specific post-biblical figures (Rav X, Rabbi Y)
   - "a certain man" = partial (weakener)
   - No names at all = FALSE

2. MULTIPLE_EVENTS: At least 2 distinct events described
   - Count the events explicitly
   - Single action = FALSE

3. CAUSAL_CHAIN: Events connected by cause and effect
   - A caused B, which caused C
   - Random sequence without causation = FALSE

4. TEMPORAL_PROGRESSION: Time markers or clear sequence
   - יומא חד (one day), לסוף (eventually), בראשונה (initially)
   - No time reference = FALSE

5. DESCRIPTIVE: Describes what DID happen (not what SHOULD happen)
   - Past tense narration = TRUE
   - Legal rules, hypotheticals = FALSE

6. CHANGE_OUTCOME: Situation different at end than beginning
   - Clear before/after = TRUE
   - Static report = FALSE

=== AUTOMATIC DISQUALIFIERS ===

If ANY of these are present, classify as NOT_A_STORY:

- MISHNA section (מתני׳)
- Hypothetical case ("If X were to...")
- Biblical narrative (Moses, David, etc.)
- Habitual action (היה רגיל = "was accustomed to")
- Pure legal ruling without narrative

=== WEAKENERS (push YES → HIGH_CONFIDENCE) ===

- Embedded in legal discussion
- Short (≤2 segments)
- Implied causality (not explicit)
- Partial character naming
- Ambiguous outcome
- Continues to/from another page

=== VALIDATED EXAMPLES ===

--- YES Examples ---
{yes_examples}

--- HIGH_CONFIDENCE Examples ---
{high_conf_examples}

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

Return JSON:
{{
  "page_ref": "{ref}",
  "stories": [
    {{
      "start_segment": <int>,
      "end_segment": <int>,
      "classification": "YES | HIGH_CONFIDENCE | LOW_CONFIDENCE | NOT_A_STORY",
      "criteria": {{
        "named_characters": {{"met": true/false, "evidence": "..."}},
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
      "classification_reasoning": "..."
    }}
  ]
}}

If no stories found: {{"page_ref": "{ref}", "stories": []}}
"""
        return prompt

    def build_self_check_prompt(self, ref: str, stories: List[Dict], segments: List[Dict]) -> str:
        """Jeff's domain-specific self-check questions."""

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

=== JEFF'S SELF-CHECK QUESTIONS ===

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
   "Can I list at least 2 distinct events? What are they?"
   - If only 1 event → NOT_A_STORY

5. CAUSALITY TEST:
   "Can I state the causal chain as: A caused B, which caused C?"
   - If no causation → NOT_A_STORY or downgrade to LOW_CONFIDENCE

6. CHANGE TEST:
   "What is different at the end compared to the beginning?"
   - If nothing changed → NOT_A_STORY

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
        "causality_test": {{"passed": true/false, "chain": "..."}},
        "change_test": {{"passed": true/false, "before": "...", "after": "..."}}
      }},
      "tests_passed": <0-6>,
      "final_classification": "YES | HIGH_CONFIDENCE | LOW_CONFIDENCE | NOT_A_STORY",
      "adjustment_reason": "..." or null if no change
    }}
  ]
}}
"""
        return prompt

    def _call_google(self, prompt: str) -> str:
        """Call Google Gemini API."""
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=8192,
                    temperature=0.1,
                ),
                request_options={"timeout": 120}
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

    def classify_page(self, ref: str, segments: List[Dict]) -> Dict[str, Any]:
        """
        Classify stories on a page using categorical system.
        """
        if not self.model:
            return {"page_ref": ref, "stories": [], "error": "No API configured"}

        # Build and send classification prompt
        prompt = self.build_classification_prompt(ref, segments)
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
                        # Apply self-check adjustments
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

                                stories_to_check[story_num]['self_check_results'] = v.get('self_check_results')

            return result

        except Exception as e:
            print(f"  Classification error: {e}")
            import traceback
            traceback.print_exc()
            return {"page_ref": ref, "stories": [], "error": str(e)}


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

def analyze_tractate_v5(tractate: str, start_page: int = 2, end_page: int = 10):
    """
    Analyze a tractate using v5 categorical classification.
    """
    print("=" * 70)
    print(f"Talmud Story Detection v5 - Categorical Classification")
    print(f"Tractate: {tractate}, Pages: {start_page}-{end_page}")
    print("=" * 70)

    classifier = CategoricalStoryClassifier(provider="google")

    results = {
        "tractate": tractate,
        "version": "v5_categorical",
        "pages": [],
        "summary": {
            "yes": 0,
            "high_confidence": 0,
            "low_confidence": 0,
            "not_a_story": 0
        }
    }

    for page_num in range(start_page, end_page + 1):
        for side in ['a', 'b']:
            ref = f"{tractate} {page_num}{side}"
            print(f"\nAnalyzing {ref}...")

            page_data = get_page_with_segments(ref)
            if not page_data:
                continue

            classification_result = classifier.classify_page(ref, page_data['segments'])

            stories = classification_result.get('stories', [])

            # Count by classification
            for story in stories:
                cls = story.get('classification', 'NOT_A_STORY')
                if cls == 'YES':
                    results['summary']['yes'] += 1
                    print(f"  YES: {story.get('one_sentence_summary', 'Story found')[:50]}...")
                elif cls == 'HIGH_CONFIDENCE':
                    results['summary']['high_confidence'] += 1
                    print(f"  HIGH: {story.get('one_sentence_summary', 'Likely story')[:50]}...")
                elif cls == 'LOW_CONFIDENCE':
                    results['summary']['low_confidence'] += 1
                    print(f"  LOW: {story.get('one_sentence_summary', 'May be story')[:50]}...")
                else:
                    results['summary']['not_a_story'] += 1

            # Store page result with segments for UI
            page_result = {
                "ref": ref,
                "segments": page_data['segments'],
                "stories": stories
            }
            results['pages'].append(page_result)

            time.sleep(0.5)  # Rate limiting

    # Print summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"YES (definitive stories): {results['summary']['yes']}")
    print(f"HIGH_CONFIDENCE (likely stories): {results['summary']['high_confidence']}")
    print(f"LOW_CONFIDENCE (needs review): {results['summary']['low_confidence']}")
    print(f"NOT_A_STORY (rejected): {results['summary']['not_a_story']}")

    return results


def save_results(results: Dict, filename: str):
    """Save results to JSON file."""
    output_dir = Path("results/v5")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / filename
    output_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"\nResults saved to {output_path}")


if __name__ == "__main__":
    # Test on first page only for debugging
    results = analyze_tractate_v5("Ketubot", start_page=2, end_page=2)
    save_results(results, "ketubot_v5_test.json")
