#!/usr/bin/env python3
"""Build the Yes Bro landing page (the front door) at the site root.

Usage:
    python3 build_landing.py [--site /workspace/yesbro-site] [--stories-dir /workspace/yesbro]

Writes <site>/index.html and <site>/manifest.json. It never touches CNAME, daily/ or any edition folder.
Each card reads its edition's newest stories JSON (stories_DATE.json for Daily, stories_<key>_DATE.json for the
editions) for the top headline. A missing file just leaves the card without a headline.
To add a new paper, add one line to EDITIONS (and optionally a config JSON for its price and motto).
"""
import argparse, glob, html, json, os, re, datetime
from build_html import A2HS_CSS, a2hs_html, house_count_check
import share, maker
import yb_auth_strip
# Landing page share: the front door URL, so friends land on all the papers (share.py).
SHARE_URL, SHARE_TITLE = "https://yesbrohq.com/", "Yes Bro"
SHARE_TEXT = share.text_for("landing", SHARE_TITLE)

# key, card name, path on the site, stories file prefix, config JSON (or None), one line about who it is for,
# card photo (site relative, grayscale 16:9 webp about 800x450 under 80KB, or "" for none)
EDITIONS = [
    ("daily", "Yes Bro Daily", "daily/", "stories_", None, "India and the world, from politics to climate. Neither waits for you to finish your tea", "img/landing/daily.webp"),
    ("finance", "Yes Bro Finance", "finance/", "stories_finance_", "editions/config/finance.json", "For bankers and anyone keeping an eye on their own savings. Not investment advice", "img/landing/finance.webp"),
    ("business", "Yes Bro Business", "business/", "stories_business_", "editions/config/business.json", "For people who read the business pages before the sports pages", "img/landing/business.webp"),
    ("ai", "Yes Bro AI", "ai/", "stories_ai_", "editions/config/ai.json", "For anyone keeping up with artificial intelligence, minus the launch livestream", "img/landing/ai.webp"),
    ("health", "Yes Bro Health", "health/", "stories_health_", "editions/config/health.json", "For doctors and health people with a minute between rounds, which is about how long they have", "img/landing/health.webp"),
    ("startups", "Yes Bro Startups", "startups/", "stories_startups_", "editions/config/startups.json", "For founders and the investors who reply eventually. Runway sold separately", "img/landing/startups.webp"),
    ("realestate", "Yes Bro Real Estate", "realestate/", "stories_realestate_", "editions/config/realestate.json", "For developers, brokers and anyone who has argued about carpet area", "img/landing/realestate.webp"),
    ("auto", "Yes Bro Auto", "auto/", "stories_auto_", "editions/config/auto.json", "For anyone who still negotiates the on-road price", "img/landing/auto.webp"),
    ("fashion", "Yes Bro Fashion", "fashion/", "stories_fashion_", "editions/config/fashion.json", "For anyone who follows fashion, jewellery and accessories, India first", "img/landing/fashion.webp"),
    ("highered", "Yes Bro Higher Ed", "highered/", "stories_highered_", "editions/config/highered.json", "For applicants and admissions teams. The essay is still your problem", "img/landing/highered.webp"),
    ("schools", "Yes Bro Schools", "schools/", "stories_schools_", "editions/config/schools.json", "For IB and Cambridge students and their teachers. Admissions dates included, panic optional", "img/landing/schools.webp"),
    ("marketing", "Yes Bro Marketing", "marketing/", "stories_marketing_", "editions/config/marketing.json", "For marketers with strong opinions about the new logo", "img/landing/marketing.webp"),
    ("ux", "Yes Bro UX & Design", "ux/", "stories_ux_", "editions/config/ux.json", "For UX, product and design people who still care about the craft", "img/landing/ux.webp"),
    ("arch", "Yes Bro Architecture", "architecture/", "stories_arch_", "editions/config/arch.json", "For architects and anyone who has argued about a facade", "img/landing/arch.webp"),
    ("sustainability", "Yes Bro Sustainability", "sustainability/", "stories_sustainability_", "editions/config/sustainability.json", "For people who say ESG out loud at work", "img/landing/sustainability.webp"),
    ("consulting", "Yes Bro Consulting", "consulting/", "stories_consulting_", "editions/config/consulting.json", "For consultants who will skim this before the call anyway", "img/landing/consulting.webp"),
    ("aviation", "Yes Bro Aviation", "aviation/", "stories_aviation_", "editions/config/aviation.json", "For pilots and cadets in training. Cadet intakes are listed near the back", "img/landing/aviation.webp"),
    ("packaging", "Yes Bro Packaging", "packaging/", "stories_packaging_", "editions/config/packaging.json", "For anyone who makes, buys or recycles packaging, plastic first", "img/landing/packaging.webp"),
    ("healing", "Yes Bro Healing", "healing/", "stories_healing_", "editions/config/healing.json", "For anyone trying to feel better, with the evidence kept in the room", "img/landing/healing.webp"),
]
DAILY_DEFAULTS = {"price": "Price: Free, unlike your opinions", "motto": "All the news worth your morning chai"}
FIELD_MAIL = ("mailto:ontheworldroad@gmail.com?subject=" + "Yes%20Bro%20for%20my%20field"
              + "&body=" + "Hi%20Yes%20Bro%2C%0A%0AMy%20field%20is%3A%20%0AI%20would%20want%20sections%20on%3A%20%0A")

