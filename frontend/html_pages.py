"""Load and patch static HTML for Streamlit multipage routing."""

from __future__ import annotations

import re
from pathlib import Path

STATIC_DIR = Path(__file__).resolve().parent.parent / "app" / "static"

STREAMLIT_SUBMIT_HANDLER = """
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
    });
"""


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
    html = _patch_streamlit_links(html)

    old_submit = """    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (!validateStep(8)) return;

      message.className = "message";
      message.textContent = "";
      submitBtn.disabled = true;
      nextBtn.disabled = true;
      prevBtn.disabled = true;

      const payload = buildPayload();

      try {
        const res = await fetch("/api/leads", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const data = await res.json();
        if (!res.ok) {
          const detail = Array.isArray(data.detail)
            ? data.detail.map((d) => d.msg || (d.loc ? d.loc.join(".") + ": " + d.msg : JSON.stringify(d))).join("; ")
            : (data.detail || "Submission failed.");
          throw new Error(detail);
        }

        const lastName = payload.full_name.split(" ").slice(-1)[0];
        form.classList.add("hidden");
        document.getElementById("topDisclaimer").classList.add("hidden");
        document.getElementById("navButtons").classList.add("hidden");
        successPanel.classList.remove("hidden");
        document.getElementById("tierBadge").textContent = "Score Tier: " + (data.score_tier || "Pending");
        document.getElementById("scoreDetail").textContent = data.score != null ? "Preliminary Score: " + data.score + " / 100" : "";
        document.getElementById("successName").textContent = "Thank you, Dr. " + lastName + ". Reference ID: #" + data.id;
      } catch (err) {
        message.className = "message error";
        message.textContent = err.message;
      } finally {
        submitBtn.disabled = false;
        nextBtn.disabled = false;
        prevBtn.disabled = false;
      }
    });"""

    if old_submit not in html:
        raise RuntimeError("capture_form.html submit handler changed — update html_pages.py patch.")
    return html.replace(old_submit, STREAMLIT_SUBMIT_HANDLER.strip())