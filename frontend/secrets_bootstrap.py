"""Map Streamlit Cloud secrets into os.environ before app settings load."""

from __future__ import annotations

import os

import streamlit as st


def _flatten_secrets(prefix: str, value: object) -> list[tuple[str, str]]:
    if isinstance(value, dict):
        pairs: list[tuple[str, str]] = []
        for key, nested in value.items():
            nested_prefix = f"{prefix}{key}." if prefix else f"{key}."
            pairs.extend(_flatten_secrets(nested_prefix, nested))
        return pairs
    return [(prefix.rstrip("."), str(value))]


def bootstrap_env() -> None:
    try:
        for key, value in st.secrets.items():
            for secret_key, secret_value in _flatten_secrets(str(key), value):
                env_key = secret_key.upper().replace(".", "_")
                if env_key not in os.environ or not os.environ[env_key]:
                    os.environ[env_key] = secret_value
    except (FileNotFoundError, AttributeError, RuntimeError, KeyError):
        pass

    try:
        from app.config import get_settings

        get_settings.cache_clear()
    except Exception:
        pass