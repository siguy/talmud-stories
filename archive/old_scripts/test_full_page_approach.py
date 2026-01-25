#!/usr/bin/env python3
"""
Test script for Full Page Storage approach.
Stores complete page text with TEXT ANCHOR boundaries.
Uses a small test set of 10-15 pages for rapid iteration.

KEY INSIGHT: LLMs cannot reliably provide character offsets.
Instead, we ask for text anchors (first/last words of story)
and find their positions programmatically.
"""

import requests
import json
import time
import os
import re
from typing import List, Dict, Any, Optional, Tuple

# Import Google Generative AI
try:
    import google.generativeai as genai
    GOOGLE_AI_AVAILABLE = True
except ImportError:
    GOOGLE_AI_AVAILABLE = False
    print("Run: pip install google-generativeai")

SEFARIA_API = "https://www.sefaria.org/api"

# Test set: Known story-rich pages + edge cases
# Mix of: known stories, multiple stories, no stories, edge cases
TEST_PAGES = [
    "Ketubot 8b",   # Known story: mourning narratives
    "Ketubot 10b",  # Known: 3 stories (Jeff validated)
    "Ketubot 20b",  # Known story: Rav Ashi memory (Jeff validated)
    "Ketubot 62b",  # Known: Rav Rehumi story (wife distress)
    "Ketubot 67b",  # Known: 4 stories (Hillel, charity)
    "Ketubot 103b", # Known: Rabbi Yehuda HaNasi death narratives
    "Ketubot 104a", # Continuation of death narratives
    "Ketubot 2a",   # Known FALSE POSITIVE: legal discussion (Jeff validated)
    "Ketubot 3a",   # Known FALSE POSITIVE: legal hypothetical (Jeff validated)
    "Ketubot 3b",   # Known FALSE POSITIVE: legal discussion (Jeff validated)
]


def get_full_page_text(ref: str) -> Optional[Dict[str, Any]]:
    """
    Fetch COMPLETE page text from Sefaria - both English and Hebrew.
    Returns the full text without any truncation.
    """
    url = f"{SEFARIA_API}/texts/{ref}"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()

        # Get English - handle both string and list formats
        english = data.get('text', '')
        if isinstance(english, list):
            # Join all segments with proper spacing
            english = ' '.join(str(t) for t in english if t)

        # Get Hebrew - handle both string and list formats
        hebrew = data.get('he', '')
        if isinstance(hebrew, list):
            # Join all segments with proper spacing
            hebrew = ' '.join(str(t) for t in hebrew if t)

        # Clean up whitespace
        english = re.sub(r'\s+', ' ', english.strip())
        hebrew = re.sub(r'\s+', ' ', hebrew.strip())

        return {
            'ref': ref,
            'full_english': english,
            'full_hebrew': hebrew,
            'english_length': len(english),
            'hebrew_length': len(hebrew)
        }
    except Exception as e:
        print(f"  Error fetching {ref}: {e}")
        return None


def normalize_hebrew(text: str) -> str:
    """Remove Hebrew vowel marks (nikud) and normalize for matching."""
    import unicodedata
    # Normalize unicode
    text = unicodedata.normalize('NFC', text)
    # Remove Hebrew vowel points (nikud) - Unicode range 0x0591 to 0x05C7
    text = re.sub(r'[\u0591-\u05C7]', '', text)
    return text


def find_anchor_position(text: str, anchor: str, search_from: int = 0) -> Tuple[int, int]:
    """
    Find the position of an anchor text within the full text.
    Uses fuzzy matching to handle minor variations.
    Returns (start_pos, end_pos) or (-1, -1) if not found.
    """
    if not anchor or not text:
        return (-1, -1)

    # Clean anchor: remove extra whitespace, normalize
    anchor_clean = re.sub(r'\s+', ' ', anchor.strip())

    # Detect if this is Hebrew text (contains Hebrew characters)
    is_hebrew = bool(re.search(r'[\u0590-\u05FF]', anchor_clean))

    if is_hebrew:
        # For Hebrew: normalize both and do a more flexible search
        text_norm = normalize_hebrew(text)
        anchor_norm = normalize_hebrew(anchor_clean)

        # Try exact match on normalized text
        pos = text_norm.find(anchor_norm, search_from)
        if pos >= 0:
            return (pos, pos + len(anchor_norm))

        # Try flexible whitespace matching
        anchor_pattern = re.sub(r'\s+', r'\\s+', re.escape(anchor_norm))
        match = re.search(anchor_pattern, text_norm)
        if match:
            return (match.start(), match.end())

        # Try first few words
        words = anchor_norm.split()
        if len(words) >= 3:
            partial = ' '.join(words[:3])
            partial_pattern = re.sub(r'\s+', r'\\s+', re.escape(partial))
            match = re.search(partial_pattern, text_norm)
            if match:
                return (match.start(), match.start())

        # Try last few words (for end anchors)
        if len(words) >= 3:
            partial = ' '.join(words[-3:])
            partial_pattern = re.sub(r'\s+', r'\\s+', re.escape(partial))
            match = re.search(partial_pattern, text_norm)
            if match:
                return (match.end(), match.end())

    else:
        # For English: case-insensitive matching
        text_lower = text.lower()
        anchor_lower = anchor_clean.lower()

        # Try exact match first
        pos = text_lower.find(anchor_lower, search_from)
        if pos >= 0:
            return (pos, pos + len(anchor_clean))

        # Try matching with flexible whitespace
        anchor_pattern = re.sub(r'\s+', r'\\s+', re.escape(anchor_clean))
        match = re.search(anchor_pattern, text, re.IGNORECASE)
        if match:
            return (match.start(), match.end())

        # Try matching first few significant words (skip common words)
        words = [w for w in anchor_clean.split() if len(w) > 3]
        if len(words) >= 3:
            # Try first 3 significant words
            partial = ' '.join(words[:3])
            partial_pattern = re.sub(r'\s+', r'\\s+', re.escape(partial))
            match = re.search(partial_pattern, text, re.IGNORECASE)
            if match:
                return (match.start(), match.start())  # Return start only

    return (-1, -1)


