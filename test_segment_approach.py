#!/usr/bin/env python3
"""
Comprehensive Segment-Based Story Detection
Combines:
- Idea D: Enhanced prompt with Jeff's criteria
- Idea E: Segment-based detection with Hebrew marker pre-processing
- Idea F: Segment boundary intelligence for multi-segment stories
"""

import requests
import json
import time
import os
import re
from typing import List, Dict, Any, Optional, Tuple

try:
    import google.generativeai as genai
    GOOGLE_AI_AVAILABLE = True
except ImportError:
    GOOGLE_AI_AVAILABLE = False
    print("Run: pip install google-generativeai")

SEFARIA_API = "https://www.sefaria.org/api"

# Test pages: mix of known stories and known false positives
TEST_PAGES = [
    "Ketubot 62b",  # Known: multiple stories (Rav Rehumi, etc.)
    "Ketubot 2a",   # Known FALSE POSITIVE (Jeff validated)
    "Ketubot 10b",  # Known: 3 stories (Jeff validated)
    "Ketubot 67b",  # Known: Hillel charity stories
]


def fetch_page_segments(ref: str) -> Optional[Dict[str, Any]]:
    """
    Fetch page from Sefaria with SEGMENTS PRESERVED.
    Returns aligned English and Hebrew segment arrays.
    """
    url = f"{SEFARIA_API}/texts/{ref}"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()

        text_segments = data.get('text', [])
        hebrew_segments = data.get('he', [])

        # Handle nested lists (some pages have deeper structure)
        if text_segments and isinstance(text_segments[0], list):
            text_segments = [item for sublist in text_segments for item in sublist]
            hebrew_segments = [item for sublist in hebrew_segments for item in sublist]

        # Ensure both arrays are same length
        min_len = min(len(text_segments), len(hebrew_segments))

        return {
            'ref': ref,
            'he_ref': data.get('heRef', ''),
            'segments': [
                {
                    'index': i,
                    'english': str(text_segments[i]) if text_segments[i] else '',
                    'hebrew': str(hebrew_segments[i]) if hebrew_segments[i] else ''
                }
                for i in range(min_len)
            ],
            'total_segments': min_len
        }
    except Exception as e:
        print(f"  Error fetching {ref}: {e}")
        return None


def detect_hebrew_markers(hebrew_text: str) -> Dict[str, List[str]]:
    """
    Detect Hebrew narrative markers in a segment.
    Returns categorized markers found.
    """
    markers = {
        'story': [],
        'dialogue': [],
        'temporal': [],
        'outcome': [],
        'legal': [],
        'hypothetical': []
    }

    # Normalize for matching (remove some nikud)
    h = hebrew_text

    # STORY MARKERS (strong positive signals)
    if 'מעשה' in h:
        markers['story'].append('מעשה')
    if 'כי הא ד' in h or 'כִּי הָא דְּ' in h:
        markers['story'].append('כי_הא_ד')
    if 'פעם אחת' in h:
        markers['story'].append('פעם_אחת')
    if 'יומא חד' in h or 'יוֹמָא חַד' in h:
        markers['story'].append('יומא_חד')
    if 'זמנא חדא' in h:
        markers['story'].append('זמנא_חדא')

    # DIALOGUE MARKERS
    if 'אמר ליה' in h or 'אֲמַר לֵיהּ' in h:
        markers['dialogue'].append('אמר_ליה')
    if 'אמר לה' in h or 'אָמַר לָהּ' in h:
        markers['dialogue'].append('אמר_לה')
    if 'אמרה ליה' in h:
        markers['dialogue'].append('אמרה_ליה')
    if 'א"ל' in h:
        markers['dialogue'].append('א"ל')

    # TEMPORAL MARKERS
    if 'לסוף' in h or 'לְסוֹף' in h:
        markers['temporal'].append('לסוף')
    if 'לבסוף' in h:
        markers['temporal'].append('לבסוף')
    if 'למחר' in h:
        markers['temporal'].append('למחר')
    if 'באותה שעה' in h:
        markers['temporal'].append('באותה_שעה')

    # OUTCOME MARKERS
    if 'נח נפשיה' in h or 'נָח נַפְשֵׁיהּ' in h:
        markers['outcome'].append('נח_נפשיה')
    if 'נפטר' in h:
        markers['outcome'].append('נפטר')
    if 'נתרפא' in h:
        markers['outcome'].append('נתרפא')

    # LEGAL MARKERS (negative signals)
    if 'מתני' in h or 'מַתְנִי' in h:
        markers['legal'].append('mishna')
    if 'הלכה' in h or 'הֲלָכָה' in h:
        markers['legal'].append('halakha')
    if 'תנו רבנן' in h:
        markers['legal'].append('tanu_rabanan')

    return markers


