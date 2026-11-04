#!/usr/bin/env python3
"""Research and Development for every Yes Bro paper.

  python3 research.py --date YYYY-MM-DD [ed ...]  -> research_<ed>_YYYY-MM-DD.json

Pulls recent papers and lab notes from arXiv, ScienceDaily topic feeds, Nature RSS and a few
field feeds. India first where the source supports it. Summaries are 30 to 50 words from the
abstract or press release only. Preprints are labelled. Findings are never overstated.
Dedupes against research/seen.json so the same paper does not keep coming back.
"""
import argparse, datetime as dt, html, json, os, re, sys
from concurrent.futures import ThreadPoolExecutor
import feedparser, requests
import blocklist

HERE = os.path.dirname(os.path.abspath(__file__))
EDS = ["daily","ux","arch","schools","sustainability","startups","highered","consulting","health",
       "marketing","finance","aviation","business","healing","ai","packaging","fashion","realestate","auto"]
UA = {"User-Agent": "Mozilla/5.0 (compatible; YesBroResearch/1.0)", "Accept-Language": "en"}
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
CAP = 8
SEEN = os.path.join(HERE, "research", "seen.json")
BAD = re.compile(r"[\u2014\u2013;]")
INTERN = re.compile(r"\bintern(s|ship|ships)?\b", re.I)
POL = re.compile(r"\b(election|vote|voter|parliament|minister|war|gaza|ukraine|religion|hindu|muslim|christian)\b", re.I)