# Width of 'Yes Bro <Field>' in em at equal size (UnifrakturMaguntia 'Yes Bro ' = 3.89em, Playfair 900 field word), measured in Chrome.
BRAND_W = {'Daily': 2.52, 'UX & Design': 5.85, 'Architecture': 5.91, 'Schools': 3.68, 'Sustainability': 6.54, 'Startups': 4.03, 'Higher Ed': 4.8, 'Consulting': 5.21, 'Health': 3.14, 'Marketing': 4.9, 'Finance': 3.72, 'Aviation': 3.95, 'Business': 4.12, 'Healing': 3.55, 'AI': 1.09, 'Newspaper': 5.18, 'Packaging': 4.93, 'Fashion': 3.80, 'Real Estate': 5.50, 'Auto': 2.20}
def brand(name):
    """'Yes Bro' in blackletter, the field word in bold Playfair at the SAME size (cap heights match at 1em).
    The whole title scales down together via --w when the line is too narrow."""
    if name.startswith("Yes Bro "):
        f = name[8:]
        w = round((3.99 + BRAND_W.get(f, 0.56 * len(f))) * 1.03, 2)
        return (f'<span class="ybt" style="--w:{w}"><span class="yb">Yes Bro</span> '
                f'<span class="fw">{esc(f)}</span></span>')
    return esc(name)

def esc(s): return html.escape(s or "", quote=True)

def newest(prefix, d):
    pat = re.compile(re.escape(prefix) + r"(\d{4}-\d{2}-\d{2})\.json$")
    best = None
    for f in glob.glob(os.path.join(d, prefix + "*.json")):
        m = pat.search(os.path.basename(f))
        if m and (best is None or m.group(1) > best[0]):
            best = (m.group(1), f)
    return best

def card(e, d, site):
    key, name, path, prefix, cfgp, blurb = e[:6]
    img = e[6] if len(e) > 6 else ""
    if img and not os.path.exists(os.path.join(site, img)):
        print(f"warning: card photo {img} not found in site, card shown without photo")
        img = ""
    photo = (f'<figure class="c-photo"><img src="{esc(img)}" alt="{esc(name)}" width="800" height="450" loading="lazy" decoding="async"></figure>'
             if img else "")
    cfg = dict(DAILY_DEFAULTS)
    if cfgp and os.path.exists(os.path.join(d, cfgp)):
        try: cfg.update(json.load(open(os.path.join(d, cfgp))))
        except Exception: pass
    top, date, n = "", "", 0
    nb = newest(prefix, d)
    if nb:
        try:
            st = json.load(open(nb[1]))
            import blocklist
            st = blocklist.keep(st, "stories") if isinstance(st, list) else st  # Begin Group blocklist
            if isinstance(st, list) and st:
                top, n = st[0].get("headline", ""), len(st)
                date = datetime.date.fromisoformat(nb[0]).strftime("%-d %b %Y")
        except Exception: pass
    jobs = cfgp is not None and bool(glob.glob(os.path.join(d, f"jobs_{key}_*.json")))
    head = (f'<p class="c-top"><span class="c-kick">Top story{", " + esc(date) if date else ""}</span>{esc(top)}</p>' if top else "")
    meta = []
    if jobs: meta.append("Jobs inside")
    if glob.glob(os.path.join(d, f"events_{key}_*.json")): meta.append("Events")
    return (f'<a class="card" href="{esc(path)}" data-key="{esc(key)}" data-name="{esc(name)}">'
            f'{photo}<span class="c-mine">Your paper</span>'
            f'<h2>{brand(name)}</h2><p class="c-motto">{esc(cfg.get("motto", ""))}</p>'
            f'<p class="c-blurb">{esc(blurb)}</p>{head}'
            f'<p class="c-foot"><span>{esc(cfg.get("price", ""))}</span>{"<span>" + " | ".join(meta) + "</span>" if meta else ""}</p>'
            f'<span class="c-go">Read today\'s paper &rarr;</span></a>'), (nb[0] if nb else "")

