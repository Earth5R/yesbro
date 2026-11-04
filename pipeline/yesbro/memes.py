"""Yes Bro Meme of the day. In-house text memes (HTML and CSS, real text, no images, no meme templates).

Each paper gets one meme tied to a real story in that day's edition, linked to it, placed after the second news section.
Source order:
  1. memes/<key>_<YYYY-MM-DD>.json, written by the copy worker (hand or LLM captions):
     {"url": "<story url in today's edition>", "format": "nobody|expect|chart|classic", ...format fields}
       nobody : "lines": [["Nobody", ""], ["Absolutely nobody", ""], ["Speaker", "what they say"]], "after": "optional reaction line"
       expect : "expect": "...", "reality": "..."
       chart  : "title": "...", "bars": [["label", pct], ["label", pct]]
       classic: "top": "...", "bottom": "..."
  2. If that file is missing or fails validate(), a template meme on a safe story picked by pick_story().
  3. If no story is safe, a house meme about reading the paper (never an empty box, never a failed build).
Validator: banned characters, no-intern, Earth5R never an NGO, no FIELDWORK/Earth5R on Healing, no "not X but Y",
no tricolons, no counting our own things, and no politics, religion or conflict, no death, illness, disaster or victims.
"""
import datetime, hashlib, html, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
esc = lambda s: html.escape(s or "", quote=True)

# ---- Story filters (applied to headline + summary of the story the meme is about)
POLITICAL = re.compile(r"(?i)\b(politic\w*|election\w*|elector\w*|vot(e|es|er|ers|ing)|poll(s|ing)? (body|panel)|ballot|minist(er|ers|ry|ries)|cabinet|parliament\w*|lok sabha|rajya sabha|assembly|legislat\w*|congress|bjp|aap|tmc|dmk|shiv sena|\bparty\b|parties|govern(ment|ments|or|ors)|govt|union minister|chief minister|prime minister|president\w*|senat\w*|white house|kremlin|downing street|modi|kharge|gandhi|trump|biden|harris|putin|xi jinping|zelensky|netanyahu|sharif|opposition|protest\w*|rally|rallies|campaign trail|mp|mla|mps|mlas|sir|ec|bill|ordinance|sanction\w*|tariff\w*|diplomat\w*|embassy|treaty|war|wars|warfare|woke|democrat\w*|republican\w*|midterm\w*|tory|tories|labour party|lawmaker\w*|deputies|mayor\w*|royal\w*|prince|princess|king|queen|monarch\w*|epstein|gaza|israel\w*|palestin\w*|hamas|hezbollah|ukrain\w*|russia\w*|pakistan\w*|china|chinese|taiwan|iran\w*|kashmir|manipur|border|militar\w*|army|armed forces|missile\w*|terror\w*|insurgen\w*|religio\w*|hindu\w*|muslim\w*|islam\w*|christian\w*|sikh\w*|church|temple|mosque|caste|communal|puja|diwali|eid|god|faith|riot\w*|fascis\w*|viksit bharat|union budget)\b")
SENSITIVE = re.compile(r"(?i)\b(death|deaths|dead|die|dies|died|dying|kill\w*|murder\w*|suicid\w*|self.harm|cancer\w*|tumou?r\w*|dementia|alzheimer\w*|stroke|disease\w*|patient\w*|infect\w*|outbreak\w*|virus\w*|pandemic|disorder\w*|depress\w*|anxi\w*|autis\w*|adhd|diabet\w*|syndrome|ill|illness\w*|sick\w*|injur\w*|hospital\w*|icu|accident\w*|crash\w*|collision\w*|fire|fires|wildfire\w*|burn\w*|flood\w*|cyclone\w*|earthquake\w*|disaster\w*|tragedy|tragic|victim\w*|casualt\w*|abuse\w*|assault\w*|rape\w*|harass\w*|fraud\w*|scam\w*|arrest\w*|jail\w*|prison\w*|court\w*|lawsuit\w*|sued|layoff\w*|laid off|job cuts|jobs go|closure|shut|shuts|bankrupt\w*|graveyard|grief|mourn\w*|funeral|hostage\w*|shoot\w*|gun\w*|weapon\w*|invasion|refugee\w*|poverty|hunger|famine|child|children|minor|missing|emergency|stigma|addict\w*|substance\w*|drug|drugs|alcohol\w*|overdose|eating disorder|weight loss|obes\w*|cure\w*)\b")
COMMUNITY = re.compile(r"(?i)\b(tribe|tribes|tribal|indigenous|adivasi\w*|ethnic\w*|dalit\w*|caste|race|racial|of colou?r|community|communities|minorit\w*|chenchus?|savaras?|migrant\w*|immigrant\w*)\b")
SKIP_SECTIONS = re.compile(r"(?i)politic|policy|regulation|safety|public health|mental health|alternative therap|government")

