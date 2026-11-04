#!/usr/bin/env python3
"""Ping IndexNow (Bing/Yandex/etc.) with today's changed paper URLs.

  python3 indexnow_ping.py [--site DIR]

Key is read from seo_categories.json site.indexnow_key, INDEXNOW_KEY env, or indexnow_key.txt.
No-op (exit 0) when key missing. Failures print but do not raise — publish should not block on Bing.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sys
import urllib.request
from pathlib import Path

SITE = "https://yesbrohq.com"
HOST = "yesbrohq.com"


def key_and_urls(site: Path) -> tuple[str | None, list[str]]:
    here = Path(__file__).resolve().parent
    cats = {}
    cp = here / "seo_categories.json"
    if cp.exists():
        cats = json.loads(cp.read_text(encoding="utf-8"))
    key = (
        os.environ.get("INDEXNOW_KEY")
        or (cats.get("site") or {}).get("indexnow_key")
        or ""
    ).strip()
    if not key and (here / "indexnow_key.txt").exists():
        key = (here / "indexnow_key.txt").read_text(encoding="utf-8").strip()
    if not key and (site / "indexnow-key.txt").exists():
        key = (site / "indexnow-key.txt").read_text(encoding="utf-8").strip()
    urls = [f"{SITE}/"]
    today = dt.date.today()
    cutoff = today - dt.timedelta(days=2)
    for idx in sorted(site.glob("*/index.html")):
        folder = idx.parent.name
        if folder in {"archive", "img", "data", "mypaper_src", "pipeline"}:
            continue
        urls.append(f"{SITE}/{folder}/")
        urls.append(f"{SITE}/{folder}/feed.xml")
        for a in sorted((idx.parent / "archive").glob("*.html")) if (idx.parent / "archive").exists() else []:
            try:
                d = dt.date.fromisoformat(a.stem[:10]) if len(a.stem) >= 10 else None
            except ValueError:
                d = None
            if d and d >= cutoff:
                urls.append(f"{SITE}/{folder}/archive/{a.name}")
    urls += [f"{SITE}/sitemap.xml", f"{SITE}/news-sitemap.xml", f"{SITE}/llms.txt"]
    # dedupe preserve order
    seen, out = set(), []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return (key or None), out


def ping(key: str, urls: list[str]) -> None:
    body = json.dumps({
        "host": HOST,
        "key": key,
        "keyLocation": f"{SITE}/{key}.txt",
        "urlList": urls[:10000],
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.indexnow.org/indexnow",
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            print(f"IndexNow {resp.status}: submitted {len(urls)} URLs")
    except Exception as ex:
        # 200/202 OK; some endpoints return 4xx on empty change — do not fail the job
        print(f"IndexNow ping note: {ex}")


def main() -> int:
    a = sys.argv[1:]
    site = Path(a[a.index("--site") + 1] if "--site" in a else "/workspace/yesbro-site")
    key, urls = key_and_urls(site)
    if not key:
        print("IndexNow: no key configured; skip")
        return 0
    # ensure key file exists on site
    (site / f"{key}.txt").write_text(key + "\n", encoding="utf-8")
    ping(key, urls)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
