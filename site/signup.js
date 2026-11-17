// Sign-up pages: landing, minutes question, My stories, Progress, and three small text pages; the three-link nav under the title; and the story-page button.
// app.js calls SeptimusSignup.route() first on every route; we return true when the hash is one of ours,
// false otherwise (then app.js draws the tractate list / reader as before).
// Everything from the person or from Google goes on the page as text nodes (el() below), never as HTML.
// This script loads BEFORE config.js, so config is read at route time through cfg(), never at load time.
(function () {
  "use strict";
  var app = document.getElementById("app");
  var srcDone = false;
  var token = 0;        // bumped on every route; a late answer from an old screen checks it and does nothing
  var indexP = null;    // data/index.json, fetched once
  var sdkP = null;      // the Firebase SDK, loaded once, only on sign-up screens
  var S = { sdk: null, user: null, record: null, recordFailed: false, settled: false, listener: null };

  function cfg() { return (window.SEPTIMUS_CONFIG || {}).signup || {}; }
  function load(k, d) { try { var v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch (e) { return d; } }
  function save(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }

  // "Has joined" is remembered per device so reader pages can show the right first link, and the front page can skip the
  // join pitch, without loading Firebase. The sign-in listener below keeps it true.
  var JOINED = "septimus-joined", here = "", navLinks = [];
  function setJoined(on) {
    if (on) save(JOINED, true); else { try { localStorage.removeItem(JOINED); } catch (e) {} }
    navUpdate();
  }

  // ---- DOM helper: el("p", {class: "x", text: "hi"}, [child, "text"]) -----------------------
  function el(tag, props, kids) {
    var n = document.createElement(tag);
    Object.keys(props || {}).forEach(function (k) {
      var v = props[k];
      if (v == null || v === false) return;
      if (k === "class") n.className = v;
      else if (k === "text") n.textContent = v;
      else if (typeof v === "function") n[k] = v;          // onclick, oninput ...
      else n.setAttribute(k, v === true ? "" : v);
    });
    (kids || []).forEach(function (c) { if (c != null) n.appendChild(typeof c === "string" ? document.createTextNode(c) : c); });
    return n;
  }
  function svgEl(tag, attrs, kids) {
    var n = document.createElementNS("http://www.w3.org/2000/svg", tag);
    Object.keys(attrs || {}).forEach(function (k) { n.setAttribute(k, attrs[k]); });
    (kids || []).forEach(function (c) { n.appendChild(c); });
    return n;
  }
  function show(nodes) { app.textContent = ""; nodes.forEach(function (n) { if (n) app.appendChild(n); }); }
  function link(text, href, cls) { return el("a", { href: href, text: text, class: cls }); }
  function back() { return el("p", {}, [link("← Back", "#/", "su-back")]); }
  // Automatic redirects replace the current history entry, so Back does not land on a page that bounces straight on again.
  function redirect(hash) { location.replace(location.pathname + location.search + hash); }

  // ---- ?src=: the community link. Kept in storage so it survives leaving an in-app browser --
  var SRC_KEY = "septimus-src";
  function allowedSrc(v) { return typeof v === "string" && v && (cfg().communities || []).indexOf(v) !== -1; }
  // Called on the first route, once config.js has loaded, so the allowlist is known before anything is stored.
  function urlSrc() {
    var m = /[?&]src=([^&#]*)/.exec(location.search), v;
    if (!m) return "";
    try { v = decodeURIComponent(m[1]).toLowerCase(); } catch (e) { return ""; }
    return allowedSrc(v) ? v : "";
  }
  function rememberSrc() { var v = urlSrc(); if (v) save(SRC_KEY, v); }
  // Storage can be blocked (private mode, in-app browsers), so fall back to the link we were opened with.
  function savedSrc() { var v = load(SRC_KEY, ""); return allowedSrc(v) ? v : urlSrc(); }

  // ---- dates and numbers ----------------------------------------------------------------------
  var MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
  function parseISO(s) { var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(s || ""); return m ? new Date(+m[1], +m[2] - 1, +m[3]) : null; }
  function fmtDate(d) { return d.getDate() + " " + MONTHS[d.getMonth()]; }
  function today() { var d = new Date(); d.setHours(0, 0, 0, 0); return d; }
  function launchText() { var d = parseISO(cfg().launchDate); return d ? fmtDate(d) : ""; }   // "" when no launch date is set; callers branch on it
  function label() { return cfg().yahrzeitLabel || "8 Elul"; }
  function hasLaunched() { var d = parseISO(cfg().launchDate); return !!d && today() >= d; }
  function afterYahrzeit() { var d = parseISO(cfg().yahrzeit); return !!d && today() > d; }
  function nextSunday() { var d = today(); d.setDate(d.getDate() + ((7 - d.getDay()) % 7 || 7)); return d; }
  // The last Sunday hand-out is over: the next Sunday falls after the yahrzeit.
  function ended() { var y = parseISO(cfg().yahrzeit); return hasLaunched() && !!y && nextSunday() > y; }
  function startLine() {
    if (ended()) return "The weekly stories have ended.";
    return hasLaunched() ? "Your first stories arrive Sunday " + fmtDate(nextSunday()) + "."
      : launchText() ? "Everyone starts together on " + launchText() + ". Your first stories arrive by email that week."
      : "We will email you when the learning begins.";
  }
  // Campaign weeks, counted the way campaign_week() in scripts/septimus_assign.py counts them:
  // week 1 is the seven days starting on the launch date. Whole days via rounding, so a clock change does not shift a week.
  function dayDiff(a, b) { return Math.round((b - a) / 864e5); }
  function campaignWeek() {
    var l = parseISO(cfg().launchDate);
    return l && today() >= l ? Math.floor(dayDiff(l, today()) / 7) + 1 : null;   // null: not set, or not started
  }
  function lastWeek() {   // the campaign week that contains the yahrzeit
    var l = parseISO(cfg().launchDate), y = parseISO(cfg().yahrzeit);
    return l && y && y >= l ? Math.floor(dayDiff(l, y) / 7) + 1 : null;
  }
  function weeksToYahrzeit() {   // whole weeks from today, rounded up; null once it is today or past
    var y = parseISO(cfg().yahrzeit), n = y ? Math.ceil(dayDiff(today(), y) / 7) : 0;
    return n >= 1 ? n : null;
  }
  // A number from progress/summary is used only if it is a real number; anything else counts as absent.
  function num(x) { return typeof x === "number" && isFinite(x) ? x : 0; }
  function isNum(x) { return typeof x === "number" && isFinite(x); }
  // Firestore write promises do not settle while offline (the write waits in its queue), so after 8 seconds say so.
  // say(text) puts the text in that control's status line; the later success or failure message replaces it.
  var SLOW_MSG = "Not saved yet. You seem to be offline; it will save when you reconnect.";
  function watchSlow(p, t, say) {
    var timer = setTimeout(function () { if (t === token) say(SLOW_MSG); }, 8000);
    function stop() { clearTimeout(timer); }
    p.then(stop, stop);
    return p;
  }
  function commas(n) { return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ","); }

  // Same order as TABLE in scripts/tractates.py. TODO(step s): read the order from index.json instead.
  var SHAS_ORDER = [
    "berakhot", "shabbat", "eruvin", "pesachim", "rosh_hashanah", "yoma",
    "sukkah", "beitzah", "taanit", "megillah", "moed_katan", "chagigah",
    "yevamot", "ketubot", "nedarim", "nazir", "sotah", "gittin",
    "kiddushin", "bava_kamma", "bava_metzia", "bava_batra", "sanhedrin", "makkot",
    "shevuot", "avodah_zarah", "horayot", "zevachim", "menachot", "chullin",
    "bekhorot", "arakhin", "temurah", "keritot", "meilah", "tamid",
    "niddah"
  ];
  // Position in Shas; a tractate not in the list goes last (ties keep index.json order, see sortTractates).
  function shasRank(slug) { var i = SHAS_ORDER.indexOf(slug); return i < 0 ? 1e9 : i; }
  function sortTractates(list) {
    return list.map(function (x, i) { return { x: x, i: i }; }).sort(function (a, b) { return (shasRank(a.x.tractate) - shasRank(b.x.tractate)) || (a.i - b.i); })
      .map(function (o) { return o.x; });
  }

  function getIndex() {
    return indexP || (indexP = fetch("data/index.json").then(function (r) { if (!r.ok) throw new Error("index"); return r.json(); })
      .catch(function (e) { indexP = null; throw e; }));
  }
  function stats(idx) {
    var stories = 0, words = 0;
    idx.tractates.forEach(function (t) { stories += t.story; words += t.words; });
    return { stories: stories, words: words, tractates: idx.tractates.length, mean: words / Math.max(1, stories) };
  }
  // The same label the reader uses for a story: two refs read "Berakhot 3a – 3b".
  function refLabel(s) { return s.refs && s.refs.length > 1 ? s.refs[0] + " – " + s.refs[1].split(" ").pop() : s.ref; }
  function listLine(idx, st) {
    return idx.list_version && idx.published_at ? "Story list v" + idx.list_version + ", dated " + idx.published_at + "."
      : "Story list: " + commas(st.stories) + " stories in " + st.tractates + " tractates.";
  }
  // One tractate file, fetched once. A tractate that is not in index.json has no file (a made-up id): null, not an error.
  var tractP = {};
  function getTractate(slug, idx) {
    if (!idx.tractates.some(function (x) { return x.tractate === slug; })) return Promise.resolve(null);
    return tractP[slug] || (tractP[slug] = fetch("data/" + slug + ".json").then(function (r) { if (!r.ok) throw new Error(slug); return r.json(); })
      .catch(function (e) { delete tractP[slug]; throw e; }));
  }
  // Story ids are permanent; data/redirects.json maps an id that was merged into another story to that story's id (null: removed).
  // For each id missing from `found`, add the story it was merged into. A failed load = no redirects.
  var redirectsP = null;
  function followMerged(ids, found, idx) {
    redirectsP = redirectsP || fetch("data/redirects.json").then(function (r) { if (!r.ok) throw new Error("redirects"); return r.json(); }).catch(function () { return {}; });
    return redirectsP.then(function (m) {
      return Promise.all(ids.filter(function (id) { return !found[id]; }).map(function (id) {
        var to = Object.prototype.hasOwnProperty.call(m, id) ? m[id] : null;
        if (typeof to !== "string") return null;
        return getTractate(to.split("-")[0], idx).then(function (d) {
          if (d) d.stories.forEach(function (s, i) { if (s.id === to) found[id] = { story: s, pos: i }; });
        }).catch(function () {});
      }));
    });
  }
  function storiesFor(minutes, st) { return Math.max(1, Math.round(minutes * (cfg().wpm || 75) / st.mean)); }

  // Draw a screen once index.json is in; otherwise show the same message app.js shows.
  function withIndex(t, draw) {
    getIndex().then(function (idx) { if (t === token) draw(idx, stats(idx)); })
      .catch(function () { if (t === token) show([el("p", { class: "notice", text: "Could not load the stories. Please check your connection and reload." })]); });
  }

  function sdkFailed(t) {
    if (t === token) show([el("p", { "class": "notice", text: "Could not load sign-in. Please check your connection and reload." })]);
  }

  // ---- Firebase --------------------------------------------------------------------------------
  function emulatorOn() {
    return /^(localhost|127\.0\.0\.1)$/.test(location.hostname) && /[?&]emulator=1(&|$)/.test(location.search);
  }
  // Pinned here, not in config.js: the calls below are written for this version, and a browser holding an
  // older cached config.js must still load the right files.
  var SDK_VERSION = "13.3.0";
  function loadSdk() {
    if (sdkP) return sdkP;
    var c = window.SEPTIMUS_CONFIG || {}, base = "https://www.gstatic.com/firebasejs/" + SDK_VERSION + "/firebase-";
    sdkP = Promise.all([import(base + "app.js"), import(base + "auth.js"), import(base + "firestore.js")]).then(function (m) {
      var emu = emulatorOn(), conf = Object.assign({}, c.firebase);
      if (emu) conf.projectId = "demo-septimus";
      var a = m[1], f = m[2], fbApp = m[0].initializeApp(conf), auth = a.getAuth(fbApp), db = f.getFirestore(fbApp);
      if (emu) { a.connectAuthEmulator(auth, "http://localhost:9099"); f.connectFirestoreEmulator(db, "localhost", 8080); }
      var provider = new a.GoogleAuthProvider();
      provider.setCustomParameters({ prompt: "select_account" });   // so "Switch account" shows Google's account chooser
      S.sdk = { auth: auth, db: db, a: a, f: f, provider: provider };
      if (emu) window.SeptimusSignup._test = { auth: auth, db: db, sdk: { app: m[0], auth: a, firestore: f } };
      a.onAuthStateChanged(auth, function (user) {
        ++seq;   // an answer still on its way for the previous person is now stale
        S.user = user; S.record = null; S.recordFailed = false; S.settled = !user;
        if (!user) setJoined(false);
        notify();
        if (user) loadRecord(user);
      });
      return S.sdk;
    });
    sdkP.catch(function () { sdkP = null; });   // let the next visit try again
    return sdkP;
  }
  // Read users/{uid}. Used when someone signs in and by "Try again". A late answer for an earlier call is ignored.
  var seq = 0;
  function loadRecord(user) {
    var mine = ++seq, f = S.sdk.f;
    S.record = null; S.recordFailed = false; S.settled = false;
    return f.getDoc(f.doc(S.sdk.db, "users", user.uid)).then(function (snap) { if (mine === seq) { S.record = snap.exists() ? snap.data() : null; if (S.record) setJoined(true); } })
      .catch(function () { if (mine === seq) S.recordFailed = true; })
      .then(function () { if (mine === seq) { S.settled = true; notify(); } });
  }
  function notify() { if (S.listener) S.listener(); }
  function signOut() {
    var go = function () { location.hash = "#/"; };
    return S.sdk.a.signOut(S.sdk.auth).then(go, go);
  }

  // The public group counts (progress/summary). Resolves to the data, or null when there is none or it cannot be read:
  // callers draw zeros and carry on, never an error.
  function loadSummary() {
    return loadSdk().then(function (sdk) { return sdk.f.getDoc(sdk.f.doc(sdk.db, "progress", "summary")); })
      .then(function (snap) { return snap.exists() ? snap.data() : null; })
      .catch(function () { return null; });
  }
  // One read of the summary per screen, shared by the progress card and the week lookup below.
  var sumCache = null;
  function summaryFor(t) {
    if (!sumCache || sumCache.t !== t) sumCache = { t: t, p: loadSummary() };
    return sumCache.p;
  }
  // The campaign week and last week: the script's answer in the summary when it has one, else counted from config.js.
  function weeksFrom(d) {
    return { wk: d && isNum(d.week) ? d.week : campaignWeek(), last: d && isNum(d.lastWeek) ? d.lastWeek : lastWeek() };
  }
  // The "N of about T stories learned" card, filled in when the summary arrives. withJoined adds the people-joined line (landing only).
  function progressCard(t, total, withJoined) {
    var title = el("div", { "class": "su-progress-title" }), fill = el("div", { "class": "su-fill" });
    var joinedEl = el("div", { "class": "su-muted su-small", hidden: true });   // stays hidden until progress/summary exists
    function setProgress(learned) {
      title.textContent = learned + " of about " + commas(total) + " stories learned";
      fill.style.width = Math.min(100, 100 * learned / Math.max(1, total)) + "%";
    }
    setProgress(0);
    summaryFor(t).then(function (d) {
      if (t !== token || !d) return;
      if (isNum(d.learned)) setProgress(d.learned);
      if (isNum(d.joined)) { joinedEl.textContent = d.joined + " " + (d.joined === 1 ? "person has" : "people have") + " joined"; joinedEl.hidden = false; }
    });
    var kids = [title, el("div", { "class": "su-track" }, [fill])];
    if (withJoined) kids.push(joinedEl);
    return el("div", { "class": "su-progress" }, kids);
  }

  // ---- in-app browsers (Google refuses sign-in inside them) -------------------------------------
  function inAppBrowser() {
    if (/^(localhost|127\.0\.0\.1)$/.test(location.hostname) && /[?&]inapp=1(&|$)/.test(location.search)) return true;
    var ua = navigator.userAgent || "";
    if (/Instagram|FBAN|FBAV|FB_IAB|WhatsApp|Line\//i.test(ua) || /; wv\)/.test(ua)) return true;
    return /iPhone|iPad|iPod/.test(ua) && !/Safari/.test(ua);
  }
  function pageUrl() {
    var s = savedSrc();
    return location.origin + location.pathname + (s ? "?src=" + encodeURIComponent(s) : "");
  }
  function openInBrowserPicture() {
    return svgEl("svg", { "class": "su-pic", viewBox: "0 0 240 120", role: "img", "aria-label": "Tap the menu with three dots, then Open in browser." }, [
      svgEl("rect", { "class": "su-pic-bg", x: "1", y: "1", width: "238", height: "118", rx: "10" }),
      svgEl("text", { "class": "su-pic-dots", x: "214", y: "28", "text-anchor": "middle" }, [document.createTextNode("⋯")]),
      svgEl("rect", { "class": "su-pic-menu", x: "100", y: "40", width: "130", height: "68", rx: "8" }),
      svgEl("rect", { "class": "su-pic-hi", x: "106", y: "46", width: "118", height: "24", rx: "5" }),
      svgEl("text", { "class": "su-pic-hitext", x: "165", y: "62", "text-anchor": "middle" }, [document.createTextNode("Open in browser")]),
      svgEl("text", { "class": "su-pic-row", x: "165", y: "92", "text-anchor": "middle" }, [document.createTextNode("Share")])
    ]);
  }
  function inAppNotice() {
    var btn = el("button", { type: "button", "class": "su-btn", text: "Copy link" });
    var box = el("input", { type: "text", readonly: true, "class": "su-copybox", value: pageUrl(), "aria-label": "Page link", hidden: true });
    var timer;
    btn.onclick = function () {
      function done() { btn.textContent = "Copied"; clearTimeout(timer); timer = setTimeout(function () { btn.textContent = "Copy link"; }, 2000); }
      function manual() { box.hidden = false; box.focus(); box.select(); }
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(pageUrl()).then(done, manual); else manual();
    };
    return el("div", {}, [
      el("p", { "class": "notice", text: "Google sign-in does not work inside this app. Open this page in Safari or Chrome." }),
      btn, box, openInBrowserPicture()
    ]);
  }

  // ---- landing --------------------------------------------------------------------------------
  var GOOGLE_G = '<svg width="18" height="18" viewBox="0 0 48 48" aria-hidden="true"><path fill="#EA4335" d="M24 9.5c3.5 0 6.6 1.2 9.1 3.6l6.8-6.8C35.8 2.4 30.3 0 24 0 14.6 0 6.5 5.4 2.6 13.2l7.9 6.1C12.4 13.6 17.7 9.5 24 9.5z"/><path fill="#4285F4" d="M46.5 24.5c0-1.6-.1-3.1-.4-4.5H24v9h12.7c-.6 3-2.3 5.500-4.800 7.200l7.600 5.900c4.400-4.100 7-10.100 7-17.600z"/><path fill="#FBBC05" d="M10.500 28.700c-.5-1.500-.8-3-.8-4.700s.3-3.200.8-4.700l-7.900-6.100C.9 16.500 0 20.100 0 24s.9 7.500 2.600 10.800l7.900-6.100z"/><path fill="#34A853" d="M24 48c6.500 0 11.900-2.100 15.900-5.800l-7.600-5.900c-2.100 1.400-4.900 2.300-8.300 2.300-6.300 0-11.600-4.200-13.500-9.900l-7.900 6.100C6.500 42.600 14.600 48 24 48z"/></svg>';

  // "Could not load your sign-up. Try again": used on the landing page and on Your data.
  function recordFailedNode(redraw) {
    var retry = el("button", { type: "button", "class": "su-linkbtn", text: "Try again" });
    retry.onclick = function () { loadRecord(S.user); redraw(); };
    return el("p", { "class": "su-error", role: "alert" }, ["Could not load your sign-up. ", retry]);
  }

  function landing(t) {
    loadSdk();
    withIndex(t, function (idx, st) {
      var c = cfg(), total = Math.round(st.stories / 100) * 100;
      var card = el("a", { "class": "su-progresslink", href: "#/progress" }, [progressCard(t, total, true)]);
      var dataLink = el("p", { "class": "su-center su-small" }, [link("Your data", "#/your-data")]);

      var area = el("div", { "class": "su-signin" });
      var errorLine = "";
      function drawArea() {
        var kids = [];
        if (afterYahrzeit()) { area.textContent = ""; return; }
        dataLink.hidden = !!(S.user && S.record && S.record.deleteRequested);
        if (S.user && S.record && S.record.deleteRequested) {
          // Deletion is waiting for the weekly script: nothing else on offer until it is cancelled (on Your data).
          kids.push(el("p", { "class": "su-signedin", text: "Your data is being deleted." }), el("p", { "class": "su-center su-small" }, [link("Your data", "#/your-data")]));
        } else if (S.user && S.recordFailed) {
          // Signed in but the record could not be read: never offer Google sign-in, and never the Join form.
          kids.push(recordFailedNode(drawArea));
        } else if (inAppBrowser()) {
          kids.push(inAppNotice());
        } else {
          var ready = !!S.sdk && S.settled;
          var btn = el("button", { type: "button", "class": "su-google", disabled: !ready });
          var g = el("span", { "class": "su-g", "aria-hidden": "true" }); g.innerHTML = GOOGLE_G;   // constant markup, nothing from the person
          btn.appendChild(g); btn.appendChild(document.createTextNode("Sign in with Google to join"));
          btn.onclick = function () {
            // No await before this call: the popup must open straight from the tap or the browser blocks it.
            S.sdk.a.signInWithPopup(S.sdk.auth, S.sdk.provider).catch(function (e) {
              var code = (e && e.code) || "";
              if (code === "auth/popup-closed-by-user" || code === "auth/cancelled-popup-request") errorLine = "";
              else if (code === "auth/popup-blocked") errorLine = "The sign-in window was blocked. Allow pop-ups and try again.";
              else errorLine = "Could not sign in. Check your connection and try again.";
              drawArea();
            });
          };
          kids.push(btn);
          if (errorLine) kids.push(el("p", { "class": "su-error", role: "alert", text: errorLine }));
          kids.push(el("p", { "class": "su-muted su-small su-center", text: "We email you your stories each week." }));
        }
        var contact = cfg().contactEmail;
        if (contact && !(S.user && S.record)) kids.push(el("p", { "class": "su-muted su-small su-center" }, ["No Google account? Email ", link(contact, "mailto:" + contact)]));
        area.textContent = "";
        kids.forEach(function (k) { area.appendChild(k); });
      }
      // Someone who joined on this device waits for sign-in to settle instead of seeing the pitch flash by.
      var held = load(JOINED, false) && !S.settled, page = [
        el("h1", { text: "Learn every story in the Talmud, together" }),
        el("p", { "class": "su-dedication", text: "In memory of Joe Septimus." }),
        el("p", { "class": "su-muted", text: afterYahrzeit() ? "Thank you to everyone who learned."
          : "A few minutes a week" + (launchText() ? ", from " + launchText() : "") + " until his yahrzeit, " + label() + "." }),
        card,
        area,
        dataLink,
        el("p", { "class": "su-links" }, aboutLinks())
      ];
      function reveal() { if (held) { held = false; show(page); } }
      S.listener = function () {
        if (t !== token) return;
        if (S.user && S.settled && S.record && !S.record.deleteRequested) { redirect("#/my"); return; }
        if (S.user && S.settled && !S.record && !S.recordFailed) { redirect("#/join"); return; }   // signed in but never answered the question
        if (S.settled) reveal();
        if (!held) drawArea();
      };
      sdkP && sdkP.catch(function () { errorLine = "Could not sign in. Check your connection and try again."; reveal(); drawArea(); });
      show(held ? [el("p", { "class": "su-muted", text: "Loading…" })] : page);
      S.listener();
    });
  }

  // ---- minutes question -----------------------------------------------------------------------
  var PRESETS = [5, 10, 15, 30];
  function join(t) {
    if (afterYahrzeit()) { redirect("#/"); return; }
    show([el("p", { "class": "su-muted", text: "Loading…" })]);
    loadSdk().catch(function () { sdkFailed(t); });
    var built = false, uid = null;
    S.listener = function () {
      if (t !== token) return;
      // The screen was built for one person; if the account changes under it, do not leave their form up.
      if (built && (!S.user || S.user.uid !== uid)) { redirect("#/"); return; }
      if (!S.settled) return;
      if (!S.user || S.recordFailed || (S.record && S.record.deleteRequested)) { redirect("#/"); return; }   // a failed read must never reach the Join form; a pending deletion has no form
      if (built) return;
      built = true; uid = S.user.uid;
      withIndex(t, function (idx, st) { drawJoin(t, st); });
    };
    S.listener();
  }
  function drawJoin(t, st) {
    var max = cfg().maxMinutes || 120, has = !!S.record, current = has && S.record.minutesPerWeek > 0 ? S.record.minutesPerWeek : 10;
    var otherOn = PRESETS.indexOf(current) === -1, chosen = otherOn ? "other" : String(current);
    var legend = el("legend", { "class": "su-sr", text: "Minutes a week" });
    var group = el("fieldset", { "class": "su-choices" }, [legend]);
    var otherBox = el("input", { type: "text", inputmode: "numeric", id: "su-other", "class": "su-number", "aria-label": "Minutes a week", autocomplete: "off", value: otherOn ? String(current) : "" });
    var otherMsg = el("p", { "class": "su-error", role: "alert", hidden: true, text: "Enter a whole number from 1 to " + max + "." });
    var otherWrap = el("div", { hidden: !otherOn }, [otherBox, otherMsg]);
    var estimate = el("p", { "class": "notice" });
    var joinBtn = el("button", { type: "button", "class": "su-btn", text: has ? "Save" : "Join" });
    var errLine = el("p", { "class": "su-error su-center", role: "alert", hidden: true });

    // The minutes the person has chosen, or 0 when "Other" holds something that is not 1..max.
    function minutes() {
      if (chosen !== "other") return +chosen;
      var v = otherBox.value.trim();
      return /^\d+$/.test(v) && +v >= 1 && +v <= max ? +v : 0;
    }
    function refresh(showOtherError) {
      var m = minutes();
      otherMsg.hidden = !(chosen === "other" && !m && (otherBox.value.trim() || showOtherError));
      estimate.hidden = !m;
      if (m) { var k = storiesFor(m, st); estimate.textContent = m + (m === 1 ? " minute" : " minutes") + " a week is about " + k + (k === 1 ? " story." : " stories."); }
    }
    PRESETS.concat(["other"]).forEach(function (v) {
      var id = "su-m-" + v;
      var input = el("input", { type: "radio", name: "su-minutes", id: id, value: String(v), checked: String(v) === chosen });
      input.onchange = function () { chosen = input.value; otherWrap.hidden = chosen !== "other"; if (chosen === "other") otherBox.focus(); refresh(false); };
      group.appendChild(input);
      group.appendChild(el("label", { "for": id, text: v === "other" ? "Other" : v + " minutes" }));
    });
    group.appendChild(otherWrap);   // the number box comes after the "Other" choice it belongs to
    otherBox.oninput = function () { refresh(false); };

    joinBtn.onclick = function () {
      var m = minutes();
      if (!m) { refresh(true); otherBox.focus(); return; }
      var f = S.sdk.f, ref = f.doc(S.sdk.db, "users", S.user.uid);
      joinBtn.disabled = true; joinBtn.textContent = "Saving…"; errLine.hidden = true;
      var say = function (text) { errLine.textContent = text; errLine.hidden = false; };
      // The only place a users record is ever written. Join creates it; Save changes the minutes and nothing else.
      var write = has ? f.updateDoc(ref, { minutesPerWeek: m })
        : f.setDoc(ref, { createdAt: f.serverTimestamp(), minutesPerWeek: m, src: savedSrc(), deleteRequested: false });
      watchSlow(write, t, say).then(function () {
        S.record = Object.assign({}, S.record || {}, { minutesPerWeek: m });
        setJoined(true);
        if (t === token) location.hash = "#/my";   // only if they are still on this screen
      }).catch(function () {
        say(SAVE_ERR);
        joinBtn.disabled = false; joinBtn.textContent = has ? "Save" : "Join";
      });
    };
    var switchBtn = el("button", { type: "button", "class": "su-linkbtn", text: "Not you? Switch account" });
    switchBtn.onclick = signOut;

    show([
      el("p", { "class": "su-muted su-small" }, ["Signed in as " + (S.user.email || ""), " ", switchBtn]),
      el("h1", { text: "How many minutes a week will you learn?" }),
      el("p", { "class": "su-muted", text: (launchText() ? "From " + launchText() + " until " : "Until ") + label() + ". You can change this any time." }),
      group, estimate, joinBtn, errLine,
      has ? el("p", { "class": "su-muted su-small su-center", text: "A change applies from next Sunday." }) : null,
      el("p", { "class": "su-muted su-small su-center", text: startLine() })
    ]);
    refresh(false);
  }

  // ---- My stories -----------------------------------------------------------------------------
  var SAVE_ERR = "Could not save. Check your connection and try again.";
  function myStories(t) {
    show([el("p", { "class": "su-muted", text: "Loading…" })]);
    loadSdk().catch(function () { sdkFailed(t); });
    var drawn = false, uid = null;
    S.listener = function () {
      if (t !== token || !S.settled) return;
      if (drawn && (!S.user || S.user.uid !== uid)) { redirect("#/"); return; }   // the account changed under the page
      if (drawn) return;
      if (!S.user || !S.record || S.record.deleteRequested) { redirect("#/"); return; }   // signed out, no sign-up yet, record unreadable, or deletion pending
      drawn = true; uid = S.user.uid;
      loadMine(t, S.user);
    };
    S.listener();
  }
  function loadMine(t, user) {
    var f = S.sdk.f, col = f.collection(S.sdk.db, "assignments");
    // The rules only allow a list filtered on the person's own uid, so every query carries it (and equality tests only: no index).
    // Open rows (not learned, not handed back) are always read; when the week is known, so is every row of this week, learned or not.
    var open = f.query(col, f.where("uid", "==", user.uid), f.where("doneAt", "==", null), f.where("releasedAt", "==", null));
    // The summary is waited for first: it says which week it is. It never fails (null when unreadable).
    Promise.all([getIndex(), summaryFor(t)]).then(function (res) {
      var wk = weeksFrom(res[1]);
      var qs = [f.getDocs(open)];
      if (wk.wk != null) qs.push(f.getDocs(f.query(col, f.where("uid", "==", user.uid), f.where("week", "==", wk.wk))));
      return Promise.all(qs).then(function (snaps) { return [res[0], wk, snaps]; });
    }).then(function (res) {
      var idx = res[0], wk = res[1], byId = {}, rows = [], slugs = [], failed = {};
      res[2].forEach(function (snap) { snap.forEach(function (d) { byId[d.id] = { id: d.id, ref: d.ref, d: d.data() }; }); });
      Object.keys(byId).forEach(function (id) { if (byId[id].d.releasedAt == null) rows.push(byId[id]); });   // handed-back rows are never listed
      rows.forEach(function (r) {
        r.slug = String(r.d.storyId || "").split("-")[0];
        if (slugs.indexOf(r.slug) === -1) slugs.push(r.slug);
      });
      // Each tractate file on its own: one that fails to load must not blank the page.
      return Promise.all(slugs.map(function (s) { return getTractate(s, idx).catch(function () { failed[s] = true; return null; }); })).then(function (files) {
        var found = {};   // storyId -> { story, pos } where pos is the story's place in its tractate file
        files.forEach(function (d) { if (d) d.stories.forEach(function (s, i) { found[s.id] = { story: s, pos: i }; }); });
        return followMerged(rows.map(function (r) { return r.d.storyId; }), found, idx).then(function () {
          if (t === token) drawMine(t, idx, stats(idx), rows, found, failed, wk);
        });
      });
    }).catch(function () {
      if (t === token) show([el("p", { "class": "notice", text: "Could not load your stories. Please check your connection and reload." })]);
    });
  }
  function drawMine(t, idx, st, rows, found, failed, weeks) {
    var wpm = cfg().wpm || 75, touched = {}, onTick = function () {};   // touched: rows ticked during this visit stay on the page
    rows.forEach(function (r) {
      var hit = found[r.d.storyId];
      r.hit = hit || null;
      r.ti = shasRank(r.slug);
      r.pos = hit ? hit.pos : 1e9;
    });
    // Always on the page, empty until there is something to say, so a screen reader announces the text when it arrives.
    var topStatus = el("p", { "class": "su-rowmsg", role: "status" });

    function rowNode(r, latest, m) {
      var s = r.hit && r.hit.story, learned = r.d.doneAt != null, busy = false, sumId = "su-sum-" + r.id;
      var name = s ? "Learned: " + refLabel(s) : failed[r.slug] ? "Learned: story that did not load" : "Learned: story no longer on the list";
      var tick = el("button", { type: "button", "class": "su-tick", "aria-pressed": String(learned), "aria-label": name, "aria-describedby": sumId });
      var ring = el("span", { "class": "check", "aria-hidden": "true", text: learned ? "✓" : "" });
      tick.appendChild(ring);
      var msg = el("p", { "class": "su-rowmsg", role: "status" });
      var body = [];
      if (s) {
        var mins = Math.ceil(s.words / wpm), top = [el("span", {}, [el("span", { "class": "row-ref", text: refLabel(s) })])];
        if (r.d.week < latest) top[0].appendChild(el("span", { "class": "chip", text: "from week " + r.d.week }));
        if (m > 0 && s.words / wpm > m) top[0].appendChild(el("span", { "class": "chip", text: "longer than usual" }));
        top.push(el("span", { "class": "su-rowmin", text: "about " + mins + " min" }));
        body.push(el("a", { "class": "su-rowlink", href: "#/s/" + s.id }, [el("div", { "class": "su-rowtop" }, top), el("div", { "class": "row-sum", id: sumId, text: s.summary })]));
      } else {
        // No link: either the story left the list, or its tractate file did not load.
        body.push(el("div", { "class": "row-sum", id: sumId, text: failed[r.slug] ? "Could not load this story." : "No longer on the list" }));
      }
      body.push(msg);
      var row = el("div", { "class": "row su-myrow" + (learned ? " read" : "") }, [tick, el("div", { "class": "su-rowbody" }, body)]);
      tick.onclick = function () {
        if (busy) return;   // not the disabled attribute: that would drop keyboard focus
        var f = S.sdk.f, want = r.d.doneAt == null;
        busy = true; tick.setAttribute("aria-disabled", "true"); msg.textContent = "Saving…";
        // The tick changes only after the write is confirmed.
        watchSlow(f.updateDoc(r.ref, { doneAt: want ? f.serverTimestamp() : null }), t, function (x) { msg.textContent = x; }).then(function () {
          r.d.doneAt = want ? new Date() : null; touched[r.id] = true;
          row.className = "row su-myrow" + (want ? " read" : "");
          ring.textContent = want ? "✓" : "";
          tick.setAttribute("aria-pressed", String(want));
          msg.textContent = "Saved"; busy = false; tick.removeAttribute("aria-disabled");
          onTick();
        }).catch(function () { msg.textContent = SAVE_ERR; busy = false; tick.removeAttribute("aria-disabled"); });
      };
      return row;
    }

    function render() {
      var m = S.record.minutesPerWeek, wk = weeks.wk, last = weeks.last, latest = wk;
      if (latest == null) { latest = 0; rows.forEach(function (r) { if (isNum(r.d.week) && r.d.week > latest) latest = r.d.week; }); }   // week unknown: the newest week on the page
      // Learned rows stay for this week (and for any row ticked during this visit); older learned rows are not listed.
      var shown = rows.filter(function (r) { return r.d.doneAt == null || touched[r.id] || (wk != null && r.d.week === wk); })
        .sort(function (a, b) { return (a.d.week - b.d.week) || (a.ti - b.ti) || (a.pos - b.pos); });
      var now = shown.filter(function (r) { return r.d.week >= latest; }), earlier = shown.filter(function (r) { return r.d.week < latest; });
      var paused = m > 0 && S.record.pausedAt != null;   // stopped wins over paused
      var nodes = [el("h1", { text: "My stories" })];
      if (m > 0) {
        var mt = m + (m === 1 ? " minute" : " minutes") + " a week";
        nodes.push(el("p", { "class": "su-muted", text: wk != null && last != null && wk >= 1 && wk <= last ? "Week " + wk + " of " + last + " · " + mt : mt }));
      }
      nodes.push(topStatus);
      if (paused) {
        var resume = el("button", { type: "button", "class": "su-btn", text: "Resume" }), rmsg = el("p", { "class": "su-rowmsg", role: "status" }), rbusy = false;
        resume.onclick = function () {
          if (rbusy) return;
          rbusy = true; resume.textContent = "Saving…"; resume.setAttribute("aria-disabled", "true"); rmsg.textContent = "";
          watchSlow(S.sdk.f.updateDoc(S.sdk.f.doc(S.sdk.db, "users", S.user.uid), { pausedAt: null }), t, function (x) { rmsg.textContent = x; }).then(function () {
            S.record = Object.assign({}, S.record, { pausedAt: null });
            if (t !== token) return;
            render();
            var said = ended() ? "Resumed." : hasLaunched() ? "Resumed. New stories arrive Sunday " + fmtDate(nextSunday()) + "."
              : launchText() ? "Resumed. Your first stories arrive the week of " + launchText() + "." : "Resumed.";
            setTimeout(function () { if (t === token) topStatus.textContent = said; }, 100);   // after the redraw, so it is announced
          }).catch(function () { rmsg.textContent = SAVE_ERR; rbusy = false; resume.textContent = "Resume"; resume.removeAttribute("aria-disabled"); });
        };
        nodes.push(el("p", { "class": "notice", text: "Your stories are paused because none were marked learned." }), resume, rmsg);
      }
      if (m === 0) nodes.push(el("p", { "class": "notice", text: "Your stories are stopped." }), link("Start again", "#/join", "su-btn"));
      if (!shown.length && m > 0 && !paused) {
        nodes.push(el("p", { text: wk != null && last != null && wk > last ? "The weekly stories have ended."
          : !hasLaunched() ? (launchText() ? "Your first stories arrive the week of " + launchText() + "." : "The learning has not started yet. We will email you when it begins.") : "Nothing open right now. New stories arrive each Sunday." }));
      }
      [["This week", now], ["Still open from earlier weeks", earlier]].forEach(function (sec) {
        if (!sec[1].length) return;
        nodes.push(el("h2", { "class": "su-h2", text: sec[0] }));
        sec[1].forEach(function (r) { nodes.push(rowNode(r, latest, m)); });
        if (sec[1] === now) {
          var done = el("p", { "class": "su-muted", text: "All done for this week." });
          onTick = function () { done.hidden = !now.every(function (r) { return r.d.doneAt != null; }); };
          onTick();
          nodes.push(done);
        }
      });
      if (earlier.length) nodes.push(el("p", { "class": "notice", text: "Stories you do not get to stay on your list for about two weeks, then go back to the group. Nothing is lost." }));
      nodes.push(el("h2", { "class": "su-h2", text: "Everyone together" }));
      var card = progressCard(t, Math.round(st.stories / 100) * 100, false);
      card.appendChild(link("See overall progress", "#/progress", "su-btn su-btn-outline"));
      nodes.push(card);
      // Two short rows, so no separator dot is left dangling at phone width.
      nodes.push(el("p", { "class": "su-links" }, [link("Change my minutes", "#/join"), " · ", link("Your data", "#/your-data")]));
      nodes.push(el("p", { "class": "su-links" }, aboutLinks()));
      show(nodes);
    }
    render();
  }

  // ---- progress (public) ------------------------------------------------------------------------
  function dateTime(d) { return fmtDate(d) + ", " + String(d.getHours()).padStart(2, "0") + ":" + String(d.getMinutes()).padStart(2, "0"); }
  // The person's own learned stories, de-duplicated, in Shas order. Resolves to a node, or null when the read fails (no error shown).
  function learnedSection(t, idx, uid) {
    var f = S.sdk.f;
    return f.getDocs(f.query(f.collection(S.sdk.db, "assignments"), f.where("uid", "==", uid))).then(function (snap) {
      var seen = {}, items = [], slugs = [], failed = {};
      snap.forEach(function (d) {
        var id = d.data().storyId, slug = String(id || "").split("-")[0];
        if (d.data().doneAt == null || !id || seen[id]) return;
        seen[id] = true; items.push({ id: id, slug: slug });
        if (slugs.indexOf(slug) === -1) slugs.push(slug);
      });
      return Promise.all(slugs.map(function (sl) { return getTractate(sl, idx).catch(function () { failed[sl] = true; return null; }); })).then(function (files) {
        var found = {};
        files.forEach(function (d) { if (d) d.stories.forEach(function (s, i) { found[s.id] = { story: s, pos: i }; }); });
        return followMerged(items.map(function (x) { return x.id; }), found, idx).then(function () { return found; });
      }).then(function (found) {
        items.forEach(function (x) { x.hit = found[x.id] || null; x.ti = shasRank(x.slug); x.pos = x.hit ? x.hit.pos : 1e9; });
        items.sort(function (a, b) { return (a.ti - b.ti) || (a.pos - b.pos); });
        var n = items.length, kids = [el("h2", { text: "Stories you have learned" }),
          el("p", { text: n ? "You have learned " + n + (n === 1 ? " story." : " stories.") : "You have not marked a story learned yet." })];
        if (n) {
          var list = el("ul", { "class": "su-list su-learned" });
          items.forEach(function (x) {
            var s = x.hit && x.hit.story;
            list.appendChild(el("li", {}, s ? [link(refLabel(s), "#/s/" + s.id, "su-learned-ref"), el("div", { "class": "su-muted su-small", text: s.summary })]
              : [el("div", { "class": "su-muted", text: failed[x.slug] ? "Could not load this story." : "No longer on the list" })]));
          });
          kids.push(el("details", { "class": "su-more" }, [el("summary", { text: "Show them" }), list]));
        }
        return el("div", {}, kids);
      });
    }).catch(function () { return null; });
  }
  function progress(t) {
    show([el("p", { "class": "su-muted", text: "Loading…" })]);
    withIndex(t, function (idx, st) {
      summaryFor(t).then(function (d) {
        if (t !== token) return;
        d = d || {};
        var learned = num(d.learned), done = num(d.roundsCompleted), by = d.byTractate || {};
        var head = done === 0 ? "First time through Shas" : "Shas completed " + done + (done === 1 ? " time" : " times");
        var cardKids = [el("div", { "class": "su-progress-big", text: head }),
          el("p", { "class": "su-progress-title", text: "This time through: " + learned + " of " + commas(st.stories) + " stories learned" }),
          el("div", { "class": "su-track" }, [el("div", { "class": "su-fill", style: "width:" + Math.min(100, 100 * learned / Math.max(1, st.stories)) + "%" })])];
        if (num(d.openInRound) > 0 && learned > 0.9 * st.stories) cardKids.push(el("p", { "class": "su-muted", text: d.openInRound + " stories still open this time through" }));
        var small = [], w = weeksToYahrzeit();
        if (isNum(d.joined)) small.push(d.joined + " " + (d.joined === 1 ? "person has" : "people have") + " joined");
        if (w) small.push(w + (w === 1 ? " week" : " weeks") + " until " + (cfg().yahrzeitLabel || "8 Elul"));
        if (small.length) cardKids.push(el("p", { "class": "su-muted su-small", text: small.join(" · ") }));
        var mine = el("div");   // "Stories you have learned": filled only for a signed-in person with a record
        var nodes = [el("h1", { text: "Progress" }), el("p", { "class": "dedication", text: "In memory of Joe Septimus." }), el("div", { "class": "su-progress" }, cardKids),
          mine, el("h2", { text: "The whole group, tractate by tractate" }),
          el("p", { "class": "su-muted", text: "A tractate is one volume of the Talmud. Each bar shows how many of its stories the group has learned this time through." })];
        sortTractates(idx.tractates).forEach(function (x) {
          var n = num(by[x.tractate]);
          nodes.push(el("div", { "class": "card" }, [
            el("span", { "class": "card-he", text: x.he }), el("div", { "class": "card-name", text: x.name }),
            el("div", { "class": "bar-track" }, [el("div", { "class": "bar-fill", style: "width:" + Math.min(100, x.story ? 100 * n / x.story : 0) + "%" })]),
            el("div", { "class": "card-meta", text: n + " of " + x.story + " learned by the group" + (x.reviewed ? "" : " · not yet reviewed") })]));
        });
        var at = d.updatedAt && typeof d.updatedAt.toDate === "function" ? d.updatedAt.toDate() : null;
        if (at) nodes.push(el("p", { "class": "su-muted su-small", text: "Updated " + dateTime(at) }));
        nodes.push(el("p", { "class": "su-muted su-small", text: listLine(idx, st) }));
        // Signed-out visitors only, and only once we know that: sign-in has settled with nobody, or the SDK would not load.
        var invite = el("div"), sdkBad = false;
        function drawInvite() {
          if (t !== token) return;
          invite.textContent = "";
          if (!S.user && (S.settled || sdkBad)) invite.appendChild(link("Sign in with Google to join", "#/", "su-btn su-btn-outline"));
        }
        var mineUid = null;   // whose list is drawn (or being fetched); one read per person
        function drawMineLearned() {
          if (t !== token || !S.settled) return;
          if (!S.user || !S.record) { mine.textContent = ""; mineUid = null; return; }
          if (mineUid === S.user.uid) return;
          mineUid = S.user.uid;
          learnedSection(t, idx, S.user.uid).then(function (node) { if (t === token && mineUid === S.user.uid) { mine.textContent = ""; if (node) mine.appendChild(node); } });
        }
        S.listener = function () { drawInvite(); drawMineLearned(); };
        loadSdk().then(S.listener, function () { sdkBad = true; drawInvite(); });
        nodes.push(invite, back());
        show(nodes);
      });
    });
  }

  // ---- small text pages -----------------------------------------------------------------------
  function how(t) {
    withIndex(t, function (idx, st) {
      var names = idx.tractates.filter(function (x) { return x.reviewed; }).map(function (x) { return x.name; });
      var list = names.length > 1 ? names.slice(0, -1).join(", ") + " and " + names[names.length - 1] : names.join("");
      show([
        el("h1", { text: "How the stories were chosen" }),
        el("p", { text: "A story here is a passage of the Babylonian Talmud that tells of something that happened: people, an event, and how it turned out." }),
        el("p", { text: "The stories were found by software. In " + list + " they were then checked by Prof. Jeff Rubenstein of New York University. The other tractates are marked “not yet reviewed”: some passages there may not be stories, or may start or end in the wrong place." }),
        el("p", { text: listLine(idx, st) }),
        back()
      ]);
    });
  }
  function yourData(t) {
    var holder = el("div"), status = el("p", { "class": "su-rowmsg", role: "status", tabindex: "-1" });   // status line: exists from the start, text goes in later
    var out = el("button", { type: "button", "class": "su-linkbtn", text: "Sign out", hidden: true });
    out.onclick = signOut;
    show([
      el("h1", { text: "Your data" }),
      el("ul", { "class": "su-list" }, [
        el("li", { text: "What we store: your Google name and email address, the link you joined from, how many minutes a week you chose, and which stories you were given and when you marked them learned." }),
        el("li", { text: "Who sees it: Simon Brief, who runs the site. The Septimus family sees how many people joined from each community, and names. Only you and Simon see which stories you read." }),
        el("li", { text: "Nothing about you is shown publicly." }),
        el("li", { text: "Stopping: you can stop your stories or delete your data at any time, on this page when you are signed in." }),
        el("li", { text: "Everyone's personal data is deleted six months after the yahrzeit." }),
        el("li", { text: "You must be 13 or older to join." })
      ]),
      holder, status, out,
      back()
    ]);
    // Signed-in people with a sign-up get the stop / delete controls; everyone else sees the page as above.
    var deleted = false, mode = "idle", busy = false;
    function setStatus(text) { status.textContent = text; }
    // After a redraw the button that had focus is gone: put focus on the first button of the new state, or on the status line.
    function focusFirst() { var b = holder.querySelector("button"); (b || status).focus(); }
    function draw(refocus) {
      if (t !== token) return;
      out.hidden = !S.user;
      if (deleted) return;
      holder.textContent = "";
      if (S.settled && S.user && S.recordFailed) { holder.appendChild(recordFailedNode(draw)); return; }
      if (!S.settled || !S.user || !S.record) return;
      var stopped = S.record.minutesPerWeek === 0, kids = [el("h2", { text: "Your sign-up" })];
      var ref = S.sdk.f.doc(S.sdk.db, "users", S.user.uid);
      // Run a write for a button; busy stops a second tap without the disabled attribute (which would drop focus).
      function run(btn, label, write, after) {
        if (busy) return;
        busy = true; btn.setAttribute("aria-disabled", "true"); btn.textContent = "Saving…"; setStatus("");
        watchSlow(write(), t, setStatus).then(function () { busy = false; setStatus(""); after(); },
          function () { busy = false; draw(true); setStatus(SAVE_ERR); });
      }
      function ask(text, doText, write, after) {
        var yes = el("button", { type: "button", "class": "su-btn", text: doText }), no = el("button", { type: "button", "class": "su-btn su-btn-outline", text: "Cancel" });
        yes.onclick = function () { run(yes, doText, write, after); };
        no.onclick = function () { if (busy) return; mode = "idle"; setStatus(""); draw(true); };
        kids.push(el("p", { "class": "notice", text: text }), yes, no);
      }
      if (stopped && !S.record.deleteRequested) kids.push(el("p", { text: "Your stories are stopped. You can start again any time." }));
      if (S.record.deleteRequested) {
        // Waiting for the weekly script. Nothing else is offered until it is cancelled.
        var cancel = el("button", { type: "button", "class": "su-linkbtn", text: "Cancel deletion" });
        cancel.onclick = function () {
          run(cancel, "Cancel deletion", function () { return S.sdk.f.updateDoc(ref, { deleteRequested: false }); },
            function () { S.record = Object.assign({}, S.record, { deleteRequested: false }); draw(true); });
        };
        kids.push(el("p", { text: "Your data is being deleted." }), cancel);
      } else if (mode === "stop" && !stopped) {
        ask("You will get no new stories. Stories you have not read go back to the group.", "Stop",
          function () { return S.sdk.f.updateDoc(ref, { minutesPerWeek: 0 }); },
          function () { S.record = Object.assign({}, S.record, { minutesPerWeek: 0 }); mode = "idle"; draw(true); });
      } else if (mode === "delete") {
        ask("This removes your account and your name and email from our records. A record of which stories were read, with no name attached, is kept so the group totals stay right. It cannot be undone.", "Delete my data",
          function () { return S.sdk.f.updateDoc(ref, { deleteRequested: true }); },
          function () {
            deleted = true;
            holder.textContent = "";
            setStatus("Your data will be deleted, usually within a day.");
            status.focus();
            S.sdk.a.signOut(S.sdk.auth).catch(function () {});
          });
      } else {
        if (!stopped) { var b1 = el("button", { type: "button", "class": "su-btn su-btn-outline", text: "Stop my stories" }); b1.onclick = function () { mode = "stop"; setStatus(""); draw(true); }; kids.push(b1); }
        var b2 = el("button", { type: "button", "class": "su-btn su-btn-outline", text: "Delete my data" }); b2.onclick = function () { mode = "delete"; setStatus(""); draw(true); }; kids.push(b2);
      }
      kids.forEach(function (k) { holder.appendChild(k); });
      if (refocus === true) focusFirst();
    }
    S.listener = draw;
    loadSdk().then(draw, function () {});   // no SDK: the page stays as it is for a signed-out visitor
  }
  // Paragraphs about Joe Septimus, from his family, separated by blank lines. Empty hides the About page and every link to it.
  var ABOUT_TEXT = "";
  // The "About" and "How the stories were chosen" links; no About link (and no separator) while ABOUT_TEXT is empty.
  function aboutLinks() {
    var how = link("How the stories were chosen", "#/how");
    return ABOUT_TEXT ? [link("About Joe Septimus", "#/about"), " · ", how] : [how];
  }
  function about() {
    if (!ABOUT_TEXT) { redirect("#/"); return; }
    var paras = ABOUT_TEXT.split(/\n\s*\n/).map(function (p) { return el("p", { text: p.trim() }); });
    show([el("h1", { text: "About Joe Septimus" })].concat(paras, [back()]));
  }

  // ---- routing --------------------------------------------------------------------------------
  // On the staging copy of the site (config.js sets `staging`), say so in the top bar so nobody mistakes it for the real one.
  function stagingLabel() {
    var title = document.querySelector(".bar-title");
    if ((window.SEPTIMUS_CONFIG || {}).staging && title) title.appendChild(el("span", { "class": "su-staging", text: "Staging" }));
  }
  // The three links under the title, on every page. The first is "Join" until this device has joined.
  var NAV_AT = { browse: 1, t: 1, s: 1, progress: 2 };   // which link marks the page (route name -> link number)
  function navInit() {
    var nav = el("nav", { "class": "su-nav", "aria-label": "Main" });
    for (var i = 0; i < 3; i++) { navLinks.push(el("a", { href: ["#/", "#/browse", "#/progress"][i], text: ["Join", "All stories", "Progress"][i] })); nav.appendChild(navLinks[i]); }
    document.getElementById("settings").after(nav);   // before <main>, so index.html needs no edit
  }
  function navUpdate() {
    if (!navLinks.length) return;
    var j = load(JOINED, false), c = NAV_AT.hasOwnProperty(here) ? NAV_AT[here] : (j ? here === "my" : here === "" || here === "join") ? 0 : -1;
    navLinks[0].textContent = j ? "My stories" : "Join";
    navLinks[0].setAttribute("href", j ? "#/my" : "#/");
    navLinks.forEach(function (a, i) { if (i === c) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current"); });
  }

  var SCREENS = { "": landing, join: join, how: how, "your-data": yourData, about: about, my: myStories, progress: progress };
  function route(parts) {
    if (!srcDone) { srcDone = true; rememberSrc(); stagingLabel(); navInit(); }
    var t = ++token;
    S.listener = null;
    var name = here = parts[1] || "";
    navUpdate();
    if (!Object.prototype.hasOwnProperty.call(SCREENS, name)) return false;
    SCREENS[name](t);
    return true;
  }

  // The story page, called by app.js after it draws a story: if the story is one of yours, add a "Mark as learned" block
  // that writes to your row. Anyone else sees the page unchanged.
  // TODO(signup d): "Next story" on that block.
  function story(id) {
    if (!load(JOINED, false)) return;   // not joined on this device: no Firebase on reader pages
    var t = token;
    loadSdk().catch(function () {});
    S.listener = function () {
      if (t !== token || !S.settled) return;
      S.listener = null;
      if (!S.user || !S.record) return;
      var f = S.sdk.f, q = f.query(f.collection(S.sdk.db, "assignments"), f.where("uid", "==", S.user.uid), f.where("storyId", "==", id));
      f.getDocs(q).then(function (snap) {
        var row = null, actions = app.querySelector(".actions");
        snap.forEach(function (d) { if (d.data().releasedAt == null) row = d; });
        if (!row || t !== token || location.hash !== "#/s/" + id || !actions || app.querySelector(".su-mine")) return;   // not yours, or they have moved on
        var learned = row.data().doneAt != null, busy = false;
        var btn = el("button", { type: "button", "class": "btn primary" }), msg = el("p", { "class": "su-rowmsg", role: "status" });
        function paint() { btn.textContent = learned ? "✓ Learned" : "Mark as learned"; btn.setAttribute("aria-pressed", String(learned)); }
        paint();
        btn.onclick = function () {
          if (busy) return;   // not the disabled attribute: that would drop keyboard focus
          busy = true; btn.setAttribute("aria-disabled", "true"); msg.textContent = "Saving…";
          watchSlow(f.updateDoc(row.ref, { doneAt: learned ? null : f.serverTimestamp() }), t, function (x) { msg.textContent = x; }).then(function () {
            learned = !learned; paint(); msg.textContent = "Saved"; busy = false; btn.removeAttribute("aria-disabled");
          }).catch(function () { msg.textContent = SAVE_ERR; busy = false; btn.removeAttribute("aria-disabled"); });
        };
        actions.parentNode.insertBefore(el("div", { "class": "su-mine" }, [el("p", { "class": "notice", text: "One of your stories." }), btn, msg, link("← Back to my stories", "#/my", "su-back")]), actions);
      }).catch(function () {});
    };
    S.listener();
  }

  window.SeptimusSignup = { route: route, story: story };
})();
