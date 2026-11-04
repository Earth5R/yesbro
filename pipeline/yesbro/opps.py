#!/usr/bin/env python3
"""Utility listings for Yes Bro Business: Government Tenders and Releases, and Funding Opportunities.

  python3 opps.py --date YYYY-MM-DD      -> opps_business_YYYY-MM-DD.json

Tenders and releases (automatic, every run):
  - PIB English press releases (latest feed), kept when the title is about trade, industry, schemes, tenders,
    investment, exports, MSMEs, ports or regulation. The release page must show 'Posted On' within 3 days.
  - Google News RSS (when:3d) for tenders and bid invitations, and for ministry circulars, scheme decisions and
    deadline extensions. Links are decoded to the publisher URL and must load. The publisher's headline is used as is.
Funding opportunities (opps/funding.json, curated with web search, re-checked every run):
  - The page must load (status < 400), must show every string in 'checks', and must show the deadline date
    (any common format) unless the item is 'rolling'. Past deadlines drop out. Never add an item whose amount or date
    you have not read on the official page.
"""
import argparse, datetime as dt, html, json, os, re, sys, time
import blocklist
import requests, feedparser
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36", "Accept-Language": "en"}
MON = ["january","february","march","april","may","june","july","august","september","october","november","december"]

def get(u, t=25):
    return requests.get(u, headers=UA, timeout=t, allow_redirects=True)

def text(h):
    h = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", h)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h)))

def date_on_page(d, t):
    m = MON[d.month - 1]; a = m[:3]; day = d.day
    pats = [rf"\b0?{day}(st|nd|rd|th)?\s*(of\s*)?({m}|{a})\.?\b", rf"\b({m}|{a})\.?\s*0?{day}(st|nd|rd|th)?\b",
            rf"\b0?{day}[/.-]0?{d.month}[/.-]{d.year}\b", d.isoformat()]
    return any(re.search(p, t, re.I) for p in pats)

PIB_OK = re.compile(r"trade|industr|scheme|tender|bid|invest|export|import|msme|startup|port|shipbuild|gst|tax|policy|regulat|ccpa|consumer|"
                    r"portal|manufactur|mou|agreement|procure|auction|disinvest|bank|rbi|sebi|corporate|company|companies|scrap|revenue|crore", re.I)
PIB_NO = re.compile(r"english rendering|mann ki baat|visit|medal|parliamentary forum|operation|condol|greet|yoga|drugs", re.I)

def pib(today):
    out = []
    try:
        r = get("https://www.pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=3&reg=3", 30)
        items = re.findall(r"<item><title>(.*?)</title><link>(.*?)</link>", r.content.decode("utf-8", "replace"), re.S)
    except Exception as e:
        print("pib feed failed", e); return out
    def one(it):
        t, l = html.unescape(it[0]).strip(), it[1].strip()
        if not PIB_OK.search(t) or PIB_NO.search(t): return None
        try:
            p = text(get(l.replace("PressReleaseIframePage", "PressReleasePage")).text)
        except Exception: return None
        m = re.search(r"Posted On:?\s*(\d{1,2}) ([A-Z]{3}) (\d{4})", p, re.I)
        if not m: return None
        d = dt.date(int(m[3]), [x[:3] for x in MON].index(m[2].lower()) + 1, int(m[1]))
        if (today - d).days > 3: return None
        return {"kind": "Release", "title": clean(t), "org": "Press Information Bureau", "date": d.isoformat(), "url": l.replace("PressReleaseIframePage", "PressReleasePage"), "source": "PIB"}
    with ThreadPoolExecutor(6) as ex:
        out = [x for x in ex.map(one, items) if x]
    return out

GN = "https://news.google.com/rss/search?q={}+when:3d&hl=en-IN&gl=IN&ceid=IN:en"
QUERIES = [("Tender", "tender+OR+%22invites+bids%22+OR+%22floats+tender%22+OR+%22request+for+proposal%22+India"),
           ("Release", "ministry+%28circular+OR+notification+OR+%22extends+deadline%22+OR+%22scheme%22%29+business+India")]
T_OK = {"Tender": re.compile(r"tender|invites? bids|bids? invited|floats|rfp|request for proposal|eoi|expression of interest|auction", re.I),
        "Release": re.compile(r"ministry|govt|government|centre|cabinet|circular|notif|scheme|extends|deadline|rules?\b|policy|gst|mca|dpiit|cbdt|cbic|rbi|sebi", re.I)}
T_NO = re.compile(r"court|violative|inquiry|probe|scam|controvers|claims|accuse|alleg|protest|\baap\b|temple|prasad|yatra|story|offers|services|solutions|high court|supreme court|tribunal|\bipo\b|subscri|gmp|share price|stock|sensex|nifty|tender (their|your) shares|open offer|rally|election|cricket|bjp|congress|uzbekistan|pakistan|may exclude|less than a third|opinion|explained", re.I)

