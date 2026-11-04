"""Hard blocklist: what Yes Bro must not cover on any paper or the landing page.

1. Begin Group (below). 2. Education fairs and expos in general (FAIR rule further down): fair coverage
is a paid product since 27 Oct 2026, so a fair, expo or roadshow for education, study abroad,
universities or admissions appears only when it has a confirmed paid deal listed in sponsors.json.

Begin Group (begingroup.com, begin-expo.com, Begin Expo, Begin India, Begin fairs, the International
Education Fair by Begin, Begin school visits). Saurabh is negotiating with them and offering coverage,
so no edition gives them any coverage until he confirms a partnership. Remove this block only on his say.

The ordinary word "begin" ("exams begin in February") is never blocked. "Nehru Centre" is blocked only
next to an education fair.

Use
- blocked(x): True when a story, job, event, opp, meme, column or string mentions Begin.
- keep(items, label, counter): drops matching items silently, adds the drop count to counter[label].
- log(counter, out): prints one "BLOCKED: Begin <n> ..." line for the build log.
- guard_html(page, label): final check on built HTML, raises SystemExit if anything slipped through.
"""
import html as _html, json, re, sys
from urllib.parse import urlparse

DOMAINS = ("begingroup", "begin-expo", "beginexpo")
_D = r"(?:begingroup|begin-expo|beginexpo)"
_NEHRU = r"nehru\s+cent(?:re|er)"
_FAIR = r"education(?:al)?\s+(?:fair|expo)s?"
PATTERNS = [
    _D,                                                                        # any domain or handle with begingroup / begin-expo
    r"\bbegin\s+(?:group|expo|india(?!['\u2019]s)|fairs?|education\s+fairs?|school\s+visits?)\b",
    r"\b(?:by|from|with|at|of)\s+begin\s+(?:group|expo|india)\b",
    r"\b(?:organi[sz]ed|hosted|presented|run|powered|brought)\s+by\s+begin\b",
    r"\bbegin['\u2019]s\s+(?:international\s+)?(?:education|fair|expo|school|university|universities|counsel\w*)\b",
    r"\binternational\s+education\s+fairs?\b[^.\n<]{0,40}\b(?:by|from|of)\s+begin\b",   # International Education Fair by Begin
    r"\bbegin\s+international\s+education\s+fairs?\b",
    _NEHRU + r"[\s\S]{0,240}?" + _FAIR, _FAIR + r"[\s\S]{0,240}?" + _NEHRU,  # Nehru Centre only with an education fair
]
RE = re.compile("|".join(f"(?:{p})" for p in PATTERNS), re.I)

# ---- Fairs (paid product). Main subject only: the item's title or URL, never a passing mention in a summary.
_EDU = (r"(?:education(?:al)?|edu|study(?:ing)?[\s-]+(?:abroad|overseas|in\s+[a-z]+)|overseas\s+(?:education|study|studies)|"
        r"universit(?:y|ies)|college|campus|admissions?|higher\s+(?:education|studies)|grad(?:uate)?\s+school|mba|"
        r"masters|scholarships?|international\s+students?|student\s+recruitment)")
