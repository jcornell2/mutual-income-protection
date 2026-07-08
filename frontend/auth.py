"""Admin-only passkey authentication for the CRM."""

from __future__ import annotations

import os

import streamlit as st


def get_admin_passkey() -> str:
    """Read passkey from Streamlit secrets, then environment."""
    try:
        return st.secrets["ADMIN_PASSKEY"]
    except (KeyError, FileNotFoundError, AttributeError):
        pass
    return os.getenv("ADMIN_PASSKEY", "change-me-passkey")


def require_admin() -> bool:
    """Return True when admin is authenticated; otherwise render login gate."""
    if st.session_state.get("mip_admin_authenticated"):
        return True

    st.warning("Admin area — enter your passkey to access the CRM.")
    passkey = st.text_input("Admin Passkey", type="password", key="admin_passkey_input")
    if st.button("Unlock Admin", type="primary", key="admin_unlock_btn"):
        if passkey == get_admin_passkey():
            st.session_state["mip_admin_authenticated"] = True
            st.rerun()
        else:
            st.error("Invalid passkey.")
    return False


def lock_admin() -> None:
    st.session_state.pop("mip_admin_authenticated", None)