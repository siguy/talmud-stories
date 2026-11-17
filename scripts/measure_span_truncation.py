#!/usr/bin/env python3
"""How often does a story's span stop before the thing that happens?

TWO PASSES over every accepted golden span, asking one question each time:
does anything non-speech happen HERE?

  pass 1  the span exactly as we publish it
  pass 2  the same span plus up to N following segments

A span that reads speech-only in pass 1 and eventful in pass 2 was never a criteria
case. The story is real; our boundary stopped before its action. That passage then
looks like legal dialogue to every downstream consumer -- the classifier, the
confidence band, and Jeff.

Found by hand in 3 of 6 entries (PR #36), measured at 9 of 13 on a follow-up sample.
This is the corpus-wide rate.

The screen is the same question and the same tiers as scripts/screen_quasi_speech_acts.py.
Thinking is deliberately LOW: this is a narrow factual question, not a judgement call, and
pass 2 must not differ from pass 1 in anything but the text.

Usage:
  python3 scripts/measure_span_truncation.py [--extend 2] [--limit N] [--workers 8]
"""
import argparse, json, os, re, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

for line in (ROOT / ".env").read_text().splitlines():
    if "=" in line and not line.strip().startswith("#"):
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

from google import genai
from google.genai import types

TAG = re.compile(r"<[^>]+>")
clean = lambda s: TAG.sub("", s or "").strip()

PROMPT = (ROOT / "scripts/screen_quasi_speech_acts.py").read_text().split('PROMPT = """')[1].split('"""')[0]


def spans(extend):
    out = []
    for tract in ("ketubot", "kiddushin", "gittin"):
        d = json.load(open(ROOT / f"results/canonical/{tract}_canonical.json"))
        for page in d["pages"]:
            segs = {s["index"]: s for s in page.get("segments", [])}
            if not segs:
                continue
            for i, st in enumerate(page.get("stories", [])):
                if st.get("classification") == "NOT_A_STORY":
                    continue
                a, b = st.get("start_segment"), st.get("end_segment")
                if a is None or b is None:
                    continue
                inner = [j for j in range(a, b + 1) if j in segs]
                outer = [j for j in range(a, b + 1 + extend) if j in segs]
                if not inner:
                    continue
                out.append({
                    "id": f"{tract}:{page['ref']}:{a}-{b}:{i}",
                    "tractate": tract, "ref": page["ref"],
                    "start_segment": a, "end_segment": b,
                    "classification": st.get("classification"),
                    "extra_segments": len(outer) - len(inner),
                    "summary": (st.get("one_sentence_summary") or "")[:160],
                    "_inner": ("\n".join(clean(segs[j]["hebrew"]) for j in inner),
                               "\n".join(clean(segs[j]["english"]) for j in inner)),
                    "_outer": ("\n".join(clean(segs[j]["hebrew"]) for j in outer),
                               "\n".join(clean(segs[j]["english"]) for j in outer)),
                })
    return out


def parse(txt):
    c = txt.split("```")[1] if "```" in txt else txt
    c = c[4:] if c.startswith("json") else c
    i, j = c.find("{"), c.rfind("}")
    return json.loads(c[i:j + 1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--extend", type=int, default=2)
    ap.add_argument("--limit", type=int)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--model", default="gemini-3.8-flash")
    ap.add_argument("--out", default="results/criteria/span_truncation_rate.json")
    args = ap.parse_args()

    rows = spans(args.extend)
    if args.limit:
        rows = rows[:args.limit]
    print(f"{len(rows)} accepted golden spans, extend=+{args.extend}", flush=True)
    client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

    def ask(he, en):
        for attempt in range(3):
            try:
                r = client.models.generate_content(
                    model=args.model,
                    contents=PROMPT.format(hebrew=he[:12000], english=en[:12000]),
                    config=types.GenerateContentConfig(
                        max_output_tokens=8192, temperature=0.1,
                        response_mime_type="application/json",
                        thinking_config=types.ThinkingConfig(thinking_level="LOW")))
                t = "".join(p.text for p in r.candidates[0].content.parts
                            if p.text and not getattr(p, "thought", False))
                return parse(t)
            except Exception as e:
                if attempt == 2:
                    return {"error": str(e)[:160]}
                time.sleep(2 * (attempt + 1))

    def run(row):
        inner = ask(*row["_inner"])
        outer = ask(*row["_outer"]) if row["extra_segments"] else dict(inner)
        row = {k: v for k, v in row.items() if not k.startswith("_")}
        row["in_span"] = inner.get("verdict")
        row["extended"] = outer.get("verdict")
        row["revealed_english"] = outer.get("evidence_english", "")
        row["revealed_hebrew"] = outer.get("evidence_hebrew", "")
        row["error"] = inner.get("error") or outer.get("error")
        return row

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        res = list(ex.map(run, rows))

    from collections import Counter
    speech = [r for r in res if r["in_span"] == "speech_only"]
    flipped = [r for r in speech if r["extended"] == "non_speech_event"]
    errs = [r for r in res if r.get("error")]
    rate = (len(flipped) / len(speech) * 100) if speech else 0.0

    payload = {
        "measured": time.strftime("%Y-%m-%d"),
        "model": args.model, "thinking": "low", "extend": args.extend,
        "question": "does a span that reads speech-only become eventful when extended?",
        "spans_screened": len(res), "errors": len(errs),
        "speech_only_in_span": len(speech),
        "flipped_when_extended": len(flipped),
        "truncation_rate_pct": round(rate, 1),
        "by_tractate": {f"{t}": {
            "spans": sum(1 for r in res if r["tractate"] == t),
            "speech_only": sum(1 for r in speech if r["tractate"] == t),
            "flipped": sum(1 for r in flipped if r["tractate"] == t)} for t in
            ("ketubot", "kiddushin", "gittin")},
        "by_classification": dict(Counter(r["classification"] for r in flipped)),
        "elapsed_s": round(time.time() - t0),
        "note": "MEASUREMENT ONLY. No golden changed, no boundary moved.",
        "spans": res,
    }
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    print(json.dumps({k: v for k, v in payload.items() if k != "spans"}, indent=2))
    print(f"\n-> {out}")


if __name__ == "__main__":
    main()
