(function () {
  "use strict";
  var HE = { ketubot: "כתובות", kiddushin: "קידושין", gittin: "גיטין", yevamot: "יבמות" };
  var NAME = { ketubot: "Ketubot", kiddushin: "Kiddushin", gittin: "Gittin", yevamot: "Yevamot" };
  var app = document.getElementById("app");
  var cache = {}, index = null;

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

  function home() {
    return getJSON("data/index.json").then(function (idx) {
      index = idx;
      return Promise.all(idx.tractates.map(function (t) { return getJSON("data/" + t.tractate + ".json"); })).then(function (all) {
        var cards = idx.tractates.map(function (t, i) {
          var ids = all[i].stories.filter(function (s) { return s.tier === "story"; }).map(function (s) { return s.id; });
          var done = ids.filter(function (id) { return read.has(id); }).length;
          return '<a class="card" href="#/t/' + t.tractate + '"><span class="card-he">' + HE[t.tractate] + '</span>' +
            '<div class="card-name">' + NAME[t.tractate] + '</div>' +
            '<div class="card-meta">' + t.story + ' stories' + (t.borderline ? ' · ' + t.borderline + ' borderline' : '') +
            (t.reviewed ? '' : ' · not yet reviewed') + '</div>' +
            '<div class="bar-track"><div class="bar-fill" style="width:' + (ids.length ? 100 * done / ids.length : 0) + '%"></div></div>' +
            '<div class="card-meta">' + done + ' of ' + ids.length + ' read</div></a>';
        }).join("");
        app.innerHTML = '<h1>Stories of the Talmud</h1>' +
          '<p class="dedication">In memory of Joe Septimus.</p>' +
          '<p class="lede">The narrative stories found in four tractates of the Babylonian Talmud, with the Hebrew and an English translation. Pick a tractate to start reading.</p>' + cards;
      });
    });
  }

  function tractate(t, tab) {
    return getJSON("data/" + t + ".json").then(function (d) {
      tab = tab === "borderline" ? "borderline" : "story";
      var counts = { story: 0, borderline: 0 };
      d.stories.forEach(function (s) { counts[s.tier]++; });
      var list = d.stories.filter(function (s) { return s.tier === tab; }).sort(function (a, b) { return dafKey(a.ref) - dafKey(b.ref) || a.start_segment - b.start_segment; });
      var html = '<div class="crumb"><a href="#/">All tractates</a></div><h1>' + NAME[t] + ' <span style="font-family:\'Frank Ruhl Libre\',serif">' + HE[t] + '</span></h1>';
      if (!d.reviewed) html += '<p class="notice">These stories were found by software and have not yet been checked by a scholar. Some may not be stories, or may be cut at the wrong place.</p>';
      html += '<div class="tabs"><button class="tab" aria-pressed="' + (tab === "story") + '" data-tab="story">Stories (' + counts.story + ')</button>' +
        (counts.borderline ? '<button class="tab" aria-pressed="' + (tab === "borderline") + '" data-tab="borderline">Borderline (' + counts.borderline + ')</button>' : '') + '</div>';
      if (tab === "borderline") html += '<p class="notice">Borderline: scholars could reasonably disagree about whether these count as stories.</p>';
      var last = "";
      list.forEach(function (s) {
        var daf = s.ref.split(" ").pop();
        if (daf !== last) { html += '<h2>' + esc(NAME[t]) + ' ' + esc(daf) + '</h2>'; last = daf; }
        html += '<a class="row' + (read.has(s.id) ? " read" : "") + '" href="#/s/' + s.id + '"><span class="check">' + (read.has(s.id) ? "✓" : "") + '</span><span>' +
          '<span class="row-ref">' + esc(refLabel(s)) + '</span>' + (s.in_mishnah ? '<span class="chip">Mishnah</span>' : '') +
          '<div class="row-sum">' + esc(s.summary) + '</div></span></a>';
      });
      app.innerHTML = html;
      app.querySelectorAll("[data-tab]").forEach(function (b) { b.addEventListener("click", function () { location.hash = "#/t/" + t + "?tab=" + b.dataset.tab; }); });
    });
  }

  function story(id) {
    var t = id.split("-")[0];
    var draftMode = /[?&]notes=draft/.test(location.search) || !!CFG.showDraftNotes;
    var notesP = getJSON("data/notes/" + t + ".json").catch(function () { return { notes: {} }; });
    return Promise.all([getJSON("data/" + t + ".json"), notesP]).then(function (both) {
      var d = both[0], note = both[1].notes[id];
      if (note && !note.approved && !draftMode) note = null; // unreviewed AI drafts never reach readers
      var s = d.stories.filter(function (x) { return x.id === id; })[0];
      if (!s) { app.innerHTML = '<p>Story not found. <a href="#/">Home</a></p>'; return; }
      var siblings = d.stories.filter(function (x) { return x.tier === s.tier; }).sort(function (a, b) { return dafKey(a.ref) - dafKey(b.ref) || a.start_segment - b.start_segment; });
      var i = siblings.indexOf(s), prev = siblings[i - 1], next = siblings[i + 1];
      var segs = s.segments.map(function (g, n) { return '<div class="seg"><div class="he" lang="he" dir="rtl">' + g.he + '</div><div class="en" lang="en">' + g.en + '</div><button class="flag" data-seg="' + n + '" aria-label="Report a problem with this passage" title="Report a problem with this passage">⚑ Report</button></div>'; }).join("");
      app.innerHTML = '<div class="crumb"><a href="#/t/' + t + (s.tier === "borderline" ? "?tab=borderline" : "") + '">← ' + NAME[t] + '</a></div>' +
        '<h1>' + esc(refLabel(s)) + '</h1>' +
        (s.in_mishnah ? '<span class="chip" style="margin:0">Mishnah</span> ' : '') + (s.tier === "borderline" ? '<span class="chip" style="margin:0">Borderline</span> ' : '') +
        (s.reviewed ? '' : '<span class="chip" style="margin:0">Not yet reviewed</span>') +
        '<p class="summary">' + esc(s.summary) + '</p>' + noteMarkup(note) + '<p class="notice">Bold English is a translation of the original Aramaic; plain text is explanation added by the translators.</p>' + segs +
        '<div class="actions"><button id="read-btn" class="btn primary" aria-pressed="' + read.has(id) + '"></button>' +
        '<a class="btn" href="' + sefariaUrl(s) + '" target="_blank" rel="noopener">Open on Sefaria</a></div>' +
        feedbackMarkup() + '<div class="pager actions">' + (prev ? '<a class="btn" href="#/s/' + prev.id + '">← Previous</a>' : '<span></span>') + (next ? '<a class="btn" href="#/s/' + next.id + '">Next →</a>' : '') + '</div>';
      var btn = document.getElementById("read-btn");
      function label() { btn.textContent = read.has(id) ? "✓ Marked as read" : "Mark as read"; btn.setAttribute("aria-pressed", read.has(id)); }
      label();
      btn.addEventListener("click", function () { toggleRead(id); label(); });
      wireFeedback(s);
    });
  }

  // ---- feedback: inline per story; fills in the story's details itself ------------------------
  var CATS = [["hebrew", "The Hebrew text looks wrong"], ["translation", "The English is wrong or unclear"], ["not_story", "This isn't really a story"],
              ["boundary", "The story starts or ends in the wrong place"], ["other", "Something else"]];
  var CFG = window.SEPTIMUS_CONFIG || {};
  function plain(h) { var d = document.createElement("div"); d.innerHTML = h; return (d.textContent || "").trim(); }
  function noteMarkup(n) {
    if (!n) return "";
    var h = '<details class="note"' + (n.approved ? '' : ' open') + '><summary>Background: what\'s going on here?' +
      (n.approved ? '' : ' <span class="chip">DRAFT — not yet reviewed</span>') + '</summary><p>' + esc(n.note) + '</p>';
    if (n.people.length) h += '<h3>Who\'s who</h3><ul>' + n.people.map(function (p) { return '<li><b>' + esc(p.name) + '</b>' + (p.about ? ' — ' + esc(p.about) : '') + '</li>'; }).join("") + '</ul>';
    if (n.terms.length) h += '<h3>Words to know</h3><ul>' + n.terms.map(function (t) { return '<li><b>' + esc(t.term) + '</b> — ' + esc(t.meaning) + '</li>'; }).join("") + '</ul>';
    return h + '<p class="fine">Written with the help of AI' + (n.approved ? ' and reviewed by a person' : '') + '. Spot a mistake? Use “Report a problem” below.</p></details>';
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
  function wireFeedback(s) {
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
        story_id: s.id, tractate: s.tractate, ref: s.ref, refs: s.refs, tier: s.tier, classification: s.classification,
        reviewed: s.reviewed, in_mishnah: s.in_mishnah, summary: s.summary, category: cat, comment: comment,
        segment: g ? { ref: g.ref, index: g.i, he: plain(g.he), en: plain(g.en) } : null,
        name: document.getElementById("fb-name").value.trim(), website: document.getElementById("fb-website").value,
        page_url: location.href.slice(0, 300)
      };
      var send = document.getElementById("fb-send"); send.disabled = true; msg.className = "msg"; msg.textContent = "Sending…";
      function done(ok, text) { send.disabled = false; msg.className = "msg"; msg.innerHTML = text; if (ok) document.getElementById("fb-comment").value = ""; }
      function fallback() {
        var title = "[Feedback] " + (g ? g.ref + " segment " + g.i : s.ref) + ": " + cat;
        var body = (comment ? "> " + comment + "\n\n" : "") + "```json\n" + JSON.stringify(payload, null, 1) + "\n```";
        var url = "https://github.com/" + (CFG.repo || "") + "/issues/new?labels=" + encodeURIComponent("story-feedback") + "&title=" + encodeURIComponent(title) + "&body=" + encodeURIComponent(body.slice(0, 6000));
        window.open(url, "_blank", "noopener");
        done(true, "Opened GitHub with your note filled in — press “Submit new issue” there to send it.");
      }
      if (!CFG.feedbackEndpoint) { fallback(); return; }
      fetch(CFG.feedbackEndpoint, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) })
        .then(function (r) { if (!r.ok) throw new Error(r.status); done(true, "Thank you — your note was sent."); })
        .catch(function () { done(false, 'Sorry, that did not send. <button type="button" class="linkbtn" id="fb-alt">Send via GitHub instead</button>'); document.getElementById("fb-alt").addEventListener("click", fallback); });
    });
  }

  function route() {
    var h = location.hash.slice(1) || "/", q = h.split("?"), parts = q[0].split("/"), p;
    window.scrollTo(0, 0);
    if (parts[1] === "t" && NAME[parts[2]]) p = tractate(parts[2], (/tab=(\w+)/.exec(q[1] || "") || [])[1]);
    else if (parts[1] === "s") p = story(parts[2]);
    else p = home();
    p.catch(function () { app.innerHTML = '<p class="notice">Could not load the stories. Please check your connection and reload.</p>'; });
  }
  window.addEventListener("hashchange", route);
  applyPrefs();
  route();
})();
