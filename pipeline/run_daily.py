#!/usr/bin/env python3
"""Yes Bro daily pipeline: gather -> Gemini write -> build -> publish. Talks dropped.

Env:
  GEMINI_API_KEY   required for AI text (else dry-run / fallback copy)
  YESBRO_DRY_RUN=1 force fallback copy (no AI calls)
  YESBRO_ROOT      default /workspace/yesbro
  YESBRO_SITE      default /workspace/yesbro-site
  YESBRO_EDS       comma list to limit papers (default: all)
  YESBRO_SKIP_PUBLISH=1  build HTML only, do not write site
"""
from __future__ import annotations
import argparse, calendar, datetime as dt, html, json, os, re, sys, time, traceback
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(os.environ.get("YESBRO_ROOT", "/workspace/yesbro")).resolve()
SITE = Path(os.environ.get("YESBRO_SITE", "/workspace/yesbro-site")).resolve()
PIPE = Path(__file__).resolve().parent
sys.path[:0] = [str(PIPE), str(ROOT)]

FIELD_EDS = [
    "business", "ux", "arch", "schools", "sustainability", "startups", "highered",
    "consulting", "health", "marketing", "finance", "aviation", "healing", "ai",
    "packaging", "fashion", "realestate", "auto",
]
ALL_EDS = ["daily"] + FIELD_EDS

# Column rotation (approx from house practice). Empty = skip that weekday.
COLUMN_DAYS = {
    0: ["daily", "business", "ux"],          # Mon
    1: ["arch", "schools", "health"],        # Tue
    2: ["ai", "startups", "consulting"],     # Wed
    3: ["finance", "highered", "healing"],   # Thu
    4: ["marketing", "aviation", "sustainability"],  # Fri
    5: ["daily", "business"],                # Sat
    6: ["ai", "healing", "daily"],           # Sun
}

def today_ist() -> dt.date:
    return dt.datetime.now(dt.timezone(dt.timedelta(hours=5, minutes=30))).date()

def dateline(d: dt.date) -> str:
    return d.strftime("%A %-d %B %Y") if sys.platform != "win32" else d.strftime("%A %d %B %Y").replace(" 0", " ")

def load_cfg(ed: str) -> dict:
    key = "daily" if ed == "daily" else ed
    return json.loads((ROOT / "editions" / "config" / f"{key}.json").read_text(encoding="utf-8"))

def ensure_run_dir(d: dt.date) -> Path:
    rd = ROOT / f"run_actions_{d.isoformat()}"
    rd.mkdir(exist_ok=True)
    (rd / "copy").mkdir(exist_ok=True)
    return rd

