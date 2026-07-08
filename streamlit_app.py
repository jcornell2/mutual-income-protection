"""Streamlit Cloud entry — public site first, Admin optional."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from frontend.secrets_bootstrap import bootstrap_env

    bootstrap_env()
except Exception:
    pass

st.set_page_config(
    page_title="Mutual Income Protection",
    page_icon="🛡️",
    layout="wide",
)

home = st.Page(
    "frontend/home.py",
    title="Home",
    icon="🏠",
    default=True,
)
# Full application form — admin/internal only (not in public navigation)
apply = st.Page(
    "frontend/pages/Apply.py",
    title="Apply",
    icon="📝",
    url_path="Apply",
)
admin = st.Page(
    "frontend/pages/Admin.py",
    title="Admin",
    icon="🔒",
    url_path="Admin",
)

pg = st.navigation([home, admin, apply], position="hidden")
pg.run()