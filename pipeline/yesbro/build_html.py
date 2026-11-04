#!/usr/bin/env python3
"""Build the printed-newsprint HTML edition of Yes Bro Newspaper.

Usage:
  python3 build_html.py stories.html.json "Sunday 25 October 2026" out.html [--fallback stories.out.json]

stories.html.json : output of `fetch_images.py ... --mode html` (needs section, headline, summary, url, image).
--fallback        : optional output of the canvas-mode fetch (small embedded thumbnails). When given, each
                    remote image gets its thumbnail as an onerror fallback, so a blocked hotlink still shows
                    a picture. Stories with no image at all render text only (no placeholder).
"""
import sys, argparse, html, json, re
from sources import src
import yb_auth_strip

# Long sections: only the top FEATURED stories in each section get photos and the full card layout.
# Every story after that runs as a compact brief (headline, source, summary, Read more) in a
# ruled multi-column list with no image. This keeps 20 to 30 story sections readable and the file small.
FEATURED = 5

SECTIONS = ["India Politics", "India Overall", "India Startups", "India ESG and Environment",
            "Global Overall", "Global AI and Technology", "Global ESG and Environment"]

# Width of 'Yes Bro <Field>' in em at equal size (UnifrakturMaguntia 'Yes Bro ' = 3.89em, Playfair 900 field word), measured in Chrome.
BRAND_W = {'Daily': 2.52, 'UX & Design': 5.85, 'Architecture': 5.91, 'Schools': 3.68, 'Sustainability': 6.54, 'Startups': 4.03, 'Higher Ed': 4.8, 'Consulting': 5.21, 'Health': 3.14, 'Marketing': 4.9, 'Finance': 3.72, 'Aviation': 3.95, 'Business': 4.12, 'Newspaper': 5.18, 'Packaging': 4.93, 'Fashion': 3.80, 'Real Estate': 5.50, 'Auto': 2.20}
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

def slug(s):
    return "".join(c if c.isalnum() else "-" for c in s.lower()).strip("-")

CSS = r"""
:root{
  --paper:#f1e7cf; --paper-deep:#e8dbbb; --ink:#2e2a24; --ink-soft:#4a4238; --ink-faint:#6f6454;
  --rule:#3d362d; --rule-soft:#a8987a; --link:#5b3a1e;
}
*{box-sizing:border-box}
html{background:#d9cba8}
body{margin:0;color:var(--ink);font-family:"Libre Caslon Text","Old Standard TT",Georgia,"Times New Roman",serif;
  font-size:15.5px;line-height:1.5;-webkit-font-smoothing:antialiased}
.sheet{max-width:1320px;margin:0 auto;padding:22px 34px 40px;background-color:var(--paper);
  background-image:
    radial-gradient(ellipse at 20% 0%,rgba(255,250,235,.55),transparent 60%),
    radial-gradient(ellipse at 100% 100%,rgba(190,165,115,.28),transparent 55%),
    url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='180' height='180'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='3' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 .35  0 0 0 0 .28  0 0 0 0 .18  0 0 0 .09 0'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>");
  box-shadow:0 0 0 1px rgba(80,60,30,.15),0 8px 40px rgba(70,50,20,.25)}
a{color:inherit}
/* Masthead */
.ears{display:flex;justify-content:space-between;align-items:flex-end;gap:16px;font-family:"Old Standard TT",Georgia,serif;
  font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--ink-soft)}
.ear{border:1px solid var(--rule-soft);padding:6px 10px;max-width:220px;text-align:center;line-height:1.35}
.masthead{text-align:center;border-top:4px double var(--rule);border-bottom:1px solid var(--rule);margin-top:10px;padding:6px 0 2px}
.masthead h1{margin:0;font-family:"UnifrakturMaguntia","Old English Text MT","Playfair Display",serif;font-weight:400;
  font-size:clamp(46px,9vw,112px);line-height:1.02;color:var(--ink);letter-spacing:.01em}
.motto{font-family:"Old Standard TT",Georgia,serif;font-style:italic;font-size:14px;color:var(--ink-soft);margin:0 0 6px}
.dateline{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;border-bottom:4px double var(--rule);
  padding:5px 2px;font-family:"Old Standard TT",Georgia,serif;font-size:13px;letter-spacing:.08em;text-transform:uppercase;color:var(--ink-soft)}
.dateline b{color:var(--ink);font-weight:700}
nav.sections{display:flex;flex-wrap:wrap;justify-content:center;gap:6px 0;border-bottom:1px solid var(--rule);padding:8px 0;margin-bottom:18px}
nav.sections a{font-family:"Old Standard TT",Georgia,serif;font-size:13.5px;font-weight:700;letter-spacing:.07em;text-transform:uppercase;
  text-decoration:underline;text-decoration-color:var(--rule);text-underline-offset:4px;color:var(--ink);padding:3px 14px;border-right:2px solid var(--ink-soft);cursor:pointer}
nav.sections a:last-child{border-right:none}
nav.sections a:hover{color:var(--ink);text-decoration-color:var(--ink);background:rgba(90,70,40,.08)}
/* Sections */
section.sec{margin:0 0 26px;scroll-margin-top:12px}
.sec-head{display:flex;align-items:baseline;gap:14px;border-top:3px solid var(--rule);border-bottom:1px solid var(--rule);
  padding:5px 0 3px;margin-bottom:14px}
.sec-head h2{margin:0;font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:24px;letter-spacing:.02em;
  text-transform:uppercase;color:var(--ink)}
.sec-head span{font-family:"Old Standard TT",Georgia,serif;font-style:italic;font-size:13px;color:var(--ink-faint)}
.cols{display:grid;grid-template-columns:2fr 1fr 1fr;align-items:start}
.cols.nolead{grid-template-columns:1fr 1fr}
.rail{padding:0 16px;border-left:1px solid var(--rule-soft);min-height:100%}
.cols > .rail:first-child{border-left:0;padding-left:0}
.cols > .rail:last-child{padding-right:0}
.rail article.story + article.story{border-top:1px solid var(--rule-soft);padding-top:12px;margin-top:2px}
article.story{padding:0 0 12px}
.story figure{margin:0 0 8px;border:1px solid var(--rule-soft);background:var(--paper-deep)}
.story img{display:block;width:100%;aspect-ratio:16/9;object-fit:cover;filter:grayscale(1) contrast(1.08) brightness(.97)}
.story h3{margin:0 0 6px;font-family:"Playfair Display",Georgia,serif;font-weight:700;font-size:19px;line-height:1.18;color:var(--ink)}
article.lead h3{font-size:27px;font-weight:900;line-height:1.12}
.story h3 a{text-decoration:none}
.story h3 a:hover{text-decoration:underline;text-decoration-thickness:1px}
.byline{font-family:"Old Standard TT",Georgia,serif;font-size:11.5px;letter-spacing:.09em;text-transform:uppercase;color:var(--ink-faint);margin:0 0 5px}
.story p.sum{margin:0 0 7px;text-align:justify;hyphens:auto;color:var(--ink)}
article.lead p.sum{font-size:16.5px}
article.lead p.sum::first-letter{float:left;font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:3.1em;line-height:.85;padding:4px 6px 0 0;color:var(--ink)}
.more{font-family:"Old Standard TT",Georgia,serif;font-style:italic;font-size:14px;color:var(--link);text-decoration:none;border-bottom:1px solid var(--rule-soft)}
.more:hover{color:var(--ink);border-bottom-color:var(--ink)}
/* Briefs: compact items after the featured stories */
.briefs-head{font-family:"Old Standard TT",Georgia,serif;font-size:12px;letter-spacing:.12em;text-transform:uppercase;
  color:var(--ink-soft);text-align:center;border-top:1px solid var(--rule);border-bottom:1px solid var(--rule-soft);
  padding:4px 0 3px;margin:4px 0 12px}
.briefs{column-count:3;column-gap:30px;column-rule:1px solid var(--rule-soft)}
.briefs article.brief{break-inside:avoid;padding:0 0 10px;margin:0 0 10px;border-bottom:1px dotted var(--rule-soft)}
.brief h3{margin:0 0 3px;font-family:"Playfair Display",Georgia,serif;font-weight:700;font-size:16px;line-height:1.2;color:var(--ink)}
.brief h3 a{text-decoration:none}
.brief h3 a:hover{text-decoration:underline;text-decoration-thickness:1px}
.brief .byline{margin:0 0 3px;font-size:10.5px}
.brief p.sum{margin:0 0 4px;font-size:14px;line-height:1.45;text-align:justify;hyphens:auto;color:var(--ink)}
.brief .more{font-size:13px}
footer{border-top:4px double var(--rule);padding-top:8px;text-align:center;font-family:"Old Standard TT",Georgia,serif;
  font-size:12.5px;font-style:italic;color:var(--ink-faint)}
@media (max-width:1050px){
  .cols{grid-template-columns:1fr 1fr}
  .cols > .rail.leadrail{grid-column:1 / -1;padding:0 0 12px;border-bottom:1px solid var(--rule-soft);margin-bottom:12px}
  .cols > .rail.leadrail + .rail{border-left:0;padding-left:0}
}
@media (max-width:1050px){.briefs{column-count:2}}
@media (max-width:640px){
  .briefs{column-count:1}
  .sheet{padding:14px 14px 30px}
  .ears .ear{display:none}
  .dateline{justify-content:center;font-size:11.5px}
  nav.sections{gap:6px 0}
  nav.sections a{font-size:12px;padding:3px 9px}
  .cols,.cols.nolead{grid-template-columns:1fr}
  .rail,.cols > .rail.leadrail + .rail{border-left:0;padding:0}
  .rail + .rail{border-top:1px solid var(--rule-soft);padding-top:12px}
  article.lead h3{font-size:24px}
}
"""

KICKER_CSS = r"""
.kicker{margin:0 0 3px;font-family:"Old Standard TT",Georgia,serif;font-size:10.5px;letter-spacing:.16em;text-transform:uppercase;color:#7a2e12}
"""

