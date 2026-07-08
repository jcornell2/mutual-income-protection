"""Customer-facing landing page."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from frontend.secrets_bootstrap import bootstrap_env

bootstrap_env()

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from frontend.db import ensure_db
from frontend.html_pages import load_landing_html

CUSTOMER_CSS = """
<style>
.stApp { background: #F4F6F9; }
[data-testid="stSidebar"] { display: none; }
[data-testid="stSidebarCollapsedControl"] { display: none; }
header[data-testid="stHeader"] { opacity: 0; pointer-events: none; }
.block-container { padding-top: 0; padding-left: 0; padding-right: 0; max-width: 100%; }
.main .block-container { padding-top: 0; }
/* Do not let admin CRM styles override the public landing page */
.stApp h1, .stApp h2, .stApp h3 { color: inherit; }
</style>
"""


def render() -> None:
    ensure_db()
    st.set_page_config(
        page_title="Mutual Income Protection | Home",
        page_icon="🛡️",
        layout="wide",
    )
    st.markdown(CUSTOMER_CSS, unsafe_allow_html=True)
    st.html(load_landing_html(), width="stretch")


render()