# Per-edition feed list: (url, source_label, kind_hint). kind_hint is preprint|journal|press.
FEEDS = {
 "schools": [
  ("https://feeds.nature.com/natindia/rss/current", "Nature India", "journal"),
  ("https://www.sciencedaily.com/rss/mind_brain/child_development.xml", "ScienceDaily", "press"),
  ("https://www.sciencedaily.com/rss/mind_brain/language_acquisition.xml", "ScienceDaily", "press"),
  ("https://www.sciencedaily.com/rss/mind_brain/learning_disorders.xml", "ScienceDaily", "press"),
  ("https://www.nature.com/nathumbehav.rss", "Nature Human Behaviour", "journal"),
  ("https://rss.arxiv.org/rss/cs.CY", "arXiv", "preprint"),
 ],
 "packaging": [
  ("https://www.sciencedaily.com/rss/earth_climate/recycling_and_waste.xml", "ScienceDaily", "press"),
  ("https://www.sciencedaily.com/rss/matter_energy/materials_science.xml", "ScienceDaily", "press"),
  ("https://rss.arxiv.org/rss/cond-mat.soft", "arXiv", "preprint"),
  ("https://rss.arxiv.org/rss/physics.chem-ph", "arXiv", "preprint"),
 ],
 "fashion": [
  ("https://www.sciencedaily.com/rss/matter_energy/materials_science.xml", "ScienceDaily", "press"),
  ("https://rss.arxiv.org/rss/cs.CV", "arXiv", "preprint"),
  ("https://www.sciencedaily.com/rss/matter_energy/nanotechnology.xml", "ScienceDaily", "press"),
 ],
 "daily": [
  ("https://feeds.nature.com/natindia/rss/current", "Nature India", "journal"),
  ("https://www.thehindu.com/sci-tech/science/feeder/default.rss", "The Hindu Science", "press"),
  ("https://indianexpress.com/section/technology/science/feed/", "Indian Express Science", "press"),
  ("https://www.sciencedaily.com/rss/top.xml", "ScienceDaily", "press"),
  ("https://www.nature.com/nature.rss", "Nature", "journal"),
  ("https://rss.arxiv.org/rss/cs.AI", "arXiv", "preprint"),
 ],
 "ai": [
  ("https://feeds.nature.com/natindia/rss/current", "Nature India", "journal"),
  ("https://rss.arxiv.org/rss/cs.AI", "arXiv", "preprint"),
  ("https://rss.arxiv.org/rss/cs.LG", "arXiv", "preprint"),
  ("https://rss.arxiv.org/rss/cs.CL", "arXiv", "preprint"),
  ("https://www.sciencedaily.com/rss/computers_math/artificial_intelligence.xml", "ScienceDaily", "press"),
 ],
 "ux": [
  ("https://rss.arxiv.org/rss/cs.HC", "arXiv", "preprint"),
  ("https://www.sciencedaily.com/rss/computers_math/computer_science.xml", "ScienceDaily", "press"),
 ],
 "arch": [
  ("https://www.sciencedaily.com/rss/earth_climate/environmental_science.xml", "ScienceDaily", "press"),
  ("https://www.sciencedaily.com/rss/matter_energy/materials_science.xml", "ScienceDaily", "press"),
  ("https://rss.arxiv.org/rss/physics.soc-ph", "arXiv", "preprint"),
 ],
 "health": [
  ("https://feeds.nature.com/natindia/rss/current", "Nature India", "journal"),
  ("https://www.thehindu.com/sci-tech/science/feeder/default.rss", "The Hindu Science", "press"),
  ("https://www.sciencedaily.com/rss/health_medicine.xml", "ScienceDaily", "press"),
  ("https://www.nature.com/nm.rss", "Nature Medicine", "journal"),
 ],
 "healing": [
  ("https://feeds.nature.com/natindia/rss/current", "Nature India", "journal"),
  ("https://www.thehindu.com/sci-tech/science/feeder/default.rss", "The Hindu Science", "press"),
  ("https://www.sciencedaily.com/rss/mind_brain.xml", "ScienceDaily", "press"),
  ("https://www.sciencedaily.com/rss/health_medicine/nutrition.xml", "ScienceDaily", "press"),
  ("https://www.sciencedaily.com/rss/mind_brain/sleep.xml", "ScienceDaily", "press"),
 ],
 "sustainability": [
  ("https://feeds.nature.com/natindia/rss/current", "Nature India", "journal"),
  ("https://www.thehindu.com/sci-tech/science/feeder/default.rss", "The Hindu Science", "press"),
  ("https://www.sciencedaily.com/rss/earth_climate/climate.xml", "ScienceDaily", "press"),
  ("https://www.sciencedaily.com/rss/earth_climate/recycling_and_waste.xml", "ScienceDaily", "press"),
  ("https://rss.arxiv.org/rss/physics.ao-ph", "arXiv", "preprint"),
 ],
 "finance": [
  ("https://rss.arxiv.org/rss/q-fin.GN", "arXiv", "preprint"),
  ("https://rss.arxiv.org/rss/econ.GN", "arXiv", "preprint"),
  ("https://www.sciencedaily.com/rss/science_society/economics.xml", "ScienceDaily", "press"),
 ],
 "business": [
  ("https://www.sciencedaily.com/rss/science_society/economics.xml", "ScienceDaily", "press"),
  ("https://rss.arxiv.org/rss/econ.GN", "arXiv", "preprint"),
 ],
 "startups": [
  ("https://rss.arxiv.org/rss/cs.AI", "arXiv", "preprint"),
  ("https://www.sciencedaily.com/rss/computers_math/artificial_intelligence.xml", "ScienceDaily", "press"),
 ],
 "marketing": [
  ("https://rss.arxiv.org/rss/cs.SI", "arXiv", "preprint"),
  ("https://www.sciencedaily.com/rss/science_society/economics.xml", "ScienceDaily", "press"),
 ],
 "consulting": [
  ("https://rss.arxiv.org/rss/econ.GN", "arXiv", "preprint"),
  ("https://www.sciencedaily.com/rss/science_society/economics.xml", "ScienceDaily", "press"),
 ],
 "highered": [
  ("https://feeds.nature.com/natindia/rss/current", "Nature India", "journal"),
  ("https://indianexpress.com/section/technology/science/feed/", "Indian Express Science", "press"),
  ("https://www.nature.com/nathumbehav.rss", "Nature Human Behaviour", "journal"),
  ("https://rss.arxiv.org/rss/cs.CY", "arXiv", "preprint"),
  ("https://www.sciencedaily.com/rss/mind_brain/education.xml", "ScienceDaily", "press"),
 ],
 "aviation": [
  ("https://rss.arxiv.org/rss/physics.flu-dyn", "arXiv", "preprint"),
  ("https://www.sciencedaily.com/rss/matter_energy/aviation.xml", "ScienceDaily", "press"),
  ("https://rss.arxiv.org/rss/eess.SY", "arXiv", "preprint"),
 ],
 "auto": [
  ("https://news.google.com/rss/search?q=SIAM+OR+FADA+OR+ACMA+India+(report+OR+outlook+OR+sales)+when:21d&hl=en-IN&gl=IN&ceid=IN:en", "Google News India Auto", "press"),
  ("https://news.google.com/rss/search?q=ICRA+OR+CRISIL+automobile+OR+auto+sector+India+when:21d&hl=en-IN&gl=IN&ceid=IN:en", "Google News ICRA CRISIL Auto", "press"),
  ("https://news.google.com/rss/search?q=IEA+Global+EV+Outlook+OR+ICCT+India+OR+ARAI+when:30d&hl=en-IN&gl=IN&ceid=IN:en", "Google News EV Outlook", "press"),
  ("https://www.sciencedaily.com/rss/matter_energy/batteries.xml", "ScienceDaily", "press"),
  ("https://www.sciencedaily.com/rss/matter_energy/automotive_and_transportation.xml", "ScienceDaily", "press"),
  ("https://rss.arxiv.org/rss/eess.SY", "arXiv", "preprint"),
  ("https://rss.arxiv.org/rss/cs.RO", "arXiv", "preprint"),
 ],
 "realestate": [
  ("https://news.google.com/rss/search?q=JLL+India+(office+OR+housing+OR+warehouse)+report+when:21d&hl=en-IN&gl=IN&ceid=IN:en", "Google News JLL India", "press"),
  ("https://news.google.com/rss/search?q=Knight+Frank+India+(office+OR+residential)+when:21d&hl=en-IN&gl=IN&ceid=IN:en", "Google News Knight Frank India", "press"),
  ("https://news.google.com/rss/search?q=CBRE+India+(office+OR+industrial)+when:21d&hl=en-IN&gl=IN&ceid=IN:en", "Google News CBRE India", "press"),
  ("https://news.google.com/rss/search?q=Anarock+OR+PropEquity+(housing+OR+residential)+India+when:21d&hl=en-IN&gl=IN&ceid=IN:en", "Google News Anarock PropEquity", "press"),
  ("https://www.sciencedaily.com/rss/matter_energy/materials_science.xml", "ScienceDaily", "press"),
  ("https://www.sciencedaily.com/rss/earth_climate/environmental_science.xml", "ScienceDaily", "press"),
  ("https://rss.arxiv.org/rss/physics.soc-ph", "arXiv", "preprint"),
 ],
}

