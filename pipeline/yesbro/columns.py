#!/usr/bin/env python3
"""Yes Bro Explains: original columns for every Yes Bro paper.

Source files: columns/<key>/<YYYY-MM-DD>-<slug>.md, each with a front matter block:

  ---
  title: How AI is changing UX design jobs in 2026
  slug: how-ai-is-changing-ux-design-jobs-2026
  date: 2026-10-25
  dek: One or two sentences under the headline.
  description: Optional meta description (defaults to the dek).
  ---
  Body in light Markdown: blank-line paragraphs, "## " subheads, "- " bullets,
  **bold**, *italic* and [inline links](https://...).

Commands:
  python3 columns.py check   [keys...]          validate copy (words, banned characters, links load)
  python3 columns.py publish [keys...] [--site DIR]   write column pages and /<folder>/explains/ indexes, then the sitemap

build_html.py calls columns.box_html(key, date) to show the current column (newest, at most 7 days old)
in a "Yes Bro Explains" box after section 1, so every daily rebuild picks it up automatically.
"""
import datetime, glob, html, json, os, re, sys
import blocklist

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = "https://yesbrohq.com"
# key: (folder, field label used in "Yes Bro <label>", share image)
EDS = {
    "daily": ("daily", "Daily"),
    "finance": ("finance", "Finance"),
    "business": ("business", "Business"),
    "ai": ("ai", "AI"),
    "health": ("health", "Health"),
    "startups": ("startups", "Startups"),
    "realestate": ("realestate", "Real Estate"),
    "auto": ("auto", "Auto"),
    "fashion": ("fashion", "Fashion"),
    "highered": ("highered", "Higher Ed"),
    "schools": ("schools", "Schools"),
    "marketing": ("marketing", "Marketing"),
    "ux": ("ux", "UX & Design"),
    "arch": ("architecture", "Architecture"),
    "sustainability": ("sustainability", "Sustainability"),
    "consulting": ("consulting", "Consulting"),
    "aviation": ("aviation", "Aviation"),
    "packaging": ("packaging", "Packaging"),
    "healing": ("healing", "Healing"),
}
# Papers that carry no Earth5R credit or FIELDWORK promotion anywhere (Healing promotes mindfulwholeness.org instead).
NO_E5R = {"healing"}
KEEP_DAYS = 7
BANNED = re.compile(r"[\u2014\u2013;]|\bNGO\b")
# House rule: never say intern/internship in our own copy (readers are professionals). Earth5R offers the FIELDWORK fellowship.
NOINTERN = re.compile(r"(?i)\bintern(ship)?s?\b")
E5R_INTERN = re.compile(r"(?i)earth5r\.org/[^)\s\"]*intern")

# Width of 'Yes Bro <Field>' in em at equal size (UnifrakturMaguntia 'Yes Bro ' = 3.89em, Playfair 900 field word), measured in Chrome.
BRAND_W = {'Daily': 2.52, 'UX & Design': 5.85, 'Architecture': 5.91, 'Schools': 3.68, 'Sustainability': 6.54, 'Startups': 4.03, 'Higher Ed': 4.8, 'Consulting': 5.21, 'Health': 3.14, 'Marketing': 4.9, 'Finance': 3.72, 'Aviation': 3.95, 'Business': 4.12, 'Newspaper': 5.18, 'AI': 1.09, 'Packaging': 4.93, 'Fashion': 3.80, 'Real Estate': 5.50, 'Auto': 2.20}
def brand(name):
    """'Yes Bro' in blackletter, the field word in bold Playfair at the SAME size (cap heights match at 1em).
    The whole title scales down together via --w when the line is too narrow."""
    if name.startswith("Yes Bro "):
        f = name[8:]
        w = round((3.99 + BRAND_W.get(f, 0.56 * len(f))) * 1.03, 2)
        return (f'<span class="ybt" style="--w:{w}"><span class="yb">Yes Bro</span> '
                f'<span class="fw">{esc(f)}</span></span>')
    return esc(name)

def esc(s):
    return html.escape(s or "", quote=True)

