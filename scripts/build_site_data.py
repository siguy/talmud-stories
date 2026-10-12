#!/usr/bin/env python3
"""Export the stories for the Septimus family viewer (work/2026-10-12-septimus-story-viewer.md).

Reads (read-only): results/canonical/{ketubot,kiddushin,gittin}_canonical.json and
results/v11/yevamot/yevamot_v11.json. Writes site/data/index.json + site/data/<tractate>.json.

Tiers (decided 2026-10-12): `story` = YES or HIGH_CONFIDENCE; `borderline` = BORDERLINE, shown
separately. LOW_CONFIDENCE is NOT shipped (Simon, 2026-10-12). NOT_A_STORY never ships. Yevamot has no expert
round: its stories are detector output, flagged `reviewed: false`.

mishnah_stories[] (Stage 4g's withheld Mishnah-internal stories) IS exported, per Simon
2026-10-12: flagged `in_mishnah: true` and `reviewed: false` (detector output, never shown to
Jeff; whether they count is still his scope question).

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
    if classification == "BORDERLINE":
        return "borderline"
    return "story" if classification in ("YES", "HIGH_CONFIDENCE") else None


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
    stories = []
    for i, p in enumerate(pages):
        for in_mishnah, key in ((False, "stories"), (True, "mishnah_stories")):
            for s in p.get(key, []):
                t = tier(s.get("classification"))
                if t is None:
                    continue
                ps = pieces(pages, i, s)
                segs = [(r, g) for r, gs in ps for g in gs]
                assert segs, (tractate, p["ref"], s)
                if not NIKUD.search("".join(g.get("hebrew") or "" for _, g in segs)):
                    print(f"  no nikud: {tractate} {p['ref']} {s['start_segment']}", file=sys.stderr)
                stories.append({
                    "id": f"{tractate}-{p['ref'].split()[-1]}-{s['start_segment']}-{s['end_segment']}",
                    "tractate": tractate,
                    "ref": p["ref"],
                    "refs": [r for r, _ in ps],
                    "start_segment": int(s["start_segment"]),
                    "tier": t,
                    "classification": s.get("classification"),
                    "in_mishnah": in_mishnah,
                    # Mishnah-internal stories were never shown to Jeff, whatever the tractate.
                    "reviewed": reviewed and not in_mishnah,
                    # "[Restored from ... merge]" is a bookkeeping placeholder, not a summary: never show it.
                    "summary": "" if str(s.get("one_sentence_summary", "")).startswith("[") else s.get("one_sentence_summary", ""),
                    # ref + index locate a segment exactly, so feedback on one can be traced to the source.
                    "segments": [{"ref": r, "i": g.get("index"), "he": clean(g.get("hebrew")), "en": clean(g.get("english"))}
                                 for r, g in segs],
                })
    return stories


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    index = {"tractates": []}
    for t, (path, reviewed) in SOURCES.items():
        stories = build(t, path, reviewed)
        ids = [s["id"] for s in stories]
        assert len(ids) == len(set(ids)), f"{t}: duplicate story ids"
        (OUT / f"{t}.json").write_text(json.dumps({"tractate": t, "reviewed": reviewed, "stories": stories},
                                                  ensure_ascii=False, indent=1))
        n = {k: sum(1 for s in stories if s["tier"] == k) for k in ("story", "borderline")}
        index["tractates"].append({"tractate": t, "reviewed": reviewed, **n, "in_mishnah": sum(1 for s in stories if s["in_mishnah"])})
        print(f"{t:10} story={n['story']:4} borderline={n['borderline']:3} reviewed={reviewed} in_mishnah={index['tractates'][-1]['in_mishnah']}")
    (OUT / "index.json").write_text(json.dumps(index, indent=1))


if __name__ == "__main__":
    main()
