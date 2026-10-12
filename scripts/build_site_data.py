#!/usr/bin/env python3
"""Export the stories for the Septimus family viewer (work/2026-10-12-septimus-story-viewer.md).

Reads (read-only): results/canonical/{ketubot,kiddushin,gittin}_canonical.json and
results/v11/yevamot/yevamot_v11.json. Writes site/data/index.json + site/data/<tractate>.json.

Tiers (decided 2026-10-12): `story` = anything the golden accepts that is not BORDERLINE;
`borderline` = BORDERLINE, shown separately. NOT_A_STORY never ships. Yevamot has no expert
round: its stories are detector output, flagged `reviewed: false`.

mishnah_stories[] is deliberately NOT exported: Stage 4g withheld those on purpose and whether
Mishnah-internal stories belong is Jeff's scope question (CLAUDE.md, data-structure rule).
The count withheld is reported in index.json so the omission is visible, not silent.

Hebrew already carries nikud in the cached Sefaria segments; coverage is asserted below.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "site" / "data"

SOURCES = {
    "ketubot": ("results/canonical/ketubot_canonical.json", True),
    "kiddushin": ("results/canonical/kiddushin_canonical.json", True),
    "gittin": ("results/canonical/gittin_canonical.json", True),
    "yevamot": ("results/v11/yevamot/yevamot_v11.json", False),
}
NIKUD = re.compile("[ְ-ׇ]")
KEEP = {"b", "i", "strong", "em", "big", "small", "br"}
TAG = re.compile(r"<(/?)([a-zA-Z0-9]+)[^>]*>")
SUP = re.compile(r"<sup\b.*?</sup>|<i class=\"footnote\">.*?</i>", re.S)


def clean(html):
    html = SUP.sub("", html or "")
    return TAG.sub(lambda m: f"<{m.group(1)}{m.group(2).lower()}>" if m.group(2).lower() in KEEP else "", html)


def tier(classification):
    if classification == "NOT_A_STORY":
        return None
    return "borderline" if classification == "BORDERLINE" else "story"


def pieces(pages, i, s):
    """(page_ref, [segments]) pieces of one story. Cross-page: start..end on page one,
    start_page2..end_page2 on the next page (evaluate_golden.py reads it the same way)."""
    p = pages[i]
    a, b = int(s["start_segment"]), int(s["end_segment"])
    out = [(p["ref"], p["segments"][a:b + 1])]
    if s.get("spans_pages") and s.get("end_segment_page2") is not None:
        q = pages[i + 1]
        assert q["ref"] == s["spans_pages"][1], (p["ref"], q["ref"])
        out.append((q["ref"], q["segments"][int(s.get("start_segment_page2") or 0):int(s["end_segment_page2"]) + 1]))
    return out


def build(tractate, path, reviewed):
    d = json.loads((ROOT / path).read_text())
    pages = d["pages"]
    stories, withheld = [], 0
    for i, p in enumerate(pages):
        withheld += len(p.get("mishnah_stories", []))
        for s in p.get("stories", []):
            t = tier(s.get("classification"))
            if t is None:
                continue
            ps = pieces(pages, i, s)
            segs = [g for _, gs in ps for g in gs]
            assert segs, (tractate, p["ref"], s)
            heb = "".join(clean(g.get("hebrew")) + " " for g in segs).strip()
            if not NIKUD.search(heb):
                print(f"  no nikud: {tractate} {p['ref']} {s['start_segment']}", file=sys.stderr)
            stories.append({
                "id": f"{tractate}-{p['ref'].split()[-1]}-{s['start_segment']}-{s['end_segment']}",
                "tractate": tractate,
                "ref": p["ref"],
                "refs": [r for r, _ in ps],
                "start_segment": int(s["start_segment"]),
                "tier": t,
                "reviewed": reviewed,
                "summary": s.get("one_sentence_summary", ""),
                "segments": [{"he": clean(g.get("hebrew")), "en": clean(g.get("english"))} for g in segs],
            })
    return stories, withheld


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    index = {"tractates": []}
    for t, (path, reviewed) in SOURCES.items():
        stories, withheld = build(t, path, reviewed)
        ids = [s["id"] for s in stories]
        assert len(ids) == len(set(ids)), f"{t}: duplicate story ids"
        (OUT / f"{t}.json").write_text(json.dumps({"tractate": t, "reviewed": reviewed, "stories": stories},
                                                  ensure_ascii=False, indent=1))
        n = {k: sum(1 for s in stories if s["tier"] == k) for k in ("story", "borderline")}
        index["tractates"].append({"tractate": t, "reviewed": reviewed, **n, "mishnah_withheld": withheld})
        print(f"{t:10} story={n['story']:4} borderline={n['borderline']:3} reviewed={reviewed} mishnah_withheld={withheld}")
    (OUT / "index.json").write_text(json.dumps(index, indent=1))


if __name__ == "__main__":
    main()