CSS = r"""
:root{--paper:#f1e7cf;--paper-deep:#e8dbbb;--ink:#2e2a24;--ink-soft:#4a4238;--ink-faint:#6f6454;--rule:#3d362d;--rule-soft:#a8987a;--link:#5b3a1e}
*{box-sizing:border-box}
html{background:#d9cba8}
body{margin:0;color:var(--ink);font-family:"Libre Caslon Text","Old Standard TT",Georgia,"Times New Roman",serif;font-size:16px;line-height:1.5;
  -webkit-font-smoothing:antialiased}
.sheet{max-width:1100px;margin:0 auto;padding:18px 18px 34px;background-color:var(--paper);
  background-image:radial-gradient(ellipse at 20% 0%,rgba(255,250,235,.55),transparent 60%),radial-gradient(ellipse at 100% 100%,rgba(190,165,115,.28),transparent 55%),
  url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='180' height='180'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='3' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 .35  0 0 0 0 .28  0 0 0 0 .18  0 0 0 .09 0'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>");
  box-shadow:0 0 0 1px rgba(80,60,30,.15),0 8px 40px rgba(70,50,20,.25);min-height:100vh}
a{color:inherit}
.masthead{text-align:center;border-top:4px double var(--rule);border-bottom:1px solid var(--rule);margin-top:6px;padding:4px 0 2px}
.masthead h1{margin:0;font-family:"UnifrakturMaguntia","Old English Text MT","Playfair Display",serif;font-weight:400;font-size:clamp(64px,17vw,136px);line-height:1.02;color:var(--ink)}
.motto{font-family:"Old Standard TT",Georgia,serif;font-style:italic;font-size:14px;color:var(--ink-soft);margin:0 0 6px}
.dateline{display:flex;justify-content:space-between;gap:6px 12px;flex-wrap:wrap;border-bottom:4px double var(--rule);padding:5px 2px;
  font-family:"Old Standard TT",Georgia,serif;font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--ink-soft)}
.dateline b{color:var(--ink)}
.tagline{text-align:center;font-family:"Playfair Display",Georgia,serif;font-weight:700;font-size:clamp(20px,5.2vw,28px);line-height:1.25;margin:18px 6px 4px;color:var(--ink)}
.subtag{text-align:center;font-style:italic;color:var(--ink-soft);font-size:14.5px;margin:0 8px 18px}
.mypaper-door{display:flex;justify-content:center;margin:8px 0 18px}.mypaper-door a{display:inline-flex;align-items:center;gap:8px;min-height:44px;padding:0 18px;border:2px solid var(--rule,#3d362d);border-radius:999px;background:#2e2a24;color:#f3ead6;text-decoration:none;font-family:"Old Standard TT",Georgia,serif;font-weight:700;font-size:13px;letter-spacing:.14em;text-transform:uppercase}.mypaper-door a:hover{background:#4a4238}.mypaper-door a span{font-weight:400;font-style:italic;letter-spacing:.02em;text-transform:none;font-size:12.5px;opacity:.85}
.pick-head{font-family:"Old Standard TT",Georgia,serif;font-size:12px;letter-spacing:.22em;text-transform:uppercase;text-align:center;color:var(--ink);
  border-top:3px solid var(--rule);border-bottom:1px solid var(--rule);padding:4px 0 3px;margin:0 0 14px}
.cards{display:grid;grid-template-columns:1fr;gap:14px}
@media (min-width:700px){.cards{grid-template-columns:1fr 1fr;gap:18px}.sheet{padding:22px 30px 40px}}
@media (min-width:1100px){.cards{grid-template-columns:1fr 1fr 1fr}}
@media (max-width:699px){.cards .c-photo img{aspect-ratio:21/9}.cards .card h2{font-size:clamp(28px,8vw,36px)}.cards .c-top{font-size:16.5px}}
.card{position:relative;display:block;text-decoration:none;border:1px solid var(--rule);outline:1px solid var(--rule-soft);outline-offset:3px;
  padding:14px 16px 14px;background:rgba(255,250,235,.35);color:var(--ink);transition:background .15s}
.card:hover,.card:focus-visible{background:rgba(90,70,40,.08)}
.c-photo{margin:-14px -16px 12px;border-bottom:1px solid var(--rule);background:var(--paper-deep);overflow:hidden}
.c-photo img{display:block;width:100%;height:auto;aspect-ratio:16/9;object-fit:cover;filter:grayscale(1) contrast(1.06);opacity:.95}
.card:hover .c-photo img{opacity:1}
.card{container-type:inline-size}.ybt{font-size:min(1em,calc((100cqw - 34px)/var(--w)))}.yb,.fw{display:inline-block}.fw{font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:1em;letter-spacing:0;margin-left:.1em;vertical-align:baseline}
.card h2{margin:0;font-family:"UnifrakturMaguntia","Old English Text MT",serif;font-weight:400;font-size:clamp(32px,9vw,42px);line-height:1.05}
.c-motto{margin:2px 0 6px;font-family:"Old Standard TT",Georgia,serif;font-style:italic;font-size:13.5px;color:var(--ink-soft)}
.c-blurb{margin:0 0 8px;font-size:15px;color:var(--ink-soft)}
.c-top{margin:0 0 10px;padding:8px 0 0;border-top:1px dotted var(--rule-soft);font-family:"Playfair Display",Georgia,serif;font-weight:700;font-size:17.5px;line-height:1.28}
.c-kick{display:block;font-family:"Old Standard TT",Georgia,serif;font-weight:400;font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:var(--ink-faint);margin-bottom:2px}
.c-foot{display:flex;flex-wrap:wrap;justify-content:space-between;gap:4px 12px;margin:0 0 10px;font-family:"Old Standard TT",Georgia,serif;font-size:12px;
  letter-spacing:.06em;text-transform:uppercase;color:var(--ink-faint);border-top:1px solid var(--rule-soft);padding-top:6px}
.c-go{display:inline-block;font-family:"Old Standard TT",Georgia,serif;font-weight:700;font-size:13px;letter-spacing:.14em;text-transform:uppercase;
  border:1px solid var(--rule);padding:7px 14px;color:var(--ink)}
.c-mine{display:none;position:absolute;top:10px;right:10px;z-index:2;font-family:"Old Standard TT",Georgia,serif;font-size:10.5px;letter-spacing:.16em;text-transform:uppercase;
  border:1px solid var(--rule);padding:1px 6px;background:var(--paper-deep)}
.card.mine .c-mine{display:inline-block}
.card.mine{border-width:2px}
.housead{margin:26px auto 8px;max-width:720px;border:3px double var(--rule);padding:14px 18px 16px;text-align:center;background:rgba(232,219,187,.55);
  outline:1px solid var(--rule-soft);outline-offset:4px}
.housead .ad-kicker{font-family:"Old Standard TT",Georgia,serif;font-size:11px;letter-spacing:.24em;text-transform:uppercase;color:var(--ink-faint);margin:0 0 4px}
.housead .ad-brand{font-family:"Playfair Display",Georgia,serif;font-weight:900;letter-spacing:.01em;font-size:40px;line-height:1.05;margin:0 0 4px}
.housead h3{margin:0 0 6px;font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:22px;line-height:1.2}
.housead p{margin:0 0 10px;font-size:15px;line-height:1.45;color:var(--ink-soft)}
.btn{display:inline-block;font-family:"Old Standard TT",Georgia,serif;font-weight:700;font-size:13px;letter-spacing:.14em;text-transform:uppercase;
  color:var(--ink);text-decoration:none;border:1px solid var(--rule);padding:7px 16px;background:transparent;cursor:pointer}
.btn:hover{background:rgba(90,70,40,.1)}
.yourfield{margin:26px 0 6px;text-align:center;border-top:1px solid var(--rule);padding-top:16px}
.yourfield h3{margin:0 0 4px;font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:22px}
.yourfield p{margin:0 0 12px;color:var(--ink-soft);font-size:15px}
.yourfield .btn{border-width:2px;font-size:14px;padding:10px 18px}
footer .credit{margin:6px 0 0;font-style:normal;letter-spacing:.04em}footer .credit a{color:inherit}
footer{margin-top:24px;border-top:4px double var(--rule);padding-top:8px;text-align:center;font-family:"Old Standard TT",Georgia,serif;font-style:italic;font-size:13px;color:var(--ink-faint)}
.cbar{display:none;position:sticky;top:0;z-index:20;background:var(--rule);color:var(--paper);font-family:"Old Standard TT",Georgia,serif;
  padding:6px 10px;align-items:center;justify-content:space-between;gap:2px 10px;flex-wrap:wrap;box-shadow:0 2px 10px rgba(40,30,15,.3)}
.cbar.on{display:flex}
.cbar a.cgo{color:var(--paper);font-weight:700;font-size:15px;letter-spacing:.04em;text-decoration:none;border:1px solid var(--paper-deep);padding:6px 10px;flex:1 1 220px;text-align:center}
.cmore{display:flex;gap:12px;flex:0 1 auto;margin-left:auto}
.cbar button{background:none;border:0;color:var(--paper-deep);font-family:inherit;font-style:italic;font-size:12.5px;text-decoration:underline;cursor:pointer;padding:3px 0}
"""

