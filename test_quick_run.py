#!/usr/bin/env python3
"""Quick test to verify setup works"""

import sys
import os

print("Step 1: Checking environment...")
sys.stdout.flush()

api_key = os.environ.get('GOOGLE_API_KEY')
if api_key:
    print(f"✓ GOOGLE_API_KEY found: {api_key[:20]}...")
else:
    print("✗ GOOGLE_API_KEY not set")
sys.stdout.flush()

print("\nStep 2: Importing google.generativeai...")
sys.stdout.flush()

try:
    import google.generativeai as genai
    print("✓ Import successful")
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)
sys.stdout.flush()

print("\nStep 3: Configuring API...")
sys.stdout.flush()

try:
    genai.configure(api_key=api_key)
    print("✓ API configured")
except Exception as e:
    print(f"✗ Configuration failed: {e}")
    sys.exit(1)
sys.stdout.flush()

print("\nStep 4: Creating model...")
sys.stdout.flush()

try:
    model = genai.GenerativeModel("gemini-2.0-flash")
    print("✓ Model created: gemini-2.0-flash")
except Exception as e:
    print(f"✗ Model creation failed: {e}")
    sys.exit(1)
sys.stdout.flush()

print("\nStep 5: Testing API call...")
sys.stdout.flush()

try:
    response = model.generate_content("Say hello")
    print(f"✓ API call successful: {response.text[:50]}")
except Exception as e:
    print(f"✗ API call failed: {e}")
    sys.exit(1)
sys.stdout.flush()

print("\n✓ ALL TESTS PASSED - Ready to run full validation")
