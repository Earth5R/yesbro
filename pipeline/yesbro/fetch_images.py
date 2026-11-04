#!/usr/bin/env python3
"""Fetch og:image / twitter:image for each story and embed a tiny thumbnail as a data URI.

Usage:
  python3 fetch_images.py stories.json out.json [--width 200] [--quality 30] [--format webp] [--crop 16:9]

stories.json: list of objects with at least {"url": ...} (section, headline, summary kept as-is).
out.json: same list, each with "image" set to a data URI string, or "" if none could be fetched.
Thumbnails are cached in ./cache/ keyed by article URL.

HTML mode (for build_html.py):
  python3 fetch_images.py stories.json out.json --mode html [--width 640] [--quality 60]
  Each story gets "image_url" (the original og:image, full quality) and "image" which is:
    - the original URL itself when the image host allows hotlinking (no Referer / foreign Referer), or
    - an embedded data URI (default 640px WebP q60) when the host blocks hotlinking, or
    - "" when the article has no usable image.
"""
import argparse, base64, hashlib, html, io, json, os, re, sys
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin
import subprocess
from PIL import Image

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/129.0 Safari/537.36")
HDRS = {"User-Agent": UA, "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
        "Accept-Language": "en-IN,en;q=0.9"}
META_RE = re.compile(r"<meta\b[^>]*>", re.I)
# Site-wide fallback images that are not the story's own picture: skip them.
GENERIC = re.compile(r"placeholder|og-image|meta-facebook|generic|emblem|/default[._-]|/logo\.|favicon", re.I)

def find_image(page, base):
    for tag in META_RE.findall(page):
        m = re.search(r'(?:property|name)\s*=\s*["\']?\s*(og:image(?::secure_url|:url)?|twitter:image(?::src)?)\b', tag, re.I)
        if not m:
            continue
        c = re.search(r'content\s*=\s*(?:"([^"]+)"|\'([^\']+)\'|([^\s>]+))', tag, re.I)
        if c:
            v = html.unescape((c.group(1) or c.group(2) or c.group(3)).strip())
            if v.startswith("https:/") and not v.startswith("https://"):
                v = "https://" + v[7:]
            if v:
                return urljoin(base, v)
    return None

def curl(url, referer=None, accept="text/html,*/*", extra=()):
    cmd = ["curl", "-sL", "--compressed", "-m", "30", "-A", UA, "-H", "Accept-Language: en-IN,en;q=0.9",
           "-H", f"Accept: {accept}", "-w", "\n%{http_code}"]
    if referer:
        cmd += ["-e", referer]
    for h in extra:
        cmd += ["-H", h]
    out = subprocess.run(cmd + [url], capture_output=True).stdout
    body, _, code = out.rpartition(b"\n")
    return int(code or 0), body

def get_page(url):
    code, body = curl(url)
    if code == 200 and find_image(body.decode("utf-8", "replace"), url):
        return code, body.decode("utf-8", "replace"), "direct"
    # Fallback: public reader proxy returns the original HTML for sites that block plain curl.
    c2, b2 = curl("https://r.jina.ai/" + url, extra=["X-Return-Format: html"])
    if c2 == 200:
        return c2, b2.decode("utf-8", "replace"), "reader"
    return code, body.decode("utf-8", "replace"), "direct"

def process(story, width, quality, fmt, cache, crop=(16, 9)):
    url = story["url"]
    key = hashlib.md5(f"{url}|{width}|{quality}|{fmt}|{crop}".encode()).hexdigest()
    cpath = os.path.join(cache, key + ".txt")
    if os.path.exists(cpath):
        return open(cpath).read(), "cached"
    try:
        code, page, how = get_page(url)
        if code != 200:
            return "", f"page HTTP {code}"
        img_url = find_image(page, url)
        if not img_url:
            return "", "no og:image"
        if GENERIC.search(img_url):
            return "", f"generic site image skipped ({img_url})"
        icode, data = curl(img_url, referer=url, accept="image/*")
        if icode != 200:
            return "", f"image HTTP {icode}"
        im = Image.open(io.BytesIO(data)).convert("RGB")
        if im.width < 200:
            return "", "image too small"
        if crop:  # centre-crop to a fixed ratio (default 16:9) so cards line up
            tw, th = crop
            if im.width / im.height > tw / th:
                nw = round(im.height * tw / th); x = (im.width - nw) // 2
                im = im.crop((x, 0, x + nw, im.height))
            else:
                nh = round(im.width * th / tw); y = (im.height - nh) // 2
                im = im.crop((0, y, im.width, y + nh))
        h = round(im.height * width / im.width)
        im = im.resize((width, h), Image.LANCZOS)
        buf = io.BytesIO()
        if fmt == "webp":
            im.save(buf, "WEBP", quality=quality, method=6)
            mime = "image/webp"
        else:
            im.save(buf, "JPEG", quality=quality, optimize=True, progressive=True)
            mime = "image/jpeg"
        uri = f"data:{mime};base64," + base64.b64encode(buf.getvalue()).decode()
        open(cpath, "w").write(uri)
        return uri, f"ok {len(buf.getvalue())}B via {how} from {img_url}"
    except Exception as e:
        return "", f"error {type(e).__name__}: {e}"