BANNER_CSS = r"""
.satire-banner{margin:0 0 18px;padding:14px 16px 13px;border:3px solid #7a2e12;background:#f7e6c8;color:var(--ink);
  box-shadow:inset 0 0 0 1px #e8dbbb}
.satire-banner .sb-kicker{margin:0 0 4px;font-family:"Old Standard TT",Georgia,serif;font-size:11px;letter-spacing:.22em;
  text-transform:uppercase;color:#7a2e12;font-weight:700}
.satire-banner h2{margin:0 0 6px;font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:22px;line-height:1.15;color:#7a2e12;
  letter-spacing:.04em;text-transform:uppercase}
.satire-banner p{margin:0;font-family:"Old Standard TT",Georgia,serif;font-size:15px;line-height:1.45;color:var(--ink)}
.inspired{margin:4px 0 6px;font-family:"Old Standard TT",Georgia,serif;font-size:12px;font-style:italic;color:var(--ink-faint);line-height:1.35}
.inspired a{color:var(--link)}
.brief .inspired{font-size:11px;margin:2px 0 4px}
@media (max-width:640px){.satire-banner{padding:12px 12px 11px}.satire-banner h2{font-size:18px}}
"""


def _byline(s):
    """Display byline: optional story source, else hostname map."""
    return s.get("source") or src(s["url"])

def _more(s):
    """Read-more label. Satire stories can set more_label so we never imply a real report."""
    if s.get("more_label"):
        return esc(s["more_label"])
    return f'Read more at {esc(_byline(s))} &rarr;'

def _inspired(s):
    """Optional tiny 'Inspired by' link for satire spun from a real report."""
    u = (s.get("inspired_url") or "").strip()
    if not u:
        return ""
    label = esc(s.get("inspired_by") or "a real report")
    return (f'<p class="inspired">Inspired by <a href="{esc(u)}" target="_blank" rel="noopener">{label}</a> '
            f'(real report). This card is still satire.</p>')

def story_html(s, lead, cls, fallbacks):
    img = s.get("image") or ""
    fig = ""
    if img:
        fb = fallbacks.get(s["url"], "")
        onerr = (f"this.onerror=function(){{this.parentNode.remove()}};this.src='{fb}'" if fb and not img.startswith("data:")
                 else "this.parentNode.remove()")
        fig = (f'<figure><img src="{esc(img)}" alt="{esc(s["headline"])}" loading="lazy" '
               f'referrerpolicy="no-referrer" onerror="{esc(onerr)}"></figure>')
    u = esc(s["url"])
    kick = f'<p class="kicker">{esc(s["kicker"])}</p>' if s.get("kicker") else ""
    # Same-page satire anchors stay in-tab; real reports still open in a new tab.
    tgt = '' if u.startswith('#') else ' target="_blank" rel="noopener"'
    return (f'<article class="story{" lead" if lead else ""}">{fig}{kick}'
            f'<h3><a href="{u}"{tgt}>{esc(s["headline"])}</a></h3>'
            f'<p class="byline">{esc(_byline(s))}</p>'
            f'<p class="sum">{esc(s["summary"])}</p>'
            f'{_inspired(s)}'
            f'<a class="more" href="{u}"{tgt}>{_more(s)}</a></article>')

def brief_html(s):
    u = esc(s["url"])
    kick = f'<p class="kicker">{esc(s["kicker"])}</p>' if s.get("kicker") else ""
    tgt = '' if u.startswith('#') else ' target="_blank" rel="noopener"'
    return (f'<article class="brief">{kick}<h3><a href="{u}"{tgt}>{esc(s["headline"])}</a></h3>'
            f'<p class="byline">{esc(_byline(s))}</p><p class="sum">{esc(s["summary"])}</p>'
            f'{_inspired(s)}'
            f'<a class="more" href="{u}"{tgt}>{_more(s)}</a></article>')

DEFAULTS = {
    "title": "Yes Bro Newspaper", "masthead": "Yes Bro Newspaper", "family": "",
    "motto": "All the news worth your morning chai",
    "ear_left": "India and the World<br>in One Sitting", "ear_right": "Printed This Morning<br>Read at Your Own Pace",
    "edition": "Morning Edition", "price": "Price: Free, unlike your opinions",
    "footer": "Printed for SCMK G. Every headline links to the original report, which opens in a new tab.",
    "head_extra": "", "ad_html": "", "ad_after": 0,
    # Ad anchor and menu entry. Default is the FIELDWORK house ad. Healing overrides these (ad_id, ad_menu, ad_menu_note)
    # and sets no_earth5r, which drops the Earth5R footer credit and JSON-LD parent and fails the build on any
    # FIELDWORK or Earth5R mention. ad2_html / ad2_after place an optional second, smaller ad.
    "ad_id": "fieldwork", "ad_menu": "Fieldwork", "ad_menu_note": "Earth5R", "ad2_html": "", "ad2_after": 0, "no_earth5r": False,
    # SEO and Yes Bro Explains (all optional): key (columns.py edition key), url (canonical), seo_title, seo_desc
    "key": "", "url": "", "seo_title": "", "seo_desc": "",
}

SITE = "https://yesbrohq.com"
CREDIT = '<p class="credit"><a href="https://earth5r.org/">A product of Earth5R</a></p>'
CREDIT_CSS = "footer .credit{margin:6px 0 0;font-style:normal;letter-spacing:.04em}footer .credit a{color:var(--ink-soft)}"

def _iso(date):
    import datetime as _dt
    try:
        return _dt.datetime.strptime(date, "%A %d %B %Y").date().isoformat()
    except ValueError:
        return _dt.date.today().isoformat()

def seo_head(c, date, secs):
    """Canonical, description, Open Graph, Twitter card and CollectionPage/ItemList JSON-LD for a paper.
    No JobPosting markup: the jobs are third party listings we do not host."""
    if not c.get("url"):
        return ""
    title = c["seo_title"] or c["title"]
    desc = c["seo_desc"] or c["motto"]
    import share
    img = share.og_image(c.get("key"))
    iso = _iso(date)
    items, pos = [], 0
    for n, ss in secs:
        for st in ss[:3]:
            pos += 1
            items.append({"@type": "ListItem", "position": pos, "url": st["url"], "name": st["headline"]})
    ld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": title, "url": c["url"], "description": desc,
          "inLanguage": "en", "dateModified": iso, "isAccessibleForFree": True,
          "isPartOf": {"@type": "WebSite", "name": "Yes Bro", "url": SITE + "/"},
          "publisher": {"@type": "Organization", "name": "Yes Bro", "url": SITE + "/",
                        "logo": {"@type": "ImageObject", "url": SITE + "/icon-512.png"},
                        "parentOrganization": {"@type": "Organization", "name": "Earth5R", "url": "https://earth5r.org/"}},
          "image": img,
          "mainEntity": {"@type": "ItemList", "name": f'{c["title"]} top stories, {date}', "itemListElement": items}}
    if c.get("no_earth5r"):
        ld["publisher"].pop("parentOrganization", None)
    return f"""
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{c["url"]}">
<meta name="robots" content="index,follow,max-image-preview:large">
<meta property="og:type" content="website"><meta property="og:site_name" content="Yes Bro">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{c["url"]}"><meta property="og:image" content="{img}"><meta property="og:image:width" content="800"><meta property="og:image:height" content="450"><meta property="og:image:alt" content="{esc(c["title"])}">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(desc)}"><meta name="twitter:image" content="{img}">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>"""

AD_CSS = r"""
.housead{max-width:760px;margin:6px auto 30px;border:3px double var(--rule);padding:14px 22px 16px;text-align:center;
  background:rgba(232,219,187,.55);outline:1px solid var(--rule-soft);outline-offset:4px}
.housead .ad-kicker{font-family:"Old Standard TT",Georgia,serif;font-size:11px;letter-spacing:.24em;text-transform:uppercase;color:var(--ink-faint);margin:0 0 4px}
.housead .ad-brand{font-family:"Playfair Display",Georgia,serif;font-weight:900;letter-spacing:.01em;font-size:38px;line-height:1.05;margin:0 0 4px;color:var(--ink)}
.housead h4{margin:0 0 6px;font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:22px;line-height:1.2;color:var(--ink)}
.housead p{margin:0 0 8px;font-size:15px;line-height:1.45;color:var(--ink-soft)}
.housead a.ad-cta{display:inline-block;font-family:"Old Standard TT",Georgia,serif;font-weight:700;font-size:13px;letter-spacing:.14em;
  text-transform:uppercase;color:var(--ink);text-decoration:none;border:1px solid var(--rule);padding:5px 16px}
.housead a.ad-cta:hover{background:rgba(90,70,40,.1)}
.family{font-family:"Old Standard TT",Georgia,serif;font-size:11.5px;letter-spacing:.22em;text-transform:uppercase;color:var(--ink-faint);margin:2px 0 0}
"""

JOBS_CSS = r"""
.jobsad{max-width:900px;margin:0 auto 16px;border:1px solid var(--rule);border-left:6px solid var(--rule);padding:9px 16px;
  background:rgba(232,219,187,.55);font-size:14px;line-height:1.45;color:var(--ink-soft)}
.jobsad b{font-family:"Old Standard TT",Georgia,serif;letter-spacing:.16em;text-transform:uppercase;color:var(--ink)}
.jobsad a{color:var(--link);font-style:italic}
.jobs-intro{font-family:"Old Standard TT",Georgia,serif;font-style:italic;font-size:13px;color:var(--ink-faint);text-align:center;margin:0 0 10px}
.jobgroup{margin:0 0 14px}
.jobgroup h4{margin:0 0 8px;font-family:"Old Standard TT",Georgia,serif;font-size:12.5px;letter-spacing:.2em;text-transform:uppercase;
  text-align:center;color:var(--ink);border-top:1px solid var(--rule);border-bottom:1px solid var(--rule-soft);padding:3px 0 2px}
.classifieds{column-count:3;column-gap:26px;column-rule:1px solid var(--rule-soft)}
.classified{break-inside:avoid;font-family:"Libre Caslon Text",Georgia,serif;font-size:13px;line-height:1.38;padding:0 0 7px;margin:0 0 7px;
  border-bottom:1px dotted var(--rule-soft)}
.classified .jt{font-weight:700;color:var(--ink);text-decoration:none}
.classified .jt:hover{text-decoration:underline}
.classified .jm{display:block;color:var(--ink-soft)}
.classified .jd{display:block;font-style:italic;color:var(--ink-faint);font-size:12px}
.classified .tag{font-family:"Old Standard TT",Georgia,serif;font-size:10px;letter-spacing:.12em;text-transform:uppercase;border:1px solid var(--rule-soft);
  padding:0 4px;margin-right:4px;color:var(--ink-soft);vertical-align:1px}
.classified .new{font-family:"Old Standard TT",Georgia,serif;font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:#7a2e12;margin-left:4px}
.classified .apply{font-family:"Old Standard TT",Georgia,serif;font-size:12px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;
  color:var(--link);text-decoration:none;border-bottom:1px solid var(--rule-soft)}
.classified .via{font-size:11px;color:var(--ink-faint)}
@media (max-width:1050px){.classifieds{column-count:2}}
@media (max-width:640px){.classifieds{column-count:1}.jobsad{font-size:13.5px}}
"""

