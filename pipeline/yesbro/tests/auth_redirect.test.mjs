import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import fs from "node:fs";
import http from "node:http";
import net from "node:net";
import os from "node:os";
import path from "node:path";
import { mkdtemp, rm } from "node:fs/promises";
import { test } from "node:test";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const repo = path.resolve(here, "../../..");
const authDir = path.join(repo, "__/auth");
const normalizerPath = path.join(authDir, "normalize-auth-path.js");

function loadNormalizer() {
  const sandbox = { URL, console };
  sandbox.globalThis = sandbox;
  vm.createContext(sandbox);
  vm.runInContext(fs.readFileSync(normalizerPath, "utf8"), sandbox, { filename: normalizerPath });
  assert.equal(typeof sandbox.yesbroCanonicalAuthUrl, "function");
  return sandbox;
}

function scriptSrcs(html) {
  return [...html.matchAll(/<script\b[^>]*\ssrc="([^"]+)"/gi)].map((match) => match[1]);
}

function readApiKey() {
  const live = fs.readFileSync(path.join(repo, "mypaper/firebase-config.js"), "utf8");
  const src = fs.readFileSync(path.join(repo, "pipeline/yesbro/mypaper_src/firebase-config.js"), "utf8");
  assert.equal(live, src, "deployed firebase-config.js must match mypaper_src");
  const domain = live.match(/authDomain:\s*"([^"]+)"/);
  const key = live.match(/apiKey:\s*"([^"]+)"/);
  assert.ok(domain && key);
  return { live, authDomain: domain[1], apiKey: key[1] };
}

test("canonical auth URLs drop only the helper trailing slash", () => {
  const { yesbroCanonicalAuthUrl } = loadNormalizer();
  const cases = [
    [
      "https://yesbrohq.com/__/auth/handler/?apiKey=abc&authType=signInViaPopup&providerId=google.com",
      "https://yesbrohq.com/__/auth/handler?apiKey=abc&authType=signInViaPopup&providerId=google.com"
    ],
    [
      "https://www.yesbrohq.com/__/auth/iframe/?apiKey=abc",
      "https://www.yesbrohq.com/__/auth/iframe?apiKey=abc"
    ],
    [
      "https://yesbrohq.com/__/auth/callback/?state=1#id_token=abc",
      "https://yesbrohq.com/__/auth/callback?state=1#id_token=abc"
    ],
    [
      "https://yesbrohq.com/__/auth/handler?apiKey=abc",
      "https://yesbrohq.com/__/auth/handler?apiKey=abc"
    ],
    [
      "https://yesbrohq.com/mypaper/?mine",
      "https://yesbrohq.com/mypaper/?mine"
    ],
    [
      "http://localhost:8765/__/auth/handler/?apiKey=abc",
      "http://localhost:8765/__/auth/handler?apiKey=abc"
    ]
  ];
  for (const [input, expected] of cases) {
    assert.equal(yesbroCanonicalAuthUrl(input), expected);
  }
});

test("replaceState runs for a slashed helper and leaves other pages alone", () => {
  const { yesbroApplyCanonicalAuthPath } = loadNormalizer();
  const slashed = fakeWindow("https://yesbrohq.com/__/auth/handler/?apiKey=abc&providerId=google.com");
  const next = yesbroApplyCanonicalAuthPath(slashed);
  assert.equal(next, "https://yesbrohq.com/__/auth/handler?apiKey=abc&providerId=google.com");
  assert.equal(slashed.location.href, next);
  assert.equal(slashed.history.calls.length, 1);

  const paper = fakeWindow("https://yesbrohq.com/mypaper/");
  assert.equal(yesbroApplyCanonicalAuthPath(paper), "https://yesbrohq.com/mypaper/");
  assert.equal(paper.history.calls.length, 0);
});

