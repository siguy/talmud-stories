#!/usr/bin/env python3
"""
Offline test of story extraction logic using sample text.
Tests the boundary extraction without needing Sefaria API access.
"""

import sys
import json
from find_talmud_stories import SefariaStoryFinder, NarrativeAnalyzer

# Sample text with multiple stories (simulated Ketubot 10b-like content)
SAMPLE_FULL_TEXT = """
MISHNAH: A virgin is married on Wednesday and a widow on Thursday. This is because the courts convene in the cities on Monday and Thursday. And if a husband has a grievance concerning a claim of virginity, he will go early in the morning to the court.

GEMARA: There was a certain woman who came before Rav Nahman with a claim about her ketubba. She said: "My husband died and I need my ketubba payment." Rav Nahman examined the witnesses and the documents. After investigation, he found that her claim was valid. He ruled in her favor and she received her payment. She went on her way rejoicing.

The mishna continues: What is the reason for the Wednesday wedding? It is so that if the husband has a complaint about his wife's virginity, he can go to court on Thursday morning.

There was another case where a man betrothed a woman and then died before the wedding. His brother came to perform levirate marriage. The woman said: "I do not want to marry the brother." The brother said: "The law requires levirate marriage." They came before Rav Ashi. Rav Ashi examined the case carefully. He determined that the woman had valid reasons to refuse. He released her from the obligation and she was free to marry whomever she chose.

The halakha is as follows: The wedding feast takes place on Wednesday for virgins and Thursday for widows.
"""

SAMPLE_HEBREW = """
משנה: בתולה נישאת ביום הרביעי ואלמנה ביום החמישי שבית דין יושבין בעיירות בשני ובחמישי ואם היתה לו טענת בתולים משכים לבית דין

גמרא: ההוא איתתא דאתאי לקמיה דרב נחמן בטענת כתובה אמרה מיתה בעלי וצריכנא כתובתי בדק רב נחמן בסהדי ובשטרא משכחה דמסתברא טענתה פסק לה וקבלתה ואזלה בשמחה

והא תנן מאי טעמא דיום רביעי בשביל שאם היתה לו טענת בתולים משכים לבית דין ביום החמישי

ההוא גברא דקדיש איתתא ומית קודם נישואין אתא אחוה למיבם אמרה לא בעינא למינסב לאחוה אמר האח דינא למיבם אתו לקמיה דרב אשי בדק רב אשי בדינא משכח דאית לה טענה מעליתא שריא והויא פנויה למינסב למאן דבעיא

הלכתא: משתה חתנות הוא ביום רביעי לבתולה וביום חמישי לאלמנה
"""

