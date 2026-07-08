"""Load and patch static HTML for Streamlit multipage routing."""

from __future__ import annotations

import re
from pathlib import Path

STATIC_DIR = Path(__file__).resolve().parent.parent / "app" / "static"

def _patch_streamlit_links(html: str) -> str:
    """Patch links used inside components.html iframes (intake form)."""
    html = html.replace(
        'href="/"',
        'href="/" target="_top" onclick="window.top.location.href=\'/\';return false;"',
    )
    return html


def load_landing_html() -> str:
    """Return landing styles + body for st.html (not iframed — links work normally)."""
    html = (STATIC_DIR / "landing.html").read_text(encoding="utf-8")
    styles = "\n".join(
        re.findall(r"<style[^>]*>.*?</style>", html, flags=re.DOTALL | re.IGNORECASE)
    )
    # Body rules do not apply once <body> is stripped — scope them to our wrapper.
    styles = styles.replace("body {", ".mip-landing {", 1)
    styles += """
<style>
.mip-landing {
  width: 100%;
  margin: 0;
  padding: 0;
}
.mip-landing h1,
.mip-landing h2,
.mip-landing h3,
.mip-landing h4,
.mip-landing p,
.mip-landing a,
.mip-landing li,
.mip-landing span {
  font-family: inherit;
  line-height: inherit;
}
</style>
"""
    body_match = re.search(r"<body[^>]*>(.*)</body>", html, flags=re.DOTALL | re.IGNORECASE)
    if not body_match:
        raise RuntimeError("landing.html is missing <body>")
    body = body_match.group(1).replace('href="/apply"', 'href="/Apply"')
    return f'{styles}\n<div class="mip-landing">{body}</div>'


def load_intake_html() -> str:
    html = (STATIC_DIR / "capture_form.html").read_text(encoding="utf-8")
    return _patch_streamlit_links(html)