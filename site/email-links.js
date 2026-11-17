// Shared by unsubscribe.html and learned.html: the two pages a link in the weekly email opens.
// Neither page needs a sign-in. Each link carries the person's id (u) and their private code (t), and
// firestore.rules accepts the change only when the code matches the one on their record.
// Loaded after config.js, which says which Firebase project this copy of the site uses.
window.EmailLinks = (function () {
  var UID = /^[A-Za-z0-9_-]{1,128}$/, CODE = /^[A-Za-z0-9_-]{20,128}$/, STORY = /^[a-z0-9_-]{1,120}$/, WEEK = /^[0-9]{1,3}$/;

  // The link's values, or null when the link is broken or was cut short.
  function params(needStory) {
    var q = new URLSearchParams(location.search), p = { u: q.get("u") || "", t: q.get("t") || "", w: q.get("w") || "", s: q.get("s") || "" };
    if (!UID.test(p.u) || !CODE.test(p.t)) return null;
    if (needStory && (!WEEK.test(p.w) || !STORY.test(p.s))) return null;
    return p;
  }

  // One write to Firestore as a signed-out visitor. Resolves true when it was accepted.
  function commit(write) {
    var fb = (window.SEPTIMUS_CONFIG || {}).firebase || {};
    var base = "projects/" + fb.projectId + "/databases/(default)/documents";
    write.update.name = base + "/" + write.update.name;
    write.currentDocument = { exists: true };
    return fetch("https://firestore.googleapis.com/v1/" + base + ":commit?key=" + encodeURIComponent(fb.apiKey || ""), {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ writes: [write] })
    }).then(function (r) { return r.ok; });
  }

  function setEmailOff(p, off) {
    return commit({ update: { name: "users/" + p.u, fields: { emailOff: { booleanValue: off }, mailTokenUsed: { stringValue: p.t } } },
                    updateMask: { fieldPaths: ["emailOff", "mailTokenUsed"] } });
  }

  // Tick one story as learned, with the server's clock. The row id is <week>_<uid>_<storyId>.
  function markLearned(p) {
    return commit({ update: { name: "assignments/" + p.w + "_" + p.u + "_" + p.s, fields: { mailTokenUsed: { stringValue: p.t } } },
                    updateMask: { fieldPaths: ["mailTokenUsed"] },
                    updateTransforms: [{ fieldPath: "doneAt", setToServerValue: "REQUEST_TIME" }] });
  }

  return { params: params, setEmailOff: setEmailOff, markLearned: markLearned };
})();