_FAIRW = r"(?:fairs?|expos?|exhibitions?|roadshows?|road\s+shows?|melas?|edufairs?|(?<=mba\s)tours?|(?<=school\s)tours?|(?<=masters\s)tours?)"
_NOTFAIR = r"(?!\s+(?:pric\w*|play|share|value|trade|deal|chance|use|treatment|wages?|go|game|enough|access|assessment|evaluation|process|practice|competition|representation|and|or|to)\b)"
FAIR_PATTERNS = [
    _EDU + r"(?:[\s,&-]+[a-z0-9]+){0,3}?[\s-]+" + _FAIRW + r"\b" + _NOTFAIR,           # International Education Fair, Study Abroad Expo, QS World MBA Tour
    r"\b(?:fairs?|expos?|roadshows?)\b" + _NOTFAIR + r"\s+(?:for|on|of)\s+(?:[a-z]+\s+){0,2}" + _EDU,   # fair for study abroad, expo on higher education
    r"\bedu[\s-]?(?:fairs?|expos?)\b",
    r"\bdidac\b",
    r"\bpack\.nxt\b",
    r"\bpacknxt\b",
    r"\b(?:idp|qs|begin|edufair|kc\s+overseas|leverage\s+edu|univariety)\b[^.\n<]{0,30}\b(?:fairs?|expos?|tours?|roadshows?)\b" + _NOTFAIR,
]
# Packaging, plastics and print trade expos are paid too (Yes Bro Packaging, from 27 Oct 2026).
_TRADE = r"(?:packaging|packag\w*|plastics?|polymers?|pack|print(?:ing)?|labels?|converting|recycling|rubber)"
FAIR_PATTERNS += [
    r"\b(?:plastindia|iplex|packex|interpack|pacprocess|pack\s*expo|packexpo|packplus|pack\s*plus|india\s*pack|fachpack|chinaplas|npe\s*20\d\d|"
    r"labelexpo|drupa|plastivision|plastasia|plastics\s+recycling\s+show|propak|printpack|paperex|loupe\s+india|packmach(?:\s+asia)?|gulfood\s+manufacturing|print\s+sangam|all\s+in\s+print|agroprodmash|pamex|indiaplast|plastfocus|k\s*20\d\d\s+(?:trade\s+fair|show|fair)|k\s+(?:show|trade\s+fair))\b",
    _TRADE + r"(?:[\s,&-]+[a-z0-9]+){0,2}?[\s-]+(?:trade\s+)?(?:fairs?|expos?|exhibitions?|trade\s+shows?|roadshows?)\b" + _NOTFAIR,
]

# Fashion and jewellery trade expos are paid too (Yes Bro Fashion, from 29 Oct 2026).
_FASHTRADE = r"(?:jewellery|jewelry|gems?|diamonds?|fashion|apparel|garment|textile|footwear)"
FAIR_PATTERNS += [
    r"\b(?:iijs|india\s+international\s+jewellery\s+show|vicenzaoro|jck\s+las\s+vegas|hong\s+kong\s+jewellery|base\s*lworld|watches\s+and\s+wonders|magic\s+las\s+vegas|prem\s*ière\s+vision|premiere\s+vision|texworld|intertextile|yarn\s+expo|app\s*arelsourcing)\b",
    _FASHTRADE + r"(?:[\s,&-]+[a-z0-9]+){0,2}?[\s-]+(?:trade\s+)?(?:fairs?|expos?|exhibitions?|trade\s+shows?)\b" + _NOTFAIR,
]

# Auto Expo, motor shows and automotive trade expos are paid too (Yes Bro Auto, from 31 Oct 2026).
_AUTOTRADE = r"(?:auto(?:motive)?|automobile|motor|car|vehicle|EV|electric\s+vehicle|mobility)"
FAIR_PATTERNS += [
    r"\b(?:auto\s*expo|bharat\s+mobility(?:\s+global)?\s+expo|delhi\s+auto\s+expo|motor\s+show|geneva\s+international\s+motor\s+show|paris\s+motor\s+show|detroit\s+auto\s+show|iaa\s+mobility|tokyo\s+motor\s+show|auto\s*china|busworld|bauma)\b",
    _AUTOTRADE + r"(?:[\s,&-]+[a-z0-9]+){0,2}?[\s-]+(?:trade\s+)?(?:fairs?|expos?|exhibitions?|trade\s+shows?|motor\s+shows?)\b" + _NOTFAIR,
]

FAIR_RE = re.compile(r"\b(?:" + "|".join(f"(?:{p})" for p in FAIR_PATTERNS) + ")", re.I)

# Known fair organiser domains: an item linking here is dropped, and the publish guard fails any page that links here.
FAIR_DOMAINS = ("didacindia", "didacindia.com", "educationfair.net", "begingroup", "begin-expo", "beginexpo", "edufair", "studyabroadexpo",
                "qsworldmbatour", "qs-mba-tour", "worldgradschooltour", "iefi.in", "eduworldwideindia",
                "plastindia", "interpack.com", "pacprocess", "k-online", "packexindia", "packplus", "packexpo", "chinaplasonline",
                "npe.org", "labelexpo", "drupa.com", "plastivision", "fachpack", "printpack", "paperex", "iplex", "loupeindia", "packmachasia", "printsangam", "indiaplast",
                "iijs.org", "jckopens", "vicenzaoro", "premierevision", "texworld",
                "autoexpo", "autoexpo.in", "bharatmobility", "bharat-mobility", "acma.in/expo")
