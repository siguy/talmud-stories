#!/usr/bin/env python3
"""
Test improved prompt on expert-reviewed false positives.
Uses feedback from Jeffrey Rubenstein to validate improvements.
"""

import os
import sys
import json
from find_talmud_stories import NarrativeAnalyzer, SefariaStoryFinder

# Test cases from expert feedback (false positives that should now be detected)
TEST_CASES = [
    {
        "ref": "Ketubot 2a",
        "expected": False,  # Should be false (legal discussion)
        "expert_note": "Legal discussion with no story. Prescriptive rule about weddings."
    },
    {
        "ref": "Ketubot 3a",
        "expected": False,
        "expert_note": "Legal discussion with hypothetical cases, not one-time events"
    },
    {
        "ref": "Ketubot 3b",
        "expected": False,
        "expert_note": "Legal discussion with narrative elements but no story"
    },
    {
        "ref": "Ketubot 8b",
        "expected": True,  # Should be true (contains real stories)
        "expert_note": "Contains two stories - Rav Ḥiyya bar Abba and Rabbi Gamliel burial reform"
    },
    {
        "ref": "Ketubot 10b",
        "expected": True,
        "expert_note": "Contains three stories about marriage cases"
    },
    {
        "ref": "Ketubot 20b",
        "expected": True,
        "expert_note": "Contains story about Rav Ashi and Rav Kahana testimony"
    }
]


def test_improved_prompt():
    """Test the improved prompt on expert-reviewed cases"""

    # Get API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ERROR: ANTHROPIC_API_KEY not set")
        print("Run: export ANTHROPIC_API_KEY='your-key'")
        sys.exit(1)

    print("=" * 80)
    print("Testing Improved Story Detection Prompt")
    print("Based on expert feedback from Jeffrey Rubenstein")
    print("=" * 80)
    print()

    # Initialize
    analyzer = NarrativeAnalyzer(api_key=api_key, model="claude-3-5-haiku-20241022")
    finder = SefariaStoryFinder(analyzer, use_windowing=False)

    results = {
        "total": len(TEST_CASES),
        "correct": 0,
        "incorrect": 0,
        "details": []
    }

    for i, test_case in enumerate(TEST_CASES, 1):
        ref = test_case["ref"]
        expected = test_case["expected"]
        expert_note = test_case["expert_note"]

        print(f"Test {i}/{len(TEST_CASES)}: {ref}")
        print(f"Expert says: {'IS story' if expected else 'NOT story'}")
        print(f"Note: {expert_note}")

        # Fetch text
        text_data = finder.get_text(ref)
        if not text_data:
            print(f"❌ Could not fetch text for {ref}")
            print()
            continue

        # Extract text
        english_text = text_data.get('text', '')
        if isinstance(english_text, list):
            english_text = ' '.join(str(t) for t in english_text if t)

        hebrew_text = text_data.get('he', '')
        if isinstance(hebrew_text, list):
            hebrew_text = ' '.join(str(t) for t in hebrew_text if t)

        # Analyze with improved prompt
        analysis = analyzer.analyze_narrative_structure(english_text, ref, hebrew_text)

        ai_result = analysis.get('is_story', False)
        confidence = analysis.get('confidence', 0)
        reasoning = analysis.get('reasoning', '')
        validation_notes = analysis.get('validation_notes', '')
        embedded = analysis.get('embedded_in_legal_context', False)

        # Check if correct
        is_correct = (ai_result == expected)

        if is_correct:
            results['correct'] += 1
            print(f"✅ CORRECT - AI says: {'IS story' if ai_result else 'NOT story'} (confidence: {confidence}%)")
        else:
            results['incorrect'] += 1
            print(f"❌ INCORRECT - AI says: {'IS story' if ai_result else 'NOT story'} (confidence: {confidence}%)")

        print(f"AI reasoning: {reasoning[:150]}...")
        if validation_notes:
            print(f"Validation: {validation_notes[:150]}...")
        if embedded:
            print(f"⚠️  AI detected story embedded in legal context")

        print()

        results['details'].append({
            "ref": ref,
            "expected": expected,
            "ai_result": ai_result,
            "correct": is_correct,
            "confidence": confidence,
            "reasoning": reasoning,
            "validation_notes": validation_notes
        })

    # Summary
    print("=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)
    accuracy = (results['correct'] / results['total']) * 100
    print(f"Accuracy: {results['correct']}/{results['total']} ({accuracy:.1f}%)")
    print(f"Correct: {results['correct']}")
    print(f"Incorrect: {results['incorrect']}")
    print()

    if results['incorrect'] > 0:
        print("FAILURES:")
        for detail in results['details']:
            if not detail['correct']:
                print(f"  - {detail['ref']}: Expected {'story' if detail['expected'] else 'not story'}, "
                      f"got {'story' if detail['ai_result'] else 'not story'} ({detail['confidence']}%)")
        print()

    # Save detailed results
    output_file = "validation_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Detailed results saved to: {output_file}")
    print()

    # Recommendation
    if accuracy >= 80:
        print("✅ RECOMMENDATION: Prompt improvements are working well!")
        print("   Consider deploying to full analysis.")
    elif accuracy >= 60:
        print("⚠️  RECOMMENDATION: Prompt shows improvement but needs refinement.")
        print("   Review failures and adjust prompt further.")
    else:
        print("❌ RECOMMENDATION: Prompt needs significant revision.")
        print("   Review all failures carefully.")

    return results


if __name__ == "__main__":
    test_improved_prompt()
