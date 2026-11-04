#!/usr/bin/env python3
"""Publish one built paper to the site and refresh the sitemap.

  python3 publish.py <key> <built.html> <YYYY-MM-DD> [--site /workspace/yesbro-site]

key is one of daily, ux, arch, schools, sustainability, startups, highered, consulting, health, marketing, finance, aviation.
Writes <folder>/index.html and <folder>/archive/<date>.html. The archive copy gets ../ head paths
(manifest.json, icon-512.png) and its canonical, og:url and JSON-LD url point at the archive page itself,
so back issues stay indexable without competing with today's paper. Never touches CNAME or root archive/.
"""
import os, sys, shutil
from columns import EDS, SITE

def main():
    a = sys.argv[1:]
    site = "/workspace/yesbro-site"
    if "--site" in a:
        i = a.index("--site"); site = a[i + 1]; del a[i:i + 2]
    key, built, date = a
    folder = EDS[key][0]
    t = open(built, encoding="utf-8").read()
    import blocklist
    blocklist.guard_html(t, key)  # final guard: a paper that mentions Begin Group is never published
    os.makedirs(os.path.join(site, folder, "archive"), exist_ok=True)
    open(os.path.join(site, folder, "index.html"), "w").write(t)
    live, arch = f"{SITE}/{folder}/", f"{SITE}/{folder}/archive/{date}.html"
    at = (t.replace('href="manifest.json"', 'href="../manifest.json"')
           .replace('"../icon-512.png"', '"../../icon-512.png"')
           .replace(f'<link rel="canonical" href="{live}">', f'<link rel="canonical" href="{arch}">')
           .replace(f'<meta property="og:url" content="{live}">', f'<meta property="og:url" content="{arch}">')
           .replace(f'"url": "{live}"', f'"url": "{arch}"'))
    open(os.path.join(site, folder, "archive", f"{date}.html"), "w").write(at)
    print(f"published {key} to {folder}/index.html and {folder}/archive/{date}.html")
    import sitemap
    sitemap.write(site)

if __name__ == "__main__":
    main()
