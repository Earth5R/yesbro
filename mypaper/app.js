/* Yes Bro My Paper — picker + reader. Zero server AI.
   Picks in localStorage and ?t= URL. Whole-paper picks use key.* (e.g. ux.*).
   Google sign-in syncs picks across devices when sign-in is enabled. */
(function () {
  "use strict";

  var LS_KEY = "yesbro_mypaper_topics";
  var catalog = null;
  var paperCache = {};
  var picks = [];
  var authUser = null;
  var authReady = false;
  var cloudHydrated = false;
  var firebaseFailed = false;

  function $(id) { return document.getElementById(id); }

  function unique(arr) {
    var seen = {}, out = [];
    (arr || []).forEach(function (t) {
      if (!t || seen[t]) return;
      seen[t] = 1;
      out.push(t);
    });
    return out;
  }

  function isWhole(id) {
    return typeof id === "string" && /\.\*$/.test(id);
  }

  function paperKeyOf(topicId) {
    var i = String(topicId || "").indexOf(".");
    return i < 0 ? topicId : topicId.slice(0, i);
  }

  function topicSuffix(topicId) {
    var i = String(topicId || "").indexOf(".");
    return i < 0 ? "" : topicId.slice(i + 1);
  }

  function wholeId(key) { return key + ".*"; }

  function hasWhole(key) {
    return picks.indexOf(wholeId(key)) >= 0;
  }

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

  function saveLocal() {
    try { localStorage.setItem(LS_KEY, JSON.stringify(picks)); } catch (e) {}
  }

  function writeUrl() {
    try {
      var u = new URL(location.href);
      if (picks.length) {
        u.searchParams.set("t", picks.join(","));
        u.searchParams.delete("mine");
      } else {
        u.searchParams.delete("t");
      }
      history.replaceState(null, "", u.pathname + u.search + u.hash);
    } catch (e) {}
  }

  function setPicks(next, opts) {
    picks = unique(next);
    saveLocal();
    writeUrl();
    renderPickerState();
    if (!(opts && opts.skipCloud)) syncCloudPicks();
  }

  function addWholePaper(key) {
    var next = picks.filter(function (t) { return paperKeyOf(t) !== key; });
    next.push(wholeId(key));
    setPicks(next);
  }

  function removeWholePaper(key) {
    setPicks(picks.filter(function (t) { return t !== wholeId(key); }));
  }

  function toggleWholePaper(key) {
    if (hasWhole(key)) removeWholePaper(key);
    else addWholePaper(key);
  }

  function toggleTopic(id) {
    var key = paperKeyOf(id);
    if (hasWhole(key)) {
      /* Switching from whole paper to a la carte: drop .* and keep other sections except this one if removing */
      var paper = (catalog.papers || []).find(function (p) { return p.key === key; });
      var all = (paper && paper.topics ? paper.topics.map(function (t) { return t.id; }) : []);
      var next = picks.filter(function (t) { return paperKeyOf(t) !== key; });
      all.forEach(function (tid) {
        if (tid !== id) next.push(tid);
      });
      setPicks(next);
      return;
    }
    if (picks.indexOf(id) >= 0) setPicks(picks.filter(function (x) { return x !== id; }));
    else setPicks(picks.concat([id]));
  }

  function mergePicks(a, b) {
    return unique([].concat(a || [], b || []));
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

  function paperIcon(key) {
    try { return (window.YESBRO_ICON && window.YESBRO_ICON(key)) || ""; } catch (e) { return ""; }
  }

  function topicIcon(topic) {
    var kind = (topic && topic.kind) || "section";
    if (kind === "events" || kind === "research" || kind === "jobs" || kind === "talks") {
      return paperIcon(kind);
    }
    return paperIcon("section");
  }

  function wantsMine() {
    try {
      var u = new URL(location.href);
      if (u.searchParams.has("mine")) return true;
      return false;
    } catch (e) { return false; }
  }


  function pickCountLabel() {
    var wholes = picks.filter(isWhole).length;
    var parts = picks.filter(function (t) { return !isWhole(t); }).length;
    if (wholes && parts) return wholes + " papers, " + parts + " sections";
    if (wholes) return wholes === 1 ? "1 paper" : wholes + " papers";
    if (parts) return parts === 1 ? "1 section" : parts + " sections";
    return "My Paper";
  }

  function stickyLabel() {
    if (!picks.length) return "My Paper";
    return "My Paper (" + picks.length + ")";
  }

  /* ---- Picker ---- */
  function renderPicker() {
    var root = $("picker-grid");
    if (!catalog) {
      root.innerHTML = "<p class=\"empty\">Catalog is still warming up.</p>";
      return;
    }
    var html = "";
    (catalog.papers || []).forEach(function (paper) {
      var on = hasWhole(paper.key);
      var topicCount = (paper.topics || []).length;
      html += "<section class=\"paper-block\" data-paper=\"" + esc(paper.key) + "\">";
      html += "<div class=\"paper-card" + (on ? " on" : "") + "\">";
      html += "<div class=\"paper-card-main\">";
      html += "<div class=\"paper-card-left\">";
      html += "<span class=\"paper-ico\">" + paperIcon(paper.key) + "</span>";
      html += "<div class=\"paper-card-text\"><h2>" + esc(paper.label) + "</h2>";
      html += "<p class=\"paper-card-meta\">Yes Bro " + esc(paper.label);
      if (topicCount) html += " · " + topicCount + " topics today";
      html += "</p></div></div>";
      html += "<button type=\"button\" class=\"whole-btn" + (on ? " on" : "") + "\" data-whole=\"" + esc(paper.key) + "\" aria-pressed=\"" + (on ? "true" : "false") + "\">";
      html += on ? "✓ Whole paper" : "+ Add whole paper";
      html += "</button></div>";
      html += "<a class=\"paper-link\" href=\"" + esc(paper.url) + "\">Open full paper</a>";
      html += "</div>";

      if (paper.topics && paper.topics.length) {
        html += "<details class=\"section-pick\"" + (on ? "" : "") + ">";
        html += "<summary>Or pick sections</summary>";
        html += "<div class=\"topic-grid\">";
        paper.topics.forEach(function (t) {
          var ton = on || picks.indexOf(t.id) >= 0;
          html += "<button type=\"button\" class=\"topic" + (ton ? " on" : "") + (on ? " locked" : "") + "\" data-id=\"" + esc(t.id) + "\" aria-pressed=\"" + (ton ? "true" : "false") + "\">";
          html += "<span class=\"t-row\"><span class=\"t-ico\">" + topicIcon(t) + "</span>";
          html += "<span class=\"t-name\">" + esc(t.name) + "</span></span>";
          html += "<span class=\"t-meta\">" + esc(String(t.count)) + (t.kind === "section" ? " stories" : "") + "</span>";
          html += "<span class=\"t-btn\" aria-hidden=\"true\">" + (ton ? "✓" : "+") + "</span>";
          html += "</button>";
        });
        html += "</div></details>";
      }
      html += "</section>";
    });
    root.innerHTML = html || "<p class=\"empty\">No papers yet for today.</p>";
    root.querySelectorAll(".whole-btn").forEach(function (btn) {
      btn.addEventListener("click", function () { toggleWholePaper(btn.getAttribute("data-whole")); });
    });
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
    var summary = $("pick-summary");
    if (countEl) countEl.textContent = String(n);
    if (summary) summary.textContent = n ? pickCountLabel() : "Nothing picked yet";
    if (sticky) {
      sticky.disabled = n === 0;
      sticky.textContent = stickyLabel();
    }
    document.querySelectorAll(".paper-block").forEach(function (block) {
      var key = block.getAttribute("data-paper");
      var on = hasWhole(key);
      var card = block.querySelector(".paper-card");
      var whole = block.querySelector(".whole-btn");
      if (card) card.classList.toggle("on", on);
      if (whole) {
        whole.classList.toggle("on", on);
        whole.setAttribute("aria-pressed", on ? "true" : "false");
        whole.textContent = on ? "✓ Whole paper" : "+ Add whole paper";
      }
      block.querySelectorAll(".topic").forEach(function (btn) {
        var id = btn.getAttribute("data-id");
        var ton = on || picks.indexOf(id) >= 0;
        btn.classList.toggle("on", ton);
        btn.classList.toggle("locked", on);
        btn.setAttribute("aria-pressed", ton ? "true" : "false");
        var mark = btn.querySelector(".t-btn");
        if (mark) mark.textContent = ton ? "✓" : "+";
      });
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
    return (items || []).map(function (j) {
      return (
        "<article class=\"meta-card\">" +
        "<h3><a href=\"" + esc(j.url) + "\" target=\"_blank\" rel=\"noopener\">" + esc(j.title) + "</a></h3>" +
        "<p class=\"byline\">" + esc([j.org, j.location || j.region].filter(Boolean).join(" · ")) + "</p>" +
        "</article>"
      );
    }).join("");
  }

  function renderEvents(items) {
    return (items || []).map(function (e) {
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
    return (items || []).map(function (r) {
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
    return (items || []).map(function (t) {
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
      "<div class=\"sec-head\"><h2>" + esc(title) + "</h2>" +
      (kicker ? "<span>" + esc(kicker) + "</span>" : "") +
      "</div><div class=\"sec-body\">" + body + "</div></section>"
    );
  }

  function renderWholePaper(paper) {
    var html = "";
    html += "<div class=\"paper-banner\"><h2 class=\"paper-banner-title\">Yes Bro " + esc(paper.label) + "</h2>";
    html += "<p class=\"paper-banner-meta\">Whole paper · " + esc(paper.date || "") + "</p></div>";
    (paper.sections || []).forEach(function (sec, idx) {
      if (!sec.stories || !sec.stories.length) return;
      var body = sec.stories.map(function (s, i) { return storyCard(s, i === 0); }).join("");
      html += buildSectionHtml(sec.name, paper.label, body);
      if (idx === 1) html += fieldworkAd();
    });
    if ((paper.events || []).length) html += buildSectionHtml("Events and Conferences", paper.label, renderEvents(paper.events));
    if ((paper.research || []).length) html += buildSectionHtml("Research and Development", paper.label, renderResearch(paper.research));
    if ((paper.talks || []).length) html += buildSectionHtml("Talks", paper.label, renderTalks(paper.talks));
    if ((paper.jobs || []).length) html += buildSectionHtml("Jobs", paper.label, renderJobs(paper.jobs));
    return html;
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
      var seenWhole = {};

      picks.forEach(function (tid) {
        var key = paperKeyOf(tid);
        var paper = paperCache[key];
        if (!paper) return;

        if (isWhole(tid)) {
          if (seenWhole[key]) return;
          seenWhole[key] = 1;
          html += renderWholePaper(paper);
          return;
        }
        if (hasWhole(key) || seenWhole[key]) return;

        var suf = topicSuffix(tid);
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
      if ($("reader-date")) $("reader-date").textContent = dateLabel;
      if ($("pick-summary-reader")) $("pick-summary-reader").textContent = pickCountLabel();
      mount.innerHTML = html;
    }).catch(function () {
      mount.innerHTML = "<p class=\"empty\">Could not load today's sections. Try again in a minute.</p>";
    });
  }

  /* ---- Auth / Firestore ---- */
  function configEnabled() {
    var c = window.YESBRO_FIREBASE;
    return !!(c && c.enabled && c.apiKey && c.projectId);
  }

  function firebaseReady() {
    return configEnabled() && !!window.firebase && !firebaseFailed;
  }

  function showAuthWrap(show) {
    var wrap = $("auth-wrap");
    if (!wrap) return;
    wrap.hidden = !show;
  }

  function renderAuth() {
    var status = $("auth-status");
    var btnIn = $("auth-signin");
    var btnOut = $("auth-signout");
    var privacy = $("auth-privacy");
    if (!status) return;
    if (firebaseFailed) {
      status.textContent = "Sign-in is resting. Your picks still save on this device.";
      if (btnIn) btnIn.hidden = true;
      if (btnOut) btnOut.hidden = true;
      if (privacy) privacy.hidden = false;
      return;
    }
    if (authUser) {
      var who = authUser.displayName || authUser.email || "you";
      status.innerHTML = "Signed in as <b>" + esc(who) + "</b>";
      if (btnIn) btnIn.hidden = true;
      if (btnOut) btnOut.hidden = false;
      if (privacy) privacy.hidden = false;
    } else {
      status.textContent = "Sign in with Google to save your paper across devices.";
      if (btnIn) btnIn.hidden = false;
      if (btnOut) btnOut.hidden = true;
      if (privacy) privacy.hidden = false;
    }
  }

  function userPayload(extra) {
    var photo = "";
    try { photo = (authUser.photoURL || ""); } catch (e) {}
    var base = {
      uid: authUser.uid,
      email: authUser.email || "",
      name: authUser.displayName || "",
      photo: photo,
      picks: picks,
      last_seen: firebase.firestore.FieldValue.serverTimestamp()
    };
    if (extra) {
      Object.keys(extra).forEach(function (k) { base[k] = extra[k]; });
    }
    return base;
  }

  function syncCloudPicks() {
    if (!firebaseReady() || !authUser || !authReady) return;
    try {
      firebase.firestore().collection("users").doc(authUser.uid)
        .set(userPayload(), { merge: true })
        .catch(function () { /* localStorage still holds picks */ });
    } catch (e) {}
  }


  function maybeOpenMine() {
    if (!wantsMine()) return;
    if (!picks.length) return;
    openReader();
  }

  function hydrateFromCloud(user) {
    if (!firebaseReady() || !user) return;
    try {
      var ref = firebase.firestore().collection("users").doc(user.uid);
      ref.get().then(function (doc) {
        var local = picks.slice();
        if (!doc.exists) {
          ref.set(userPayload({
            created: firebase.firestore.FieldValue.serverTimestamp()
          }), { merge: true }).catch(function () {});
          cloudHydrated = true;
          maybeOpenMine();
          return;
        }
        var data = doc.data() || {};
        var remote = Array.isArray(data.picks) ? data.picks : [];
        /* First sign-in / any device: merge local pre-sign-in picks with cloud picks */
        var merged = mergePicks(remote, local);
        if (wantsMine() && remote.length) {
          /* ?mine prefers the saved cloud paper */
          merged = unique(remote);
        }
        if (merged.join("\n") !== picks.join("\n")) {
          setPicks(merged, { skipCloud: true });
          renderPicker();
        }
        ref.set(userPayload(), { merge: true }).catch(function () {});
        cloudHydrated = true;
        maybeOpenMine();
      }).catch(function () {
        /* Firestore failed: keep localStorage picks */
        cloudHydrated = true;
        maybeOpenMine();
      });
    } catch (e) {
      cloudHydrated = true;
    }
  }

  function initFirebaseApp() {
    if (!configEnabled()) {
      showAuthWrap(false);
      return;
    }
    showAuthWrap(true);
    renderAuth();
    if (!window.firebase) {
      /* SDK still loading, or failed. Keep wrap visible with a soft wait, then fallback. */
      var tries = 0;
      var timer = setInterval(function () {
        tries += 1;
        if (window.firebase) {
          clearInterval(timer);
          wireAuth();
        } else if (tries > 40) {
          clearInterval(timer);
          firebaseFailed = true;
          renderAuth();
        }
      }, 250);
      return;
    }
    wireAuth();
  }

  function wireAuth() {
    try {
      if (!firebase.apps.length) firebase.initializeApp(window.YESBRO_FIREBASE);
      authReady = true;
      firebase.auth().onAuthStateChanged(function (user) {
        authUser = user;
        renderAuth();
        if (user) {
          hydrateFromCloud(user);
        } else if (wantsMine() && !window.__YB_MINE_PROMPTED__) {
          window.__YB_MINE_PROMPTED__ = true;
          /* Quiet prompt so Your paper deep-links still work */
          try {
            var provider = new firebase.auth.GoogleAuthProvider();
            provider.setCustomParameters({ prompt: "select_account" });
            firebase.auth().signInWithPopup(provider).catch(function () {});
          } catch (e) {}
        }
      });
    } catch (e) {
      firebaseFailed = true;
      renderAuth();
    }
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
      renderPicker();
    });
    var top = $("back-top");
    window.addEventListener("scroll", function () {
      if (!top) return;
      top.classList.toggle("show", window.scrollY > 480);
    });
    if (top) top.addEventListener("click", function () { window.scrollTo({ top: 0, behavior: "smooth" }); });

    var btnIn = $("auth-signin");
    var btnOut = $("auth-signout");
    if (btnIn) btnIn.addEventListener("click", function () {
      if (!firebaseReady()) {
        renderAuth();
        return;
      }
      try {
        var provider = new firebase.auth.GoogleAuthProvider();
        provider.setCustomParameters({ prompt: "select_account" });
        firebase.auth().signInWithPopup(provider).catch(function () {
          /* Popup blocked or cancelled: picks stay local */
        });
      } catch (e) {
        firebaseFailed = true;
        renderAuth();
      }
    });
    if (btnOut) btnOut.addEventListener("click", function () {
      if (!firebaseReady()) return;
      try { firebase.auth().signOut(); } catch (e) {}
    });
  }

  loadPicks();
  bind();
  initFirebaseApp();
  loadCatalog().then(function () {
    renderPicker();
    if (picks.length && parseTopicsFromUrl()) openReader();
    else if (wantsMine() && picks.length && (!configEnabled() || authUser)) maybeOpenMine();
  }).catch(function () {
    $("picker-grid").innerHTML = "<p class=\"empty\">Catalog missing. The night build may still be running.</p>";
  });
})();
