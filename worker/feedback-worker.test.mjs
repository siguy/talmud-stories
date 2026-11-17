// Tests for the feedback worker. Run: `node --test worker/` (also run by tests/test_feedback_worker.py).
// No network: GitHub is a mocked `fetch`, and the Cloud Run wrapper is spawned locally with fetch mocked too.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync, mkdtempSync, copyFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { spawn } from "node:child_process";
import net from "node:net";
import worker, { buildIssue } from "./feedback-worker.js";

const HERE = dirname(fileURLToPath(import.meta.url));
const DATA = join(HERE, "..", "site", "data");
const machine = (issue) => JSON.parse(issue.body.split("```json\n")[1].split("\n```")[0]);

// The payload exactly as site/app.js builds it (wireFeedback), for one story and optionally one passage.
function payloadFor(s, segIndex = null, extra = {}) {
  const g = segIndex == null ? null : s.segments[segIndex];
  return {
    story_id: s.id, tractate: s.tractate, ref: s.ref, refs: s.refs, reviewed: s.reviewed, in_mishnah: s.in_mishnah,
    summary: s.summary, category: "translation", comment: "",
    segment: g ? { ref: g.ref, index: g.i, he: g.he, en: g.en } : null,
    name: "", website: "", page_url: "http://localhost/#/s/" + s.id, ...extra,
  };
}
const stories = readdirSync(DATA).filter((f) => f.endsWith(".json") && !["index.json", "boundary_extensions.json"].includes(f))
  .map((f) => JSON.parse(readFileSync(join(DATA, f), "utf8")))
  .filter((d) => Array.isArray(d.stories))   // tractate files only: not story_ids.json / redirects.json
  .flatMap((d) => d.stories);

const ok = { story_id: "ketubot-20a-2-3", tractate: "ketubot", ref: "Ketubot 20a", category: "translation",
  comment: "line 2 is unclear\n```x```", segment: { ref: "Ketubot 20a", index: 2, he: "א", en: "b" }, name: "Dana" };

// ---- buildIssue -------------------------------------------------------------------------------
test("every story on the site passes buildIssue, whole-story and per-passage, with nothing dropped", () => {
  assert.ok(stories.length > 1000, `only ${stories.length} stories read`);
  const tractates = new Set();
  for (const s of stories) {
    const whole = buildIssue(payloadFor(s));
    const d = machine(whole);
    assert.equal(d.story_id, s.id);
    assert.equal(d.tractate, s.tractate, s.id);
    assert.ok(whole.labels.includes(`tractate:${s.tractate}`), s.id);
    assert.deepEqual(d.refs, s.refs, s.id);
    assert.equal(d.ref, s.ref, s.id);
    assert.equal(d.summary, s.summary || "", s.id);
    const last = s.segments.length - 1;
    const one = machine(buildIssue(payloadFor(s, last)));
    assert.equal(one.segment.ref, s.segments[last].ref, s.id);
    assert.equal(one.segment.index, s.segments[last].i, s.id);
    tractates.add(s.tractate);
  }
  assert.ok(tractates.has("avodah_zarah") && tractates.has("rosh_hashanah") && tractates.has("ketubot"));
});

test("title, labels and the machine-readable block", () => {
  const i = buildIssue(ok);
  assert.ok(i.title.includes("Ketubot 20a segment 2"));
  assert.deepEqual(i.labels, ["story-feedback", "tractate:ketubot"]);
  assert.ok(!i.body.split("```json")[1].split("```")[0].includes("```"), "a comment's fence must not close the JSON block");
  const whole = buildIssue({ ...ok, segment: null });
  assert.ok(whole.title.startsWith("[Feedback] Ketubot 20a: "));
  assert.ok(whole.body.includes("From: (anonymous)") === false && whole.body.includes("From: Dana"));
  assert.ok(buildIssue({ ...ok, name: "" }).body.includes("From: (anonymous)"));
});

test("bad story ids are rejected", () => {
  for (const id of ["x; DROP", "", "Ketubot-20a-2-3", "ketubot-20c-2-3", "ketubot-20a-2", "ketubot_-20a-1-1", "_ketubot-20a-1-1",
    "ketubot-20a-1-1\n", "../ketubot-20a-1-1", "ketubot2-20a-1-1", "ketubot-20a-1-1-v", "ketubot-20a-1-1-2", "ketubot-20a-1-1-v2-v3",
    undefined, null, 7]) {
    assert.throws(() => buildIssue({ ...ok, story_id: id }), /bad story_id/, String(id));
  }
  assert.throws(() => buildIssue(null), /bad story_id/);
  assert.throws(() => buildIssue("string"), /bad story_id/);
});

