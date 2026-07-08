"""Public pre-application intake — no password required."""

from __future__ import annotations

import base64
import hashlib
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

import streamlit as st
import streamlit.components.v1 as components
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from frontend.secrets_bootstrap import bootstrap_env

bootstrap_env()

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from app.schemas import LeadCreate
from app.services import create_lead, lead_to_response
from frontend.db import ensure_db, get_session
from frontend.html_pages import load_intake_html

# Parent-page bridge: iframe cannot navigate Streamlit (sandbox), so the form posts here.
SUBMIT_BRIDGE_JS = """
<script>
window.addEventListener("message", function (event) {
  if (event.origin !== window.location.origin) return;
  if (!event.data || event.data.type !== "mip:lead_submit") return;
  try {
    const encoded = btoa(unescape(encodeURIComponent(JSON.stringify(event.data.payload))));
    const applyPath = window.location.pathname.includes("Apply")
      ? window.location.pathname
      : "/Apply";
    const url = new URL(applyPath, window.location.origin);
    url.searchParams.set("lead_data", encoded);
    window.location.assign(url.toString());
  } catch (err) {
    console.error("MIP submit bridge failed:", err);
  }
});
</script>
"""

CUSTOMER_CSS = """
<style>
.stApp { background: #F5F7FA; }
[data-testid="stSidebar"] { display: none; }
[data-testid="stSidebarCollapsedControl"] { display: none; }
header[data-testid="stHeader"] { opacity: 0; pointer-events: none; }
.block-container { padding-top: 0; padding-left: 0; padding-right: 0; max-width: 100%; }
.main .block-container { padding-top: 0; }
.stApp h1, .stApp h2, .stApp h3 { color: inherit; }
</style>
"""


def _decode_lead_param(param: str) -> dict[str, Any]:
    decoded = base64.b64decode(param)
    payload = json.loads(decoded.decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Submission payload must be a JSON object.")
    return payload


def _process_submission(form_payload: dict[str, Any]) -> None:
    if form_payload.get("date_of_birth") and isinstance(form_payload["date_of_birth"], str):
        form_payload["date_of_birth"] = date.fromisoformat(form_payload["date_of_birth"])

    try:
        lead_data = LeadCreate.model_validate(form_payload)
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
            lead = create_lead(db, lead_data, actor="public_streamlit")
            response = lead_to_response(lead)
    except ValueError as exc:
        st.error(str(exc))
        return
    except Exception as exc:
        st.error(
            "We could not save your application. Confirm ENCRYPTION_KEY is set in Streamlit Secrets."
        )
        st.caption(f"Details: {exc}")
        return

    st.session_state["submission_success"] = {
        "id": response.id,
        "name": response.full_name,
        "score": response.score,
        "tier": response.score_tier,
    }
    st.query_params.clear()
    st.rerun()


ensure_db()
st.markdown(CUSTOMER_CSS, unsafe_allow_html=True)

if st.session_state.get("submission_success"):
    success = st.session_state["submission_success"]
    st.markdown(
        f"""
        <div style="max-width:720px;margin:1.5rem auto;padding:1.5rem;background:#fff;
        border-radius:12px;border:1px solid #D4DCE6;border-bottom:4px solid #C4A962;">
          <h2 style="color:#002F6C;margin:0 0 0.5rem;">Application received</h2>
          <p style="margin:0;color:#1A2B3C;line-height:1.6;">
            Thank you, <strong>{success['name']}</strong>. Reference ID <strong>#{success['id']}</strong>.<br>
            Preliminary score: <strong>{success['score']}/100</strong> ({success['tier']} tier).<br>
            Jacob Cornell (NPN 20476670) will contact you using your stated preference.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Submit another application", type="primary"):
        st.session_state.pop("submission_success", None)
        st.session_state.pop("processed_submission_key", None)
        st.rerun()
    st.stop()

lead_data_param = st.query_params.get("lead_data")
if lead_data_param:
    submission_key = hashlib.sha256(lead_data_param.encode("utf-8")).hexdigest()
    if st.session_state.get("processed_submission_key") != submission_key:
        st.session_state["processed_submission_key"] = submission_key
        with st.spinner("Processing your application…"):
            try:
                form_payload = _decode_lead_param(lead_data_param)
            except Exception as exc:
                st.error("Could not read your submission. Please try again.")
                st.caption(f"Details: {exc}")
                st.query_params.clear()
                st.stop()
            _process_submission(form_payload)
    st.stop()

# Iframe: step-navigation JS runs reliably. Submit uses postMessage → bridge above.
st.html(SUBMIT_BRIDGE_JS, unsafe_allow_javascript=True)
components.html(load_intake_html(), height=1800, scrolling=True)