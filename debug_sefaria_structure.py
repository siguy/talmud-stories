#!/usr/bin/env python3
"""
Debug script to see what Sefaria API returns for Ketubot structure
"""

import requests
import json

url = "https://www.sefaria.org/api/index/Ketubot"
response = requests.get(url)
data = response.json()

print("=" * 60)
print("Sefaria API Response for Ketubot")
print("=" * 60)

print("\nLengths array:")
print(json.dumps(data.get('lengths', []), indent=2))

print("\nSchema structure:")
print(json.dumps(data.get('schema', {}), indent=2))

print("\nTitle:")
print(data.get('title'))

print("\nAll keys:")
print(list(data.keys()))

# Try to understand the structure
lengths = data.get('lengths', [])
if lengths:
    print(f"\nTotal amudim (page sides): {lengths[0] if lengths else 'unknown'}")
    print(f"Expected pages: 2a through {2 + lengths[0]//2}{'a' if lengths[0] % 2 == 0 else 'b'}")

# Generate some test references to see if they work
print("\n" + "=" * 60)
print("Testing some references:")
print("=" * 60)

test_refs = [
    "Ketubot 2a",
    "Ketubot 2b",
    "Ketubot 3a",
    "Ketubot 62b"
]

for ref in test_refs:
    try:
        text_url = f"https://www.sefaria.org/api/texts/{ref}"
        resp = requests.get(text_url, timeout=5)
        if resp.status_code == 200:
            text_data = resp.json()
            text = text_data.get('text', '')
            if isinstance(text, list):
                text = ' '.join(str(t) for t in text[:2])  # First 2 lines
            print(f"✓ {ref}: {text[:100]}...")
        else:
            print(f"✗ {ref}: HTTP {resp.status_code}")
    except Exception as e:
        print(f"✗ {ref}: {e}")
