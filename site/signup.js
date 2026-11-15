// Sign-up pages: landing, minutes question, "You're in", and three small text pages.
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
  function show(nodes) { app.textContent = ""; nodes.forEach(function (n) { app.appendChild(n); }); }
  function link(text, href, cls) { return el("a", { href: href, text: text, class: cls }); }
  function back() { return el("p", {}, [link("← Back", "#/", "su-keep")]); }   // su-keep: this "#/" is the landing page

  // ---- ?src=: the community link. Kept in storage so it survives leaving an in-app browser --
  var SRC_KEY = "septimus-src";
  function allowedSrc(v) { return typeof v === "string" && v && (cfg().communities || []).indexOf(v) !== -1; }
  // Called on the first route, once config.js has loaded, so the allowlist is known before anything is stored.
  function rememberSrc() {
    var m = /[?&]src=([^&#]*)/.exec(location.search), v;
    if (!m) return;
    try { v = decodeURIComponent(m[1]).toLowerCase(); } catch (e) { return; }
    if (allowedSrc(v)) save(SRC_KEY, v);
  }
  function savedSrc() { var v = load(SRC_KEY, ""); return allowedSrc(v) ? v : ""; }

  // ---- dates and numbers ----------------------------------------------------------------------
  var MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
  function parseISO(s) { var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(s || ""); return m ? new Date(+m[1], +m[2] - 1, +m[3]) : null; }
  function fmtDate(d) { return d.getDate() + " " + MONTHS[d.getMonth()]; }
  function today() { var d = new Date(); d.setHours(0, 0, 0, 0); return d; }
  function launchText() { var d = parseISO(cfg().launchDate); return d ? fmtDate(d) : "[launch date]"; }
  function hasLaunched() { var d = parseISO(cfg().launchDate); return !!d && today() >= d; }
  function afterYahrzeit() { var d = parseISO(cfg().yahrzeit); return !!d && today() > d; }
  function nextMonday() { var d = today(); d.setDate(d.getDate() + (((1 - d.getDay() + 7) % 7) || 7)); return d; }
  function startLine() {
    return hasLaunched() ? "Your first stories arrive Monday " + fmtDate(nextMonday()) + "."
      : "Everyone starts together on " + launchText() + ". Your first stories arrive by email that week.";
  }
  function commas(n) { return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ","); }
  function contactNode() {
    var c = cfg().contactEmail;
    return c ? link(c, "mailto:" + c) : document.createTextNode("[contact]");
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
  function storiesFor(minutes, st) { return Math.max(1, Math.round(minutes * (cfg().wpm || 75) / st.mean)); }

  // Draw a screen once index.json is in; otherwise show the same message app.js shows.
  function withIndex(t, draw) {
    getIndex().then(function (idx) { if (t === token) draw(idx, stats(idx)); })
      .catch(function () { if (t === token) show([el("p", { class: "notice", text: "Could not load the stories. Please check your connection and reload." })]); });
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
      S.sdk = { auth: auth, db: db, a: a, f: f, provider: new a.GoogleAuthProvider() };
      if (emu) window.SeptimusSignup._test = { auth: auth, db: db, sdk: { app: m[0], auth: a, firestore: f } };
      var seq = 0;
      a.onAuthStateChanged(auth, function (user) {
        var mine = ++seq;
        S.user = user; S.record = null; S.recordFailed = false; S.settled = !user;
        notify();
        if (!user) return;
        f.getDoc(f.doc(db, "users", user.uid)).then(function (snap) { if (mine === seq) S.record = snap.exists() ? snap.data() : null; })
          .catch(function () { if (mine === seq) S.recordFailed = true; })
          .then(function () { if (mine === seq) { S.settled = true; notify(); } });
      });
      return S.sdk;
    });
    sdkP.catch(function () { sdkP = null; });   // let the next visit try again
    return sdkP;
  }
  function notify() { if (S.listener) S.listener(); }

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

  function landing(t) {
    loadSdk();
    withIndex(t, function (idx, st) {
      var c = cfg(), total = Math.round(st.stories / 100) * 100;
      var learnedEl = el("div", { "class": "su-progress-title" });
      var fill = el("div", { "class": "su-fill" });
      var joinedEl = el("div", { "class": "su-muted su-small", hidden: true });   // stays hidden until progress/summary exists
      function setProgress(learned) {
        learnedEl.textContent = learned + " of about " + commas(total) + " stories learned";
        fill.style.width = Math.min(100, 100 * learned / Math.max(1, total)) + "%";
      }
      setProgress(0);
      loadSdk().then(function (sdk) { return sdk.f.getDoc(sdk.f.doc(sdk.db, "progress", "summary")); }).then(function (snap) {
        if (t !== token || !snap.exists()) return;
        var d = snap.data();
        if (typeof d.learned === "number") setProgress(d.learned);
        if (typeof d.joined === "number") { joinedEl.textContent = d.joined + " " + (d.joined === 1 ? "person has" : "people have") + " joined"; joinedEl.hidden = false; }
      }).catch(function () {});   // no document yet, or no network: the card just shows 0 and no join count

      var area = el("div", { "class": "su-signin" });
      var errorLine = "";
      function drawArea() {
        var kids = [];
        if (afterYahrzeit()) { area.textContent = ""; return; }
        if (S.user && S.record) {
          var m = S.record.minutesPerWeek;
          kids.push(el("p", { "class": "su-signedin" }, [m === 0 ? "Signed in. Your stories are stopped." : "Signed in, " + m + " min a week", m === 0 ? null : " ", link("Change", "#/join")]));
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
        if (S.recordFailed && !errorLine) kids.push(el("p", { "class": "su-error", role: "alert", text: "Could not sign in. Check your connection and try again." }));
        if (!(S.user && S.record)) kids.push(el("p", { "class": "su-muted su-small su-center" }, ["No Google account? Email ", contactNode()]));
        area.textContent = "";
        kids.forEach(function (k) { area.appendChild(k); });
      }
      S.listener = function () {
        if (t !== token) return;
        if (S.user && S.settled && !S.record && !S.recordFailed) { location.hash = "#/join"; return; }   // signed in but never answered the question
        drawArea();
      };
      sdkP && sdkP.catch(function () { errorLine = "Could not sign in. Check your connection and try again."; drawArea(); });

      show([
        el("h1", { text: "Learn every story in the Talmud, together" }),
        el("p", { "class": "su-dedication", text: "In memory of Joe Septimus." }),
        el("p", { "class": "su-muted", text: afterYahrzeit() ? "Thank you to everyone who learned."
          : "A few minutes a week, from " + launchText() + " until his yahrzeit, " + (c.yahrzeitLabel || "8 Elul") + "." }),
        el("div", { "class": "su-progress" }, [learnedEl, el("div", { "class": "su-track" }, [fill]), joinedEl]),
        area,
        el("p", { "class": "su-center su-small" }, [link("Your data", "#/your-data")]),
        el("p", { "class": "su-links" }, [link("About Joe Septimus", "#/about"), " · ", link("Browse the stories", "#/browse"), " · ", link("How the stories were chosen", "#/how")])
      ]);
      S.listener();
    });
  }

  // ---- minutes question -----------------------------------------------------------------------
  var PRESETS = [5, 10, 15, 30];
  function join(t) {
    loadSdk();
    var built = false;
    S.listener = function () {
      if (t !== token) return;
      if (!S.settled) return;
      if (!S.user || S.recordFailed) { location.hash = "#/"; return; }
      if (built) return;
      built = true;
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
      // The only place a users record is ever written. Join creates it; Save changes the minutes and nothing else.
      var write = has ? f.updateDoc(ref, { minutesPerWeek: m })
        : f.setDoc(ref, { createdAt: f.serverTimestamp(), minutesPerWeek: m, src: savedSrc(), deleteRequested: false });
      write.then(function () {
        S.record = Object.assign({}, S.record || {}, { minutesPerWeek: m });
        location.hash = "#/joined";
      }).catch(function () {
        errLine.textContent = "Could not save. Check your connection and try again."; errLine.hidden = false;
        joinBtn.disabled = false; joinBtn.textContent = has ? "Save" : "Join";
      });
    };
    var switchBtn = el("button", { type: "button", "class": "su-linkbtn", text: "Not you? Switch account" });
    switchBtn.onclick = function () { S.sdk.a.signOut(S.sdk.auth).then(function () { location.hash = "#/"; }, function () { location.hash = "#/"; }); };

    show([
      el("p", { "class": "su-muted su-small" }, ["Signed in as " + (S.user.email || ""), " ", switchBtn]),
      el("h1", { text: "How many minutes a week will you learn?" }),
      el("p", { "class": "su-muted", text: "From " + launchText() + " until " + (cfg().yahrzeitLabel || "8 Elul") + ". You can change this any time." }),
      group, estimate, joinBtn, errLine,
      el("p", { "class": "su-muted su-small su-center", text: startLine() })
    ]);
    refresh(false);
  }

  // ---- you're in ------------------------------------------------------------------------------
  function joined(t) {
    loadSdk();
    var drawn = false;
    S.listener = function () {
      if (t !== token || !S.settled || drawn) return;
      if (!S.user || !S.record) { location.hash = "#/"; return; }
      drawn = true;
      var m = S.record.minutesPerWeek;
      show([
        el("h1", { text: "You're in" }),
        el("p", { text: m + (m === 1 ? " minute" : " minutes") + " a week." }),
        el("p", { "class": "su-muted", text: startLine() }),
        el("div", { "class": "su-actions" }, [link("Browse the stories", "#/browse", "su-btn"), link("Change", "#/join", "su-btn su-btn-outline")])
      ]);
    };
    S.listener();
  }

  // ---- small text pages -----------------------------------------------------------------------
  function how(t) {
    withIndex(t, function (idx, st) {
      var names = idx.tractates.filter(function (x) { return x.reviewed; }).map(function (x) { return x.name; });
      var list = names.length > 1 ? names.slice(0, -1).join(", ") + " and " + names[names.length - 1] : names.join("");
      var listLine = idx.list_version && idx.published_at ? "Story list v" + idx.list_version + ", dated " + idx.published_at + "."
        : "Story list: " + commas(st.stories) + " stories in " + st.tractates + " tractates.";
      show([
        el("h1", { text: "How the stories were chosen" }),
        el("p", { text: "A story here is a passage of the Babylonian Talmud that tells of something that happened: people, an event, and how it turned out." }),
        el("p", { text: "The stories were found by software. In " + list + " they were then checked by Prof. Jeff Rubenstein of New York University. The other tractates are marked “not yet reviewed”: some passages there may not be stories, or may start or end in the wrong place." }),
        el("p", { text: listLine }),
        back()
      ]);
    });
  }
  function yourData() {
    show([
      el("h1", { text: "Your data" }),
      el("ul", { "class": "su-list" }, [
        el("li", { text: "What we store: your Google name and email address, the link you joined from, how many minutes a week you chose, and which stories you were given and when you marked them learned." }),
        el("li", { text: "Who sees it: Simon Brief, who runs the site. The Septimus family sees how many people joined from each community, and names. Nobody sees your reading record but you." }),
        el("li", { text: "Nothing about you is shown publicly." }),
        el("li", {}, ["Stopping: you can stop your stories or delete your data at any time. Until those buttons are on the site, email ", contactNode(), "."]),
        el("li", { text: "Everyone's personal data is deleted six months after the yahrzeit." }),
        el("li", { text: "You must be 13 or older to join." })
      ]),
      back()
    ]);
  }
  function about() {
    show([
      el("h1", { text: "About Joe Septimus" }),
      el("p", { "class": "notice", text: "[Placeholder: a few paragraphs about Joe Septimus, to be written by his family.]" }),
      back()
    ]);
  }

  // ---- routing --------------------------------------------------------------------------------
  var SCREENS = { "": landing, join: join, joined: joined, how: how, "your-data": yourData, about: about };
  function route(parts) {
    if (!srcDone) { srcDone = true; rememberSrc(); }
    var t = ++token;
    S.listener = null;
    var name = parts[1] || "";
    if (!Object.prototype.hasOwnProperty.call(SCREENS, name)) return false;
    SCREENS[name](t);
    return true;
  }

  // TODO(signup): after the Jeff-responses branch merges, change the two "#/" links in app.js ("All tractates"
  // crumb, "Home" on story-not-found) to "#/browse" and delete this listener. Until then "#/" there means the list.
  app.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest('a[href="#/"]');
    if (a && app.contains(a) && !a.classList.contains("su-keep")) { e.preventDefault(); location.hash = "#/browse"; }
  });

  window.SeptimusSignup = { route: route };
})();
