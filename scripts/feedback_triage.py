#!/usr/bin/env python3
"""Reader feedback triage: read the "Report a problem" issues, sort them, keep a ledger.

Plan: docs/history/2026-11-15-PLAN-reader-feedback-loop.md. Three rules it never breaks:
  1. A reader's report is a TIP (suspected), never expert evidence. Nothing here writes under
     results/canonical/, and nothing here feeds a prompt as an example.
  2. Every fix is display-only (decisions file, notes, boundary extensions). Goldens untouched.
  3. Nothing is silently dropped: an issue we cannot read is counted and NAMED.

Commands (the first four read; `close` and `route-note` write):
  pull          read EVERY open issue (no label filter), sort, write the queue + ledger
  report        print the weekly list for Simon
  close         record an outcome, comment, label and close the issue
  changelog     regenerate docs/site-feedback-log.md from the scrubbed outcomes
  route-note    put a story whose note a reader disputes on the held list (D2: redraft next)
  case          write one story's case file (for not_story / boundary review) to the local folder

Where things live (the main repo is PUBLIC, the feedback repo is private):
  results/site_feedback/outcomes.json   main repo. Ids and outcomes ONLY: no comment, no name.
  results/site_feedback/_local/         git-ignored. queue.json and case files (quote readers).
  $FEEDBACK_PRIVATE_DIR/ledger.json     the full ledger. Point this at a clone of the private
                                        feedback repo; default results/site_feedback/_private/
                                        (git-ignored). Commit it THERE, never here.
The worker's rules (categories, id pattern, caps) are read out of worker/feedback-worker.js
rather than copied, because fallback reports never passed through the worker.
"""
import argparse
import json
import logging
import os
import re
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKER_JS = ROOT / "worker/feedback-worker.js"
DATA = ROOT / "site/data"
DECISIONS = ROOT / "results/shas_run/septimus_site_decisions.json"
HELD = ROOT / "results/site_notes/held.json"
OUT_DIR = ROOT / "results/site_feedback"
OUTCOMES = OUT_DIR / "outcomes.json"
LOCAL = OUT_DIR / "_local"
PRIVATE = Path(os.environ.get("FEEDBACK_PRIVATE_DIR") or OUT_DIR / "_private")
CHANGELOG = ROOT / "docs/site-feedback-log.md"
REPO = "siguy/talmud-stories-feedback"
OUTCOME_LABELS = ["fixed", "no-change", "duplicate", "sefaria", "asked-jeff", "spam", "test"]
log = logging.getLogger("feedback-triage")


# ---- the worker's rules, read from the worker itself -------------------------------------------
def worker_rules(src=None):
    """Categories, id pattern and field caps from worker/feedback-worker.js (one definition)."""
    src = src if src is not None else WORKER_JS.read_text()
    cats = re.search(r"const CATEGORIES = \{(.*?)\};", src, re.S).group(1)
    id_re = re.search(r"const ID_RE = /(.*?)/;", src).group(1)
    max_refs = int(re.search(r"const MAX_REFS = (\d+);", src).group(1))
    caps = {m.group(1): int(m.group(2)) for m in re.finditer(r"cap\(p\.(\w+(?:\.\w+)?), (\d+)\)", src)}
    return {"categories": re.findall(r"^\s*(\w+):", cats, re.M), "id_re": re.compile(id_re), "max_refs": max_refs, "caps": caps}


# ---- reading one issue ------------------------------------------------------------------------
# Anchored to line starts: a worker issue quotes the comment with "> ", so a fence typed into it cannot open a block.
FENCE = re.compile(r"^```json\n(.*?)\n^```", re.S | re.M)


def parse_issue(issue):
    """-> (kind, payload|None, why). kind is worker / fallback / unreadable.

    The reader's comment sits OUTSIDE the machine-readable block (quoted in a worker issue,
    placed first in a fallback one), so a comment containing a fake json fence comes before
    the real block. Taking the LAST fence, never the first, is what stops it being read as data.
    """
    body = issue.get("body") or ""
    fences = FENCE.findall(body)
    if not fences:
        return "unreadable", None, "no json block in the issue body"
    try:
        payload = json.loads(fences[-1])
    except ValueError as e:
        return "unreadable", None, "json block does not parse (cut off?): %s" % str(e)[:60]
    if not isinstance(payload, dict):
        return "unreadable", None, "json block is not an object"
    kind = "worker" if "Machine-readable (for Claude)" in body else "fallback"
    return kind, payload, ""


