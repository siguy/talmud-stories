// Google Cloud Run wrapper around feedback-worker.js (the code is plain fetch/Request, so it could run elsewhere).
// Reads REPO, ALLOWED_ORIGIN, GITHUB_TOKEN from the environment; no dependencies.
import http from "node:http";
import worker from "./feedback-worker.js";

const env = { REPO: process.env.REPO, ALLOWED_ORIGIN: process.env.ALLOWED_ORIGIN, GITHUB_TOKEN: process.env.GITHUB_TOKEN };

http.createServer(async (req, res) => {
  const chunks = [];
  let size = 0;
  for await (const c of req) { size += c.length; if (size > 100000) { res.writeHead(413).end("too big"); return; } chunks.push(c); }
  const hasBody = !["GET", "HEAD", "OPTIONS"].includes(req.method);
  const request = new Request("https://feedback.invalid/", {
    method: req.method, headers: { "content-type": req.headers["content-type"] || "", ...(req.headers.origin ? { origin: req.headers.origin } : {}) },
    body: hasBody ? Buffer.concat(chunks) : undefined,
  });
  try {
    const r = await worker.fetch(request, env);
    const headers = {}; r.headers.forEach((v, k) => { headers[k] = v; });
    res.writeHead(r.status, headers).end(await r.text());
  } catch (e) { // never let one bad request become an unhandled rejection, which kills the process
    console.error("worker error", String(e).slice(0, 300));
    res.writeHead(500, { "Access-Control-Allow-Origin": (env.ALLOWED_ORIGIN || "*").split(",")[0] }).end("error");
  }
}).listen(process.env.PORT || 8080);
