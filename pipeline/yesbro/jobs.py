#!/usr/bin/env python3
"""Yes Bro Jobs: gather real, currently open job listings for a Yes Bro field edition.

Usage:
  python3 jobs.py ux|arch|schools|sustainability|startups|highered|consulting|health|marketing|finance|aviation|business|healing|ai|packaging|fashion|realestate|auto [--date YYYY-MM-DD] [--out jobs_ux_YYYY-MM-DD.json]

Sources are public job board APIs and feeds only (Greenhouse, Lever, Ashby, SmartRecruiters and
Workday public job APIs, Himalayas, Remotive, We Work Remotely, Working Nomads, Dribbble jobs RSS,
Archinect jobs feed, SuccessFactors career site search pages, and a few school career pages).
Every listing must be fetched this run, look open, be no older than MAX_AGE days where a date is
visible, and its Apply link must load (HTTP < 400). Nothing is invented.

Dedupe across days: jobs/jobs_seen.json maps listing id to the date first seen. A listing is marked
new only on the day it is first seen. Still-open roles stay listed on later days.

Output JSON: {edition, date, counts, sources, jobs:[{id,title,org,location,region,posted,deadline,
url,source,tag,new}]}  region is India, Global or Remote. tag is Teacher or Student (schools only).
"""
import argparse, concurrent.futures as cf, datetime as dt, html, json, os, re, sys, time
import blocklist
import requests, feedparser

HERE = os.path.dirname(os.path.abspath(__file__))
SEEN = os.path.join(HERE, "jobs", "jobs_seen.json")
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36 YesBroJobs/1.0"}
MAX_AGE = 30
CAP = {"India": 14, "Global": 8, "Remote": 8}
TOTAL = 30
PER_ORG = 3

INDIA = re.compile(r"\b(india|bengaluru|bangalore|mumbai|bombay|delhi|gurugram|gurgaon|noida|hyderabad|pune|chennai|kolkata|"
                   r"ahmedabad|jaipur|kochi|chandigarh|indore|coimbatore|kodaikanal|thiruvananthapuram|lucknow|goa|vadodara|"
                   r"surat|nagpur|mysuru|mysore|bhubaneswar|visakhapatnam|haridwar|pondicherry|puducherry|assam|doom dooma|gujarat|maharashtra|karnataka|tamil nadu|telangana|kerala|uttarakhand)\b|,\s*IN\b(?!\s*,\s*(?:USA|US|United States)\b)|\bIN\.", re.I)
REMOTE = re.compile(r"\b(remote|anywhere|worldwide|online|work from home)\b", re.I)

# ---------------------------------------------------------------- edition filters
UX_RE = re.compile(r"\b(ux|ui|user experience|user research|ux research\w*|product design\w*|interaction design\w*|service design\w*|"
                   r"content design\w*|ux writ\w*|design systems?|experience design\w*|visual design\w*|design research\w*|"
                   r"product designer|ui designer|ux designer|graphic designer|industrial designer|interior designer|visual designer|brand designer|communication designer|design lead|head of design|design manager|design director|graphic design\w*|industrial design\w*|interior design\w*|"
                   r"director,? (product |experience |content )?design)\b", re.I)
UX_NO = re.compile(r"learning experience|brand experience|engineer|developer|scientist|analyst|marketing|sales|account|recruit|motion|hardware|"
                   r"chip|asic|silicon|circuit|mechanical|instructional|game designer|level designer|"
                   r"fashion|architect|qa\b|test|data\b", re.I)
ARCH_RE = re.compile(r"\b(architect|architects|architectural|architecture|urban design\w*|urban planner|town planner|planner|"
                     r"landscape|bim|revit|green building|leed|igbc|griha|sustainability consultant|sustainable design|"
                     r"building performance|energy model\w*|facade|fa\u00e7ade|masterplan\w*|interior architect\w*|"
                     r"job captain|project architect|draftsperson|draftsman|specifications writer)\b", re.I)
ARCH_NO = re.compile(r"\b(solution|solutions|software|cloud|data|enterprise|security|technical|systems?|network|platform|"
                     r"integration|application|salesforce|aws|azure|gcp|ai|ml|infrastructure|it|devops|sap|oracle|"
                     r"database|product|principal software|java|backend|frontend|mobile|identity|storage|kubernetes)\s+"
                     r"(architect|architecture)|engineer(ing)? manager|financial planner|demand planner|media planner|"
                     r"supply|merchandis|production planner|sales|account|recruit|servicenow|naval|electrical|mechanical|mechnical|\(structures\)|\bphe\b|plumbing|"
                     r"\bmep\b|hvac|structural|civil 3d|water|economic|data cent|railway|acoustic|ecologist|financial|wealth|"
                     r"estate planner|event planner|travel planner|workforce planner|capacity planner|maintenance planner", re.I)
TEACH_RE = re.compile(r"teach|coordinator|head of|tutor|educator|lecturer|principal|counsel|librar|learning support|"
                      r"homeroom|\bpyp\b|\bmyp\b|\bdp\b|ibdp|igcse|a level|eal|curriculum", re.I)
TEACH_NO = re.compile(r"assistant|admissions|admin|finance|facilities|it support|technician|marketing|driver|nurse|"
                      r"housekeep|security|accountant|chef|cook|bus|maintenance|receptionist|hr\b|human resources|"
                      r"talent|payroll|procurement|cover teacher", re.I)

SUS_RE = re.compile(r"sustainab|\besg\b|climate|carbon|decarboni|net[- ]zero|environment|\bbrsr\b|circular|energy transition|renewable|\behs\b|\bcsr\b", re.I)
SUS_NO = re.compile(r"green ?field|driver|software engineer|sales executive|carbon black|security|account executive", re.I)
# House rule (25 Oct 2026, final): NO internship listings anywhere on Yes Bro. Promoting other companies' internships
# conflicts with Earth5R's FIELDWORK fellowship. Any listing whose title, employment type, org or URL marks it as an
# internship is dropped in main(), for every edition and every source, seeds included.
NO_INTERN = re.compile(r"\bintern(ship)?s?\b|internship|summer (analyst|associate)|\bpr[a\u00e1]cticas?\b|praktik|stagiaire|werkstudent|stagiair|tirocin|becari[oa]|pasant[i\u00ed]a|alternance|\bstage (20\d\d|en|de|d.)\b|^stage\b|\bstage 20", re.I)
NO_INTERN_URL = re.compile(r"intern(?!ation|al|et)", re.I)
def is_internship(j):
    t = " ".join(str(j.get(k) or "") for k in ("title", "type", "org", "note"))
    return bool(NO_INTERN.search(t) or NO_INTERN_URL.search(j.get("url") or ""))
ENTRY_RE = re.compile(r"graduate (program|programme|scheme|trainee)|\bgraduate\b|\btrainee\b|campus hire|fresher|entry[- ]level|\bjunior\b|new grad|early career|rotational|research (assistant|associate)|\b20(26|27)\b|teaching (assistant|fellow)|academic (associate|assistant)", re.I)
SENIOR_RE = re.compile(r"senior|\bsr\b|lead|director|head|principal|\bvp\b|manager|\bii\b|\biii\b", re.I)
EDU_RE = re.compile(r"education|teacher|teaching|admission|counsel|curriculum|academic|tutor|instructional|learning designer|faculty|lecturer|professor|university|scholarship|student success|course", re.I)
CONS_RE = re.compile(r"consult|strategy|strategic|advisory|engagement manager|transformation|due diligence|\bdeals\b|business analyst|research analyst|market research|specialist analyst|economist|parthenon", re.I)
CONS_NO = re.compile(r"software|engineer|developer|data scientist|sales|recruit|administrative|receptionist|nurse|driver|information security|client support|accounting|admissions|expression of interest|support", re.I)
MKT_RE = re.compile(r"marketing|\bbrand|growth|content|social media|\bseo\b|\bsem\b|performance market|communications|\bpr\b|public relations|copywrit|creative|campaign|demand gen|community|influencer|creator|partnerships marketing|crm|lifecycle|media plann|advertis", re.I)
MKT_NO = re.compile(r"engineer|developer|scientist|account executive|sales development|recruit", re.I)
FIN_RE = re.compile(r"financ|fp&a|accountant|accounting|treasury|\brisk\b|credit|investment|audit|\btax\b|compliance|banking|wealth|actuar|\bquant|trader|trading|underwrit|portfolio|valuation|controller|payments|lending|equity research|analyst", re.I)
FIN_NO = re.compile(r"software engineer|developer|recruit|nurse|driver|data engineer|security engineer|marketing", re.I)
AV_NO = re.compile(r"\bsales\b|recruit|receptionist|legal counsel|software engineer", re.I)
def sus_ok(t): return bool(SUS_RE.search(t)) and not SUS_NO.search(t)
def highered_ok(t): return bool((EDU_RE.search(t) or (ENTRY_RE.search(t) and not SENIOR_RE.search(t))) and not NO_INTERN.search(t))
def cons_ok(t): return bool(CONS_RE.search(t)) and not CONS_NO.search(t)
def mkt_ok(t): return bool(MKT_RE.search(t)) and not MKT_NO.search(t)
def fin_ok(t): return bool(FIN_RE.search(t)) and not FIN_NO.search(t)
BIZ_RE = re.compile(r"business development|\bbd\b|sales|operations|strategy|strategic|procurement|sourcing|\bbid\b|tender|partnership|alliances|account manager|key account|"
                    r"category manager|business analyst|commercial|supply chain|corporate development|\bm&a\b|investor relations|revenue|general manager|business head|finance", re.I)