def detect_english_markers(english_text: str) -> Dict[str, List[str]]:
    """
    Detect English narrative markers in a segment.
    """
    markers = {
        'story': [],
        'dialogue': [],
        'legal': [],
        'hypothetical': []
    }

    e = english_text

    # Story intro patterns
    if 'It is related' in e:
        markers['story'].append('it_is_related')
    if 'There was an incident' in e:
        markers['story'].append('incident')
    if 'A certain' in e and ('came before' in e or 'person' in e):
        markers['story'].append('certain_person')
    if e.startswith('This is <b>as</b>'):
        markers['story'].append('this_is_as')

    # Legal markers
    if 'MISHNA' in e or 'mishna stated' in e.lower():
        markers['legal'].append('mishna')
    if 'The halakha is' in e or 'the <i>halakha</i>' in e:
        markers['legal'].append('halakha')

    # Hypothetical markers
    if re.search(r'\bIf\s+\w+\s+were\s+to', e):
        markers['hypothetical'].append('if_were_to')
    if 'What if' in e:
        markers['hypothetical'].append('what_if')
    if 'One might think' in e:
        markers['hypothetical'].append('might_think')

    return markers


def calculate_story_likelihood(heb_markers: Dict, eng_markers: Dict) -> str:
    """
    Calculate likelihood that a segment contains a story.
    """
    score = 0

    # Strong positive signals
    if heb_markers['story']:
        score += 40
    if eng_markers['story']:
        score += 30
    if heb_markers['dialogue']:
        score += 10
    if heb_markers['temporal']:
        score += 10
    if heb_markers['outcome']:
        score += 15

    # Negative signals
    if heb_markers['legal'] or eng_markers['legal']:
        score -= 30
    if eng_markers['hypothetical']:
        score -= 25

    if score >= 30:
        return 'HIGH'
    elif score >= 10:
        return 'MEDIUM'
    else:
        return 'LOW'


def preprocess_segments(segments: List[Dict]) -> List[Dict]:
    """
    Pre-process all segments with marker detection.
    """
    processed = []
    for seg in segments:
        heb_markers = detect_hebrew_markers(seg['hebrew'])
        eng_markers = detect_english_markers(seg['english'])
        likelihood = calculate_story_likelihood(heb_markers, eng_markers)

        processed.append({
            'index': seg['index'],
            'english': seg['english'],
            'hebrew': seg['hebrew'],
            'hebrew_markers': heb_markers,
            'english_markers': eng_markers,
            'story_likelihood': likelihood,
            'all_markers': {
                'story': heb_markers['story'] + eng_markers['story'],
                'dialogue': heb_markers['dialogue'],
                'temporal': heb_markers['temporal'],
                'outcome': heb_markers['outcome'],
                'legal': heb_markers['legal'] + eng_markers['legal'],
                'hypothetical': eng_markers['hypothetical']
            }
        })
    return processed


def extract_characters(english_text: str) -> List[str]:
    """
    Extract character names from English text.
    Returns list of rabbi/character names found.
    """
    characters = []

    # Common rabbi name patterns
    patterns = [
        r'(?:Rabbi|Rav|Rabban|Mar)\s+[A-Z][a-z]+(?:\s+(?:bar|ben|son of)\s+[A-Z][a-z]+)?',
        r'(?:Rabbi|Rav)\s+[A-Z][a-z]+\s+[A-Z][a-z]+',  # Rabbi Yehuda HaNasi
        r'Reish Lakish',
        r'Abaye',
        r'Rava(?!\s+in)',  # Rava but not "Rava in Mehoza"
    ]

    for pattern in patterns:
        matches = re.findall(pattern, english_text)
        characters.extend(matches)

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for c in characters:
        c_clean = c.strip()
        if c_clean not in seen:
            seen.add(c_clean)
            unique.append(c_clean)

    return unique


