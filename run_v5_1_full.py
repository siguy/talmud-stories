#!/usr/bin/env python3
"""
Run v5.1 on Ketubot 2-39 for Jeff's full validation range.
"""

import requests
import json
import time
import os
import re
from typing import List, Dict, Any, Optional
from pathlib import Path

# Add the v5_categorical directory to the path
import sys
sys.path.insert(0, str(Path(__file__).parent / 'tests' / 'v5_categorical'))

# Now import the module properly by loading it
import importlib.util
spec = importlib.util.spec_from_file_location(
    "test_v5_1",
    Path(__file__).parent / 'tests' / 'v5_categorical' / 'test_categorical_classification_v5.1.py'
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

# Use the functions from the module
analyze_tractate_v5 = module.analyze_tractate_v5
save_results = module.save_results

if __name__ == "__main__":
    print("="  * 80)
    print("Running v5.1 on Ketubot 2-39 (Jeff's Full Validation Range)")
    print("=" * 80)
    print()
    print("This will analyze 76 pages (38 pages × 2 sides)")
    print("Expected time: 8-10 minutes due to API rate limits (10 req/min)")
    print()

    results = analyze_tractate_v5("Ketubot", start_page=2, end_page=39)
    save_results(results, "ketubot_v5.1_full_validation_2-39.json")

    print("\n" + "=" * 80)
    print("DONE - Full validation results saved")
    print("=" * 80)