# ---------- gather ----------
def gather_fields(run_dir: Path, d: dt.date) -> Path:
    """RSS gather for field editions into items_all.json."""
    import feedparser, requests
    sys.path[:0] = [str(ROOT / "editions4"), str(ROOT / "editions2"), str(ROOT / "editions3"), str(ROOT / "editions")]
    import feeds_new, feeds_biz, feeds_ed, feeds2, feeds_healing, feeds_ai, feeds_packaging, feeds_arch_climate, feeds_fashion, feeds_realestate, feeds_auto
    FEEDS = {}
    for m in (feeds_ed, feeds2, feeds_new, feeds_biz, feeds_healing, feeds_ai, feeds_packaging, feeds_arch_climate, feeds_fashion, feeds_realestate, feeds_auto):
        for k, v in m.FEEDS.items():
            FEEDS.setdefault(k, [])
            for u in v:
                u = u.replace("when:7d", "when:3d").replace("+when%3A7d", "+when%3A3d")
                if u not in FEEDS[k]:
                    FEEDS[k].append(u)
    cut = calendar.timegm((d - dt.timedelta(days=3)).timetuple())
    now = time.time() + 3600
    UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36"}

    def get(args):
        ed, u = args
        try:
            r = requests.get(u, headers=UA, timeout=20)
            f = feedparser.parse(r.content)
            st = r.status_code
        except Exception as e:
            return ed, u, str(e)[:40], []
        out = []
        for e in f.entries:
            t = e.get("published_parsed") or e.get("updated_parsed")
            ts = calendar.timegm(t) if t else None
            if not ts or ts < cut or ts > now:
                continue
            desc = re.sub(r"<[^>]+>", " ", html.unescape(e.get("summary", "") or ""))
            desc = re.sub(r"\s+", " ", desc).strip()[:450]
            src = (e.get("source") or {}).get("title", "")
            out.append({"ed": ed, "feed": u, "title": html.unescape(e.get("title", "")).strip(), "url": e.get("link", ""), "ts": ts, "desc": desc, "src": src})
        return ed, u, st, out

    jobs = [(s, u) for s, us in FEEDS.items() for u in us]
    allit = []
    with ThreadPoolExecutor(24) as ex:
        for ed, u, st, items in ex.map(get, jobs):
            print(f"feed {ed} {st} {len(items)} {u[:90]}", flush=True)
            allit += items
    seen, res = set(), []
    for i in allit:
        k = (i["ed"], i["url"])
        kt = (i["ed"], i["title"].lower()[:70])
        if k in seen or kt in seen or not i["url"]:
            continue
        seen.add(k); seen.add(kt); res.append(i)
    res.sort(key=lambda i: -i["ts"])
    for n, i in enumerate(res):
        i["id"] = n
    out = run_dir / "items_all.json"
    out.write_text(json.dumps(res, indent=0), encoding="utf-8")
    print(f"gathered fields {len(res)} -> {out}", flush=True)
    return out

def gather_daily(run_dir: Path, d: dt.date) -> Path:
    import feedparser, requests
    sys.path.insert(0, str(ROOT / "gather31"))
    from feeds import FEEDS
    cut = calendar.timegm((d - dt.timedelta(days=3)).timetuple())
    UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36"}

    def get(args):
        sec, u = args
        try:
            r = requests.get(u, headers=UA, timeout=20)
            f = feedparser.parse(r.content)
            st = r.status_code
        except Exception as e:
            return sec, u, str(e), []
        out = []
        for e in f.entries:
            t = e.get("published_parsed") or e.get("updated_parsed")
            ts = calendar.timegm(t) if t else None
            if ts and ts < cut:
                continue
            desc = re.sub(r"<[^>]+>", " ", html.unescape(e.get("summary", "") or ""))
            desc = re.sub(r"\s+", " ", desc).strip()[:500]
            out.append({"sec": sec, "feed": u, "title": html.unescape(e.get("title", "")).strip(), "url": e.get("link", ""), "ts": ts, "desc": desc})
        return sec, u, st, out

    jobs = [(s, u) for s, us in FEEDS.items() for u in us]
    allit = []
    with ThreadPoolExecutor(24) as ex:
        for sec, u, st, items in ex.map(get, jobs):
            print(f"dailyfeed {sec} {st} {len(items)}", flush=True)
            allit += items
    seen, res = set(), []
    for i in allit:
        if i["url"] in seen or not i["url"]:
            continue
        seen.add(i["url"]); res.append(i)
    for n, i in enumerate(res):
        i["id"] = n
    out = run_dir / "items_daily.json"
    out.write_text(json.dumps(res, indent=0), encoding="utf-8")
    print(f"gathered daily {len(res)} -> {out}", flush=True)
    return out

def titles_for_field(run_dir: Path, ed: str) -> list[str]:
    items = json.loads((run_dir / "items_all.json").read_text(encoding="utf-8"))
    lines = []
    for i in items:
        if i.get("ed") != ed:
            continue
        src = i.get("src") or re.sub(r"https?://(www\.)?", "", i.get("feed", ""))[:40]
        lines.append(f"{i['id']}|{src}|{i['title']}")
    (run_dir / f"titles_{ed}.txt").write_text("\n".join(lines), encoding="utf-8")
    return lines