def image(key):
    return f"{SITE}/img/landing/{key}.webp"

def parse(path):
    raw = open(path, encoding="utf-8").read()
    m = re.match(r"---\n(.*?)\n---\n(.*)", raw, re.S)
    if not m:
        raise SystemExit(f"{path}: missing front matter")
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1); meta[k.strip()] = v.strip()
    meta["body"] = m.group(2).strip()
    meta["file"] = path
    for f in ("title", "slug", "date", "dek"):
        if not meta.get(f):
            raise SystemExit(f"{path}: front matter needs {f}")
    meta["d"] = datetime.date.fromisoformat(meta["date"])
    return meta

def load(key):
    import blocklist  # Begin Group blocklist: a column that mentions Begin is never shown or published
    cols = [parse(p) for p in glob.glob(os.path.join(HERE, "columns", key, "*.md"))]
    n = len(cols); cols = [c for c in cols if not blocklist.blocked({k: v for k, v in c.items() if isinstance(v, str)})]
    if n != len(cols): print(f"BLOCKED: Begin or fairs {n - len(cols)} column(s) in {key}", file=sys.stderr)
    return sorted(cols, key=lambda c: (c["d"], c["slug"]), reverse=True)

def url(key, col=None):
    folder = EDS[key][0]
    return f"{SITE}/{folder}/explains/" + (f"{col['slug']}/" if col else "")

def to_date(date):
    """Accepts 2026-10-25 or 'Sunday 25 October 2026'."""
    if isinstance(date, datetime.date):
        return date
    try:
        return datetime.date.fromisoformat(date)
    except ValueError:
        return datetime.datetime.strptime(date, "%A %d %B %Y").date()

def current(key, date):
    d = to_date(date)
    for c in load(key):
        if c["d"] <= d and (d - c["d"]).days < KEEP_DAYS:
            return c
    return None

def nice(d):
    return f"{d.day} {d.strftime('%B')} {d.year}"

def inline(s):
    s = esc(s)
    def link(m):
        t, u = m.group(1), html.unescape(m.group(2))
        return f'<a href="{esc(u)}" target="_blank" rel="noopener">{t}</a>'
    s = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", s)
    return s

def render(body):
    out = []
    for block in re.split(r"\n\s*\n", body.strip()):
        b = block.strip()
        if b.startswith("## "):
            out.append(f"<h2>{inline(b[3:].strip())}</h2>")
        elif all(l.strip().startswith("- ") for l in b.splitlines()):
            out.append("<ul>" + "".join(f"<li>{inline(l.strip()[2:])}</li>" for l in b.splitlines()) + "</ul>")
        else:
            out.append(f"<p>{inline(' '.join(l.strip() for l in b.splitlines()))}</p>")
    return "\n".join(out)

def plain(body):
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", body)
    return re.sub(r"[*#]", "", t)

def words(body):
    return len(re.findall(r"[A-Za-z0-9₹$€£%][\w'.,%₹$€£-]*", plain(body)))

def links(body):
    return re.findall(r"\[([^\]]+)\]\(([^)\s]+)\)", body)