# ---- Copy validator for our own meme text (the quoted headline is news copy and is checked by the story filters instead)
BANNED_CH = ("\u2014", "\u2013", ";")
COUNT_WORDS = r"(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|twenty|thirty|dozens?|hundreds?)"
COUNT_RE = re.compile(r"\b" + COUNT_WORDS + r"\s+(?:[a-z]+\s+)?(?:papers?|editions?|sections?|stories|story|jobs?|listings?|openings?|roles?|events?|items?|columns?|memes?)\b", re.I)
NOT_BUT = re.compile(r"(?i)\bnot\b[^.!?]{1,60}\bbut\b|\bisn't\b[^.!?]{1,60}\bit's\b")
TRICOLON = re.compile(r"(?i)\b[\w'-]+(?: [\w'-]+){0,3}, [\w'-]+(?: [\w'-]+){0,3},? (?:and|or) [\w'-]+")
MEAN = re.compile(r"(?i)\b(stupid|idiot\w*|dumb|loser\w*|ugly|crazy|insane|psycho|retard\w*|lame|pathetic|cringe|fat)\b")

def validate(texts, key=""):
    """Return a list of problems in our own meme copy. Empty list means it can ship."""
    probs = []
    for t in texts:
        t = t or ""
        for ch in BANNED_CH:
            if ch in t: probs.append(f"banned character {ch!r} in {t!r}")
        if re.search(r"(?i)\bintern(ship)?s?\b", t): probs.append(f"intern word in {t!r}")
        if re.search(r"(?i)earth5r", t) and re.search(r"(?i)\bngo\b|non.?profit|charity", t): probs.append(f"Earth5R called an NGO in {t!r}")
        if key == "healing" and re.search(r"(?i)fieldwork|earth5r", t): probs.append(f"FIELDWORK/Earth5R on Healing in {t!r}")
        if NOT_BUT.search(t): probs.append(f"'not X but Y' in {t!r}")
        if TRICOLON.search(t): probs.append(f"tricolon in {t!r}")
        if COUNT_RE.search(t): probs.append(f"counting in {t!r}")
        if POLITICAL.search(t): probs.append(f"political word in {t!r}")
        if SENSITIVE.search(t): probs.append(f"sensitive word in {t!r}")
        if MEAN.search(t): probs.append(f"unkind word in {t!r}")
        if len(t) > 160: probs.append(f"too long ({len(t)}) {t[:40]!r}")
    return probs

def story_ok(s, key=""):
    import blocklist
    if blocklist.blocked(s): return False  # Begin Group blocklist
    txt = f'{s.get("headline", "")} {s.get("summary", "")}'
    if POLITICAL.search(txt) or SENSITIVE.search(txt) or COMMUNITY.search(txt): return False
    if SKIP_SECTIONS.search(s.get("section", "")): return False
    if key == "healing" and re.search(r"(?i)fieldwork|earth5r|therap|supplement|remed", txt): return False
    h = s.get("headline", "")
    return 20 <= len(h) <= 95 and not any(ch in h for ch in BANNED_CH)

def pick_story(stories, key, date_iso):
    ok = [s for s in stories if story_ok(s, key)]
    if not ok: return None
    # Prefer the stronger stories (top of each section), rotate by date so it does not always pick the same slot.
    pos, top = {}, []
    for s in stories:
        pos[s["section"]] = pos.get(s["section"], 0) + 1
        if s in ok and pos[s["section"]] <= 4: top.append(s)
    pool = top or ok
    h = int(hashlib.md5(f"{key}{date_iso}".encode()).hexdigest(), 16)
    return pool[h % len(pool)]

# ---- Template captions per paper (deadpan, kind, nothing about the people in the story)
PERSONA = {
    "daily": "Me, holding a cup of chai", "business": "Me, an hour before the market opens", "ux": "Me, a designer with views on corner radius",
    "arch": "Me, an architect with views on facades", "schools": "Me, a student with a mock exam on Thursday",
    "sustainability": "Me, saying ESG out loud at work", "startups": "Me, a founder refreshing the runway sheet",
    "highered": "Me, on yet another draft of my personal essay", "consulting": "Me, opening a blank slide called Key Takeaways",
    "health": "Me, between rounds with a cold coffee", "marketing": "Me, still defending the new logo",
    "finance": "Me, checking my savings again", "aviation": "Me, a cadet who knows the checklist by heart",
    "healing": "Me, taking a slow breath with my tea",
    "ai": "Me, waiting for my GPU quota to reset",
    "packaging": "Me, a packaging buyer refreshing the resin price sheet",
    "realestate": "Me, refreshing Magicbricks while the broker says possession is next quarter",
    "auto": "Me, refreshing the waiting period while the dealer says next month",
}
REACT = ["Clears the afternoon to think about it properly.", "Forwards it to the family group with no further comment.",
         "Reads it again, slower, for the gravity it deserves.", "Adds it to the list of things I will bring up at dinner.",
         "Treats it as a personal development.", "Puts the kettle on. This calls for a second cup.",
         "Updates the group chat with the solemnity of a lighthouse keeper.", "Saves it for later, which means forever.",
         "Underlines it in a pen reserved for important things.", "Sits with it quietly until the tea goes cold."]