def _d(iso):
    import datetime as _dt
    d = _dt.date.fromisoformat(iso)
    return f"{d.day} {d.strftime('%b')} {d.year}"

def job_html(j, mark_new=True):
    u = esc(j["url"])
    tag = f'<span class="tag">{esc(j["tag"])}</span>' if j.get("tag") else ""
    new = '<span class="new">New</span>' if mark_new and j.get("new") else ""
    bits = []
    if j.get("posted"): bits.append("Posted " + _d(j["posted"]))
    if j.get("deadline"): bits.append("Apply by " + _d(j["deadline"]))
    if j.get("note"): bits.append(j["note"])
    d = f'<span class="jd">{esc(", ".join(bits))}</span>' if bits else ""
    loc = j.get("location") or ("Remote" if j.get("region") == "Remote" else "")
    meta = esc(j["org"]) + (f" &middot; {esc(loc)}" if loc else "")
    return (f'<div class="classified">{tag}<a class="jt" href="{u}" target="_blank" rel="noopener">{esc(j["title"])}</a>{new}'
            f'<span class="jm">{meta}</span>{d}'
            f'<a class="apply" href="{u}" target="_blank" rel="noopener">Apply</a> <span class="via">via {esc(j.get("source", ""))}</span></div>')

def jobs_section(jobs, c):
    groups = []
    mark = not all(j.get("new") for j in jobs["jobs"])  # first run: everything is new, so mark nothing
    labels = {"India": "India", "Global": "Global", "Remote": c.get("jobs_remote_label", "Remote")}
    for reg in ("India", "Global", "Remote"):
        js = [j for j in jobs["jobs"] if j["region"] == reg]
        if js:
            groups.append(f'<div class="jobgroup"><h4>{labels[reg]}</h4><div class="classifieds">' + "".join(job_html(j, mark) for j in js) + "</div></div>")
    n = len(jobs["jobs"])
    return (c.get("jobs_ad_html", "")
            + f'<section class="sec" id="jobs"><div class="sec-head"><h2>Jobs</h2><span>Checked this morning</span></div>'
            + f'<p class="jobs-intro">{c.get("jobs_intro", "Open roles checked today. Every listing links to the original posting.")}</p>'
            + "".join(groups) + "</section>")


# ---- Events and Conferences (all papers, from events.py) and Opportunities (Business, from opps.py).
EV_CSS = r"""
.ev-intro{font-family:"Old Standard TT",Georgia,serif;font-style:italic;font-size:13px;color:var(--ink-faint);text-align:center;margin:0 0 10px}
.classified .ed{display:block;font-family:"Old Standard TT",Georgia,serif;font-size:11.5px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--ink)}
.classified .jl{display:block;color:var(--ink);font-size:13px}
.opps-top{border:3px double var(--rule);padding:10px 14px 4px;margin:0 0 22px;background:rgba(232,219,187,.35)}
.opps-top > .sec-head{margin-top:0}
"""

def _range(a, b):
    import datetime as _dt
    x, y = _dt.date.fromisoformat(a), _dt.date.fromisoformat(b or a)
    if x == y: return f"{x.strftime('%a')} {x.day} {x.strftime('%b')} {x.year}"
    if x.month == y.month: return f"{x.day} to {y.day} {y.strftime('%b')} {y.year}"
    return f"{x.day} {x.strftime('%b')} to {y.day} {y.strftime('%b')} {y.year}"

def event_html(e):
    u = esc(e["url"])
    when = _range(e["start"], e.get("end")) + (f', {e["time"]}' if e.get("time") else "")
    where = e.get("city") or ""
    mode = e.get("mode") or ""
    meta = esc(where) + (f" &middot; {esc(mode)}" if mode and mode != where else "")
    lab = "Event page on Luma" if e.get("source") == "Luma" else ("Details" if e.get("source") == "confs.tech" else "Official page")
    return (f'<div class="classified"><span class="ed">{esc(when)}</span><a class="jt" href="{u}" target="_blank" rel="noopener">{esc(e["name"])}</a>'
            f'<span class="jm">{meta}</span><span class="jd">{esc(e.get("line", ""))}</span>'
            f'<a class="apply" href="{u}" target="_blank" rel="noopener">{lab}</a></div>')

def events_section(ev, c):
    es = ev.get("events") or []
    groups = []
    for reg, label in (("India", "India"), ("World", "Worldwide"), ("Online", "Online")):
        xs = [e for e in es if e.get("region", "World") == reg]
        if xs:
            groups.append(f'<div class="jobgroup"><h4>{label}</h4><div class="classifieds">' + "".join(event_html(e) for e in xs) + "</div></div>")
    n = len(es)
    intro = c.get("events_intro") or DEFAULT_EVENTS_INTRO
    return (f'<section class="sec" id="events"><div class="sec-head"><h2>Events and Conferences</h2><span>Coming up</span></div>'
            f'<p class="ev-intro">{intro}</p>' + "".join(groups) + "</section>")

DEFAULT_EVENTS_INTRO = ("Conferences and meetups coming up, each checked against its own page this morning. "
                        "Dates do move, so click before you book the train.")

def opp_html(x):
    u = esc(x["url"])
    if x.get("kind") == "Funding":
        dl = ("Apply by " + _d(x["deadline"])) if x.get("deadline") else ("Rolling applications" if x.get("rolling") else "")
        meta = esc(x.get("org", "")) + (f' &middot; {esc(x["where"])}' if x.get("where") else "")
        return (f'<div class="classified"><span class="ed">{esc(dl)}</span><a class="jt" href="{u}" target="_blank" rel="noopener">{esc(x["title"])}</a>'
                f'<span class="jm">{meta}</span><span class="jd">{esc(x.get("line", ""))}</span>'
                f'<a class="apply" href="{u}" target="_blank" rel="noopener">Official page</a></div>')
    tag = f'<span class="tag">{esc(x.get("kind", ""))}</span>'
    return (f'<div class="classified">{tag}<a class="jt" href="{u}" target="_blank" rel="noopener">{esc(x["title"])}</a>'
            f'<span class="jm">{esc(x.get("source") or x.get("org", ""))} &middot; {esc(_d(x["date"]))}</span>'
            f'<a class="apply" href="{u}" target="_blank" rel="noopener">Read</a></div>')

def tenders_section(op, c):
    ts, rs = op.get("tenders") or [], op.get("releases") or []
    groups = []
    if ts: groups.append('<div class="jobgroup"><h4>Tenders and bids</h4><div class="classifieds">' + "".join(opp_html(x) for x in ts) + "</div></div>")
    if rs: groups.append('<div class="jobgroup"><h4>Government releases</h4><div class="classifieds">' + "".join(opp_html(x) for x in rs) + "</div></div>")
    intro = c.get("tenders_intro", "Bid invitations and official releases from the past few days, each linked to the report or the release itself. "
                  "Read the actual tender document before you quote. The government certainly will.")
    return (f'<section class="sec" id="tenders"><div class="sec-head"><h2>Government Tenders and Releases</h2><span>This week</span></div>'
            f'<p class="ev-intro">{intro}</p>' + "".join(groups) + "</section>")

def funding_section(op, c):
    fs = op.get("funding") or []
    intro = c.get("funding_intro", "Calls for applications that are open today, re-checked on the official page every morning. "
                  "Extensions remain a rumour until someone announces one.")
    return (f'<section class="sec" id="funding"><div class="sec-head"><h2>Funding Opportunities</h2><span>Still open</span></div>'
            f'<p class="ev-intro">{intro}</p><div class="classifieds">' + "".join(opp_html(x) for x in fs) + "</div></section>")


