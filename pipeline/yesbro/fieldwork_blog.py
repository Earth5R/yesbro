#!/usr/bin/env python3
"""From the FIELDWORK Blog for Yes Bro Schools.

  python3 fieldwork_blog.py --date YYYY-MM-DD -> fieldwork_blog_schools_YYYY-MM-DD.json

Pulls real Earth5R posts useful to school students (university applications, profile building,
research programmes, careers, climate work). Summaries from the post. Never calls FIELDWORK an
internship. Earth5R is never an NGO. Rotates 3 to 5 posts via fieldwork_blog/seen.json.
"""
import argparse, datetime as dt, html, json, os, re, sys
from concurrent.futures import ThreadPoolExecutor
import requests
import blocklist

HERE = os.path.dirname(os.path.abspath(__file__))
SEEN = os.path.join(HERE, "fieldwork_blog", "seen.json")
UA = {"User-Agent": "Mozilla/5.0 (compatible; YesBroFieldwork/1.0)", "Accept-Language": "en"}
CAP = 5
BAD = re.compile(r"[\u2014\u2013;]")
INTERN = re.compile(r"\bintern(s|ship|ships)?\b", re.I)
NGO = re.compile(r"\bNGOs?\b", re.I)

# Curated student-facing Earth5R posts (official pages). Order is preference; seen rotates.
POOL = [
  "https://earth5r.org/research-programs-for-high-school-students/",
  "https://earth5r.org/college-essay-examples-climate-community-work/",
  "https://earth5r.org/recommendation-letter-climate-work-mentor/",
  "https://earth5r.org/what-is-a-fellowship-9-reasons-to-consider-a-fellowship/",
  "https://earth5r.org/preparing-for-a-career-in-sustainability-essential-skills-and-experiences/",
  "https://earth5r.org/career-opportunities-in-the-climate-change-and-sustainability-sector/",
  "https://earth5r.org/building-a-sustainable-future-insights-from-the-sustainability-career-launchpad-episode-3/",
  "https://earth5r.org/future-proofing-indias-youth-earth5rs-sustainability-skill-training-model/",
  "https://earth5r.org/creating-green-jobs-through-circular-economy-earth5rs-youth-focused-framework/",
  "https://earth5r.org/attention-harvest-dopamine-platforms-india-teenage-sustainability/",
]

def tidy(s):
    s = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", s or "")
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    s = re.sub(r"\s*[\u2013\u2014]\s*", ", ", s).replace(";", ",")
    return re.sub(r"\s+", " ", s).strip(" ,")

def load_seen():
    try: return list(json.load(open(SEEN)))
    except Exception: return []

def save_seen(s):
    os.makedirs(os.path.dirname(SEEN), exist_ok=True)
    json.dump(s[-500:], open(SEEN, "w"), indent=0)

def fetch(url):
    try:
        r = requests.get(url, headers=UA, timeout=25)
        if r.status_code != 200: return None
        t = r.text
        title = ""
        m = re.search(r'property="og:title" content="([^"]+)"', t) or re.search(r"<title>(.*?)</title>", t, re.S)
        if m: title = tidy(m[1]).split("|")[0].split("- Earth")[0].strip()
        desc = ""
        m = re.search(r'property="og:description" content="([^"]+)"', t)
        if m: desc = tidy(m[1])
        if len((desc or "").split()) < 30:
            paras = re.findall(r"<p[^>]*>(.*?)</p>", t, re.S)
            for p in paras:
                d = tidy(p)
                low = d.lower()
                if len(d.split()) < 30: continue
                if low.startswith("cookie") or "what we do" in low or "terra climate" in low: continue
                if low.count("http") > 2: continue
                desc = d; break
        if not title or not desc: return None
        # Soft-clean SEO wording without dropping the post
        title = INTERN.sub("programme", title); desc = INTERN.sub("programme", desc)
        title = NGO.sub("organisation", title); desc = NGO.sub("organisation", desc)
        title = BAD.sub(",", title); desc = BAD.sub(",", desc)
        title = re.sub(r"\s+", " ", title).strip(" ,")
        desc = re.sub(r"\s+", " ", desc).strip(" ,")
        words = desc.split()
        if len(words) > 48: desc = " ".join(words[:48]).rstrip(",.") + "."
        if len(desc.split()) < 22:
            # pad carefully from title
            desc = (desc.rstrip(".") + ". " + title).strip()
            words = desc.split()
            if len(words) > 50: desc = " ".join(words[:50]).rstrip(",.") + "."
        if len(desc.split()) < 22 or INTERN.search(title + " " + desc): return None
        return {"title": title[:140], "url": url, "summary": desc, "source": "Earth5R"}
    except Exception as e:
        print("fail", url, e); return None

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--date", default=dt.date.today().isoformat())
    a = ap.parse_args()
    seen = load_seen()
    seen_set = set(seen)
    # prefer unseen
    order = [u for u in POOL if u not in seen_set] + [u for u in POOL if u in seen_set]
    with ThreadPoolExecutor(6) as ex:
        got = list(ex.map(fetch, order))
    items = []
    for u, it in zip(order, got):
        if not it: continue
        items.append(it)
        if u not in seen_set: seen.append(u); seen_set.add(u)
        if len(items) >= CAP: break
    _bl = {}
    items = blocklist.keep(items, "fieldwork_blog", _bl)
    if _bl: blocklist.log(_bl)
    path = os.path.join(HERE, f"fieldwork_blog_schools_{a.date}.json")
    json.dump({"date": a.date, "edition": "schools", "items": items}, open(path, "w"), indent=1, ensure_ascii=False)
    save_seen(seen)
    print("fieldwork_blog", len(items), [i["title"][:40] for i in items])

if __name__ == "__main__":
    main()