# ---------------------------------------------------------------- the box in each paper
BOX_CSS = r"""
.ex-special{--ex-bg:#E3BF5A;--ex-ink:#2a1f12;--ex-soft:#3b2d1a;--ex-faint:#4a3a22;--ex-link:#4a2c10;
  background-color:var(--ex-bg);background-image:radial-gradient(rgba(70,45,10,.13) .9px,transparent 1.3px),linear-gradient(180deg,rgba(255,240,190,.35),rgba(150,105,20,.12));
  background-size:5px 5px,100% 100%;border:6px double var(--ex-ink);outline:1px solid var(--ex-ink);outline-offset:3px;color:var(--ex-ink);position:relative}
.ex-tab{display:inline-block;margin:0 0 6px;background:var(--ex-ink);color:#F6E3A6;font-family:"Old Standard TT",Georgia,serif;font-weight:700;font-size:11.5px;
  letter-spacing:.26em;text-transform:uppercase;padding:4px 10px 3px;line-height:1.2}
.ex-brand{margin:0 0 4px;font-family:"UnifrakturMaguntia","Old English Text MT","Playfair Display",serif;font-weight:400;font-size:clamp(30px,5vw,40px);line-height:1.05;color:var(--ex-ink)}
.ex-brand .yb,.ex-brand .fw{display:inline-block}.ex-brand .fw{font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:1em;margin-left:.1em}
.explains{max-width:980px;margin:8px auto 32px;padding:14px 22px 18px;scroll-margin-top:70px}
.explains .ex-kick{font-family:"Old Standard TT",Georgia,serif;font-size:11.5px;letter-spacing:.2em;text-transform:uppercase;color:var(--ex-faint);
  border-top:2px solid var(--ex-ink);border-bottom:1px solid var(--ex-ink);padding:4px 0 3px;margin:0 0 10px}
.explains h3{margin:0 0 6px;font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:clamp(23px,3.4vw,32px);line-height:1.15;color:var(--ex-ink)}
.explains h3 a{color:var(--ex-ink);text-decoration:none}
.explains h3 a:hover{text-decoration:underline;text-decoration-thickness:2px}
.explains p.ex-dek{margin:0 0 10px;font-size:16px;line-height:1.5;color:var(--ex-soft);font-style:italic}
.explains .ex-foot{display:flex;flex-wrap:wrap;gap:8px 16px;align-items:center;margin:0;font-family:"Old Standard TT",Georgia,serif;font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--ex-faint)}
.explains a.ex-go{font-weight:700;font-size:13px;letter-spacing:.14em;color:#F6E3A6;background:var(--ex-ink);text-decoration:none;border:2px solid var(--ex-ink);padding:6px 14px}
.explains a.ex-go:hover{background:#4a3a22}
.explains a.ex-all{color:var(--ex-link);font-weight:700}
"""

def box_html(key, date):
    """HTML for the featured box, or '' when the paper has no column from the last 7 days."""
    if key not in EDS:
        return ""
    c = current(key, date)
    if not c:
        return ""
    folder = EDS[key][0]
    href = f"/{folder}/explains/{c['slug']}/"
    mins = max(1, round(words(c["body"]) / 220))
    return (f'<aside class="explains ex-special" id="explains" aria-label="Yes Bro Explains, special column">'
            f'<p class="ex-tab">Special column</p><p class="ex-brand"><span class="yb">Yes Bro</span> <span class="fw">Explains</span></p>'
            f'<p class="ex-kick">Our own column, sourced to the hilt &middot; {esc(nice(c["d"]))}</p>'
            f'<h3><a href="{href}">{esc(c["title"])}</a></h3><p class="ex-dek">{esc(c["dek"])}</p>'
            f'<p class="ex-foot"><a class="ex-go" href="{href}">Read the column &rarr;</a><span>Yes Bro Desk &middot; {mins} min read</span>'
            f'<a class="ex-all" href="/{folder}/explains/">All columns</a></p></aside>')

