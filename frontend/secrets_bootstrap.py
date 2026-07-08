"""Map Streamlit Cloud secrets into os.environ before app settings load."""

from __future__ import annotations

import os

import streamlit as st

# Top-level keys expected in Streamlit Cloud → Secrets (TOML).
_STREAMLIT_SECRET_KEYS = (
    "ENCRYPTION_KEY",
    "ADMIN_PASSKEY",
    "ADMIN_API_KEY",
    "DATABASE_URL",
    "SMTP_ENABLED",
    "SMTP_HOST",
    "SMTP_PORT",
    "SMTP_USER",
    "SMTP_PASSWORD",
    "SMTP_FROM_EMAIL",
    "ALERT_EMAIL_TO",
    "ORGANIZATION_NAME",
)


def _flatten_secrets(prefix: str, value: object) -> list[tuple[str, str]]:
    if isinstance(value, dict):
        pairs: list[tuple[str, str]] = []
        for key, nested in value.items():
            nested_prefix = f"{prefix}{key}." if prefix else f"{key}."
            pairs.extend(_flatten_secrets(nested_prefix, nested))
        return pairs
    return [(prefix.rstrip("."), str(value))]


def _apply_streamlit_secrets() -> None:
    """Copy st.secrets into os.environ. Streamlit secrets always win."""
    try:
        for key in _STREAMLIT_SECRET_KEYS:
            try:
                value = st.secrets[key]
            except (KeyError, TypeError):
                continue
            if value is None:
                continue
            text = str(value).strip()
            if text:
                os.environ[key] = text

        for key, value in st.secrets.items():
            for secret_key, secret_value in _flatten_secrets(str(key), value):
                env_key = secret_key.upper().replace(".", "_")
                text = str(secret_value).strip()
                if text:
                    os.environ[env_key] = text
    except (FileNotFoundError, AttributeError, RuntimeError, KeyError):
        pass


def bootstrap_env() -> None:
    _apply_streamlit_secrets()
    try:
        from app.config import get_settings

        get_settings.cache_clear()
    except Exception:
        pass


def encryption_key_configured() -> bool:
    """True when a Fernet key is available from secrets or environment."""
    bootstrap_env()
    key = os.environ.get("ENCRYPTION_KEY", "").strip()
    if key:
        return True
    try:
        return bool(str(st.secrets["ENCRYPTION_KEY"]).strip())
    except Exception:
        return False