def check_payload(p, rules):
    """Problems with a report, using the worker's own rules. A list; empty means it would pass."""
    out = []
    sid = p.get("story_id")
    if not isinstance(sid, str) or not rules["id_re"].match(sid):
        out.append("bad story_id")
    if p.get("category") not in rules["categories"]:
        out.append("unknown category")
    caps = rules["caps"]
    for field, n in (("comment", caps.get("comment", 4000)), ("summary", caps.get("summary", 600)),
                     ("name", caps.get("name", 120)), ("page_url", caps.get("page_url", 300))):
        if len(str(p.get(field) or "")) > n:
            out.append("%s over %d characters" % (field, n))
    seg = p.get("segment")
    if isinstance(seg, dict):
        for f in ("he", "en"):
            if len(str(seg.get(f) or "")) > caps.get("segment.%s" % f, 2000):
                out.append("segment.%s over cap" % f)
    if isinstance(p.get("refs"), list) and len(p["refs"]) > rules["max_refs"]:
        out.append("too many refs")
    if p.get("category") == "other" and not str(p.get("comment") or "").strip():
        out.append("empty comment on 'other'")
    return out


def tag(p):
    """site / test flags. Tags, never drops."""
    site = p.get("site") or ("staging" if "staging" in str(p.get("page_url") or "") else "prod")
    test = bool(p.get("test")) or bool(re.match(r"\s*TEST\b", str(p.get("comment") or ""), re.I))
    return site, test


# ---- today's state of a story -----------------------------------------------------------------
class SiteState:
    def __init__(self, data=DATA, decisions=DECISIONS, held=HELD):
        self.data, self.held = Path(data), {}
        self.redirects = json.loads((self.data / "redirects.json").read_text())
        self.ext = json.loads((self.data / "boundary_extensions.json").read_text())
        dec = json.loads(Path(decisions).read_text()) if Path(decisions).exists() else {}
        self.keep = (dec.get("keep") or {}).get("passages") or []
        self.remove = (dec.get("remove") or {}).get("passages") or []
        if Path(held).exists():
            self.held = json.loads(Path(held).read_text())
        self._tr = {}

    def follow(self, sid):
        """Follow redirects (a merged story). -> (id or None if retired, was_redirected)."""
        seen, cur = set(), sid
        while cur in self.redirects and cur not in seen:
            seen.add(cur)
            cur = self.redirects[cur]
            if cur is None:
                return None, True
        return cur, cur != sid

    def _tractate(self, slug):
        if slug not in self._tr:
            f = self.data / ("%s.json" % slug)
            self._tr[slug] = json.loads(f.read_text()) if f.exists() else None
        return self._tr[slug]

    def story(self, sid):
        t = self._tractate(sid.split("-")[0])
        for s in (t or {}).get("stories", []):
            if s["id"] == sid:
                return s, t
        return None, t

    def notes(self, sid):
        f = self.data / "notes" / ("%s.json" % sid.split("-")[0])
        return ((json.loads(f.read_text()) if f.exists() else {}).get("notes") or {}).get(sid)

    def lookup(self, sid):
        s, t = self.story(sid)
        if not s:
            return {"on_site": False}
        n = self.notes(sid) or {}
        kept = any(k.get("card") == sid for k in self.keep)
        return {"on_site": True, "reviewed": bool(t.get("reviewed") or s.get("reviewed")),
                "classification": s.get("classification"), "in_keep": kept,
                "extended": sid in self.ext or bool(s.get("extended")),
                "span": s.get("span"), "note_held": sid in self.held, "note_approved": bool(n.get("approved")),
                "note_drafted": n.get("drafted")}


def maybe_fixed(p, st):
    """Why a report may already be out of date, or None. Old reports lack span/note_drafted: unknown, not fixed."""
    why = []
    if p.get("span") is not None and st.get("span") is not None and p["span"] != st["span"]:
        why.append("the passage shown has changed since the report")
    if p.get("category") == "note" and p.get("note_drafted") and st.get("note_drafted") \
            and p["note_drafted"] != st["note_drafted"]:
        why.append("the note has been redrafted since the report")
    return "; ".join(why) or None


