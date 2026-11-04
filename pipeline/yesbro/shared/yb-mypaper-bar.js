/* Yes Bro shared strip: sign in to build your own newspaper.
   Injected on landing + every field paper. Uses /mypaper/firebase-config.js for Google sign-in.
   Light reading-first chrome. No big colours. */
(function () {
  "use strict";
  if (window.__YB_MYPAPER_BAR__) return;
  window.__YB_MYPAPER_BAR__ = true;

  var MYPAPER = "/mypaper/";
  var MINE = "/mypaper/?mine";
  var SDK = [
    "https://www.gstatic.com/firebasejs/10.14.1/firebase-app-compat.js",
    "https://www.gstatic.com/firebasejs/10.14.1/firebase-auth-compat.js",
    "https://www.gstatic.com/firebasejs/10.14.1/firebase-firestore-compat.js"
  ];

  function cfgOk() {
    var c = window.YESBRO_FIREBASE;
    return !!(c && c.enabled && c.apiKey && c.projectId);
  }

  function injectCss() {
    if (document.getElementById("yb-mp-bar-css")) return;
    var s = document.createElement("style");
    s.id = "yb-mp-bar-css";
    s.textContent = [
      "#yb-mp-bar{position:relative;z-index:40;width:100%;box-sizing:border-box;",
      "background:rgba(243,234,214,.92);border-bottom:1px solid var(--rule-soft,#a8987a);",
      "color:var(--ink,#2e2a24);font-family:\"Old Standard TT\",Georgia,serif;",
      "font-size:12.5px;letter-spacing:.04em;line-height:1.3}",
      "#yb-mp-bar .yb-mp-inner{max-width:1100px;margin:0 auto;padding:6px 14px;",
      "display:flex;align-items:center;justify-content:center;gap:10px 14px;flex-wrap:wrap;",
      "min-height:34px;text-align:center}",
      "#yb-mp-bar .yb-mp-msg{margin:0;color:var(--ink-soft,#4a4238);font-style:italic}",
      "#yb-mp-bar .yb-mp-actions{display:inline-flex;align-items:center;gap:10px;flex-wrap:wrap}",
      "#yb-mp-bar button,#yb-mp-bar a.yb-mp-btn{appearance:none;cursor:pointer;",
      "min-height:28px;padding:0 12px;border:1px solid var(--rule,#3d362d);border-radius:999px;",
      "background:transparent;color:var(--ink,#2e2a24);font:inherit;font-style:normal;",
      "font-size:11.5px;letter-spacing:.1em;text-transform:uppercase;text-decoration:none;",
      "display:inline-flex;align-items:center}",
      "#yb-mp-bar button:hover,#yb-mp-bar a.yb-mp-btn:hover{background:rgba(46,42,36,.06)}",
      "#yb-mp-bar a.yb-mp-link{color:var(--ink,#2e2a24);text-decoration:underline;",
      "text-underline-offset:3px;font-style:normal;letter-spacing:.06em}",
      "#yb-mp-bar a.yb-mp-out{color:var(--ink-faint,#6f6454);font-size:11px;",
      "letter-spacing:.06em;text-decoration:underline;text-underline-offset:3px}",
      "#yb-mp-bar[hidden]{display:none!important}",
      "@media (max-width:640px){",
      "#yb-mp-bar{font-size:12px}",
      "#yb-mp-bar .yb-mp-inner{padding:7px 10px;gap:8px;min-height:0}",
      "#yb-mp-bar .yb-mp-msg{flex:1 1 100%}",
      "#yb-mp-bar button,#yb-mp-bar a.yb-mp-btn{min-height:32px;padding:0 14px}",
      "}"
    ].join("");
    document.head.appendChild(s);
  }

  function ensureBar() {
    var bar = document.getElementById("yb-mp-bar");
    if (bar) return bar;
    bar = document.createElement("div");
    bar.id = "yb-mp-bar";
    bar.setAttribute("role", "region");
    bar.setAttribute("aria-label", "My Paper");
    bar.innerHTML = '<div class="yb-mp-inner"><p class="yb-mp-msg" id="yb-mp-msg"></p>' +
      '<div class="yb-mp-actions" id="yb-mp-actions"></div></div>';
    var body = document.body;
    if (body.firstChild) body.insertBefore(bar, body.firstChild);
    else body.appendChild(bar);
    return bar;
  }

  function renderSignedOut() {
    var msg = document.getElementById("yb-mp-msg");
    var act = document.getElementById("yb-mp-actions");
    if (!msg || !act) return;
    msg.textContent = "Sign in to build your own newspaper";
    act.innerHTML = "";
    var btn = document.createElement("button");
    btn.type = "button";
    btn.id = "yb-mp-signin";
    btn.textContent = "Sign in with Google";
    btn.addEventListener("click", doSignIn);
    act.appendChild(btn);
  }

  function renderSignedIn(user) {
    var msg = document.getElementById("yb-mp-msg");
    var act = document.getElementById("yb-mp-actions");
    if (!msg || !act) return;
    var who = (user && (user.displayName || user.email)) || "";
    msg.textContent = who ? ("Signed in as " + who) : "Signed in";
    act.innerHTML = "";
    var mine = document.createElement("a");
    mine.className = "yb-mp-btn";
    mine.href = MINE;
    mine.textContent = "Your paper";
    act.appendChild(mine);
    var out = document.createElement("a");
    out.href = "#";
    out.className = "yb-mp-out";
    out.id = "yb-mp-signout";
    out.textContent = "Sign out";
    out.addEventListener("click", function (e) {
      e.preventDefault();
      doSignOut();
    });
    act.appendChild(out);
  }

  function doSignIn() {
    if (!window.firebase || !cfgOk()) return;
    try {
      if (!firebase.apps.length) firebase.initializeApp(window.YESBRO_FIREBASE);
      var provider = new firebase.auth.GoogleAuthProvider();
      provider.setCustomParameters({ prompt: "select_account" });
      firebase.auth().signInWithPopup(provider).then(function () {
        location.href = MYPAPER;
      }).catch(function () { /* cancelled or blocked */ });
    } catch (e) {}
  }

  function doSignOut() {
    if (!window.firebase || !cfgOk()) return;
    try {
      firebase.auth().signOut().then(function () { renderSignedOut(); }).catch(function () {});
    } catch (e) {}
  }

  function loadScript(src) {
    return new Promise(function (resolve, reject) {
      var existing = document.querySelector('script[src="' + src + '"]');
      if (existing) {
        if (src.indexOf("firebase") >= 0 && window.firebase) return resolve();
        existing.addEventListener("load", function () { resolve(); });
        existing.addEventListener("error", function () { reject(); });
        /* already loaded */
        if (src.indexOf("firebase-config") >= 0 && window.YESBRO_FIREBASE) return resolve();
        setTimeout(resolve, 0);
        return;
      }
      var s = document.createElement("script");
      s.src = src;
      s.async = true;
      s.onload = function () { resolve(); };
      s.onerror = function () { reject(); };
      document.head.appendChild(s);
    });
  }

  function wireAuth() {
    try {
      if (!firebase.apps.length) firebase.initializeApp(window.YESBRO_FIREBASE);
      firebase.auth().onAuthStateChanged(function (user) {
        if (user) renderSignedIn(user);
        else renderSignedOut();
      });
    } catch (e) {
      renderSignedOut();
    }
  }

  function boot() {
    injectCss();
    ensureBar();
    renderSignedOut();
    loadScript("/mypaper/firebase-config.js")
      .then(function () {
        if (!cfgOk()) return Promise.reject(new Error("disabled"));
        return SDK.reduce(function (p, src) {
          return p.then(function () { return loadScript(src); });
        }, Promise.resolve());
      })
      .then(wireAuth)
      .catch(function () {
        /* Sign-in unavailable: keep strip as a quiet link into My Paper */
        var msg = document.getElementById("yb-mp-msg");
        var act = document.getElementById("yb-mp-actions");
        if (msg) msg.textContent = "Build your own newspaper";
        if (act) {
          act.innerHTML = "";
          var a = document.createElement("a");
          a.className = "yb-mp-btn";
          a.href = MYPAPER;
          a.textContent = "My Paper";
          act.appendChild(a);
        }
      });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
