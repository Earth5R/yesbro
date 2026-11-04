"""Maker credit at the end of every paper and the landing page (imported by build_html.py and build_landing.py).

Prints "Created by Saurabh Gupta", a mailto link to ontheworldroad@gmail.com with the paper name as the subject,
and one deadpan line per paper from LINES. House voice: dry, no dashes, semicolons, tricolons, counting or
intern words. Healing stays gentle and never mentions FIELDWORK or Earth5R (the Healing guard still checks).

ENABLED switches the credit on (approved 27 Oct 2026). Set it False to remove it from every page on the next build.
"""
import html, os, re
from urllib.parse import quote

ENABLED = True
NAME = "Saurabh Gupta"
EMAIL = "ontheworldroad@gmail.com"

# Spare lines. A new paper without its own line in LINES uses GENERAL[0].
GENERAL = [
    "He reads the news so you can say you did.",
    "Replies arrive. Eventually, but they arrive.",
    "He also has no idea why you scrolled this far, but respects it.",
    "Feedback is welcome. Praise is welcomed slightly faster.",
    "He made this before breakfast and would like some credit for that.",
    "Write in. He reads his email more carefully than the terms and conditions.",
    "You have reached the bottom. He is proud of you.",
    "Corrections are welcome and will be accepted with mild embarrassment.",
    "He would sign each copy, but the internet makes that difficult.",
    "If you liked this, tell a friend. If you did not, tell him.",
]

LINES = {  # approved by the owner on 27 Oct 2026, use exactly
    "landing": "If you liked this, tell a friend. If you did not, tell him.",
    "daily": "He read all of it. He is fine.",
    "business": "His own balance sheet is not up for discussion.",
    "ux": "The email link works on the first click, a rare thing in this industry.",
    "arch": "He would like more natural light and less brutalism.",
    "schools": "He was also once told to read the newspaper, and here we are.",
    "sustainability": "No trees were harmed in printing this, because nothing was printed.",
    "startups": "He replies faster than your investors.",
    "highered": "The essay is still your problem, and he is sorry about that.",
    "consulting": "Writing to him is not billable.",
    "health": "His only prescription is reading to the end, which you did.",
    "marketing": "This is the call to action. It is very calm.",
    "finance": "Writing to him is also not investment advice.",
    "aviation": "Replies may experience mild turbulence.",
    "healing": "Breathe in, write in, breathe out.",
    "ai": "He has not been replaced yet, and he checks every morning.",
    "packaging": "Handle with care. He wrapped this one himself.",
    "fashion": "He did not invent the trend. He only reported it, mostly.",
    "realestate": "He measured twice. He still reported the brochure figure.",
    "auto": "He checked the on-road price. He still asked for a discount.",
}

def _check(s):
    if any(ch in s for ch in ("\u2014", "\u2013", ";")) or re.search(r"(?i)\bintern(ship)?s?\b|fieldwork|earth5r", s):
        raise SystemExit(f"maker copy breaks house rules: {s!r}")
for _v in list(LINES.values()) + GENERAL:
    _check(_v)

CSS = r"""
.maker{margin:14px auto 0;padding:10px 0 2px;border-top:1px solid var(--rule-soft);max-width:520px;text-align:center;
  font-family:"Old Standard TT",Georgia,serif;font-style:normal;color:var(--ink-soft)}
.maker p{margin:0 0 3px;line-height:1.45}
.maker .mk-by{font-size:12px;letter-spacing:.2em;text-transform:uppercase;color:var(--ink)}
.maker .mk-mail{font-size:13.5px}
.maker .mk-mail a{color:var(--ink);text-decoration:underline;text-underline-offset:2px;word-break:break-all}
.maker .mk-line{font-style:italic;font-size:13px;color:var(--ink-faint)}
"""

def line_for(key):
    return LINES.get(key) or GENERAL[0]

def html_block(key, subject):
    if not ENABLED:
        return ""
    e = lambda s: html.escape(s, quote=True)
    href = f"mailto:{EMAIL}?subject=" + quote(subject, safe="")
    return (f'<div class="maker"><p class="mk-by">Created by {e(NAME)}</p>'
            f'<p class="mk-mail">Say hello at <a href="{e(href)}">{e(EMAIL)}</a></p>'
            f'<p class="mk-line">{e(line_for(key))}</p></div>')

def css():
    return CSS if ENABLED else ""
