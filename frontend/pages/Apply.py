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
from frontend.styles import apply_brand, brand_header

ensure_db()
apply_brand("Mutual Income Protection | Pre-Application")

if st.session_state.get("submission_success"):
    success = st.session_state["submission_success"]
    brand_header("Pre-Application Submitted")
    st.success(
        f"Thank you, **{success['name']}**. Your reference ID is **#{success['id']}**.\n\n"
        f"Preliminary score: **{success['score']}/100** ({success['tier']} tier). "
        "A licensed agent will contact you using your stated preference."
    )
    if st.button("Submit another application"):
        st.session_state.pop("submission_success", None)
        st.session_state.pop("processed_submission_key", None)
        st.rerun()
    st.stop()

brand_header("Secure Pre-Application")
st.caption("This form is open to the public. No login required.")

payload = components.html(load_intake_html(), height=1600, scrolling=True)

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