JS = r"""<script>(function(){
var K='yesbro.pick',bar=document.getElementById('cbar'),go=document.getElementById('cgo'),cards=document.querySelectorAll('.card');
function get(){try{return localStorage.getItem(K)}catch(e){return null}}
function set(v){try{v?localStorage.setItem(K,v):localStorage.removeItem(K)}catch(e){}}
for(var i=0;i<cards.length;i++){cards[i].addEventListener('click',function(){set(this.getAttribute('data-key'))})}
var p=get(),c=p?document.querySelector('.card[data-key="'+p+'"]'):null;
if(c){c.classList.add('mine');go.href=c.getAttribute('href');go.textContent='Continue to '+c.getAttribute('data-name')+' \u2192';bar.classList.add('on');
  go.addEventListener('click',function(){set(p)})}
document.getElementById('call').addEventListener('click',function(){bar.classList.remove('on');var t=document.getElementById('papers');if(t)t.scrollIntoView({behavior:'smooth',block:'start'})});
document.getElementById('cforget').addEventListener('click',function(){set(null);bar.classList.remove('on');if(c)c.classList.remove('mine')});
})();</script>"""

AD = ('<aside class="housead" id="fieldwork"><p class="ad-kicker">Advertisement</p><p class="ad-brand">Fieldwork</p>'
      '<h3>Your neighbourhood is the syllabus.</h3>'
      '<p>FIELDWORK by Earth5R takes school and university students out of the classroom and into their own neighbourhoods to study '
      'real problems alongside the community. A mentor guides each step and the work is verified. Whatever you do, '
      'there is a street to start on.</p>'
      '<a class="btn" href="https://earth5r.org/fieldwork/" target="_blank" rel="noopener">Learn more at earth5r.org</a></aside>')