def titles_for_daily(run_dir: Path) -> dict[str, list[str]]:
    """Map daily section code -> title lines."""
    items = json.loads((run_dir / "items_daily.json").read_text(encoding="utf-8"))
    secmap = {
        "IP": "India Politics", "IO": "India Overall", "IS": "India Startups",
        "IE": "India ESG and Environment", "GO": "Global Overall",
        "GA": "Global AI and Technology", "GE": "Global ESG and Environment",
        "HE": "Health", "SS": "Space and Science", "HU": "Humour",
    }
    by = {v: [] for v in secmap.values()}
    for i in items:
        name = secmap.get(i.get("sec"))
        if not name:
            continue
        by[name].append(f"{i['id']}|{i.get('sec')}|{i['title']}")
    return by

# ---------- fetch ----------
def fetch_ids(run_dir: Path, ed: str, picks: dict, items_path: Path) -> dict:
    import requests
    try:
        import trafilatura
    except Exception:
        trafilatura = None
    try:
        from googlenewsdecoder import gnewsdecoder
    except Exception:
        gnewsdecoder = None
    items = {i["id"]: i for i in json.loads(items_path.read_text(encoding="utf-8"))}
    UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36", "Accept-Language": "en"}
    cf = run_dir / f"fetched_{ed}.json"
    try:
        cache = json.loads(cf.read_text(encoding="utf-8"))
    except Exception:
        cache = {}

    def resolve(u):
        if "news.google.com" not in u or not gnewsdecoder:
            return u
        for _ in range(2):
            try:
                r = gnewsdecoder(u, interval=1)
                if r.get("status") or r.get("success"):
                    return r["decoded_url"]
            except Exception:
                pass
            time.sleep(1)
        return None

    def meta(page, prop):
        m = re.search(r'<meta[^>]+(?:property|name|itemprop)=["\']%s["\'][^>]*content=["\']([^"\']*)' % prop, page, re.I) or re.search(r'<meta[^>]+content=["\']([^"\']*)["\'][^>]*(?:property|name|itemprop)=["\']%s["\']' % prop, page, re.I)
        return html.unescape(m.group(1)).strip() if m else ""

    def strip(s):
        return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()

    def work(i):
        k = str(i)
        if k in cache and cache[k].get("status") == 200:
            return k, cache[k]
        it = items[i]
        u = resolve(it["url"])
        out = {"id": i, "title": it["title"], "rss_desc": strip(it.get("desc", ""))[:300], "url": u, "status": None, "final": "", "ogt": "", "ogd": "", "tx": "", "ts": it.get("ts"), "pub": ""}
        if not u:
            out["status"] = "unresolved"
            return k, out
        try:
            r = requests.get(u, headers=UA, timeout=25, allow_redirects=True)
            out["status"] = r.status_code
            out["final"] = r.url
            p = r.text
            out["ogt"] = meta(p, "og:title")
            out["ogd"] = meta(p, "og:description") or meta(p, "description")
            out["pub"] = meta(p, "article:published_time") or meta(p, "datePublished") or ""
            t = ""
            if trafilatura:
                t = trafilatura.extract(p) or ""
            if len(t) < 150:
                t = (t + " " + out["ogd"] + " " + out["rss_desc"]).strip()
            out["tx"] = re.sub(r"\s+", " ", t)[:900]
        except Exception as e:
            out["status"] = str(e)[:60]
        return k, out

    ids = list(dict.fromkeys(i for v in picks.values() for i in v))
    with ThreadPoolExecutor(8) as ex:
        for k, o in ex.map(work, ids):
            cache[k] = o
    cf.write_text(json.dumps(cache, indent=0), encoding="utf-8")
    print(f"fetched {ed} {len(ids)}", flush=True)
    return cache

