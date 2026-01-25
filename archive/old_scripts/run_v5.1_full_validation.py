#!/usr/bin/env python3
"""
Run v5.1 on Ketubot 2-39 for Jeff's full validation range
"""

import sys
sys.path.insert(0, 'tests/v5_categorical')

from test_categorical_classification_v5_1 import analyze_tractate_v5, save_results

if __name__ == "__main__":
    print("Running v5.1 on Ketubot 2-39 for Jeff's validation comparison...")
    print("This may take a while due to API rate limits (10 req/min)")
    print()

    results = analyze_tractate_v5("Ketubot", start_page=2, end_page=39)
    save_results(results, "ketubot_v5.1_full_validation_2-39.json")
