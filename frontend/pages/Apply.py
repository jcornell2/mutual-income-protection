"""Public pre-application intake — no password required."""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

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

CUSTOMER_CSS = """
<style>
.stApp { background: #F5F7FA; }
[data-testid="stSidebar"] { display: none; }
[data-testid="stSidebarCollapsedControl"] { display: none; }
header[data-testid="stHeader"] { opacity: 0; pointer-events: none; }
.block-container { padding-top: 0; padding-left: 0; padding-right: 0; max-width: 100%; }
.main .block-container { padding-top: 0; }
.stApp h1, .stApp h2, .stApp h3 { color: inherit; }
iframe { border: none !important; }
</style>
"""

ensure_db()
st.set_page_config(
    page_title="Start My Protected Application | Mutual Income Protection",
    page_icon="🛡️",
    layout="wide",
)
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

payload = components.html(load_intake_html(), height=2400, scrolling=True)

if not payload:
    st.stop()

if isinstance(payload, str):
    try:
        payload = json.loads(payload)
    except json.JSONDecodeError:
        st.error("Invalid submission format.")
        st.stop()

submission_key = json.dumps(payload, sort_keys=True, default=str)
if st.session_state.get("processed_submission_key") == submission_key:
    st.stop()

if payload.get("date_of_birth") and isinstance(payload["date_of_birth"], str):
    payload["date_of_birth"] = date.fromisoformat(payload["date_of_birth"])

try:
    lead_data = LeadCreate.model_validate(payload)
except ValidationError as exc:
    st.error("Please correct the following and resubmit:")
    for err in exc.errors():
        loc = " → ".join(str(x) for x in err.get("loc", []))
        st.write(f"- **{loc}:** {err.get('msg', 'invalid')}")
    st.stop()
except Exception as exc:
    st.error(str(exc))
    st.stop()

try:
    with get_session() as db:
        lead = create_lead(db, lead_data, actor="public_streamlit")
        response = lead_to_response(lead)
except ValueError as exc:
    st.error(str(exc))
    st.stop()

st.session_state["processed_submission_key"] = submission_key
st.session_state["submission_success"] = {
    "id": response.id,
    "name": response.full_name,
    "score": response.score,
    "tier": response.score_tier,
}
st.rerun()