test("auth helper pages load the normalizer before Firebase helper scripts", () => {
  const handler = scriptSrcs(fs.readFileSync(path.join(authDir, "handler/index.html"), "utf8"));
  const callback = scriptSrcs(fs.readFileSync(path.join(authDir, "callback/index.html"), "utf8"));
  const iframe = scriptSrcs(fs.readFileSync(path.join(authDir, "iframe/index.html"), "utf8"));
  assert.deepEqual(handler, ["/__/auth/normalize-auth-path.js", "/__/auth/experiments.js", "/__/auth/handler.js"]);
  assert.deepEqual(callback, ["/__/auth/normalize-auth-path.js", "/__/auth/experiments.js", "/__/auth/handler.js"]);
  assert.deepEqual(iframe, ["/__/auth/normalize-auth-path.js", "/__/auth/iframe.js"]);
  for (const htmlPath of ["handler/index.html", "callback/index.html", "iframe/index.html"]) {
    const html = fs.readFileSync(path.join(authDir, htmlPath), "utf8");
    const normalizerAt = html.indexOf("normalize-auth-path.js");
    const initAt = html.indexOf(".initialize(");
    assert.ok(normalizerAt > 0 && initAt > normalizerAt, htmlPath);
  }
});

test("sign-in keeps the yesbrohq.com auth domain in both config copies", () => {
  const { live, authDomain } = readApiKey();
  assert.equal(authDomain, "yesbrohq.com");
  assert.match(live, /authDomain:\s*"yesbrohq.com"/);
  assert.doesNotMatch(live, /authDomain:\s*"[^"]*firebaseapp\.com"/);
  assert.match(live, /projectId:\s*"yes-bro-5c2dd"/);
  assert.match(live, /enabled:\s*true/);
});

test("GitHub-style slash redirect is what the real handler would send, and the normalizer stops it", async (t) => {
  const { apiKey } = readApiKey();
  const server = await startAuthServer();
  t.after(() => server.stop());
  const fixed = await withChrome(async (page) => {
    server.stripNormalizer = false;
    return page.captureAuthRequest(server.origin + "/__/auth/handler?" + handlerQuery(apiKey));
  });
  assert.equal(fixed.continueUri, server.origin + "/__/auth/handler");
  assert.equal(fixed.googleRedirectUri, fixed.continueUri);
  assert.equal(fixed.clientId, OAUTH_CLIENT_ID);

  const broken = await withChrome(async (page) => {
    server.stripNormalizer = true;
    return page.captureAuthRequest(server.origin + "/__/auth/handler?" + handlerQuery(apiKey));
  });
  assert.equal(broken.continueUri, server.origin + "/__/auth/handler/");
  assert.equal(broken.googleRedirectUri, broken.continueUri);
  assert.equal(broken.clientId, OAUTH_CLIENT_ID);
});

const OAUTH_CLIENT_ID = "1043001791506-m22ntu3e41nl2n8oqfo1tv1htak3tjuk.apps.googleusercontent.com";

function handlerQuery(apiKey) {
  return new URLSearchParams({
    apiKey,
    appName: "[DEFAULT]",
    authType: "signInViaPopup",
    redirectUrl: "https://yesbrohq.com/mypaper/",
    v: "10.14.1",
    providerId: "google.com",
    customParameters: JSON.stringify({ prompt: "select_account" })
  }).toString();
}

function fakeWindow(href) {
  const location = { href };
  return {
    location,
    history: {
      calls: [],
      replaceState(_state, _title, next) {
        this.calls.push(next);
        location.href = String(next);
      }
    }
  };
}