# Soft keyword keep filters when a feed is broad (title+summary must match at least one if set).
KEEP = {
 "schools": re.compile(r"\b(schools?|students?|teachers?|classrooms?|pedagog\w*|literacy|curriculum|education|tutoring|homework|edtech|lesson plan|K-12|\bIB\b|Cambridge Assessment|child development|reading comprehension|dyslex\w*|math education|science education|autis\w*|learning|adolescents?|classroom|tutoring|scaffolding|LLM.{0,20}tutor)\b", re.I),
 "fashion": re.compile(r"\b(fashion|apparel|textile|fabric|fibre|fiber|garment|jewellery|jewelry|diamond|cotton|silk|wool|dye|weav|knit|handloom|sustainable fashion|circular fashion|leather|footwear)\b", re.I),
 "realestate": re.compile(r"\b(real.?estate|housing market|housing price|mortgage|\bREIT\b|proptech|urban planning|land use|zoning|green building|\bLEED\b|building energy|construction material|\bcement\b|\bconcrete\b|smart city|residential property|commercial property|office vacancy|warehouse|JLL|Knight Frank|CBRE|Anarock|PropEquity)\b", re.I),
 "auto": re.compile(r"\b(auto(?:motive)?|automobile|vehicle|\bEV\b|electric vehicle|battery|charging|mobility|ADAS|autonomous|two.?wheeler|passenger car|commercial vehicle|SIAM|FADA|ACMA|ICCT|IEA|tyre|tire|powertrain|safety)\b", re.I),
 "packaging": re.compile(r"\b(packag\w*|plastics?|polymers?|recycl\w*|polyethylene|polypropylene|polyolefin|microplastics?|bioplastics?|compostable|plastic waste|circular (?:economy|packaging)|flexible packaging|food packaging|PET bottles?|HDPE|LDPE|labelstock)\b", re.I),
 "healing": re.compile(r"sleep|meditat|mindful|anxiety|depress|wellbeing|well-being|nutrition|exercise|yoga|breath|longevity|stress|therapy|mood", re.I),
 "health": re.compile(r"clinic|patient|disease|trial|vaccine|hospital|public health|cancer|diabetes|heart|infect|drug|treatment|epidemi", re.I),
}

def strip(s):
    s = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", s or "")
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()

def tidy(s):
    s = strip(s)
    s = re.sub(r"\s*[\u2013\u2014]\s*", ", ", s)
    s = s.replace(";", ",")
    return re.sub(r"\s+", " ", s).strip(" ,")

def summarise(text, title, kind):
    t = tidy(text or "")
    # Drop arxiv noise headers
    t = re.sub(r"^arXiv:\S+\s*", "", t)
    t = re.sub(r"^(Authors?:|Comments?:|Subjects?:|Journal-ref:).*$", "", t, flags=re.M)
    t = re.sub(r"\s+", " ", t).strip()
    if not t:
        t = tidy(title)
    words = t.split()
    if len(words) > 48:
        t = " ".join(words[:48]).rstrip(",.;:") + "."
    elif len(words) < 30 and kind == "preprint":
        t = (t.rstrip(".") + ". This is a preprint and has not been peer reviewed.").strip()
    # pad short summaries carefully from title only once
    words = t.split()
    if len(words) < 30:
        extra = tidy(title)
        t = (t.rstrip(".") + ". " + extra).strip()
        words = t.split()
        if len(words) > 50:
            t = " ".join(words[:50]).rstrip(",.;:") + "."
        elif len(words) < 30:
            return None
    if kind == "preprint" and "preprint" not in t.lower():
        words = t.split()
        if len(words) <= 42:
            t = t.rstrip(".") + ". Preprint, not peer reviewed."
        else:
            # replace last clause
            t = " ".join(words[:40]).rstrip(",.;:") + ". Preprint, not peer reviewed."
    n = len(t.split())
    if not 30 <= n <= 50: return None
    if BAD.search(t) or INTERN.search(t): return None
    return t

