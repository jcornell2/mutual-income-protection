"""Map Streamlit Cloud secrets into os.environ before app settings load."""

from __future__ import annotations

import os
from typing import Any

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


def _get_st():
    import streamlit as st

    return st


def _flatten_secrets(prefix: str, value: object) -> list[tuple[str, str]]:
    if isinstance(value, dict):
        pairs: list[tuple[str, str]] = []
        for key, nested in value.items():
            nested_prefix = f"{prefix}{key}." if prefix else f"{key}."
            pairs.extend(_flatten_secrets(nested_prefix, nested))
        return pairs
    return [(prefix.rstrip("."), str(value))]


def _safe_secret_map() -> tuple[dict[str, Any], str | None]:
    """Return secrets as a plain dict; second value is an error hint if read failed."""
    st = _get_st()
    try:
        if not st.secrets.load_if_toml_exists():
            return {}, None
        secrets_map = st.secrets.to_dict()
        if not secrets_map:
            return {}, (
                "Secrets file is empty or contains only comments. "
                "Paste all lines from exports/streamlit-secrets.toml (not just the header)."
            )
        return secrets_map, None
    except Exception as exc:
        return {}, f"Could not read secrets: {exc}"


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


def _find_encryption_key() -> str:
    key = os.environ.get("ENCRYPTION_KEY", "").strip()
    if key:
        return key

    secrets_map, _ = _safe_secret_map()
    key = _read_from_map(secrets_map, "ENCRYPTION_KEY")
    if key:
        return key

    for env_key, env_val in os.environ.items():
        if env_key.upper() == "ENCRYPTION_KEY" and str(env_val).strip():
            return str(env_val).strip()
    return ""


def _apply_streamlit_secrets() -> None:
    secrets_map, _ = _safe_secret_map()
    if not secrets_map:
        return

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


def bootstrap_env() -> None:
    try:
        _apply_streamlit_secrets()
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


def secrets_diagnostics() -> dict[str, Any]:
    status: dict[str, Any] = {
        "secrets_file_loaded": False,
        "encryption_key_found": False,
        "top_level_keys": [],
        "secrets_count": 0,
        "parse_error": None,
    }
    st = _get_st()
    try:
        status["secrets_file_loaded"] = bool(st.secrets.load_if_toml_exists())
        status["secrets_count"] = len(st.secrets)
    except Exception as exc:
        status["parse_error"] = str(exc)
        return status

    secrets_map, read_error = _safe_secret_map()
    status["top_level_keys"] = sorted(str(k) for k in secrets_map.keys())
    status["secrets_count"] = len(secrets_map) or status["secrets_count"]
    if read_error:
        status["parse_error"] = read_error
    elif not secrets_map and status["secrets_file_loaded"]:
        status["parse_error"] = (
            "Secrets file loaded but has 0 keys. Paste every line from "
            "exports/streamlit-secrets.toml — not .env format, not comments only."
        )

    bootstrap_env()
    status["encryption_key_found"] = bool(_find_encryption_key())
    return status