BIZ_NO = re.compile(r"engineer|developer|software|devops|designer|nurse|physician|clinical|driver|technician|teacher|\bsre\b|data scientist", re.I)
def biz_ok(t): return bool(BIZ_RE.search(t)) and not BIZ_NO.search(t)
HEAL_RE = re.compile(r"wellness|wellbeing|well-being|mental health|counsel|therap|psycholog|psychiatr|yoga|meditat|mindful|nutrition|dietit|health coach|wellness coach|fitness|sleep|ayurved|physiotherap|massage|care navigator|clinical social worker|behavioral health|behavioural health", re.I)
HEAL_NO = re.compile(r"talent pool|financial|engineer|developer|software|devops|sales|account executive|recruiter|finance|accountant|legal|counsel\b|general counsel|marketing|product manager|data scientist|analyst", re.I)
def heal_ok(t): return bool(HEAL_RE.search(t)) and not HEAL_NO.search(t)
# Yes Bro AI: machine learning, AI research and AI engineering roles only.
AI_RE = re.compile(r"machine learning|\bml\b|\bai\b|artificial intelligence|deep learning|\bllms?\b|\bnlp\b|computer vision|data scien|applied scientist|research scientist|research engineer|mlops|gen ?ai|generative|inference|model (training|evaluation|behavior)|alignment|interpretability", re.I)
AI_NO = re.compile(r"talent pool|\bintern|sales|account executive|account manager|recruit|legal|counsel|paralegal|accountant|payroll|facilities|executive assistant", re.I)
def ai_ok(t): return bool(AI_RE.search(t)) and not AI_NO.search(t)
PKG_RE = re.compile(r"packag|plastic|polymer|resin|extrusion|extruder|thermoform|injection mou?ld|blow mou?ld|flexible|flexo|gravure|laminat|converting|converter|corrugat|carton|label|printing press|film|recycl|sustainab|quality|production|process engineer|maintenance|plant manager|procurement", re.I)
PKG_NO = re.compile(r"\bintern(ship)?s?\b|software engineer|frontend|backend|nurse|teacher|package (design )?engineer|application pack|advanced packaging|hybrid bonding|semiconductor|fuel recycling|card plastics|counsel|attorney", re.I)
def pkg_ok(t): return bool(PKG_RE.search(t)) and not PKG_NO.search(t)
FASH_RE = re.compile(r"fashion|apparel|garment|textile|jewellery|jewelry|gems?|diamond|footwear|handbag|eyewear|watchmaker|merchandis|stylist|buyer|visual merchand|retail (?:store|manager|buyer)|e-?commerce|D2C|designer|pattern|sewing|tailor|weaver|handloom|khadi|accessories|leather|footwear|sneaker", re.I)
FASH_NO = re.compile(r"\bintern(ship)?s?\b|software engineer|frontend|backend|nurse|teacher|counsel|attorney|physician|devops|data scientist|machine learning", re.I)
def fash_ok(t): return bool(FASH_RE.search(t)) and not FASH_NO.search(t)
RE_RE = re.compile(r"real.?estate|\bproperty\b|housing|real.?estate developer|property developer|brokerage|\bbroker\b|facility management|facilities manager|valuation|valuer|appraiser|proptech|\bREIT\b|leasing manager|property manager|real.?estate (?:sales|manager|analyst|associate)|quantity survey|site engineer|construction manager|estate agent|realtor|facility manager", re.I)
RE_NO = re.compile(r"\bintern(ship)?s?\b|software|frontend|backend|devops|full.?stack|nurse|teacher|data scientist|machine learning|physician|attorney|counsel|DevEx|web developer|mobile developer", re.I)
def re_ok(t): return bool(RE_RE.search(t)) and not RE_NO.search(t)

AUTO_RE = re.compile(r"\b(?:auto(?:motive)?|automobile|vehicle|OEM|\bEV\b|electric vehicle|two.?wheeler|four.?wheeler|commercial vehicle|dealer|dealership|powertrain|drivetrain|chassis|ADAS|autonomous|mobility|battery|charging|tyre|tire|tractor|off.?highway|fleet|workshop|service advisor|sales consultant)\b|Maruti|Tata Motors|Mahindra|Hyundai|Bosch|Motherson|Ashok Leyland|Hero Moto|Bajaj|TVS|Ola Electric|Ather", re.I)
AUTO_NO = re.compile(r"\bintern(ship)?s?\b|nurse|teacher|physician|attorney|counsel|frontend|backend|full.?stack|DevEx|data scientist|machine learning engineer", re.I)
def auto_ok(t): return bool(AUTO_RE.search(t)) and not AUTO_NO.search(t)

def any_ok(t): return bool(t) and not re.search(r"general application|talent pool|expression of interest|future opportunities", t, re.I)
def av_ok(t): return any_ok(t) and not AV_NO.search(t)

def ux_ok(t): return bool(UX_RE.search(t)) and not UX_NO.search(t)
def arch_ok(t): return bool(ARCH_RE.search(t)) and not ARCH_NO.search(t)
def teach_ok(t): return bool(TEACH_RE.search(t)) and not TEACH_NO.search(t)

# ---------------------------------------------------------------- helpers
def clean(s):
    s = html.unescape(re.sub(r"<[^>]+>", " ", s or ""))
    s = s.replace("\u2014", "-").replace("\u2013", "-").replace("\u2012", "-").replace(";", ",")
    s = s.replace("\u00a0", " ")
    return re.sub(r"\s+", " ", s).strip(" ,-|")

def iso(d):
    return d.strftime("%Y-%m-%d") if d else None

def parse_date(v):
    if v is None or v == "": return None
    try:
        if isinstance(v, (int, float)):
            return dt.datetime.fromtimestamp(v / 1000 if v > 1e11 else v, dt.timezone.utc).date()
        v = str(v)
        m = re.match(r"(\d{4})-(\d{2})-(\d{2})", v)
        if m: return dt.date(int(m[1]), int(m[2]), int(m[3]))
        v = re.sub(r"\s+", " ", v).strip()
        for fmt in ("%d %b %Y", "%b %d, %Y", "%d %B %Y", "%B %d, %Y", "%d/%m/%Y", "%B %d %Y", "%d %b, %Y", "%d %B, %Y"):
            try: return dt.datetime.strptime(v, fmt).date()
            except ValueError: pass
        try:
            p = feedparser._parse_date(v)
            if p: return dt.date(p.tm_year, p.tm_mon, p.tm_mday)
        except Exception:
            pass
    except Exception:
        return None
    return None

CACHE_HOSTS = ("boards-api.greenhouse.io", "api.lever.co", "api.ashbyhq.com", "api.smartrecruiters.com", "himalayas.app/jobs/api",
               "remotive.com/api", "workingnomads.com/api", "weworkremotely.com/categories")
CACHE_DIR = os.path.join(HERE, "jobs", "cache", dt.date.today().isoformat())

class _Cached:
    def __init__(self, status, content, url): self.status_code, self.content, self.url = status, content, url
    @property
    def text(self): return self.content.decode("utf-8", "ignore")
    def json(self): return json.loads(self.content)

def get(url, **kw):
    """GET with a shared same-day disk cache for public job board APIs, so the 11 editions running in
    parallel fetch each Greenhouse, Lever, Ashby, SmartRecruiters or remote board list only once a day."""
    kw.setdefault("timeout", 25)
    h = dict(UA); h.update(kw.pop("headers", {}))
    cacheable = any(x in url for x in CACHE_HOSTS) and not kw.get("stream")
    if cacheable:
        import hashlib
        fn = os.path.join(CACHE_DIR, hashlib.sha1(url.encode()).hexdigest() + ".json")
        if os.path.exists(fn):
            c = json.load(open(fn)); return _Cached(c["status"], c["content"].encode(), url)
    r = requests.get(url, headers=h, **kw)
    if cacheable and r.status_code == 200:
        os.makedirs(CACHE_DIR, exist_ok=True)
        tmp = fn + f".{os.getpid()}"
        json.dump({"status": r.status_code, "content": r.text}, open(tmp, "w")); os.replace(tmp, fn)
    return r

CC = {"IN": "India", "US": "USA", "GB": "UK", "UK": "UK", "AE": "UAE", "SG": "Singapore", "CA": "Canada", "AU": "Australia", "SA": "Saudi Arabia", "IE": "Ireland", "VN": "Vietnam", "UY": "Uruguay", "CN": "China", "HK": "Hong Kong", "TH": "Thailand", "QA": "Qatar", "CH": "Switzerland", "ES": "Spain", "MY": "Malaysia", "KR": "South Korea", "JP": "Japan", "DE": "Germany", "FR": "France", "NL": "Netherlands", "BR": "Brazil", "MX": "Mexico", "PH": "Philippines", "ID": "Indonesia", "EG": "Egypt", "PL": "Poland", "BH": "Bahrain", "KW": "Kuwait", "OM": "Oman"}