# ---- Schools halves, Student Opportunities, FIELDWORK blog
HALF_CSS = r"""
.half-banner{margin:26px 0 18px;padding:16px 14px 14px;border-top:3px solid var(--rule);border-bottom:3px solid var(--rule);
  background:linear-gradient(to bottom,#e4d7b4 0%,#f3ead6 55%,#efe4c8 100%);text-align:center;box-shadow:inset 0 1px 0 #f7efd8,inset 0 -1px 0 #d9c89a}
.half-banner.first{margin-top:6px}
.half-banner h2{margin:0;font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:26px;letter-spacing:.06em;text-transform:uppercase;color:var(--ink);line-height:1.15}
.half-banner p{margin:6px 0 0;font-family:"Old Standard TT",Georgia,serif;font-style:italic;font-size:14px;color:var(--ink-soft)}
@media (max-width:640px){.half-banner h2{font-size:22px}.half-banner{padding:14px 10px 12px}}
.stu-opp{border:1px solid var(--rule-soft);padding:10px 14px 4px;margin:0 0 22px;background:rgba(243,234,214,.5)}
.stu-opp > .sec-head h2{font-size:22px}
.fw-blog{margin:8px 0 22px;padding:14px 14px 8px;border-top:3px solid #5c4330;border-bottom:3px solid #5c4330;
  background:linear-gradient(to bottom,#d9c7a0 0%,#cbb892 45%,#c4b087 100%);box-shadow:inset 0 1px 0 #e6d7b4,inset 0 -1px 0 #b39d72}
.fw-blog .sec-head h2{color:#2a1c12}
.fw-blog .sec-head span,.fw-blog .ev-intro{color:#4a3826}
.fw-blog .fw-item{break-inside:avoid;padding:0 0 10px;margin:0 0 10px;border-bottom:1px dotted #8a7352}
.fw-blog .fw-item h3{margin:0 0 3px;font-family:"Libre Caslon Text",Georgia,serif;font-size:15px;line-height:1.25}
.fw-blog .fw-item h3 a{color:#2a1c12;text-decoration:none}
.fw-blog .fw-item h3 a:hover{text-decoration:underline}
.fw-blog .fw-sum{margin:0;font-size:13.5px;line-height:1.4;color:#3d2e1f}
.fw-blog .fw-meta{display:block;font-size:11.5px;color:#5c4a34;margin:0 0 4px;letter-spacing:.04em;text-transform:uppercase;font-family:"Old Standard TT",Georgia,serif}
.menu-list .m-half{margin:10px 12px 4px;padding:6px 0 2px;border-top:2px solid var(--rule);font-family:"Playfair Display",Georgia,serif;font-weight:700;font-size:13px;letter-spacing:.08em;text-transform:uppercase;color:var(--ink);list-style:none}
.menu-list .m-half:first-child{border-top:0;margin-top:4px}
"""

def half_banner_html(h, first=False):
    title = esc(h.get("title") or "")
    note = esc(h.get("note") or "")
    hid = esc(h.get("id") or slug(title))
    return (f'<section class="half-banner{" first" if first else ""}" id="half-{hid}">'
            f'<h2>{title}</h2>' + (f'<p>{note}</p>' if note else "") + "</section>")

def student_opps_section(data, c):
    items = (data or {}).get("items") or []
    if not items: return ""
    blk = c.get("student_opps_block") or {}
    title = blk.get("title") or "Student Opportunities"
    intro = blk.get("intro") or "Competitions, olympiads, contests and scholarships still open, each checked on its official page this morning."
    cards = []
    for it in items:
        u = esc(it["url"])
        dl = ("Apply by " + _d(it["deadline"])) if it.get("deadline") else "Deadline on the official page"
        meta = esc(it.get("org") or "")
        loc = it.get("location") or it.get("region") or ""
        if loc: meta = meta + (f" &middot; {esc(loc)}" if meta else esc(loc))
        cards.append(f'<div class="classified"><span class="ed">{esc(dl)}</span>'
                     f'<a class="jt" href="{u}" target="_blank" rel="noopener">{esc(it["title"])}</a>'
                     f'<span class="jm">{meta}</span><span class="jd">{esc(it.get("line") or "")}</span>'
                     f'<a class="apply" href="{u}" target="_blank" rel="noopener">Official page</a></div>')
    return (f'<section class="sec stu-opp" id="student_opps"><div class="sec-head"><h2>{esc(title)}</h2><span>Still open</span></div>'
            f'<p class="ev-intro">{esc(intro)}</p><div class="classifieds">' + "".join(cards) + "</div></section>")

def fieldwork_blog_section(data, c):
    items = (data or {}).get("items") or []
    if not items: return ""
    blk = c.get("fieldwork_blog_block") or {}
    title = blk.get("title") or "From the FIELDWORK Blog"
    intro = blk.get("intro") or "Notes from Earth5R on university applications, profile building and live projects for school students."
    cards = []
    for it in items:
        cards.append(f'<article class="fw-item"><h3><a href="{esc(it["url"])}" target="_blank" rel="noopener">{esc(it["title"])}</a></h3>'
                     f'<span class="fw-meta">{esc(it.get("source") or "Earth5R")}</span>'
                     f'<p class="fw-sum">{esc(it.get("summary") or "")}</p></article>')
    return (f'<section class="sec fw-blog" id="fieldwork_blog"><div class="sec-head"><h2>{esc(title)}</h2><span>From Earth5R</span></div>'
            f'<p class="ev-intro">{esc(intro)}</p><div class="rd-grid">' + "".join(cards) + "</div></section>")


# ---- All Yes Bro papers pills (top and bottom) and the Add to home screen note (every paper and the landing page).
PILL_CSS = r"""
.sheet{position:relative}
.allpapers{position:absolute;top:14px;right:14px;display:inline-flex;align-items:center;gap:6px;min-height:40px;padding:0 14px;border:1.5px solid var(--rule);
  border-radius:999px;background:#f3ead6;color:var(--ink);text-decoration:none;font-family:"Old Standard TT",Georgia,serif;font-size:12px;font-weight:700;
  letter-spacing:.12em;text-transform:uppercase;box-shadow:0 2px 0 var(--rule-soft)}
.allpapers:hover,.allpapers:focus-visible{background:#e8dbbb;outline:none}
.allpapers-bottom{text-align:center;margin:26px 0 14px}
.allpapers-bottom a{display:inline-block;padding:10px 20px;border:2px solid var(--rule);border-radius:999px;background:#f3ead6;color:var(--ink);text-decoration:none;
  font-family:"Old Standard TT",Georgia,serif;font-size:13px;font-weight:700;letter-spacing:.12em;text-transform:uppercase}
.allpapers-bottom a span{display:block;margin-top:2px;font-weight:400;font-style:italic;letter-spacing:.02em;text-transform:none;color:var(--ink-faint);font-size:12.5px}
.allpapers-bottom a:hover{background:#e8dbbb}
@media (max-width:640px){.allpapers{top:16px;right:12px;min-height:40px;padding:0 12px;font-size:11px;letter-spacing:.08em}}
.paper-pills{position:absolute;top:14px;right:14px;display:flex;gap:6px;flex-wrap:wrap;justify-content:flex-end;max-width:70%}
.paper-pills .allpapers{position:static}
.mypaper-pill{display:inline-flex;align-items:center;gap:6px;min-height:40px;padding:0 14px;border:1.5px solid var(--rule);
  border-radius:999px;background:#2e2a24;color:#f3ead6;text-decoration:none;font-family:"Old Standard TT",Georgia,serif;font-size:12px;font-weight:700;
  letter-spacing:.12em;text-transform:uppercase;box-shadow:0 2px 0 var(--rule-soft)}
.mypaper-pill:hover,.mypaper-pill:focus-visible{background:#4a4238;outline:none}
@media (max-width:640px){.paper-pills{top:12px;right:10px;max-width:78%}.mypaper-pill{min-height:36px;padding:0 10px;font-size:10.5px;letter-spacing:.06em}}

"""
A2HS_CSS = r"""
.a2hs{max-width:100%;margin:10px 0 14px;border:1px solid var(--rule);border-left:4px solid #6b4a2e;background:#e4d4b4;font-size:14px;line-height:1.45;color:var(--ink-soft);
  box-shadow:inset 0 1px 0 rgba(255,255,255,.35)}
.a2hs summary{cursor:pointer;list-style:none;padding:10px 14px;font-family:"Old Standard TT",Georgia,serif;font-weight:700;font-size:12.5px;letter-spacing:.1em;
  text-transform:uppercase;color:var(--ink);display:flex;align-items:center;gap:10px}
.a2hs summary::-webkit-details-marker{display:none}
.a2hs summary .a2hs-label{flex:1;text-align:left}
.a2hs summary .a2hs-toggle{font-size:18px;font-weight:400;line-height:1}
.a2hs[open] summary .a2hs-toggle{content:"\2212"}
.a2hs .a2hs-ico{flex:0 0 auto;display:block;width:22px;height:34px}
.a2hs .a2hs-body{padding:0 14px 12px}
.a2hs p{margin:0 0 8px;font-style:italic}
.a2hs ol{margin:0 0 8px;padding-left:20px}
.a2hs b.os{display:block;font-family:"Old Standard TT",Georgia,serif;font-size:11.5px;letter-spacing:.16em;text-transform:uppercase;color:var(--ink);margin:6px 0 2px}
.a2hs button{font-family:"Old Standard TT",Georgia,serif;font-weight:700;font-size:13px;letter-spacing:.12em;text-transform:uppercase;color:var(--ink);
  background:#f3ead6;border:2px solid var(--rule);padding:8px 16px;cursor:pointer;margin-top:4px}
@media (max-width:640px){.a2hs summary{font-size:11.5px;letter-spacing:.06em;padding:9px 12px;gap:8px}.a2hs .a2hs-ico{width:18px;height:28px}}
"""
A2HS_INTRO = "It sits on your phone like an app and has never once asked for an update."
A2HS_PHONE = ('<svg class="a2hs-ico" viewBox="0 0 28 44" width="22" height="34" aria-hidden="true" focusable="false">'
              '<rect x="2.5" y="1.5" width="23" height="41" rx="3.5" ry="3.5" fill="none" stroke="#6b4a2e" stroke-width="1.6"/>'
              '<line x1="9" y1="4.5" x2="19" y2="4.5" stroke="#6b4a2e" stroke-width="1.4" stroke-linecap="round"/>'
              '<circle cx="14" cy="38.5" r="1.6" fill="none" stroke="#6b4a2e" stroke-width="1.3"/></svg>')
def a2hs_html(intro=A2HS_INTRO):
    return ('<details class="a2hs" id="homescreen"><summary>' + A2HS_PHONE
            + '<span class="a2hs-label">Add Yes Bro to your phone as a web app</span>'
            + '<span class="a2hs-toggle" aria-hidden="true">+</span></summary><div class="a2hs-body">'
            f'<p>{intro}</p>'
            '<b class="os">iPhone</b><ol><li>Open this page in Safari.</li><li>Tap the Share button.</li><li>Tap &ldquo;Add to Home Screen&rdquo;, then Add.</li></ol>'
            '<b class="os">Android</b><ol><li>Open this page in Chrome.</li><li>Tap the three-dot menu.</li><li>Tap &ldquo;Add to Home screen&rdquo; or &ldquo;Install app&rdquo;.</li></ol>'
            '<button type="button" id="a2hs-install" hidden>Install Yes Bro</button></div></details>'
            '<script>(function(){var d,b=document.getElementById("a2hs-install"),t=document.querySelector("#homescreen");'
            'if(t){t.addEventListener("toggle",function(){var x=t.querySelector(".a2hs-toggle");if(x)x.textContent=t.open?"\\u2212":"+"});}'
            'window.addEventListener("beforeinstallprompt",function(e){e.preventDefault();d=e;b.hidden=false});'
            'b.addEventListener("click",function(){if(!d)return;d.prompt();d.userChoice.then(function(){d=null;b.hidden=true})});'
            'window.addEventListener("appinstalled",function(){b.hidden=true})})();</script>')

