#!/usr/bin/env python3
"""Enrich existing paper index.html <head> tags with category SEO/AEO.

Invisible only: title, meta, link[rel=alternate], JSON-LD. Does not touch <body>.
  python3 enrich_seo.py [--site DIR] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SITE = "https://yesbrohq.com"


def load_cats(root: Path) -> dict:
    p = root / "seo_categories.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"papers": {}}


def meta_for_folder(cats: dict, folder: str) -> dict | None:
    for key, meta in (cats.get("papers") or {}).items():
        if meta.get("folder") == folder or key == folder:
            return {**meta, "key": key}
    return None


def replace_or_insert_meta(head: str, attr: str, value: str, prop: bool = False) -> str:
    """Replace content of a meta tag matched by name= or property=, or insert before </head>."""
    key = "property" if prop else "name"
    pat = re.compile(
        rf'<meta\s+{key}="{re.escape(attr)}"\s+content="[^"]*"\s*/?>',
        re.I,
    )
    tag = f'<meta {key}="{attr}" content="{_esc(value)}">'
    if pat.search(head):
        return pat.sub(tag, head, count=1)
    # also try reverse attribute order
    pat2 = re.compile(
        rf'<meta\s+content="[^"]*"\s+{key}="{re.escape(attr)}"\s*/?>',
        re.I,
    )
    if pat2.search(head):
        return pat2.sub(tag, head, count=1)
    return head.rstrip() + "\n" + tag + "\n"


def _esc(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def extract_stories(html: str, limit: int = 25) -> list[dict]:
    stories = []
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', html, re.S | re.I):
        try:
            data = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict) or data.get("@type") != "CollectionPage":
            continue
        main = data.get("mainEntity") or {}
        for it in main.get("itemListElement") or []:
            if isinstance(it, dict) and it.get("url") and it.get("name"):
                stories.append({"headline": it["name"], "url": it["url"]})
        if stories:
            return stories[:limit]
    return stories


def build_jsonld(meta: dict, folder: str, stories: list[dict], iso: str, no_earth5r: bool) -> tuple[dict, dict]:
    title = meta.get("title") or meta.get("name") or folder
    desc = meta.get("description") or ""
    about = meta.get("about") or desc
    keywords = meta.get("keywords") or []
    if folder == "healing" or meta.get("key") == "healing":
        def _scrub(s):
            if not isinstance(s, str) or not s:
                return s
            s = re.sub(r"(?i)\bEarth5R\b", "the publisher", s)
            s = re.sub(r"(?i)\bFIELDWORK\b", "the house programme", s)
            s = re.sub(r"(?i)earth5r\.org[^\s\"']*", "yesbrohq.com", s)
            return s
        title, desc, about = _scrub(title), _scrub(desc), _scrub(about)
        keywords = [_scrub(k) for k in keywords]
        meta = {**meta, "title": title, "description": desc, "about": about, "keywords": keywords}
    genre = meta.get("genre") or []
    url = f"{SITE}/{folder}/"
    name = meta.get("name") or title
    items, articles, pos = [], [], 0
    for st in stories:
        pos += 1
        items.append({"@type": "ListItem", "position": pos, "url": st["url"], "name": st["headline"]})
        art = {
            "@type": "NewsArticle",
            "headline": st["headline"],
            "url": st["url"],
            "datePublished": iso,
            "isAccessibleForFree": True,
            "inLanguage": "en",
            "isPartOf": {"@type": "Periodical", "name": name, "url": url},
            "publisher": {"@type": "Organization", "name": "Yes Bro", "url": SITE + "/"},
        }
        if keywords:
            art["keywords"] = keywords
        if genre:
            art["genre"] = genre
        if about:
            art["about"] = {"@type": "Thing", "name": name, "description": about}
        articles.append(art)
    publisher = {
        "@type": "Organization",
        "name": "Yes Bro",
        "url": SITE + "/",
        "logo": {"@type": "ImageObject", "url": SITE + "/icon-512.png"},
        "parentOrganization": {"@type": "Organization", "name": "Earth5R", "url": "https://earth5r.org/"},
    }
    if no_earth5r:
        publisher.pop("parentOrganization", None)
    ld = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": title,
        "url": url,
        "description": desc,
        "abstract": about,
        "inLanguage": "en",
        "dateModified": iso,
        "isAccessibleForFree": True,
        "isPartOf": {"@type": "WebSite", "name": "Yes Bro", "url": SITE + "/"},
        "publisher": publisher,
        "mainEntity": {"@type": "ItemList", "name": f"{name} top stories", "itemListElement": items},
        "hasPart": articles,
    }
    if keywords:
        ld["keywords"] = keywords
    if genre:
        ld["genre"] = genre
    if about:
        ld["about"] = {"@type": "Thing", "name": name, "description": about}
    crumbs = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Yes Bro", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": name, "item": url},
        ],
    }
    return ld, crumbs


def enrich_file(path: Path, meta: dict, dry: bool) -> bool:
    html = path.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"(.*?<head[^>]*>)(.*?)(</head>)(.*)", html, re.S | re.I)
    if not m:
        return False
    pre, head, head_close, post = m.group(1), m.group(2), m.group(3), m.group(4)
    folder = path.parent.name
    title = meta.get("title") or meta.get("name") or folder
    desc = meta.get("description") or ""
    about = meta.get("about") or desc
    keywords = meta.get("keywords") or []
    # title
    if re.search(r"<title>.*?</title>", head, re.S | re.I):
        head = re.sub(r"<title>.*?</title>", f"<title>{_esc(title)}</title>", head, count=1, flags=re.S | re.I)
    else:
        head = f"<title>{_esc(title)}</title>\n" + head
    head = replace_or_insert_meta(head, "description", desc)
    if keywords:
        head = replace_or_insert_meta(head, "keywords", ", ".join(keywords))
    if about:
        head = replace_or_insert_meta(head, "abstract", about)
    head = replace_or_insert_meta(head, "og:title", title, prop=True)
    head = replace_or_insert_meta(head, "og:description", desc, prop=True)
    head = replace_or_insert_meta(head, "twitter:title", title)
    head = replace_or_insert_meta(head, "twitter:description", desc)
    feed = f"{SITE}/{folder}/feed.xml"
    rss_tag = f'<link rel="alternate" type="application/rss+xml" title="{_esc(title)}" href="{feed}">'
    if 'type="application/rss+xml"' not in head:
        head = head.rstrip() + "\n" + rss_tag + "\n"
    else:
        head = re.sub(
            r'<link[^>]+type="application/rss\+xml"[^>]*>',
            rss_tag,
            head,
            count=1,
            flags=re.I,
        )
    # date from existing JSON-LD or today
    iso_m = re.search(r'"dateModified":\s*"(\d{4}-\d{2}-\d{2})', html) or re.search(
        r'"datePublished":\s*"(\d{4}-\d{2}-\d{2})', html
    )
    iso = iso_m.group(1) if iso_m else __import__("datetime").date.today().isoformat()
    stories = extract_stories(html)
    no_earth5r = "healing" in folder or '"no_earth5r": true' in html.lower()
    # healing config flag — check config
    if folder == "healing":
        no_earth5r = True
    ld, crumbs = build_jsonld(meta, folder, stories, iso, no_earth5r)

    # Remove existing CollectionPage and BreadcrumbList JSON-LD scripts, then insert fresh ones
    def drop_ld(h: str, type_name: str) -> str:
        out = h
        for mm in list(re.finditer(r'<script type="application/ld\+json">(.*?)</script>', h, re.S | re.I)):
            try:
                data = json.loads(mm.group(1))
            except json.JSONDecodeError:
                continue
            types = data.get("@type") if isinstance(data, dict) else None
            if types == type_name or (isinstance(types, list) and type_name in types):
                out = out.replace(mm.group(0), "", 1)
        return out

    head = drop_ld(head, "CollectionPage")
    head = drop_ld(head, "BreadcrumbList")
    head = (
        head.rstrip()
        + "\n<script type=\"application/ld+json\">"
        + json.dumps(ld, ensure_ascii=False)
        + "</script>\n"
        + "<script type=\"application/ld+json\">"
        + json.dumps(crumbs, ensure_ascii=False)
        + "</script>\n"
    )
    new_html = pre + head + head_close + post
    if new_html == html:
        return False
    # Safety: body must be unchanged
    body_old = re.search(r"<body[^>]*>.*</body>", html, re.S | re.I)
    body_new = re.search(r"<body[^>]*>.*</body>", new_html, re.S | re.I)
    if body_old and body_new and body_old.group(0) != body_new.group(0):
        raise RuntimeError(f"body changed unexpectedly in {path}")
    if not dry:
        path.write_text(new_html, encoding="utf-8")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", default="/workspace/yesbro-site")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    site = Path(a.site)
    cats = load_cats(Path(__file__).resolve().parent)
    n = 0
    for idx in sorted(site.glob("*/index.html")):
        folder = idx.parent.name
        if folder in {"archive", "img", "data", "mypaper_src", "pipeline"}:
            continue
        meta = meta_for_folder(cats, folder)
        if not meta:
            print("no category meta for", folder)
            continue
        if enrich_file(idx, meta, a.dry_run):
            print(("would enrich" if a.dry_run else "enriched"), folder)
            n += 1
        else:
            print("unchanged", folder)
    print(f"done: {n} papers")
    return 0


if __name__ == "__main__":
    sys.exit(main())