def tidy_loc(loc):
    loc = clean(loc)
    m = re.match(r"^([A-Z]{2})-[A-Z]{2}-([A-Za-z ]+?)(?:-|$)", loc)
    if m: loc = f"{m[2]}, {CC.get(m[1], m[1])}"
    m = re.match(r"^([A-Z]{2})\.([A-Z]{2})\.([^.]+)(\..*)?$", loc) or None
    if m: loc = f"{m[3]}, {m[2]}, {CC.get(m[1], m[1])}"
    else:
        m = re.match(r"^([A-Z]{2})\.([^.]+)(\..*)?$", loc)
        if m: loc = f"{m[2]}, {CC.get(m[1], m[1])}"
    loc = re.sub(r"\b\d{5,6}\b", "", loc).replace("Dheli", "Delhi")
    loc = re.sub(r",\s*([A-Z]{2})\s*$", lambda m: ", " + CC.get(m[1], m[1]), loc)
    loc = re.sub(r",\s*[A-Z]{2}\s*,\s*India$", ", India", loc)
    loc = re.sub(r"(,\s*IN\s*,\s*(?:USA|United States))\s*,\s*India$", r"\1", loc)  # Indiana, not India
    loc = re.sub(r"(,\s*)+", ", ", loc).strip(", ")
    loc = ", ".join(w[:1].upper() + w[1:] if w[:1].islower() else w for w in [p.strip() for p in loc.split(",")])
    m = re.search(r"(?:Office|Campus)\s+(Bangalore|Bengaluru|Mumbai|Gurgaon|Gurugram|Noida|Chennai|Hyderabad|Pune|Delhi|Kolkata)\b", loc)
    if m: loc = m[1].replace("Bangalore", "Bengaluru") + ", India"
    loc = re.sub(r",\s*(KA|DL|MH|TN|TS|HR|UP)\s*,\s*India$", ", India", loc)
    loc = re.sub(r"\b[A-Z]{4,}\b", lambda m: m[0].title(), loc)
    parts = [p.strip() for p in loc.split(",")]
    COUNTRIES = set(CC.values()) | {"United Arab Emirates", "United Kingdom", "United States", "Panama", "Peru", "Colombia", "Chile", "Ecuador", "Ghana", "Nigeria", "Kenya", "Morocco", "Italy", "Portugal", "Romania"}
    if len(parts) == 3 and parts[1] in COUNTRIES and re.search(r"school|academy|college|\b[A-Z]{3,5}\b", parts[0], re.I):
        parts = [parts[2], parts[1]]; loc = ", ".join(parts)
    elif len(parts) == 2 and re.search(r"school|academy|college", parts[0], re.I):
        loc = parts[1]; parts = [loc]
    if len(loc) > 48 and "and more" not in loc:
        loc = ", ".join(parts[:2]) + " and more"
    return loc

def job(title, org, location, url, source, posted=None, deadline=None, tag=None, remote=False):
    title, org, location = clean(title), clean(org), tidy_loc(location)
    if title.isupper() and len(title) > 4: title = title.title()
    if INDIA.search(location or ""): region = "India"
    elif remote or REMOTE.search(location or ""): region = "Remote"
    else: region = "Global"
    if region == "Remote" and not location: location = "Remote"
    return {"title": title, "org": org, "location": location or ("Remote" if remote else ""), "region": region,
            "posted": iso(posted) if isinstance(posted, dt.date) else posted, "deadline": iso(deadline) if isinstance(deadline, dt.date) else deadline,
            "url": url, "source": source, "tag": tag}

