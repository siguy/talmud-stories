"""Apply Jeff's 2026-06-03 Ketubot corrections to the canonical golden dataset.

Source: Jeff email (2026-06-03) accompanying validation/feedback/kiddushin_review_2026-05-26 (1).json

Corrections:
  1. Ketubot 7a seg 1: NOT_A_STORY -> LOW_CONFIDENCE
  2. Ketubot 26a seg 9: confirms NOT_A_STORY (no change)
  3. Ketubot 102a seg 6: confirms not a story (no change; not in canonical)
  4. Ketubot 106a: existing 3-3 HIGH_CONFIDENCE story extends back to start_segment=2
"""
import json
from pathlib import Path
from datetime import date

PATH = Path("results/canonical/ketubot_canonical.json")
data = json.loads(PATH.read_text())

log_entries = []

for page in data["pages"]:
    if page["ref"] == "Ketubot 7a":
        for s in page["stories"]:
            if s["start_segment"] == 1 and s["end_segment"] == 1:
                old = s["classification"]
                s["classification"] = "LOW_CONFIDENCE"
                s.setdefault("corrections", []).append({
                    "date": "2026-06-03",
                    "source": "Jeff email reply to Wave 3 review",
                    "action": "reclassify",
                    "old": old,
                    "new": "LOW_CONFIDENCE",
                    "note": "Jeff: 'low confidence' (re-adding to golden as LOW)",
                })
                log_entries.append({
                    "key": "Ketubot 7a_1-1",
                    "action": "reclassify",
                    "old_classification": old,
                    "new_classification": "LOW_CONFIDENCE",
                    "note": "Jeff 2026-06-03 email: low confidence",
                })
                break

    if page["ref"] == "Ketubot 106a":
        for s in page["stories"]:
            if s["start_segment"] == 3 and s["end_segment"] == 3:
                s["start_segment"] = 2
                s.setdefault("corrections", []).append({
                    "date": "2026-06-03",
                    "source": "Jeff email reply to Wave 3 review",
                    "action": "extend_start",
                    "old_range": "3-3",
                    "new_range": "2-3",
                    "note": "Jeff: 'the story is segments 2-3, not really 1' (v9 detected 1-2; correct is 2-3)",
                })
                log_entries.append({
                    "key": "Ketubot 106a_3-3 -> 2-3",
                    "action": "extend_start",
                    "old_range": "3-3",
                    "new_range": "2-3",
                    "note": "Jeff 2026-06-03 email",
                })
                break

# Audit: confirm v9-detected 1-2 on 106a is now resolved by our 2-3 (Jeff said NOT seg 1)
# Audit: confirm 26a_9 and 102a_6 are NOT_A_STORY / not-present (no-op)

data.setdefault("canonical_review_applied_log", []).extend(log_entries)
data.setdefault("round2_jeff_2026_06_03", {
    "date": "2026-06-03",
    "source": "validation/feedback/kiddushin_review_2026-05-26 (1).json + email",
    "applied": log_entries,
    "confirmed_no_change": [
        {"key": "Ketubot 26a_9", "note": "Jeff confirms NOT_A_STORY; canonical already NOT_A_STORY"},
        {"key": "Ketubot 102a_6", "note": "Jeff confirms not a story; canonical does not include it"},
    ],
})

PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2))
print("Applied corrections:")
for e in log_entries:
    print(" ", e)
print(f"\nWrote {PATH}")
