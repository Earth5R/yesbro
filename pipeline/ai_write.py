"""Gemini-backed picks and copy for Yes Bro. Memes default to templates to save quota."""
from __future__ import annotations
import json, os, re, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROMPTS = HERE / "prompts"

def _read(name: str) -> str:
    return (PROMPTS / name).read_text(encoding="utf-8")

def _voice() -> str:
    return _read("VOICE.md")

def _system(extra: str) -> str:
    return _voice() + "\n\n" + extra

def write_picks(ed: str, sections: list[str], titles_lines: list[str], *, per_section: int = 10) -> dict:
    """One Gemini call for the whole paper. Return {section: [ids...]}."""
    from gemini_client import available, generate_json
    lines = titles_lines[:350]
    if not available():
        return _fallback_picks(sections, lines, per_section)
    prompt = (
        _read("picks.txt")
        + f"\n\nPaper key: {ed}\nSections in order:\n"
        + "\n".join(f"- {s}" for s in sections)
        + f"\n\nAim for about {per_section} ids per section.\nCandidates:\n"
        + "\n".join(lines)
    )
    try:
        data = generate_json(prompt, system=_system("Return JSON object only."), temperature=0.2)
        time.sleep(1.2)
    except Exception as e:
        print(f"picks failed for {ed}: {e}", flush=True)
        return _fallback_picks(sections, lines, per_section)
    out = {}
    valid = set()
    for ln in lines:
        try:
            valid.add(int(ln.split("|", 1)[0]))
        except Exception:
            pass
    for sec in sections:
        ids = []
        for x in (data.get(sec) or []):
            try:
                i = int(x)
            except Exception:
                continue
            if i in valid and i not in ids:
                ids.append(i)
        if not ids:
            ids = _fallback_picks([sec], lines, per_section).get(sec, [])
        out[sec] = ids[: max(per_section + 2, 12)]
    return out

def _fallback_picks(sections: list[str], lines: list[str], per_section: int) -> dict:
    ids = []
    for ln in lines:
        try:
            ids.append(int(ln.split("|", 1)[0]))
        except Exception:
            pass
    out = {}
    if not sections:
        return out
    chunk = max(per_section, 8)
    for n, sec in enumerate(sections):
        start = (n * chunk) % max(len(ids), 1)
        take = ids[start:start + chunk] or ids[:chunk]
        out[sec] = list(dict.fromkeys(take))[:chunk]
    return out

def write_copy(ed: str, items: list[dict]) -> dict:
    """items: [{id, title, text}]. Return {id: (headline, summary)}.
    Uses large batches (up to 20) to stay inside free-tier request limits.
    """
    from gemini_client import available, generate_json
    if not items:
        return {}
    if not available():
        return _fallback_copy(items)
    out = {}
    batch = int(os.environ.get("YESBRO_COPY_BATCH", "18"))
    for i in range(0, len(items), batch):
        chunk = items[i:i + batch]
        blob = []
        for it in chunk:
            tx = re.sub(r"\s+", " ", (it.get("text") or ""))[:700]
            blob.append(f"ID {it['id']}\nTITLE: {it.get('title','')}\nTEXT: {tx}\n")
        prompt = _read("copy.txt") + "\n\nPaper: " + ed + "\n\n" + "\n".join(blob)
        try:
            data = generate_json(prompt, system=_system("Return JSON only with a stories array."), temperature=0.35)
            time.sleep(1.5)
            for row in data.get("stories") or []:
                try:
                    iid = int(row["id"])
                except Exception:
                    continue
                h = _clean(str(row.get("headline") or ""))
                s = _clean(str(row.get("summary") or ""))
                if h and s:
                    out[iid] = (h, s)
        except Exception as e:
            print(f"copy batch failed for {ed}: {e}", flush=True)
            out.update(_fallback_copy(chunk))
    missing = [it for it in items if int(it["id"]) not in out]
    if missing:
        out.update(_fallback_copy(missing))
    return out

def _clean(t: str) -> str:
    t = t.replace("\u2014", ",").replace("\u2013", " to ").replace(";", ",")
    t = re.sub(r"\s+", " ", t).strip()
    return t

def _fallback_copy(items: list[dict]) -> dict:
    out = {}
    for it in items:
        title = _clean(it.get("title") or "Untitled")
        tx = _clean(it.get("text") or it.get("title") or "")
        words = tx.split()
        if len(words) < 30:
            summary = (tx + " The full piece is for subscribers, and the headline is all that is public for now.").strip()
        else:
            summary = " ".join(words[:45])
        sw = summary.split()
        if len(sw) < 30:
            summary = summary + " Further details were not available in the open teaser."
            sw = summary.split()
        summary = " ".join(sw[:50])
        out[int(it["id"])] = (title[:120], _clean(summary))
    return out

def write_meme(ed: str, stories: list[dict], date: str, prefer_format: str | None = None) -> dict | None:
    """Template meme only by default (YESBRO_AI_MEMES=1 to call Gemini)."""
    skip = re.compile(r"(?i)politic|policy|regulation|safety|mental health|alternative")
    cand = [s for s in stories if not skip.search(s.get("section", ""))] or list(stories)
    if not cand:
        return None
    # Prefer a mid-list story so the meme is not always the lead politics/business piece.
    story = cand[min(len(cand)//3, len(cand)-1)]
    use_ai = os.environ.get("YESBRO_AI_MEMES", "").strip() in ("1", "true", "yes")
    if not use_ai:
        return {
            "format": prefer_format or "classic",
            "url": story["url"],
            "top": "Reading Yes Bro",
            "bottom": "Still free, still printed in HTML",
        }
    from gemini_client import available, generate_json
    if not available():
        return {
            "format": "classic",
            "url": story["url"],
            "top": "Reading Yes Bro",
            "bottom": "Still free, still printed in HTML",
        }
    brief = {"url": story["url"], "headline": story.get("headline"), "summary": story.get("summary"), "section": story.get("section")}
    prompt = _read("meme.txt") + "\n\nPaper: " + ed + "\nDate: " + date + "\nStory:\n" + json.dumps(brief)
    try:
        data = generate_json(prompt, system=_system("Return one JSON object only."), temperature=0.5)
        time.sleep(1.0)
        if isinstance(data, dict) and data.get("format"):
            data["url"] = story["url"]
            return data
    except Exception as e:
        print(f"meme failed for {ed}: {e}", flush=True)
    return {"format": "classic", "url": story["url"], "top": "Reading Yes Bro", "bottom": "Still free, still printed in HTML"}

def write_column_md(ed: str, date: str, sources: list[dict], title_hint: str = "") -> str | None:
    if os.environ.get("YESBRO_AI_COLUMNS", "0").strip() not in ("1", "true", "yes"):
        return None
    from gemini_client import available, generate
    if not available() or not sources:
        return None
    prompt = (
        _read("column.txt")
        + f"\n\nPaper key: {ed}\nDate: {date}\nTitle hint: {title_hint or 'pick a timely explainable topic'}\nSources:\n"
        + "\n".join(f"- {s.get('title')}: {s.get('url')}\n  note: {s.get('summary','')}" for s in sources[:8])
    )
    try:
        text = generate(prompt, system=_system("Return markdown with YAML front matter only."), temperature=0.4)
        time.sleep(1.5)
        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:markdown|md)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        if "---" in text[:20] and "slug:" in text:
            return text
    except Exception as e:
        print(f"column failed for {ed}: {e}", flush=True)
    return None
