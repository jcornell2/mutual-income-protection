"""Load secrets from .streamlit/secrets.toml (repo) and Streamlit Cloud UI."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
PROJECT_SECRETS = ROOT / ".streamlit" / "secrets.toml"

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
    "CALENDLY_URL",
)


def _flatten_secrets(prefix: str, value: object) -> list[tuple[str, str]]:
    if isinstance(value, dict):
        pairs: list[tuple[str, str]] = []
        for key, nested in value.items():
            nested_prefix = f"{prefix}{key}." if prefix else f"{key}."
            pairs.extend(_flatten_secrets(nested_prefix, nested))
        return pairs
    return [(prefix.rstrip("."), str(value))]


def _load_toml_file(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        import toml

        data = toml.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _load_streamlit_secrets() -> dict[str, Any]:
    try:
        import streamlit as st

        if not st.secrets.load_if_toml_exists():
            return {}
        data = st.secrets.to_dict()
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _merged_secrets() -> dict[str, Any]:
    """Project secrets.toml first; Streamlit Cloud UI secrets override."""
    merged: dict[str, Any] = {}
    merged.update(_load_toml_file(PROJECT_SECRETS))
    cloud = _load_streamlit_secrets()
    for key, value in cloud.items():
        if value is not None and value != "" and value != {}:
            merged[key] = value
    return merged


def _read_from_map(secrets_map: dict[str, Any], key: str) -> str:
    if key in secrets_map:
        value = secrets_map[key]
        if value is not None and not isinstance(value, dict):
            text = str(value).strip()
            if text:
                return text

    target = key.upper()
    for secret_key, value in secrets_map.items():
        if str(secret_key).upper() != target or isinstance(value, dict):
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def _apply_secrets_to_environ(secrets_map: dict[str, Any]) -> None:
    for key in _STREAMLIT_SECRET_KEYS:
        text = _read_from_map(secrets_map, key)
        if text:
            os.environ[key] = text

    for key, value in secrets_map.items():
        for secret_key, secret_value in _flatten_secrets(str(key), value):
            env_key = secret_key.upper().replace(".", "_")
            text = str(secret_value).strip()
            if text:
                os.environ[env_key] = text


def _find_encryption_key() -> str:
    key = os.environ.get("ENCRYPTION_KEY", "").strip()
    if key:
        return key

    secrets_map = _merged_secrets()
    key = _read_from_map(secrets_map, "ENCRYPTION_KEY")
    if key:
        return key

    for env_key, env_val in os.environ.items():
        if env_key.upper() == "ENCRYPTION_KEY" and str(env_val).strip():
            return str(env_val).strip()
    return ""


def bootstrap_env() -> None:
    try:
        _apply_secrets_to_environ(_merged_secrets())
    except Exception:
        pass
    try:
        from app.config import get_settings

        get_settings.cache_clear()
    except Exception:
        pass


def encryption_key_configured() -> bool:
    bootstrap_env()
    return bool(_find_encryption_key())