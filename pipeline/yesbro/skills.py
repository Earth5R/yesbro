"""Jobs vs Certifications: reads the day's real job postings (jobs_<ed>_<date>.json) and shows which
skills, software and certifications they ask for. Rebuilt every run from that day's jobs, so it changes
when the job mix changes. Called from build_html.py when the config has "skills_block". Never stops the build."""
import re, json, os, hashlib, html as _h
from concurrent.futures import ThreadPoolExecutor
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skills_cache")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36",
      "Accept-Language": "en"}
I = re.I
# (label, kind, pattern, flags). Kinds: Certification, Software, Skill.
VOCAB = [
 ("LEED", "Certification", r"\bLEED\b", 0),
 ("GRIHA", "Certification", r"\bGRIHA\b", I),
 ("IGBC", "Certification", r"\bIGBC\b", 0),
 ("WELL AP", "Certification", r"\bWELL\s*(AP|Accredited|Building Standard|certif)", 0),
 ("EDGE", "Certification", r"\bEDGE\s*(expert|certif|AP)", I),
 ("BREEAM", "Certification", r"\bBREEAM\b", I),
 ("Passive House", "Certification", r"passive\s*house|passivhaus|\bCPHD\b", I),
 ("COA registration", "Certification", r"council of architecture|\bCOA\b", 0),
 ("Licensed or registered architect", "Certification", r"(licensed|registered)\s+architect|architectural licens|\bNCARB\b|path to licensure|\bARE\b\s*(exam|division)", I),
 ("RIBA or ARB", "Certification", r"\bRIBA\b|\bARB\b", 0),
 ("PMP", "Certification", r"\bPMP\b", 0),
 ("Revit", "Software", r"\brevit\b", I),
 ("AutoCAD", "Software", r"\bauto\s?cad\b", I),
 ("BIM", "Software", r"\bBIM\b|building information model", I),
 ("Rhino", "Software", r"\brhino(ceros)?\b(?!s)", I),
 ("Grasshopper", "Software", r"\bgrasshopper\b", I),
 ("SketchUp", "Software", r"\bsketch\s?up\b", I),
 ("ArchiCAD", "Software", r"\barchicad\b", I),
 ("Navisworks", "Software", r"\bnavisworks\b", I),
 ("Dynamo", "Software", r"\bdynamo\b", I),
 ("Enscape, Lumion or V-Ray", "Software", r"\benscape\b|\blumion\b|\bv-?ray\b|\btwinmotion\b", I),
 ("3ds Max", "Software", r"\b3ds\s?max\b", I),
 ("Adobe Creative Suite", "Software", r"\badobe\b|photoshop|indesign|illustrator\b", I),
 ("Bluebeam", "Software", r"\bbluebeam\b", I),
 ("Energy modelling", "Skill", r"energy model|energy simulation|\bIES\s?VE\b|energyplus|\beQUEST\b|designbuilder|\bASHRAE\s*90\.1", I),
 ("Daylight and climate analysis", "Skill", r"daylight(ing)?\s*(analys|simulat|model)|\bladybug\b|\bhoneybee\b|climate analys", I),
 ("CFD", "Skill", r"\bCFD\b|computational fluid", 0),
 ("Building codes", "Skill", r"building codes?|\bNBC\b|\bIBC\b|code compliance|\bECBC\b", I),
 ("Construction documents", "Skill", r"construction documents?|working drawings|\bGFC\b|construction drawings", I),
]
INTERN = re.compile(r"\bintern(s|ship|ships)?\b|\btrainee\b", I)
KIND_ORDER = ["Certification", "Software", "Skill"]
KIND_LABEL = {"Certification": "Certifications and registration", "Software": "Software", "Skill": "Skills"}

def _key(u):
    m = re.search(r"archinect\.com/jobs/entry/(\d+)", u)
    return "archinect:" + m.group(1) if m else u.split("?")[0].rstrip("/")

def _strip(s):
    s = re.sub(r"(?is)<(script|style|nav|footer|header)[^>]*>.*?</\1>", " ", s or "")
    return re.sub(r"\s+", " ", _h.unescape(re.sub(r"<[^>]+>", " ", s))).strip()

def _text(u):
    import requests
    f = os.path.join(CACHE, hashlib.sha1(u.encode()).hexdigest()[:16] + ".json")
    if os.path.exists(f):
        return json.load(open(f)).get("text", "")
    t = ""
    try:
        m = re.match(r"https://([^.]+)\.(wd\d+)\.myworkdayjobs\.com/(?:[a-z]{2}-[A-Z]{2}/)?([^/]+)/job/(.+)", u)
        if m:
            api = f"https://{m.group(1)}.{m.group(2)}.myworkdayjobs.com/wday/cxs/{m.group(1)}/{m.group(3)}/job/{m.group(4)}"
            r = requests.get(api, headers={**UA, "Accept": "application/json"}, timeout=25)
            if r.ok:
                t = _strip(r.json().get("jobPostingInfo", {}).get("jobDescription", ""))
        else:
            r = requests.get(u, headers=UA, timeout=25)
            if r.ok:
                try:
                    import trafilatura
                    t = trafilatura.extract(r.text) or ""
                except Exception:
                    t = ""
                if len(t) < 400:
                    t = _strip(r.text)
    except Exception:
        t = ""
    if t:
        os.makedirs(CACHE, exist_ok=True)
        json.dump({"url": u, "text": t[:30000]}, open(f, "w"))
    return t