def entry_date(e):
    for k in ("published_parsed", "updated_parsed"):
        p = e.get(k)
        if p:
            try: return dt.date(*p[:3])
            except Exception: pass
    return None

def fetch_feed(url):
    try:
        r = requests.get(url, headers=UA, timeout=25)
        entries = feedparser.parse(r.content).entries if r.status_code == 200 else []
        # Nature feeds sometimes return a bot HTML wall to requests, curl still works
        if (not entries) and ("nature.com" in url or "feeds.nature.com" in url):
            import subprocess
            raw = subprocess.check_output(
                ["curl", "-sL", "-A", "Mozilla/5.0 (compatible; YesBroResearch/1.0)",
                 "--max-time", "25", url], stderr=subprocess.DEVNULL)
            entries = feedparser.parse(raw).entries
        return entries
    except Exception as ex:
        print("feed fail", url, ex); return []

def load_seen():
    try: return set(json.load(open(SEEN)))
    except Exception: return set()

def save_seen(s):
    os.makedirs(os.path.dirname(SEEN), exist_ok=True)
    json.dump(sorted(s)[-4000:], open(SEEN, "w"), indent=0)

def india_score(title, summary):
    return 1 if re.search(r"\b(India|Indian|IIT|IISc|CSIR|ICMR|Delhi|Mumbai|Bengaluru|Bangalore|Chennai|Hyderabad)\b", title + " " + summary) else 0

def pick_for(ed, today, seen):
    feeds = FEEDS.get(ed) or FEEDS["daily"]
    keep = KEEP.get(ed)
    horizon = today - dt.timedelta(days=21)
    cands = []
    with ThreadPoolExecutor(6) as ex:
        results = list(ex.map(lambda f: (f, fetch_feed(f[0])), feeds))
    for (url, src, kind), entries in results:
        for e in entries[:25]:
            title = tidy(e.get("title") or "")
            link = (e.get("link") or "").split("#")[0]
            if not title or not link: continue
            if link in seen: continue
            if POL.search(title): continue
            summ_src = e.get("summary") or e.get("description") or ""
            if keep and not keep.search(title + " " + summ_src): continue
            d = entry_date(e)
            if d and d < horizon: continue
            kind2 = kind
            if "arxiv.org" in link: kind2 = "preprint"
            summary = summarise(summ_src, title, kind2)
            if not summary: continue
            if BAD.search(title + summary) or INTERN.search(title + summary): continue
            # Healing/health: keep caveats wording already from source; skip cure claims
            if ed in ("healing", "health") and re.search(r"\b(cure[sd]?|miracle|guaranteed)\b", title + " " + summary, re.I):
                continue
            cands.append({
                "title": title[:140], "url": link, "summary": summary, "source": src,
                "kind": kind2, "date": (d.isoformat() if d else today.isoformat()),
                "_india": india_score(title, summary), "_d": d or today,
            })
    # prefer India, then newer
    cands.sort(key=lambda x: (-x["_india"], -x["_d"].toordinal(), x["title"]))
    out, used = [], set()
    for c in cands:
        k = c["url"].rstrip("/").lower()
        if k in used: continue
        used.add(k)
        out.append({k2: c[k2] for k2 in ("title", "url", "summary", "source", "kind", "date")})
        if len(out) >= CAP: break
    return out

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--date", default=dt.date.today().isoformat()); ap.add_argument("eds", nargs="*")
    a = ap.parse_args(); today = dt.date.fromisoformat(a.date); eds = a.eds or EDS
    seen = load_seen(); report = {}
    for ed in eds:
        items = pick_for(ed, today, seen)
        _bl = {}
        items = blocklist.keep(items, "research", _bl)
        if _bl: print(f"{ed}:", end=" "); blocklist.log(_bl)
        for it in items: seen.add(it["url"])
        json.dump({"date": a.date, "edition": ed, "items": items},
                  open(os.path.join(HERE, f"research_{ed}_{a.date}.json"), "w"), indent=1, ensure_ascii=False)
        report[ed] = len(items)
        print(ed, len(items), [i["title"][:40] for i in items[:3]])
    save_seen(seen)
    print("research per paper:", json.dumps(report))

if __name__ == "__main__":
    main()
