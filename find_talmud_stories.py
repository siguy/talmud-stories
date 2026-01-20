#!/usr/bin/env python3
"""
Talmud Stories Finder - Semantic Narrative Detection
Uses AI to identify passages with narrative structure (beginning, middle, end).
Finds "Literary Stories" including brief dialogues and vignettes with narrative arcs.
"""

import requests
import json
import time
import os
from typing import List, Dict, Any, Optional
from pathlib import Path

# Import Google Generative AI for Gemini support
try:
    import google.generativeai as genai
    GOOGLE_AI_AVAILABLE = True
except ImportError:
    GOOGLE_AI_AVAILABLE = False
    print("⚠️  google-generativeai not installed. Run: pip install google-generativeai")

# Sefaria API base URL
SEFARIA_API = "https://www.sefaria.org/api"

# Major Babylonian Talmud tractates organized by order
TALMUD_TRACTATES = {
    "Zeraim": ["Berakhot"],
    "Moed": [
        "Shabbat", "Eruvin", "Pesachim", "Rosh Hashanah",
        "Yoma", "Sukkah", "Beitzah", "Taanit", "Megillah",
        "Moed Katan", "Chagigah"
    ],
    "Nashim": [
        "Yevamot", "Ketubot", "Nedarim", "Nazir",
        "Sotah", "Gittin", "Kiddushin"
    ],
    "Nezikin": [
        "Bava Kamma", "Bava Metzia", "Bava Batra",
        "Sanhedrin", "Makkot", "Shevuot", "Avodah Zarah", "Horayot"
    ],
    "Kodashim": [
        "Zevachim", "Menachot", "Chullin", "Bekhorot",
        "Arakhin", "Temurah", "Keritot", "Meilah", "Tamid"
    ],
    "Tahorot": ["Niddah"]
}