def test_extraction_logic():
    """Test the text extraction function with known boundaries"""

    print("=" * 80)
    print("Testing Story Extraction Logic (Offline)")
    print("=" * 80)
    print()

    # Initialize (no API key needed for extraction function)
    finder = SefariaStoryFinder(None, use_windowing=False)

    # Define test stories with known boundaries
    test_stories = [
        {
            "name": "Story 1: Woman with ketubba claim",
            "start": "There was a certain woman who came before Rav Nahman",
            "end": "She went on her way rejoicing.",
            "expected_length": 200,  # approximate
        },
        {
            "name": "Story 2: Levirate marriage case",
            "start": "There was another case where a man betrothed a woman",
            "end": "she was free to marry whomever she chose.",
            "expected_length": 300,  # approximate
        }
    ]

    results = []

    for i, test in enumerate(test_stories, 1):
        print(f"Test {i}: {test['name']}")
        print("-" * 80)
        print(f"Looking for: '{test['start'][:40]}...'")
        print(f"           → '{test['end'][:40]}...'")
        print()

        # Extract story
        extracted = finder.extract_story_text(
            SAMPLE_FULL_TEXT,
            test['start'],
            test['end'],
            language="english"
        )

        if extracted:
            print(f"✅ Extraction successful: {len(extracted)} characters")
            print(f"   Expected ~{test['expected_length']} chars")

            # Verify it starts and ends correctly
            starts_correctly = extracted.strip().startswith(test['start'][:20])
            ends_correctly = test['end'][:20] in extracted

            if starts_correctly and ends_correctly:
                print(f"   ✓ Boundaries correct")
            else:
                print(f"   ⚠️  Boundary mismatch")
                if not starts_correctly:
                    print(f"      Start mismatch: '{extracted[:50]}...'")
                if not ends_correctly:
                    print(f"      End mismatch: '...{extracted[-50:]}'")

            # Show excerpt
            excerpt = extracted[:100] + "..." if len(extracted) > 100 else extracted
            print(f"   Preview: {excerpt}")

            # Verify it's NOT the full text
            is_full_text = len(extracted) > len(SAMPLE_FULL_TEXT) * 0.8
            if is_full_text:
                print(f"   ⚠️  WARNING: Extracted text is {len(extracted)/len(SAMPLE_FULL_TEXT)*100:.0f}% of full page")
            else:
                print(f"   ✓ Correctly extracted subset ({len(extracted)/len(SAMPLE_FULL_TEXT)*100:.0f}% of full page)")

            results.append({
                "test": test['name'],
                "success": True,
                "length": len(extracted),
                "boundaries_correct": starts_correctly and ends_correctly,
                "is_subset": not is_full_text
            })
        else:
            print(f"❌ Extraction failed")
            results.append({
                "test": test['name'],
                "success": False
            })

        print()

    # Test Hebrew extraction
    print("Test 3: Hebrew extraction")
    print("-" * 80)

    hebrew_story = {
        "start": "ההוא איתתא דאתאי לקמיה דרב נחמן",
        "end": "ואזלה בשמחה"
    }

    extracted_hebrew = finder.extract_story_text(
        SAMPLE_HEBREW,
        hebrew_story['start'],
        hebrew_story['end'],
        language="hebrew"
    )

    if extracted_hebrew:
        print(f"✅ Hebrew extraction successful: {len(extracted_hebrew)} characters")
        print(f"   Preview: {extracted_hebrew[:80]}...")
        results.append({
            "test": "Hebrew extraction",
            "success": True,
            "length": len(extracted_hebrew)
        })
    else:
        print(f"❌ Hebrew extraction failed")
        results.append({
            "test": "Hebrew extraction",
            "success": False
        })

    print()

    # Test edge cases
    print("Test 4: Edge cases")
    print("-" * 80)

    # Test with extra whitespace
    print("Testing whitespace normalization...")
    messy_start = "There  was   a certain woman"  # extra spaces
    extracted_messy = finder.extract_story_text(
        SAMPLE_FULL_TEXT,
        messy_start,
        "She went on her way rejoicing.",
        language="english"
    )

    if extracted_messy:
        print("   ✓ Whitespace normalization working")
    else:
        print("   ⚠️  Whitespace normalization may need adjustment")

    # Test with partial match
    print("Testing partial match (first 3 words)...")
    partial_start = "There was a"  # Only first 3 words
    extracted_partial = finder.extract_story_text(
        SAMPLE_FULL_TEXT,
        partial_start,
        "rejoicing.",  # Last word
        language="english"
    )

    if extracted_partial:
        print("   ✓ Partial match working")
    else:
        print("   ⚠️  Partial match needs adjustment")

    print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)

    successful = sum(1 for r in results if r.get('success', False))
    total = len(results)

    print(f"Tests passed: {successful}/{total}")
    print()

    if successful == total:
        print("✅ All extraction tests passed!")
        print("   The text extraction logic is working correctly.")
        print("   Ready to run full analysis when network access is available.")
    elif successful >= total * 0.8:
        print("⚠️  Most tests passed, but some edge cases need attention.")
    else:
        print("❌ Multiple failures - extraction logic needs debugging.")

    print()
    print("Next steps:")
    print("1. If tests pass: Run 'python3 test_ketubot.py' when network is available")
    print("2. The system will now:")
    print("   - Detect multiple stories per page")
    print("   - Extract ONLY the story text (not full page)")
    print("   - Save each story as a separate entry")

    return results


if __name__ == "__main__":
    results = test_extraction_logic()

    # Save results
    with open('test_extraction_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    print()
    print("Results saved to: test_extraction_results.json")
