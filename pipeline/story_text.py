"""Keep challenge pages, cookie walls and headline echoes out of story blurbs.

The daily pipeline fetches each picked URL and, when the body is short, used to
glue it to the feed description. Bot walls are short, so the blurb became
"Enable JavaScript and cookies…" plus the headline plus the source name, and
the no-AI fallback then added "The full piece is for subscribers…".

This module is the shared cleaner for fetch, Gemini input, the fallback teaser,
and HTML rendering. It does not invent article facts.
"""
from __future__ import annotations

import html
import re

# Long, distinctive wall phrases. Removed anywhere they appear. Order matters:
# longer lines first so a short piece of a longer line is not left behind.
_PHRASES = (
    "the full piece is for subscribers, and the headline is all that is public for now",
    "further details were not available in the open teaser",
    "please enable js and disable any ad blocker",
    "please enable javascript and cookies to continue",
    "enable javascript and cookies to continue",
    "please enable javascript to continue",
    "please enable javascript to proceed",
    "javascript is disabled in your browser",
    "a required part of this site couldn't load",
    "this may be due to a browser extension, network issues, or browser settings",
    "we are verifying your browser",
    "we're verifying your browser",
    "website owner? click here to fix",
    "verify you are human",
    "are you a robot",
    "just a quick check",
    "we are checking your connection to prevent automated abuse",
    "we're checking your connection to prevent automated abuse",
    "checking your connection to prevent automated abuse",
    "you don't have permission to access",
    "you do not have permission to access",
    "enable javascript to continue",
    "checking your browser before accessing",
    "checking your browser",
    "this may take a few seconds",
    "click here if you are not redirected automatically",
    "if you are not redirected automatically",
    "px-captcha",
    "403 forbidden",
    "errors.edgesuite.net",
    "cf-browser-verification",
    "oeps, je hebt javascript nodig voor deze website",
    "je hebt javascript nodig",
    "if you have trouble reading this e-mail",
    "if you have trouble reading this email",
    "read the online version",
    "we use cookies to authenticate, authorize, verify, analyze and secure the application",
    "the application will not work with cookies disabled",
    "if the cookies are disabled on your browser, please enable them from browser settings",
    "by clicking accept, you provide your consent",
    "this cookie is used to store the user's cookie consent preferences",
    "the full piece is for subscribers",
    "основные файлы cookie",
)

_BAD_TITLE = re.compile(
    r"just a moment|attention required|access denied|403 forbidden|are you a robot|"
    r"verify you are human|px-captcha|enable javascript|please enable js",
    re.I,
)

_WALL_PREFIX = (
    "enable javascript",
    "please enable js",
    "please enable javascript",
    "just a moment",
    "access denied",
    "403 forbidden",
    "px-captcha",
    "attention required",
    "oeps, je hebt javascript",
)

# Words that do not make a headline-plus-source stub into a real blurb.
_ECHO_EXTRA_MAX = 6


def _flex(phrase: str) -> re.Pattern:
    parts = []
    for ch in phrase:
        if ch == "'":
            parts.append(r"['\u2019]")
        elif ch == " ":
            parts.append(r"\s+")
        else:
            parts.append(re.escape(ch))
    return re.compile("".join(parts), re.I)


_PHRASE_RES = tuple(_flex(p) for p in _PHRASES)

# A sentence that tells the reader to get past a wall, including a model paraphrase
# of that wall ("available to users who enable JavaScript").
_WALL_SENTENCE = re.compile(
    r"(?i)(\benable javascript\b|\bjavascript is disabled\b|\bjavascript to proceed\b|"
    r"\brequires javascript\b|\bad blockers?\b|\bplease check your connection\b|"
    r"\btry using a different\b|\bcrawler bot\b|\bbot detection\b|"
    r"\bverifying your browser\b|\bchecking your browser\b|"
    r"\bnot redirected automatically\b|\bby clicking accept\b|"
    r"\bcookies are disabled\b|\bwe use cookies to\b|"
    r"\bprovide your consent\b)"
)


