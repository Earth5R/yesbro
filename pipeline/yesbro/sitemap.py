#!/usr/bin/env python3
"""Write sitemap.xml and robots.txt for yesbrohq.com.

  python3 sitemap.py [--site /workspace/yesbro-site]

Covers the landing page, every paper (<folder>/index.html), its back issues (<folder>/archive/*.html),
and Yes Bro Explains (<folder>/explains/ and each column). Root archive/ holds old redirect stubs and is skipped.
lastmod comes from the page's JSON-LD dateModified/datePublished, an archive file name, or today.
Run it after every publish: build_landing.py (8 am run), publish.py (editions) and columns.py publish all call it.
"""
import datetime, glob, os, re, sys

SITE = "https://yesbrohq.com"

def lastmod(path):
    m = re.search(r"(\d{4}-\d{2}-\d{2})\.html$", path)
    if m:
        return m.group(1)
    t = open(path, encoding="utf-8", errors="ignore").read(200000)
    m = re.search(r'"dateModified":\s*"(\d{4}-\d{2}-\d{2})', t) or re.search(r'"datePublished":\s*"(\d{4}-\d{2}-\d{2})', t)
    return m.group(1) if m else datetime.date.today().isoformat()

def write(site="/workspace/yesbro-site"):
    rows = []
    def add(path, loc, freq, prio):
        rows.append((loc, lastmod(path), freq, prio))
    add(os.path.join(site, "index.html"), SITE + "/", "daily", "1.0")
    for idx in sorted(glob.glob(os.path.join(site, "*", "index.html"))):
        folder = os.path.basename(os.path.dirname(idx))
        if folder in ("archive", "img", "data", "mypaper_src"):
            continue
        add(idx, f"{SITE}/{folder}/", "daily", "0.9")
        ex = os.path.join(site, folder, "explains", "index.html")
        if os.path.exists(ex):
            add(ex, f"{SITE}/{folder}/explains/", "weekly", "0.7")
            for col in sorted(glob.glob(os.path.join(site, folder, "explains", "*", "index.html"))):
                add(col, f"{SITE}/{folder}/explains/{os.path.basename(os.path.dirname(col))}/", "monthly", "0.8")
        for a in sorted(glob.glob(os.path.join(site, folder, "archive", "*.html")), reverse=True):
            add(a, f"{SITE}/{folder}/archive/{os.path.basename(a)}", "never", "0.4")
    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, lm, f, p in rows:
        xml.append(f"  <url><loc>{loc}</loc><lastmod>{lm}</lastmod><changefreq>{f}</changefreq><priority>{p}</priority></url>")
    xml.append("</urlset>")
    open(os.path.join(site, "sitemap.xml"), "w").write("\n".join(xml) + "\n")
    open(os.path.join(site, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")
    print(f"wrote sitemap.xml ({len(rows)} URLs) and robots.txt")

if __name__ == "__main__":
    a = sys.argv[1:]
    write(a[a.index("--site") + 1] if "--site" in a else "/workspace/yesbro-site")