# ---------- stories ----------
def build_stories(ed: str, d: dt.date, cfg: dict, picks: dict, cache: dict, copy_map: dict) -> list:
    out, urls, ids, probs = [], set(), set(), []
    cut = (d - dt.timedelta(days=3)).isoformat()
    for sec, L in picks.items():
        if sec not in cfg.get("sections", []) and ed != "daily":
            # daily sections come from picks keys directly
            if ed != "daily":
                probs.append(f"unknown section {sec}")
        for i in L:
            o = cache.get(str(i))
            if not o:
                continue
            if int(i) not in copy_map:
                continue
            h, s = copy_map[int(i)]
            u = o.get("final") or o.get("url") or ""
            u = re.sub(r"[?&](source|utm_[a-z]+)=[^&]*", "", u)
            st = o.get("status")
            if st not in (200, 403, 401) and st != "unresolved":
                # still allow if we have text from rss
                if len(o.get("tx") or "") < 40 and len(o.get("rss_desc") or "") < 40:
                    continue
            n = len(s.split())
            if not 30 <= n <= 50:
                # trim or pad lightly
                words = s.split()
                if n > 50:
                    s = " ".join(words[:50])
                elif n < 30:
                    s = (s + " Further details were thin in the open report.").strip()
                    s = " ".join(s.split()[:50])
            if re.search(r"[\u2014\u2013;]", h + s):
                h = h.replace("\u2014", ",").replace("\u2013", " to ").replace(";", ",")
                s = s.replace("\u2014", ",").replace("\u2013", " to ").replace(";", ",")
            if u in urls or i in ids:
                continue
            if "news.google" in (u or ""):
                continue
            urls.add(u); ids.add(i)
            out.append({"section": sec, "headline": h, "summary": s, "url": u})
    # sort by config section order
    order = {s: n for n, s in enumerate(cfg.get("sections", []))}
    out.sort(key=lambda x: order.get(x["section"], 99))
    print(f"stories {ed} {len(out)} problems={probs[:5]}", flush=True)
    return out

def write_copy_py(run_dir: Path, ed: str, picks: dict, copy_map: dict):
    """Optional artifact matching old worker format."""
    lines = ["S=["]
    for sec, L in picks.items():
        lines.append(f"({sec!r},[")
        for i in L:
            if int(i) not in copy_map:
                continue
            h, s = copy_map[int(i)]
            lines.append(f"({i},{h!r},{s!r}),")
        lines.append("]),")
    lines.append("]")
    (run_dir / "copy" / f"copy_{ed}.py").write_text("\n".join(lines), encoding="utf-8")

# ---------- paper pipeline ----------
def process_field(run_dir: Path, ed: str, d: dt.date, per_section: int) -> Path | None:
    import ai_write
    cfg = load_cfg(ed)
    sections = cfg["sections"]
    lines = titles_for_field(run_dir, ed)
    if len(lines) < 5:
        print(f"skip {ed}: too few titles ({len(lines)})", flush=True)
        return None
    picks = ai_write.write_picks(ed, sections, lines, per_section=per_section)
    (run_dir / f"picks_{ed}.py").write_text("P=" + json.dumps(picks, indent=1), encoding="utf-8")
    # also as importable module style
    (run_dir / f"picks_{ed}.py").write_text("P = " + repr(picks) + "\n", encoding="utf-8")
    cache = fetch_ids(run_dir, ed, picks, run_dir / "items_all.json")
    items = []
    for sec, L in picks.items():
        for i in L:
            o = cache.get(str(i)) or {}
            tx = o.get("tx") or ""
            if len(tx) < 80:
                tx = (tx + " " + (o.get("ogd") or "") + " " + (o.get("rss_desc") or "")).strip()
            items.append({"id": i, "title": o.get("ogt") or o.get("title") or "", "text": tx, "section": sec})
    copy_map = ai_write.write_copy(ed, items)
    write_copy_py(run_dir, ed, picks, copy_map)
    stories = build_stories(ed, d, cfg, picks, cache, copy_map)
    if len(stories) < 8:
        print(f"skip {ed}: only {len(stories)} stories", flush=True)
        return None
    sp = ROOT / f"stories_{ed}_{d.isoformat()}.json"
    sp.write_text(json.dumps(stories, indent=1, ensure_ascii=False), encoding="utf-8")
    meme = ai_write.write_meme(ed, stories, d.isoformat())
    if meme:
        (ROOT / "memes" / f"{ed}_{d.isoformat()}.json").write_text(json.dumps(meme, indent=1), encoding="utf-8")
    return sp