test("a permanent id minted with a -vN suffix is accepted (scripts/story_ids.py)", () => {
  const d = machine(buildIssue({ ...ok, story_id: "ketubot-20a-2-3-v2" }));
  assert.equal(d.story_id, "ketubot-20a-2-3-v2");
  assert.equal(d.tractate, "ketubot");
});

test("bad categories are rejected; 'other' needs a comment", () => {
  for (const c of ["zzz", "", undefined, "__proto__", "toString", "constructor"]) assert.throws(() => buildIssue({ ...ok, category: c }), /bad category/, String(c));
  assert.throws(() => buildIssue({ ...ok, category: "other", comment: " " }), /empty comment/);
  assert.doesNotThrow(() => buildIssue({ ...ok, category: "other", comment: "x" }));
  for (const c of ["hebrew", "translation", "not_story", "boundary"]) assert.doesNotThrow(() => buildIssue({ ...ok, category: c, comment: "" }));
});

test("the tractate label comes from the id, not from the payload", () => {
  const d = machine(buildIssue({ ...ok, story_id: "rosh_hashanah-14a-10-10", tractate: "evil label, very long indeed" }));
  assert.equal(d.tractate, "rosh_hashanah");
  assert.deepEqual(buildIssue({ ...ok, story_id: "avodah_zarah-2b-1-15", tractate: undefined }).labels, ["story-feedback", "tractate:avodah_zarah"]);
});

test("every field is capped and only whitelisted fields are copied", () => {
  const big = "א".repeat(10000);
  const d = machine(buildIssue({ ...ok, comment: big, ref: big, summary: big, name: big, page_url: big,
    refs: Array.from({ length: 50 }, () => big), segment: { ref: big, index: 3, he: big, en: big },
    reviewed: "yes", in_mishnah: 0, classification: "HIGH", __proto__: { x: 1 }, extra: "smuggled" }));
  assert.equal(d.comment.length, 4000); assert.equal(d.ref.length, 40); assert.equal(d.summary.length, 600);
  assert.equal(d.name.length, 120); assert.equal(d.page_url.length, 300);
  assert.equal(d.refs.length, 10); assert.ok(d.refs.every((r) => r.length === 40));
  assert.equal(d.segment.ref.length, 40); assert.equal(d.segment.he.length, 2000); assert.equal(d.segment.en.length, 2000);
  assert.equal(d.reviewed, true); assert.equal(d.in_mishnah, false);
  assert.equal(d.extra, undefined); assert.equal(d.classification, undefined);
  assert.deepEqual(Object.keys(d).sort(), ["category", "comment", "extended", "in_mishnah", "name", "note_approved", "note_drafted",
    "page_url", "ref", "refs", "reviewed", "segment", "site", "span", "story_id", "submitted_at", "summary", "test", "tractate"]);
});

test("refs: up to 10 kept (an extended story can cross more than two pages); non-array becomes []", () => {
  const refs = ["Ketubot 20a", "Ketubot 20b", "Ketubot 21a"];
  assert.deepEqual(machine(buildIssue({ ...ok, refs })).refs, refs);
  assert.deepEqual(machine(buildIssue({ ...ok, refs: "Ketubot 20a" })).refs, []);
});

test("segment index must be an integer", () => {
  assert.equal(machine(buildIssue({ ...ok, segment: { ...ok.segment, index: "2" } })).segment.index, null);
  assert.equal(machine(buildIssue({ ...ok, segment: { ...ok.segment, index: 0 } })).segment.index, 0);
});

// ---- the request handler ----------------------------------------------------------------------
const ENV = { REPO: "owner/repo", GITHUB_TOKEN: "test-token", ALLOWED_ORIGIN: "https://site.example" };
const post = (body, headers = { "Content-Type": "application/json" }) =>
  new Request("https://w.invalid/", { method: "POST", headers, body: typeof body === "string" ? body : JSON.stringify(body) });

function mockFetch(t, impl = async () => new Response("{}", { status: 201 })) {
  const calls = [];
  t.mock.method(globalThis, "fetch", async (url, init) => { calls.push({ url: String(url), init }); return impl(url, init); });
  t.mock.method(console, "error", () => {});
  return calls;
}

test("OPTIONS preflight answers with CORS headers and calls nothing", async (t) => {
  const calls = mockFetch(t);
  const r = await worker.fetch(new Request("https://w.invalid/", { method: "OPTIONS" }), ENV);
  assert.equal(r.status, 200);
  assert.equal(r.headers.get("Access-Control-Allow-Origin"), "https://site.example");
  assert.equal(r.headers.get("Access-Control-Allow-Methods"), "POST, OPTIONS");
  assert.equal(r.headers.get("Access-Control-Allow-Headers"), "Content-Type");
  assert.equal(calls.length, 0);
});

