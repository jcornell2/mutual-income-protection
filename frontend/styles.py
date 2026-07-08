"""Shared Streamlit styling for Mutual Income Protection."""

from __future__ import annotations

import streamlit as st

from app.config import APP_NAME

BRAND_CSS = """
<style>
.stApp { background:#F5F7FA; }
[data-testid="stSidebar"] { background:linear-gradient(180deg,#001E45,#002F6C); }
[data-testid="stSidebar"] * { color:#fff !important; }
h1,h2,h3 { color:#002F6C !important; }
.brand-header {
  background:linear-gradient(135deg,#001E45,#002F6C);
  color:#fff; padding:1rem 1.25rem;
  border-radius:8px; border-bottom:4px solid #C4A962; margin-bottom:1rem;
}
</style>
"""


def apply_brand(page_title: str | None = None) -> None:
    title = page_title or APP_NAME
    st.set_page_config(page_title=title, page_icon="🛡️", layout="wide")
    st.markdown(BRAND_CSS, unsafe_allow_html=True)


def brand_header(subtitle: str = "") -> None:
    sub = f'<p style="margin:0.25rem 0 0;opacity:0.9;">{subtitle}</p>' if subtitle else ""
    st.markdown(
        f'<div class="brand-header"><h1 style="color:#fff!important;margin:0;font-size:1.4rem;">'
        f"{APP_NAME}</h1>{sub}</div>",
        unsafe_allow_html=True,
    )