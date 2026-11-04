#!/usr/bin/env python3
"""Write SEO/AEO site assets for yesbrohq.com.

  python3 sitemap.py [--site /workspace/yesbro-site]

Writes:
  - sitemap.xml (landing, papers, explains, archives)
  - news-sitemap.xml (paper pages + archive issues from the last 48 hours, with keywords)
  - robots.txt (Allow all + AI crawlers; points at both sitemaps and llms.txt)
  - llms.txt and llms-full.txt (AI-search plain-text map; per-paper sections from seo_categories.json)
  - <folder>/feed.xml RSS 2.0 per paper
  - IndexNow key file at /{key}.txt when present in seo_categories or INDEXNOW_KEY env

lastmod comes from the page's JSON-LD dateModified/datePublished, an archive file name, or today.
Called after every publish: build_landing.py, publish.py and columns.py publish.
"""
from __future__ import annotations

import datetime as dt
import glob
import html
import json
import os
import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape as xml_esc

SITE = "https://yesbrohq.com"
SKIP_FOLDERS = {"archive", "img", "data", "mypaper_src", ".git", "pipeline", "node_modules"}


def _here() -> Path:
    return Path(__file__).resolve().parent


def load_categories() -> dict:
    path = _here() / "seo_categories.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"site": {"url": SITE + "/", "name": "Yes Bro"}, "papers": {}}


def lastmod(path: str) -> str:
    m = re.search(r"(\d{4}-\d{2}-\d{2})\.html$", path)
    if m:
        return m.group(1)
    try:
        t = open(path, encoding="utf-8", errors="ignore").read(200000)
    except OSError:
        return dt.date.today().isoformat()
    m = re.search(r'"dateModified":\s*"(\d{4}-\d{2}-\d{2})', t) or re.search(
        r'"datePublished":\s*"(\d{4}-\d{2}-\d{2})', t
    )
    return m.group(1) if m else dt.date.today().isoformat()


def _paper_folders(site: str) -> list[str]:
    out = []
    for idx in sorted(glob.glob(os.path.join(site, "*", "index.html"))):
        folder = os.path.basename(os.path.dirname(idx))
        if folder in SKIP_FOLDERS:
            continue
        out.append(folder)
    return out


def _paper_meta(cats: dict, folder: str) -> dict:
    papers = cats.get("papers") or {}
    for key, meta in papers.items():
        if meta.get("folder") == folder or key == folder:
            return {**meta, "key": key}
    # fallback from edition config if present
    cfg_path = _here() / "editions" / "config"
    for p in cfg_path.glob("*.json") if cfg_path.exists() else []:
        c = json.loads(p.read_text(encoding="utf-8"))
        url = c.get("url") or ""
        if url.rstrip("/").endswith("/" + folder) or c.get("key") == folder:
            return {
                "key": c.get("key") or folder,
                "folder": folder,
                "name": c.get("title") or folder,
                "title": c.get("seo_title") or c.get("title") or folder,
                "description": c.get("seo_desc") or c.get("motto") or "",
                "about": c.get("seo_desc") or "",
                "keywords": [],
                "genre": [],
            }
    return {
        "key": folder,
        "folder": folder,
        "name": folder,
        "title": f"{folder} | Yes Bro",
        "description": "",
        "about": "",
        "keywords": [],
        "genre": [],
    }