def extract_story_boundaries(full_english: str, full_hebrew: str, story: Dict) -> Dict:
    """
    Given AI-provided anchor texts, find actual character positions in the full text.
    """
    # Get anchor texts from AI response
    start_anchor_e = story.get('story_start_anchor_english', '')
    end_anchor_e = story.get('story_end_anchor_english', '')
    start_anchor_h = story.get('story_start_anchor_hebrew', '')
    end_anchor_h = story.get('story_end_anchor_hebrew', '')

    # Find positions in English text
    start_e, _ = find_anchor_position(full_english, start_anchor_e)
    _, end_e = find_anchor_position(full_english, end_anchor_e, start_e if start_e >= 0 else 0)

    # If end not found, try to estimate from start anchor
    if end_e < 0 and start_e >= 0:
        # Use a reasonable story length estimate (2000 chars)
        end_e = min(start_e + 2000, len(full_english))

    # Find positions in Hebrew text
    start_h, _ = find_anchor_position(full_hebrew, start_anchor_h)
    _, end_h = find_anchor_position(full_hebrew, end_anchor_h, start_h if start_h >= 0 else 0)

    # If end not found, estimate from start
    if end_h < 0 and start_h >= 0:
        end_h = min(start_h + 1000, len(full_hebrew))

    return {
        'story_start_char_english': start_e,
        'story_end_char_english': end_e,
        'story_start_char_hebrew': start_h,
        'story_end_char_hebrew': end_h,
        'english_found': start_e >= 0 and end_e > start_e,
        'hebrew_found': start_h >= 0 and end_h > start_h,
    }


def analyze_page_with_anchors(full_english: str, full_hebrew: str, ref: str, model) -> Dict[str, Any]:
    """
    Analyze a page and return story boundaries as TEXT ANCHORS.
    We ask for exact text quotes, then find their positions programmatically.
    """

    prompt = f"""Analyze this Talmudic passage and identify ALL "Literary Stories" it contains.

CRITICAL: For each story, provide TEXT ANCHORS - exact quotes from the text marking where the story begins and ends.

For each story, provide:
- story_start_anchor_english: Copy EXACTLY the first 10-15 words where the story BEGINS in English
- story_end_anchor_english: Copy EXACTLY the last 10-15 words where the story ENDS in English
- story_start_anchor_hebrew: Copy EXACTLY the first 5-8 words where the story BEGINS in Hebrew
- story_end_anchor_hebrew: Copy EXACTLY the last 5-8 words where the story ENDS in Hebrew

STORY CRITERIA (all must be met):
1. DESCRIPTIVE (what DID happen), not prescriptive (what should happen)
2. ONE-TIME SPECIFIC EVENT with named individuals
3. AT LEAST 2 EVENTS with CAUSAL relationship (A caused B)
4. CHANGE or outcome (before → after state)
5. POST-BIBLICAL characters (rabbis, not Moses/David)
6. ACTUAL event (not hypothetical "if X then Y")

NOT STORIES:
- Legal rules ("A virgin is married on Wednesday")
- Hypothetical cases ("If a man does X, then Y")
- Legal debates without narrative
- Single events without causality
- Habitual actions ("Rabbi X would always...")

═══════════════════════════════════════════════════════════════════════════════
Passage Reference: {ref}

ENGLISH TEXT:
{full_english}

HEBREW TEXT:
{full_hebrew}
═══════════════════════════════════════════════════════════════════════════════

Respond in JSON format:
{{
  "total_stories": <number>,
  "page_summary": "brief description of what this page contains",
  "stories": [
    {{
      "story_number": 1,
      "story_start_anchor_english": "exact first 10-15 words of story from English text",
      "story_end_anchor_english": "exact last 10-15 words of story from English text",
      "story_start_anchor_hebrew": "exact first 5-8 words from Hebrew text",
      "story_end_anchor_hebrew": "exact last 5-8 words from Hebrew text",
      "confidence": 0-100,
      "story_type": "full_narrative" | "dialogue_vignette" | "brief_anecdote",
      "one_sentence_summary": "brief description",
      "reasoning": "why this is a story - mention causality and change",
      "validation_notes": "which criteria were met"
    }}
  ]
}}

If NO stories found, return: {{"total_stories": 0, "page_summary": "...", "stories": []}}

IMPORTANT: Copy anchor text EXACTLY as it appears, including any HTML tags like <b> or <i>."""

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=4096,
                temperature=0.1,
            ),
            request_options={"timeout": 60}
        )

        content = response.candidates[0].content.parts[0].text

        # Parse JSON from response
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0]
        elif '```' in content:
            parts = content.split('```')
            if len(parts) >= 2:
                content = parts[1]

        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            return json.loads(content[json_start:json_end])

        return {"total_stories": 0, "stories": [], "error": "Could not parse response"}

    except Exception as e:
        print(f"  AI error: {e}")
        return {"total_stories": 0, "stories": [], "error": str(e)}