def detect_continuations(segments: List[Dict]) -> List[Tuple[int, int]]:
    """
    Idea F (Strengthened): Detect segments that continue from previous segment.
    Uses multiple signals: continuation words, shared characters, narrative flow.
    Returns list of (segment_index, continues_from_index) tuples.
    """
    continuations = []

    # Strong continuation starters (pronouns referring back)
    pronoun_starters = ['He ', 'She ', 'They ', 'His ', 'Her ']

    # Narrative flow indicators
    flow_starters = [
        'When he', 'When she', 'When they',
        'After', 'By the time', 'The next day',
        'In the meantime', 'Meanwhile',
        'Ultimately', 'Finally', 'Eventually',
    ]

    # New story indicators (these BREAK continuation)
    new_story_indicators = [
        '§',  # Section marker
        'MISHNA', 'GEMARA',
        'It is related further that',  # New story intro
        'The Gemara relates:',
        'There was an incident',
        'A certain',  # Usually starts new story
    ]

    for i in range(1, len(segments)):
        prev_seg = segments[i-1]
        curr_seg = segments[i]
        eng = curr_seg['english']

        # Skip if current segment starts a NEW story/section
        is_new_story = any(indicator in eng[:80] for indicator in new_story_indicators)
        if is_new_story:
            continue

        # Check if previous segment is story-like
        prev_is_story = prev_seg['story_likelihood'] in ['HIGH', 'MEDIUM']

        # Signal 1: Starts with pronoun (strong continuation signal)
        starts_with_pronoun = any(eng.startswith(starter) for starter in pronoun_starters)

        # Signal 2: Starts with narrative flow word
        starts_with_flow = any(eng.startswith(starter) for starter in flow_starters)

        # Signal 3: Shared characters between segments
        prev_chars = set(extract_characters(prev_seg['english']))
        curr_chars = set(extract_characters(curr_seg['english']))
        shared_chars = prev_chars & curr_chars
        has_shared_characters = len(shared_chars) > 0

        # Signal 4: Current segment continues same rabbi's story
        # (starts with "Rabbi X" where X appeared in previous)
        rabbi_match = re.match(r'^(?:<[^>]+>)*(?:Rabbi|Rav)\s+(\w+)', eng)
        continues_same_rabbi = False
        if rabbi_match:
            rabbi_name = rabbi_match.group(1)
            continues_same_rabbi = any(rabbi_name in c for c in prev_chars)

        # Determine if this is a continuation
        is_continuation = False

        if prev_is_story:
            # Strong signals: pronoun start or narrative flow + shared characters
            if starts_with_pronoun:
                is_continuation = True
            elif starts_with_flow and (has_shared_characters or prev_seg['story_likelihood'] == 'HIGH'):
                is_continuation = True
            elif has_shared_characters and not eng.startswith('§'):
                # Same characters, not a new section
                is_continuation = True
            elif continues_same_rabbi:
                is_continuation = True

        if is_continuation:
            continuations.append((i, i-1))

    return continuations


def build_story_groups(segments: List[Dict], continuations: List[Tuple]) -> List[List[int]]:
    """
    Group segments into connected story units based on continuations.
    Returns list of segment index lists, each representing one story.
    """
    # Build adjacency from continuations
    continues_from = {c[0]: c[1] for c in continuations}

    # Find all story-likely segments
    story_segments = [s['index'] for s in segments
                      if s['story_likelihood'] in ['HIGH', 'MEDIUM']]

    # Build groups by following continuation chains
    groups = []
    used = set()

    for seg_idx in story_segments:
        if seg_idx in used:
            continue

        # Start a new group
        group = [seg_idx]
        used.add(seg_idx)

        # Follow forward continuations
        current = seg_idx
        while True:
            # Find segments that continue from current
            next_segs = [c[0] for c in continuations if c[1] == current]
            if not next_segs:
                break
            next_seg = next_segs[0]
            if next_seg not in used:
                group.append(next_seg)
                used.add(next_seg)
                current = next_seg
            else:
                break

        groups.append(sorted(group))

    return groups