def _extract_stories(html_text: str, limit: int = 25) -> list[dict]:
    """Pull headline/url pairs from CollectionPage ItemList JSON-LD, else from story anchors."""
    stories = []
    for m in re.finditer(
        r'<script type="application/ld\+json">(.*?)</script>', html_text, re.S | re.I
    ):
        try:
            data = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        main = data.get("mainEntity") if isinstance(data, dict) else None
        if not isinstance(main, dict):
            continue
        for it in main.get("itemListElement") or []:
            if not isinstance(it, dict):
                continue
            url = it.get("url") or ""
            name = it.get("name") or ""
            if url and name:
                stories.append({"headline": name, "url": url})
        if stories:
            return stories[:limit]
    # Fallback: story links in body
    for m in re.finditer(
        r'<a[^>]+href="(https?://[^"]+)"[^>]*class="[^"]*hl[^"]*"[^>]*>(.*?)</a>',
        html_text,
        re.S | re.I,
    ):
        stories.append(
            {"url": m.group(1), "headline": re.sub(r"<[^>]+>", "", m.group(2)).strip()}
        )
    if not stories:
        for m in re.finditer(
            r'<h[23][^>]*>\s*<a[^>]+href="(https?://[^"]+)"[^>]*>(.*?)</a>',
            html_text,
            re.S | re.I,
        ):
            stories.append(
                {
                    "url": m.group(1),
                    "headline": re.sub(r"<[^>]+>", "", m.group(2)).strip(),
                }
            )
    return stories[:limit]


def write_sitemap_xml(site: str, rows: list[tuple]) -> None:
    xml = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for loc, lm, f, p in rows:
        xml.append(
            f"  <url><loc>{xml_esc(loc)}</loc><lastmod>{lm}</lastmod>"
            f"<changefreq>{f}</changefreq><priority>{p}</priority></url>"
        )
    xml.append("</urlset>")
    Path(site, "sitemap.xml").write_text("\n".join(xml) + "\n", encoding="utf-8")


def write_news_sitemap(site: str, cats: dict) -> int:
    """Google News sitemap for paper fronts and archive issues from the last 48 hours."""
    cutoff = dt.date.today() - dt.timedelta(days=2)
    entries = []
    for folder in _paper_folders(site):
        meta = _paper_meta(cats, folder)
        keywords = ", ".join(meta.get("keywords") or [])
        name = meta.get("name") or f"Yes Bro {folder}"
        idx = os.path.join(site, folder, "index.html")
        lm = lastmod(idx)
        try:
            lm_date = dt.date.fromisoformat(lm)
        except ValueError:
            lm_date = dt.date.today()
        if lm_date >= cutoff:
            entries.append((f"{SITE}/{folder}/", lm, name, keywords, meta.get("title") or name))
        for a in sorted(glob.glob(os.path.join(site, folder, "archive", "*.html")), reverse=True):
            lm = lastmod(a)
            try:
                lm_date = dt.date.fromisoformat(lm)
            except ValueError:
                continue
            if lm_date < cutoff:
                continue
            title = f"{name} — {lm}"
            entries.append(
                (f"{SITE}/{folder}/archive/{os.path.basename(a)}", lm, name, keywords, title)
            )
    xml = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
        '        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">',
    ]
    for loc, lm, publication, keywords, title in entries:
        xml.append("  <url>")
        xml.append(f"    <loc>{xml_esc(loc)}</loc>")
        xml.append("    <news:news>")
        xml.append("      <news:publication>")
        xml.append(f"        <news:name>{xml_esc(publication)}</news:name>")
        xml.append("        <news:language>en</news:language>")
        xml.append("      </news:publication>")
        xml.append(f"      <news:publication_date>{lm}</news:publication_date>")
        xml.append(f"      <news:title>{xml_esc(title)}</news:title>")
        if keywords:
            xml.append(f"      <news:keywords>{xml_esc(keywords)}</news:keywords>")
        xml.append("    </news:news>")
        xml.append("  </url>")
    xml.append("</urlset>")
    Path(site, "news-sitemap.xml").write_text("\n".join(xml) + "\n", encoding="utf-8")
    return len(entries)