# ---------------------------------------------------------------- ATS sources
def greenhouse(token, org, ok):
    j = get(f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs").json()
    out = []
    for p in j.get("jobs", []):
        if not ok(p["title"]): continue
        out.append(job(p["title"], org, (p.get("location") or {}).get("name", ""), p["absolute_url"], "Greenhouse",
                       parse_date(p.get("first_published") or p.get("updated_at")), parse_date(p.get("application_deadline"))))
    return out

def lever(token, org, ok):
    j = get(f"https://api.lever.co/v0/postings/{token}?mode=json").json()
    out = []
    for p in j:
        if not ok(p["text"]): continue
        c = p.get("categories") or {}
        loc = c.get("location") or ", ".join(c.get("allLocations") or [])
        if (p.get("workplaceType") == "remote") and "remote" not in loc.lower(): loc = (loc + " (Remote)").strip()
        out.append(dict(job(p["text"], org, loc.title() if loc.islower() else loc, p["hostedUrl"], "Lever", parse_date(p.get("createdAt"))), type=c.get("commitment") or ""))
    return out

def ashby(token, org, ok):
    j = get(f"https://api.ashbyhq.com/posting-api/job-board/{token}").json()
    out = []
    for p in j.get("jobs", []):
        if not p.get("isListed", True) or not ok(p["title"]): continue
        locs = [p.get("location") or ""] + [s.get("location", "") for s in p.get("secondaryLocations") or []]
        loc = next((l for l in locs if INDIA.search(l)), locs[0])
        out.append(dict(job(p["title"], org, loc, p["jobUrl"], "Ashby", parse_date(p.get("publishedAt")), remote=bool(p.get("isRemote")) and not loc), type=p.get("employmentType") or ""))
    return out

def smartrecruiters(cid, org, ok, q=None):
    out = []
    for off in (0, 100):
        u = f"https://api.smartrecruiters.com/v1/companies/{cid}/postings?limit=100&offset={off}" + (f"&q={q}" if q else "")
        j = get(u).json()
        for p in j.get("content", []):
            if not ok(p["name"]): continue
            L = p.get("location") or {}
            out.append(job(p["name"], org, L.get("fullLocation") or L.get("city", ""), f"https://jobs.smartrecruiters.com/{cid}/{p['id']}",
                           "SmartRecruiters", parse_date(p.get("releasedDate")), remote=bool(L.get("remote"))) | {"type": " ".join(str((p.get(k) or {}).get("label", "")) for k in ("typeOfEmployment", "experienceLevel"))})
        if len(j.get("content", [])) < 100: break
    return out

def wd_posted(s, today):
    s = (s or "").lower()
    if "today" in s: return today
    if "yesterday" in s: return today - dt.timedelta(days=1)
    m = re.search(r"(\d+)\+?\s*days", s)
    if m:
        if "+" in s: return None if False else today - dt.timedelta(days=99)
        return today - dt.timedelta(days=int(m[1]))
    return None

def workday(host, tenant, site, org, ok, queries, today, pages=2):
    out, seen = [], set()
    H = {"Content-Type": "application/json", "Accept": "application/json"}
    for q in queries:
        for pg in range(pages):
            r = requests.post(f"https://{host}/wday/cxs/{tenant}/{site}/jobs", headers={**UA, **H}, timeout=25,
                              json={"appliedFacets": {}, "limit": 20, "offset": pg * 20, "searchText": q})
            posts = r.json().get("jobPostings", [])
            for p in posts:
                path = p.get("externalPath")
                if not path or path in seen or not ok(p.get("title", "")): continue
                seen.add(path)
                posted = wd_posted(p.get("postedOn"), today)
                if posted is None or (today - posted).days > MAX_AGE: continue
                loc = p.get("locationsText", "")
                if re.match(r"\d+ Locations", loc):  # ask the detail endpoint which locations
                    try:
                        d = requests.get(f"https://{host}/wday/cxs/{tenant}/{site}{path}", headers={**UA, **H}, timeout=25).json()
                        info = d.get("jobPostingInfo", {})
                        locs = [info.get("location", "")] + list(info.get("additionalLocations") or [])
                        ind = next((l for l in locs if INDIA.search(l)), None)
                        loc = ind or (f"{locs[0]} and {len(locs) - 1} more" if len(locs) > 1 and locs[0] else loc)
                    except Exception:
                        pass
                out.append(job(p["title"], org, loc, f"https://{host}/en-US/{site}{path}", "Workday", posted))
            if len(posts) < 20: break
    return out

def successfactors(base, org, ok, q, extra=""):
    """SAP SuccessFactors career site search page (public HTML, both table and tile layouts)."""
    t = get(f"{base}/search/?q={q}&sortColumn=referencedate&sortDirection=desc{extra}").text
    out = []
    for row in re.findall(r'<tr class="data-row">(.*?)</tr>', t, re.S):
        a = re.search(r'href="([^"]+)" class="jobTitle-link">(.*?)</a>|class="jobTitle-link" href="([^"]+)">(.*?)</a>', row, re.S)
        if not a: continue
        href, title = (a[1] or a[3]), (a[2] or a[4])
        loc = re.search(r'<span class="jobLocation">(.*?)</span>', row, re.S)
        d = re.search(r'<span class="jobDate">(.*?)</span>', row, re.S)
        if ok(clean(title)):
            out.append(job(title, org, clean(loc[1]) if loc else "", base + html.unescape(href), "Career site", parse_date(clean(d[1])) if d else None))
    for m in re.finditer(r'<li class="job-tile job-id-(\d+)[^"]*"[^>]*data-url="([^"]+)"', t):
        jid, href = m[1], m[2]
        seg = t[m.end(): m.end() + 12000]
        title = re.search(r'class="jobTitle-link[^"]*"[^>]*>(.*?)</a>', seg, re.S)
        f = {k: clean(v) for k, v in re.findall(rf'id="job-{jid}-desktop-section-([a-zA-Z0-9]+)-value"[^>]*>(.*?)</div>', seg, re.S)}
        if not title or not ok(clean(title[1])): continue
        school = f.get("customfield3", "")
        loc = ", ".join(x for x in [f.get("city", ""), {"IN": "India"}.get(f.get("country", ""), f.get("country", ""))] if x)
        out.append(job(title[1], school or org, loc, base + html.unescape(href), "Career site", None))
    return out

def sf_date(url):
    """Read the posting date from a SuccessFactors job page."""
    try:
        t = get(url).text
        m = re.search(r'itemprop="datePosted"[^>]*content="([^"]+)"', t) or re.search(r'data-careersite-propertyid="date"[^>]*>\s*([^<]+)<', t) \
            or re.search(r'Posting Date:?\s*</?[^>]*>?\s*([0-9]{1,2} [A-Z][a-z]{2} [0-9]{4})', t)
        return parse_date(m[1].strip()) if m else None
    except Exception:
        return None

def dotjobs(domain, org, ok, queries, location="India"):
    """DirectEmployers .jobs career sites publish an RSS feed of their search results."""
    out, seen = [], set()
    for q in queries:
        f = feedparser.parse(get(f"https://{domain}/jobs/feed/rss?location={location}&q={requests.utils.quote(q)}").content)
        for e in f.entries:
            if e.link in seen: continue
            seen.add(e.link)
            m = re.match(r"\(([A-Z]{3})-([^)]+)\)\s*(.+)$", e.title)
            title, loc = (m[3], f"{m[2]}, India" if m[1] == "IND" else f"{m[2]}, {m[1]}") if m else (e.title, location)
            if not ok(clean(title)): continue
            out.append(job(title, org, loc, e.link, "Career site", parse_date(e.get("published"))))
    return out

def seeds(ed, today):
    """Direct posting URLs discovered with web search (jobs/seeds_<ed>.json). Each is re-checked every run:
    the page must load, must not say it is closed, and must show a closing date ahead or a posting date
    within MAX_AGE days. Add new finds to the file, stale ones simply drop out."""
    fn = os.path.join(HERE, "jobs", f"seeds_{ed}.json")
    if not os.path.exists(fn): return []
    items = json.load(open(fn))
    CLOSED = re.compile(r"no longer (accepting|available|open)|position (has been|is) filled|job (has )?expired|"
                        r"applications? (are |is )?(now )?closed|this job is closed|vacancy (has )?closed|posting has expired", re.I)
    POSTED = re.compile(rf"(?:posted(?: on)?|posting date|published|date posted|advertised)\s*:?\s*({DATE_RE.pattern}|\d{{4}}-\d{{2}}-\d{{2}}|\d{{1,2}}/\d{{1,2}}/\d{{4}})", re.I)
    CLOSE = re.compile(rf"(?:closing date|closes(?: on)?|last date(?: to apply| for applications?| of application)?|apply by|deadline|application deadline)\s*:?\s*(?:is\s*)?({DATE_RE.pattern}|\d{{4}}-\d{{2}}-\d{{2}}|\d{{1,2}}/\d{{1,2}}/\d{{4}}|\d{{1,2}}\.\d{{1,2}}\.\d{{4}})", re.I)
    def one(it):
        try:
            r = get(it["url"])
            if r.status_code >= 400:
                # some academy sites block scripts (403). allow_blocked seeds were checked by hand, keep them only while the deadline is ahead
                dl = parse_date(it.get("deadline"))
                if it.get("allow_blocked") and r.status_code in (401, 403) and dl and dl >= today:
                    x = job(it["title"], it["org"], it["location"], it["url"], it.get("source", "Employer site"), parse_date(it.get("posted")), dl,
                            tag=it.get("tag"), remote=it.get("remote", False))
                    if it.get("note"): x["note"] = it["note"]
                    x["link_ok"] = True
                    return x
                return None
            txt = clean(re.sub(r"(?is)<script\b.*?</script>", " ", r.text))  # Next.js pages embed their 404 template in scripts
            if CLOSED.search(txt): return None
            pm, cm = POSTED.search(txt), CLOSE.search(txt)
            posted = parse_date(pm[1]) if pm else parse_date(it.get("posted"))
            close = parse_date(cm[1].replace(".", "/")) if cm else parse_date(it.get("deadline"))
            if close and close < today: return None
            if not close and not (posted and (today - posted).days <= MAX_AGE): return None
            x = job(it["title"], it["org"], it["location"], it["url"], it.get("source", "Employer site"), posted, close,
                    tag=it.get("tag"), remote=it.get("remote", False))
            if it.get("note"): x["note"] = it["note"]
            x["link_ok"] = True
            return x
        except Exception:
            return None
    with cf.ThreadPoolExecutor(6) as ex:
        return [x for x in ex.map(one, items) if x]

def hirehive(sub, org, ok, tag=None):
    j = get(f"https://{sub}.hirehive.com/api/v1/jobs").json()
    out = []
    for p in j.get("jobs", []):
        if not ok(p["title"]): continue
        loc = p.get("location") or ""
        c = (p.get("country") or {}).get("name")
        if c and c not in loc: loc = f"{loc}, {c}" if loc else c
        d = dt.datetime.fromtimestamp(p["publishedDate"], dt.timezone.utc).date() if p.get("publishedDate") else None
        out.append(job(p["title"], org, loc, p["hostedUrl"], "HireHive", d, tag=tag))
    return out

# ---------------------------------------------------------------- remote boards
def himalayas(queries, ok):
    out, seen = [], set()
    for q in queries:
        j = get(f"https://himalayas.app/jobs/api/search?q={requests.utils.quote(q)}").json()
        for p in j.get("jobs", []):
            if p["guid"] in seen or not ok(p["title"]): continue
            seen.add(p["guid"])
            locs = p.get("locationRestrictions") or []
            loc = "Remote, India eligible" if "India" in locs else ("Remote, worldwide" if not locs else "Remote")
            exp = parse_date(p.get("expiryDate"))
            r = job(p["title"], p["companyName"], loc, p["guid"], "Himalayas", parse_date(p.get("pubDate")), remote=True)
            r["region"] = "Remote"; r["_expires"] = iso(exp); r["type"] = p.get("employmentType") or ""
            out.append(r)
    return out

def remotive(category, ok):
    j = get(f"https://remotive.com/api/remote-jobs?category={category}&limit=100").json()
    out = []
    for p in j.get("jobs", []):
        if not ok(p["title"]): continue
        r = job(p["title"], p["company_name"], "Remote, " + (p.get("candidate_required_location") or "worldwide"), p["url"], "Remotive",
                parse_date(p.get("publication_date")), remote=True)
        r["region"] = "Remote"; out.append(r)
    return out

def wwr(feed, ok):
    f = feedparser.parse(get(feed).content)
    out = []
    for e in f.entries:
        org, _, title = e.title.partition(": ")
        if not title: title, org = e.title, ""
        if not ok(title): continue
        r = job(title, org, "Remote, " + (e.get("region") or "worldwide"), e.link, "We Work Remotely", parse_date(e.get("published")), remote=True)
        r["region"] = "Remote"; out.append(r)
    return out

def workingnomads(ok):
    j = get("https://www.workingnomads.com/api/exposed_jobs/").json()
    out = []
    for p in j:
        if not ok(p["title"]): continue
        r = job(p["title"], p["company_name"], "Remote, " + (p.get("location") or "worldwide"), p["url"], "Working Nomads", parse_date(p.get("pub_date")), remote=True)
        r["region"] = "Remote"; out.append(r)
    return out

def dribbble(ok):
    f = feedparser.parse(get("https://dribbble.com/jobs.rss").content)
    out = []
    for e in f.entries:
        m = re.match(r"(.+?) is hiring for a position of (.+?)(?: in (.+))?$", e.title)
        if not m or not ok(m[2]): continue
        loc = m[3] or "Remote"
        out.append(job(m[2], m[1], loc, e.link.split("?")[0], "Dribbble", parse_date(e.get("published")), remote=("remote" in loc.lower())))
    return out

def archinect(ok):
    out = []
    f = feedparser.parse(get("https://archinect.com/feed/11/jobs").content)
    for e in f.entries:
        m = re.match(r"(.+?) seeking (.+?) in (.+)$", clean(e.title))
        if not m or not ok(m[2]): continue
        out.append(job(m[2], m[1], m[3], e.link, "Archinect", parse_date(e.get("published"))))
    # Remote board page: titles only on the list, so read each entry page for firm, place and date.
    t = get("https://archinect.com/jobs/region/Remote/all/remote").text
    links = sorted(set(re.findall(r'href="(/jobs/entry/\d+/[^"]+)"', t)), reverse=True)[:14]
    def one(path):
        try:
            p = get("https://archinect.com" + path).text
            og = re.search(r'property="og:title" content="([^"]+)"', p)
            tm = re.match(r"\s*(.+?) (?:is hiring|seeking)(?: -)? (.+?) in (.+)$", clean(og[1])) if og else None
            if not tm or not ok(tm[2]): return None
            d = re.search(r'"datePosted"\s*:\s*"([^"]+)"', p)
            r = job(tm[2], tm[1], tm[3] + " (Remote)", "https://archinect.com" + path, "Archinect", parse_date(d[1]) if d else None, remote=True)
            r["region"] = "India" if INDIA.search(tm[3]) else "Remote"
            return r
        except Exception:
            return None
    with cf.ThreadPoolExecutor(4) as ex:
        out += [r for r in ex.map(one, links) if r]
    return out

# ---------------------------------------------------------------- schools
def kis():
    base = "https://www.kis.in"
    t = get(base + "/careers/open-positions").text
    out = []
    for path in sorted(set(re.findall(r'href="(/careers/open-positions/[^"#?]+)"', t))):
        p = get(base + path).text
        h = re.search(r"<h1[^>]*>(.*?)</h1>", p, re.S) or re.search(r"<title>(.*?)</title>", p, re.S)
        title = clean(h[1]).split(" - Kodaikanal")[0] if h else ""
        if not teach_ok(title + " teacher" if re.search(r"english|math|science|literature|language|music|voice|choir", title, re.I) else title):
            continue
        if re.search(r"english|literature|science|math|history|language", title, re.I) and "teacher" not in title.lower():
            title = title + " Teacher"
        jd = re.search(r"Joining Date:?\s*</?[^>]*>?\s*([0-9]{1,2} [A-Za-z]+ [0-9]{4})", p)
        r = job(title, "Kodaikanal International School", "Kodaikanal, India", base + path, "School site", None, tag="Teacher")
        if jd: r["note"] = "Joins " + clean(jd[1])
        out.append(r)
    return out

def asb():
    url = "https://www.asbindia.org/join-our-school/work-at-asb"
    t = clean(get(url).text)
    m = re.search(r"(20\d\d)\s*[-]\s*(20\d\d) START(.*?)Apply", t)
    out = []
    if not m: return out
    start = f"{m[1]} to {m[2]}"
    names = re.findall(r"((?:International Baccalaureate|Elementary|Middle|High|Middle and High)[^|]*?(?:Teacher(?: Leader)?|Coordinator / Teacher|Counselor)(?: \(TENTATIVE\))?(?::[^|]*?(?:Grade \d|Kindergarten to Grade \d))?)", m[3])
    for n in names:
        n = clean(n)
        if "TENTATIVE" in n or not teach_ok(n): continue
        r = job(n, "American School of Bombay", "Mumbai, India", url, "School site", None, tag="Teacher")
        r["note"] = f"Starts {start}"
        out.append(r)
    return out

# Student opportunities: official programme pages. Each is listed only if its page, fetched this run,
# shows an application or registration deadline between today and 150 days ahead.
STUDENT_PROGRAMS = [
    ("Earth Prize environmental competition (ages 13 to 19)", "The Earth Prize", "Online", "https://www.theearthprize.org/competition"),
    ("Non-Trivial research fellowship (ages 14 to 20)", "Non-Trivial", "Online", "https://www.non-trivial.org/faqs"),
    ("Research Science Institute summer research programme", "Center for Excellence in Education", "MIT, Cambridge, USA", "https://www.cee.org/programs/apply-rsi"),
    ("Summer Science Program research camp", "Summer Science Program", "USA", "https://ssp.org/application/"),
    ("Yale Young Global Scholars summer programme", "Yale University", "New Haven, USA", "https://globalscholars.yale.edu/how-apply/application-deadlines"),
    ("Technovation Girls app and AI challenge", "Technovation", "Online", "https://technovationchallenge.org/competition/"),
    ("Conrad Challenge innovation competition", "Conrad Challenge", "Online", "https://conrad.spacecenter.org/the-challenge/innovation-stage/"),
    ("Diamond Challenge entrepreneurship competition", "University of Delaware", "Online", "https://diamondchallenge.org/competition/"),
    ("Techkriti Open School Championship (Classes 6 to 12)", "IIT Kanpur Techkriti", "Kanpur, India", "https://tosc.techkriti.org/"),
    ("PROMYS India mathematics programme", "PROMYS India", "Bengaluru, India", "https://promysindia.org/"),
    ("International Youth Math Challenge", "IYMC", "Online", "https://www.iymc.info/"),
    ("Pioneer Academics online research programme", "Pioneer Academics", "Online", "https://pioneeracademics.com/apply/"),
    ("Immerse Education essay competition", "Immerse Education", "Online", "https://www.immerse.education/essay-competition/"),
    ("John Locke Institute essay competition", "John Locke Institute", "Online", "https://www.johnlockeinstitute.com/essay-competition"),
    ("MIT Beaver Works Summer Institute", "MIT Lincoln Laboratory", "USA", "https://beaverworks.ll.mit.edu/CMS/bw/bwsi"),
    ("WriteToWin Winter Environmental Article Competition", "Better Human Life Foundation", "India", "https://wiwitness.com/opportunities/writetowin-winter-environmental-article-writing-competition"),
]

MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec"
DATE_RE = re.compile(rf"\b(?:(\d{{1,2}})(?:st|nd|rd|th)?\s+({MONTHS})\.?,?\s+(20\d\d)|({MONTHS})\.?\s+(\d{{1,2}})(?:st|nd|rd|th)?,?\s+(20\d\d))\b")
KEY_RE = re.compile(r"deadline|apply by|applications? (?:close|due|open)|registration|register by|closes|due date|last date|submit", re.I)

def program_deadline(text, today):
    best = None
    for m in DATE_RE.finditer(text):
        d_, mo, y = (m[1], m[2], m[3]) if m[1] else (m[5], m[4], m[6])
        try: d = dt.datetime.strptime(f"{int(d_)} {mo[:3]} {y}", "%d %b %Y").date()
        except ValueError: continue
        if not (today <= d <= today + dt.timedelta(days=150)): continue
        ctx = text[max(0, m.start() - 160): m.start() + 20]
        if KEY_RE.search(ctx) and (best is None or d < best): best = d
    return best

def students(today):
    def one(p):
        title, org, loc, url = p
        try:
            r = get(url)
            if r.status_code >= 400: return None, f"{org}: HTTP {r.status_code}"
            d = program_deadline(clean(r.text), today)
            if not d: return None, f"{org}: no upcoming deadline on page"
            x = job(title, org, loc, url, "Programme site", None, d, tag="Student", remote=(loc == "Online"))
            x["link_ok"] = True
            return x, None
        except Exception as e:
            return None, f"{org}: {type(e).__name__}"
    with cf.ThreadPoolExecutor(8) as ex:
        res = list(ex.map(one, STUDENT_PROGRAMS))
    return [r for r, _ in res if r], [e for _, e in res if e]

# ---------------------------------------------------------------- editions
def sources_for(ed, today):
    S = []
    if ed == "ux":
        ok = ux_ok
        for t, o in [("razorpaysoftwareprivatelimited", "Razorpay"), ("glance", "Glance"), ("thoughtworks", "Thoughtworks"), ("agoda", "Agoda"), ("groww", "Groww"), ("slice", "slice"), ("inmobi", "InMobi"),
                     ("druva", "Druva"), ("figma", "Figma"), ("airbnb", "Airbnb"), ("dropbox", "Dropbox"), ("pinterest", "Pinterest"),
                     ("discord", "Discord"), ("reddit", "Reddit"), ("asana", "Asana"), ("intercom", "Intercom"), ("duolingo", "Duolingo"),
                     ("coinbase", "Coinbase"), ("squarespace", "Squarespace"), ("gitlab", "GitLab"), ("monzo", "Monzo"), ("wise", "Wise"),
                     ("mercury", "Mercury"), ("gusto", "Gusto"), ("instacart", "Instacart"), ("robinhood", "Robinhood"), ("brex", "Brex"),
                     ("toast", "Toast"), ("samsara", "Samsara"), ("twilio", "Twilio"), ("okta", "Okta"), ("elastic", "Elastic"),
                     ("mongodb", "MongoDB"), ("cloudflare", "Cloudflare"), ("databricks", "Databricks"), ("stripe", "Stripe"), ("deliveroo", "Deliveroo")]:
            S.append((f"Greenhouse {o}", lambda t=t, o=o: greenhouse(t, o, ok)))
        for t, o in [("cred", "CRED"), ("mindtickle", "Mindtickle"), ("zeta", "Zeta"), ("meesho", "Meesho"), ("paytm", "Paytm"), ("spotify", "Spotify"), ("palantir", "Palantir")]:
            S.append((f"Lever {o}", lambda t=t, o=o: lever(t, o, ok)))
        for t, o in [("notion", "Notion"), ("linear", "Linear"), ("ramp", "Ramp"), ("openai", "OpenAI"), ("perplexity", "Perplexity"),
                     ("replit", "Replit"), ("posthog", "PostHog"), ("supabase", "Supabase"), ("cursor", "Cursor"), ("miro", "Miro"),
                     ("elevenlabs", "ElevenLabs"), ("sierra", "Sierra"), ("harvey", "Harvey"), ("plaid", "Plaid"), ("atlan", "Atlan"), ("sarvam", "Sarvam AI")]:
            S.append((f"Ashby {o}", lambda t=t, o=o: ashby(t, o, ok)))
        for c, o in [("Freshworks", "Freshworks"), ("Swiggy", "Swiggy"), ("phonepelimited", "PhonePe"), ("ServiceNow", "ServiceNow"), ("Canva", "Canva")]:
            S.append((f"SmartRecruiters {o}", lambda c=c, o=o: smartrecruiters(c, o, ok)))
        S.append(("SmartRecruiters Bosch", lambda: smartrecruiters("BoschGroup", "Bosch", ok, q="UX")))
        for h, t, s, o in [("adobe.wd5.myworkdayjobs.com", "adobe", "external_experienced", "Adobe"),
                           ("autodesk.wd1.myworkdayjobs.com", "autodesk", "Ext", "Autodesk"),
                           ("salesforce.wd12.myworkdayjobs.com", "salesforce", "External_Career_Site", "Salesforce"),
                           ("paypal.wd1.myworkdayjobs.com", "paypal", "jobs", "PayPal"),
                           ("mastercard.wd1.myworkdayjobs.com", "mastercard", "CorporateCareers", "Mastercard"),
                           ("cisco.wd5.myworkdayjobs.com", "cisco", "Cisco_Careers", "Cisco")]:
            S.append((f"Workday {o}", lambda h=h, t=t, s=s, o=o: workday(h, t, s, o, ok, ["UX designer India", "product designer", "UX"], today)))
        S.append(("Direct postings (seeds_ux.json)", lambda: seeds("ux", today)))
        S += [("Himalayas", lambda: himalayas(["ux designer", "product designer", "ux researcher", "content designer", "graphic designer", "industrial designer", "interior designer", "visual designer"], ok)),
              ("Remotive", lambda: remotive("design", ok)),
              ("We Work Remotely", lambda: wwr("https://weworkremotely.com/categories/remote-design-jobs.rss", ok)),
              ("Working Nomads", lambda: workingnomads(ok)),
              ("Dribbble jobs RSS", lambda: dribbble(ok))]
    elif ed == "arch":
        ok = arch_ok
        S += [("Archinect jobs feed", lambda: archinect(ok)),
              ("Workday AtkinsRealis", lambda: workday("slihrms.wd3.myworkdayjobs.com", "slihrms", "Careers", "AtkinsR\u00e9alis", ok,
                                                       ["architect India", "BIM India", "sustainability India", "architect", "landscape architect", "urban design"], today)),
              ("Workday Surbana Jurong", lambda: workday("surbanajurong.wd3.myworkdayjobs.com", "surbanajurong", "SJ_Careers", "Surbana Jurong", ok,
                                                         ["architect", "BIM", "landscape", "urban design", "planner"], today)),
              ("Workday JLL", lambda: workday("jll.wd1.myworkdayjobs.com", "jll", "jllcareers", "JLL", ok, ["architect India", "BIM India", "sustainability India"], today)),
              ("RINA career site", lambda: successfactors("https://careers.rina.org", "RINA", ok, "architect")),
              ("AECOM careers RSS", lambda: dotjobs("aecom.jobs", "AECOM", ok, ["architect", "landscape", "urban design", "planner", "sustainability", "BIM", "interior design"])),
              ("Stantec careers RSS", lambda: dotjobs("stantec.jobs", "Stantec", ok, ["architect", "landscape", "planner"])),
              ("Direct postings (seeds_arch.json)", lambda: seeds("arch", today)),
              ("SmartRecruiters Colliers", lambda: smartrecruiters("Colliers", "Colliers", ok, q="architect")),
              ("Himalayas", lambda: himalayas(["architect", "BIM", "architectural designer", "landscape architect", "urban planner", "sustainability consultant buildings"], ok))]
    elif ed == "schools":
        def t_ok(t): return teach_ok(t)
        S += [("Workday ISP schools", lambda: [dict(x, tag="Teacher") for x in workday("internationalschools.wd3.myworkdayjobs.com", "internationalschools", "ISPCareers",
                                                       "International Schools Partnership", t_ok, ["teacher India", "IB teacher", "Cambridge teacher", "teacher"], today, pages=3)]),
              ("Nord Anglia career site", lambda: [dict(x, tag="Teacher") for x in
                                                   successfactors("https://careers.nordanglia.com", "Nord Anglia Education", t_ok, "India")
                                                   + successfactors("https://careers.nordanglia.com", "Nord Anglia Education", t_ok, "IB+teacher")]),
              ("Kodaikanal International School", kis),
              ("Woodstock School (HireHive)", lambda: hirehive("woodstock-school", "Woodstock School", t_ok, tag="Teacher")),
              ("American School of Bombay", asb),
              ("Direct postings (seeds_schools.json)", lambda: seeds("schools", today))]
    elif ed in ("sustainability", "startups", "highered", "consulting", "health", "marketing", "finance", "aviation", "business", "healing", "ai", "packaging", "fashion", "realestate", "auto"):
        S += field_sources(ed, today)
    return S

def _ats(S, ok, gh=(), lv=(), ab=(), sr=()):
    for t, o in gh: S.append((f"Greenhouse {o}", lambda t=t, o=o: greenhouse(t, o, ok)))
    for t, o in lv: S.append((f"Lever {o}", lambda t=t, o=o: lever(t, o, ok)))
    for t, o in ab: S.append((f"Ashby {o}", lambda t=t, o=o: ashby(t, o, ok)))
    for c, o in sr: S.append((f"SmartRecruiters {o}", lambda c=c, o=o: smartrecruiters(c, o, ok)))

def _wd(S, ok, today, sites, queries, pages=1):
    for h, t, s, o in sites:
        S.append((f"Workday {o}", lambda h=h, t=t, s=s, o=o: workday(h, t, s, o, ok, queries, today, pages)))

WD = {"pwc": ("pwc.wd3.myworkdayjobs.com", "pwc", "Global_Experienced_Careers", "PwC"),
      "accenture": ("accenture.wd103.myworkdayjobs.com", "accenture", "AccentureCareers", "Accenture"),
      "erm": ("erm.wd3.myworkdayjobs.com", "erm", "ERM_Careers", "ERM"),
      "spgi": ("spgi.wd5.myworkdayjobs.com", "spgi", "SPGI_Careers", "S&P Global"),
      "lseg": ("lseg.wd3.myworkdayjobs.com", "lseg", "Careers", "LSEG"),
      "unilever": ("unilever.wd3.myworkdayjobs.com", "unilever", "Unilever_Experienced_Professionals", "Unilever"),
      "gartner": ("gartner.wd5.myworkdayjobs.com", "gartner", "EXT", "Gartner"),
      "kantar": ("kantar.wd3.myworkdayjobs.com", "kantar", "KANTAR", "Kantar"),
      "relx": ("relx.wd3.myworkdayjobs.com", "relx", "relx", "RELX"),
      "mastercard": ("mastercard.wd1.myworkdayjobs.com", "mastercard", "CorporateCareers", "Mastercard"),
      "paypal": ("paypal.wd1.myworkdayjobs.com", "paypal", "jobs", "PayPal"),
      "blackrock": ("blackrock.wd1.myworkdayjobs.com", "blackrock", "BlackRock_Professional", "BlackRock"),
      "statestreet": ("statestreet.wd1.myworkdayjobs.com", "statestreet", "Global", "State Street"),
      "barclays": ("barclays.wd3.myworkdayjobs.com", "barclays", "External_Career_Site_Barclays", "Barclays"),
      "citi": ("citi.wd5.myworkdayjobs.com", "citi", "2", "Citi"),
      "novartis": ("novartis.wd3.myworkdayjobs.com", "novartis", "Novartis_Careers", "Novartis"),
      "astrazeneca": ("astrazeneca.wd3.myworkdayjobs.com", "astrazeneca", "Careers", "AstraZeneca"),
      "gsk": ("gsk.wd5.myworkdayjobs.com", "gsk", "GSKCareers", "GSK"),
      "pfizer": ("pfizer.wd1.myworkdayjobs.com", "pfizer", "PfizerCareers", "Pfizer"),
      "philips": ("philips.wd3.myworkdayjobs.com", "philips", "jobs-and-careers", "Philips"),
      "medtronic": ("medtronic.wd1.myworkdayjobs.com", "medtronic", "MedtronicCareers", "Medtronic"),
      "abbott": ("abbott.wd5.myworkdayjobs.com", "abbott", "abbottcareers", "Abbott"),
      "jj": ("jj.wd5.myworkdayjobs.com", "jj", "JJ", "Johnson & Johnson"),
      "gehc": ("gehc.wd5.myworkdayjobs.com", "gehc", "GEHC_ExternalSite", "GE HealthCare"),
      "airbus": ("ag.wd3.myworkdayjobs.com", "ag", "Airbus", "Airbus"),
      "boeing": ("boeing.wd1.myworkdayjobs.com", "boeing", "EXTERNAL_CAREERS", "Boeing"),
      "geaero": ("geaerospace.wd5.myworkdayjobs.com", "geaerospace", "GE_ExternalSite", "GE Aerospace"),
      "rtx": ("globalhr.wd5.myworkdayjobs.com", "globalhr", "REC_RTX_Ext_Gateway", "RTX"),
      "cae": ("cae.wd3.myworkdayjobs.com", "cae", "career", "CAE")}
INDIA_GH = [("razorpaysoftwareprivatelimited", "Razorpay"), ("groww", "Groww"), ("glance", "Glance"), ("inmobi", "InMobi"), ("druva", "Druva"), ("slice", "slice")]
INDIA_LV = [("paytm", "Paytm"), ("meesho", "Meesho"), ("zeta", "Zeta"), ("cred", "CRED")]
GLOBAL_GH = [("stripe", "Stripe"), ("databricks", "Databricks"), ("coinbase", "Coinbase"), ("agoda", "Agoda"), ("airbnb", "Airbnb"), ("pinterest", "Pinterest"), ("reddit", "Reddit"), ("duolingo", "Duolingo")]

def ey(queries, ok):
    """EY careers (SuccessFactors) India search, newest first, with the posting date read from each job page."""
    out, seen = [], set()
    for q in queries:
        for j in successfactors("https://careers.ey.com", "EY", ok, requests.utils.quote(q), "&locationsearch=India"):
            if j["url"] not in seen: seen.add(j["url"]); out.append(j)
    with cf.ThreadPoolExecutor(6) as ex:
        for j, d in zip(out, ex.map(lambda j: sf_date(j["url"]), out)): j["posted"] = iso(d) if d else None
    return out

def field_sources(ed, today):
    """Sources for the eight newer field editions. Workday, Greenhouse, Lever and Ashby boards were probed on
    25 Oct 2026 and answer with live listings. Seeds hold direct postings found with web search."""
    S = []
    w = lambda *k: [WD[x] for x in k]
    if ed == "sustainability":
        ok = sus_ok
        _wd(S, ok, today, w("erm", "pwc", "accenture", "spgi", "lseg", "unilever"), ["sustainability India", "ESG India", "climate", "ESG", "sustainability"], pages=2)
        _ats(S, ok, gh=[("patch", "Patch"), ("carbondirect", "Carbon Direct"), ("watershed", "Watershed")] + INDIA_GH,
             ab=[("watershed", "Watershed"), ("sylvera", "Sylvera"), ("sweep", "Sweep")], lv=[("ashoka", "Ashoka")] + INDIA_LV)
        S.append(("EY careers India", lambda: ey(["ESG", "climate", "sustainability"], ok)))
        S.append(("Himalayas", lambda: himalayas(["sustainability", "ESG", "climate", "carbon"], ok)))
    elif ed == "startups":
        ok = any_ok
        _ats(S, ok, gh=INDIA_GH, lv=INDIA_LV, ab=[("sarvam", "Sarvam AI"), ("crisp", "Crisp"), ("ycombinator", "Y Combinator")])
        S.append(("Himalayas", lambda: himalayas(["startup founding", "early stage startup", "founding engineer", "founder associate"], ok)))
        S.append(("Remotive", lambda: remotive("all-others", ok)))
    elif ed == "highered":
        ok = highered_ok
        _ats(S, ok, gh=INDIA_GH + [("coursera", "Coursera"), ("duolingo", "Duolingo"), ("khanacademy", "Khan Academy"), ("udemy", "Udemy")],
             lv=INDIA_LV, ab=[("sarvam", "Sarvam AI"), ("outschool", "Outschool")])
        _wd(S, ok, today, w("pwc", "accenture", "relx", "mastercard", "citi", "novartis", "airbus"), ["graduate trainee India", "graduate programme", "entry level India", "analyst India", "research assistant"])
        S.append(("Himalayas", lambda: himalayas(["education", "admissions", "curriculum", "instructional designer", "academic advisor", "student success", "university"], ok)))
    elif ed == "consulting":
        ok = cons_ok
        _wd(S, ok, today, w("pwc", "accenture", "gartner", "erm", "kantar", "spgi"), ["consultant India", "strategy India", "analyst India", "consultant", "associate"], pages=2)
        _ats(S, ok, gh=[("alixpartners", "AlixPartners"), ("thoughtworks", "Thoughtworks")] + INDIA_GH, lv=INDIA_LV)
        S.append(("EY careers India", lambda: ey(["consultant", "strategy", "Parthenon"], ok)))
        S.append(("Himalayas", lambda: himalayas(["consultant", "strategy analyst", "management consultant"], ok)))
    elif ed == "health":
        ok = any_ok
        _wd(S, ok, today, w("novartis", "astrazeneca", "gsk", "pfizer", "philips", "medtronic", "abbott", "jj", "gehc"), ["India", "Bengaluru", "Mumbai", "Hyderabad"], pages=1)
        _ats(S, ok, gh=[("zocdoc", "Zocdoc"), ("oura", "Oura"), ("flatironhealth", "Flatiron Health")])
        S.append(("Himalayas", lambda: himalayas(["healthcare", "clinical", "health tech", "medical"], ok)))
    elif ed == "marketing":
        ok = mkt_ok
        _ats(S, ok, gh=INDIA_GH + GLOBAL_GH, lv=INDIA_LV, ab=[("sarvam", "Sarvam AI")])
        _wd(S, ok, today, w("unilever", "kantar", "mastercard", "paypal", "accenture"), ["marketing India", "brand India", "marketing"])
        S += [("Himalayas", lambda: himalayas(["marketing", "content marketing", "growth marketing", "social media", "brand"], ok)),
              ("Remotive", lambda: remotive("marketing", ok)),
              ("We Work Remotely", lambda: wwr("https://weworkremotely.com/categories/remote-sales-and-marketing-jobs.rss", ok))]
    elif ed == "finance":
        ok = fin_ok
        _wd(S, ok, today, w("mastercard", "paypal", "blackrock", "statestreet", "barclays", "citi", "spgi", "lseg"), ["India", "analyst India", "finance"], pages=2)
        _ats(S, ok, gh=INDIA_GH + [("stripe", "Stripe"), ("coinbase", "Coinbase"), ("robinhood", "Robinhood"), ("sofi", "SoFi"), ("chime", "Chime"), ("affirm", "Affirm"), ("wise", "Wise"), ("monzo", "Monzo")],
             lv=INDIA_LV, ab=[("nubank", "Nubank")])
        S.append(("Himalayas", lambda: himalayas(["finance", "accountant", "financial analyst", "fintech"], ok)))
    elif ed == "business":
        ok = biz_ok
        _wd(S, ok, today, w("pwc", "accenture", "unilever", "mastercard", "citi", "spgi", "gartner"), ["business development India", "operations India", "procurement India", "strategy India", "sales India"], pages=2)
        _ats(S, ok, gh=INDIA_GH, lv=INDIA_LV)
        S.append(("EY careers India", lambda: ey(["business development", "strategy", "operations"], ok)))
        S.append(("Himalayas", lambda: himalayas(["business development", "operations manager", "procurement", "sales manager", "strategy"], ok)))
    elif ed == "ai":
        ok = ai_ok
        _ats(S, ok, gh=[("anthropic", "Anthropic"), ("scaleai", "Scale AI"), ("databricks", "Databricks"), ("deepmind", "Google DeepMind"), ("glean", "Glean")] + INDIA_GH,
             lv=[("mistral", "Mistral AI")] + INDIA_LV, ab=[("openai", "OpenAI"), ("sarvam", "Sarvam AI"), ("cohere", "Cohere"), ("perplexity", "Perplexity")])
        S.append(("Himalayas", lambda: himalayas(["machine learning engineer", "AI engineer", "data scientist", "LLM", "applied scientist", "MLOps"], ok)))
    elif ed == "packaging":
        ok = pkg_ok
        _wd(S, ok, today, [("amcor.wd5.myworkdayjobs.com", "amcor", "Amcor_External_Career_Site", "Amcor"),
                           ("huhtamaki.wd103.myworkdayjobs.com", "huhtamaki", "DirectsExternal", "Huhtamaki"),
                           ("dow.wd1.myworkdayjobs.com", "dow", "ExternalCareers", "Dow")], ["India", "packaging", "plastics"], pages=2)
        S.append(("Himalayas", lambda: himalayas(["packaging engineer", "packaging technologist", "plastics engineer", "polymer", "flexible packaging", "recycling"], ok)))
    elif ed == "fashion":
        ok = fash_ok
        _ats(S, ok, gh=[("lululemon", "lululemon"), ("nike", "Nike"), ("allbirds", "Allbirds"), ("warbyparker", "Warby Parker"), ("everlane", "Everlane"), ("patagonia", "Patagonia")] + INDIA_GH,
             lv=INDIA_LV, ab=[("reformation", "Reformation"), ("therealreal", "The RealReal")])
        S.append(("Himalayas", lambda: himalayas(["fashion designer", "fashion merchandiser", "apparel", "jewellery", "jewelry", "textile", "footwear", "retail buyer", "visual merchandiser"], ok)))
    elif ed == "auto":
        ok = auto_ok
        _ats(S, ok, gh=[("tesla", "Tesla"), ("rivian", "Rivian"), ("lucidmotors", "Lucid"), ("zoox", "Zoox"), ("chargepoint", "ChargePoint")] + INDIA_GH,
             lv=INDIA_LV,
             ab=[("nuro", "Nuro")])
        # EV charging OEM board: keep India roles even when the title omits "auto"/"charging"
        def _cp_india():
            loose = lambda t: bool(t) and not AUTO_NO.search(t) and not re.search(r"intern(ship)?s?", t, re.I)
            return [j for j in greenhouse("chargepoint", "ChargePoint", loose) if j.get("region") == "India"]
        S.append(("Greenhouse ChargePoint India", _cp_india))
        _wd(S, ok, today, w("pwc", "accenture", "unilever"),
            ["automotive India", "automobile India", "EV India", "electric vehicle", "vehicle", "mobility India", "dealer India"], pages=2)
        S.append(("Himalayas India auto", lambda: himalayas([
            "automotive India", "automobile India", "EV India", "electric vehicle India",
            "sales consultant automotive", "service advisor", "automotive engineer", "powertrain engineer",
            "battery engineer", "charging infrastructure", "fleet manager", "automotive quality engineer",
            "dealership", "tyre", "auto component"
        ], ok)))
        S.append(("Remotive", lambda: remotive("all-others", ok)))
    elif ed == "realestate":
        ok = re_ok
        _ats(S, ok, gh=[("cbre", "CBRE"), ("jll", "JLL"), ("cushwake", "Cushman & Wakefield"), ("colliers", "Colliers")] + INDIA_GH,
             lv=[("proptiger", "PropTiger"), ("housing", "Housing.com")], ab=[("redfin", "Redfin"), ("zillow", "Zillow"), ("compass", "Compass")])
        def _broker_india(tok, org):
            loose = lambda t: bool(t) and not RE_NO.search(t) and not re.search(r"intern(ship)?s?", t, re.I)
            return [j for j in greenhouse(tok, org, loose) if j.get("region") == "India"]
        S.append(("Greenhouse CBRE India", lambda: _broker_india("cbre", "CBRE")))
        S.append(("Greenhouse JLL India", lambda: _broker_india("jll", "JLL")))
        S.append(("Greenhouse Cushman India", lambda: _broker_india("cushwake", "Cushman & Wakefield")))
        _wd(S, ok, today, w("pwc", "accenture", "unilever"), ["real estate India", "property India", "facilities India", "quantity surveyor India", "valuation India", "property manager"], pages=2)
        S.append(("Himalayas", lambda: himalayas(["real estate", "property manager", "facility manager", "facilities manager", "valuation", "proptech", "leasing manager", "quantity surveyor", "site engineer", "real estate India", "property manager India", "facility manager India", "leasing India"], ok)))
    elif ed == "healing":
        ok = heal_ok
        _ats(S, ok, gh=[("talkspace", "Talkspace"), ("calm", "Calm"), ("oura", "Oura")], lv=[("lyrahealth", "Lyra Health")])
        S.append(("Himalayas", lambda: himalayas(["wellness", "mental health therapist", "counselor", "yoga instructor", "nutritionist", "health coach", "meditation"], ok)))
    elif ed == "aviation":
        ok = av_ok
        _wd(S, ok, today, w("airbus", "boeing", "geaero", "rtx", "cae"), ["India", "Bengaluru", "pilot", "aircraft", "engineer"], pages=2)
        _ats(S, ok, gh=[("heartaerospace", "Heart Aerospace")])
    S.append((f"Direct postings (seeds_{ed}.json)", lambda: seeds(ed, today)))
    return S

# ---------------------------------------------------------------- main
CHALLENGE_OK = {"Himalayas"}  # Cloudflare challenge for scripts, API confirms the posting is live (expiryDate)

def link_ok(j):
    try:
        r = get(j["url"], allow_redirects=True, stream=True)
        code = r.status_code
        body = r.raw.read(4000, decode_content=True).decode("utf-8", "ignore") if code == 403 else ""
        r.close()
        if code < 400: return True
        if code == 403 and j["source"] in CHALLENGE_OK and "Just a moment" in body:
            j["link_note"] = "Cloudflare check for scripts, API shows live"
            return True
        return False
    except Exception:
        return False

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("edition", choices=["ux", "arch", "schools", "sustainability", "startups", "highered", "consulting", "health", "marketing", "finance", "aviation", "business", "healing", "ai", "packaging", "fashion", "realestate", "auto"])
    ap.add_argument("--date", default=dt.date.today().isoformat())
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    today = dt.date.fromisoformat(a.date)
    out = a.out or os.path.join(HERE, f"jobs_{a.edition}_{a.date}.json")

    status, pool = {}, []
    with cf.ThreadPoolExecutor(10) as ex:
        futs = {ex.submit(fn): name for name, fn in sources_for(a.edition, today)}
        for f in cf.as_completed(futs):
            name = futs[f]
            try:
                r = f.result(); pool += r; status[name] = f"ok {len(r)}"
            except Exception as e:
                status[name] = f"failed: {type(e).__name__} {str(e)[:80]}"
    errs = []
    if a.edition == "schools":
        st, errs = students(today)
        pool += st
        status["Student programme pages"] = f"ok {len(st)} of {len(STUDENT_PROGRAMS)}"

    # no internships, ever (see NO_INTERN)
    n0 = len(pool); pool = [j for j in pool if not is_internship(j)]
    status["Excluded by house rule"] = f"dropped {n0 - len(pool)}"
    # freshness, expiry and dedupe
    fresh, seen_url, seen_key = [], set(), set()
    for j in pool:
        p = parse_date(j.get("posted"))
        if p and (today - p).days > MAX_AGE: continue
        if p and p > today + dt.timedelta(days=1): continue
        dl = parse_date(j.get("deadline"))
        if dl and dl < today: continue
        if j.get("_expires") and parse_date(j["_expires"]) < today: continue
        if not j["title"] or not j["url"]: continue
        key = (j["title"].lower(), j["org"].lower(), j["region"])
        if j["url"] in seen_url or key in seen_key: continue
        seen_url.add(j["url"]); seen_key.add(key); fresh.append(j)

    def sortkey(j):
        return (j.get("posted") or j.get("deadline") or "0000", )
    # pick: India first, then Global, then Remote, max PER_ORG per org, newest first within a region
    _bl = {}
    fresh = blocklist.keep(fresh, "jobs", _bl)  # Begin Group blocklist
    if _bl: blocklist.log(_bl)
    picked = []
    spare = TOTAL
    order = ["India", "Global", "Remote"]
    for reg in order:
        cands = sorted([j for j in fresh if j["region"] == reg], key=lambda j: (j.get("tag") == "Cadet", j["source"] not in CHALLENGE_OK, j.get("posted") or "0000"), reverse=True)
        if a.edition == "schools":  # undated school roles are current career page listings, put deadlines soonest first for students
            cands.sort(key=lambda j: (j.get("tag") != "Teacher", -(int((j.get("posted") or "0000-00-00").replace("-", "")))))
        per_org, chosen = {}, []
        for j in cands:
            if per_org.get(j["org"], 0) >= PER_ORG: continue
            per_org[j["org"]] = per_org.get(j["org"], 0) + 1
            chosen.append(j)
        picked += [j for j in chosen if j.get("tag") != "Student"][: CAP[reg] * 2 + 6] + [j for j in chosen if j.get("tag") == "Student"]  # take extra, link check trims
    # link check
    with cf.ThreadPoolExecutor(12) as ex:
        oks = list(ex.map(lambda j: True if j.get("link_ok") else link_ok(j), picked))
    dead = [j["url"] for j, k in zip(picked, oks) if not k]
    live = [j for j, k in zip(picked, oks) if k]
    studs = [j for j in live if j.get("tag") == "Student"][:10]  # schools: every live student opportunity, then teachers fill the rest
    live = [j for j in live if j.get("tag") != "Student"]
    room = TOTAL - len(studs)
    by = {r: [j for j in live if j["region"] == r] for r in order}
    take = {r: min(CAP[r], len(by[r])) for r in order}
    while sum(take.values()) > room:
        r = max(order[::-1], key=lambda r: take[r] - (100 if r == "India" else 0)); take[r] -= 1
    while sum(take.values()) < room:  # spread unused room to regions that still have listings
        grow = [r for r in order if take[r] < len(by[r])]
        if not grow: break
        r = min(grow, key=lambda r: take[r]); take[r] += 1
    final = [j for r in order for j in by[r][:take[r]] + sorted([x for x in studs if x["region"] == r], key=lambda x: x.get("deadline") or "9999")]

    # jobs_seen
    os.makedirs(os.path.dirname(SEEN), exist_ok=True)
    seen = json.load(open(SEEN)) if os.path.exists(SEEN) else {}
    for j in final:
        j["location"] = tidy_loc(j.get("location") or "") or ("Remote" if j["region"] == "Remote" else "")
        if j["region"] == "India" and "India" not in j["location"]: j["location"] = (j["location"] + ", India").strip(", ")
        j.pop("_expires", None); j.pop("link_ok", None)
        j["id"] = re.sub(r"[?#].*$", "", j["url"]).rstrip("/")
        first = seen.setdefault(j["id"], a.date)
        j["first_seen"] = first
        j["new"] = first == a.date
    json.dump(seen, open(SEEN, "w"), indent=1, sort_keys=True)

    counts = {r: sum(1 for j in final if j["region"] == r) for r in order}
    res = {"edition": a.edition, "date": a.date, "counts": counts, "total": len(final), "sources": dict(sorted(status.items())),
           "notes": errs, "dead_links_dropped": dead, "jobs": final}
    assert not [j for j in final if is_internship(j)], "internship listing slipped through"
    for j in final: j.pop("type", None)
    json.dump(res, open(out, "w"), indent=1, ensure_ascii=False)
    print(f"wrote {out}: {len(final)} jobs {counts}")
    for k, v in sorted(status.items()): print(f"  {k}: {v}")
    for e in errs: print("  note:", e)
    if dead: print("  dead links dropped:", len(dead))

if __name__ == "__main__":
    main()
