// Cloudflare Worker: receives feedback from the family site and files it as a GitHub issue,
// so Claude (or anyone) can read it straight from the repo: label `story-feedback`.
// The GitHub token lives only here, as a secret; the site never sees it. See worker/README.md.

const CATEGORIES = {
  hebrew: "Hebrew text looks wrong",
  translation: "English translation is wrong or unclear",
  not_story: "This isn't really a story",
  boundary: "Story starts or ends in the wrong place",
  other: "Something else",
};
// Any tractate slug from scripts/tractates.py (lowercase, underscores: avodah_zarah). It was the 4 reviewed
// tractates only, so feedback on the other 33 was rejected after the site grew to all of Shas.
const ID_RE = /^[a-z]+(_[a-z]+)*-\d+[ab]-\d+-\d+$/;
// A story spans at most a few pages: two in today's data, more once a display-only extension
// (start_back <= 2, end_forward <= 4 segments) crosses a page break. 10 is headroom, not a limit anyone hits.
const MAX_REFS = 10;
const cap = (v, n) => String(v == null ? "" : v).slice(0, n);

export function buildIssue(p) {
  if (!p || !ID_RE.test(p.story_id || "")) throw new Error("bad story_id");
  // hasOwn, not CATEGORIES[...]: "__proto__", "toString" and "constructor" are truthy inherited keys.
  if (typeof p.category !== "string" || !Object.hasOwn(CATEGORIES, p.category)) throw new Error("bad category");
  const comment = cap(p.comment, 4000).trim();
  if (!comment && p.category === "other") throw new Error("empty comment");
  // Only these fields are copied, each capped, so a hostile payload cannot smuggle structure.
  const data = {
    // The tractate comes from the validated id, never from the payload: it becomes a GitHub label,
    // so a free-text field here could mint arbitrary labels (and a 20-char cap would cut a long slug).
    story_id: p.story_id, tractate: p.story_id.split("-")[0], ref: cap(p.ref, 40),
    refs: Array.isArray(p.refs) ? p.refs.slice(0, MAX_REFS).map((r) => cap(r, 40)) : [],
    reviewed: !!p.reviewed, in_mishnah: !!p.in_mishnah, summary: cap(p.summary, 600),
    category: p.category, comment,
    segment: p.segment ? { ref: cap(p.segment.ref, 40), index: Number.isInteger(p.segment.index) ? p.segment.index : null,
      he: cap(p.segment.he, 2000), en: cap(p.segment.en, 2000) } : null,
    name: cap(p.name, 120), page_url: cap(p.page_url, 300), submitted_at: new Date().toISOString(),
  };
  const where = data.segment ? `${data.segment.ref} segment ${data.segment.index}` : data.ref;
  const body = [
    `**${CATEGORIES[data.category]}** — ${data.ref} (${data.story_id})`,
    data.comment ? `> ${data.comment.replace(/\n/g, "\n> ")}` : "",
    data.name ? `From: ${data.name}` : "From: (anonymous)",
    "", "<details><summary>Machine-readable (for Claude)</summary>", "", "```json",
    JSON.stringify(data, null, 2).replace(/```/g, "'''"), "```", "</details>",
  ].join("\n");
  return { title: `[Feedback] ${where}: ${CATEGORIES[data.category]}`, body, labels: ["story-feedback", `tractate:${data.tractate}`] };
}

const cors = (env) => ({
  "Access-Control-Allow-Origin": env.ALLOWED_ORIGIN || "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
});

export default {
  async fetch(req, env) {
    if (req.method === "OPTIONS") return new Response(null, { headers: cors(env) });
    if (req.method !== "POST") return new Response("POST only", { status: 405, headers: cors(env) });
    let payload;
    try { payload = await req.json(); } catch { return new Response("bad json", { status: 400, headers: cors(env) }); }
    if (payload && payload.website) return new Response("ok", { headers: cors(env) }); // honeypot: bots fill it, people never see it
    let issue;
    try { issue = buildIssue(payload); } catch (e) { return new Response(e.message, { status: 400, headers: cors(env) }); }
    let r;
    // A network failure must answer 502, not throw: on Cloud Run an unhandled rejection takes the whole process down.
    try {
      r = await fetch(`https://api.github.com/repos/${env.REPO}/issues`, {
        method: "POST",
        headers: { Authorization: `Bearer ${env.GITHUB_TOKEN}`, Accept: "application/vnd.github+json", "User-Agent": "septimus-feedback", "Content-Type": "application/json" },
        body: JSON.stringify(issue),
      });
    } catch (e) { console.error("github unreachable", String(e).slice(0, 300)); return new Response("upstream error", { status: 502, headers: cors(env) }); }
    if (!r.ok) console.error("github", r.status, (await r.text()).slice(0, 300)); // visible in the host's logs, never sent to the browser
    return new Response(r.ok ? "ok" : "upstream error", { status: r.ok ? 200 : 502, headers: cors(env) });
  },
};
