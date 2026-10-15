// Google Cloud Functions (2nd gen, Node 20) version of the feedback worker.
// Same behaviour as ../feedback-worker.js (Cloudflare): files a GitHub issue labelled `story-feedback`.
// deploy.sh copies feedback-worker.js next to this file so `buildIssue` is shared, not duplicated.
import functions from "@google-cloud/functions-framework";
import { buildIssue } from "./feedback-worker.js";

export async function handle(req, res, env = process.env, doFetch = fetch) {
  res.set("Access-Control-Allow-Origin", env.ALLOWED_ORIGIN || "*");
  res.set("Access-Control-Allow-Methods", "POST, OPTIONS");
  res.set("Access-Control-Allow-Headers", "Content-Type");
  if (req.method === "OPTIONS") return res.status(204).send("");
  if (req.method !== "POST") return res.status(405).send("POST only");
  const payload = req.body;
  if (!payload || typeof payload !== "object") return res.status(400).send("bad json");
  if (payload.website) return res.status(200).send("ok"); // honeypot
  let issue;
  try { issue = buildIssue(payload); } catch (e) { return res.status(400).send(e.message); }
  const r = await doFetch(`https://api.github.com/repos/${env.REPO}/issues`, {
    method: "POST",
    headers: { Authorization: `Bearer ${env.GITHUB_TOKEN}`, Accept: "application/vnd.github+json", "User-Agent": "septimus-feedback", "Content-Type": "application/json" },
    body: JSON.stringify(issue),
  });
  return res.status(r.ok ? 200 : 502).send(r.ok ? "ok" : "upstream error");
}

functions.http("feedback", (req, res) => handle(req, res));
