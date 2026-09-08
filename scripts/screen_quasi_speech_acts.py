#!/usr/bin/env python3
"""Wave 6 Phase 6a — measure the speech-act blast radius.

Classifies every LOW_CONFIDENCE golden story on ONE axis:
does anything NON-SPEECH happen?  (physical event, or the emotional/internal
reaction Jeff 2026-07-06 says counts).

This is a MEASUREMENT. Nothing in the golden changes. Output is the number and
the examples that go to Jeff so the speech-act policy question is answered with
evidence instead of intuition.

Prompt carries ABSTRACT PATTERNS only, never the golden's own passages (Lesson 8).

Usage:
  python3 scripts/measure_speech_act_blast_radius.py [--model gemini-3-flash-preview] [--limit N]
"""
import argparse, json, os, re, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
from src.speech_act_lexicon import (TIER1_SPEECH_ACTS, TIER2_SCRUTINY,  # noqa
                                    TIER3_REAL_EVENTS, surface_flags)

for line in (ROOT / ".env").read_text().splitlines():
    if "=" in line and not line.strip().startswith("#"):
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

from google import genai
from google.genai import types

TAG = re.compile(r"<[^>]+>")


def clean(s):
    return TAG.sub("", s or "").strip()


PROMPT = """You are helping decide whether a Talmudic passage records a STORY or is
legal discussion in narrative clothing.

Judge ONE question only: **does anything non-speech happen in this passage?**

WHAT COUNTS AS A NON-SPEECH EVENT
  physical  — someone moves, travels, arrives, finds, takes, gives, strikes, buys,
              sells, marries, divorces, falls ill, dies; an object changes hands or
              state; something is done in the world.
  emotional — an internal or emotional change in a person: embarrassment, shame,
              distress, anger, fear, grief, joy. This DOES count as an event.

WHAT DOES NOT COUNT — speech-acts and quasi speech-acts
  Verbal activity is not an event, however dramatic its verb. Saying, stating,
  replying, answering, asking, objecting, raising a difficulty, ruling, teaching,
  reciting, citing, expounding, permitting, prohibiting — all speech.

  Some verbs LOOK like actions but are speech-acts when their object is verbal.
  Judge the object, not the verb:
    - "sent" — sending a MESSAGE or a QUESTION to a sage is speech; sending a
      messenger, a gift, or a document is physical.
    - "retracted" — retracting an OPINION or ruling is speech; physically
      retracting or cancelling a written document is physical.
    - "considered", "thought", "held", "reasoned" — deliberation about the law is
      speech-like reasoning, NOT the emotional reaction described above.
    - "came before" / "brought before" a sage — this is the framing of a legal
      query, not an event, unless the passage narrates the journey or what
      physically occurred.
    - "sat", "was sitting", "stood" — scene-setting for a discussion is not an
      event.

  A hypothetical case ("if a man does X...") is never an event, no matter how much
  action it describes. Only what is narrated as actually having happened counts.

PASSAGE (Hebrew/Aramaic):
{hebrew}

PASSAGE (English translation):
{english}

Return ONLY valid JSON:
{{"verdict": "non_speech_event" | "speech_only",
  "event_kind": "physical" | "emotional" | "both" | "none",
  "evidence_english": "<the shortest phrase showing the event, or empty>",
  "evidence_hebrew": "<the corresponding Hebrew/Aramaic words, or empty>",
  "quasi_speech_acts": ["<verbs in this passage that look like actions but are speech>"],
  "confidence": "high" | "medium" | "low",
  "why": "<one sentence>"}}"""


def load_stories():
    out = []
    for tract in ("ketubot", "kiddushin"):
        d = json.load(open(ROOT / f"results/canonical/{tract}_canonical.json"))
        for page in d["pages"]:
            segs = {s["index"]: s for s in page.get("segments", [])}
            for i, st in enumerate(page.get("stories", [])):
                if st.get("classification") != "LOW_CONFIDENCE":
                    continue
                a, b = st.get("start_segment"), st.get("end_segment")
                if a is None or b is None:
                    continue
                idxs = [j for j in range(a, b + 1) if j in segs]
                he = "\n".join(clean(segs[j]["hebrew"]) for j in idxs)
                en = "\n".join(clean(segs[j]["english"]) for j in idxs)
                if not en.strip():
                    continue
                out.append({
                    "id": f"{tract}:{page['ref']}:{a}-{b}:{i}",
                    "tractate": tract, "ref": page["ref"],
                    "start_segment": a, "end_segment": b,
                    "summary": st.get("one_sentence_summary", ""),
                    "hebrew": he, "english": en,
                })
    return out


def parse(txt):
    c = txt
    if "```" in c:
        c = c.split("```")[1]
        c = c[4:] if c.startswith("json") else c
    i, j = c.find("{"), c.rfind("}")
    return json.loads(c[i:j + 1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=os.getenv("GEMINI_MODEL", "gemini-3-flash-preview"))
    ap.add_argument("--limit", type=int)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--out", default="results/criteria/speech_act_blast_radius.json")
    args = ap.parse_args()

    stories = load_stories()
    if args.limit:
        stories = stories[:args.limit]
    print(f"{len(stories)} LOW_CONFIDENCE golden stories", flush=True)

    client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

    def run(s):
        p = PROMPT.format(hebrew=s["hebrew"][:12000], english=s["english"][:12000])
        for attempt in range(3):
            try:
                r = client.models.generate_content(
                    model=args.model, contents=p,
                    config=types.GenerateContentConfig(
                        max_output_tokens=8192, temperature=0.1,
                        response_mime_type="application/json",
                        thinking_config=types.ThinkingConfig(thinking_level="LOW"),
                    ))
                txt = "".join(part.text for part in r.candidates[0].content.parts
                              if part.text and not getattr(part, "thought", False))
                v = parse(txt)
                v["error"] = None
                return {**s, "verdict_obj": v, "surface": surface_flags(s["english"] + " " + s["hebrew"])}
            except Exception as e:
                if attempt == 2:
                    return {**s, "verdict_obj": {"error": str(e)[:200]},
                            "surface": surface_flags(s["english"] + " " + s["hebrew"])}
                time.sleep(2 * (attempt + 1))

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        results = list(ex.map(run, stories))

    for r in results:
        r.pop("hebrew"), r.pop("english")

    from collections import Counter
    verdicts = Counter(r["verdict_obj"].get("verdict", "ERROR") for r in results)
    kinds = Counter(r["verdict_obj"].get("event_kind", "ERROR") for r in results)
    by_tract = Counter((r["tractate"], r["verdict_obj"].get("verdict", "ERROR")) for r in results)

    payload = {
        "generated": time.strftime("%Y-%m-%d %H:%M"),
        "model": args.model,
        "phase": "wave6-6a",
        "note": "MEASUREMENT ONLY. Nothing in the golden was relabelled.",
        "n": len(results),
        "verdicts": dict(verdicts),
        "event_kinds": dict(kinds),
        "by_tractate": {f"{k[0]}:{k[1]}": v for k, v in by_tract.items()},
        "stories": results,
    }
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2))

    print(json.dumps({"verdicts": dict(verdicts), "event_kinds": dict(kinds),
                      "by_tractate": payload["by_tractate"]}, indent=2))
    print(f"\n-> {out}")


if __name__ == "__main__":
    main()
