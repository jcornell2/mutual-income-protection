"""Customer-facing landing page."""

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

CUSTOMER_CSS = """
<style>
[data-testid="stSidebar"] { display: none; }
[data-testid="stSidebarCollapsedControl"] { display: none; }
header[data-testid="stHeader"] { opacity: 0; pointer-events: none; }
.block-container { padding-top: 0.5rem; max-width: 100%; }
iframe { border: none !important; }
</style>
"""


def render() -> None:
    ensure_db()
    apply_brand("Mutual Income Protection | Home")
    st.markdown(CUSTOMER_CSS, unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button(
            "Begin Secure Pre-Application →",
            type="primary",
            use_container_width=True,
            key="home_start_apply",
        ):
            st.switch_page("frontend/pages/Apply.py")

    components.html(load_landing_html(), height=2400, scrolling=True)


render()