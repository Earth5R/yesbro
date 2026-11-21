"""Live papers that absorb other edition keys. Config is the source of truth.

A config with merge_sources is the paper that gets built. Keys listed there, other than
the live key, are retired: their feeds, jobs, events and research fold into the live paper.
"""
from __future__ import annotations
import json
from pathlib import Path

def config_dir() -> Path:
    return Path(__file__).resolve().parent / "editions" / "config"

def specs() -> list[dict]:
    out = []
    for p in sorted(config_dir().glob("*.json")):
        try:
            c = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if c.get("merge_sources") and c.get("key"):
            out.append(c)
    return out

def by_key() -> dict:
    return {c["key"]: c for c in specs()}

def sources_of(key: str) -> list[str]:
    c = by_key().get(key)
    if not c:
        return [key]
    srcs = [s for s in c.get("merge_sources") or [] if s]
    return srcs or [key]

def retired_keys() -> set[str]:
    gone = set()
    for c in specs():
        live = c["key"]
        for src in c.get("merge_sources") or []:
            if src != live:
                gone.add(src)
        for r in c.get("redirects") or []:
            if r != live:
                gone.add(r)
    return gone

def apply_feeds(feeds: dict) -> dict:
    """Point the live key at the union of source feed URLs. Drop retired keys."""
    retired = set()
    for c in specs():
        target = c["key"]
        urls = []
        for src in sources_of(target):
            for u in feeds.get(src) or []:
                if u not in urls:
                    urls.append(u)
            if src != target:
                retired.add(src)
        if urls:
            feeds[target] = urls
    for k in retired:
        feeds.pop(k, None)
    return feeds

def trim_picks(picks: dict, cfg: dict, per_section: int) -> dict:
    """Dedupe across sections, cap each section, then cap the paper. Lead sections win."""
    sections = list(cfg.get("sections") or picks.keys())
    tail = set(cfg.get("tail_sections") or [])
    default = int(cfg.get("per_section") or per_section)
    tail_n = cfg.get("tail_per_section")
    seen, out = set(), {}
    for sec in sections:
        ids = []
        for i in picks.get(sec) or []:
            if i in seen:
                continue
            seen.add(i)
            ids.append(i)
        n = int(tail_n) if (sec in tail and tail_n is not None) else default
        if ids:
            out[sec] = ids[:n]
    max_stories = cfg.get("max_stories")
    if not max_stories:
        return out
    kept, left = {}, int(max_stories)
    for sec in sections:
        if left <= 0:
            break
        ids = out.get(sec) or []
        take = ids[:left]
        if take:
            kept[sec] = take
            left -= len(take)
    return kept