DESC = ("Build your own newspaper. Read every day what you want. Free daily papers for your field: India and world news, business, finance, AI, health, startups, UX and design, "
        "architecture, schools, sustainability, higher ed, consulting, marketing, aviation, healing, packaging, fashion, real estate and auto, with jobs and explainers. No tracking.")

def ld(day):
    org = {"@type": "Organization", "@id": "https://yesbrohq.com/#org", "name": "Yes Bro", "url": "https://yesbrohq.com/",
           "logo": {"@type": "ImageObject", "url": "https://yesbrohq.com/icon-512.png"},
           "parentOrganization": {"@type": "Organization", "name": "Earth5R", "url": "https://earth5r.org/"}}
    site = {"@type": "WebSite", "@id": "https://yesbrohq.com/#site", "name": "Yes Bro", "url": "https://yesbrohq.com/",
            "description": DESC, "inLanguage": "en-IN", "publisher": {"@id": "https://yesbrohq.com/#org"},
            "dateModified": day + "T08:00:00+05:30"}
    items = [{"@type": "ListItem", "position": i + 1, "name": e[1], "url": "https://yesbrohq.com/" + e[2]} for i, e in enumerate(EDITIONS)]
    page = {"@type": "CollectionPage", "@id": "https://yesbrohq.com/#page", "url": "https://yesbrohq.com/", "name": "Yes Bro papers",
            "isPartOf": {"@id": "https://yesbrohq.com/#site"}, "mainEntity": {"@type": "ItemList", "itemListElement": items}}
    return json.dumps({"@context": "https://schema.org", "@graph": [org, site, page]}, ensure_ascii=False).replace("</", "<\\/")