# ---------------------------------------------------------------- column pages
PAGE_CSS = r"""
:root{--paper:#f1e7cf;--paper-deep:#e8dbbb;--ink:#2e2a24;--ink-soft:#4a4238;--ink-faint:#6f6454;--rule:#3d362d;--rule-soft:#a8987a;--link:#5b3a1e}
*{box-sizing:border-box}
html{background:#d9cba8}
body{margin:0;color:var(--ink);font-family:"Libre Caslon Text","Old Standard TT",Georgia,"Times New Roman",serif;font-size:17px;line-height:1.62;-webkit-font-smoothing:antialiased}
.sheet{max-width:860px;margin:0 auto;padding:22px 34px 40px;background-color:var(--paper);
  background-image:radial-gradient(ellipse at 20% 0%,rgba(255,250,235,.55),transparent 60%),radial-gradient(ellipse at 100% 100%,rgba(190,165,115,.28),transparent 55%);
  box-shadow:0 0 0 1px rgba(80,60,30,.15),0 8px 40px rgba(70,50,20,.25);min-height:100vh}
a{color:var(--link)}
.topbar{display:flex;justify-content:space-between;flex-wrap:wrap;gap:6px 14px;font-family:"Old Standard TT",Georgia,serif;font-size:12.5px;letter-spacing:.1em;text-transform:uppercase}
.topbar a{color:var(--ink);text-decoration:none;border-bottom:1px solid var(--rule-soft)}
.masthead{text-align:center;border-top:4px double var(--rule);border-bottom:1px solid var(--rule);margin-top:10px;padding:6px 0 4px}
.family{font-family:"Old Standard TT",Georgia,serif;font-size:11.5px;letter-spacing:.22em;text-transform:uppercase;color:var(--ink-faint);margin:2px 0 0}
.masthead .mh{margin:0;font-family:"UnifrakturMaguntia","Old English Text MT","Playfair Display",serif;font-weight:400;font-size:clamp(40px,8vw,72px);line-height:1.05}
.masthead .mh a{color:inherit;text-decoration:none}
.masthead{container-type:inline-size}.ybt{font-size:min(1em,calc((100cqw - 4px)/var(--w)))}.yb,.fw{display:inline-block}.fw{font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:1em;letter-spacing:0;margin-left:.1em;vertical-align:baseline}
.dateline{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;border-bottom:4px double var(--rule);padding:5px 2px;
  font-family:"Old Standard TT",Georgia,serif;font-size:12.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--ink-soft);margin-bottom:22px}
.ex-special{--ex-bg:#E3BF5A;--ex-ink:#2a1f12;--ex-soft:#3b2d1a;--ex-faint:#4a3a22;--ex-link:#4a2c10;
  background-color:var(--ex-bg);background-image:radial-gradient(rgba(70,45,10,.13) .9px,transparent 1.3px),linear-gradient(180deg,rgba(255,240,190,.35),rgba(150,105,20,.12));
  background-size:5px 5px,100% 100%;border:6px double var(--ex-ink);outline:1px solid var(--ex-ink);outline-offset:3px;color:var(--ex-ink);position:relative}
.ex-tab{display:inline-block;margin:0 0 6px;background:var(--ex-ink);color:#F6E3A6;font-family:"Old Standard TT",Georgia,serif;font-weight:700;font-size:11.5px;
  letter-spacing:.26em;text-transform:uppercase;padding:4px 10px 3px;line-height:1.2}
.ex-brand{margin:0 0 4px;font-family:"UnifrakturMaguntia","Old English Text MT","Playfair Display",serif;font-weight:400;font-size:clamp(30px,5vw,40px);line-height:1.05;color:var(--ex-ink)}
.ex-brand .yb,.ex-brand .fw{display:inline-block}.ex-brand .fw{font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:1em;margin-left:.1em}
.colhead{padding:14px 20px 4px;margin:0 0 22px}.colhead .kicker{color:var(--ex-faint);border-top:2px solid var(--ex-ink);padding-top:5px}.colhead h1{color:var(--ex-ink)}.colhead .dek{color:var(--ex-soft)}.colhead .byline{color:var(--ex-faint);border-color:var(--ex-ink)}.colhead .byline b{color:var(--ex-ink)}
.kicker{font-family:"Old Standard TT",Georgia,serif;font-size:12px;letter-spacing:.24em;text-transform:uppercase;color:var(--ink-faint);margin:0 0 6px}
h1{margin:0 0 10px;font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:clamp(30px,5.4vw,46px);line-height:1.1;color:var(--ink)}
.dek{margin:0 0 12px;font-size:19px;line-height:1.5;font-style:italic;color:var(--ink-soft)}
.byline{font-family:"Old Standard TT",Georgia,serif;font-size:12.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--ink-faint);
  border-top:1px solid var(--rule-soft);border-bottom:1px solid var(--rule-soft);padding:6px 0;margin:0 0 18px}
.byline b{color:var(--ink)}
article.col p{margin:0 0 14px;text-align:justify;hyphens:auto}
article.col > header.colhead + p::first-letter{float:left;font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:3.4em;line-height:.85;padding:5px 7px 0 0;color:var(--ink)}
article.col h2{margin:24px 0 8px;font-family:"Playfair Display",Georgia,serif;font-weight:700;font-size:23px;line-height:1.2;border-top:1px solid var(--rule);padding-top:8px}
article.col ul{margin:0 0 14px;padding-left:22px}
article.col li{margin:0 0 6px}
article.col a{text-decoration-color:var(--rule-soft);text-underline-offset:3px}
.sources{margin:26px 0 0;border-top:3px double var(--rule);padding-top:8px;font-size:14px;line-height:1.5;color:var(--ink-soft)}
.sources h2{margin:0 0 6px;font-family:"Old Standard TT",Georgia,serif;font-size:12.5px;letter-spacing:.2em;text-transform:uppercase;color:var(--ink)}
.sources ol{margin:0;padding-left:22px}
.sources a{word-break:break-word}
.more{margin:26px 0 8px;display:flex;flex-wrap:wrap;gap:10px}
.more a{display:inline-block;font-family:"Old Standard TT",Georgia,serif;font-weight:700;font-size:13px;letter-spacing:.14em;text-transform:uppercase;
  color:var(--ink);text-decoration:none;border:1px solid var(--rule);padding:7px 14px}
.more a:hover{background:rgba(90,70,40,.1)}
.list{list-style:none;margin:0;padding:0}
.list li{border-bottom:1px dotted var(--rule-soft);padding:12px 0}
.list h2{margin:0 0 4px;font-family:"Playfair Display",Georgia,serif;font-weight:700;font-size:23px;line-height:1.2}
.list h2 a{color:var(--ink);text-decoration:none}
.list h2 a:hover{text-decoration:underline}
.list p{margin:0 0 4px;font-style:italic;color:var(--ink-soft)}
.list .when{font-family:"Old Standard TT",Georgia,serif;font-size:12px;letter-spacing:.1em;text-transform:uppercase;color:var(--ink-faint)}
footer{margin-top:28px;border-top:4px double var(--rule);padding-top:8px;text-align:center;font-family:"Old Standard TT",Georgia,serif;font-size:12.5px;font-style:italic;color:var(--ink-faint)}
footer a{color:var(--ink-soft)}
@media (max-width:640px){.sheet{padding:14px 16px 30px}body{font-size:16.5px}.dek{font-size:17.5px}article.col p{text-align:left}}
"""
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=UnifrakturMaguntia&family=Playfair+Display:wght@700;900&family=Old+Standard+TT:ital,wght@0,400;0,700;1,400&family=Libre+Caslon+Text:ital,wght@0,400;0,700;1,400&display=swap" rel="stylesheet">')
CREDIT = '<p class="credit"><a href="https://earth5r.org/">A product of Earth5R</a></p>'
PUBLISHER = {"@type": "Organization", "name": "Yes Bro", "url": SITE + "/",
             "logo": {"@type": "ImageObject", "url": SITE + "/icon-512.png", "width": 512, "height": 512}}