def build_analysis_prompt(ref: str, processed_segments: List[Dict], continuations: List[Tuple], story_groups: List[List[int]]) -> str:
    """
    Build the enhanced prompt with all context.
    """

    # Build segment display
    segment_display = []
    for seg in processed_segments:
        markers = []
        if seg['all_markers']['story']:
            markers.append(f"STORY:{','.join(seg['all_markers']['story'])}")
        if seg['all_markers']['dialogue']:
            markers.append(f"DIAL:{','.join(seg['all_markers']['dialogue'])}")
        if seg['all_markers']['temporal']:
            markers.append(f"TIME:{','.join(seg['all_markers']['temporal'])}")
        if seg['all_markers']['outcome']:
            markers.append(f"END:{','.join(seg['all_markers']['outcome'])}")
        if seg['all_markers']['legal']:
            markers.append(f"LEGAL:{','.join(seg['all_markers']['legal'])}")
        if seg['all_markers']['hypothetical']:
            markers.append(f"HYPO:{','.join(seg['all_markers']['hypothetical'])}")

        marker_str = ' | '.join(markers) if markers else '(no markers)'
        likelihood = seg['story_likelihood']

        # Extract characters for display
        chars = extract_characters(seg['english'])
        char_str = f" CHARS:[{', '.join(chars[:3])}]" if chars else ""

        # Truncate English for display
        eng_preview = seg['english'][:150].replace('\n', ' ')

        segment_display.append(f"[Seg {seg['index']}] [{likelihood}]{char_str} [{marker_str}]\n  {eng_preview}...")

    # Note continuations and suggested groupings
    continuation_notes = ""
    if continuations:
        cont_list = [f"Seg {c[0]} continues Seg {c[1]}" for c in continuations]
        continuation_notes = f"\nDETECTED CONTINUATIONS:\n" + "\n".join(cont_list)

    # Show suggested story groups
    group_notes = ""
    if story_groups:
        group_list = [f"Suggested Story Group: Segments {g}" for g in story_groups if len(g) > 1]
        if group_list:
            group_notes = f"\n\nSUGGESTED MULTI-SEGMENT STORIES:\n" + "\n".join(group_list)

    prompt = f"""Analyze this Talmudic page to identify "Literary Stories" (aggadot/narratives).

=== JEFF RUBENSTEIN'S VALIDATED CRITERIA ===
(Based on expert Talmud scholar review)

A passage IS A STORY if it has ALL of:
✓ SPECIFIC NAMED CHARACTERS (e.g., "Rav Reḥumi", "Rabban Gamliel")
✓ DIALOGUE between characters (not just "Rabbi X said the law is...")
✓ TEMPORAL PROGRESSION (before → during → after)
✓ CAUSAL CHAIN (Event A caused Event B caused Event C)
✓ CHANGE IN SITUATION or OUTCOME (something is different at the end)
✓ DESCRIPTIVE of what DID happen (not what SHOULD happen)

A passage is NOT A STORY if it has ANY of:
✗ Hypothetical scenarios ("If X were to do Y, then Z would apply...")
✗ Legal rulings without narrative ("The halakha is...", "One is obligated...")
✗ MISHNA sections (these are almost always legal codifications)
✗ Habitual actions without specific incident ("He would always do X")
✗ Purely theoretical debates between rabbis about law

=== EXAMPLES FROM JEFF'S VALIDATION ===

TRUE STORY (Ketubot 62b - Rav Reḥumi):
"Rav Reḥumi would commonly study before Rava in Meḥoza. He was accustomed to come
home every year on the eve of Yom Kippur. One day he was engrossed in the halakha.
His wife was expecting him: 'Now he is coming, now he is coming.' He did not come.
She was distressed. A tear fell from her eye. He was sitting on the roof.
The roof collapsed under him and he died."
→ WHY IT'S A STORY: Named characters, temporal progression ("one day", "at that moment"),
  causal chain (engrossed→didn't come→wife distressed→tear→roof collapsed→died), tragic outcome.

NOT A STORY (Ketubot 2a):
"A virgin is married on Wednesday and a widow on Thursday. Due to the fact that
courts convene in towns twice a week... If he had a claim concerning virginity..."
→ WHY NOT A STORY: Legal rule (prescriptive), hypothetical scenarios throughout,
  no specific named individuals in an actual event, conditional "if X then Y" logic.

NOT A STORY (Ketubot 3a):
"If a man said to agents: Give this bill of divorce to my wife if I do not return
within thirty days, and he wanted to come but was prevented..."
→ WHY NOT A STORY: Hypothetical case construction, legal reasoning about theoretical
  scenarios, no actual event being described.

=== PRE-PROCESSED SEGMENTS WITH MARKERS ===
{chr(10).join(segment_display)}
{continuation_notes}
{group_notes}

=== YOUR TASK ===
Identify which SEGMENT RANGES contain genuine stories.

CRITICAL INSTRUCTIONS:
1. MERGE CONTINUOUS NARRATIVES: If segments 10, 11, 12, 13 all tell ONE story about
   the same character(s), report it as ONE story (start_segment: 10, end_segment: 13),
   NOT as four separate stories!

2. Use SUGGESTED MULTI-SEGMENT STORIES above as guidance - these segments likely
   belong together as one narrative.

3. A story that spans multiple segments should be reported ONCE with the full range.

4. Only count as SEPARATE stories if they involve DIFFERENT main characters or
   are clearly distinct narrative events.

5. Use the marker analysis to guide you (HIGH likelihood = likely story)

6. MISHNA segments are almost NEVER stories

7. Segments with HYPO (hypothetical) markers are usually NOT stories

8. A segment with dialogue alone is NOT enough - needs temporal progression + causality

Return JSON:
{{
  "page_analysis": "Brief description of what this page contains overall",
  "stories": [
    {{
      "start_segment": <int>,
      "end_segment": <int>,
      "characters": ["name1", "name2"],
      "confidence": 0-100,
      "story_type": "full_narrative" | "brief_anecdote" | "dialogue_vignette",
      "one_sentence_summary": "...",
      "why_this_is_a_story": "Explain: named characters, temporal progression, causal chain, outcome"
    }}
  ]
}}

If NO genuine stories found, return: {{"page_analysis": "...", "stories": []}}

Page: {ref}
"""

    return prompt


