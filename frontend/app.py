"""Mutual Income Protection — public landing page (Streamlit deployment entry)."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from frontend.secrets_bootstrap import bootstrap_env

bootstrap_env()

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from frontend.db import ensure_db
from frontend.html_pages import load_landing_html
from frontend.styles import apply_brand

ensure_db()
apply_brand("Mutual Income Protection | Home")

components.html(load_landing_html(), height=2400, scrolling=True)

with st.sidebar:
    st.markdown("### Quick Links")
    st.page_link("pages/Apply.py", label="Start Pre-Application", icon="📝")
    st.page_link("pages/Admin.py", label="Agent Admin (protected)", icon="🔒")