def run_test():
    """Run the full page approach test on our test set."""

    # Check for API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: Set GOOGLE_API_KEY environment variable")
        return

    if not GOOGLE_AI_AVAILABLE:
        print("ERROR: Install google-generativeai package")
        return

    # Initialize Gemini
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")

    print("=" * 70)
    print("Full Page Storage Approach - Test Run")
    print("=" * 70)
    print(f"Testing {len(TEST_PAGES)} pages")
    print()

    results = []

    for ref in TEST_PAGES:
        print(f"\n{'─' * 50}")
        print(f"Processing: {ref}")
        print(f"{'─' * 50}")

        # Get full page text
        page_data = get_full_page_text(ref)
        if not page_data:
            print(f"  SKIP: Could not fetch page")
            continue

        print(f"  English: {page_data['english_length']} chars")
        print(f"  Hebrew:  {page_data['hebrew_length']} chars")

        # Analyze with AI - get text anchors
        analysis = analyze_page_with_anchors(
            page_data['full_english'],
            page_data['full_hebrew'],
            ref,
            model
        )

        print(f"  Stories found: {analysis.get('total_stories', 0)}")

        # Process each story: convert anchors to character positions
        for story in analysis.get('stories', []):
            boundaries = extract_story_boundaries(
                page_data['full_english'],
                page_data['full_hebrew'],
                story
            )
            # Add computed boundaries to story
            story.update(boundaries)

        # Build result with full page storage
        result = {
            'ref': ref,
            'full_english': page_data['full_english'],
            'full_hebrew': page_data['full_hebrew'],
            'english_length': page_data['english_length'],
            'hebrew_length': page_data['hebrew_length'],
            'analysis': analysis
        }

        # Validate and show boundaries for each story
        for story in analysis.get('stories', []):
            sn = story.get('story_number', '?')
            conf = story.get('confidence', 0)
            stype = story.get('story_type', 'unknown')
            summary = story.get('one_sentence_summary', '')[:50]

            # Get computed boundary info
            start_e = story.get('story_start_char_english', -1)
            end_e = story.get('story_end_char_english', -1)
            start_h = story.get('story_start_char_hebrew', -1)
            end_h = story.get('story_end_char_hebrew', -1)
            eng_found = story.get('english_found', False)
            heb_found = story.get('hebrew_found', False)

            print(f"    Story {sn}: {stype} ({conf}%)")
            print(f"      Summary: {summary}...")

            # Show anchor info
            start_anchor = story.get('story_start_anchor_english', '')[:60]
            end_anchor = story.get('story_end_anchor_english', '')[:60]
            print(f"      Start anchor: \"{start_anchor}...\"")
            print(f"      End anchor: \"{end_anchor}...\"")

            # Show computed positions
            if eng_found:
                print(f"      English: chars {start_e}-{end_e} ({end_e - start_e} chars) ✓")
            else:
                print(f"      English: NOT FOUND ✗")

            if heb_found:
                print(f"      Hebrew: chars {start_h}-{end_h} ({end_h - start_h} chars) ✓")
            else:
                print(f"      Hebrew: NOT FOUND ✗")

            # Show preview of extracted text
            if eng_found and start_e >= 0 and end_e > start_e:
                preview = page_data['full_english'][start_e:min(start_e+120, end_e)]
                print(f"      Preview: {preview}...")

        results.append(result)
        time.sleep(0.5)  # Rate limiting

    # Save results
    output = {
        'test_run': True,
        'approach': 'full_page_storage_with_text_anchors',
        'total_pages': len(results),
        'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
        'pages': results
    }

    output_file = 'test_full_page_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 70}")
    print(f"Results saved to: {output_file}")
    print(f"Total pages analyzed: {len(results)}")

    # Summary
    total_stories = sum(p['analysis'].get('total_stories', 0) for p in results)
    print(f"Total stories found: {total_stories}")
    print(f"{'=' * 70}")

    return results


if __name__ == "__main__":
    run_test()