def analyze_page_with_segments(page_data: Dict, model) -> Dict[str, Any]:
    """
    Run AI analysis on pre-processed segments.
    """
    # Pre-process segments
    processed = preprocess_segments(page_data['segments'])

    # Detect continuations (Idea F)
    continuations = detect_continuations(processed)

    # Build story groups from continuations
    story_groups = build_story_groups(processed, continuations)

    # Build prompt
    prompt = build_analysis_prompt(page_data['ref'], processed, continuations, story_groups)

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

        # Parse JSON
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0]
        elif '```' in content:
            parts = content.split('```')
            if len(parts) >= 2:
                content = parts[1]

        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            result = json.loads(content[json_start:json_end])
            result['_processed_segments'] = processed
            result['_continuations'] = continuations
            return result

        return {"stories": [], "error": "Could not parse JSON"}

    except Exception as e:
        print(f"  AI error: {e}")
        return {"stories": [], "error": str(e)}


def run_test():
    """Run the comprehensive segment-based test."""

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: Set GOOGLE_API_KEY environment variable")
        return

    if not GOOGLE_AI_AVAILABLE:
        print("ERROR: Install google-generativeai package")
        return

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")

    print("=" * 70)
    print("COMPREHENSIVE SEGMENT-BASED STORY DETECTION")
    print("With Hebrew Markers + Jeff's Criteria + Continuation Detection")
    print("=" * 70)

    results = []

    for ref in TEST_PAGES:
        print(f"\n{'─' * 60}")
        print(f"PAGE: {ref}")
        print(f"{'─' * 60}")

        # Fetch with segments
        page_data = fetch_page_segments(ref)
        if not page_data:
            print("  SKIP: Could not fetch")
            continue

        print(f"  Total segments: {page_data['total_segments']}")

        # Pre-process and show marker summary
        processed = preprocess_segments(page_data['segments'])
        high_likelihood = [s['index'] for s in processed if s['story_likelihood'] == 'HIGH']
        medium_likelihood = [s['index'] for s in processed if s['story_likelihood'] == 'MEDIUM']

        print(f"  HIGH likelihood segments: {high_likelihood if high_likelihood else 'none'}")
        print(f"  MEDIUM likelihood segments: {medium_likelihood if medium_likelihood else 'none'}")

        # Detect continuations
        continuations = detect_continuations(processed)
        if continuations:
            print(f"  Detected continuations: {continuations}")

        # Run AI analysis
        print("  Running AI analysis...")
        analysis = analyze_page_with_segments(page_data, model)

        stories = analysis.get('stories', [])
        print(f"  Stories found: {len(stories)}")

        for story in stories:
            start = story.get('start_segment', '?')
            end = story.get('end_segment', '?')
            conf = story.get('confidence', 0)
            stype = story.get('story_type', 'unknown')
            summary = story.get('one_sentence_summary', '')[:60]

            print(f"\n    Story: Segments {start}-{end} ({stype}, {conf}%)")
            print(f"    Summary: {summary}...")
            print(f"    Characters: {story.get('characters', [])}")

            # Show the actual text
            if isinstance(start, int) and isinstance(end, int):
                for i in range(start, min(end + 1, len(page_data['segments']))):
                    seg_text = page_data['segments'][i]['english'][:100]
                    print(f"    [Seg {i}]: {seg_text}...")

        # Build result
        result = {
            'ref': ref,
            'total_segments': page_data['total_segments'],
            'segments': page_data['segments'],
            'marker_analysis': {
                'high_likelihood': high_likelihood,
                'medium_likelihood': medium_likelihood,
                'continuations': continuations
            },
            'analysis': analysis
        }
        results.append(result)

        time.sleep(0.5)

    # Save results
    output = {
        'approach': 'segment_based_with_markers_and_continuations',
        'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
        'pages': results
    }

    output_file = 'test_segment_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n{'=' * 70}")
    print(f"Results saved to: {output_file}")

    # Summary
    total_stories = sum(len(r['analysis'].get('stories', [])) for r in results)
    print(f"Total stories found across {len(results)} pages: {total_stories}")
    print("=" * 70)

    return results


if __name__ == "__main__":
    run_test()
