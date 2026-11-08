/* GitHub Pages serves these Firebase helpers from directories, so
   /__/auth/handler 301s to /__/auth/handler/ (query string kept).
   Firebase Auth uses that page's location, without the query, as the
   Google redirect_uri. The OAuth client for Yes Bro allows
   https://yesbrohq.com/__/auth/handler and rejects the trailing-slash URI
   with Error 400 redirect_uri_mismatch.
   history.replaceState fixes the URL the helper reads. It does not navigate,
   so it does not loop on the 301. */
(function (root) {
  var CANONICAL = {
    "/__/auth/handler/": "/__/auth/handler",
    "/__/auth/iframe/": "/__/auth/iframe",
    "/__/auth/callback/": "/__/auth/callback"
  };

  function canonicalAuthUrl(href) {
    var url = new URL(href);
    var next = CANONICAL[url.pathname];
    if (!next) return href;
    url.pathname = next;
    return url.href;
  }

  function applyCanonicalAuthPath(target) {
    if (!target || !target.location || !target.history) return null;
    var next = canonicalAuthUrl(target.location.href);
    if (next !== target.location.href) target.history.replaceState(null, "", next);
    return next;
  }

  root.yesbroCanonicalAuthUrl = canonicalAuthUrl;
  root.yesbroApplyCanonicalAuthPath = applyCanonicalAuthPath;
  if (root.window && root.window.location && root.window.history) {
    applyCanonicalAuthPath(root.window);
  }
})(typeof globalThis !== "undefined" ? globalThis : this);
