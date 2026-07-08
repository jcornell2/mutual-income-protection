"""Admin CRM — password protected."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from frontend.secrets_bootstrap import bootstrap_env

bootstrap_env()

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from frontend.auth import lock_admin, require_admin
from frontend.crm import render_crm_page
from frontend.db import ensure_db
from frontend.styles import apply_brand, brand_header

ensure_db()
apply_brand("Mutual Income Protection | Admin CRM")

if not require_admin():
    st.stop()

brand_header("Admin CRM")

with st.sidebar:
    if st.button("Lock Admin"):
        lock_admin()
        st.rerun()

render_crm_page()