test("CORS origin falls back to * only when ALLOWED_ORIGIN is unset", async (t) => {
  mockFetch(t);
  const r = await worker.fetch(new Request("https://w.invalid/", { method: "OPTIONS" }), { ...ENV, ALLOWED_ORIGIN: undefined });
  assert.equal(r.headers.get("Access-Control-Allow-Origin"), "*");
});

test("non-POST methods get 405", async (t) => {
  const calls = mockFetch(t);
  for (const m of ["GET", "PUT", "DELETE"]) {
    const r = await worker.fetch(new Request("https://w.invalid/", { method: m }), ENV);
    assert.equal(r.status, 405, m);
    assert.equal(r.headers.get("Access-Control-Allow-Origin"), "https://site.example");
  }
  assert.equal(calls.length, 0);
});

test("malformed JSON gets 400 'bad json'; invalid payloads get 400 with the reason; nothing reaches GitHub", async (t) => {
  const calls = mockFetch(t);
  let r = await worker.fetch(post("{not json"), ENV);
  assert.equal(r.status, 400); assert.equal(await r.text(), "bad json");
  r = await worker.fetch(post(""), ENV);
  assert.equal(r.status, 400);
  r = await worker.fetch(post({ ...ok, story_id: "nope" }), ENV);
  assert.equal(r.status, 400); assert.equal(await r.text(), "bad story_id");
  r = await worker.fetch(post("null"), ENV);
  assert.equal(r.status, 400);
  assert.equal(calls.length, 0);
});

test("honeypot: a filled 'website' field is answered ok and never filed", async (t) => {
  const calls = mockFetch(t);
  const r = await worker.fetch(post({ ...ok, website: "http://spam" }), ENV);
  assert.equal(r.status, 200); assert.equal(calls.length, 0);
});

test("a valid submission (non-reviewed tractate) files one issue with the right request", async (t) => {
  const calls = mockFetch(t);
  const s = stories.find((x) => x.tractate === "avodah_zarah");
  const r = await worker.fetch(post(payloadFor(s, 0, { comment: "typo", name: "Dana" })), ENV);
  assert.equal(r.status, 200); assert.equal(await r.text(), "ok");
  assert.equal(r.headers.get("Access-Control-Allow-Origin"), "https://site.example");
  assert.equal(calls.length, 1);
  const { url, init } = calls[0];
  assert.equal(url, "https://api.github.com/repos/owner/repo/issues");
  assert.equal(init.method, "POST");
  assert.equal(init.headers.Authorization, "Bearer test-token");
  assert.equal(init.headers.Accept, "application/vnd.github+json");
  assert.ok(init.headers["User-Agent"]);
  const issue = JSON.parse(init.body);
  assert.deepEqual(issue.labels, ["story-feedback", "tractate:avodah_zarah"]);
  assert.ok(issue.title.startsWith(`[Feedback] ${s.segments[0].ref} segment ${s.segments[0].i}: `));
  assert.equal(machine(issue).story_id, s.id);
  assert.equal(machine(issue).comment, "typo");
});

test("GitHub refusing the issue gives 502; the error body is logged, never returned", async (t) => {
  mockFetch(t, async () => new Response("Bad credentials secret-detail", { status: 401 }));
  const r = await worker.fetch(post(ok), ENV);
  assert.equal(r.status, 502); assert.equal(await r.text(), "upstream error");
  assert.equal(console.error.mock.calls.length, 1);
});

test("GitHub unreachable (fetch throws) gives 502 instead of throwing", async (t) => {
  mockFetch(t, async () => { throw new TypeError("fetch failed"); });
  const r = await worker.fetch(post(ok), ENV);
  assert.equal(r.status, 502);
});

// ---- the Cloud Run wrapper (worker/gcp/server.js), the thing actually deployed -------------------
const freePort = () => new Promise((res) => { const s = net.createServer().listen(0, () => { const p = s.address().port; s.close(() => res(p)); }); });

async function startServer(t, githubStatus) {
  // Lay the files out as deploy.sh does (server.js next to feedback-worker.js), plus a preload that mocks fetch.
  const dir = mkdtempSync(join(tmpdir(), "fbw-"));
  copyFileSync(join(HERE, "gcp", "server.js"), join(dir, "server.js"));
  copyFileSync(join(HERE, "gcp", "package.json"), join(dir, "package.json"));
  copyFileSync(join(HERE, "feedback-worker.js"), join(dir, "feedback-worker.js"));
  writeFileSync(join(dir, "mock.mjs"), `globalThis.fetch = async (u) => {
    if (!String(u).startsWith("https://api.github.com/")) throw new Error("unexpected fetch " + u);
    if (${githubStatus} === 0) throw new TypeError("fetch failed");
    return new Response("{}", { status: ${githubStatus} }); };`);
  const port = await freePort();
  const child = spawn(process.execPath, ["--import", join(dir, "mock.mjs"), join(dir, "server.js")],
    { env: { PATH: process.env.PATH, PORT: String(port), REPO: "owner/repo", GITHUB_TOKEN: "t", ALLOWED_ORIGIN: "https://site.example" }, stdio: "pipe" });
  t.after(() => child.kill());
  const base = `http://127.0.0.1:${port}/`;
  for (let i = 0; i < 100; i++) { try { await fetch(base, { method: "OPTIONS" }); return { base, child }; } catch { await new Promise((r) => setTimeout(r, 50)); } }
  throw new Error("server did not start");
}