STOP = {"government", "invites", "tender", "tenders", "scheme", "india", "indian", "centre", "minister", "ministry", "project", "crore", "floats"}

def clean(t):
    t = re.sub(r"\s*[\u2014\u2013]\s*", ", ", t)
    return re.sub(r"\s*;\s*", ", ", t).strip()

def news(today):
    from googlenewsdecoder import gnewsdecoder
    cut = time.time() - 3 * 86400
    raw = []
    for kind, q in QUERIES:
        try:
            f = feedparser.parse(get(GN.format(q)).content)
        except Exception as e:
            print("gn failed", kind, e); continue
        for e in f.entries:
            ts = e.get("published_parsed")
            if not ts or time.mktime(ts) < cut: continue
            t = html.unescape(e.title)
            src = (e.get("source") or {}).get("title", "")
            if src.startswith("http"):
                src = re.sub(r"^https?://(www\.)?|/.*$", "", src).split(".")[0].replace("indiagazette", "India Gazette").title() if src else src
            if src and t.endswith(" - " + src): t = t[: -len(src) - 3]
            if not T_OK[kind].search(t) or T_NO.search(t): continue
            raw.append((kind, t.strip(), src, e.link, dt.date(*ts[:3]).isoformat()))
    seen, picks = [], []
    for r in raw:
        w = set(re.findall(r"[a-z0-9]{5,}", r[1].lower())) - STOP
        if any(len(w & s) >= 2 for s in seen): continue
        seen.append(w); picks.append(r)
    def one(r):
        kind, t, src, link, d = r
        try:
            dec = gnewsdecoder(link, interval=1)
            u = dec.get("decoded_url") if (dec.get("status") or dec.get("success")) else None
            if not u: return None
            s = get(u).status_code
            if s >= 400 and s not in (401, 403): return None
        except Exception: return None
        return {"kind": kind, "title": clean(t), "org": src, "date": d, "url": u, "source": src}
    with ThreadPoolExecutor(4) as ex:
        return [x for x in ex.map(one, picks[:30]) if x]

def funding(today):
    items = json.load(open(os.path.join(HERE, "opps", "funding.json")))
    def one(it):
        dl = dt.date.fromisoformat(it["deadline"]) if it.get("deadline") else None
        if dl and dl < today: return None, f"past deadline: {it['title']}"
        try:
            r = get(it["url"])
            if r.status_code >= 400: return None, f"status {r.status_code}: {it['title']}"
            t = text(r.text)
        except Exception as e:
            return None, f"failed {str(e)[:40]}: {it['title']}"
        miss = [c for c in it.get("checks", []) if c.lower() not in t.lower()]
        if miss: return None, f"missing {miss}: {it['title']}"
        if dl and not date_on_page(dl, t): return None, f"deadline not on page: {it['title']}"
        x = {k: it.get(k) for k in ("title", "org", "where", "url", "deadline", "line", "rolling")}
        x["kind"] = "Funding"; return x, None
    out, notes = [], []
    with ThreadPoolExecutor(6) as ex:
        for x, n in ex.map(one, items):
            if x: out.append(x)
            if n: notes.append(n)
    out.sort(key=lambda x: (x.get("deadline") or "9999"))
    return out, notes

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--date", default=dt.date.today().isoformat()); a = ap.parse_args()
    today = dt.date.fromisoformat(a.date)
    rel = pib(today); nw = news(today); fund, notes = funding(today)
    _bl = {}
    rel, nw, fund = (blocklist.keep(x, "opps", _bl) for x in (rel, nw, fund))  # Begin Group blocklist
    if _bl: blocklist.log(_bl)
    tenders = [x for x in nw if x["kind"] == "Tender"][:12]
    releases = (rel + [x for x in nw if x["kind"] == "Release"])[:12]
    for x in tenders + releases + fund:
        if re.search(r"(?i)\bintern(ship)?s?\b", " ".join(str(v) for v in x.values())): raise SystemExit("no-intern rule")
    res = {"date": a.date, "tenders": tenders, "releases": releases, "funding": fund,
           "status": {"tenders": len(tenders), "releases": len(releases), "funding": len(fund), "funding_dropped": notes}}
    out = os.path.join(HERE, f"opps_business_{a.date}.json")
    json.dump(res, open(out, "w"), indent=1, ensure_ascii=False)
    print(f"wrote {out}: {len(tenders)} tenders, {len(releases)} releases, {len(fund)} funding")
    for n in notes: print("  dropped", n)

if __name__ == "__main__":
    main()