class NarrativeAnalyzer:
    """Uses AI to detect narrative structure in Talmudic passages"""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-5-haiku-20241022",
                 provider: str = "anthropic"):
        """
        Initialize with AI API key.

        Args:
            api_key: API key (or None to use environment variable)
            model: Model name
                - Anthropic: "claude-3-5-haiku-20241022", "claude-3-5-sonnet-20241022"
                - Google: "gemini-3-flash-preview", "gemini-2.0-flash-exp", "gemini-1.5-flash", "gemini-1.5-pro"
            provider: "anthropic" or "google"
        """
        self.provider = provider.lower()
        self.model = model

        if self.provider == "anthropic":
            self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
            self.api_url = "https://api.anthropic.com/v1/messages"

            if not self.api_key:
                print("\n⚠️  WARNING: No Anthropic API key found.")
                print("Set ANTHROPIC_API_KEY environment variable or pass api_key parameter.")
                print("Falling back to basic heuristic analysis.\n")

        elif self.provider == "google":
            self.api_key = api_key or os.getenv("GOOGLE_API_KEY")

            if not GOOGLE_AI_AVAILABLE:
                print("\n❌ ERROR: google-generativeai package not installed.")
                print("Run: pip install google-generativeai")
                self.api_key = None
            elif not self.api_key:
                print("\n⚠️  WARNING: No Google API key found.")
                print("Set GOOGLE_API_KEY environment variable or pass api_key parameter.")
                print("Falling back to basic heuristic analysis.\n")
            else:
                # Configure Google AI
                genai.configure(api_key=self.api_key)
                self.gemini_model = genai.GenerativeModel(self.model)

        else:
            raise ValueError(f"Unsupported provider: {provider}. Use 'anthropic' or 'google'.")

    def analyze_narrative_structure(self, text: str, ref: str, hebrew_text: str = None) -> Dict[str, Any]:
        """
        Use AI to determine if passage contains a narrative arc.

        Analyzes both English translation and Hebrew/Aramaic original when available.

        Definition: "Literary Stories" - any narrative arc with beginning, middle,
        and end, including brief two-line dialogues or vignettes.
        """
        if not self.api_key:
            return self._heuristic_analysis(text, ref)

        # Prepare bilingual prompt if Hebrew available
        text_section = f"""English Translation:
{text}"""

        if hebrew_text and hebrew_text.strip():
            text_section += f"""

Hebrew/Aramaic Original:
{hebrew_text}

Note: You can read both Hebrew and English. Use BOTH to determine if this is a story.

IMPORTANT: Analyze the narrative structure semantically - do NOT require specific markers.
Some Hebrew phrases that MAY appear in stories (but are NOT required):
- ויהי (vayehi) - "and it was"
- מעשה ב (ma'aseh be) - "an incident involving"
- פעם אחת (pa'am achat) - "one time"
- אמר לו (amar lo) - "said to him"

Many stories have NONE of these markers. Focus on: Does this passage have beginning, middle, end?
If the texts differ or if one is clearer, rely on the more complete version."""

        prompt = f"""Analyze this Talmudic passage and identify ALL "Literary Stories" it contains.

CRITICAL INSTRUCTIONS:
1. A SINGLE PAGE can contain MULTIPLE STORIES (2-4 stories are common)
2. Scan the ENTIRE passage from beginning to end
3. Identify EACH story SEPARATELY with precise boundaries
4. A page may also contain NO stories (only legal discussions)

CRITICAL: This passage may contain LEGAL DISCUSSIONS, HYPOTHETICAL CASES, or STORIES. You must distinguish between them.

═══════════════════════════════════════════════════════════════════════════════
STORIES ARE DESCRIPTIVE (What DID Happen - One-Time Events)
═══════════════════════════════════════════════════════════════════════════════

A STORY must have ALL of these:

1. DESCRIPTIVE, not prescriptive
   ✓ Tells what DID happen in a specific instance
   ✗ NOT what SHOULD happen, COULD happen, or what the law is

2. ONE-TIME SPECIFIC EVENT with named individuals
   ✓ "Ravina arranged his son's marriage..." (specific person, specific event)
   ✓ "A certain man came before Rav Nahman..." (specific incident)
   ✗ "A virgin is married on Wednesday" (general rule)
   ✗ "Women are always married on Wednesday" (repeated action)

3. AT LEAST TWO EVENTS with CAUSAL RELATIONSHIP
   ✓ Event A happened → which caused → Event B → resulting in → Outcome
   ✗ Single fact with no causality: "Rav Zevid had intercourse on Shabbat" (one event, no story)

4. CHANGE or IMPLIED CHANGE (Before → After)
   ✓ Situation changes due to events
   ✗ Report without change: "Rav Asi came and recited blessings" (no causal progression)

5. POST-BIBLICAL RABBINIC CHARACTERS ONLY
   ✓ Stories about rabbis and their contemporaries
   ✗ NOT biblical stories (David, Moses, etc.)

═══════════════════════════════════════════════════════════════════════════════
NOT STORIES (Even if They Sound Narrative)
═══════════════════════════════════════════════════════════════════════════════

❌ LEGAL HYPOTHETICALS - Prescriptive scenarios:
   "If a man gives a woman a ring, and she throws it away, then she is not betrothed"
   → This is a HYPOTHETICAL LEGAL CASE, not a story about something that happened

❌ LEGAL RULINGS - Even with narrative form:
   "A virgin is married on Wednesday and a widow on Thursday"
   → This is a RULE about what should happen, not what did happen

❌ HYPOTHETICAL LEGAL DEBATES:
   "What if he does X? Then the law is Y"
   "Rabbi X says [legal opinion]... Rabbi Y says [legal opinion]..." (unless embedded in actual story)
   → These are legal positions, not narratives about events

❌ REPEATED/HABITUAL ACTIONS:
   "When R. Abbah would come from the academy..." (whenever = not one-time event)
   "Rabbi X would always say..." (habitual, not specific)

❌ SINGLE EVENTS without causality:
   "Rav Zevid engaged in intercourse on Shabbat" (one fact, not a story)

❌ REPORTS without causality or change:
   "Rav Asi happened to come to the house of Rav Ashi and recited six blessings"
   → Events but no causal relationship or change

═══════════════════════════════════════════════════════════════════════════════
EXAMPLES FROM EXPERT REVIEW
═══════════════════════════════════════════════════════════════════════════════

FALSE POSITIVE Example 1:
Text: "A virgin is married on Wednesday and a widow on Thursday. The reason is..."
Why NOT a story: This is PRESCRIPTIVE (what should happen), not descriptive. It's a legal rule.

FALSE POSITIVE Example 2:
Text: "If a man gives a woman a ring and she throws it away, then she is not betrothed..."
Why NOT a story: HYPOTHETICAL legal case. Not a one-time event that actually happened.

FALSE POSITIVE Example 3 (Report, not story):
Text: "Rav Asi happened to come to the house of Rav Ashi and recited six blessings"
Why NOT a story: Just a report of events with no causality or change. No story arc.

TRUE STORY Example 1:
Text: "Ravina arranged for his son to marry a woman from the house of Rav Ḥaviva and recited the blessing from the time of betrothal. He said: I am certain with regard to them, that they will not retract their commitment. Nevertheless, the matter was not to be, and ultimately they retracted their commitment, and the wedding was canceled."
Why IS a story:
✓ One-time specific event (Ravina's son)
✓ Two+ events with causality: arrangement → confidence → unexpected retraction
✓ Change: from betrothal to cancellation
✓ Descriptive (what did happen)

TRUE STORY Example 2:
Text: "Initially, funeral expenditures for the deceased were more taxing than his death, until people would abandon the deceased and flee. This continued until Rabbi Gamliel came and conducted himself in self-deprecatory manner, instructing that they take him for burial in plain linen garments. And all the people conducted themselves following his example."
Why IS a story:
✓ Change over time (before → after)
✓ Causality: Rabbi Gamliel's action → people changed behavior
✓ Multiple events with progression

MULTIPLE STORIES Example (Ketubot 10b):
This page contains THREE separate stories:
Story 1: A certain woman comes before Rav Nahman with testimony → judgment given
Story 2: A man betrothed a woman → died → brother's betrothal case → ruling
Story 3: Another marriage case → witnesses brought → judgment rendered

Each story has its own beginning, middle, end, and must be identified separately!

═══════════════════════════════════════════════════════════════════════════════
STORY BOUNDARIES - CRITICAL REQUIREMENT
═══════════════════════════════════════════════════════════════════════════════

For EACH story you identify, you MUST provide EXACT text boundaries:

1. story_start_english: The first 5-10 words where the story begins in English
2. story_end_english: The last 5-10 words where the story ends in English
3. story_start_hebrew: The first 5-10 words where the story begins in Hebrew/Aramaic
4. story_end_hebrew: The last 5-10 words where the story ends in Hebrew/Aramaic

These boundaries allow us to extract ONLY the story text, excluding legal discussions.

Example boundaries:
- Start: "A certain man came before"
- End: "and he went on his way"

The output should contain ONLY the story text between these markers, not the entire page!

═══════════════════════════════════════════════════════════════════════════════
VALIDATION CHECKLIST
═══════════════════════════════════════════════════════════════════════════════

Before marking is_story=true, verify:
□ Is this DESCRIPTIVE (what happened) not PRESCRIPTIVE (what should happen)?
□ Is this a ONE-TIME specific event with named individuals?
□ Are there AT LEAST 2 EVENTS with CAUSAL relationship?
□ Is there CHANGE or outcome (not just a report)?
□ Is this about RABBIS/post-biblical figures (not biblical characters)?
□ Is this an ACTUAL event (not hypothetical "if X then Y")?
□ Have I provided EXACT start/end boundaries for extraction?

If ANY checkbox is NO → is_story = false

═══════════════════════════════════════════════════════════════════════════════

Passage Reference: {ref}

{text_section}

Respond in JSON format with an ARRAY of stories found:
{{
  "total_stories": <number of stories found, 0 if none>,
  "stories_found": [
    {{
      "story_number": 1,
      "is_story": true,
      "confidence": 0-100,
      "story_start_english": "exact first 5-10 words of story in English",
      "story_end_english": "exact last 5-10 words of story in English",
      "story_start_hebrew": "exact first 5-10 words in Hebrew/Aramaic",
      "story_end_hebrew": "exact last 5-10 words in Hebrew/Aramaic",
      "narrative_elements": {{
        "has_beginning": true/false,
        "has_middle": true/false,
        "has_end": true/false,
        "has_characters": true/false,
        "has_action": true/false,
        "has_dialogue": true/false,
        "has_temporal_progression": true/false
      }},
      "story_type": "full_narrative" | "dialogue_vignette" | "brief_anecdote",
      "one_sentence_summary": "brief description of this specific story",
      "reasoning": "why this is a story - mention causality and change",
      "embedded_in_legal_context": true/false,
      "continuation": {{
        "seems_incomplete": true/false,
        "missing_beginning": true/false,
        "missing_end": true/false,
        "note": "explanation if story continues to next page"
      }},
      "validation_notes": "explain which validation criteria were met"
    }}
  ]
}}

IMPORTANT: If NO stories are found, return: {{"total_stories": 0, "stories_found": []}}"""

        try:
            # Route to appropriate provider
            if self.provider == "anthropic":
                content = self._call_anthropic(prompt)
            elif self.provider == "google":
                content = self._call_google(prompt)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")

            # Extract JSON from response
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                analysis = json.loads(content[json_start:json_end])

                # Convert to new array format if needed (backward compatibility)
                if 'stories_found' not in analysis:
                    # Old format: single story object
                    if analysis.get('is_story', False):
                        # Wrap in array format
                        analysis = {
                            'total_stories': 1,
                            'stories_found': [analysis]
                        }
                    else:
                        # No story found
                        analysis = {
                            'total_stories': 0,
                            'stories_found': []
                        }

                # Validate stories have required boundary fields
                for i, story in enumerate(analysis.get('stories_found', [])):
                    if not story.get('story_start_english'):
                        print(f"  ⚠️  Story {i+1} missing English start boundary")
                    if not story.get('story_start_hebrew'):
                        print(f"  ⚠️  Story {i+1} missing Hebrew start boundary")

                return analysis
            else:
                print(f"  ⚠️  Could not parse AI response for {ref}")
                return self._heuristic_analysis(text, ref)

        except Exception as e:
            print(f"  ⚠️  AI analysis failed for {ref}: {e}")
            return self._heuristic_analysis(text, ref)

    def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic Claude API"""
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        payload = {
            "model": self.model,
            "max_tokens": 1024,
            "messages": [{
                "role": "user",
                "content": prompt
            }]
        }

        response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()

        result = response.json()
        return result["content"][0]["text"]

    def _call_google(self, prompt: str) -> str:
        """Call Google Gemini API"""
        response = self.gemini_model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=2048,
                temperature=0.1,
            )
        )
        return response.text

    def _heuristic_analysis(self, text: str, ref: str) -> Dict[str, Any]:
        """Fallback heuristic analysis when AI is unavailable - returns array format"""
        text_lower = text.lower()

        # Narrative indicators
        has_dialogue = any(marker in text_lower for marker in [
            "said to him", "asked him", "replied", "answered", "told him"
        ])
        has_action = any(marker in text_lower for marker in [
            "went to", "came to", "saw", "found", "did", "made"
        ])
        has_temporal = any(marker in text_lower for marker in [
            "once", "one time", "happened", "afterward", "then", "when"
        ])
        has_characters = "rabbi" in text_lower or "ben " in text_lower

        narrative_count = sum([has_dialogue, has_action, has_temporal, has_characters])
        is_story = narrative_count >= 2

        story_data = {
            "story_number": 1,
            "is_story": is_story,
            "confidence": min(narrative_count * 25, 75),  # Max 75 for heuristic
            "story_start_english": "",  # Can't determine without AI
            "story_end_english": "",
            "story_start_hebrew": "",
            "story_end_hebrew": "",
            "narrative_elements": {
                "has_beginning": has_temporal or has_characters,
                "has_middle": has_action or has_dialogue,
                "has_end": has_dialogue,  # Approximation
                "has_characters": has_characters,
                "has_action": has_action,
                "has_dialogue": has_dialogue,
                "has_temporal_progression": has_temporal
            },
            "story_type": "heuristic_detection" if is_story else "not_a_story",
            "one_sentence_summary": "",
            "reasoning": f"Heuristic analysis: {narrative_count}/4 narrative markers found",
            "embedded_in_legal_context": False,
            "continuation": {
                "seems_incomplete": False,
                "missing_beginning": False,
                "missing_end": False,
                "note": ""
            },
            "validation_notes": "Heuristic fallback - boundaries not available"
        }

        # Return in array format
        if is_story:
            return {
                "total_stories": 1,
                "stories_found": [story_data]
            }
        else:
            return {
                "total_stories": 0,
                "stories_found": []
            }


class SefariaStoryFinder:
    """Find stories in Talmud using semantic narrative detection"""

    def __init__(self, analyzer: NarrativeAnalyzer, use_windowing: bool = True):
        self.analyzer = analyzer
        self.session = requests.Session()
        self.cache = {}
        self.use_windowing = use_windowing  # Enable multi-page story detection

    def extract_story_text(self, full_text: str, start_marker: str, end_marker: str,
                          language: str = "english") -> Optional[str]:
        """
        Extract story text using start/end boundaries.
        Handles cases where markers aren't found exactly.

        Args:
            full_text: The complete page text
            start_marker: First 5-10 words where story begins
            end_marker: Last 5-10 words where story ends
            language: "english" or "hebrew" for better error messages

        Returns:
            Extracted story text, or None if extraction failed
        """
        if not start_marker or not end_marker:
            print(f"  ⚠️  Missing {language} boundaries - cannot extract")
            return None

        # Try exact match first
        start_pos = full_text.find(start_marker)
        end_pos = full_text.find(end_marker)

        if start_pos != -1 and end_pos != -1 and end_pos >= start_pos:
            # Success - extract the story
            return full_text[start_pos:end_pos + len(end_marker)]

        # Fallback: Try with normalized whitespace
        import re

        # Normalize whitespace in both text and markers
        normalized_text = re.sub(r'\s+', ' ', full_text)
        normalized_start = re.sub(r'\s+', ' ', start_marker.strip())
        normalized_end = re.sub(r'\s+', ' ', end_marker.strip())

        start_pos = normalized_text.find(normalized_start)
        end_pos = normalized_text.find(normalized_end)

        if start_pos != -1 and end_pos != -1 and end_pos >= start_pos:
            # Map back to original text positions (approximate)
            # This is a simple approach - could be improved
            return normalized_text[start_pos:end_pos + len(normalized_end)]

        # If still not found, try partial match (first few words)
        first_words = ' '.join(normalized_start.split()[:3])  # First 3 words
        last_words = ' '.join(normalized_end.split()[-3:])     # Last 3 words

        start_pos = normalized_text.find(first_words)
        end_pos = normalized_text.find(last_words)

        if start_pos != -1 and end_pos != -1 and end_pos >= start_pos:
            print(f"  ⚠️  {language} boundaries: using partial match")
            return normalized_text[start_pos:end_pos + len(last_words)]

        # Give up
        print(f"  ❌ {language} boundaries not found in text")
        print(f"     Looking for start: '{start_marker[:50]}...'")
        print(f"     Looking for end: '{end_marker[:50]}...'")
        return None

    def get_tractate_structure(self, tractate: str) -> List[str]:
        """Get all text references (pages/sections) in a tractate"""
        url = f"{SEFARIA_API}/index/{tractate}"
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Get the length information from schema
            schema = data.get('schema', {})
            lengths = schema.get('lengths', [])

            # Generate references for Talmud pages (2a, 2b, 3a, 3b, etc.)
            # Talmud starts at page 2 and each page has 2 sides (a and b)
            refs = []
            if lengths:
                # For Talmud, lengths[0] is the total number of amudim (page sides)
                total_amudim = lengths[0] if lengths else 0

                # Starting page is 2 (Talmud convention)
                # Each page has 2 sides: a and b
                page_num = 2
                for i in range(total_amudim):
                    side = 'a' if i % 2 == 0 else 'b'
                    refs.append(f"{tractate} {page_num}{side}")
                    if side == 'b':
                        page_num += 1

            return refs
        except Exception as e:
            print(f"  Error getting structure for {tractate}: {e}")
            return []

    def get_text(self, ref: str) -> Optional[Dict[str, Any]]:
        """Get full text for a reference"""
        if ref in self.cache:
            return self.cache[ref]

        url = f"{SEFARIA_API}/texts/{ref}"
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            self.cache[ref] = data
            return data
        except Exception as e:
            print(f"  Error fetching {ref}: {e}")
            return None

    def get_combined_text(self, refs: List[str]) -> Optional[Dict[str, Any]]:
        """
        Get combined text from multiple consecutive references.
        For multi-page story detection (e.g., 2a→2b→3a).
        """
        combined_english = []
        combined_hebrew = []

        for ref in refs:
            text_data = self.get_text(ref)
            if not text_data:
                continue

            # Collect English
            eng = text_data.get('text', '')
            if isinstance(eng, list):
                eng = ' '.join(str(t) for t in eng if t)
            if eng:
                combined_english.append(eng)

            # Collect Hebrew
            heb = text_data.get('he', '')
            if isinstance(heb, list):
                heb = ' '.join(str(t) for t in heb if t)
            if heb:
                combined_hebrew.append(heb)

        if not combined_english and not combined_hebrew:
            return None

        return {
            'text': ' '.join(combined_english),
            'he': ' '.join(combined_hebrew),
            'refs': refs,
            'combined': True
        }

    def search_tractate_systematically(self, tractate: str, order: str,
                                      sample_rate: int = 1) -> List[Dict[str, Any]]:
        """
        Systematically analyze a tractate for narrative content.
        Uses multi-page windowing to catch stories spanning 2a→2b→3a.
        sample_rate: analyze every Nth section (1 = all sections, 2 = every other, etc.)
        """
        print(f"\n{'='*60}")
        print(f"Analyzing {tractate} ({order}) for narrative structure...")
        if self.use_windowing:
            print("Using multi-page windowing to detect stories spanning pages")
        print(f"{'='*60}")

        stories = []
        seen_story_keys = set()  # For deduplication

        # Get all references in tractate
        refs = self.get_tractate_structure(tractate)
        if not refs:
            print(f"  Could not get structure, trying page-based approach...")
            # Fallback: try common page ranges
            refs = [f"{tractate} {page}a" for page in range(2, 100)]

        # Sample refs based on sample_rate
        refs = refs[::sample_rate]

        print(f"  Analyzing {len(refs)} sections...")
        analyzed_count = 0

        # PASS 1: Analyze individual pages
        for i, ref in enumerate(refs):
            text_data = self.get_text(ref)
            if not text_data:
                continue

            # Get both English and Hebrew text
            english_text = text_data.get('text', '')
            hebrew_text = text_data.get('he', '')

            # Convert lists to strings
            if isinstance(english_text, list):
                english_text = ' '.join(str(t) for t in english_text if t)
            if isinstance(hebrew_text, list):
                hebrew_text = ' '.join(str(t) for t in hebrew_text if t)

            # Skip if both are too short
            if (not english_text or len(english_text) < 50) and (not hebrew_text or len(hebrew_text) < 50):
                continue

            # Truncate if too long (keep both under reasonable size)
            if len(english_text) > 2500:
                english_text = english_text[:2500] + "..."
            if len(hebrew_text) > 2500:
                hebrew_text = hebrew_text[:2500] + "..."

            # Analyze with AI - use both languages
            analysis = self.analyzer.analyze_narrative_structure(english_text, ref, hebrew_text)

            # Process each story found on this page
            total_stories = analysis.get('total_stories', 0)
            stories_found = analysis.get('stories_found', [])

            if total_stories > 0:
                print(f"  Found {total_stories} {'story' if total_stories == 1 else 'stories'} on {ref}")

            for story_data in stories_found:
                # Extract just the story text using boundaries
                story_english = self.extract_story_text(
                    english_text,
                    story_data.get('story_start_english', ''),
                    story_data.get('story_end_english', ''),
                    language="english"
                )

                story_hebrew = self.extract_story_text(
                    hebrew_text,
                    story_data.get('story_start_hebrew', ''),
                    story_data.get('story_end_hebrew', ''),
                    language="hebrew"
                )

                # If extraction failed, fall back to full text with warning
                if not story_english and not story_hebrew:
                    print(f"  ⚠️  Story extraction failed - using full page text as fallback")
                    story_english = english_text
                    story_hebrew = hebrew_text

                # Create story entry
                story_number = story_data.get('story_number', 1)
                story_key = self._create_story_key(story_english or english_text, f"{ref}_story{story_number}")

                if story_key not in seen_story_keys:
                    seen_story_keys.add(story_key)
                    stories.append({
                        'ref': ref,
                        'story_number': story_number,
                        'book': tractate,
                        'text': story_english if story_english else english_text,
                        'hebrew_text': story_hebrew if story_hebrew else hebrew_text,
                        'analysis': story_data,
                        'spans_multiple_pages': False
                    })
                    confidence = story_data.get('confidence', 0)
                    story_type = story_data.get('story_type', 'unknown')
                    summary = story_data.get('one_sentence_summary', '')[:60]
                    print(f"    ✓ Story {story_number}: {story_type} (confidence: {confidence}%) - {summary}...")

            # PASS 2: Check for continuation and analyze with next page if needed
            if self.use_windowing and i < len(refs) - 1:
                # Check if any story seems incomplete
                has_incomplete = any(
                    story.get('continuation', {}).get('seems_incomplete', False)
                    for story in stories_found
                )

                if has_incomplete:
                    # Story might continue to next page
                    next_ref = refs[i + 1]
                    combined_data = self.get_combined_text([ref, next_ref])

                    if combined_data:
                        comb_eng = combined_data['text']
                        comb_heb = combined_data['he']

                        # Truncate combined text if too long
                        if len(comb_eng) > 4000:
                            comb_eng = comb_eng[:4000] + "..."
                        if len(comb_heb) > 4000:
                            comb_heb = comb_heb[:4000] + "..."

                        combined_ref = f"{ref}-{next_ref.split()[-1]}"
                        combined_analysis = self.analyzer.analyze_narrative_structure(
                            comb_eng, combined_ref, comb_heb
                        )

                        # Process each story from the combined pages
                        for combined_story in combined_analysis.get('stories_found', []):
                            # Extract story text
                            story_eng = self.extract_story_text(
                                comb_eng,
                                combined_story.get('story_start_english', ''),
                                combined_story.get('story_end_english', ''),
                                language="english"
                            )
                            story_heb = self.extract_story_text(
                                comb_heb,
                                combined_story.get('story_start_hebrew', ''),
                                combined_story.get('story_end_hebrew', ''),
                                language="hebrew"
                            )

                            # Use combined text if extraction fails
                            if not story_eng and not story_heb:
                                story_eng = comb_eng
                                story_heb = comb_heb

                            # Add if not already seen and higher confidence
                            story_key = self._create_story_key(story_eng or comb_eng, combined_ref)
                            if story_key not in seen_story_keys:
                                # Only add if significantly better than single-page version
                                if combined_story.get('confidence', 0) > 75:
                                    seen_story_keys.add(story_key)
                                    stories.append({
                                        'ref': combined_ref,
                                        'story_number': combined_story.get('story_number', 1),
                                        'book': tractate,
                                        'text': story_eng or comb_eng,
                                        'hebrew_text': story_heb or comb_heb,
                                        'analysis': combined_story,
                                        'spans_multiple_pages': True
                                    })
                                    print(f"  ✓✓ {combined_ref} - MULTI-PAGE (confidence: {combined_story.get('confidence')}%)")

            analyzed_count += 1
            if analyzed_count % 10 == 0:
                print(f"    ... analyzed {analyzed_count}/{len(refs)} sections")

            time.sleep(0.3)  # Rate limiting

        print(f"  Found {len(stories)} stories in {tractate}")
        multi_page = sum(1 for s in stories if s.get('spans_multiple_pages'))
        if multi_page > 0:
            print(f"  ({multi_page} span multiple pages)")
        return stories

    def _create_story_key(self, text: str, ref: str) -> str:
        """Create a unique key for story deduplication"""
        # Use first 200 chars + ref as key to avoid duplicate stories
        text_snippet = text[:200].strip() if text else ""
        return f"{text_snippet}:{ref}"

    def search_all_tractates(self, sample_rate: int = 2):
        """Search all Talmud tractates for stories"""
        all_stories = []

        for order, tractates in TALMUD_TRACTATES.items():
            print(f"\n\n{'#'*60}")
            print(f"# ORDER: {order}")
            print(f"{'#'*60}")

            for tractate in tractates:
                try:
                    stories = self.search_tractate_systematically(tractate, order, sample_rate)
                    all_stories.extend(stories)
                    time.sleep(1)  # Rate limiting between tractates

                except Exception as e:
                    print(f"  Error processing {tractate}: {e}")

        return all_stories

    def save_results(self, stories: List[Dict[str, Any]], filename: str = "talmud_stories.json"):
        """Save results to JSON file"""
        output = {
            'total_stories': len(stories),
            'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'definition': 'Literary Stories - any narrative arc with beginning, middle, and end',
            'stories': sorted(stories, key=lambda x: x['analysis']['confidence'], reverse=True)
        }

        Path(filename).write_text(json.dumps(output, indent=2, ensure_ascii=False))
        print(f"\n\n{'='*60}")
        print(f"Results saved to {filename}")
        print(f"Total stories found: {len(stories)}")
        print(f"{'='*60}")


def main():
    """Main execution"""
    print("=" * 70)
    print("Talmud Stories Finder - Semantic Narrative Detection")
    print("=" * 70)
    print("\nDefinition: 'Literary Stories' - any narrative arc with")
    print("beginning, middle, and end (including brief vignettes)\n")

    # Check for API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        print("✓ Anthropic API key found - using AI narrative analysis")
        model_choice = input("Model (haiku/sonnet, default=haiku): ").strip().lower()
        if model_choice == "sonnet":
            model = "claude-3-5-sonnet-20241022"
        else:
            model = "claude-3-5-haiku-20241022"
    else:
        print("⚠️  No API key - using heuristic analysis")
        print("For better results, set ANTHROPIC_API_KEY environment variable\n")
        model = None

    analyzer = NarrativeAnalyzer(api_key=api_key, model=model) if model else NarrativeAnalyzer()
    finder = SefariaStoryFinder(analyzer)

    # Search options
    print("\nOptions:")
    print("1. Search all tractates (comprehensive, ~2-4 hours with AI)")
    print("2. Search specific tractate")
    print("3. Search story-rich tractates (Taanit, Berakhot, Sanhedrin)")

    choice = input("\nEnter choice (1-3, default=3): ").strip() or "3"

    if choice == "1":
        sample = input("Sample rate (1=all, 2=every other, 3=every third, default=2): ").strip() or "2"
        stories = finder.search_all_tractates(sample_rate=int(sample))
    elif choice == "2":
        tractate = input("Enter tractate name (e.g., 'Berakhot'): ").strip()
        sample = input("Sample rate (1=all sections, 2=every other, default=1): ").strip() or "1"
        stories = finder.search_tractate_systematically(tractate, "Custom", sample_rate=int(sample))
    else:  # Default to story-rich tractates
        story_rich = ["Taanit", "Berakhot", "Sanhedrin"]
        stories = []
        sample = input("Sample rate (1=all, 2=every other, default=1): ").strip() or "1"
        for tractate in story_rich:
            stories.extend(finder.search_tractate_systematically(
                tractate, "Selected", sample_rate=int(sample)
            ))
            time.sleep(2)

    # Save results
    finder.save_results(stories)

    # Print top stories
    print("\n\nTop Story Passages Found:")
    print("=" * 70)
    for story in sorted(stories, key=lambda x: x['analysis']['confidence'], reverse=True)[:15]:
        analysis = story['analysis']
        print(f"\n📖 {story['ref']}")
        print(f"   Type: {analysis['story_type']} (Confidence: {analysis['confidence']}%)")
        if analysis.get('one_sentence_summary'):
            print(f"   Summary: {analysis['one_sentence_summary']}")
        print(f"   Elements: {', '.join(k for k, v in analysis['narrative_elements'].items() if v)}")
        preview = story['text'][:150] + "..." if len(story['text']) > 150 else story['text']
        print(f"   Preview: {preview}")


if __name__ == "__main__":
    main()