def landing_meme(d):
    """Small Meme of the day from Yes Bro Daily (memes.py). Empty string if anything goes wrong."""
    try:
        import memes
        nb = newest("stories_", d)
        if not nb: return "", ""
        m, st, _ = memes.make(json.load(open(nb[1])), "daily", nb[0])
        return memes.html_box(m, st, small=True, paper_link=("daily/", "More in Yes Bro Daily")), memes.CSS
    except Exception as ex:
        print("landing meme skipped:", ex); return "", ""

def build(d, site):
    meme, meme_css = landing_meme(d)
    cards, dates = [], []
    for e in EDITIONS:
        h, dt = card(e, d, site); cards.append(h)
        if dt: dates.append(dt)
    day = max(dates) if dates else datetime.date.today().isoformat()
    dlabel = datetime.date.fromisoformat(day).strftime("%A %-d %B %Y")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Yes Bro: Free Daily Newspapers for Your Field, with News, Jobs and Explainers</title>
<meta name="description" content="{DESC}">
<meta name="abstract" content="Yes Bro publishes free daily newspapers by field. Build your own newspaper. Read every day what you want. No accounts and no tracking of what you read.">
<meta name="keywords" content="Yes Bro, daily newspaper, India news, AI news, business news, free newspaper, no tracking">
<link rel="canonical" href="https://yesbrohq.com/">
<link rel="alternate" type="text/plain" title="llms.txt" href="https://yesbrohq.com/llms.txt">
<meta name="robots" content="index,follow,max-image-preview:large">
<meta property="og:type" content="website"><meta property="og:site_name" content="Yes Bro">
<meta property="og:title" content="Yes Bro: Free Daily Newspapers for Your Field">
<meta property="og:description" content="{DESC}">
<meta property="og:url" content="https://yesbrohq.com/">
<meta property="og:image" content="https://yesbrohq.com/img/landing/daily.webp">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Yes Bro: Free Daily Newspapers for Your Field">
<meta name="twitter:description" content="{DESC}">
<meta name="twitter:image" content="https://yesbrohq.com/img/landing/daily.webp">
<meta property="og:image:alt" content="Yes Bro, free daily newspapers">
<script type="application/ld+json">{ld(day)}</script>
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Yes Bro">
<meta name="theme-color" content="#f3ead6">
<link rel="manifest" href="manifest.json">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<link rel="apple-touch-icon" href="icon-512.png">
<link rel="icon" href="icon-512.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=UnifrakturMaguntia&family=Playfair+Display:wght@700;900&family=Old+Standard+TT:ital,wght@0,400;0,700;1,400&family=Libre+Caslon+Text:ital,wght@0,400;0,700;1,400&display=swap" rel="stylesheet">
<style>{CSS}{A2HS_CSS}{meme_css}{share.CSS}{maker.css()}</style></head>
<body id="top">
<div class="cbar" id="cbar" role="region" aria-label="Your paper"><a class="cgo" id="cgo" href="daily/">Continue to your paper</a>
<span class="cmore"><button type="button" id="call">Show all papers</button><button type="button" id="cforget">Forget my pick</button></span></div>
<div class="sheet">
<header>
<div class="masthead"><h1>Yes Bro</h1><p class="motto">The front door. Mind the step.</p></div>
<div class="dateline"><span>Front Door</span><b>{esc(dlabel)}</b><span>Price: Free, unlike your opinions</span></div>
{a2hs_html(LANDING_A2HS)}
{share.bar(SHARE_URL, SHARE_TITLE, SHARE_TEXT, label="Share Yes Bro")}
</header>
<main>
<p class="tagline">A free daily newspaper for whatever you do.</p>
<p class="subtag">Pick your paper. Bro means everyone.</p>
<div class="mypaper-door"><a href="mypaper/">My Paper<span>Mix sections from every edition</span></a></div>
<div class="pick-head" id="papers">Pick your paper</div>
<div class="cards">{"".join(cards)}</div>
{meme}
{AD}
<section class="yourfield"><h3>Missing a paper?</h3><p>Tell us what you do and what you would read. Enough of you ask, we print it. That is the whole process, and we are quite proud of it.</p>
<a class="btn" href="{FIELD_MAIL}">Not here yet? Tell us your field</a></section>
</main>
{share.bar(SHARE_URL, SHARE_TITLE, SHARE_TEXT, foot=True, label="Share Yes Bro")}
<footer>Printed fresh every morning. Every headline links to the original report, which is more than most headlines do.<p class="credit"><a href="https://earth5r.org/">A product of Earth5R</a></p>{maker.html_block("landing", "Yes Bro")}</footer>
</div>{share.panel(SHARE_URL, SHARE_TITLE, SHARE_TEXT, heading="Share all the papers")}{JS}{share.JS}{yb_auth_strip.html()}</body></html>
"""

LANDING_A2HS = "The front door, on your phone. Opens faster than a newspaper and folds better."

MANIFEST = {"id": "/", "name": "Yes Bro", "short_name": "Yes Bro", "start_url": "/", "scope": "/", "display": "standalone",
            "background_color": "#f3ead6", "theme_color": "#f3ead6",
            "icons": [{"src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"}]}

def visible_text_check(page):
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", page, flags=re.S)
    t = re.sub(r'href="[^"]*"', "", t)
    t = html.unescape(re.sub(r"<[^>]+>", " ", t))
    house = re.sub(r'<p class="c-top">.*?</p>', "", page, flags=re.S)  # top story headlines are news, not house copy
    house = re.sub(r"<script.*?</script>|<style.*?</style>", "", house, flags=re.S)
    house_count_check("landing", html.unescape(re.sub(r"<[^>]+>", " ", house)))
    bad = [ch for ch in ("\u2014", "\u2013", ";") if ch in t]
    if bad:
        raise SystemExit(f"banned characters in visible copy: {bad}")
    # House rule: never say intern/internship in our own copy, and never link an Earth5R internship page.
    hits = re.findall(r"(?i)\bintern(?:ship)?s?\b", t) + re.findall(r"(?i)earth5r\.org/[^\"]*intern", page)
    if hits:
        raise SystemExit(f"no-intern rule broken in landing copy: {hits}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", default="/workspace/yesbro-site")
    ap.add_argument("--stories-dir", default=os.path.dirname(os.path.abspath(__file__)))
    a = ap.parse_args()
    page = build(a.stories_dir, a.site)
    visible_text_check(page)
    import blocklist; blocklist.guard_html(page, "landing")
    open(os.path.join(a.site, "index.html"), "w").write(page)
    json.dump(MANIFEST, open(os.path.join(a.site, "manifest.json"), "w"), separators=(",", ":"))
    print("wrote", os.path.join(a.site, "index.html"), "and manifest.json")
    try:
        import sitemap
        sitemap.write(a.site)
    except Exception as ex:
        print("sitemap skipped:", ex)

if __name__ == "__main__":
    main()