def write_robots(site: str, indexnow_key: str | None) -> None:
    ai_bots = [
        "GPTBot",
        "ChatGPT-User",
        "Google-Extended",
        "GoogleOther",
        "anthropic-ai",
        "ClaudeBot",
        "Claude-Web",
        "PerplexityBot",
        "Applebot-Extended",
        "Bytespider",
        "CCBot",
        "FacebookBot",
        "meta-externalagent",
        "cohere-ai",
        "Diffbot",
        "ImagesiftBot",
        "Omgilibot",
        "OAI-SearchBot",
    ]
    lines = [
        "# Yes Bro — crawl freely. AI crawlers welcome.",
        "# llms.txt: https://yesbrohq.com/llms.txt",
        "",
        "User-agent: *",
        "Allow: /",
        "",
    ]
    for bot in ai_bots:
        lines += [f"User-agent: {bot}", "Allow: /", ""]
    lines += [
        f"Sitemap: {SITE}/sitemap.xml",
        f"Sitemap: {SITE}/news-sitemap.xml",
        "",
    ]
    if indexnow_key:
        lines.append(f"# IndexNow key file: /{indexnow_key}.txt")
    Path(site, "robots.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_llms(site: str, cats: dict) -> None:
    site_meta = cats.get("site") or {}
    papers = cats.get("papers") or {}
    # order: daily first, then alpha by name
    ordered = sorted(
        papers.items(),
        key=lambda kv: (0 if kv[0] == "daily" else 1, (kv[1].get("name") or kv[0]).lower()),
    )
    short = [
        "# Yes Bro",
        "",
        f"> {site_meta.get('tagline') or 'Build your own newspaper. Read every day what you want.'}",
        f"> {site_meta.get('promise') or 'No accounts required to read. No tracking of what you read.'}",
        "",
        f"{site_meta.get('name') or 'Yes Bro'} publishes free daily newspapers for different fields. "
        "Every headline links to the original report. Readers pick a paper; there is no feed ranking and no tracking of what they read.",
        "",
        "## Papers",
        "",
    ]
    full = list(short)
    for key, meta in ordered:
        folder = meta.get("folder") or key
        name = meta.get("name") or key
        about = (meta.get("about") or meta.get("description") or "").strip()
        url = f"{SITE}/{folder}/"
        feed = f"{SITE}/{folder}/feed.xml"
        short.append(f"- [{name}]({url}): {(about[:140] + '…') if len(about) > 140 else about}")
        full += [
            f"## {name}",
            "",
            about,
            "",
            f"- Home: {url}",
            f"- RSS: {feed}",
            f"- Keywords: {', '.join(meta.get('keywords') or [])}",
            "",
        ]
    short += [
        "",
        "## Optional",
        "",
        f"- Full map: {SITE}/llms-full.txt",
        f"- Sitemap: {SITE}/sitemap.xml",
        f"- News sitemap: {SITE}/news-sitemap.xml",
        "",
    ]
    Path(site, "llms.txt").write_text("\n".join(short) + "\n", encoding="utf-8")
    Path(site, "llms-full.txt").write_text("\n".join(full) + "\n", encoding="utf-8")


def write_rss_feeds(site: str, cats: dict) -> int:
    count = 0
    today = dt.date.today().isoformat()
    for folder in _paper_folders(site):
        meta = _paper_meta(cats, folder)
        idx = os.path.join(site, folder, "index.html")
        try:
            html_text = open(idx, encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        stories = _extract_stories(html_text)
        lm = lastmod(idx)
        title = meta.get("title") or meta.get("name") or folder
        desc = meta.get("description") or meta.get("about") or ""
        link = f"{SITE}/{folder}/"
        items_xml = []
        for st in stories:
            items_xml.append(
                "    <item>\n"
                f"      <title>{xml_esc(st['headline'])}</title>\n"
                f"      <link>{xml_esc(st['url'])}</link>\n"
                f"      <guid isPermaLink=\"true\">{xml_esc(st['url'])}</guid>\n"
                f"      <pubDate>{lm}</pubDate>\n"
                f"      <description>{xml_esc(st['headline'])}</description>\n"
                "    </item>"
            )
        feed = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n'
            "  <channel>\n"
            f"    <title>{xml_esc(title)}</title>\n"
            f"    <link>{link}</link>\n"
            f"    <description>{xml_esc(desc)}</description>\n"
            f"    <language>en</language>\n"
            f"    <lastBuildDate>{lm or today}</lastBuildDate>\n"
            f'    <atom:link href="{SITE}/{folder}/feed.xml" rel="self" type="application/rss+xml"/>\n'
            + ("\n".join(items_xml) + "\n" if items_xml else "")
            + "  </channel>\n</rss>\n"
        )
        Path(site, folder, "feed.xml").write_text(feed, encoding="utf-8")
        count += 1
    return count


def ensure_indexnow_key(site: str, cats: dict) -> str | None:
    key = (
        os.environ.get("INDEXNOW_KEY")
        or (cats.get("site") or {}).get("indexnow_key")
        or ""
    ).strip()
    key_file = _here() / "indexnow_key.txt"
    if not key and key_file.exists():
        key = key_file.read_text(encoding="utf-8").strip()
    if not key:
        return None
    # Public verification file required by IndexNow
    Path(site, f"{key}.txt").write_text(key + "\n", encoding="utf-8")
    # Keep a small pointer file (not secret; key must be public)
    Path(site, "indexnow-key.txt").write_text(key + "\n", encoding="utf-8")
    return key


def collect_urls(site: str) -> list[tuple]:
    rows = []

    def add(path, loc, freq, prio):
        rows.append((loc, lastmod(path), freq, prio))

    add(os.path.join(site, "index.html"), SITE + "/", "daily", "1.0")
    for folder in _paper_folders(site):
        idx = os.path.join(site, folder, "index.html")
        add(idx, f"{SITE}/{folder}/", "daily", "0.9")
        feed = os.path.join(site, folder, "feed.xml")
        if os.path.exists(feed):
            add(feed, f"{SITE}/{folder}/feed.xml", "daily", "0.5")
        ex = os.path.join(site, folder, "explains", "index.html")
        if os.path.exists(ex):
            add(ex, f"{SITE}/{folder}/explains/", "weekly", "0.7")
            for col in sorted(
                glob.glob(os.path.join(site, folder, "explains", "*", "index.html"))
            ):
                add(
                    col,
                    f"{SITE}/{folder}/explains/{os.path.basename(os.path.dirname(col))}/",
                    "monthly",
                    "0.8",
                )
        for a in sorted(glob.glob(os.path.join(site, folder, "archive", "*.html")), reverse=True):
            add(a, f"{SITE}/{folder}/archive/{os.path.basename(a)}", "never", "0.4")
    # also list llms and news sitemap as ordinary URLs for discovery
    for name, prio in (("llms.txt", "0.3"), ("llms-full.txt", "0.3"), ("news-sitemap.xml", "0.2")):
        p = os.path.join(site, name)
        if os.path.exists(p):
            add(p, f"{SITE}/{name}", "daily", prio)
    return rows


def write(site: str = "/workspace/yesbro-site") -> None:
    cats = load_categories()
    # RSS first so sitemap can include feed URLs
    n_feeds = write_rss_feeds(site, cats)
    rows = collect_urls(site)
    write_sitemap_xml(site, rows)
    n_news = write_news_sitemap(site, cats)
    key = ensure_indexnow_key(site, cats)
    write_robots(site, key)
    write_llms(site, cats)
    print(
        f"wrote sitemap.xml ({len(rows)} URLs), news-sitemap.xml ({n_news}), "
        f"robots.txt, llms.txt, llms-full.txt, {n_feeds} RSS feeds"
        + (f", IndexNow key /{key}.txt" if key else "")
    )


if __name__ == "__main__":
    a = sys.argv[1:]
    write(a[a.index("--site") + 1] if "--site" in a else "/workspace/yesbro-site")