REACT_HEAL = ["Nods slowly and drinks some water.", "Decides to think about it after a short walk.", "Puts the kettle on and lets it sink in gently."]

FORMATS = ["nobody", "expect", "chart", "classic"]
KEYS = ["daily", "business", "ux", "arch", "schools", "sustainability", "startups", "highered", "consulting", "health",
        "marketing", "finance", "aviation", "healing", "ai", "packaging", "fashion", "realestate", "auto"]

def _short(h, n=70):
    return h if len(h) <= n else h[:n].rsplit(" ", 1)[0] + "..."

def template(story, key, date_iso):
    h = int(hashlib.md5(f"t{key}{date_iso}".encode()).hexdigest(), 16)
    who = PERSONA.get(key, "Me, with the morning paper")
    react = (REACT_HEAL if key == "healing" else REACT)[h % (3 if key == "healing" else len(REACT))]
    day = datetime.date.fromisoformat(date_iso).strftime("%A")
    q = f"\u201c{_short(story['headline'])}\u201d"
    # Rotate formats so neighbouring papers differ on the same day and each paper changes format day to day.
    fmt = FORMATS[(datetime.date.fromisoformat(date_iso).toordinal() + (KEYS.index(key) if key in KEYS else h)) % len(FORMATS)]
    if fmt == "nobody":
        return {"format": "nobody", "lines": [["Nobody", ""], ["Absolutely nobody", ""], [who, f"reads {q}"]], "after": react}
    if fmt == "expect":
        return {"format": "expect", "expect": f"A quiet {day} morning.", "reality": f"{q} {react}"}
    if fmt == "chart":
        return {"format": "chart", "title": f"How my {day} morning went", "bars": [[f"Reading {q}", 71], ["Reading it again, slower", 29]]}
    return {"format": "classic", "top": f"{who.split(',')[0]} seeing {q}", "bottom": react}

def house_meme(key, date_iso):
    day = datetime.date.fromisoformat(date_iso).strftime("%A")
    return {"format": "nobody", "lines": [["Nobody", ""], ["Absolutely nobody", ""], [PERSONA.get(key, "Me"), "opens the paper before the messages"]],
            "after": f"A calm {day}, by any standard."}

def _own_texts(m):
    """Our own words in a meme, with any quoted headline taken out (headlines are news copy)."""
    raw = []
    if m["format"] == "nobody": raw = [x for pair in m["lines"] for x in pair] + [m.get("after", "")]
    elif m["format"] == "expect": raw = [m["expect"], m["reality"]]
    elif m["format"] == "chart": raw = [m["title"]] + [b[0] for b in m["bars"]]
    elif m["format"] == "classic": raw = [m["top"], m["bottom"]]
    return [re.sub(r"\u201c[^\u201d]*\u201d", "", t or "") for t in raw]

def make(stories, key, date_iso, log=print):
    """Return (meme dict, story or None, source label). Never raises."""
    try:
        f = os.path.join(HERE, "memes", f"{key}_{date_iso}.json")
        if os.path.exists(f):
            m = json.load(open(f))
            st = next((s for s in stories if s["url"] == m.get("url")), None)
            probs = [] if st else ["story url is not in today's edition"]
            if st and not story_ok(st, key): probs.append("story fails the politics or sensitivity filter")
            if m.get("format") not in ("nobody", "expect", "chart", "classic"): probs.append("unknown format")
            else: probs += validate(_own_texts(m), key)
            import blocklist
            if blocklist.blocked(m): probs.append("BLOCKED: Begin or fair")
            if not probs: return m, st, "file"
            log(f"meme: {f} rejected, using template: {probs}")
        st = pick_story(stories, key, date_iso)
        if st:
            m = template(st, key, date_iso)
            if not validate(_own_texts(m), key): return m, st, "template"
        return house_meme(key, date_iso), None, "house"
    except Exception as e:  # a meme must never stop the paper
        log(f"meme: fallback after error {e}")
        return house_meme(key, date_iso), None, "house"

