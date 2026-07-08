"""Map Streamlit Cloud secrets into os.environ before app settings load."""

from __future__ import annotations

import os
from typing import Any

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

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


def _read_secret_value(key: str) -> str:
    try:
        value = st.secrets[key]
    except (KeyError, AttributeError, TypeError, StreamlitSecretNotFoundError):
        return ""
    if value is None or isinstance(value, dict):
        return ""
    return str(value).strip()


def _find_encryption_key_in_secrets() -> str:
    """Return ENCRYPTION_KEY from st.secrets (any casing / nesting)."""
    direct = _read_secret_value("ENCRYPTION_KEY")
    if direct:
        return direct

    try:
        if not st.secrets.load_if_toml_exists():
            return ""
        for key, value in st.secrets.to_dict().items():
            if str(key).upper() == "ENCRYPTION_KEY" and not isinstance(value, dict):
                text = str(value).strip()
                if text:
                    return text
    except (StreamlitSecretNotFoundError, FileNotFoundError, AttributeError, TypeError):
        return ""

    for env_key, env_val in os.environ.items():
        if env_key.upper() == "ENCRYPTION_KEY" and str(env_val).strip():
            return str(env_val).strip()
    return ""


def _apply_streamlit_secrets() -> None:
    """Copy st.secrets into os.environ. Streamlit secrets always win."""
    try:
        st.secrets.load_if_toml_exists()
    except StreamlitSecretNotFoundError:
        return

    try:
        for key in _STREAMLIT_SECRET_KEYS:
            text = _read_secret_value(key)
            if text:
                os.environ[key] = text

        for key, value in st.secrets.items():
            for secret_key, secret_value in _flatten_secrets(str(key), value):
                env_key = secret_key.upper().replace(".", "_")
                text = str(secret_value).strip()
                if text:
                    os.environ[env_key] = text
    except (StreamlitSecretNotFoundError, FileNotFoundError, AttributeError, RuntimeError, KeyError):
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
    return bool(_find_encryption_key_in_secrets())


def secrets_diagnostics() -> dict[str, Any]:
    """Non-sensitive status for troubleshooting Streamlit Cloud Secrets."""
    status: dict[str, Any] = {
        "secrets_file_loaded": False,
        "encryption_key_found": False,
        "top_level_keys": [],
        "parse_error": None,
    }
    try:
        status["secrets_file_loaded"] = bool(st.secrets.load_if_toml_exists())
    except StreamlitSecretNotFoundError as exc:
        status["parse_error"] = str(exc)
        return status
    except Exception as exc:
        status["parse_error"] = str(exc)
        return status

    try:
        status["top_level_keys"] = sorted(str(k) for k in st.secrets.to_dict().keys())
    except Exception as exc:
        status["parse_error"] = str(exc)

    bootstrap_env()
    key = _find_encryption_key_in_secrets()
    status["encryption_key_found"] = bool(key)
    return status