# ---- House voice check: no counting in our own copy (mottos, ears, intros, footers, ads, menus, home screen note).
# Flags spelled out or numeric counts of our own things, such as "thirteen papers" or "30 jobs". News copy is not checked.
COUNT_WORDS = r"(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|twenty|thirty|dozens?|hundreds?)"
COUNT_RE = re.compile(r"(?<!to )(?<!\d )\b" + COUNT_WORDS + r"\s+(?:[a-z]+\s+)?(?:papers?|editions?|sections?|stories|story|jobs?|listings?|openings?|roles?|events?|items?|columns?|cities|tenders?|calls?)\b", re.I)
def house_count_check(label, text):
    """Print a warning for every count found in house copy. Returns the list of hits."""
    plain = re.sub(r"<[^>]+>", " ", text or "")
    hits = [m.group(0) for m in COUNT_RE.finditer(plain)]
    for h in hits:
        print(f"HOUSE VOICE WARNING ({label}): count in house copy: {h!r}. Rewrite without counting.", file=sys.stderr)
    return hits
HOUSE_KEYS = ("motto", "ear_left", "ear_right", "edition", "price", "footer", "jobs_intro", "events_intro", "tenders_intro",
              "funding_intro", "research_intro", "talks_intro", "ad_html", "ad2_html", "jobs_ad_html", "pill_top", "pill_bottom", "a2hs_intro")

PWA_RE = re.compile(r'\s*<(meta name="(apple-mobile-web-app-[a-z-]+|mobile-web-app-capable|theme-color)"|link rel="(manifest|apple-touch-icon|icon)")[^>]*>')
def pwa_head(c):
    """Standard home screen tags for a paper folder (manifest.json is written by pwa.py next to index.html)."""
    name = c.get("masthead") or c.get("title") or "Yes Bro"
    return (f'\n<meta name="apple-mobile-web-app-capable" content="yes">\n<meta name="mobile-web-app-capable" content="yes">'
            f'\n<meta name="apple-mobile-web-app-title" content="{esc(name)}">\n<meta name="apple-mobile-web-app-status-bar-style" content="default">'
            f'\n<meta name="theme-color" content="#f3ead6">\n<link rel="manifest" href="manifest.json">'
            f'\n<link rel="apple-touch-icon" href="../icon-512.png">\n<link rel="icon" href="../icon-512.png">')

# Slide-out section menu (all papers). A fixed button at the top left opens a left side panel listing
# every section in order, with Jobs pinned at the top when the paper has one, and the FIELDWORK ad.
# Plain HTML, CSS and a few lines of vanilla JS. Closes with the X, a tap outside, Esc, or picking a link.
MENU_CSS = r"""
html{scroll-behavior:smooth}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
.sheet{padding-top:66px}
section.sec,.housead{scroll-margin-top:70px}
.menu-btn{position:fixed;top:12px;left:12px;z-index:60;display:inline-flex;align-items:center;gap:8px;min-height:46px;padding:0 14px 0 11px;
  background:#f3ead6;color:var(--ink);border:2px solid var(--rule);border-radius:3px;box-shadow:0 2px 0 var(--rule-soft),0 4px 14px rgba(70,50,20,.25);
  font-family:"Old Standard TT",Georgia,serif;font-size:13px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;cursor:pointer;
  -webkit-tap-highlight-color:transparent}
.menu-btn:hover,.menu-btn:focus-visible{background:#e8dbbb;outline:none}
.menu-btn svg{display:block;width:22px;height:22px}
.menu-scrim{position:fixed;inset:0;z-index:70;background:rgba(46,42,36,.42);opacity:0;visibility:hidden;transition:opacity .22s,visibility .22s}
.menu-panel{position:fixed;top:0;left:0;bottom:0;z-index:80;width:min(86vw,340px);display:flex;flex-direction:column;
  background-color:#f3ead6;background-image:radial-gradient(ellipse at 0% 0%,rgba(255,250,235,.6),transparent 60%);
  border-right:3px double var(--rule);box-shadow:6px 0 30px rgba(70,50,20,.35);transform:translateX(-105%);visibility:hidden;
  transition:transform .25s ease,visibility .25s;overscroll-behavior:contain}
body.menu-open .menu-panel{transform:none;visibility:visible}
body.menu-open .menu-scrim{opacity:1;visibility:visible}
@media (prefers-reduced-motion:reduce){.menu-panel,.menu-scrim{transition:none}}
.masthead{container-type:inline-size}.ybt{font-size:min(1em,calc((100cqw - 4px)/var(--w)))}.yb,.fw{display:inline-block}.fw{font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:1em;letter-spacing:0;margin-left:.1em;vertical-align:baseline}
.menu-head{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:12px 12px 8px 18px;border-bottom:4px double var(--rule)}
.menu-head .mh{margin:0;font-family:"UnifrakturMaguntia","Old English Text MT","Playfair Display",serif;font-weight:400;font-size:34px;line-height:1;color:var(--ink)}
.menu-head .mh small{display:block;margin-top:4px;font-family:"Old Standard TT",Georgia,serif;font-size:11px;letter-spacing:.2em;text-transform:uppercase;color:var(--ink-faint)}
.menu-close{flex:none;width:46px;height:46px;display:inline-flex;align-items:center;justify-content:center;background:transparent;
  border:2px solid var(--rule);border-radius:3px;color:var(--ink);cursor:pointer;-webkit-tap-highlight-color:transparent}
.menu-close:hover,.menu-close:focus-visible{background:#e8dbbb;outline:none}
.menu-close svg{width:20px;height:20px}
.menu-list{list-style:none;margin:0;padding:6px 0 24px;overflow-y:auto;-webkit-overflow-scrolling:touch;flex:1}
.menu-list li{margin:0}
.menu-list a{display:flex;align-items:baseline;justify-content:space-between;gap:12px;min-height:50px;padding:13px 18px;
  border-bottom:1px dotted var(--rule-soft);text-decoration:none;color:var(--ink);font-family:"Playfair Display",Georgia,serif;
  font-weight:700;font-size:17px;line-height:1.25}
.menu-list a span{flex:none;font-family:"Old Standard TT",Georgia,serif;font-weight:400;font-style:italic;font-size:12.5px;color:var(--ink-faint)}
.menu-list a:hover,.menu-list a:focus-visible{background:rgba(90,70,40,.1);outline:none}
.menu-list .m-jobs a{margin:8px 12px 6px;border:2px solid var(--rule);border-bottom:2px solid var(--rule);background:#e8dbbb;
  text-transform:uppercase;letter-spacing:.08em;font-size:18px;font-weight:900}
.menu-list .m-jobs a span{font-style:normal;text-transform:none;letter-spacing:0;color:var(--ink-soft)}
.menu-list .m-pin a{font-size:15px;letter-spacing:.05em;margin-top:2px}
.menu-list .m-label{padding:12px 18px 4px;font-family:"Old Standard TT",Georgia,serif;font-size:11px;letter-spacing:.22em;text-transform:uppercase;color:var(--ink-faint)}
.menu-list .m-ad a{font-family:"Playfair Display",Georgia,serif;font-weight:900;font-size:21px}
.masthead h1 a.homelink{color:inherit;text-decoration:none}
.menu-list .m-top a{font-family:"Old Standard TT",Georgia,serif;font-style:italic;font-weight:400;font-size:14px;color:var(--link)}
.menu-list .m-home a{font-style:normal;font-weight:700;font-size:15px;color:var(--ink);border-top:1px solid var(--rule-soft)}
html.menu-lock,html.menu-lock body{overflow:hidden}
@media (max-width:640px){.sheet{padding-top:68px}}
"""

MENU_ICON = ('<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round">'
             '<path d="M4 6.5h16M4 12h16M4 17.5h16"/></svg>')
CLOSE_ICON = ('<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round">'
              '<path d="M6 6l12 12M18 6L6 18"/></svg>')

HOME_URL = "https://yesbrohq.com/"  # the landing page, front door for every paper

MENU_JS = r"""<script>(function(){
var b=document.body,btn=document.getElementById('menu-btn'),p=document.getElementById('menu-panel'),
s=document.getElementById('menu-scrim'),x=document.getElementById('menu-close'),h=document.documentElement;
function open(){b.classList.add('menu-open');h.classList.add('menu-lock');btn.setAttribute('aria-expanded','true');p.setAttribute('aria-hidden','false');setTimeout(function(){x.focus()},60)}
function close(f){b.classList.remove('menu-open');h.classList.remove('menu-lock');btn.setAttribute('aria-expanded','false');p.setAttribute('aria-hidden','true');if(f)btn.focus()}
btn.addEventListener('click',function(){b.classList.contains('menu-open')?close(true):open()});
x.addEventListener('click',function(){close(true)});s.addEventListener('click',function(){close(false)});
document.addEventListener('keydown',function(e){if((e.key==='Escape'||e.key==='Esc')&&b.classList.contains('menu-open'))close(true)});
p.addEventListener('click',function(e){var a=e.target.closest('a[href^="#"]');if(!a)return;var id=a.getAttribute('href').slice(1),t=id?document.getElementById(id):null;
e.preventDefault();close(false);setTimeout(function(){if(t)t.scrollIntoView({behavior:'smooth',block:'start'});else window.scrollTo({top:0,behavior:'smooth'});
if(history.replaceState)history.replaceState(null,'','#'+id)},30)});
})();</script>"""

