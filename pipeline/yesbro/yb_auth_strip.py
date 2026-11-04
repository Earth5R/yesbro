"""Shared My Paper auth strip for landing and every field paper.

Nightly rebuilds (rebuild_today.sh → build_html.py / build_landing.py) emit
script tags that load /js/yb-mypaper-bar.js. The JS injects a slim top strip
and uses /mypaper/firebase-config.js for Google sign-in.
"""
from __future__ import annotations

SNIPPET = (
    '<!-- yb-mypaper-bar: shared sign-in strip -->'
    '<script src="/js/yb-mypaper-bar.js" defer></script>'
)


def html() -> str:
    return SNIPPET
