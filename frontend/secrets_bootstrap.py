"""Map Streamlit Cloud secrets into os.environ before app settings load."""

from __future__ import annotations

import os

import streamlit as st


def bootstrap_env() -> None:
    try:
        for key, value in st.secrets.items():
            if isinstance(value, dict):
                continue
            env_key = str(key).upper()
            if env_key not in os.environ or not os.environ[env_key]:
                os.environ[env_key] = str(value)
    except (FileNotFoundError, AttributeError, RuntimeError):
        pass