function startAuthServer() {
  const helpers = new Set(["handler", "iframe", "callback"]);
  const server = http.createServer((req, res) => {
    server.hits.push(req.url);
    const url = new URL(req.url, "http://localhost");
    if (!url.pathname.startsWith("/__/auth/")) {
      res.writeHead(404);
      res.end("not found");
      return;
    }
    const rel = decodeURIComponent(url.pathname.slice("/__/auth/".length));
    if (helpers.has(rel)) {
      res.writeHead(301, { Location: url.pathname + "/" + url.search });
      res.end();
      return;
    }
    let fileRel = rel;
    if (rel.endsWith("/")) fileRel = rel + "index.html";
    const file = path.normalize(path.join(authDir, fileRel));
    if (!file.startsWith(authDir + path.sep) || !fs.existsSync(file) || !fs.statSync(file).isFile()) {
      res.writeHead(404);
      res.end("missing " + rel);
      return;
    }
    let body = fs.readFileSync(file);
    if (server.stripNormalizer && file.endsWith("index.html")) {
      body = Buffer.from(body.toString("utf8").replace(/\n?<script\b[^>]*normalize-auth-path\.js"><\/script>/, ""));
    }
    const type = file.endsWith(".js") ? "text/javascript; charset=utf-8" : "text/html; charset=utf-8";
    res.writeHead(200, { "Content-Type": type, "Cache-Control": "no-store" });
    res.end(body);
  });
  server.stripNormalizer = false;
  server.hits = [];
  const stop = () => new Promise((done) => server.close(done));
  return new Promise((resolve, reject) => {
    server.on("error", reject);
    server.listen(0, "127.0.0.1", () => {
      const port = server.address().port;
      server.origin = "http://localhost:" + port;
      server.stop = stop;
      resolve(server);
    });
  });
}

async function withChrome(run) {
  const debugPort = await freePort();
  const userData = await mkdtemp(path.join(os.tmpdir(), "yb-auth-chrome-"));
  const chrome = spawn("google-chrome", [
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--no-first-run",
    "--disable-extensions",
    "--remote-debugging-address=127.0.0.1",
    "--remote-debugging-port=" + debugPort,
    "--user-data-dir=" + userData,
    "about:blank"
  ], { stdio: ["ignore", "pipe", "pipe"] });
  let chromeLog = "";
  chrome.stderr.on("data", (chunk) => {
    chromeLog += chunk.toString();
    if (chromeLog.length > 8000) chromeLog = chromeLog.slice(-8000);
  });
  try {
    const version = await waitJson("http://127.0.0.1:" + debugPort + "/json/version");
    const ws = new WebSocket(version.webSocketDebuggerUrl);
    await new Promise((resolve, reject) => {
      ws.addEventListener("open", resolve, { once: true });
      ws.addEventListener("error", reject, { once: true });
    });
    const browser = new Cdp(ws);
    try {
      const { targetId } = await browser.send("Target.createTarget", { url: "about:blank" });
      const { sessionId } = await browser.send("Target.attachToTarget", { targetId, flatten: true });
      const page = browser.session(sessionId);
      await page.send("Page.enable");
      await page.send("Network.enable");
      page.network = [];
      await page.send("Fetch.enable", {
        patterns: [
          { urlPattern: "*createAuthUri*", requestStage: "Request" },
          { urlPattern: "*accounts.google.com*", requestStage: "Request" }
        ]
      });
      page.captureAuthRequest = (startUrl) => captureAuthRequest(page, startUrl);
      return await run(page);
    } finally {
      ws.close();
    }
  } catch (error) {
    error.message += "\nchrome: " + chromeLog.slice(-1500);
    throw error;
  } finally {
    chrome.kill("SIGKILL");
    await new Promise((resolve) => {
      if (chrome.exitCode !== null || chrome.signalCode !== null) resolve();
      else chrome.once("exit", resolve);
    });
    await rm(userData, { recursive: true, force: true }).catch(() => {});
  }
}

function captureAuthRequest(page, startUrl) {
  const found = { continueUri: "", googleRedirectUri: "", clientId: "" };
  const wait = new Promise((resolve, reject) => {
    let finished = false;
    const finish = () => {
      if (finished) return;
      finished = true;
      clearTimeout(timer);
      resolve(found);
    };
    const timer = setTimeout(async () => {
      let pageState = "";
      try {
        const state = await page.send("Runtime.evaluate", {
          expression: "JSON.stringify({href:location.href,path:location.pathname,text:(document.body&&document.body.innerText||'').slice(0,500),scripts:[...document.scripts].map(s=>s.src)})",
          returnByValue: true
        });
        pageState = ((state.result && state.result.value) || JSON.stringify(state)).replace(/AIza[0-9A-Za-z_-]+/g, "API_KEY");
      } catch (error) {
        pageState = String(error);
      }
      reject(new Error("timed out waiting for createAuthUri page=" + pageState + " network=" + (page.network || []).slice(0, 12).join(" ")));
    }, 20000);
    page.onPaused = async (params) => {
      const url = params.request.url || "";
      try {
        if (url.includes("createAuthUri")) {
          const body = JSON.parse(params.request.postData || "{}");
          // The helper also probes createAuthUri with a #webwidgetstarter fragment.
          // The Google redirect is the call with no fragment.
          if (body.continueUri && !body.continueUri.includes("#")) found.continueUri = body.continueUri;
          await page.send("Fetch.continueRequest", { requestId: params.requestId });
          if (found.continueUri) setTimeout(finish, 2500);
          return;
        }
        if (url.includes("accounts.google.com")) {
          const parsed = new URL(url);
          found.googleRedirectUri = parsed.searchParams.get("redirect_uri") || found.googleRedirectUri;
          found.clientId = parsed.searchParams.get("client_id") || found.clientId;
          await page.send("Fetch.failRequest", { requestId: params.requestId, errorReason: "Aborted" });
          if (found.continueUri && found.googleRedirectUri) finish();
          return;
        }
        await page.send("Fetch.continueRequest", { requestId: params.requestId });
      } catch (error) {
        clearTimeout(timer);
        finished = true;
        reject(error);
      }
    };
  });
  const nav = page.send("Page.navigate", { url: startUrl });
  return Promise.all([wait, nav]).then(([captured]) => captured);
}

class Cdp {
  constructor(ws) {
    this.ws = ws;
    this.next = 1;
    this.pending = new Map();
    this.sessions = new Map();
    ws.addEventListener("message", (event) => {
      const msg = JSON.parse(event.data);
      if (msg.sessionId && this.sessions.has(msg.sessionId)) {
        this.sessions.get(msg.sessionId).dispatch(msg);
        return;
      }
      this.dispatch(msg);
    });
  }

  session(sessionId) {
    const session = new CdpSession(this, sessionId);
    this.sessions.set(sessionId, session);
    return session;
  }

  send(method, params, sessionId) {
    const id = this.next++;
    const payload = { id, method, params: params || {} };
    if (sessionId) payload.sessionId = sessionId;
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      this.ws.send(JSON.stringify(payload));
    });
  }

  dispatch(msg) {
    if (!msg.id || !this.pending.has(msg.id)) return;
    const waiter = this.pending.get(msg.id);
    this.pending.delete(msg.id);
    if (msg.error) waiter.reject(new Error(msg.error.message || JSON.stringify(msg.error)));
    else waiter.resolve(msg.result || {});
  }
}

