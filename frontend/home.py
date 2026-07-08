"""Customer-facing landing page with educational lead capture + Calendly booking."""

from __future__ import annotations

import base64
import hashlib
import json
import sys
from pathlib import Path
from typing import Any
import html as html_mod
from urllib.parse import quote

import streamlit as st
import streamlit.components.v1 as components
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from frontend.secrets_bootstrap import bootstrap_env

bootstrap_env()

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from app.config import get_settings
from app.schemas import ShortLeadCreate
from app.short_lead_service import create_short_lead, short_lead_to_response
from frontend.db import ensure_db, get_session
from frontend.html_pages import load_landing_html

SUBMIT_BRIDGE_JS = """
<script>
window.addEventListener("message", function (event) {
  if (event.origin !== window.location.origin) return;
  if (!event.data || event.data.type !== "mip:short_lead_submit") return;
  try {
    const encoded = btoa(unescape(encodeURIComponent(JSON.stringify(event.data.payload))));
    const url = new URL(window.location.pathname || "/", window.location.origin);
    url.searchParams.set("inquiry_data", encoded);
    window.location.assign(url.toString());
  } catch (err) {
    console.error("MIP short lead bridge failed:", err);
  }
});
</script>
"""

CUSTOMER_CSS = """
<style>
.stApp { background: #F7F9FC; }
[data-testid="stSidebar"] { display: none; }
[data-testid="stSidebarCollapsedControl"] { display: none; }
header[data-testid="stHeader"] { opacity: 0; pointer-events: none; }
.block-container { padding-top: 0; padding-left: 0; padding-right: 0; max-width: 100%; }
.main .block-container { padding-top: 0; }
.stApp h1, .stApp h2, .stApp h3 { color: inherit; }
</style>
"""


def _calendly_embed_html(*, base_url: str, name: str, email: str) -> str:
    """Inline Calendly widget with prospect prefill."""
    sep = "&" if "?" in base_url else "?"
    url = f"{base_url}{sep}name={quote(name)}&email={quote(email)}"
    return f"""
    <link href="https://assets.calendly.com/assets/external/widget.css" rel="stylesheet">
    <script src="https://assets.calendly.com/assets/external/widget.js" type="text/javascript" async></script>
    <div style="max-width:800px;margin:0 auto;padding:0 1rem 2rem;font-family:Segoe UI,system-ui,sans-serif;">
      <div style="text-align:center;padding:2rem 1rem 1.25rem;background:linear-gradient(135deg,#001A3D,#002F6C);
        border-radius:12px 12px 0 0;color:#fff;border-bottom:4px solid #C4A962;">
        <div style="font-size:2.5rem;margin-bottom:0.5rem;">✅</div>
        <h2 style="margin:0 0 0.5rem;font-size:1.5rem;">Thank You, {html_mod.escape(name)}!</h2>
        <p style="opacity:0.92;font-size:1rem;line-height:1.55;max-width:480px;margin:0 auto;">
          Jake will personally review your information and get back to you within 24 hours.
        </p>
      </div>
      <div style="background:#fff;border:1px solid #D4DCE6;border-top:none;padding:1.25rem 1rem 0;border-radius:0 0 12px 12px;">
        <p style="text-align:center;color:#002F6C;font-weight:700;margin-bottom:0.75rem;">
          Book your consultation now — pick a time that works for you
        </p>
        <div class="calendly-inline-widget" data-url="{url}"
             style="min-width:300px;height:680px;"></div>
      </div>
      <p style="text-align:center;font-size:0.8rem;color:#5A6B7D;margin-top:1rem;line-height:1.5;">
        Jake Cornell, NPN 20476670<br>
        <a href="tel:3157832482" style="color:#002F6C;">(315) 783-2482</a> ·
        <a href="mailto:jcornell@financialguide.com" style="color:#002F6C;">jcornell@financialguide.com</a>
      </p>
    </div>
    """


def _thank_you_simple() -> str:
    return """
    <div style="max-width:640px;margin:3rem auto;padding:2.5rem 2rem;background:#fff;
    border-radius:16px;border:1px solid #D4DCE6;text-align:center;border-bottom:4px solid #C4A962;">
      <div style="font-size:3rem;margin-bottom:0.75rem;">✅</div>
      <h2 style="color:#002F6C;margin:0 0 1rem;">Thank You!</h2>
      <p style="color:#1A2B3C;font-size:1.1rem;line-height:1.65;margin:0 0 1rem;">
        Jake will personally review your information and get back to you within 24 hours.
      </p>
      <p style="color:#5A6B7D;font-size:0.88rem;margin:0;">
        To enable instant booking, add your Calendly link as <code>CALENDLY_URL</code> in secrets.
      </p>
    </div>
    """


def _decode_param(param: str) -> dict[str, Any]:
    decoded = base64.b64decode(param)
    payload = json.loads(decoded.decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Submission payload must be a JSON object.")
    return payload


def _process_submission(form_payload: dict[str, Any]) -> None:
    try:
        inquiry = ShortLeadCreate.model_validate(form_payload)
    except ValidationError as exc:
        st.error("Please correct the following and resubmit:")
        for err in exc.errors():
            loc = " → ".join(str(x) for x in err.get("loc", []))
            st.write(f"- **{loc}:** {err.get('msg', 'invalid')}")
        return
    except Exception as exc:
        st.error(str(exc))
        return

    try:
        with get_session() as db:
            lead = create_short_lead(db, inquiry, actor="landing_page")
            response = short_lead_to_response(lead)
    except ValueError as exc:
        st.warning(str(exc))
        st.session_state["submission_success"] = {"name": form_payload.get("full_name", ""), "email": form_payload.get("email", "")}
        st.query_params.clear()
        st.rerun()
        return
    except Exception as exc:
        st.error("We could not save your request. Please try again in a few minutes.")
        st.caption(f"Details: {exc}")
        return

    st.session_state["submission_success"] = {
        "id": response.id,
        "name": response.full_name,
        "email": response.email,
    }
    st.query_params.clear()
    st.rerun()


def render() -> None:
    ensure_db()
    st.markdown(CUSTOMER_CSS, unsafe_allow_html=True)

    success = st.session_state.get("submission_success")
    if success:
        settings = get_settings()
        calendly = (settings.calendly_url or "").strip()
        name = success.get("name", "") if isinstance(success, dict) else ""
        email = success.get("email", "") if isinstance(success, dict) else ""

        if calendly:
            components.html(
                _calendly_embed_html(base_url=calendly, name=name, email=email),
                height=820,
                scrolling=True,
            )
        else:
            st.markdown(_thank_you_simple(), unsafe_allow_html=True)
        st.stop()

    inquiry_param = st.query_params.get("inquiry_data")
    if inquiry_param:
        submission_key = hashlib.sha256(inquiry_param.encode("utf-8")).hexdigest()
        if st.session_state.get("processed_inquiry_key") != submission_key:
            st.session_state["processed_inquiry_key"] = submission_key
            with st.spinner("Submitting your request…"):
                try:
                    form_payload = _decode_param(inquiry_param)
                except Exception as exc:
                    st.error("Could not read your submission. Please try again.")
                    st.caption(f"Details: {exc}")
                    st.query_params.clear()
                    st.stop()
                _process_submission(form_payload)
        st.stop()

    st.html(SUBMIT_BRIDGE_JS, unsafe_allow_javascript=True)
    components.html(load_landing_html(), height=2400, scrolling=True)


render()