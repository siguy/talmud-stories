#!/usr/bin/env python3
"""
Talmud Stories Finder
Searches through Talmud tractates to identify narrative passages and stories.
"""

import requests
import json
import time
from typing import List, Dict, Any
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

# Keywords that often indicate narrative/story content
STORY_KEYWORDS = [
    "once", "story", "happened", "rabbi", "said to him",
    "asked him", "went to", "came to", "saw", "found",
    "Jerusalem", "Rome", "Caesar", "king", "miracle",
    "dream", "vision", "angel", "voice from heaven",
    "it happened", "there was", "a certain"
]


class SefariaStoryFinder:
    """Find stories in Talmud using Sefaria API"""

    def __init__(self):
        self.results = []
        self.session = requests.Session()

    def search_tractate(self, tractate: str, order: str) -> List[Dict[str, Any]]:
        """Search a specific tractate for story-like content"""
        print(f"\n{'='*60}")
        print(f"Searching {tractate} ({order})...")
        print(f"{'='*60}")

        stories = []

        # Search for narrative keywords in this tractate
        for keyword in ["story", "happened", "once", "miracle", "came to"]:
            try:
                results = self._search_in_book(tractate, keyword)
                stories.extend(results)
                time.sleep(0.5)  # Rate limiting
            except Exception as e:
                print(f"  Error searching '{keyword}': {e}")

        # Deduplicate by reference
        unique_stories = {}
        for story in stories:
            ref = story.get('ref', '')
            if ref and ref not in unique_stories:
                unique_stories[ref] = story

        print(f"  Found {len(unique_stories)} potential story passages")
        return list(unique_stories.values())

    def _search_in_book(self, book: str, query: str) -> List[Dict[str, Any]]:
        """Search within a specific book using Sefaria API"""
        url = f"{SEFARIA_API}/search-wrapper"
        params = {
            "q": query,
            "filters": f"path:{book}",
            "type": "text"
        }

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            results = []
            for hit in data.get('hits', {}).get('hits', []):
                source = hit.get('_source', {})
                results.append({
                    'ref': source.get('ref'),
                    'text': source.get('naive_lemmatizer', source.get('exact', '')),
                    'book': book,
                    'score': hit.get('_score', 0)
                })

            return results
        except Exception as e:
            print(f"    API error: {e}")
            return []

    def get_text(self, ref: str) -> Dict[str, Any]:
        """Get full text for a reference"""
        url = f"{SEFARIA_API}/texts/{ref}"
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"  Error fetching {ref}: {e}")
            return {}

    def analyze_passage(self, passage: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze if a passage is likely a story"""
        text = passage.get('text', '')
        if isinstance(text, list):
            text = ' '.join(text)

        # Count story indicators
        story_score = 0
        found_keywords = []

        text_lower = text.lower()
        for keyword in STORY_KEYWORDS:
            if keyword in text_lower:
                story_score += 1
                found_keywords.append(keyword)

        return {
            'ref': passage.get('ref'),
            'book': passage.get('book'),
            'text': text,
            'story_score': story_score,
            'keywords_found': found_keywords,
            'is_likely_story': story_score >= 2
        }

    def search_all_tractates(self, limit_per_tractate: int = 10):
        """Search all Talmud tractates for stories"""
        all_stories = []

        for order, tractates in TALMUD_TRACTATES.items():
            print(f"\n\n{'#'*60}")
            print(f"# ORDER: {order}")
            print(f"{'#'*60}")

            for tractate in tractates:
                try:
                    stories = self.search_tractate(tractate, order)

                    # Analyze each story
                    for story in stories[:limit_per_tractate]:
                        analyzed = self.analyze_passage(story)
                        if analyzed['is_likely_story']:
                            all_stories.append(analyzed)
                            print(f"  ✓ {analyzed['ref']} (score: {analyzed['story_score']})")

                    time.sleep(1)  # Rate limiting between tractates

                except Exception as e:
                    print(f"  Error processing {tractate}: {e}")

        return all_stories

    def save_results(self, stories: List[Dict[str, Any]], filename: str = "talmud_stories.json"):
        """Save results to JSON file"""
        output = {
            'total_stories': len(stories),
            'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'stories': sorted(stories, key=lambda x: x['story_score'], reverse=True)
        }

        Path(filename).write_text(json.dumps(output, indent=2, ensure_ascii=False))
        print(f"\n\n{'='*60}")
        print(f"Results saved to {filename}")
        print(f"Total stories found: {len(stories)}")
        print(f"{'='*60}")


def main():
    """Main execution"""
    print("Talmud Stories Finder")
    print("Using Sefaria API to search for narrative passages\n")

    finder = SefariaStoryFinder()

    # Option to search specific tractates or all
    print("Options:")
    print("1. Search all tractates (comprehensive, takes ~30+ minutes)")
    print("2. Search specific tractate")
    print("3. Search famous story-rich tractates (Taanit, Berakhot, Sanhedrin)")

    choice = input("\nEnter choice (1-3, default=3): ").strip() or "3"

    if choice == "1":
        stories = finder.search_all_tractates()
    elif choice == "2":
        tractate = input("Enter tractate name (e.g., 'Berakhot'): ").strip()
        stories_raw = finder.search_tractate(tractate, "Custom")
        stories = [finder.analyze_passage(s) for s in stories_raw if finder.analyze_passage(s)['is_likely_story']]
    else:  # Default to story-rich tractates
        story_rich = ["Taanit", "Berakhot", "Sanhedrin", "Megillah", "Shabbat"]
        stories = []
        for tractate in story_rich:
            stories_raw = finder.search_tractate(tractate, "Selected")
            analyzed = [finder.analyze_passage(s) for s in stories_raw]
            stories.extend([s for s in analyzed if s['is_likely_story']])
            time.sleep(1)

    # Save results
    finder.save_results(stories)

    # Print top stories
    print("\n\nTop Story Passages Found:")
    print("=" * 60)
    for story in sorted(stories, key=lambda x: x['story_score'], reverse=True)[:10]:
        print(f"\n{story['ref']} (Score: {story['story_score']})")
        print(f"Keywords: {', '.join(story['keywords_found'][:5])}")
        preview = story['text'][:200] + "..." if len(story['text']) > 200 else story['text']
        print(f"Preview: {preview}")


if __name__ == "__main__":
    main()