def collapse(text: str) -> str:
    text = html.unescape(text or "")
    text = text.replace("\u00a0", " ").replace("\u200b", "")
    return re.sub(r"\s+", " ", text).strip()


def _norm(text: str) -> str:
    text = collapse(text).lower().replace("\u2019", "'").replace("`", "'")
    text = re.sub(r"[^a-z0-9$%+']+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def bare_headline(title: str) -> str:
    """Drop a trailing ' - Source' so a teaser does not end on the publisher name."""
    title = collapse(title)
    match = re.search(r"^(?P<head>.+?)\s+[-|–—]\s+(?P<tail>[^-|–—]+)$", title)
    if not match:
        return title
    head, tail = match.group("head").strip(), match.group("tail").strip()
    if len(head.split()) >= 3 and 1 <= len(tail.split()) <= 6:
        return head
    return title


def cookie_banner_dump(text: str) -> bool:
    """True when the text is a consent banner, not a story that mentions cookies."""
    raw = collapse(text)
    if not raw:
        return False
    low = raw.lower()
    if "основные файлы cookie" in low and "cookie preferences" in low:
        return True
    words = _norm(raw).split()
    if len(words) < 12:
        return False
    hits = sum(1 for w in words if w in {"cookie", "cookies", "consent", "preferences"})
    return hits >= 6 and hits / len(words) >= 0.15


def clean_body(text: str) -> str:
    """Remove wall, consent and house-fallback sentences. Leave any real prose."""
    raw = collapse(text)
    if not raw or cookie_banner_dump(raw):
        return ""
    akamai = bool(re.search(r"(?i)permission to access|edgesuite|reference\s*#", raw))
    had_credit = bool(re.search(r"\sCredit\s+-", raw))
    cleaned = raw
    for rx in _PHRASE_RES:
        cleaned = rx.sub(" ", cleaned)
    cleaned = collapse(cleaned)
    if akamai:
        cleaned = re.sub(r"(?i)^access denied\b[\s.:,-]*", "", cleaned)
    cleaned = re.sub(r"(?i)^(?:just a moment\.{0,3}|px-captcha|nginx)\b[\s.:,-]*", "", cleaned)
    cleaned = re.sub(r"https?://\S+", " ", cleaned)
    cleaned = re.sub(r"(?i)\breference\s*#\S+", " ", cleaned)
    cleaned = re.sub(r"(?i)\bon this server\.?", " ", cleaned)
    cleaned = re.sub(r"\sCredit\s+-\s+[^:]{2,60}", " ", cleaned)
    cleaned = re.sub(r"(?:\|\s*)+", " ", cleaned)
    cleaned = cleaned.replace("\\|", " ")
    cleaned = re.sub(r"(?i)\bISSN\s+[\d-]+", " ", cleaned)
    cleaned = re.sub(r"\(\s*\)", " ", cleaned)
    cleaned = re.sub(r"\s+:\s+", ". ", cleaned)
    cleaned = re.sub(r"\s+([,.;:])", r"\1", cleaned)
    cleaned = re.sub(r"^[^\w$£€(\"']+", "", cleaned)
    cleaned = _drop_wall_sentences(collapse(cleaned))
    if had_credit:
        cleaned = _drop_credit_tail(cleaned)
    return collapse(cleaned).strip(" -|")


def _drop_credit_tail(text: str) -> str:
    """Google News pastes 'Credit - Source : Next headline'. Keep the first dek."""
    parts = re.split(r"(?<=[.!?])\s+", collapse(text))
    if len(parts) < 2:
        return collapse(text)
    tail = parts[-1]
    if re.search(r"[.!?]$", tail) or len(tail.split()) > 10:
        return collapse(text)
    kept = " ".join(parts[:-1])
    if len(kept.split()) < 12:
        return collapse(text)
    return kept


def _drop_wall_sentences(text: str) -> str:
    """Drop sentences that only tell the reader how to beat a block page."""
    parts = re.split(r"(?<=[.!?])\s+", collapse(text))
    kept = [part for part in parts if part and not _WALL_SENTENCE.search(part)]
    return " ".join(kept)


def text_has_wall_prefix(text: str) -> bool:
    low = collapse(text).lower()
    return low.startswith(_WALL_PREFIX)


def page_is_challenge(page_html: str, status=None, extracted: str = "") -> bool:
    """True when the fetch is a bot wall rather than an article.

    A cookie banner in the header of a real article is not enough. A long
    extract that does not itself open with a wall is kept.
    """
    page = page_html or ""
    title = ""
    match = re.search(r"<title[^>]*>(.*?)</title>", page, re.I | re.S)
    if match:
        title = collapse(re.sub(r"<[^>]+>", " ", match.group(1))).lower()
    if any(mark in title for mark in (
        "just a moment", "attention required", "access denied", "403 forbidden",
        "are you a robot", "verify you are human",
    )):
        return True
    sample = page[:15000].lower()
    hard = (
        "cf-browser-verification",
        "/cdn-cgi/challenge-platform",
        "cf-challenge-running",
        "errors.edgesuite.net",
        "enable javascript and cookies to continue",
        "please enable js and disable any ad blocker",
        "px-captcha",
    )
    extracted_clean = clean_body(extracted or "")
    looks_like_article = (
        len((extracted or "").split()) >= 40
        and len(extracted_clean.split()) >= 30
        and not text_has_wall_prefix(extracted or "")
    )
    if any(mark in sample for mark in hard):
        return not looks_like_article
    try:
        code = int(status)
    except (TypeError, ValueError):
        code = 0
    if code in (401, 403, 429, 503) and not looks_like_article:
        return True
    return False


def needs_refetch(text: str) -> bool:
    """Cached body from an earlier run that is still a wall."""
    blob = collapse(text).lower()
    if not blob:
        return False
    if text_has_wall_prefix(blob):
        return True
    return bool(re.search(
        r"access denied|edgesuite|px-captcha|enable javascript|ad blocker|just a moment|"
        r"permission to access|403 forbidden|checking your browser",
        blob,
    ))


def is_headline_echo(text: str, title: str) -> bool:
    """True when the text is the headline plus a short source name, nothing more."""
    nt = _norm(clean_body(text))
    if not nt:
        return False
    seen = []
    for cand in (bare_headline(title), title):
        nh = _norm(cand)
        if nh and nh not in seen:
            seen.append(nh)
    for nh in seen:
        if len(nh.split()) < 3 or nh not in nt:
            continue
        extra = " ".join(nt.replace(nh, " ").split()).split()
        if len(extra) <= _ECHO_EXTRA_MAX:
            return True
    return False


def has_news(text: str, title: str = "") -> bool:
    text = clean_body(text)
    if not text or len(text.split()) < 8:
        return False
    if title and is_headline_echo(text, title):
        return False
    return True


def title_is_wall(title: str) -> bool:
    return bool(_BAD_TITLE.search(collapse(title or "")))


def choose_title(og_title: str, rss_title: str) -> str:
    """Prefer the page title, unless that title is the challenge page itself."""
    for cand in (og_title, rss_title):
        title = collapse(cand)
        if title and not _BAD_TITLE.search(title):
            return title
    return collapse(rss_title or og_title or "Untitled")


def choose_source_text(extracted: str, og_desc: str, rss_desc: str, title: str) -> str:
    """One clean source. Never glue a wall, a headline and a source name together."""
    best = ""
    for raw in (extracted, og_desc, rss_desc):
        text = clean_body(raw or "")
        if not has_news(text, title):
            continue
        if len(text.split()) > len(best.split()):
            best = text
    return best[:900]


def prepare_item(fetched: dict) -> dict:
    """Title and text safe to send to Gemini or the fallback."""
    title = choose_title(fetched.get("ogt") or "", fetched.get("title") or "")
    text = choose_source_text(
        fetched.get("tx") or "",
        fetched.get("ogd") or "",
        fetched.get("rss_desc") or "",
        title,
    )
    return {"title": title, "text": text}


def prepare_copy_text(text: str, title: str) -> str:
    text = clean_body(text or "")
    if not has_news(text, title):
        return ""
    return text[:700]


def drop_leading_headline(text: str, title: str) -> str:
    """If a real dek starts by repeating the headline, start at the next sentence."""
    original = text.split()
    target = _norm(bare_headline(title) or "").split()
    if len(target) < 4 or len(original) < len(target) + 12:
        return text
    acc = []
    for n, word in enumerate(original, start=1):
        acc.append(_norm(word))
        flat = [w for w in " ".join(acc).split() if w]
        if flat == target:
            rest = " ".join(original[n:]).lstrip(" .:-|")
            if rest and rest[0].islower():
                rest = rest[0].upper() + rest[1:]
            return rest
        if len(flat) > len(target):
            return text
    return text


def fit_length(text: str) -> str:
    """Bring a real short dek up to the paper's 30-word floor without a second headline."""
    words = collapse(text).split()
    if len(words) > 50:
        return " ".join(words[:50])
    if len(words) >= 30:
        return collapse(text)
    note = "The rest of the report was not in the open text, so this note stops there."
    text = collapse(text).rstrip(" .") + ". " + note
    if len(text.split()) < 30:
        text += " Open the original report for anything further."
    return " ".join(text.split()[:50])


def headline_teaser(title: str) -> str:
    """Dry stand-in when the page and the feed gave us nothing but the headline."""
    head = bare_headline(title) or "This report"
    if _BAD_TITLE.search(head):
        head = "This report"
    words = head.split()
    if len(words) > 18:
        head = " ".join(words[:18]).rstrip(",;:")
    head = head.rstrip(" .")
    note = (
        "The source page returned a block or an empty shell, so this edition "
        "has no article body to go on and stays with the headline."
    )
    summary = f"{head}. {note}"
    if len(summary.split()) < 30:
        summary += " Open the original report for the full account."
    return " ".join(summary.split()[:50])


def present_summary(summary: str, title: str) -> str:
    """Last line of defence before a blurb is saved or printed.

    A clean summary is returned as it was. A wall, a consent dump, or a
    headline glued to a source name becomes a headline teaser. Real prose
    that was only prefixed by a wall is kept.
    """
    raw = collapse(summary)
    if not raw or cookie_banner_dump(raw):
        return headline_teaser(title)
    cleaned = clean_body(raw)
    if not cleaned or is_headline_echo(cleaned, title):
        return headline_teaser(title)
    repaired = _norm(cleaned) != _norm(raw)
    if not repaired:
        words = raw.split()
        return raw if len(words) <= 50 else " ".join(words[:50])
    if not has_news(cleaned, title):
        return headline_teaser(title)
    cleaned = drop_leading_headline(cleaned, title)
    if not cleaned or is_headline_echo(cleaned, title) or not has_news(cleaned, title):
        return headline_teaser(title)
    if len(cleaned.split()) < 30:
        return fit_length(cleaned)
    return " ".join(cleaned.split()[:50])


def fallback_summary(title: str, text: str) -> str:
    """Plain teaser used when Gemini is off, or when there is nothing to summarise."""
    title = collapse(title) or "Untitled"
    text = clean_body(text or "")
    if not has_news(text, title):
        return headline_teaser(title)
    text = drop_leading_headline(text, title)
    if not has_news(text, title):
        return headline_teaser(title)
    summary = " ".join(text.split()[:45])
    if len(summary.split()) < 30:
        summary = fit_length(summary)
    return present_summary(summary, title)


def assemble_story(page_html: str, status, rss_title: str, rss_desc: str,
                   og_title: str = "", og_desc: str = "", extracted: str = "") -> dict:
    """What fetch + fallback would print for one story. Used by tests and examples."""
    body = extracted or ""
    if page_is_challenge(page_html or "", status, body):
        body = ""
    title = choose_title(og_title, rss_title)
    text = choose_source_text(body, og_desc, rss_desc, title)
    return {
        "title": title,
        "text": text,
        "summary": fallback_summary(title, text),
    }