class CdpSession {
  constructor(browser, sessionId) {
    this.browser = browser;
    this.sessionId = sessionId;
    this.onPaused = null;
  }

  send(method, params) {
    return this.browser.send(method, params, this.sessionId);
  }

  dispatch(msg) {
    if (msg.method === "Network.requestWillBeSent" && msg.params && msg.params.request) {
      this.network = this.network || [];
      this.network.push(msg.params.request.url);
    }
    if (msg.method === "Fetch.requestPaused" && this.onPaused) {
      this.onPaused(msg.params);
      return;
    }
    this.browser.dispatch(msg);
  }
}

function freePort() {
  return new Promise((resolve, reject) => {
    const socket = net.createServer();
    socket.once("error", reject);
    socket.listen(0, "127.0.0.1", () => {
      const port = socket.address().port;
      socket.close(() => resolve(port));
    });
  });
}

function waitJson(url) {
  const started = Date.now();
  return new Promise((resolve, reject) => {
    const tick = async () => {
      try {
        const response = await fetch(url);
        if (response.ok) {
          resolve(await response.json());
          return;
        }
      } catch {
        /* chrome is still starting */
      }
      if (Date.now() - started > 15000) {
        reject(new Error("Chrome debugging port did not open"));
        return;
      }
      setTimeout(tick, 100);
    };
    tick();
  });
}
