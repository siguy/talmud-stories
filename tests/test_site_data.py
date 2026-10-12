"""The family viewer's data must match the goldens by COUNT (Critical Rule 5), never by score."""
import json
import re
import subprocess
import sys
from pathlib import Path

from tests.test_bookkeeping import GOLDEN_COUNTS

ROOT = Path(__file__).resolve().parent.parent


def test_site_data_counts_match_the_goldens():
    subprocess.run([sys.executable, str(ROOT / "scripts/build_site_data.py")], check=True, capture_output=True)
    for t in GOLDEN_COUNTS:
        d = json.loads((ROOT / f"site/data/{t}.json").read_text())
        g = json.loads((ROOT / f"results/canonical/{t}_canonical.json").read_text())
        shipped = ("YES", "HIGH_CONFIDENCE", "BORDERLINE")  # LOW_CONFIDENCE is not shipped
        n = sum(1 for p in g["pages"] for k in ("stories", "mishnah_stories")
                for s in p.get(k, []) if s.get("classification") in shipped)
        assert len(d["stories"]) == n, t
        assert not any(s["tier"] == "story" and s["in_mishnah"] and s["reviewed"] for s in d["stories"])
        assert all(s["reviewed"] for s in d["stories"] if not s["in_mishnah"])
        assert all(g["he"] and g["en"] for s in d["stories"] for g in s["segments"])
    y = json.loads((ROOT / "site/data/yevamot.json").read_text())
    assert y["stories"] and not any(s["reviewed"] for s in y["stories"])


def test_hebrew_carries_nikud():
    nik = re.compile("[ְ-ׇ]")
    for t in GOLDEN_COUNTS:
        d = json.loads((ROOT / f"site/data/{t}.json").read_text())
        assert all(nik.search("".join(g["he"] for g in s["segments"])) for s in d["stories"]), t
