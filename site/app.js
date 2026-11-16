(function () {
  "use strict";
  // Tractate names come from data/index.json (written by scripts/build_site_data.py from the one table in
  // scripts/tractates.py), so a new tractate needs no edit here. Filled in by loadIndex().
  var HE = {}, NAME = {};
  var app = document.getElementById("app");
  var cache = {}, index = null;
  // Story ids are PERMANENT (site/data/story_ids.json, scripts/story_ids.py): a boundary change keeps the id. An id
  // that is no longer active is in redirects.json: -> the id its story now has (a merge), or null (retired).
  var REDIRECTS = {};

  // localStorage can throw (private windows, blocked storage): the site must work without it.
  function load(k, d) { try { var v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch (e) { return d; } }
  function save(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }
  var read = new Set(load("septimus-read", []));
  var prefs = load("septimus-prefs", { lang: "both", size: 0 });
  var memoryOnlyNote = false;

  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function getJSON(p) { return cache[p] || (cache[p] = fetch(p).then(function (r) { if (!r.ok) throw new Error(p); return r.json(); })); }

  function applyPrefs() {
    document.body.dataset.lang = prefs.lang;
    var r = document.documentElement.style;
    r.setProperty("--he-size", (1.45 + prefs.size * 0.15) + "rem");
    r.setProperty("--en-size", (1.05 + prefs.size * 0.1) + "rem");
    document.querySelectorAll("[data-lang]").forEach(function (b) { b.setAttribute("aria-pressed", b.dataset.lang === prefs.lang); });
    save("septimus-prefs", prefs);
  }
  document.querySelectorAll("[data-lang]").forEach(function (b) { b.addEventListener("click", function () { prefs.lang = b.dataset.lang; applyPrefs(); }); });
  document.getElementById("size-up").addEventListener("click", function () { prefs.size = Math.min(5, prefs.size + 1); applyPrefs(); });
  document.getElementById("size-down").addEventListener("click", function () { prefs.size = Math.max(-3, prefs.size - 1); applyPrefs(); });
  document.getElementById("settings-btn").addEventListener("click", function () { var s = document.getElementById("settings"); s.hidden = !s.hidden; });

  function dafKey(ref) { var m = /(\d+)([ab])/.exec(ref); return m ? m[1] * 2 + (m[2] === "b" ? 1 : 0) : 0; }
  function refLabel(s) { return s.refs.length > 1 ? s.refs[0] + " – " + s.refs[1].split(" ").pop() : s.ref; }
  function sefariaUrl(s) { return "https://www.sefaria.org/" + encodeURIComponent(s.ref.replace(" ", ".")) + "?lang=bi"; }
  function toggleRead(id) { if (read.has(id)) read.delete(id); else read.add(id); save("septimus-read", Array.from(read)); }

  function loadIndex() {
    // redirects.json missing or unreadable: old ids then simply show "not found"; the site still works.
    var redirectsP = getJSON("data/redirects.json").catch(function () { return {}; });
    return Promise.all([getJSON("data/index.json"), redirectsP]).then(function (both) {
      var idx = both[0];
      index = idx;
      idx.tractates.forEach(function (t) { NAME[t.tractate] = t.name; HE[t.tractate] = t.he; });
      if (REDIRECTS !== both[1]) { REDIRECTS = both[1]; migrateRead(); }
      return idx;
    });
  }

  // A checkmark saved under an id that was merged into another story moves to that story's id. A retired id's
  // checkmark is kept (it may be revived) but counts for nothing: home() counts only ids not in REDIRECTS.
  function migrateRead() {
    var changed = false;
    Array.from(read).forEach(function (id) {
      var to = REDIRECTS[id];
      if (to) { read.delete(id); read.add(to); changed = true; }
    });
    if (changed) save("septimus-read", Array.from(read));
  }

  // The home page reads ONLY the counts in index.json (36 tractate files are ~8 MB; a phone should not
  // fetch them to draw a list). "Read" progress is the saved story ids that begin with the tractate's
  // slug and a hyphen (every id starts <slug>-, slugs have no hyphen), not retired, capped at the count.
  function home() {
    return loadIndex().then(function (idx) {
      var cards = idx.tractates.map(function (t) {
        var done = Math.min(t.story, Array.from(read).filter(function (id) { return id.indexOf(t.tractate + "-") === 0 && !(id in REDIRECTS); }).length);
        return '<a class="card" href="#/t/' + t.tractate + '"><span class="card-he">' + esc(t.he) + '</span>' +
          '<div class="card-name">' + esc(t.name) + '</div>' +
          '<div class="card-meta">' + t.story +  ' stories' +
          (t.reviewed ? '' : ' · not yet reviewed') + '</div>' +
          '<div class="bar-track"><div class="bar-fill" style="width:' + (t.story ? 100 * done / t.story : 0) + '%"></div></div>' +
          '<div class="card-meta">' + done + ' of ' + t.story + ' read</div></a>';
      }).join("");
      app.innerHTML = '<h1>Stories of the Talmud</h1>' +
        '<p class="dedication">In memory of Joe Septimus.</p>' +
        '<p class="lede">The narrative stories found in ' + idx.tractates.length + ' tractates of the Babylonian Talmud, with the Hebrew and an English translation. Pick a tractate to start reading.</p>' + cards;
    });
  }

  // Every story on the site is a definite story (scripts/build_site_data.py ships nothing else), so there is one list.
  function tractate(t) {
    return getJSON("data/" + t + ".json").then(function (d) {
      var list = d.stories.slice().sort(function (a, b) { return dafKey(a.ref) - dafKey(b.ref) || a.start_segment - b.start_segment; });
      var html = '<div class="crumb"><a href="#/">All tractates</a></div><h1>' + NAME[t] + ' <span style="font-family:\'Frank Ruhl Libre\',serif">' + HE[t] + '</span></h1>';
      if (!d.reviewed) html += '<p class="notice">These stories were found by software and have not yet been checked by a scholar. Some may not be stories, or may be cut at the wrong place.</p>';
      html += '<div class="tabs"><button class="tab" aria-pressed="true">Stories (' + list.length + ')</button></div>';
      var last = "";
      list.forEach(function (s) {
        var daf = s.ref.split(" ").pop();
        if (daf !== last) { html += '<h2>' + esc(NAME[t]) + ' ' + esc(daf) + '</h2>'; last = daf; }
        html += '<a class="row' + (read.has(s.id) ? " read" : "") + '" href="#/s/' + s.id + '"><span class="check">' + (read.has(s.id) ? "✓" : "") + '</span><span>' +
          '<span class="row-ref">' + esc(refLabel(s)) + '</span>' + (s.in_mishnah ? '<span class="chip">Mishnah</span>' : '') +
          '<div class="row-sum">' + esc(s.summary) + '</div></span></a>';
      });
      app.innerHTML = html;
    });
  }

  function story(id) {
    var t = id.split("-")[0];
    if (Object.prototype.hasOwnProperty.call(REDIRECTS, id)) {
      var to = REDIRECTS[id];
      // replace, not assign: Back must not bounce the reader through the old id again
      if (to) { location.replace("#/s/" + to); return Promise.resolve(); }
      app.innerHTML = '<div class="crumb"><a href="#/t/' + esc(t) + '">← ' + esc(NAME[t] || "All tractates") + '</a></div>' +
        '<p class="notice">This passage is no longer on the list of stories.</p>' +
        '<p><a href="#/t/' + esc(t) + '">See the stories of ' + esc(NAME[t] || t) + '</a></p>';
      return Promise.resolve();
    }
    var draftMode = /[?&]notes=draft/.test(location.search) || !!CFG.showDraftNotes;
    var notesP = getJSON("data/notes/" + t + ".json").catch(function () { return { notes: {} }; });
    return Promise.all([getJSON("data/" + t + ".json"), notesP]).then(function (both) {
      var d = both[0], note = both[1].notes[id];
      if (note && !note.approved && !draftMode) note = null; // unreviewed AI drafts never reach readers
      var s = d.stories.filter(function (x) { return x.id === id; })[0];
      if (!s) { app.innerHTML = '<p>Story not found. <a href="#/">Home</a></p>'; return; }
      var siblings = d.stories.slice().sort(function (a, b) { return dafKey(a.ref) - dafKey(b.ref) || a.start_segment - b.start_segment; });
      var i = siblings.indexOf(s), prev = siblings[i - 1], next = siblings[i + 1];
      var segs = s.segments.map(function (g, n) { return '<div class="seg"><div class="he" lang="he" dir="rtl">' + g.he + '</div><div class="en" lang="en">' + g.en + '</div><button class="flag" data-seg="' + n + '" aria-label="Report a problem with this passage" title="Report a problem with this passage">⚑ Report</button></div>'; }).join("");
      app.innerHTML = '<div class="crumb"><a href="#/t/' + t + '">← ' + NAME[t] + '</a></div>' +
        '<h1>' + esc(refLabel(s)) + '</h1>' +
        (s.in_mishnah ? '<span class="chip" style="margin:0">Mishnah</span> ' : '') +
        (s.reviewed ? '' : '<span class="chip" style="margin:0">Not yet reviewed</span> ') +
        (s.extended && (s.extended.start_back || s.extended.end_forward) ? '<span class="chip" style="margin:0" title="The passage was widened by a few lines so it ends at a natural point">Extended to finish the passage</span>' : '') +
        (s.summary ? '<p class="summary">' + esc(s.summary) + '</p>' : '') + noteMarkup(note) + '<p class="notice">Bold English is a translation of the original Aramaic; plain text is explanation added by the translators.</p>' + segs +
        '<div class="actions"><button id="read-btn" class="btn primary" aria-pressed="' + read.has(id) + '"></button>' +
        '<a class="btn" href="' + sefariaUrl(s) + '" target="_blank" rel="noopener">Open on Sefaria</a></div>' +
        feedbackMarkup() + '<div class="pager actions">' + (prev ? '<a class="btn" href="#/s/' + prev.id + '">← Previous</a>' : '<span></span>') + (next ? '<a class="btn" href="#/s/' + next.id + '">Next →</a>' : '') + '</div>';
      var btn = document.getElementById("read-btn");
      function label() { btn.textContent = read.has(id) ? "✓ Marked as read" : "Mark as read"; btn.setAttribute("aria-pressed", read.has(id)); }
      label();
      btn.addEventListener("click", function () { toggleRead(id); label(); });
      wireFeedback(s, note);
    });
  }

  // ---- feedback: inline per story; fills in the story's details itself ------------------------
  var CATS = [["hebrew", "The Hebrew text looks wrong"], ["translation", "The English is wrong or unclear"], ["not_story", "This isn't really a story"],
              ["boundary", "The story starts or ends in the wrong place"], ["note", "The background note is wrong"], ["other", "Something else"]];
  var CFG = window.SEPTIMUS_CONFIG || {};
  function plain(h) { var d = document.createElement("div"); d.innerHTML = h; return (d.textContent || "").trim(); }
  function noteMarkup(n) {
    if (!n) return "";
    var h = '<details class="note"' + (n.approved ? '' : ' open') + '><summary>Background: what\'s going on here?' +
      (n.approved ? '' : ' <span class="chip">DRAFT — not yet reviewed</span>') + '</summary><p>' + esc(n.note) + '</p>';
    if (n.people.length) h += '<h3>Who\'s who</h3><ul>' + n.people.map(function (p) { return '<li><b>' + esc(p.name) + '</b>' + (p.about ? ' — ' + esc(p.about) : '') + '</li>'; }).join("") + '</ul>';
    if (n.terms.length) h += '<h3>Words to know</h3><ul>' + n.terms.map(function (t) { return '<li><b>' + esc(t.term) + '</b> — ' + esc(t.meaning) + '</li>'; }).join("") + '</ul>';
    if (n.why) h += '<h3>Why is this story here?</h3><p>' + esc(n.why) + '</p>';   // last in the box (Simon 2026-11-15)
    return h + '<p class="fine">Written by AI. Spot a mistake? Use “Report a problem” below.</p></details>';
  }
  function feedbackMarkup() {
    return '<details class="fb" id="fb"><summary>Report a problem or suggest a fix</summary><form id="fb-form" novalidate>' +
      '<div class="about" id="fb-about"></div>' +
      '<div><label for="fb-cat">What\'s the problem?</label><select id="fb-cat">' +
      CATS.map(function (c) { return '<option value="' + c[0] + '">' + esc(c[1]) + '</option>'; }).join("") + '</select></div>' +
      '<div><label for="fb-comment">Tell us more (optional, except for "Something else")</label><textarea id="fb-comment" maxlength="4000"></textarea></div>' +
      '<div><label for="fb-name">Your name (optional)</label><input type="text" id="fb-name" maxlength="120" autocomplete="name"></div>' +
      '<div class="hp" aria-hidden="true"><label>Leave empty <input type="text" id="fb-website" tabindex="-1" autocomplete="off"></label></div>' +
      '<button class="btn" id="fb-send" type="submit">Send</button><div id="fb-msg" role="status"></div></form></details>';
  }
  function wireFeedback(s, note) {
    var seg = null; // null = about the whole story
    function about() {
      var el = document.getElementById("fb-about");
      if (seg == null) { el.textContent = "About this whole story (" + refLabel(s) + ")."; return; }
      var g = s.segments[seg];
      el.innerHTML = 'About this passage — <button type="button" class="linkbtn" id="fb-whole">report on the whole story instead</button><q>' + esc(plain(g.en).slice(0, 160)) + '…</q>';
      document.getElementById("fb-whole").addEventListener("click", function () { seg = null; about(); });
    }
    about();
    app.querySelectorAll(".flag").forEach(function (b) {
      b.addEventListener("click", function () {
        seg = +b.dataset.seg; about();
        var d = document.getElementById("fb"); d.open = true; d.scrollIntoView({ behavior: "smooth", block: "center" });
      });
    });
    document.getElementById("fb-form").addEventListener("submit", function (e) {
      e.preventDefault();
      var g = seg == null ? null : s.segments[seg], msg = document.getElementById("fb-msg");
      var cat = document.getElementById("fb-cat").value, comment = document.getElementById("fb-comment").value.trim();
      if (cat === "other" && !comment) { msg.className = "msg"; msg.textContent = "Please add a few words so we know what you mean."; return; }
      var payload = {
        story_id: s.id, tractate: s.tractate, ref: s.ref, refs: s.refs,
        reviewed: s.reviewed, in_mishnah: s.in_mishnah, summary: s.summary, category: cat, comment: comment,
        segment: g ? { ref: g.ref, index: g.i, he: plain(g.he), en: plain(g.en) } : null,
        // What the reader was looking at, so triage can tell "already fixed" from "still wrong".
        span: s.span || [], extended: !!(s.extended && (s.extended.start_back || s.extended.end_forward)),
        note_drafted: note && note.drafted ? String(note.drafted) : "", note_approved: !!(note && note.approved),
        site: /staging/.test(location.hostname) ? "staging" : "prod", test: /^\s*TEST\b/i.test(comment),
        name: document.getElementById("fb-name").value.trim(), website: document.getElementById("fb-website").value,
        page_url: location.href.slice(0, 300)
      };
      var send = document.getElementById("fb-send"); send.disabled = true; msg.className = "msg"; msg.textContent = "Sending…";
      function done(ok, text) { send.disabled = false; msg.className = "msg"; msg.innerHTML = text; if (ok) document.getElementById("fb-comment").value = ""; }
      // The endpoint did not answer. The feedback repo is private, so a GitHub link would be a 404 for readers:
      // offer the report as text to copy, and an email link (D11, Simon 2026-11-15).
      function fallback() {
        var label = CATS.filter(function (c) { return c[0] === cat; })[0][1];
        var text = "Problem: " + label + "\nStory: " + s.id + (g ? "\nPassage: " + g.ref + " segment " + g.i : "") +
          (comment ? "\nDetails: " + comment : "") + (payload.name ? "\nFrom: " + payload.name : "");
        var mail = "mailto:" + (CFG.feedbackEmail || "") + "?subject=" + encodeURIComponent("Story problem: " + s.id) + "&body=" + encodeURIComponent(text);
        done(false, 'Sorry, that did not send. Please email it instead: <a href="' + mail + '">send by email</a>, or copy this and send it to us:' +
          '<textarea readonly rows="5" id="fb-copy">' + esc(text) + '</textarea>');
        var box = document.getElementById("fb-copy"); if (box) box.addEventListener("focus", function () { box.select(); });
      }
      if (!CFG.feedbackEndpoint) { fallback(); return; }
      fetch(CFG.feedbackEndpoint, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) })
        .then(function (r) { if (!r.ok) throw new Error(r.status); done(true, "Thank you — your note was sent."); })
        .catch(fallback);
    });
  }

  function route() {
    var h = location.hash.slice(1) || "/", q = h.split("?"), parts = q[0].split("/"), p;
    window.scrollTo(0, 0);
    p = loadIndex().then(function () {
      if (parts[1] === "t" && NAME[parts[2]]) return tractate(parts[2]);
      if (parts[1] === "s") return story(parts[2]);
      return home();
    });
    p.catch(function () { app.innerHTML = '<p class="notice">Could not load the stories. Please check your connection and reload.</p>'; });
  }
  window.addEventListener("hashchange", route);
  applyPrefs();
  route();
})();
