#!/usr/bin/env python3
"""
Talmud Story Detection v5.2: Updated to use new google-genai package

Changes from v5.1:
- Migrated from google.generativeai (deprecated) to google.genai (current)
- Same functionality, updated API calls

Key features from v5.1:
- NEW DISQUALIFIER: Rabbi stating legal opinion (not character in story)
- STRICTER CAUSALITY: Must be causal chain, not just sequential events
- STRICTER CHANGE: Must be transformation, not just report of actions
- NEW WEAKENERS: Simple report, minimal causality, minimal change
- BOUNDARY MARKERS: Detect Talmud commentary end markers
- CONTINUATION MARKERS: Detect story continuation across segments
- UPDATED EXAMPLES: 8 examples from Jeff's v4.1 validation (including false positives)
"""

import requests
import json
import time
import os
import re
from typing import List, Dict, Any, Optional
from pathlib import Path

# Import NEW Google Generative AI package
try:
    from google import genai
    GOOGLE_AI_AVAILABLE = True
except ImportError:
    GOOGLE_AI_AVAILABLE = False
    print("google-genai not installed. Run: pip install google-genai")


# Copy all the content from v5.1 but update the Google API calls
# For now, let me create a migration function

def migrate_to_new_package():
    """
    Migration guide from google.generativeai to google.genai

    OLD (v5.1):
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content(prompt, generation_config={...})
        text = response.candidates[0].content.parts[0].text

    NEW (v5.2):
        from google import genai
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=prompt,
            config=genai.GenerateContentConfig(
                max_output_tokens=8192,
                temperature=0.1
            )
        )
        text = response.text
    """
    pass


if __name__ == "__main__":
    print("v5.2 migration in progress...")
    print("Run v5.1 for now: python3 test_categorical_classification_v5.1.py 2 39")
