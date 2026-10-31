/* Yes Bro My Paper — picker + reader. Zero server AI. Picks in localStorage and ?t= URL. */
(function () {
  "use strict";

  var LS_KEY = "yesbro_mypaper_topics";
  var catalog = null;
  var paperCache = {};
  var picks = [];

  function $(id) { return document.getElementById(id); }

  function parseTopicsFromUrl() {
    try {
      var q = new URLSearchParams(location.search).get("t") || "";
      if (!q) return null;
      return q.split(",").map(function (s) { return s.trim(); }).filter(Boolean);
    } catch (e) {
      return null;
    }
  }

  function loadPicks() {
    var fromUrl = parseTopicsFromUrl();
    if (fromUrl && fromUrl.length) {
      picks = unique(fromUrl);
      saveLocal();
      return;
    }
    try {
      var raw = localStorage.getItem(LS_KEY);
      picks = raw ? unique(JSON.parse(raw)) : [];
    } catch (e) {
      picks = [];
    }
  }

  function unique(arr) {
    var seen = {}, out = [];
    arr.forEach(function (t) {
      if (!t || seen[t]) return;
      seen[t] = 1;
      out.push(t);
    });
    return out;
  }

  function saveLocal() {
    try { localStorage.setItem(LS_KEY, JSON.stringify(picks)); } catch (e) {}
  }

  function writeUrl() {
    var u = new URL(location.href);
    if (picks.length) u.searchParams.set("t", picks.join(","));
    else u.searchParams.delete("t");
    history.replaceState(null, "", u.pathname + u.search + u.hash);
  }

  function setPicks(next) {
    picks = unique(next);
    saveLocal();
    writeUrl();
    renderPickerState();
    syncCloudPicks();
  }

  function toggleTopic(id) {
    if (picks.indexOf(id) >= 0) setPicks(picks.filter(function (x) { return x !== id; }));
    else setPicks(picks.concat([id]));
  }

  function paperKeyOf(topicId) {
    var i = topicId.indexOf(".");
    return i < 0 ? topicId : topicId.slice(0, i);
  }

  function topicSuffix(topicId) {
    var i = topicId.indexOf(".");
    return i < 0 ? "" : topicId.slice(i + 1);
  }

  function fetchJson(url) {
    return fetch(url, { credentials: "omit", cache: "no-cache" }).then(function (r) {
      if (!r.ok) throw new Error("fetch " + r.status);
      return r.json();
    });
  }

  function loadCatalog() {
    return fetchJson("../data/catalog.json").then(function (c) {
      catalog = c;
      return c;
    });
  }

  function loadPaper(key) {
    if (paperCache[key]) return Promise.resolve(paperCache[key]);
    return fetchJson("../data/" + key + "/latest.json").then(function (p) {
      paperCache[key] = p;
      return p;
    });
  }

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function renderPicker() {
    var root = $("picker-grid");
    if (!catalog) {
      root.innerHTML = "<p class=\"empty\">Catalog is still warming up.</p>";
      return;
    }
    var html = "";
    catalog.papers.forEach(function (paper) {
      if (!paper.topics || !paper.topics.length) return;
      html += "<section class=\"paper-block\" data-paper=\"" + esc(paper.key) + "\">";
      html += "<div class=\"paper-head\"><h2>" + esc(paper.label) + "</h2>";
      html += "<a class=\"paper-link\" href=\"" + esc(paper.url) + "\">Open paper</a></div>";
      html += "<div class=\"topic-grid\">";
      paper.topics.forEach(function (t) {
        var on = picks.indexOf(t.id) >= 0;
        html += "<button type=\"button\" class=\"topic" + (on ? " on" : "") + "\" data-id=\"" + esc(t.id) + "\" aria-pressed=\"" + (on ? "true" : "false") + "\">";
        html += "<span class=\"t-name\">" + esc(t.name) + "</span>";
        html += "<span class=\"t-meta\">" + esc(String(t.count)) + (t.kind === "section" ? " stories" : "") + "</span>";
        html += "<span class=\"t-btn\" aria-hidden=\"true\">" + (on ? "✓" : "+") + "</span>";
        html += "</button>";
      });
      html += "</div></section>";
    });
    root.innerHTML = html || "<p class=\"empty\">No topics yet for today.</p>";
    root.querySelectorAll(".topic").forEach(function (btn) {
      btn.addEventListener("click", function () { toggleTopic(btn.getAttribute("data-id")); });
    });
    var dateEl = $("catalog-date");
    if (dateEl && catalog.date) dateEl.textContent = catalog.date;
    renderPickerState();
  }

  function renderPickerState() {
    var n = picks.length;
    var sticky = $("sticky-go");
    var countEl = $("pick-count");
    if (countEl) countEl.textContent = String(n);
    if (sticky) {
      sticky.disabled = n === 0;
      sticky.textContent = n ? ("My Paper (" + n + ")") : "My Paper";
    }
    document.querySelectorAll(".topic").forEach(function (btn) {
      var id = btn.getAttribute("data-id");
      var on = picks.indexOf(id) >= 0;
      btn.classList.toggle("on", on);
      btn.setAttribute("aria-pressed", on ? "true" : "false");
      var mark = btn.querySelector(".t-btn");
      if (mark) mark.textContent = on ? "✓" : "+";
    });
    var clear = $("clear-picks");
    if (clear) clear.hidden = n === 0;
  }

  function showView(name) {
    $("view-picker").hidden = name !== "picker";
    $("view-reader").hidden = name !== "reader";
    window.scrollTo(0, 0);
    if (name === "reader") document.body.classList.add("reading");
    else document.body.classList.remove("reading");
  }

  function fieldworkAd() {
    return (
      "<aside class=\"housead\" id=\"fieldwork\">" +
      "<p class=\"ad-kicker\">Advertisement</p>" +
      "<p class=\"ad-brand\">Fieldwork</p>" +
      "<h4>Your neighbourhood is the syllabus.</h4>" +
      "<p>FIELDWORK by Earth5R takes students into their own streets to study real problems with the community, with a mentor checking the work. Before the next scroll, walk the block.</p>" +
      "<a class=\"ad-cta\" href=\"https://earth5r.org/fieldwork/\" target=\"_blank\" rel=\"noopener\">Learn more at earth5r.org</a>" +
      "</aside>"
    );
  }

  function storyCard(s, lead) {
    var img = s.image
      ? "<figure><img src=\"" + esc(s.image) + "\" alt=\"\" loading=\"lazy\" decoding=\"async\"></figure>"
      : "";
    return (
      "<article class=\"story" + (lead ? " lead" : "") + "\">" +
      img +
      "<h3><a href=\"" + esc(s.url) + "\" target=\"_blank\" rel=\"noopener\">" + esc(s.title) + "</a></h3>" +
      (s.source ? "<p class=\"byline\">" + esc(s.source) + "</p>" : "") +
      (s.summary ? "<p class=\"sum\">" + esc(s.summary) + "</p>" : "") +
      "<a class=\"more\" href=\"" + esc(s.url) + "\" target=\"_blank\" rel=\"noopener\">Read the original</a>" +
      "</article>"
    );
  }

  function renderJobs(items) {
    return items.map(function (j) {
      return (
        "<article class=\"meta-card\">" +
        "<h3><a href=\"" + esc(j.url) + "\" target=\"_blank\" rel=\"noopener\">" + esc(j.title) + "</a></h3>" +
        "<p class=\"byline\">" + esc([j.org, j.location || j.region].filter(Boolean).join(" · ")) + "</p>" +
        "</article>"
      );
    }).join("");
  }

  function renderEvents(items) {
    return items.map(function (e) {
      var when = [e.start, e.time].filter(Boolean).join(" · ");
      var where = [e.city, e.mode].filter(Boolean).join(" · ");
      return (
        "<article class=\"meta-card\">" +
        "<h3>" + (e.url ? "<a href=\"" + esc(e.url) + "\" target=\"_blank\" rel=\"noopener\">" + esc(e.name) + "</a>" : esc(e.name)) + "</h3>" +
        "<p class=\"byline\">" + esc([when, where].filter(Boolean).join(" · ")) + "</p>" +
        (e.line ? "<p class=\"sum\">" + esc(e.line) + "</p>" : "") +
        "</article>"
      );
    }).join("");
  }

  function renderResearch(items) {
    return items.map(function (r) {
      return (
        "<article class=\"meta-card\">" +
        "<h3><a href=\"" + esc(r.url) + "\" target=\"_blank\" rel=\"noopener\">" + esc(r.title) + "</a></h3>" +
        "<p class=\"byline\">" + esc([r.source, r.kind].filter(Boolean).join(" · ")) + "</p>" +
        (r.summary ? "<p class=\"sum\">" + esc(r.summary) + "</p>" : "") +
        "</article>"
      );
    }).join("");
  }

  function renderTalks(items) {
    return items.map(function (t) {
      return (
        "<article class=\"meta-card\">" +
        "<h3><a href=\"" + esc(t.url) + "\" target=\"_blank\" rel=\"noopener\">" + esc(t.title) + "</a></h3>" +
        "<p class=\"byline\">" + esc([t.channel, t.duration].filter(Boolean).join(" · ")) + "</p>" +
        (t.note ? "<p class=\"sum\">" + esc(t.note) + "</p>" : "") +
        "</article>"
      );
    }).join("");
  }

  function buildSectionHtml(title, kicker, body) {
    if (!body) return "";
    return (
      "<section class=\"sec\">" +
      "<div class=\"sec-head\"><h2>" + esc(title) + "</h2><span>" + esc(kicker) + "</span></div>" +
      "<div class=\"sec-body\">" + body + "</div></section>"
    );
  }

  function openReader() {
    if (!picks.length) return;
    showView("reader");
    var mount = $("reader-mount");
    mount.innerHTML = "<p class=\"empty\">Setting the type…</p>";
    var keys = unique(picks.map(paperKeyOf));
    Promise.all(keys.map(loadPaper)).then(function () {
      var html = "";
      var adAt = 2;
      var secCount = 0;
      picks.forEach(function (tid) {
        var key = paperKeyOf(tid);
        var suf = topicSuffix(tid);
        var paper = paperCache[key];
        if (!paper) return;
        var kicker = paper.label;
        var body = "";
        var title = suf;
        if (suf === "jobs") {
          title = "Jobs";
          body = renderJobs(paper.jobs || []);
        } else if (suf === "events") {
          title = "Events and Conferences";
          body = renderEvents(paper.events || []);
        } else if (suf === "research") {
          title = "Research and Development";
          body = renderResearch(paper.research || []);
        } else if (suf === "talks") {
          title = "Talks";
          body = renderTalks(paper.talks || []);
        } else {
          var sec = (paper.sections || []).find(function (s) { return s.id === suf; });
          if (!sec || !sec.stories || !sec.stories.length) return;
          title = sec.name;
          body = sec.stories.map(function (s, i) { return storyCard(s, i === 0); }).join("");
        }
        if (!body) return;
        html += buildSectionHtml(title, kicker, body);
        secCount += 1;
        if (secCount === adAt) html += fieldworkAd();
      });
      if (!html) html = "<p class=\"empty\">Those topics are empty today. Add another from the picker.</p>";
      var dateLabel = (catalog && catalog.date) || "";
      $("reader-date").textContent = dateLabel;
      mount.innerHTML = html;
    }).catch(function () {
      mount.innerHTML = "<p class=\"empty\">Could not load today's sections. Try again in a minute.</p>";
    });
  }

  /* ---- Phase 2 auth (inert until firebase-config enabled) ---- */
  var authUser = null;

  function firebaseReady() {
    var c = window.YESBRO_FIREBASE;
    return !!(c && c.enabled && c.apiKey && c.projectId && window.firebase);
  }

  function setupAuthUi() {
    var wrap = $("auth-wrap");
    if (!wrap) return;
    if (!firebaseReady()) {
      wrap.hidden = true;
      return;
    }
    wrap.hidden = false;
    try {
      if (!firebase.apps.length) firebase.initializeApp(window.YESBRO_FIREBASE);
      var auth = firebase.auth();
      auth.onAuthStateChanged(function (user) {
        authUser = user;
        renderAuth();
        if (user) syncCloudPicks();
      });
    } catch (e) {
      wrap.hidden = true;
    }
  }

  function renderAuth() {
    var status = $("auth-status");
    var btnIn = $("auth-signin");
    var btnOut = $("auth-signout");
    if (!status) return;
    if (authUser) {
      status.textContent = "Signed in as " + (authUser.email || authUser.displayName || "you");
      if (btnIn) btnIn.hidden = true;
      if (btnOut) btnOut.hidden = false;
    } else {
      status.textContent = "Sign in with Google to save your paper across devices.";
      if (btnIn) btnIn.hidden = false;
      if (btnOut) btnOut.hidden = true;
    }
  }

  function syncCloudPicks() {
    if (!firebaseReady() || !authUser) return;
    try {
      var db = firebase.firestore();
      var ref = db.collection("users").doc(authUser.uid);
      ref.set({
        email: authUser.email || "",
        name: authUser.displayName || "",
        picks: picks,
        last_seen: firebase.firestore.FieldValue.serverTimestamp()
      }, { merge: true });
    } catch (e) {}
  }

  function pullCloudPicks() {
    if (!firebaseReady() || !authUser) return;
    try {
      firebase.firestore().collection("users").doc(authUser.uid).get().then(function (doc) {
        if (!doc.exists) return;
        var remote = doc.data().picks;
        if (Array.isArray(remote) && remote.length && !picks.length) setPicks(remote);
      });
    } catch (e) {}
  }

  function bind() {
    $("sticky-go").addEventListener("click", function () {
      if (!picks.length) return;
      openReader();
    });
    $("back-picker").addEventListener("click", function () {
      showView("picker");
    });
    $("clear-picks").addEventListener("click", function () {
      setPicks([]);
    });
    var top = $("back-top");
    window.addEventListener("scroll", function () {
      if (!top) return;
      top.classList.toggle("show", window.scrollY > 480);
    });
    top.addEventListener("click", function () { window.scrollTo({ top: 0, behavior: "smooth" }); });

    var btnIn = $("auth-signin");
    var btnOut = $("auth-signout");
    if (btnIn) btnIn.addEventListener("click", function () {
      if (!firebaseReady()) return;
      var provider = new firebase.auth.GoogleAuthProvider();
      firebase.auth().signInWithPopup(provider).then(function () { pullCloudPicks(); }).catch(function () {});
    });
    if (btnOut) btnOut.addEventListener("click", function () {
      if (!firebaseReady()) return;
      firebase.auth().signOut();
    });
  }

  loadPicks();
  bind();
  setupAuthUi();
  loadCatalog().then(function () {
    renderPicker();
    if (picks.length && parseTopicsFromUrl()) {
      /* Shared URL lands straight in the reader */
      openReader();
    }
  }).catch(function () {
    $("picker-grid").innerHTML = "<p class=\"empty\">Catalog missing. The night build may still be running.</p>";
  });
})();