_TITLE_KEYS = ("headline", "name", "title", "topic", "slug")
_URL_KEYS = ("url", "link", "href")

def _allow():
    """Paid fair partners from sponsors.json ({"fairs": [{"name": ..., "domains": [...]}, ...]}). Empty means none."""
    import os
    f = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sponsors.json")
    try:
        d = json.load(open(f))
    except Exception:
        return [], []
    fairs = d.get("fairs", []) if isinstance(d, dict) else []
    names = [x["name"].lower() for x in fairs if isinstance(x, dict) and x.get("name")]
    doms = [dm.lower() for x in fairs if isinstance(x, dict) for dm in x.get("domains", [])]
    return names, doms

def _subject(x):
    """(title text, list of urls) that state an item's main subject."""
    if isinstance(x, str):
        return x, [u for u in re.findall(r"https?://[^\s\"'<>]+", x)]
    if isinstance(x, dict):
        t = " ".join(str(x.get(k, "")) for k in _TITLE_KEYS if x.get(k))
        us = [str(x[k]) for k in _URL_KEYS if x.get(k)]
        return t, us
    return _text(x), []

def fair_hit(x):
    """The match that makes x a fair or expo item, or None. Allowlisted paid partners return None."""
    t, us = _subject(x)
    names, doms = _allow()
    hosts = [(urlparse(u).netloc or "").lower() for u in us]
    if any(dm and dm in h for dm in doms for h in hosts) or any(n and n in t.lower() for n in names):
        return None
    for h in hosts:
        if any(d in h for d in FAIR_DOMAINS):
            return h
    m = FAIR_RE.search(_html.unescape(t))
    if m:
        return m.group(0)
    for u in us:
        p = urlparse(u)
        m = FAIR_RE.search(re.sub(r"[-_/.]+", " ", p.path))
        if m:
            return m.group(0)
    return None

def reason(x):
    """'Begin', 'fairs' or None."""
    if hit(x) is not None:
        return "Begin"
    if fair_hit(x) is not None:
        return "fairs"
    return None

def _text(x):
    if isinstance(x, str):
        return x
    try:
        return json.dumps(x, ensure_ascii=False)
    except Exception:
        return str(x)

def _urls(x, out):
    if isinstance(x, dict):
        for v in x.values(): _urls(v, out)
    elif isinstance(x, (list, tuple)):
        for v in x: _urls(v, out)
    elif isinstance(x, str) and re.match(r"(?i)https?://", x):
        out.append(x)
    return out

def hit(x):
    """The first blocked match in x (string or JSON-like item), or None."""
    for u in _urls(x, []):
        host = (urlparse(u).netloc or "").lower()
        if any(d in host for d in DOMAINS):
            return host
    t = _html.unescape(_text(x))
    m = RE.search(t)
    return m.group(0) if m else None

def blocked(x):
    return reason(x) is not None

def keep(items, label="items", counter=None):
    """Drop Begin and fair items silently. counter[(why, label)] counts the drops."""
    if not items:
        return items
    out = []
    for i in items:
        why = reason(i)
        if why is None:
            out.append(i)
        elif counter is not None:
            counter[(why, label)] = counter.get((why, label), 0) + 1
    return out

def log(counter, out=None):
    for why in ("Begin", "fairs"):
        c = {lab: v for (w, lab), v in counter.items() if w == why and v}
        detail = ", ".join(f"{k} {v}" for k, v in c.items()) or "nothing matched"
        print(f"BLOCKED: {why} {sum(c.values())} ({detail})", file=out or sys.stdout, flush=True)

def guard_html(page, label="page"):
    """Fail the build when the finished HTML mentions Begin anywhere (copy, links, scripts, meta)."""
    found = sorted({m.group(0)[:80] for m in RE.finditer(_html.unescape(page))})
    names, doms = _allow()
    for h in re.findall(r"""(?i)https?://([^/\s"'<>]+)""", page):
        h = h.lower()
        if any(d in h for d in FAIR_DOMAINS) and not any(dm and dm in h for dm in doms):
            found.append(h)
    found = sorted(set(found))
    if found:
        raise SystemExit(f"BEGIN GUARD: {label} mentions Begin or links a fair organiser, not published: {found}")