def head(title, desc, canon, img, og_type, ld, depth):
    from build_html import FIT_CSS
    up = "../" * depth
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{canon}">
<meta name="robots" content="index,follow,max-image-preview:large">
<meta property="og:type" content="{og_type}"><meta property="og:site_name" content="Yes Bro">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canon}"><meta property="og:image" content="{img}"><meta property="og:image:width" content="800"><meta property="og:image:height" content="450">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(desc)}"><meta name="twitter:image" content="{img}">
<meta name="theme-color" content="#f3ead6"><link rel="icon" href="{up}icon-512.png"><link rel="apple-touch-icon" href="{up}icon-512.png">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
{FONTS}
<style>{PAGE_CSS}{FIT_CSS}</style></head>"""

def masthead(key, kicker_right):
    folder, label = EDS[key]
    return (f'<div class="topbar"><a href="/{folder}/">&larr; Yes Bro {esc(label)}</a><a href="/">All Yes Bro papers</a></div>'
            f'<div class="masthead"><p class="family">Yes Bro Newspaper</p><p class="mh"><a href="/{folder}/">{brand("Yes Bro " + label)}</a></p></div>'
            f'<div class="dateline"><span>Yes Bro Explains</span><span>{kicker_right}</span></div>')

def column_page(key, c):
    folder, label = EDS[key]
    canon = url(key, c)
    desc = c.get("description") or c["dek"]
    srcs, seen = [], set()
    for t, u in links(c["body"]):
        if u not in seen:
            seen.add(u); srcs.append((t, u))
    mins = max(1, round(words(c["body"]) / 220))
    ld = {"@context": "https://schema.org", "@type": "NewsArticle", "headline": c["title"][:110], "description": desc,
          "image": [image(key)], "datePublished": c["date"] + "T04:30:00+05:30", "dateModified": c["date"] + "T04:30:00+05:30",
          "author": {"@type": "Organization", "name": "Yes Bro Desk", "url": SITE + "/"}, "publisher": PUBLISHER,
          "mainEntityOfPage": {"@type": "WebPage", "@id": canon}, "articleSection": f"Yes Bro {label}",
          "isAccessibleForFree": True, "inLanguage": "en", "wordCount": words(c["body"]),
          "citation": [u for _, u in srcs if "earth5r.org" not in u]}
    src_html = "".join(f'<li><a href="{esc(u)}" target="_blank" rel="noopener">{esc(re.sub(r"^www[.]", "", u.split("/")[2]))}</a>: {esc(t)}</li>' for t, u in srcs)
    return (head(f'{c["title"]} | Yes Bro {label}', desc, canon, image(key), "article", ld, 3)
            + f'\n<body><div class="sheet"><header>{masthead(key, esc(nice(c["d"])))}</header>'
            + f'<main><article class="col"><header class="colhead ex-special"><p class="ex-tab">Special column</p><p class="ex-brand"><span class="yb">Yes Bro</span> <span class="fw">Explains</span></p><p class="kicker">{esc(label)}</p><h1>{esc(c["title"])}</h1>'
            + f'<p class="dek">{esc(c["dek"])}</p>'
            + f'<p class="byline">By <b>Yes Bro Desk</b> &middot; <time datetime="{c["date"]}">{esc(nice(c["d"]))}</time> &middot; {mins} min read</p></header>'
            + render(c["body"])
            + f'<section class="sources"><h2>Sources and links in this column</h2><ol>{src_html}</ol></section>'
            + f'</article><nav class="more"><a href="/{folder}/">More Yes Bro {esc(label)} &rarr;</a><a href="/{folder}/explains/">All Yes Bro Explains columns</a></nav></main>'
            + f'<footer>Yes Bro Explains is written by the Yes Bro Desk. Every fact links to its source. The jokes link to nothing.{"" if key in NO_E5R else CREDIT}</footer></div></body></html>\n')

def index_page(key, cols):
    folder, label = EDS[key]
    canon = url(key)
    title = f"Yes Bro Explains: {label} Columns and Analysis | Yes Bro {label}"
    desc = f"Every Yes Bro Explains column for {label}: original, sourced analysis of the trends, data and jobs that matter this week."
    ld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": f"Yes Bro Explains: {label}", "url": canon,
          "description": desc, "publisher": PUBLISHER, "isPartOf": {"@type": "WebSite", "name": "Yes Bro", "url": SITE + "/"},
          "mainEntity": {"@type": "ItemList", "itemListElement": [
              {"@type": "ListItem", "position": i + 1, "url": url(key, c), "name": c["title"]} for i, c in enumerate(cols)]}}
    items = "".join(f'<li><h2><a href="{c["slug"]}/">{esc(c["title"])}</a></h2><p>{esc(c["dek"])}</p>'
                    f'<span class="when">{esc(nice(c["d"]))} &middot; Yes Bro Desk</span></li>' for c in cols)
    return (head(title, desc, canon, image(key), "website", ld, 2)
            + f'\n<body><div class="sheet"><header>{masthead(key, "The column archive")}</header>'
            + f'<main><p class="kicker">Our own columns</p><h1>Yes Bro Explains: {esc(label)}</h1>'
            + f'<p class="dek">Original analysis from the Yes Bro Desk, with a link for every fact. Opinions are kept to a minimum, with some effort.</p>'
            + f'<ul class="list">{items}</ul><nav class="more"><a href="/{folder}/">More Yes Bro {esc(label)} &rarr;</a></nav></main>'
            + f'<footer>New columns twice a week.{"" if key in NO_E5R else CREDIT}</footer></div></body></html>\n')

# ---------------------------------------------------------------- commands
def visible(htmltext):
    v = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", htmltext)
    return html.unescape(re.sub(r"<[^>]+>", " ", v))

def check(keys, net=True):
    import requests
    ok = True
    UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"}
    for k in keys:
        for c in load(k):
            probs = []
            n = words(c["body"])
            if not 500 <= n <= 800: probs.append(f"{n} words")
            for f in ("title", "dek", "body", "description"):
                for m in BANNED.finditer(c.get(f, "")):
                    probs.append(f"banned {m.group()!r} in {f}: ...{c[f][max(0, m.start()-30):m.end()+20]}...")
            for f in ("title", "dek", "body", "description"):
                txt = re.sub(r"\]\([^)]*\)", "]", c.get(f, ""))  # our words, not URLs
                for m in NOINTERN.finditer(txt):
                    probs.append(f"no-intern rule: {m.group()!r} in {f}: ...{txt[max(0, m.start()-30):m.end()+20]}... (say FIELDWORK fellowship or role)")
            for m in E5R_INTERN.finditer(c["body"]):
                probs.append(f"no-intern rule: Earth5R internship URL {m.group()}..., link https://earth5r.org/fieldwork/ instead")
            if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", c["slug"]): probs.append("bad slug")
            ls = links(c["body"])
            if len(ls) < 3: probs.append("fewer than 3 links")
            if net:
                for t, u in ls:
                    try:
                        r = requests.get(u, headers=UA, timeout=25, allow_redirects=True)
                        st = r.status_code
                    except Exception as e:
                        st = str(e)[:40]
                    if st != 200: probs.append(f"link {st}: {u}")
            print(f"{k:15s} {c['date']} {n:4d}w {len(ls):2d} links  {c['slug']}  {'OK' if not probs else probs}")
            ok = ok and not [p for p in probs if not p.startswith("link 403")]
    return ok

def publish(keys, site):
    for k in keys:
        cols = load(k)
        if not cols:
            continue
        folder = EDS[k][0]
        for c in cols:
            d = os.path.join(site, folder, "explains", c["slug"]); os.makedirs(d, exist_ok=True)
            page = column_page(k, c)
            bad = BANNED.findall(visible(page))
            if bad: raise SystemExit(f"{k}/{c['slug']}: banned characters in page {bad}")
            bad = NOINTERN.findall(visible(page)) or E5R_INTERN.findall(page)
            if bad: raise SystemExit(f"{k}/{c['slug']}: no-intern rule broken in page {bad}")
            import blocklist; blocklist.guard_html(page, f"{k}/{c['slug']}")
            open(os.path.join(d, "index.html"), "w").write(page)
        ip = index_page(k, cols); blocklist.guard_html(ip, f"{k}/explains")
        open(os.path.join(site, folder, "explains", "index.html"), "w").write(ip)
        print(f"published {k}: {len(cols)} column(s), latest {cols[0]['slug']}")
    import sitemap
    sitemap.write(site)

if __name__ == "__main__":
    args = sys.argv[1:]
    site = "/workspace/yesbro-site"
    if "--site" in args:
        i = args.index("--site"); site = args[i + 1]; del args[i:i + 2]
    net = "--no-net" not in args
    args = [a for a in args if a != "--no-net"]
    cmd, keys = (args[0] if args else "check"), (args[1:] or list(EDS))
    if cmd == "check":
        sys.exit(0 if check(keys, net) else 1)
    elif cmd == "publish":
        publish(keys, site)
    else:
        raise SystemExit(__doc__)
