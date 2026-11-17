// Tests for site/api/unsubscribe.js (the one-click unsubscribe function). No network: fetch is replaced.
// Run: node --test tests/js/unsubscribe.test.mjs   (the python suite runs it too)
import test from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
const handler = createRequire(import.meta.url)("../../site/api/unsubscribe.js");

const CODE = "abcDEF123_-abcDEF123_-abcDEF12345";
function call(method, url, host = "talmud-stories.vercel.app") {
  const res = { headers: {}, statusCode: 0, ended: false,
                setHeader(k, v) { this.headers[k] = v; }, end() { this.ended = true; } };
  return handler({ method, url, headers: { host } }, res).then(() => res);
}
function withFetch(fake, run) {
  const real = globalThis.fetch, calls = [];
  globalThis.fetch = async (url, init) => { calls.push({ url, init }); return fake(url, init); };
  return run(calls).finally(() => { globalThis.fetch = real; });
}

test("POST switches the emails off for that person, in the live project", () =>
  withFetch(async () => ({ ok: true }), async (calls) => {
    const res = await call("POST", `/api/unsubscribe?u=alice123&t=${CODE}`);
    assert.equal(res.statusCode, 200);
    assert.equal(calls.length, 1);
    assert.equal(calls[0].url, "https://firestore.googleapis.com/v1/projects/septimus-stories/databases/(default)/documents:commit");
    assert.equal(calls[0].init.headers.Authorization, undefined);          // signed out: the rules decide
    const write = JSON.parse(calls[0].init.body).writes[0];
    assert.equal(write.update.name, "projects/septimus-stories/databases/(default)/documents/users/alice123");
    assert.deepEqual(write.update.fields, { emailOff: { booleanValue: true }, mailTokenUsed: { stringValue: CODE } });
    assert.deepEqual(write.updateMask.fieldPaths, ["emailOff", "mailTokenUsed"]);
    assert.deepEqual(write.currentDocument, { exists: true });               // never creates a record
  }));

test("the staging site writes to the staging project", () =>
  withFetch(async () => ({ ok: true }), async (calls) => {
    await call("POST", `/api/unsubscribe?u=alice123&t=${CODE}`, "talmud-stories-staging.vercel.app");
    assert.match(calls[0].url, /projects\/septimus-stories-staging\//);
  }));

test("GET changes nothing and sends the person to the confirm page (mail scanners open links)", () =>
  withFetch(async () => ({ ok: true }), async (calls) => {
    const res = await call("GET", `/api/unsubscribe?u=alice123&t=${CODE}`);
    assert.equal(res.statusCode, 302);
    assert.equal(res.headers.Location, `/unsubscribe.html?u=alice123&t=${CODE}`);
    assert.equal(calls.length, 0);
  }));

test("a wrong code looks the same from outside as a right one", () =>
  withFetch(async () => ({ ok: false, status: 403 }), async () => {
    assert.equal((await call("POST", `/api/unsubscribe?u=alice123&t=${CODE}`)).statusCode, 200);
  }));

test("broken links are refused before anything is sent on", () =>
  withFetch(async () => ({ ok: true }), async (calls) => {
    for (const url of ["/api/unsubscribe", "/api/unsubscribe?u=alice123", `/api/unsubscribe?u=a/b&t=${CODE}`,
                       "/api/unsubscribe?u=alice123&t=short", `/api/unsubscribe?u=${"a".repeat(200)}&t=${CODE}`,
                       `/api/unsubscribe?u=alice123&t=${CODE}%22%7D`]) {
      assert.equal((await call("POST", url)).statusCode, 400, url);
      assert.equal((await call("GET", url)).statusCode, 400, url);
    }
    assert.equal(calls.length, 0);
  }));

test("other methods are refused; Firestore being unreachable is reported so the mail program can retry", async () => {
  await withFetch(async () => ({ ok: true }), async (calls) => {
    assert.equal((await call("DELETE", `/api/unsubscribe?u=alice123&t=${CODE}`)).statusCode, 405);
    assert.equal(calls.length, 0);
  });
  await withFetch(async () => { throw new Error("network down"); }, async () => {
    assert.equal((await call("POST", `/api/unsubscribe?u=alice123&t=${CODE}`)).statusCode, 502);
  });
});