def process_daily(run_dir: Path, d: dt.date, per_section: int) -> Path | None:
    import ai_write
    cfg = load_cfg("daily")
    by = titles_for_daily(run_dir)
    sections = [s for s in cfg.get("sections", []) if by.get(s)]
    # one flat candidate list with section hint preserved in the middle field
    flat = []
    for sec in sections:
        flat.extend(by.get(sec) or [])
    picks = ai_write.write_picks("daily", sections, flat, per_section=per_section) if sections else {}
    if not picks:
        return None
    (run_dir / "picks_daily.py").write_text("P = " + repr(picks) + "\n", encoding="utf-8")
    cache = fetch_ids(run_dir, "daily", picks, run_dir / "items_daily.json")
    items = []
    for sec, L in picks.items():
        for i in L:
            o = cache.get(str(i)) or {}
            tx = o.get("tx") or ""
            if len(tx) < 80:
                tx = (tx + " " + (o.get("ogd") or "") + " " + (o.get("rss_desc") or "")).strip()
            items.append({"id": i, "title": o.get("ogt") or o.get("title") or "", "text": tx, "section": sec})
    copy_map = ai_write.write_copy("daily", items)
    stories = build_stories("daily", d, cfg, picks, cache, copy_map)
    if len(stories) < 10:
        print(f"skip daily: only {len(stories)} stories", flush=True)
        return None
    sp = ROOT / f"stories_{d.isoformat()}.json"
    sp.write_text(json.dumps(stories, indent=1, ensure_ascii=False), encoding="utf-8")
    meme = ai_write.write_meme("daily", stories, d.isoformat())
    if meme:
        (ROOT / "memes" / f"daily_{d.isoformat()}.json").write_text(json.dumps(meme, indent=1), encoding="utf-8")
    return sp

def fetch_images_safe(stories_json: Path, html_json: Path, out_json: Path):
    import subprocess
    try:
        subprocess.run([sys.executable, str(ROOT / "fetch_images.py"), str(stories_json), str(html_json), "--mode", "html"], cwd=str(ROOT), check=False, timeout=600)
        subprocess.run([sys.executable, str(ROOT / "fetch_images.py"), str(stories_json), str(out_json)], cwd=str(ROOT), check=False, timeout=600)
    except Exception as e:
        print(f"images warn: {e}", flush=True)
        # minimal pass-through
        data = json.loads(stories_json.read_text(encoding="utf-8"))
        html_json.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
        out_json.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")

def aux_jobs_events(d: dt.date, eds: list[str]):
    import subprocess
    # jobs one at a time (cache helps)
    for ed in eds:
        if ed == "daily":
            continue
        try:
            subprocess.run([sys.executable, str(ROOT / "jobs.py"), ed, "--date", d.isoformat()], cwd=str(ROOT), check=False, timeout=300)
        except Exception as e:
            print(f"jobs {ed}: {e}", flush=True)
    try:
        cmd = [sys.executable, str(ROOT / "events.py"), "--date", d.isoformat()] + [e for e in eds if e != "daily"]
        if "daily" in eds:
            cmd.append("daily")
        subprocess.run(cmd, cwd=str(ROOT), check=False, timeout=600)
    except Exception as e:
        print(f"events: {e}", flush=True)
    try:
        if "business" in eds:
            subprocess.run([sys.executable, str(ROOT / "opps.py"), "--date", d.isoformat()], cwd=str(ROOT), check=False, timeout=300)
    except Exception as e:
        print(f"opps: {e}", flush=True)
    # research optional
    try:
        subprocess.run([sys.executable, str(ROOT / "research.py"), "--date", d.isoformat()] + [e for e in eds if e != "daily"], cwd=str(ROOT), check=False, timeout=600)
    except Exception as e:
        print(f"research: {e}", flush=True)
    # schools extras
    if "schools" in eds:
        for script in ("student_opps.py", "fieldwork_blog.py"):
            try:
                subprocess.run([sys.executable, str(ROOT / script), "--date", d.isoformat()], cwd=str(ROOT), check=False, timeout=300)
            except Exception as e:
                print(f"{script}: {e}", flush=True)
    # NOTE: talks.py intentionally not called

