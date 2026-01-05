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

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-5-haiku-20241022"):
        """
        Initialize with Anthropic API key.
        Falls back to ANTHROPIC_API_KEY environment variable.
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model
        self.api_url = "https://api.anthropic.com/v1/messages"

        if not self.api_key:
            print("\n⚠️  WARNING: No Anthropic API key found.")
            print("Set ANTHROPIC_API_KEY environment variable or pass api_key parameter.")
            print("Falling back to basic heuristic analysis.\n")

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

        prompt = f"""Analyze this Talmudic passage and determine if it contains a "Literary Story."

Definition: A "Literary Story" is any narrative arc with a beginning, middle, and end. This includes:
- Full narratives with multiple scenes
- Brief two-line dialogues with narrative progression
- Vignettes showing character actions and outcomes
- Anecdotes with temporal progression

Look for:
1. Beginning: Setup, characters introduced, situation established
2. Middle: Action, dialogue, conflict, or change
3. End: Resolution, conclusion, or outcome

Even a brief exchange like "Rabbi X asked Rabbi Y a question. Rabbi Y replied with a parable" can be a story if it has this arc.

DO NOT count:
- Pure legal discussions without narrative
- Abstract philosophical debates
- Lists of rulings without context
- Bare statements of law

Passage Reference: {ref}

{text_section}

Respond in JSON format:
{{
  "is_story": true/false,
  "confidence": 0-100,
  "narrative_elements": {{
    "has_beginning": true/false,
    "has_middle": true/false,
    "has_end": true/false,
    "has_characters": true/false,
    "has_action": true/false,
    "has_dialogue": true/false,
    "has_temporal_progression": true/false
  }},
  "story_type": "full_narrative" | "dialogue_vignette" | "brief_anecdote" | "not_a_story",
  "one_sentence_summary": "brief description if is_story is true, else empty string",
  "reasoning": "brief explanation of your classification",
  "continuation": {{
    "seems_incomplete": true/false,
    "missing_beginning": true/false,
    "missing_end": true/false,
    "note": "explanation if story appears to continue beyond this passage or starts mid-narrative"
  }}
}}"""

        try:
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
            content = result["content"][0]["text"]

            # Extract JSON from response
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                analysis = json.loads(content[json_start:json_end])
                return analysis
            else:
                print(f"  ⚠️  Could not parse AI response for {ref}")
                return self._heuristic_analysis(text, ref)

        except Exception as e:
            print(f"  ⚠️  AI analysis failed for {ref}: {e}")
            return self._heuristic_analysis(text, ref)

    def _heuristic_analysis(self, text: str, ref: str) -> Dict[str, Any]:
        """Fallback heuristic analysis when AI is unavailable"""
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

        return {
            "is_story": narrative_count >= 2,
            "confidence": min(narrative_count * 25, 75),  # Max 75 for heuristic
            "narrative_elements": {
                "has_beginning": has_temporal or has_characters,
                "has_middle": has_action or has_dialogue,
                "has_end": has_dialogue,  # Approximation
                "has_characters": has_characters,
                "has_action": has_action,
                "has_dialogue": has_dialogue,
                "has_temporal_progression": has_temporal
            },
            "story_type": "heuristic_detection" if narrative_count >= 2 else "not_a_story",
            "one_sentence_summary": "",
            "reasoning": f"Heuristic analysis: {narrative_count}/4 narrative markers found"
        }


class SefariaStoryFinder:
    """Find stories in Talmud using semantic narrative detection"""

    def __init__(self, analyzer: NarrativeAnalyzer, use_windowing: bool = True):
        self.analyzer = analyzer
        self.session = requests.Session()
        self.cache = {}
        self.use_windowing = use_windowing  # Enable multi-page story detection

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

            if analysis['is_story']:
                story_key = self._create_story_key(english_text, ref)
                if story_key not in seen_story_keys:
                    seen_story_keys.add(story_key)
                    stories.append({
                        'ref': ref,
                        'book': tractate,
                        'text': english_text,
                        'hebrew_text': hebrew_text if hebrew_text else None,
                        'analysis': analysis,
                        'spans_multiple_pages': False
                    })
                    confidence = analysis['confidence']
                    story_type = analysis['story_type']
                    print(f"  ✓ {ref} - {story_type} (confidence: {confidence}%)")

            # PASS 2: Check for continuation and analyze with next page if needed
            if self.use_windowing and i < len(refs) - 1:
                continuation = analysis.get('continuation', {})
                if continuation.get('seems_incomplete') or continuation.get('missing_end'):
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

                        # If combined version has higher confidence and complete story, use it
                        if combined_analysis['is_story'] and combined_analysis['confidence'] > analysis['confidence'] + 10:
                            if not combined_analysis.get('continuation', {}).get('seems_incomplete'):
                                story_key = self._create_story_key(comb_eng, combined_ref)
                                if story_key not in seen_story_keys:
                                    seen_story_keys.add(story_key)
                                    stories.append({
                                        'ref': combined_ref,
                                        'book': tractate,
                                        'text': comb_eng,
                                        'hebrew_text': comb_heb if comb_heb else None,
                                        'analysis': combined_analysis,
                                        'spans_multiple_pages': True
                                    })
                                    print(f"  ✓✓ {combined_ref} - MULTI-PAGE {combined_analysis['story_type']} (confidence: {combined_analysis['confidence']}%)")

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