# ---- pull -------------------------------------------------------------------------------------
def build_queue(issues, state, rules):
    """Pure function of issues + site state: no network, no writes. Every issue lands somewhere."""
    items, unreadable = [], []
    for iss in issues:
        kind, p, why = parse_issue(iss)
        if p is None:
            unreadable.append({"issue": iss["number"], "title": iss.get("title", ""), "why": why})
            continue
        site, test = tag(p)
        sid, redirected = (None, False)
        if isinstance(p.get("story_id"), str) and rules["id_re"].match(p["story_id"]):
            sid, redirected = state.follow(p["story_id"])
        st = state.lookup(sid) if sid else {"on_site": False}
        items.append({"issue": iss["number"], "created": iss.get("createdAt", ""), "kind": kind, "site": site, "test": test,
                      "story_id": p.get("story_id"), "now_id": sid, "redirected": redirected,
                      "retired": sid is None and redirected,
                      "category": p.get("category"), "comment": str(p.get("comment") or "")[:4000],
                      "name": str(p.get("name") or "")[:120],
                      "segment_index": (p.get("segment") or {}).get("index") if isinstance(p.get("segment"), dict) else None,
                      "problems": check_payload(p, rules), "state": st, "maybe_fixed": maybe_fixed(p, st),
                      "labels": [l["name"] for l in iss.get("labels", [])]})
    # De-duplicate: same (current story, category, passage) = one item with a count. The count is shown, not weighed.
    groups = {}
    for it in items:
        groups.setdefault((it["now_id"] or it["story_id"], it["category"], it["segment_index"], it["site"], it["test"]), []).append(it)
    queue = []
    for g in groups.values():
        g.sort(key=lambda i: i["issue"])
        first = dict(g[0], count=len(g), issues=[i["issue"] for i in g])
        queue.append(first)
    queue.sort(key=lambda i: i["issue"])
    return {"queue": queue, "unreadable": unreadable, "n_issues": len(issues),
            "n_worker": sum(i["kind"] == "worker" for i in items), "n_fallback": sum(i["kind"] == "fallback" for i in items)}


def read_json(path, default):
    return json.loads(Path(path).read_text()) if Path(path).exists() else default


def ledger_path():
    return PRIVATE / "ledger.json"


def update_ledger(items, ledger):
    """Append-only: an issue already in the ledger keeps its report exactly as first stored."""
    added = 0
    for it in items:
        key = str(it["issue"])
        if key in ledger:
            continue
        ledger[key] = {"report": {k: it[k] for k in ("created", "kind", "site", "test", "story_id", "category", "comment", "name",
                                                  "segment_index", "problems")},
                       "outcome": None, "decided_by": None, "what": None, "commit": None, "closed": None}
        added += 1
    return added


def gh_open_issues():
    r = subprocess.run(["gh", "issue", "list", "-R", REPO, "--state", "open", "--limit", "500",
                        "--json", "number,title,body,createdAt,labels"], capture_output=True, text=True)
    if r.returncode:
        sys.exit("gh issue list failed: " + r.stderr[:300])
    return json.loads(r.stdout)


def cmd_pull(a):
    issues = json.loads(Path(a.from_file).read_text()) if a.from_file else gh_open_issues()
    log.info("feedback: %d open issues read (no label filter)", len(issues))
    q = build_queue(issues, SiteState(), worker_rules())
    log.info("feedback: %d worker, %d fallback, %d unreadable", q["n_worker"], q["n_fallback"], len(q["unreadable"]))
    LOCAL.mkdir(parents=True, exist_ok=True)
    (LOCAL / "queue.json").write_text(json.dumps(q, ensure_ascii=False, indent=1))
    PRIVATE.mkdir(parents=True, exist_ok=True)
    led = read_json(ledger_path(), {})
    by_issue = {}
    for it in q["queue"]:
        for n in it["issues"]:
            by_issue[n] = it
    rows = [dict(by_issue[n], issue=n) for n in sorted(by_issue)]
    added = update_ledger(rows, led)
    ledger_path().write_text(json.dumps(led, ensure_ascii=False, indent=1, sort_keys=True))
    write_outcomes(led)
    log.info("feedback: %d queue items, %d new ledger entries (ledger %s)", len(q["queue"]), added, ledger_path())
    print("pulled %d open issues -> %d items (%d worker, %d fallback, %d could not read); %d new in the ledger"
          % (len(issues), len(q["queue"]), q["n_worker"], q["n_fallback"], len(q["unreadable"]), added))


