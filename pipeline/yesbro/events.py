#!/usr/bin/env python3
"""Events and Conferences for every Yes Bro paper.

  python3 events.py --date YYYY-MM-DD [ed ...]      -> events_<ed>_YYYY-MM-DD.json (default: all papers)

Sources:
  1. events/seeds.json: conferences, summits, expos and fairs found with web search on official pages
     (name, start, end, city, mode, line, url, eds). Never add one whose date you have not read on its official page.
  2. Luma public discovery API (no key): city and category feeds for Bengaluru, Mumbai and New Delhi, matched to each
     paper by keywords. Crypto and web3 are excluded. The Luma event page is the official page.
  3. confs.tech open data (GitHub) for UX, "ux": r"\bux\b|ui/ux|figma|user research|product design|design system|accessib|usability|service design|speculative design|design thinking|interaction design|\bhci\b|graphic design|industrial design|interior design|visual design|design week|awwwards|brand identity|\bd&ad\b|red dot"ility and product conferences worldwide, online and offline.
Rules: upcoming only (start or end >= today, start <= today + 90 days). Seeds are re-verified every run: the page must
load and must show the start date (any common format), otherwise the event is dropped and reported. Past events drop
out by date. Max 14 per paper, sorted by start date.
"""
import argparse, datetime as dt, html, json, os, re, sys
import blocklist
import requests
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
EDS = ["daily", "ux", "arch", "schools", "sustainability", "startups", "highered", "consulting", "health", "marketing", "finance", "aviation", "business", "healing", "ai", "packaging", "fashion", "realestate", "auto"]
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36", "Accept-Language": "en"}
MON = ["january","february","march","april","may","june","july","august","september","october","november","december"]
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
CAP = 14
NOW = dt.datetime.now(IST)

def text(h):
    h = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", h)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h)))

def date_on_page(d, t):
    m = MON[d.month - 1]; a = m[:3]; day = d.day; o = r"(st|nd|rd|th)?"
    pats = [rf"\b0?{day}{o}\s*(of\s*)?({m}|{a})\.?\b", rf"\b({m}|{a})\.?,?\s*0?{day}{o}\b",
            rf"\b0?{day}{o}\s*(-|to|\u2013|\u2014|&|and)\s*\d{{1,2}}{o}\s*(of\s*)?({m}|{a})\b",
            rf"\b0?{day}[/.-]0?{d.month}[/.-]({d.year}|{str(d.year)[2:]})\b", d.isoformat()]
    return any(re.search(p, t, re.I) for p in pats)

EMOJI = re.compile("[\U0001F000-\U0001FFFF\u2600-\u27BF\uFE0F\u200d]")
def clean(t):
    t = EMOJI.sub("", t)
    t = re.sub(r"\s*[\u2013\u2014]\s*", " - ", t)
    t = t.replace(";", ",")
    return re.sub(r"\s+", " ", t).strip(" |-")

def host_line(cal, hosts):
    who = cal if cal and cal.lower() not in ("personal", "") else hosts
    who = clean(who or "")
    return f"Public meetup hosted by {who}." if who else "Public meetup listed on Luma."

