#!/usr/bin/env python3
"""Write the home screen manifest for every paper folder (Add to Home Screen / Install app).

  python3 pwa.py [--site /workspace/yesbro-site]

Each <folder>/manifest.json gets name "Yes Bro <Field>", start_url and scope set to the paper's own folder,
standalone display, the paper colours and the shared 512px icon. build_html.py writes the matching
apple-mobile-web-app and manifest tags in every paper's head. The landing page manifest is written by build_landing.py.
"""
import json, os, sys
from columns import EDS

def main():
    site = sys.argv[sys.argv.index("--site") + 1] if "--site" in sys.argv else "/workspace/yesbro-site"
    for key, (folder, label) in EDS.items():
        name = f"Yes Bro {label}"
        m = {"id": f"/{folder}/", "name": name, "short_name": name if len(name) <= 15 else label,
             "description": f"{name}, a free daily newspaper by Yes Bro.", "start_url": f"/{folder}/", "scope": f"/{folder}/",
             "display": "standalone", "background_color": "#f3ead6", "theme_color": "#f3ead6",
             "icons": [{"src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"}]}
        os.makedirs(os.path.join(site, folder), exist_ok=True)
        json.dump(m, open(os.path.join(site, folder, "manifest.json"), "w"), ensure_ascii=False)
    # My Paper gets its own manifest from build_mypaper.py; refresh it here too if the folder exists.
    mp = os.path.join(site, "mypaper")
    if os.path.isdir(mp):
        m = {"id": "/mypaper/", "name": "Yes Bro My Paper", "short_name": "My Paper",
             "description": "Build your own Yes Bro paper from every edition.",
             "start_url": "/mypaper/", "scope": "/mypaper/", "display": "standalone",
             "background_color": "#f3ead6", "theme_color": "#f3ead6",
             "icons": [{"src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"}]}
        json.dump(m, open(os.path.join(mp, "manifest.json"), "w"), ensure_ascii=False)
        print(f"pwa: wrote {len(EDS)} paper manifests and mypaper")
    else:
        print(f"pwa: wrote {len(EDS)} manifests")

if __name__ == "__main__":
    main()