def hotlink_ok(img_url):
    """True if the image loads without the publisher's Referer, as it would from a local file or Drive."""
    for ref in (None, "https://drive.google.com/"):
        cmd = ["curl", "-sL", "-m", "20", "-A", UA, "-H", "Accept: image/avif,image/webp,image/*,*/*",
               "-o", "/dev/null", "-w", "%{http_code} %{content_type}"]
        if ref:
            cmd += ["-e", ref]
        out = subprocess.run(cmd + [img_url], capture_output=True, text=True).stdout.split(" ", 1)
        if not (out[0] == "200" and len(out) > 1 and out[1].startswith("image/")):
            return False
    return True

def process_html(story, width, quality, cache):
    url = story["url"]
    key = hashlib.md5(f"html|{url}|{width}|{quality}".encode()).hexdigest()
    cpath = os.path.join(cache, key + ".json")
    if os.path.exists(cpath):
        d = json.load(open(cpath)); return d["image_url"], d["image"], "cached"
    try:
        code, page, how = get_page(url)
        if code != 200:
            return "", "", f"page HTTP {code}"
        img_url = find_image(page, url)
        if not img_url:
            return "", "", "no og:image"
        if GENERIC.search(img_url):
            return "", "", f"generic site image skipped ({img_url})"
        icode, data = curl(img_url, referer=url, accept="image/*")
        if icode != 200:
            return "", "", f"image HTTP {icode}"
        im = Image.open(io.BytesIO(data)).convert("RGB")
        if im.width < 200:
            return "", "", "image too small"
        if hotlink_ok(img_url):
            img, msg = img_url, f"hotlink ok via {how}"
        else:
            if im.width > width:
                im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
            buf = io.BytesIO(); im.save(buf, "WEBP", quality=quality, method=6)
            img = "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()
            msg = f"hotlink blocked, embedded {len(buf.getvalue())}B via {how}"
        json.dump({"image_url": img_url, "image": img}, open(cpath, "w"))
        return img_url, img, msg + f" from {img_url}"
    except Exception as e:
        return "", "", f"error {type(e).__name__}: {e}"

def main_html(a, stories, cache):
    with ThreadPoolExecutor(8) as ex:
        res = list(ex.map(lambda s: process_html(s, a.width or 640, a.quality or 60, cache), stories))
    for s, (iu, img, msg) in zip(stories, res):
        s["image_url"], s["image"] = iu, img
        print(f"[{'IMG' if img else '---'}] {s['url'][:70]} :: {msg}", file=sys.stderr)
    json.dump(stories, open(a.out, "w"), indent=1, ensure_ascii=False)
    n = sum(1 for s in stories if s["image"]); e = sum(1 for s in stories if s["image"].startswith("data:"))
    print(f"{n}/{len(stories)} with images ({n-e} original URLs, {e} embedded)", file=sys.stderr)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inp"); ap.add_argument("out")
    ap.add_argument("--mode", choices=["canvas", "html"], default="canvas")
    ap.add_argument("--width", type=int, default=None)
    ap.add_argument("--quality", type=int, default=None)
    ap.add_argument("--format", choices=["webp", "jpeg"], default="webp")
    ap.add_argument("--crop", default="16:9", help="W:H centre crop, or 'none'")
    a = ap.parse_args()
    crop = None if a.crop == "none" else tuple(int(x) for x in a.crop.split(":"))
    stories = json.load(open(a.inp))
    cache = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
    os.makedirs(cache, exist_ok=True)
    if a.mode == "html":
        return main_html(a, stories, cache)
    a.width = a.width or 200; a.quality = a.quality or 30
    with ThreadPoolExecutor(8) as ex:
        res = list(ex.map(lambda s: process(s, a.width, a.quality, a.format, cache, crop), stories))
    total = 0
    for s, (uri, msg) in zip(stories, res):
        s["image"] = uri
        total += len(uri)
        print(f"[{'IMG' if uri else '---'}] {s['url'][:70]} :: {msg}", file=sys.stderr)
    json.dump(stories, open(a.out, "w"), indent=1, ensure_ascii=False)
    print(f"{sum(1 for s in stories if s['image'])}/{len(stories)} with images, {total} chars of data URIs", file=sys.stderr)

if __name__ == "__main__":
    main()