def build_and_publish(d: dt.date, eds: list[str], skip_publish: bool):
    import subprocess
    dl = dateline(d)
    D = d.isoformat()
    failed = []

    def ev(ed):
        p = ROOT / f"events_{ed}_{D}.json"
        return ["--events", str(p)] if p.exists() else []

    def rd(ed):
        p = ROOT / f"research_{ed}_{D}.json"
        return ["--research", str(p)] if p.exists() else []

    def so(ed):
        if ed != "schools":
            return []
        p = ROOT / f"student_opps_schools_{D}.json"
        return ["--student-opps", str(p)] if p.exists() else []

    def fw(ed):
        if ed != "schools":
            return []
        p = ROOT / f"fieldwork_blog_schools_{D}.json"
        return ["--fieldwork-blog", str(p)] if p.exists() else []

    # daily
    if "daily" in eds:
        sj = ROOT / f"stories_{D}.json"
        if sj.exists():
            hj = ROOT / f"stories_{D}.html.json"
            oj = ROOT / f"stories_{D}.out.json"
            if not hj.exists():
                fetch_images_safe(sj, hj, oj)
            html_out = ROOT / f"yesbro_{D}.html"
            cmd = [sys.executable, str(ROOT / "build_html.py"), str(hj if hj.exists() else sj), dl, str(html_out),
                   "--config", str(ROOT / "editions/config/daily.json")] + ev("daily") + rd("daily")
            if oj.exists():
                cmd += ["--fallback", str(oj)]
            r = subprocess.run(cmd, cwd=str(ROOT), check=False)
            if r.returncode != 0:
                failed.append("daily")
            elif not skip_publish:
                subprocess.run([sys.executable, str(ROOT / "publish.py"), "daily", str(html_out), D, "--site", str(SITE)], cwd=str(ROOT), check=False)

    for ed in eds:
        if ed == "daily":
            continue
        sj = ROOT / f"stories_{ed}_{D}.json"
        if not sj.exists():
            continue
        hj = ROOT / f"stories_{ed}_{D}.html.json"
        oj = ROOT / f"stories_{ed}_{D}.out.json"
        if not hj.exists():
            fetch_images_safe(sj, hj, oj)
        html_out = ROOT / f"yesbro_{ed}_{D}.html"
        jobs = ROOT / f"jobs_{ed}_{D}.json"
        cmd = [sys.executable, str(ROOT / "build_html.py"), str(hj if hj.exists() else sj), dl, str(html_out),
               "--config", str(ROOT / f"editions/config/{ed}.json")]
        if jobs.exists():
            cmd += ["--jobs", str(jobs)]
        cmd += ev(ed) + rd(ed) + so(ed) + fw(ed)
        if ed == "business":
            op = ROOT / f"opps_business_{D}.json"
            if op.exists():
                cmd += ["--opps", str(op)]
        if oj.exists():
            cmd += ["--fallback", str(oj)]
        # NO --talks
        r = subprocess.run(cmd, cwd=str(ROOT), check=False)
        if r.returncode != 0:
            failed.append(ed)
            continue
        if not skip_publish:
            subprocess.run([sys.executable, str(ROOT / "publish.py"), ed, str(html_out), D, "--site", str(SITE)], cwd=str(ROOT), check=False)

    if not skip_publish:
        subprocess.run([sys.executable, str(ROOT / "columns.py"), "publish", "--site", str(SITE)], cwd=str(ROOT), check=False)
        subprocess.run([sys.executable, str(ROOT / "build_landing.py"), "--site", str(SITE), "--stories-dir", str(ROOT)], cwd=str(ROOT), check=False)
        subprocess.run([sys.executable, str(ROOT / "pwa.py")], cwd=str(ROOT), check=False)
        # mypaper best effort
        try:
            subprocess.run([sys.executable, str(ROOT / "build_mypaper_data.py"), "--date", D, "--site", str(SITE)], cwd=str(ROOT), check=False, timeout=120)
            subprocess.run([sys.executable, str(ROOT / "build_mypaper.py"), "--site", str(SITE)], cwd=str(ROOT), check=False, timeout=120)
        except Exception as e:
            print(f"mypaper: {e}", flush=True)
    if failed:
        print("FAILED papers:", " ".join(failed), flush=True)
        return 1
    return 0