# ---- outcomes (public, scrubbed) ---------------------------------------------------------------
def write_outcomes(ledger):
    """Ids and outcomes ONLY. No comment text, no names: this file is committed to a public repo."""
    rows = [{"issue": int(k), "story_id": v["report"]["story_id"], "category": v["report"]["category"],
             "site": v["report"]["site"], "test": v["report"]["test"], "outcome": v["outcome"],
             "decided_by": v["decided_by"], "date": v["closed"]} for k, v in sorted(ledger.items(), key=lambda kv: int(kv[0]))]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTCOMES.write_text(json.dumps(rows, indent=1))


# ---- report -----------------------------------------------------------------------------------
def classify(it):
    """-> bucket. act now / needs Simon / route elsewhere / ignored."""
    if it["test"] or it["site"] == "staging":
        return "ignored"
    st, cat = it["state"], it["category"]
    if it["problems"]:
        return "needs Simon"
    if not st.get("on_site"):
        return "needs Simon"  # retired / unknown story
    if cat == "not_story" or st.get("reviewed") or st.get("in_keep"):
        return "needs Simon"  # D3: Jeff-reviewed tractate changes only with Simon's yes; removal is always his
    if cat in ("boundary", "note"):
        return "act now"
    return "route elsewhere"


def format_report(q):
    buckets = {"act now": [], "needs Simon": [], "route elsewhere": [], "ignored": []}
    for it in q["queue"]:
        buckets[classify(it)].append(it)
    cats, trs = {}, {}
    for it in q["queue"]:
        if classify(it) != "ignored":
            cats[it["category"]] = cats.get(it["category"], 0) + 1
            trs[(it["story_id"] or "?").split("-")[0]] = trs.get((it["story_id"] or "?").split("-")[0], 0) + 1
    out = ["%d open issues: %d worker, %d fallback, %d could not read" % (q["n_issues"], q["n_worker"], q["n_fallback"], len(q["unreadable"])),
           "by category: %s" % (cats or "none"), "by tractate: %s" % (trs or "none"), ""]
    for name in ("act now", "needs Simon", "route elsewhere"):
        out.append("== %s (%d)" % (name, len(buckets[name])))
        for it in buckets[name]:
            extra = []
            if it["count"] > 1:
                extra.append("x%d reports" % it["count"])
            if it["redirected"]:
                extra.append("story merged into %s" % it["now_id"])
            if it["maybe_fixed"]:
                extra.append("MAY ALREADY BE FIXED: %s" % it["maybe_fixed"])
            if it["problems"]:
                extra.append("RE-CHECK FAILED: %s" % ", ".join(it["problems"]))
            if it["state"].get("reviewed"):
                extra.append("Jeff-reviewed tractate")
            if it["state"].get("in_keep"):
                extra.append("Simon already kept this")
            if it["category"] == "boundary" and name == "act now":
                extra.append("queued: waits for the boundary-review tool")
            out.append("  #%s %s [%s] %s" % ("/".join(map(str, it["issues"])), it["story_id"], it["category"], "; ".join(extra)))
    if q["unreadable"]:
        out.append("== could not read (%d)" % len(q["unreadable"]))
        for u in q["unreadable"]:
            out.append("  #%d %s: %s" % (u["issue"], u["title"][:60], u["why"]))
    if buckets["ignored"]:
        out.append("== set aside, tests / staging (%d): %s" % (len(buckets["ignored"]), ", ".join("#%s" % "/".join(map(str, i["issues"])) for i in buckets["ignored"])))
    return "\n".join(out)


def cmd_report(a):
    f = LOCAL / "queue.json"
    if not f.exists():
        sys.exit("no queue yet: run `feedback_triage.py pull` first")
    print(format_report(json.loads(f.read_text())))