BACK_TOP_CSS = """
/* Back to top: fixed bottom-right, clears mobile share/foot chrome */
.back-top{position:fixed;right:16px;bottom:22px;z-index:55;width:44px;height:44px;border-radius:50%;
  border:2px solid var(--rule);background:#f3ead6;color:var(--ink);display:inline-flex;align-items:center;justify-content:center;
  box-shadow:0 2px 10px rgba(70,50,20,.25);opacity:0;visibility:hidden;pointer-events:none;transform:translateY(8px);
  transition:opacity .2s,visibility .2s,transform .2s,background .15s;cursor:pointer;padding:0}
.back-top.show{opacity:1;visibility:visible;pointer-events:auto;transform:none}
.back-top:hover,.back-top:focus-visible{background:#e8dbbb;outline:none}
.back-top svg{display:block;width:20px;height:20px}
@media (max-width:640px){.back-top{right:14px;bottom:78px}}
@media (prefers-reduced-motion:reduce){.back-top{transition:none}}
"""

BACK_TOP_BTN = """<a class="back-top" id="back-to-top" href="#top" aria-label="Back to top" title="Back to top"><svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19V5"/><path d="M5 12l7-7 7 7"/></svg></a>"""

BACK_TOP_JS = """
<script>
(function(){
  var b=document.getElementById('back-to-top'); if(!b) return;
  var reduce=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  function sync(){ if(window.scrollY>320) b.classList.add('show'); else b.classList.remove('show'); }
  window.addEventListener('scroll', sync, {passive:true}); sync();
  b.addEventListener('click', function(e){ e.preventDefault();
    if(reduce) window.scrollTo(0,0); else window.scrollTo({top:0,behavior:'smooth'});
  });
})();
</script>
"""

def menu_html(secs, has_jobs, n_jobs, has_ad, has_explains=False, pinned=None, ad=("fieldwork", "Fieldwork", "Earth5R"), share_url="", halves=None, jobs_in_menu=True):
    items = []
    for pid, plabel, pnote in (pinned or []):
        if pid == "jobs":
            if has_jobs and jobs_in_menu:
                items.append(f'<li class="m-jobs"><a href="#jobs">Jobs <span>Checked today</span></a></li>')
        else:
            items.append(f'<li class="m-jobs m-pin"><a href="#{pid}">{esc(plabel)} <span>{esc(pnote)}</span></a></li>')
    if pinned is None and has_jobs and jobs_in_menu:
        items.append(f'<li class="m-jobs"><a href="#jobs">Jobs <span>Checked today</span></a></li>')
    if has_explains:
        items.append('<li class="m-ex"><a href="#explains">Yes Bro Explains <span>Our column</span></a></li>')
    if halves:
        sec_map = {n: ss for n, ss in secs}
        pinned_ids = {pid for pid, _, _ in (pinned or [])}
        for h in halves:
            items.append(f'<li class="m-half">{esc(h.get("title") or "")}</li>')
            for b in h.get("blocks") or []:
                if b in pinned_ids or b == "jobs":
                    continue  # pins already listed at top; jobs stay out of Schools menu
                if b in sec_map:
                    items.append(f'<li><a href="#{slug(b)}">{esc(b)}</a></li>')
                elif b in ("events", "research", "talks", "skills", "student_opps", "fieldwork_blog", "tenders", "funding"):
                    # extras that are not pinned still listed under the half
                    label = {"events": "Events and Conferences", "research": "Research and Development", "talks": "Talks",
                             "skills": "Jobs vs Certifications", "student_opps": "Student Opportunities",
                             "fieldwork_blog": "From the FIELDWORK Blog", "tenders": "Tenders", "funding": "Funding"}.get(b, b)
                    items.append(f'<li><a href="#{b}">{esc(label)}</a></li>')
    else:
        items.append('<li class="m-label">Sections</li>')
        for n, ss in secs:
            items.append(f'<li><a href="#{slug(n)}">{esc(n)}</a></li>')
    if has_ad:
        items.append(f'<li class="m-ad"><a href="#{esc(ad[0])}">{esc(ad[1])} <span>{esc(ad[2])}</span></a></li>')
    if share_url:  # opens the share sheet or panel (share.py), never navigates
        items.append(f'<li class="m-top m-share"><a class="sh-open" href="{esc(share_url)}" role="button">Share this paper <span>WhatsApp and friends</span></a></li>')
    items.append('<li class="m-top"><a href="#top">Top of this paper</a></li>')
    items.append(f'<li class="m-top m-home"><a href="{HOME_URL}">Back to the front page <span>All Yes Bro papers</span></a></li>')
    return ('<button class="menu-btn" id="menu-btn" type="button" aria-controls="menu-panel" aria-expanded="false" aria-label="Open sections menu">'
            + MENU_ICON + 'Sections</button>'
            + '<div class="menu-scrim" id="menu-scrim"></div>'
            + '<nav class="menu-panel" id="menu-panel" aria-label="Sections" aria-hidden="true">'
            + f'<div class="menu-head"><p class="mh">Yes Bro<small>Jump to a section. Skipping is allowed.</small></p>'
            + '<button class="menu-close" id="menu-close" type="button" aria-label="Close menu">' + CLOSE_ICON + '</button></div>'
            + '<ul class="menu-list">' + "".join(items) + '</ul></nav>')


RD_CSS = r"""
.rd-intro,.tk-intro{font-family:"Old Standard TT",Georgia,serif;font-style:italic;font-size:13px;color:var(--ink-faint);text-align:center;margin:0 0 10px}
.rd-item{break-inside:avoid;padding:0 0 10px;margin:0 0 10px;border-bottom:1px dotted var(--rule-soft)}
.rd-item h3{margin:0 0 3px;font-family:"Libre Caslon Text",Georgia,serif;font-size:15px;line-height:1.25}
.rd-item h3 a{color:var(--ink);text-decoration:none}
.rd-item h3 a:hover{text-decoration:underline}
.rd-meta{display:block;font-size:11.5px;color:var(--ink-faint);margin:0 0 4px;letter-spacing:.04em;text-transform:uppercase;font-family:"Old Standard TT",Georgia,serif}
.rd-sum{margin:0;font-size:13.5px;line-height:1.4;color:var(--ink-soft)}
.rd-tag{display:inline-block;font-size:10px;letter-spacing:.12em;text-transform:uppercase;border:1px solid var(--rule-soft);padding:0 5px;margin-right:6px;color:#7a2e12}
.rd-grid{column-count:2;column-gap:26px;column-rule:1px solid var(--rule-soft)}
@media (max-width:700px){.rd-grid{column-count:1}}
.tk-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px 18px}
.tk-card{border:1px solid var(--rule-soft);background:rgba(232,219,187,.25);overflow:hidden}
.tk-card a.tk-thumb{display:block;background:#ddd;aspect-ratio:16/9;overflow:hidden}
.tk-card img{width:100%;height:100%;object-fit:cover;display:block;filter:grayscale(1)}
.tk-body{padding:8px 10px 10px}
.tk-card h3{margin:0 0 3px;font-family:"Libre Caslon Text",Georgia,serif;font-size:14px;line-height:1.25}
.tk-card h3 a{color:var(--ink);text-decoration:none}
.tk-card h3 a:hover{text-decoration:underline}
.tk-meta{display:block;font-size:11.5px;color:var(--ink-faint);margin:0 0 4px;font-family:"Old Standard TT",Georgia,serif}
.tk-note{margin:0;font-size:12.5px;line-height:1.35;color:var(--ink-soft)}
@media (max-width:900px){.tk-grid{grid-template-columns:1fr 1fr}}
@media (max-width:560px){.tk-grid{grid-template-columns:1fr}}
"""

def research_section(rd, c):
    items = (rd or {}).get("items") or []
    if not items: return ""
    sb = c.get("research_block") or {}
    title = sb.get("title", "Research and Development")
    intro = sb.get("intro", "Papers and lab notes that landed recently. Preprints say so on the card. Findings stay where the source put them.")
    rows = []
    for it in items:
        tag = '<span class="rd-tag">Preprint</span>' if it.get("kind") == "preprint" else ""
        meta = esc(it.get("source") or "") + (f' &middot; {esc(it["date"])}' if it.get("date") else "")
        rows.append(f'<article class="rd-item">{tag}<h3><a href="{esc(it["url"])}" target="_blank" rel="noopener">{esc(it["title"])}</a></h3>'
                    f'<span class="rd-meta">{meta}</span><p class="rd-sum">{esc(it["summary"])}</p></article>')
    return (f'<section class="sec" id="research"><div class="sec-head"><h2>{esc(title)}</h2><span>Fresh from the lab</span></div>'
            f'<p class="rd-intro">{esc(intro)}</p><div class="rd-grid">' + "".join(rows) + "</div></section>")

def talks_section(tk, c):
    items = (tk or {}).get("talks") or []
    if not items: return ""
    sb = c.get("talks_block") or {}
    title = sb.get("title", "Talks")
    intro = sb.get("intro", "Talks worth a quiet half hour. Each one was still up on YouTube this morning.")
    cards = []
    for it in items:
        thumb = ""
        if it.get("thumb"):
            thumb = (f'<a class="tk-thumb" href="{esc(it["url"])}" target="_blank" rel="noopener">'
                     f'<img src="{esc(it["thumb"])}" alt="" loading="lazy"></a>')
        elif it.get("id"):
            thumb = (f'<a class="tk-thumb" href="{esc(it["url"])}" target="_blank" rel="noopener">'
                     f'<img src="https://i.ytimg.com/vi/{esc(it["id"])}/hqdefault.jpg" alt="" loading="lazy"></a>')
        meta = esc(it.get("channel") or "")
        if it.get("duration"): meta += f' &middot; {esc(it["duration"])}'
        cards.append(f'<article class="tk-card">{thumb}<div class="tk-body">'
                     f'<h3><a href="{esc(it["url"])}" target="_blank" rel="noopener">{esc(it["title"])}</a></h3>'
                     f'<span class="tk-meta">{meta}</span><p class="tk-note">{esc(it.get("note") or "")}</p></div></article>')
    return (f'<section class="sec" id="talks"><div class="sec-head"><h2>{esc(title)}</h2><span>Worth a watch</span></div>'
            f'<p class="tk-intro">{esc(intro)}</p><div class="tk-grid">' + "".join(cards) + "</div></section>")