# ---- Luma
LUMA = "https://api.luma.com/discover/get-paginated-events"
CITIES = {"bengaluru": (12.9789, 77.5917), "mumbai": (19.0761, 72.8775), "new-delhi": (28.61, 77.23)}
LUMA_CATS = ["tech", "ai", "climate", "arts"]
NO_LUMA = re.compile(r"crypto|web3|blockchain|bitcoin|\bbtc\b|ethereum|\beth\b|solana|defi|\bnft|token|dao\b|memecoin|degen|party|halloween|diwali|bookclub|book club|theatre|yoga|run club|intern", re.I)
KW = {
 "ux": r"\bux\b|ui/ux|figma|user research|product design|design system|accessib|usability|service design|speculative design|design thinking|interaction design|\bhci\b",
 "arch": r"architect|urban|built environment|interior|placemaking|cities",
 "sustainability": r"climate|sustainab|net zero|carbon|clean energy|circular|esg|green",
 "startups": r"founder|startup|start-up|pitch|demo day|investor|\bvc\b|venture|accelerator",
 "business": r"founder|business|investor|networking|\bsme\b|msme|venture|deal|demo day|accelerator",
 "marketing": r"marketing|brand|growth|content|\bseo\b|creator|advertis|\babm\b",
 "finance": r"fintech|finance|investing|banking|payments|wealth|capital markets",
 "health": r"health|medtech|biotech|clinical|pharma|medical",
 "consulting": r"strategy|consult|product management|operations|transformation",
 "highered": r"universit|campus|student|research|phd|academic|iisc|iit",
 "schools": r"teacher|school|classroom|education|edtech",
 "aviation": r"aviation|aerospace|drone|airline|airport|space",
 "ai": r"\bai\b|artificial intelligence|machine learning|\bml\b|\bllm|genai|gen ai|generative|deep learning|data science|agentic|\bagents?\b",
 "packaging": r"packaging|plastics?\b|polymer|recycl|circular economy|\bepr\b|extended producer|labels? and|converting|flexible packaging|bioplastic",
 "fashion": r"fashion|apparel|garment|jewellery|jewelry|gems?|diamond|textile|handloom|khadi|footwear|handbag|eyewear|sustainable fashion|circular fashion|runway|couture|ready.to.wear",
 "realestate": r"real.?estate|proptech|property|housing|REIT|RERA|CREDAI|NAREDCO|commercial property|office leasing|warehouse|data.?cent(?:re|er)|green building|built environment|urban development|facility management",
 "auto": r"auto(?:motive)?|automobile|\bEV\b|electric vehicle|mobility|two.?wheeler|commercial vehicle|SIAM|FADA|ACMA|SAE|charging|battery|ADAS|motorsport|vehicle",
 "healing": r"mental health|wellness|wellbeing|well-being|mindful|meditat|breathwork|ayurved|longevity|nutrition|sleep|therap",
 "daily": r"$^",
}

def luma(today, horizon):
    seen, out = set(), []
    def pull(params):
        try:
            return requests.get(LUMA, params=params, headers=UA, timeout=25).json().get("entries", [])
        except Exception as e:
            print("luma failed", params.get("slug"), e); return []
    jobs = []
    for c, (la, lo) in CITIES.items():
        jobs.append({"slug": c, "pagination_limit": 50})
        for cat in LUMA_CATS:
            jobs.append({"slug": cat, "latitude": la, "longitude": lo, "pagination_limit": 50})
    with ThreadPoolExecutor(6) as ex:
        res = list(ex.map(pull, jobs))
    for entries in res:
        for e in entries:
            ev = e.get("event") or {}
            u = ev.get("url")
            if not u or u in seen: continue
            seen.add(u)
            try:
                st = dt.datetime.fromisoformat(ev["start_at"].replace("Z", "+00:00")).astimezone(IST)
            except Exception: continue
            if st.date() < today or st.date() > horizon or st < NOW: continue
            name = clean(ev.get("name", ""))
            cal = (e.get("calendar") or {}).get("name", "")
            if NO_LUMA.search(name + " " + cal): continue
            geo = ev.get("geo_address_info") or {}
            online = ev.get("location_type") == "online"
            city = "Online" if online else (geo.get("city") or "")
            if not city or not city.isascii(): continue
            hosts = ", ".join(h.get("name", "") for h in (e.get("hosts") or [])[:2] if h.get("name"))
            out.append({"name": name, "start": st.date().isoformat(), "end": st.date().isoformat(), "time": st.strftime("%-I:%M %p IST"),
                        "city": city, "mode": "Online" if online else "In person", "line": host_line(cal, hosts),
                        "url": "https://luma.com/" + u, "source": "Luma", "hay": name.lower()})
    return out

# ---- confs.tech
CT = "https://raw.githubusercontent.com/tech-conferences/conference-data/main/conferences/{y}/{t}.json"
def confstech(today, horizon):
    out = []
    for y in sorted({today.year, horizon.year}):
        for t in ["ux", "accessibility", "product", "design"]:
            try:
                r = requests.get(CT.format(y=y, t=t), headers=UA, timeout=25)
                if r.status_code != 200: continue
                for c in r.json():
                    s = dt.date.fromisoformat(c["startDate"]); e = dt.date.fromisoformat(c.get("endDate") or c["startDate"])
                    if e < today or s > horizon: continue
                    online = bool(c.get("online")) and not c.get("city")
                    city = "Online" if online else ", ".join(x for x in [c.get("city"), c.get("country")] if x and x != "Online")
                    kind = {"ux": "UX and design", "accessibility": "Accessibility", "product": "Product", "design": "Design"}[t]
                    out.append({"name": c["name"], "start": s.isoformat(), "end": e.isoformat(), "city": city or "Online",
                                "mode": ("Online" if online else "In person") + (" and online" if c.get("online") and not online else ""),
                                "line": f"{kind} conference, listed on confs.tech.", "url": c["url"], "source": "confs.tech", "eds": ["ux"]})
            except Exception as e:
                print("confs.tech failed", y, t, e)
    return out

