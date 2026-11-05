#!/usr/bin/env python3
"""Write the home screen manifest for every paper folder (Add to Home Screen / Install app).

  python3 pwa.py [--site DIR]

Each <folder>/manifest.json gets name "Yes Bro <Field>", start_url and scope set to the paper's own folder,
standalone display, the paper colours and the shared 512px icon. build_html.py writes the matching
apple-mobile-web-app and manifest tags in every paper's head. The landing page manifest is written by build_landing.py.

On GitHub Actions, pass --site "$GITHUB_WORKSPACE" (or set YESBRO_SITE). The old /workspace/yesbro-site
default only applies when that path exists locally.
"""
import json, os, sys
from columns import EDS


def default_site() -> str:
    env = (os.environ.get("YESBRO_SITE") or "").strip()
    if env:
        return env
    gw = (os.environ.get("GITHUB_WORKSPACE") or "").strip()
    if gw:
        return gw
    # Repo layout: pipeline/yesbro/pwa.py → site root is parents[2]
    here = os.path.dirname(os.path.abspath(__file__))
    repo = os.path.abspath(os.path.join(here, "..", ".."))
    if os.path.isdir(os.path.join(repo, "daily")) or os.path.exists(os.path.join(repo, "CNAME")):
        return repo
    legacy = "/workspace/yesbro-site"
    if os.path.isdir(legacy):
        return legacy
    return repo


def main():
    if "--site" in sys.argv:
        site = sys.argv[sys.argv.index("--site") + 1]
    else:
        site = default_site()
    site = os.path.abspath(site)
    if not os.path.isdir(site):
        raise SystemExit(f"pwa: site root does not exist: {site}")
    for key, (folder, label) in EDS.items():
        name = f"Yes Bro {label}"
        m = {"id": f"/{folder}/", "name": name, "short_name": name if len(name) <= 15 else label,
             "description": f"{name}, a free daily newspaper by Yes Bro.", "start_url": f"/{folder}/", "scope": f"/{folder}/",
             "display": "standalone", "background_color": "#f3ead6", "theme_color": "#f3ead6",
             "icons": [{"src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"}]}
        dest_dir = os.path.join(site, folder)
        os.makedirs(dest_dir, exist_ok=True)
        with open(os.path.join(dest_dir, "manifest.json"), "w", encoding="utf-8") as f:
            json.dump(m, f, ensure_ascii=False)
    # My Paper gets its own manifest from build_mypaper.py; refresh it here too if the folder exists.
    mp = os.path.join(site, "mypaper")
    if os.path.isdir(mp):
        m = {"id": "/mypaper/", "name": "Yes Bro My Paper", "short_name": "My Paper",
             "description": "Build your own Yes Bro paper from every edition.",
             "start_url": "/mypaper/", "scope": "/mypaper/", "display": "standalone",
             "background_color": "#f3ead6", "theme_color": "#f3ead6",
             "icons": [{"src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"}]}
        with open(os.path.join(mp, "manifest.json"), "w", encoding="utf-8") as f:
            json.dump(m, f, ensure_ascii=False)
        print(f"pwa: wrote {len(EDS)} paper manifests and mypaper under {site}")
    else:
        print(f"pwa: wrote {len(EDS)} manifests under {site}")

if __name__ == "__main__":
    main()
