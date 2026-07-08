"""Load and patch static HTML for Streamlit multipage routing."""

from __future__ import annotations

import re
from pathlib import Path

STATIC_DIR = Path(__file__).resolve().parent.parent / "app" / "static"

STREAMLIT_SUBMIT_REDIRECT = """
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (!validateStep(8)) return;

      message.className = "message";
      message.textContent = "";
      submitBtn.disabled = true;
      nextBtn.disabled = true;
      prevBtn.disabled = true;

      const payload = buildPayload();

      try {
        window.parent.postMessage({ type: "mip:lead_submit", payload }, "*");
        message.className = "message";
        message.textContent = "Submitting your application…";
      } catch (err) {
        message.className = "message error";
        message.textContent = err.message;
        submitBtn.disabled = false;
        nextBtn.disabled = false;
        prevBtn.disabled = false;
      }
    });
"""

_LEGACY_SUBMIT_POSTMESSAGE = """    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (!validateStep(8)) return;

      message.className = "message";
      message.textContent = "";
      submitBtn.disabled = true;
      nextBtn.disabled = true;
      prevBtn.disabled = true;

      const payload = buildPayload();

      try {
        window.parent.postMessage({
          type: "streamlit:setComponentValue",
          value: payload
        }, "*");
        message.className = "message";
        message.textContent = "Submitting your application…";
      } catch (err) {
        message.className = "message error";
        message.textContent = err.message;
        submitBtn.disabled = false;
        nextBtn.disabled = false;
        prevBtn.disabled = false;
      }
    });"""


def _patch_streamlit_links(html: str) -> str:
    """Back links inside the iframe should navigate the Streamlit parent page."""
    html = html.replace('class="back-link" href="/"', 'class="back-link" href="/" target="_parent"')
    html = html.replace(
        'href="/" class="btn btn-primary" style="display: inline-block;',
        'href="/" target="_parent" class="btn btn-primary" style="display: inline-block;',
    )
    return html


def _extract_fragment(html: str, *, wrapper_class: str, body_selector_replace: str) -> str:
    styles = "\n".join(
        re.findall(r"<style[^>]*>.*?</style>", html, flags=re.DOTALL | re.IGNORECASE)
    )
    styles = styles.replace("body {", f"{body_selector_replace}" + " {", 1)
    styles += f"""
<style>
.{wrapper_class} {{
  width: 100%;
  margin: 0;
  padding: 0;
}}
</style>
"""
    body_match = re.search(r"<body[^>]*>(.*)</body>", html, flags=re.DOTALL | re.IGNORECASE)
    if not body_match:
        raise RuntimeError("HTML is missing <body>")
    return f'{styles}\n<div class="{wrapper_class}">{body_match.group(1)}</div>'


def load_landing_html() -> str:
    """Full landing page document for iframe embed (form uses postMessage to parent)."""
    html = (STATIC_DIR / "landing.html").read_text(encoding="utf-8")
    return _patch_streamlit_links(html)


def load_intake_html_fragment() -> str:
    """Return intake form for st.html with URL-based submit (works on Streamlit Cloud)."""
    html = (STATIC_DIR / "capture_form.html").read_text(encoding="utf-8")
    html = _patch_streamlit_links(html)
    if _LEGACY_SUBMIT_POSTMESSAGE in html:
        html = html.replace(_LEGACY_SUBMIT_POSTMESSAGE, STREAMLIT_SUBMIT_REDIRECT.strip())
    fragment = _extract_fragment(html, wrapper_class="mip-apply", body_selector_replace=".mip-apply")
    return fragment.replace('href="/"', 'href="/"')


def load_intake_html() -> str:
    """Full HTML document (legacy / static file generation)."""
    html = (STATIC_DIR / "capture_form.html").read_text(encoding="utf-8")
    html = _patch_streamlit_links(html)
    if _LEGACY_SUBMIT_POSTMESSAGE in html:
        html = html.replace(_LEGACY_SUBMIT_POSTMESSAGE, STREAMLIT_SUBMIT_REDIRECT.strip())
    return html