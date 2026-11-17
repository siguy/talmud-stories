// One-click unsubscribe for the weekly email (docs/technical/septimus-signup-plan.md, section 8d).
//
// Every email carries the header  List-Unsubscribe: <https://SITE/api/unsubscribe?u=UID&t=CODE>.
//   POST  what a mail program sends when the reader presses its own "Unsubscribe" button: switch the emails off.
//   GET   what a person (or a mail scanner following links) sends: change nothing, show the confirm page.
//
// This function holds NO password or key. It passes the request to Firestore as a signed-out visitor, and
// firestore.rules accepts it only when CODE equals the private code stored on that person's record
// (users/UID.mailToken, written by scripts/septimus_weekly.py). A wrong code changes nothing.
//
// Runs on Vercel as a Node function (any file in site/api/ becomes one). Tests: tests/js/unsubscribe.test.mjs

// The same two Firebase projects, and the same staging-host rule, as site/config.js
// (tests/test_septimus_email.py checks they stay in step).
const PROJECTS = { live: "septimus-stories", staging: "septimus-stories-staging" };
const STAGING_HOST = /^talmud-stories-staging[a-z0-9-]*\.vercel\.app$/;
const UID = /^[A-Za-z0-9_-]{1,128}$/;
const CODE = /^[A-Za-z0-9_-]{20,128}$/;

function projectFor(host) {
  return STAGING_HOST.test(String(host || "").split(":")[0]) ? PROJECTS.staging : PROJECTS.live;
}

// The Firestore write: set emailOff (and say which code was used) on a record that must already exist.
function commitRequest(project, uid, code, emailOff) {
  const base = "projects/" + project + "/databases/(default)/documents";
  return {
    url: "https://firestore.googleapis.com/v1/" + base + ":commit",
    body: { writes: [{
      update: { name: base + "/users/" + uid,
                fields: { emailOff: { booleanValue: emailOff }, mailTokenUsed: { stringValue: code } } },
      updateMask: { fieldPaths: ["emailOff", "mailTokenUsed"] },
      currentDocument: { exists: true }
    }] }
  };
}

function end(res, status, headers) {
  res.statusCode = status;
  Object.keys(headers || {}).forEach(function (k) { res.setHeader(k, headers[k]); });
  res.setHeader("Cache-Control", "no-store");
  res.end();
}

async function handler(req, res) {
  const url = new URL(req.url, "https://site.invalid");
  const uid = url.searchParams.get("u") || "", code = url.searchParams.get("t") || "";
  if (!UID.test(uid) || !CODE.test(code)) return end(res, 400);
  if (req.method === "GET" || req.method === "HEAD") {
    return end(res, 302, { Location: "/unsubscribe.html?u=" + uid + "&t=" + code });
  }
  if (req.method !== "POST") return end(res, 405, { Allow: "GET, POST" });
  const host = req.headers["x-forwarded-host"] || req.headers.host;
  const write = commitRequest(projectFor(host), uid, code, true);
  try {
    // Firestore's answer is not passed on: a right code and a wrong one look the same from outside.
    await fetch(write.url, { method: "POST", headers: { "Content-Type": "application/json" },
                             body: JSON.stringify(write.body) });
  } catch (err) {
    return end(res, 502);          // Firestore could not be reached: the mail program may try again
  }
  return end(res, 200);
}

module.exports = handler;
module.exports.projectFor = projectFor;
module.exports.commitRequest = commitRequest;