# ---- Rendering
def _body(m):
    f = m["format"]
    if f == "nobody":
        rows = "".join(f'<p class="mm-line"><b>{esc(a)}:</b> {esc(b)}</p>' for a, b in m["lines"])
        return f'<div class="mm-panel mm-nobody">{rows}' + (f'<p class="mm-after">{esc(m["after"])}</p>' if m.get("after") else "") + "</div>"
    if f == "expect":
        return (f'<div class="mm-panel mm-two"><div class="mm-half"><p class="mm-tag">Expectation</p><p>{esc(m["expect"])}</p></div>'
                f'<div class="mm-half mm-dark"><p class="mm-tag">Reality</p><p>{esc(m["reality"])}</p></div></div>')
    if f == "chart":
        bars = "".join(f'<div class="mm-bar"><span class="mm-bl">{esc(l)}</span><span class="mm-track"><i style="width:{max(4, min(100, int(p)))}%"></i></span>'
                       f'<span class="mm-pct">{int(p)}%</span></div>' for l, p in m["bars"])
        return f'<div class="mm-panel mm-chart"><p class="mm-ct">{esc(m["title"])}</p>{bars}</div>'
    return f'<div class="mm-panel mm-dark mm-classic"><p class="mm-top">{esc(m["top"])}</p><p class="mm-bot">{esc(m["bottom"])}</p></div>'

def html_box(m, st, small=False, paper_link=None):
    via = (f'<p class="mm-via">From today\u2019s paper: <a href="{esc(st["url"])}" target="_blank" rel="noopener">{esc(st["headline"])}</a></p>' if st
           else "")
    if paper_link: via += f'<p class="mm-via"><a href="{esc(paper_link[0])}">{esc(paper_link[1])}</a></p>'
    return (f'<aside class="meme{" meme-sm" if small else ""}" id="meme" aria-label="Meme of the day"><p class="mm-kicker">Meme of the day</p>'
            + _body(m) + via + "</aside>")

CSS = r"""
.meme{max-width:620px;margin:8px auto 30px;border:3px double var(--rule);padding:12px 16px 12px;background:rgba(232,219,187,.55);scroll-margin-top:70px}
.meme .mm-kicker{margin:0 0 8px;text-align:center;font-family:"Old Standard TT",Georgia,serif;font-size:11px;letter-spacing:.24em;text-transform:uppercase;color:var(--ink-faint)}
.meme .mm-panel{border:1px solid var(--rule);background:#f6eedb;padding:14px 16px;font-family:"Libre Caslon Text",Georgia,serif;color:var(--ink)}
.meme .mm-dark{background-color:#2e2a24;color:#f3ead6;background-image:radial-gradient(rgba(243,234,214,.09) 1px,transparent 1.2px);background-size:5px 5px}
.meme .mm-line{margin:0 0 8px;font-size:17px;line-height:1.35}
.meme .mm-line b{font-family:"Playfair Display",Georgia,serif;font-weight:900}
.meme .mm-after{margin:10px 0 0;padding-top:8px;border-top:1px dotted var(--rule-soft);font-style:italic;font-size:15.5px;color:var(--ink-soft)}
.meme .mm-two{display:grid;grid-template-columns:1fr 1fr;padding:0}
.meme .mm-half{padding:12px 14px}.meme .mm-half p{margin:0;font-size:16px;line-height:1.35}
.meme .mm-tag{font-family:"Playfair Display",Georgia,serif;font-weight:900;text-transform:uppercase;letter-spacing:.06em;font-size:14px!important;margin:0 0 6px!important}
.meme .mm-ct{margin:0 0 10px;font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:18px;text-align:center}
.meme .mm-bar{display:grid;grid-template-columns:1fr auto;gap:2px 8px;margin:0 0 10px;font-size:14.5px;line-height:1.3}
.meme .mm-bl{grid-column:1/3}.meme .mm-track{height:14px;border:1px solid var(--rule);background:#efe4c8}
.meme .mm-track i{display:block;height:100%;background:repeating-linear-gradient(45deg,#2e2a24 0 3px,#4a4238 3px 6px)}
.meme .mm-pct{font-family:"Old Standard TT",Georgia,serif;font-weight:700;font-size:13px}
.meme .mm-classic{text-align:center;padding:18px 14px}
.meme .mm-top,.meme .mm-bot{margin:0;font-family:"Playfair Display",Georgia,serif;font-weight:900;text-transform:uppercase;letter-spacing:.03em;font-size:20px;line-height:1.2}
.meme .mm-bot{margin-top:46px}
.meme .mm-via{margin:10px 0 0;font-size:13.5px;line-height:1.4;color:var(--ink-soft);text-align:center;font-style:italic}
.meme .mm-via a{color:var(--link)}
.meme-sm{max-width:520px}.meme-sm .mm-line{font-size:15.5px}
@media (max-width:640px){.meme{margin:6px 0 26px;padding:10px 10px}.meme .mm-two{grid-template-columns:1fr}.meme .mm-line{font-size:16px}.meme .mm-top,.meme .mm-bot{font-size:18px}}
"""
