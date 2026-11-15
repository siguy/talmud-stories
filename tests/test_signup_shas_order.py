"""SHAS_ORDER in site/signup.js must be the order of TABLE in scripts/tractates.py (and name real tractates)."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / 'scripts'))

import tractates  # noqa: E402


def _js_order():
    src = (ROOT / 'site' / 'signup.js').read_text()
    m = re.search(r'var SHAS_ORDER = \[(.*?)\];', src, re.S)
    assert m, 'SHAS_ORDER not found in site/signup.js'
    return re.findall(r'"([a-z_]+)"', m.group(1))


def test_shas_order_matches_table():
    assert _js_order() == [tractates.slug_of(e) for e, _ in tractates.TABLE]


def test_shas_order_slugs_are_the_index_slugs():
    index = json.loads((ROOT / 'site' / 'data' / 'index.json').read_text())
    assert set(_js_order()) == {t['tractate'] for t in index['tractates']}