test("server.js: a real HTTP round trip files the issue and passes CORS through", async (t) => {
  const { base } = await startServer(t, 201);
  let r = await fetch(base, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(ok) });
  assert.equal(r.status, 200); assert.equal(r.headers.get("access-control-allow-origin"), "https://site.example");
  r = await fetch(base, { method: "OPTIONS" });
  assert.equal(r.status, 200);
  r = await fetch(base, { method: "POST", body: "{bad" });
  assert.equal(r.status, 400);
});

test("server.js: a body over 100 KB is refused", async (t) => {
  const { base } = await startServer(t, 201);
  const r = await fetch(base, { method: "POST", headers: { "Content-Type": "application/json" }, body: "x".repeat(200000) }).catch((e) => e);
  // Either a clean 413, or the socket is closed on us; never a filed issue.
  if (r instanceof Response) assert.equal(r.status, 413);
});

test("server.js: GitHub unreachable answers 502 and the process stays up", async (t) => {
  const { base, child } = await startServer(t, 0);
  let r = await fetch(base, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(ok) });
  assert.equal(r.status, 502);
  r = await fetch(base, { method: "OPTIONS" });
  assert.equal(r.status, 200);
  assert.equal(child.exitCode, null);
});

// ---- 2026-11-15: reader feedback loop (docs/history/2026-11-15-PLAN-reader-feedback-loop.md) -------
test("the app's category list and the worker's are the same list, in the same words", () => {
  const app = readFileSync(join(HERE, "..", "site", "app.js"), "utf8");
  const block = app.match(/var CATS = \[(.*?)\];\n/s)[1];
  const appCats = [...block.matchAll(/\["(\w+)", "([^"]+)"\]/g)].map((m) => m[1]).sort();
  const src = readFileSync(join(HERE, "feedback-worker.js"), "utf8");
  const workerCats = [...src.match(/const CATEGORIES = \{(.*?)\};/s)[1].matchAll(/^\s*(\w+):/gm)].map((m) => m[1]).sort();
  assert.deepEqual(appCats, workerCats);
  assert.ok(workerCats.includes("note"));
});

test("a 'note' report keeps the new intake fields, capped, and defaults them when absent", () => {
  const full = machine(buildIssue({ ...ok, category: "note", span: [{ ref: "Ketubot 20a", start: 2, end: 9 }, { ref: "x".repeat(99), start: "2", end: null }],
    extended: 1, note_drafted: "d".repeat(99), note_approved: true, site: "staging", test: true }));
  assert.deepEqual(full.span[0], { ref: "Ketubot 20a", start: 2, end: 9 });
  assert.equal(full.span[1].ref.length, 40); assert.equal(full.span[1].start, null);
  assert.equal(full.extended, true); assert.equal(full.note_drafted.length, 40); assert.equal(full.note_approved, true);
  assert.equal(full.site, "staging"); assert.equal(full.test, true);
  const bare = machine(buildIssue(ok));
  assert.deepEqual([bare.span, bare.extended, bare.note_drafted, bare.site, bare.test], [[], false, "", "prod", false]);
  assert.equal(machine(buildIssue({ ...ok, site: "<script>" })).site, "prod");
  assert.equal(buildIssue({ ...ok, category: "note" }).title.endsWith("The background note is wrong"), true);
});

test("ALLOWED_ORIGIN may list production and staging: the caller's origin is echoed only if listed", async (t) => {
  mockFetch(t);
  const env = { ...ENV, ALLOWED_ORIGIN: "https://site.example, https://staging.example" };
  const ask = (origin) => worker.fetch(new Request("https://w.invalid/", { method: "OPTIONS", headers: origin ? { Origin: origin } : {} }), env);
  assert.equal((await ask("https://staging.example")).headers.get("Access-Control-Allow-Origin"), "https://staging.example");
  assert.equal((await ask("https://evil.example")).headers.get("Access-Control-Allow-Origin"), "https://site.example");
  assert.equal((await ask(null)).headers.get("Access-Control-Allow-Origin"), "https://site.example");
});
