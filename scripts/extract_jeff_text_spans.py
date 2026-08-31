"""Build the Wave 4 held-out fixture set from Jeff's 2026-05-26 Kiddushin review.

Reads validation/feedback/kiddushin_review_2026-05-26 (1).json and emits
tests/fixtures/wave4_text_span_cases.json with 14 cases (6 keep-full +
2 trim-correctly + 6 preserve-confirmed) per PLAN_wave4.md.

The fixture is the source of truth for tests/test_wave4_text_spans.py.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEEDBACK = ROOT / "validation" / "feedback" / "kiddushin_review_2026-05-26 (1).json"
OUT = ROOT / "tests" / "fixtures" / "wave4_text_span_cases.json"

KEEP_FULL = [
    "Kiddushin 8b_2-2",
    "Kiddushin 9a_1-1",
    "Kiddushin 9a_2-2",
    "Kiddushin 13a_3-3",
    "Kiddushin 31b_4-4",
    "Kiddushin 33a_15-15",
]

TRIM = {
    "Kiddushin 8a_9-10": "trim_first_words_line10_and_rav_ashi",
    "Kiddushin 12b_4-4": "trim_trailing_ולאו_משום_דסבירא_להו_דשמואל",
}

PRESERVE = [
    "Kiddushin 12a_13-13",
    "Kiddushin 25a_17-17",
    "Kiddushin 26b_2-2",
    "Kiddushin 26b_4-5",
    "Kiddushin 26b_10-10",
    "Kiddushin 32b_3-5",
]


def main() -> None:
    with FEEDBACK.open() as f:
        data = json.load(f)
    reviews = data["reviews"]

    cases = []
    missing = []

    for key in KEEP_FULL:
        r = reviews.get(key)
        if r is None:
            missing.append(key)
            continue
        cases.append({
            "story_key": key,
            "expected": "full",
            "jeff_verdict": r.get("verdict"),
            "jeff_notes": r.get("notes", ""),
            "rationale": "current regex over-trims; first words ARE the story",
        })

    for key, slice_label in TRIM.items():
        r = reviews.get(key)
        if r is None:
            missing.append(key)
            continue
        case = {
            "story_key": key,
            "expected": "trim",
            "trim_label": slice_label,
            "jeff_verdict": r.get("verdict"),
            "jeff_notes": r.get("notes", ""),
            "rationale": "current regex under-trims; LLM must cut framing",
        }
        if key == "Kiddushin 8a_9-10":
            case["relaxed"] = {
                "on": "2026-06-15",
                "by": "Wave 4 Phase 2 review",
                "reason": (
                    "Jeff's note asks for BOTH a start-side trim AND removal "
                    "of all of segment 10 (Rav Ashi's statement). Removing a "
                    "whole segment is a segment-boundary change, not a "
                    "text-span emit. Wave 4 only handles text-span work, so "
                    "the gate accepts start-side trim only. End-side removal "
                    "is deferred to a future segment-boundary pass."
                ),
                "jeff_quote": r.get("notes", ""),
            }
        cases.append(case)

    for key in PRESERVE:
        r = reviews.get(key)
        if r is None:
            missing.append(key)
            continue
        # SOFT fixture: silence ≠ endorsement. Jeff did not flag these in
        # his 2026-05-26 review, so we use them as regression guards
        # (Wave 4 should not introduce new trims here), NOT as positive
        # validations of any specific span output.
        cases.append({
            "story_key": key,
            "expected": "regression_guard",
            "jeff_verdict": r.get("verdict"),
            "jeff_notes": r.get("notes", ""),
            "rationale": (
                "absence of evidence, not evidence of correctness — Jeff did "
                "not flag in 2026-05-26 review. Soft guard: LLM must not "
                "error (text_span_source must be 'llm' or 'llm_kept_full'). "
                "Disagreement with regex output is acceptable; silent "
                "regression is not."
            ),
        })

    if missing:
        raise SystemExit(f"Missing keys in feedback file: {missing}")

    out = {
        "source_feedback": str(FEEDBACK.relative_to(ROOT)),
        "source_plan": "docs/history/2026-06-15-PLAN-wave4.md",
        "tractate": "Kiddushin",
        "n_cases": len(cases),
        "n_keep_full": len(KEEP_FULL),
        "n_trim": len(TRIM),
        "n_regression_guard": len(PRESERVE),
        "ship_gate": "14/14 (6 keep_full + 2 trim + 6 regression_guard soft)",
        "category_notes": {
            "keep_full": "HARD: LLM must not emit any start trim.",
            "trim": "HARD: LLM must emit the trim Jeff explicitly named.",
            "regression_guard": (
                "SOFT: silence ≠ endorsement. Pass = LLM didn't error. "
                "Disagreement with v9 regex output is allowed."
            ),
        },
        "cases": cases,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"Wrote {OUT.relative_to(ROOT)} with {len(cases)} cases")
    print(f"  keep_full={len(KEEP_FULL)}  trim={len(TRIM)}  preserve={len(PRESERVE)}")


if __name__ == "__main__":
    main()