def analyse(jobs):
    seen, todo = set(), []
    for j in jobs:
        if INTERN.search(j.get("title", "")):
            continue
        k = _key(j["url"])
        if k in seen:
            continue
        seen.add(k); todo.append(j)
    with ThreadPoolExecutor(8) as ex:
        texts = list(ex.map(lambda j: _text(j["url"]), todo))
    read = [(j, t) for j, t in zip(todo, texts) if len(t) > 300]
    hits = []
    for label, kind, pat, fl in VOCAB:
        rx = re.compile(pat, fl)
        js = [j for j, t in read if rx.search(j.get("title", "") + " " + t)]
        if js:
            hits.append({"label": label, "kind": kind, "jobs": js})
    return read, hits

def html_block(jobs, cfg):
    sb = cfg.get("skills_block") or {}
    read, hits = analyse(jobs)
    if len(read) < 4 or not hits:
        print(f"skills: skipped ({len(read)} postings readable)", flush=True)
        return ""
    esc = lambda s: _h.escape(str(s), quote=True)
    n = len(read)
    groups = []
    for kind in KIND_ORDER:
        hs = sorted([h for h in hits if h["kind"] == kind], key=lambda h: (-len(h["jobs"]), h["label"]))
        hs = [h for h in hs if len(h["jobs"]) >= 1][: sb.get("per_group", 6)]
        if not hs:
            continue
        rows = []
        for h in hs:
            pct = max(6, round(100 * len(h["jobs"]) / n))
            ex = h["jobs"][:3]
            links = ", ".join(f'<a href="{esc(j["url"])}" target="_blank" rel="noopener">{esc(j["title"])}, {esc(j["org"])}</a>' for j in ex)
            rows.append(f'<div class="sk-row"><div class="sk-top"><span class="sk-name">{esc(h["label"])}</span>'
                        f'<span class="sk-bar" aria-hidden="true"><i style="width:{pct}%"></i></span></div>'
                        f'<p class="sk-asks">Listed in {links}</p></div>')
        groups.append(f'<div class="sk-group"><h4>{KIND_LABEL[kind]}</h4>' + "".join(rows) + "</div>")
    title = sb.get("title", "Jobs vs Certifications")
    intro = sb.get("intro", "What today's postings list as prerequisites, read from the postings themselves. It changes when the jobs do.")
    note = sb.get("note", "Bars show how often a skill appears across today's postings. Every link goes to the original posting.")
    print(f"skills: {n} postings read, {len(hits)} skills found", flush=True)
    return (f'<section class="sec" id="skills"><div class="sec-head"><h2>{esc(title)}</h2><span>From today\'s postings</span></div>'
            f'<p class="jobs-intro">{esc(intro)}</p><div class="sk-grid">' + "".join(groups) + "</div>"
            f'<p class="sk-note">{esc(note)}</p></section>')

CSS = r"""
.sk-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:0 26px}
.sk-group h4{margin:0 0 8px;font-family:"Old Standard TT",Georgia,serif;font-size:12.5px;letter-spacing:.2em;text-transform:uppercase;
  text-align:center;color:var(--ink);border-top:1px solid var(--rule);border-bottom:1px solid var(--rule-soft);padding:3px 0 2px}
.sk-row{padding:0 0 8px;margin:0 0 8px;border-bottom:1px dotted var(--rule-soft)}
.sk-top{display:flex;align-items:center;gap:10px}
.sk-name{font-family:"Libre Caslon Text",Georgia,serif;font-weight:700;font-size:14px;color:var(--ink);flex:0 0 46%}
.sk-bar{flex:1;height:8px;border:1px solid var(--rule-soft);background:rgba(232,219,187,.45)}
.sk-bar i{display:block;height:100%;background:var(--ink-soft)}
.sk-asks{margin:4px 0 0;font-size:12.5px;line-height:1.4;color:var(--ink-soft)}
.sk-asks a{color:var(--link)}
.sk-note{font-family:"Old Standard TT",Georgia,serif;font-style:italic;font-size:12px;color:var(--ink-faint);text-align:center;margin:6px 0 14px}
@media (max-width:900px){.sk-grid{grid-template-columns:1fr}}
"""

if __name__ == "__main__":
    import sys
    J = json.load(open(sys.argv[1]))["jobs"]
    read, hits = analyse(J)
    print(len(read), "read of", len(J))
    for h in sorted(hits, key=lambda h: -len(h["jobs"])):
        print(h["kind"], h["label"], len(h["jobs"]), [j["org"] for j in h["jobs"][:3]])