def verify_seeds(today, horizon):
    seeds = json.load(open(os.path.join(HERE, "events", "seeds.json")))
    cache = {}
    def page(u):
        if u not in cache:
            try:
                r = requests.get(u, headers=UA, timeout=30)
                cache[u] = (r.status_code, text(r.text))
            except Exception as e:
                cache[u] = (0, str(e)[:60])
        return cache[u]
    for u in {s["url"] for s in seeds}: pass
    with ThreadPoolExecutor(8) as ex:
        list(ex.map(page, sorted({s["url"] for s in seeds})))
    ok, dropped = [], []
    for s in seeds:
        st, en = dt.date.fromisoformat(s["start"]), dt.date.fromisoformat(s["end"])
        if en < today: dropped.append(("past", s["name"])); continue
        if st > horizon: dropped.append(("beyond 90 days", s["name"])); continue
        code, t = page(s["url"])
        if code >= 400 or code == 0: dropped.append((f"status {code}", s["name"])); continue
        if not date_on_page(st, t): dropped.append(("date not on page", s["name"])); continue
        x = dict(s); x["source"] = "official"; ok.append(x)
    return ok, dropped

INDIA = {"india", "mumbai", "navi mumbai", "new delhi", "delhi", "bengaluru", "bangalore", "hyderabad", "chennai", "kolkata", "pune", "ahmedabad",
         "gandhinagar", "indore", "lucknow", "ranchi", "visakhapatnam", "noida", "greater noida", "gurugram", "gurgaon", "jaipur", "kochi", "goa",
         "guwahati", "bhubaneswar", "mysuru", "mysore", "madurai", "siliguri"}
def region(e):
    if (e.get("mode") or "").startswith("Online") or e.get("city") == "Online": return "Online"
    if e.get("source") == "Luma": return "India"  # Luma feeds are pulled for Indian cities only; online ones are caught above
    c = (e.get("city") or "").lower().split(",")[0].strip()
    return "India" if c in INDIA or c.endswith("india") else "World"

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--date", default=dt.date.today().isoformat()); ap.add_argument("eds", nargs="*")
    a = ap.parse_args(); today = dt.date.fromisoformat(a.date); horizon = today + dt.timedelta(days=90)
    eds = a.eds or EDS
    seeds, dropped = verify_seeds(today, horizon)
    lu = luma(today, horizon); ct = confstech(today, horizon)
    report = {}
    for ed in eds:
        pick = [s for s in seeds if ed in s["eds"]] + [c for c in ct if ed in c["eds"]]
        kw = re.compile(KW.get(ed, r"$^"), re.I)
        lum = [l for l in lu if kw.search(l["hay"])]
        lum.sort(key=lambda x: x["start"])
        room = max(4, CAP - len(pick))
        pick += lum[:min(6, room)]
        seen, out = set(), []
        for p in sorted(pick, key=lambda x: (x["start"], x["name"])):
            k = p["name"].lower()
            if k in seen: continue
            seen.add(k)
            if re.search(r"(?i)\bintern(ship)?s?\b", p["name"] + " " + p["line"]): continue
            x = {k2: p.get(k2) for k2 in ("name", "start", "end", "time", "city", "mode", "line", "url", "source")}
            x["region"] = region(p); out.append(x)
        _bl = {}
        out = blocklist.keep(out, "events", _bl)[:CAP]  # Begin Group blocklist
        if _bl: print(f"{ed}:", end=" "); blocklist.log(_bl)
        json.dump({"date": a.date, "edition": ed, "events": out}, open(os.path.join(HERE, f"events_{ed}_{a.date}.json"), "w"), indent=1, ensure_ascii=False)
        report[ed] = len(out)
    print("events per paper:", json.dumps(report))
    for why, n in dropped: print("  dropped seed:", why, "|", n)

if __name__ == "__main__":
    main()