def build(stories, date, fallbacks, sections=None, cfg=None, jobs=None, events=None, opps=None, research=None, talks=None, student_opps=None, fieldwork_blog=None):
    c = dict(DEFAULTS); c.update(cfg or {})
    secs = [(n, [s for s in stories if s["section"] == n]) for n in (sections or SECTIONS)]
    secs = [(n, ss) for n, ss in secs if ss]
    box = ""
    if c.get("key"):
        try:
            import columns
            box = columns.box_html(c["key"], date)
        except Exception as e:  # a broken column file must never stop the morning paper
            print(f"columns: skipped ({e})", flush=True)
    news = {}
    for n, allss in secs:
        ss, briefs = allss[:FEATURED], allss[FEATURED:]
        # Lead story = first story with an image, in a double-width rail. The rest flow into two
        # ruled rails, each story going to the currently shorter rail (image stories count as taller).
        li = next((i for i, s in enumerate(ss) if s.get("image")), None)
        rest = ss if li is None else ss[:li] + ss[li + 1:]
        rails, h = [[], []], [0.0, 0.0]
        for s in rest:
            k = 0 if h[0] <= h[1] else 1
            rails[k].append(s); h[k] += (1.0 if s.get("image") else 0.0) + 0.9
        parts = []
        if li is not None:
            parts.append(f'<div class="rail leadrail">{story_html(ss[li], True, "", fallbacks)}</div>')
        for r in rails:
            if r:
                parts.append('<div class="rail">' + "".join(story_html(s, False, "", fallbacks) for s in r) + "</div>")
        news[n] = (f'<section class="sec" id="{slug(n)}"><div class="sec-head"><h2>{esc(n)}</h2>'
                   f'</div>'
                   f'<div class="cols{"" if li is not None else " nolead"}">{"".join(parts)}</div>'
                   + (f'<div class="briefs-head">More from {esc(n)}</div><div class="briefs">'
                      + "".join(brief_html(s) for s in briefs) + '</div>' if briefs else '')
                   + '</section>')
    # Schools: Student Opportunities is its own section, so strip Student-tagged rows from Jobs.
    if jobs and jobs.get("jobs") and (student_opps or c.get("student_opps_block") is not None):
        jobs = dict(jobs)
        jobs["jobs"] = [j for j in jobs["jobs"] if j.get("tag") != "Student"]
    has_jobs = bool(jobs and jobs.get("jobs"))
    has_ev = bool(events and events.get("events"))
    extra = {}; rd_css = ""
    if student_opps and student_opps.get("items"):
        _so = student_opps_section(student_opps, c)
        if _so:
            extra["student_opps"] = (_so, (c.get("student_opps_block") or {}).get("title", "Student Opportunities"), "Still open", (c.get("student_opps_block") or {}).get("nav", "Opportunities"))
    if fieldwork_blog and fieldwork_blog.get("items"):
        _fw = fieldwork_blog_section(fieldwork_blog, c)
        if _fw:
            extra["fieldwork_blog"] = (_fw, (c.get("fieldwork_blog_block") or {}).get("title", "From the FIELDWORK Blog"), "From Earth5R", (c.get("fieldwork_blog_block") or {}).get("nav", "FIELDWORK"))
    if has_jobs: extra["jobs"] = (jobs_section(jobs, c), "Jobs", "Checked today", "Jobs")
    sk_css = ""
    if has_jobs and c.get("skills_block"):  # Jobs vs Certifications (skills.py), read from today's postings. Never stops the build.
        try:
            import skills
            _sk = skills.html_block(jobs["jobs"], c)
            if _sk:
                extra["skills"] = (_sk, c["skills_block"].get("title", "Jobs vs Certifications"), "What postings ask for", c["skills_block"].get("nav", "Skills"))
                sk_css = skills.CSS
        except Exception as e:
            print(f"skills: skipped ({e})", flush=True)
    if has_ev: extra["events"] = (events_section(events, c), "Events and Conferences", "Coming up", "Events")
    rd_css = ""
    if research and research.get("items") and c.get("research_block") is not False:
        try:
            _rd = research_section(research, c)
            if _rd:
                extra["research"] = (_rd, (c.get("research_block") or {}).get("title", "Research and Development"), "Fresh from the lab", (c.get("research_block") or {}).get("nav", "R&D"))
                rd_css = RD_CSS
        except Exception as e:
            print(f"research: skipped ({e})", flush=True)
    if talks and talks.get("talks") and c.get("talks_block") is not False:
        try:
            _tk = talks_section(talks, c)
            if _tk:
                extra["talks"] = (_tk, (c.get("talks_block") or {}).get("title", "Talks"), "Worth a watch", (c.get("talks_block") or {}).get("nav", "Talks"))
                rd_css = RD_CSS if not rd_css else rd_css  # already includes talks CSS
                if "RD_CSS" not in dir() and False: pass
                rd_css = RD_CSS
        except Exception as e:
            print(f"talks: skipped ({e})", flush=True)
    if opps and (opps.get("tenders") or opps.get("releases")):
        extra["tenders"] = (tenders_section(opps, c), "Tenders and Releases", "This week", "Tenders")
    if opps and opps.get("funding"):
        extra["funding"] = (funding_section(opps, c), "Funding Opportunities", "Still open", "Funding")
    # Block order: halves (Schools) or top_blocks, then remaining news, then extras, then bottom_blocks (Jobs last on Schools).
    halves = c.get("halves") or []
    if halves:
        order = []
        for h in halves:
            for b in h.get("blocks") or []:
                if (b in news or b in extra) and b not in order:
                    order.append(b)
        order += [n for n, _ in secs if n not in order]
        order += [k for k in ("skills", "events", "research", "talks", "tenders", "funding", "student_opps", "fieldwork_blog") if k in extra and k not in order]
        for b in c.get("bottom_blocks") or ["jobs"]:
            if b in extra and b not in order:
                order.append(b)
    else:
        order = [b for b in c.get("top_blocks", []) if b in news or b in extra]
        order += [n for n, _ in secs if n not in order] + [k for k in ("skills", "jobs", "events", "research", "talks", "tenders", "funding", "student_opps", "fieldwork_blog") if k in extra and k not in order]
        for b in c.get("bottom_blocks") or []:
            if b in extra and b not in order:
                order.append(b)
    body, nav, n_news, n_blocks = [], [], 0, 0
    half_for = {}
    if halves:
        for h in halves:
            blocks = [b for b in (h.get("blocks") or []) if b in news or b in extra]
            if blocks:
                half_for[blocks[0]] = h
    meme = ""
    if c.get("meme"):  # Meme of the day (memes.py), after the second news section. Never stops the build.
        try:
            import memes
            _m, _st, _src = memes.make(stories, c.get("key") or "daily", _iso(date))
            meme = memes.html_box(_m, _st)
            print(f"meme: {_src} ({_m['format']})", flush=True)
        except Exception as e:
            print(f"meme: skipped ({e})", flush=True)
    # Interludes (interludes.py): deadpan strips after safe news sections, spread down the page. Never stops the build.
    inter_at = {}
    try:
        import interludes
        _key = c.get("key") or "daily"
        _lines = interludes.lines_for(_key, _iso(date))
        _secmap = {n: st for n, st in secs}
        _cand, _nn, _nb = [], 0, 0
        for _i, _k in enumerate(order):
            _nb += 1
            if _k not in news:
                continue
            _nn += 1
            _nxt = order[_i + 1] if _i + 1 < len(order) else None
            busy = (meme and _nn == 2) or (box and _nn == 1) or (c["ad_html"] and _nb == c["ad_after"]) or (c.get("ad2_html") and _nb == c.get("ad2_after"))
            if _nxt is None or busy:
                continue
            if interludes.safe_slot(_k, _secmap.get(_k, []), _nxt if _nxt in news else None, _secmap.get(_nxt, []) if _nxt in news else []):
                _cand.append(_k)
        for _k, _l in zip(interludes.choose(_cand, len(_lines)), _lines):
            inter_at[_k] = interludes.html_strip(_l)
        print(f"interludes: {len(inter_at)} placed of {len(_lines)} ({len(_cand)} safe slots)", flush=True)
    except SystemExit:
        raise
    except Exception as e:
        print(f"interludes: skipped ({e})", flush=True)
    half_seen = set()
    for k in order:
        if k in half_for and half_for[k].get("id") not in half_seen:
            h = half_for[k]
            body.append(half_banner_html(h, first=(len(half_seen) == 0)))
            half_seen.add(h.get("id"))
            nav.append(f'<a href="#half-{esc(h.get("id") or slug(h.get("title") or ""))}">{esc(h.get("title") or "")}</a>')
        if k in news:
            body.append(news[k]); n_news += 1; nav.append(f'<a href="#{slug(k)}">{esc(k)}</a>')
        else:
            body.append(extra[k][0]); nav.append(f'<a href="#{k}">{esc(extra[k][3])}</a>')
        n_blocks += 1
        if meme and n_news == 2 and k in news:
            body.append(meme)
        if box and n_news == 1 and k in news and not any('class="explains"' in x for x in body):
            body.append(box)
        if c["ad_html"] and n_blocks == c["ad_after"]:
            ad = c["ad_html"]
            if 'class="housead"' in ad and ' id=' not in ad.split(">", 1)[0]:
                ad = ad.replace('<aside class="housead"', f'<aside class="housead" id="{c["ad_id"]}"', 1)
            body.append(ad)
        if c.get("ad2_html") and n_blocks == c.get("ad2_after"):
            body.append(c["ad2_html"])
        if k in inter_at:
            body.append(inter_at[k])
    nav = "".join(nav)
    # Menu: pinned utility blocks (or config menu_pins). Schools omits Jobs from the menu.
    jobs_in_menu = c.get("jobs_in_menu", True)
    pin_ids = ["jobs", "skills", "events", "research", "talks", "student_opps", "fieldwork_blog"] + [b for b in c.get("top_blocks", []) if b in extra and b not in ("jobs", "skills", "events", "research", "talks", "student_opps", "fieldwork_blog")]
    if c.get("menu_pins") is not None:  # explicit pin list only (Schools: student blocks stay in half order in the menu)
        pin_ids = [b for b in c["menu_pins"] if b in extra]
    if not jobs_in_menu:
        pin_ids = [b for b in pin_ids if b != "jobs"]
    pinned = [(k, extra[k][1], extra[k][2]) for k in pin_ids if k in extra]
    menu = menu_html(secs, has_jobs, len(jobs["jobs"]) if has_jobs else 0, any(f'id="{c["ad_id"]}"' in b for b in body), bool(box), pinned,
                     (c["ad_id"], c["ad_menu"], c["ad_menu_note"]), c.get("url", ""), halves=halves or None, jobs_in_menu=jobs_in_menu)
    css = CSS + MENU_CSS + PILL_CSS + A2HS_CSS + HALF_CSS + (AD_CSS if (c["ad_html"] or c["family"]) else "") + (JOBS_CSS if (has_jobs or has_ev or opps or student_opps) else "") + (EV_CSS if (has_ev or opps or student_opps) else "") + sk_css + rd_css + (KICKER_CSS if any(s.get("kicker") for s in stories) else "") + (BANNER_CSS if c.get("banner_html") else "")
    if inter_at:
        css += interludes.CSS
    if meme:
        import memes
        css += memes.CSS
    if box:
        import columns
        css += columns.BOX_CSS + ".menu-list .m-ex a{font-style:italic}"
    credit = CREDIT if (c.get("url") and not c.get("no_earth5r")) else ""
    if c.get("url"):
        css += CREDIT_CSS
        c["head_extra"] = PWA_RE.sub("", c["head_extra"]) + pwa_head(c)
    for hk in HOUSE_KEYS:
        if isinstance(c.get(hk), str): house_count_check(f"{c.get('key', 'daily')} {hk}", c[hk])
    house_count_check("defaults", A2HS_INTRO + " " + DEFAULT_EVENTS_INTRO)
    import maker  # "Created by" credit inside the footer (maker.py). Prints nothing until maker.ENABLED.
    maker_html = maker.html_block(c.get("key") or "daily", c.get("title") or "Yes Bro")
    css += maker.css()
    house_count_check(f"{c.get('key', 'daily')} maker", maker_html)
    ear_right = c["ear_right"].replace("{n}", str(len(stories)))
    fam = f'<p class="family">{c["family"]}</p>' if c["family"] else ""
    # Share (share.py): stable paper URL, never the archive URL. Bar under the dateline, a small one near the foot, and the panel.
    sh_top = sh_foot = sh_panel = sh_js = ""
    if c.get("url"):
        import share
        _st = share.text_for(c.get("key") or "daily", c["title"])
        sh_top = share.bar(c["url"], c["title"], _st)
        sh_foot = share.bar(c["url"], c["title"], _st, foot=True)
        sh_panel = share.panel(c["url"], c["title"], _st)
        sh_js = share.JS
        css += share.CSS
        css += BACK_TOP_CSS
        house_count_check(f"{c.get('key', 'daily')} share", _st)
    out = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(c["seo_title"]) if c["seo_title"] else esc(c["title"]) + " | " + esc(date)}</title>{c["head_extra"]}{seo_head(c, date, secs)}
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=UnifrakturMaguntia&family=Playfair+Display:wght@700;900&family=Old+Standard+TT:ital,wght@0,400;0,700;1,400&family=Libre+Caslon+Text:ital,wght@0,400;0,700;1,400&display=swap" rel="stylesheet">
<style>{css}</style></head>
<body id="top">{menu}<div class="sheet">
<div class="paper-pills"><a class="mypaper-pill" href="https://yesbrohq.com/mypaper/">My Paper</a><a class="allpapers" href="{HOME_URL}">{esc(c.get("pill_top", "All Yes Bro papers"))}</a></div>
<header>
<div class="ears"><div class="ear">{c["ear_left"]}</div><div class="ear">{ear_right}</div></div>
<div class="masthead">{fam}<h1><a class="homelink" href="{HOME_URL}" title="All Yes Bro papers">{brand(c["masthead"])}</a></h1><p class="motto">{esc(c["motto"])}</p></div>
<div class="dateline"><span>{esc(c["edition"])}</span><b>{esc(date)}</b><span>{esc(c["price"])}</span></div>
{a2hs_html(c.get("a2hs_intro", A2HS_INTRO))}
{sh_top}
<nav class="sections">{nav}</nav>
</header>
<main>{c.get("banner_html") or ""}{"".join(body)}</main>
{sh_foot}
<div class="allpapers-bottom"><a class="mypaper-pill" href="https://yesbrohq.com/mypaper/" style="margin:0 8px 10px 0">My Paper<span>Pick your sections</span></a><a href="{HOME_URL}">All Yes Bro papers<span>{esc(c.get("pill_bottom", "Other papers. Equally free."))}</span></a></div>
<footer>{esc(c["footer"])}{credit}{maker_html}</footer>
</div>{sh_panel}{BACK_TOP_BTN}{MENU_JS}{sh_js}{BACK_TOP_JS}{yb_auth_strip.html()}</body></html>
"""
    if c.get("no_earth5r"):  # Healing: no FIELDWORK or Earth5R anywhere, by house rule (see README)
        bad = re.findall(r"fieldwork|earth5r", re.sub(r"<style>.*?</style>", "", out, flags=re.S), re.I)
        if bad:
            raise SystemExit(f"NO-EARTH5R GUARD: {c.get('key')} output mentions {sorted(set(b.lower() for b in bad))}. Remove them.")
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inp"); ap.add_argument("date"); ap.add_argument("out")
    ap.add_argument("--fallback", default=None)
    ap.add_argument("--config", default=None,
                    help="optional JSON file for other editions: sections (list), title, masthead, family, motto, "
                         "ear_left, ear_right, edition, price, footer, head_extra, ad_html, ad_after (insert ad after N sections)")
    ap.add_argument("--jobs", default=None, help="optional jobs JSON from jobs.py, adds a Jobs section at the end")
    ap.add_argument("--events", default=None, help="optional events JSON from events.py, adds Events and Conferences after Jobs")
    ap.add_argument("--opps", default=None, help="optional opps JSON from opps.py (Business), adds Government Tenders and Releases and Funding Opportunities")
    ap.add_argument("--research", default=None, help="optional research JSON from research.py")
    ap.add_argument("--talks", default=None, help="optional talks JSON from talks.py")
    ap.add_argument("--student-opps", default=None, help="optional student opportunities JSON (Schools)")
    ap.add_argument("--fieldwork-blog", default=None, help="optional FIELDWORK blog JSON (Schools)")
    a = ap.parse_args()
    jobs = json.load(open(a.jobs)) if a.jobs else None
    import os as _os
    events = json.load(open(a.events)) if a.events and _os.path.exists(a.events) else None
    opps = json.load(open(a.opps)) if a.opps and _os.path.exists(a.opps) else None
    research = json.load(open(a.research)) if a.research and _os.path.exists(a.research) else None
    talks = json.load(open(a.talks)) if a.talks and _os.path.exists(a.talks) else None
    student_opps = json.load(open(a.student_opps)) if getattr(a, "student_opps", None) and _os.path.exists(a.student_opps) else None
    fieldwork_blog = json.load(open(a.fieldwork_blog)) if getattr(a, "fieldwork_blog", None) and _os.path.exists(a.fieldwork_blog) else None
    cfg = json.load(open(a.config)) if a.config else {}
    # House rule: never say intern/internship in our own copy (config labels, intros, SEO, ad copy). Third party job titles may keep their own words.
    _own = [f"{k}: {v}" for k, v in cfg.items() if isinstance(v, str) and re.search(r"(?i)\bintern(ship)?s?\b|earth5r\.org/[^\"\s]*intern", v)]
    if _own:
        raise SystemExit("no-intern rule broken in config copy: " + " | ".join(_own))
    sections = cfg.pop("sections", None)
    stories = json.load(open(a.inp))
    # Hard blocklist (blocklist.py): Begin Group gets no coverage anywhere. Drop silently, log the count.
    import blocklist
    _bl = {}
    stories = blocklist.keep(stories, "stories", _bl)
    if jobs and jobs.get("jobs"): jobs["jobs"] = blocklist.keep(jobs["jobs"], "jobs", _bl)
    if events and events.get("events"): events["events"] = blocklist.keep(events["events"], "events", _bl)
    for _k in ("tenders", "releases", "funding"):
        if opps and opps.get(_k): opps[_k] = blocklist.keep(opps[_k], "opps", _bl)
    blocklist.log(_bl)
    fb = {}
    if a.fallback:
        fb = {s["url"]: s.get("image", "") for s in json.load(open(a.fallback)) if s.get("image")}
    if research and research.get("items"): research["items"] = blocklist.keep(research["items"], "research", _bl)
    if talks and talks.get("talks"): talks["talks"] = blocklist.keep(talks["talks"], "talks", _bl)
    if cfg.get("satire"):
        for _s in stories:
            _s["kicker"] = _s.get("kicker") or "Satire"
            _s.setdefault("source", "Yes Bro Fake News Desk")
            _s.setdefault("more_label", "This is satire. Nothing here is true \u2192")
            if not (_s.get("url") or "").startswith(("http://", "https://", "#")):
                _s["url"] = "#satire-notice"
    page = build(stories, a.date, fb, sections, cfg, jobs, events, opps, research, talks, student_opps, fieldwork_blog)
    blocklist.guard_html(page, cfg.get("key") or a.out)  # final guard: fail this paper if Begin slipped in via config, column, meme or interlude
    open(a.out, "w").write(page)
    n = sum(1 for s in stories if s.get("image"))
    print(f"wrote {a.out}: {len(stories)} stories, {n} with images", flush=True)

if __name__ == "__main__":
    main()
