#!/usr/bin/env python3
"""Emit per-paper section JSON for My Paper (/mypaper/).

  python3 build_mypaper_data.py [--date YYYY-MM-DD] [--site /workspace/yesbro-site]
                                [--stories-dir /workspace/yesbro]

Writes:
  <site>/data/<key>/latest.json   stories by section plus jobs, events, research, talks
  <site>/data/catalog.json        picker index of every topic id across papers

Wired into rebuild_today.sh so the nightly build refreshes these before 4 am IST.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import OrderedDict
from urllib.parse import urlparse

from columns import EDS

_PIPE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PIPE not in sys.path:
    sys.path.append(_PIPE)
import story_text

SITE_URL = "https://yesbrohq.com"


def slug(s: str) -> str:
    s = (s or "").lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "section"


def source_from_url(url: str) -> str:
    try:
        host = urlparse(url or "").netloc.lower()
    except Exception:
        return ""
    if host.startswith("www."):
        host = host[4:]
    return host


def load_json(path):
    if not path or not os.path.exists(path):
        return None
    try:
        return json.load(open(path, encoding="utf-8"))
    except Exception:
        return None


def stories_path(stories_dir, key, date):
    if key == "daily":
        p = os.path.join(stories_dir, f"stories_{date}.html.json")
        if os.path.exists(p):
            return p
        return os.path.join(stories_dir, f"stories_daily_{date}.html.json")
    return os.path.join(stories_dir, f"stories_{key}_{date}.html.json")


def side_path(stories_dir, kind, key, date):
    """jobs/events/research/talks file for a paper. Daily uses both naming styles."""
    cands = [os.path.join(stories_dir, f"{kind}_{key}_{date}.json")]
    if key == "daily":
        cands = [
            os.path.join(stories_dir, f"{kind}_daily_{date}.json"),
            os.path.join(stories_dir, f"{kind}_{date}.json"),
        ] + cands
    for p in cands:
        if os.path.exists(p):
            return p
    return None


def normalize_stories(raw):
    if not raw:
        return []
    if isinstance(raw, dict):
        raw = raw.get("stories") or raw.get("items") or []
    out = []
    for s in raw:
        if not isinstance(s, dict):
            continue
        title = s.get("headline") or s.get("title") or ""
        url = s.get("url") or s.get("link") or ""
        if not title or not url:
            continue
        img = s.get("image") or s.get("image_url") or ""
        out.append({
            "title": title,
            "summary": story_text.present_summary(s.get("summary") or s.get("dek") or "", title),
            "url": url,
            "image": img,
            "source": s.get("source") or source_from_url(url),
            "section": s.get("section") or "Other",
        })
    return out


def group_sections(stories, preferred):
    """Keep config section order, then any extras that appeared in the feed."""
    buckets = OrderedDict()
    for name in preferred or []:
        buckets[name] = []
    for s in stories:
        name = s["section"]
        buckets.setdefault(name, []).append(s)
    sections = []
    for name, items in buckets.items():
        if not items:
            continue
        clean = [{k: v for k, v in it.items() if k != "section"} for it in items]
        sections.append({"id": slug(name), "name": name, "stories": clean})
    return sections


def normalize_jobs(raw):
    if not raw:
        return []
    items = raw.get("jobs") if isinstance(raw, dict) else raw
    out = []
    for j in items or []:
        if not isinstance(j, dict):
            continue
        title = j.get("title") or ""
        url = j.get("url") or ""
        if not title or not url:
            continue
        out.append({
            "title": title,
            "org": j.get("org") or j.get("company") or "",
            "location": j.get("location") or "",
            "region": j.get("region") or "",
            "url": url,
            "source": j.get("source") or "",
            "posted": j.get("posted") or "",
        })
    return out


def normalize_events(raw):
    if not raw:
        return []
    items = raw.get("events") if isinstance(raw, dict) else raw
    out = []
    for e in items or []:
        if not isinstance(e, dict):
            continue
        name = e.get("name") or e.get("title") or ""
        url = e.get("url") or ""
        if not name:
            continue
        out.append({
            "name": name,
            "start": e.get("start") or "",
            "end": e.get("end") or "",
            "time": e.get("time") or "",
            "city": e.get("city") or "",
            "mode": e.get("mode") or "",
            "line": e.get("line") or e.get("summary") or "",
            "url": url,
            "region": e.get("region") or "",
        })
    return out


def normalize_research(raw):
    if not raw:
        return []
    items = raw.get("items") if isinstance(raw, dict) else raw
    out = []
    for r in items or []:
        if not isinstance(r, dict):
            continue
        title = r.get("title") or ""
        url = r.get("url") or ""
        if not title or not url:
            continue
        out.append({
            "title": title,
            "summary": r.get("summary") or "",
            "url": url,
            "source": r.get("source") or source_from_url(url),
            "kind": r.get("kind") or "",
            "date": r.get("date") or "",
        })
    return out


def normalize_talks(raw):
    if not raw:
        return []
    items = raw.get("talks") if isinstance(raw, dict) else (raw.get("items") if isinstance(raw, dict) else raw)
    out = []
    for t in items or []:
        if not isinstance(t, dict):
            continue
        title = t.get("title") or ""
        url = t.get("url") or ""
        if not title or not url:
            continue
        out.append({
            "title": title,
            "url": url,
            "channel": t.get("channel") or "",
            "duration": t.get("duration") or "",
            "note": t.get("note") or "",
            "thumb": t.get("thumb") or "",
        })
    return out


def paper_label(key):
    return EDS.get(key, (key, key.title()))[1]


def paper_folder(key):
    return EDS.get(key, (key, key))[0]


def config_sections(stories_dir, key):
    cfg = load_json(os.path.join(stories_dir, "editions", "config", f"{key}.json")) or {}
    return list(cfg.get("sections") or [])


def build_paper(stories_dir, key, date):
    preferred = config_sections(stories_dir, key)
    stories = normalize_stories(load_json(stories_path(stories_dir, key, date)))
    sections = group_sections(stories, preferred)
    jobs = normalize_jobs(load_json(side_path(stories_dir, "jobs", key, date)))
    events = normalize_events(load_json(side_path(stories_dir, "events", key, date)))
    research = normalize_research(load_json(side_path(stories_dir, "research", key, date)))
    talks = normalize_talks(load_json(side_path(stories_dir, "talks", key, date)))
    folder = paper_folder(key)
    return {
        "key": key,
        "label": paper_label(key),
        "date": date,
        "url": f"{SITE_URL}/{folder}/",
        "sections": sections,
        "jobs": jobs,
        "events": events,
        "research": research,
        "talks": talks,
    }


META = [
    ("events", "Events and Conferences", "events"),
    ("research", "Research and Development", "research"),
    ("talks", "Talks", "talks"),
    ("jobs", "Jobs", "jobs"),
]


def catalog_entry(paper):
    topics = []
    for sec in paper["sections"]:
        topics.append({
            "id": f"{paper['key']}.{sec['id']}",
            "name": sec["name"],
            "kind": "section",
            "count": len(sec["stories"]),
        })
    for mid, name, field in META:
        items = paper.get(field) or []
        if not items:
            continue
        topics.append({
            "id": f"{paper['key']}.{mid}",
            "name": name,
            "kind": mid,
            "count": len(items),
        })
    return {
        "key": paper["key"],
        "label": paper["label"],
        "date": paper["date"],
        "url": paper["url"],
        "data": f"/data/{paper['key']}/latest.json",
        "whole": f"{paper['key']}.*",
        "topics": topics,
    }


def latest_date(stories_dir):
    """Pick the newest date that has a daily html.json, else today files for any paper."""
    dates = set()
    for name in os.listdir(stories_dir):
        m = re.match(r"stories_(?:[a-z]+_)?(\d{4}-\d{2}-\d{2})\.html\.json$", name)
        if m:
            dates.add(m.group(1))
        m = re.match(r"stories_(\d{4}-\d{2}-\d{2})\.html\.json$", name)
        if m:
            dates.add(m.group(1))
    return max(dates) if dates else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None)
    ap.add_argument("--site", default="/workspace/yesbro-site")
    ap.add_argument("--stories-dir", default=os.path.dirname(os.path.abspath(__file__)))
    a = ap.parse_args()
    date = a.date or latest_date(a.stories_dir)
    if not date:
        raise SystemExit("no stories_*.html.json found, pass --date")

    data_root = os.path.join(a.site, "data")
    os.makedirs(data_root, exist_ok=True)

    # Daily first, then EDS order
    keys = ["daily"] + [k for k in EDS if k != "daily"]
    catalog = {"date": date, "papers": []}
    written = 0
    for key in keys:
        sp = stories_path(a.stories_dir, key, date)
        if not os.path.exists(sp):
            # still emit empty shell if config exists so picker can list sections next run
            if not os.path.exists(os.path.join(a.stories_dir, "editions", "config", f"{key}.json")):
                continue
        paper = build_paper(a.stories_dir, key, date)
        out_dir = os.path.join(data_root, key)
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "latest.json")
        json.dump(paper, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
        catalog["papers"].append(catalog_entry(paper))
        written += 1
        n_sto = sum(len(s["stories"]) for s in paper["sections"])
        print(f"  {key}: {len(paper['sections'])} sections, {n_sto} stories, "
              f"jobs {len(paper['jobs'])}, events {len(paper['events'])}, "
              f"research {len(paper['research'])}, talks {len(paper['talks'])}")

    cat_path = os.path.join(data_root, "catalog.json")
    json.dump(catalog, open(cat_path, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    n_topics = sum(len(p["topics"]) for p in catalog["papers"])
    print(f"wrote {written} papers to {data_root}/ ({n_topics} topics), catalog {cat_path}, date {date}")


if __name__ == "__main__":
    main()