# ---- close, changelog, routes -----------------------------------------------------------------
def cmd_close(a):
    led = read_json(ledger_path(), {})
    key = str(a.issue)
    if key not in led:
        sys.exit("issue #%s is not in the ledger: run pull first" % key)
    if led[key]["outcome"]:
        sys.exit("issue #%s already has outcome %r; the ledger records one outcome" % (key, led[key]["outcome"]))
    e = led[key]
    e.update(outcome=a.outcome, decided_by=a.decided_by, what=a.what, closed=str(date.today()), commit=a.commit)
    ledger_path().write_text(json.dumps(led, ensure_ascii=False, indent=1, sort_keys=True))
    write_outcomes(led)
    if not a.no_github:
        subprocess.run(["gh", "label", "create", a.outcome, "-R", REPO], capture_output=True)
        subprocess.run(["gh", "issue", "comment", str(a.issue), "-R", REPO, "--body", "%s: %s" % (a.outcome.replace("-", " ").capitalize(), a.what)], check=True)
        subprocess.run(["gh", "issue", "edit", str(a.issue), "-R", REPO, "--add-label", a.outcome], check=True)
        if a.outcome != "asked-jeff":
            subprocess.run(["gh", "issue", "close", str(a.issue), "-R", REPO], check=True)
    log.info("feedback: issue %s closed with outcome %s", key, a.outcome)
    print("#%s -> %s" % (key, a.outcome))


def render_changelog(outcomes, ledger):
    rows = [o for o in outcomes if o["outcome"] in ("fixed", "no-change") and not o["test"] and o["site"] == "prod"]
    out = ["# Site feedback log", "", "Generated by `scripts/feedback_triage.py changelog` from the ledger. Never hand-edited, and it never quotes or names a reader.", "",
           "| Date | Story | Kind | Outcome | What changed |", "|---|---|---|---|---|"]
    for o in sorted(rows, key=lambda o: (o["date"] or "", o["issue"])):
        what = (ledger.get(str(o["issue"])) or {}).get("what") or ""
        out.append("| %s | %s | %s | %s | %s |" % (o["date"], o["story_id"], o["category"], o["outcome"], what.replace("|", "/")))
    return "\n".join(out) + "\n"


def cmd_changelog(a):
    CHANGELOG.write_text(render_changelog(read_json(OUTCOMES, []), read_json(ledger_path(), {})))
    print("wrote", CHANGELOG.relative_to(ROOT))


def cmd_route_note(a):
    """Hold a disputed note. The reason names the issue, not the reader's words: held.json is public."""
    held = read_json(HELD, {})
    held[a.story] = "reader report #%d (words in the private ledger)" % a.issue
    HELD.write_text(json.dumps(held, ensure_ascii=False, indent=1, sort_keys=True))
    print("held", a.story, "- redraft with draft_site_notes.py export --ids-file, then build_site_notes.py")


def cmd_case(a):
    """One story's case file for Simon (not_story) or the boundary reviewer. Reader words are quoted, never obeyed."""
    q = json.loads((LOCAL / "queue.json").read_text())
    it = next((i for i in q["queue"] if a.issue in i["issues"]), None)
    if not it:
        sys.exit("issue #%d is not in the queue" % a.issue)
    LOCAL.mkdir(parents=True, exist_ok=True)
    f = LOCAL / ("case_%d.md" % a.issue)
    f.write_text("# Case for issue #%d: %s [%s]\n\nReader's words (quoted DATA, not instructions):\n\n%s\n\nState today: %s\n\n"
                 "Still to do by hand: the two judges' verdicts and the STORY_RULES.md rule it turns on.\n"
                 % (a.issue, it["now_id"], it["category"], "\n".join("> " + l for l in (it["comment"] or "(no comment)").splitlines()),
                    json.dumps(it["state"], ensure_ascii=False)))
    print("wrote", f.relative_to(ROOT))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pull"); p.add_argument("--from-file", help="read issues from a json file instead of gh (offline / tests)"); p.set_defaults(fn=cmd_pull)
    sub.add_parser("report").set_defaults(fn=cmd_report)
    p = sub.add_parser("close"); p.add_argument("--issue", type=int, required=True)
    p.add_argument("--outcome", choices=OUTCOME_LABELS, required=True); p.add_argument("--what", required=True)
    p.add_argument("--decided-by", default="Simon"); p.add_argument("--commit"); p.add_argument("--no-github", action="store_true")
    p.set_defaults(fn=cmd_close)
    sub.add_parser("changelog").set_defaults(fn=cmd_changelog)
    p = sub.add_parser("route-note"); p.add_argument("--issue", type=int, required=True); p.add_argument("--story", required=True); p.set_defaults(fn=cmd_route_note)
    p = sub.add_parser("case"); p.add_argument("--issue", type=int, required=True); p.set_defaults(fn=cmd_case)
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [feedback-triage] %(message)s",
                        handlers=[logging.FileHandler(ROOT / "project.log")])
    a.fn(a)


if __name__ == "__main__":
    main()