def maybe_columns(d: dt.date, eds: list[str]):
    import ai_write
    want = [e for e in COLUMN_DAYS.get(d.weekday(), []) if e in eds]
    for ed in want:
        sj = ROOT / (f"stories_{d.isoformat()}.json" if ed == "daily" else f"stories_{ed}_{d.isoformat()}.json")
        if not sj.exists():
            continue
        stories = json.loads(sj.read_text(encoding="utf-8"))[:8]
        md = ai_write.write_column_md(ed, d.isoformat(), stories)
        if not md:
            continue
        # slug from front matter
        m = re.search(r"^slug:\s*(.+)$", md, re.M)
        slug = (m.group(1).strip() if m else f"explains-{d.isoformat()}")
        folder = ROOT / "columns" / ed
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{d.isoformat()}-{slug}.md"
        path.write_text(md, encoding="utf-8")
        print(f"column wrote {path}", flush=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=today_ist().isoformat())
    ap.add_argument("--eds", default=os.environ.get("YESBRO_EDS", ""))
    ap.add_argument("--per-section", type=int, default=10)
    ap.add_argument("--skip-gather", action="store_true")
    ap.add_argument("--skip-aux", action="store_true")
    ap.add_argument("--skip-publish", action="store_true", default=os.environ.get("YESBRO_SKIP_PUBLISH") == "1")
    ap.add_argument("--skip-images", action="store_true")
    ap.add_argument("--only-build", action="store_true", help="only build/publish existing stories")
    args = ap.parse_args()
    d = dt.date.fromisoformat(args.date)
    eds = [e.strip() for e in args.eds.split(",") if e.strip()] or ALL_EDS
    print(f"Yes Bro Actions run date={d} eds={eds} dry={os.environ.get('YESBRO_DRY_RUN')} gemini_key={'yes' if os.environ.get('GEMINI_API_KEY') else 'no'}", flush=True)

    run_dir = ensure_run_dir(d)
    os.chdir(run_dir)

    if not args.only_build:
        if not args.skip_gather:
            if any(e != "daily" for e in eds):
                gather_fields(run_dir, d)
            if "daily" in eds:
                gather_daily(run_dir, d)
        # process papers
        if "daily" in eds and (run_dir / "items_daily.json").exists():
            try:
                process_daily(run_dir, d, args.per_section)
            except Exception:
                traceback.print_exc()
        for ed in eds:
            if ed == "daily":
                continue
            if not (run_dir / "items_all.json").exists():
                break
            try:
                process_field(run_dir, ed, d, args.per_section)
            except Exception:
                traceback.print_exc()
        maybe_columns(d, eds)
        if not args.skip_aux:
            aux_jobs_events(d, eds)

    # ensure html.json exists for build
    D = d.isoformat()
    for ed in eds:
        if ed == "daily":
            sj = ROOT / f"stories_{D}.json"
            hj = ROOT / f"stories_{D}.html.json"
            oj = ROOT / f"stories_{D}.out.json"
        else:
            sj = ROOT / f"stories_{ed}_{D}.json"
            hj = ROOT / f"stories_{ed}_{D}.html.json"
            oj = ROOT / f"stories_{ed}_{D}.out.json"
        if sj.exists():
            if args.skip_images:
                data = json.loads(sj.read_text(encoding="utf-8"))
                hj.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
                oj.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
            else:
                fetch_images_safe(sj, hj, oj)

    code = build_and_publish(d, eds, args.skip_publish)
    print("done", code, flush=True)
    return code

if __name__ == "__main__":
    sys.exit(main() or 0)
