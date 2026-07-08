"""Privacy utilities: encryption, audit logging, and data minimization."""

from __future__ import annotations

import hashlib
import os
import logging
import re
from datetime import datetime, timezone
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import AuditLog

logger = logging.getLogger(__name__)
_EMAIL_RE = re.compile(r"[^@]+@[^@]+\.[^@]+")
_PHONE_RE = re.compile(r"\d{3,}")
_SSN_RE = re.compile(r"\b\d{3}-?\d{2}-?\d{4}\b")


class PrivacyError(Exception):
    pass


def _resolve_encryption_key() -> str:
    try:
        from frontend.secrets_bootstrap import bootstrap_env

        bootstrap_env()
    except Exception:
        pass

    key = get_settings().encryption_key.strip()
    if not key:
        key = os.environ.get("ENCRYPTION_KEY", "").strip()
    if not key:
        try:
            import streamlit as st

            key = str(st.secrets["ENCRYPTION_KEY"]).strip()
        except Exception:
            key = ""
    return key


def _get_fernet() -> Fernet:
    key = _resolve_encryption_key()
    if not key:
        raise PrivacyError(
            "ENCRYPTION_KEY is not set. Add it in Streamlit Cloud → App settings → Secrets."
        )
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_field(value: str | None) -> str | None:
    if value is None or value == "":
        return None
    return _get_fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_field(value: str | None) -> str | None:
    if value is None or value == "":
        return None
    try:
        return _get_fernet().decrypt(value.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise PrivacyError("Unable to decrypt stored data. Check ENCRYPTION_KEY.") from exc


def hash_identifier(value: str) -> str:
    """One-way hash for deduplication without storing plaintext."""
    return hashlib.sha256(value.strip().lower().encode("utf-8")).hexdigest()


def mask_pii(text: str) -> str:
    """Redact PII from log messages."""
    masked = _EMAIL_RE.sub("[EMAIL_REDACTED]", text)
    masked = _PHONE_RE.sub("[PHONE_REDACTED]", masked)
    return _SSN_RE.sub("[SSN_REDACTED]", masked)


def mask_ssn(ssn: str | None) -> str:
    """Return last-4 only for admin display."""
    if not ssn:
        return ""
    digits = re.sub(r"\D", "", ssn)
    if len(digits) != 9:
        return "***-**-****"
    return f"***-**-{digits[-4:]}"


def normalize_ssn(ssn: str) -> str:
    digits = re.sub(r"\D", "", ssn.strip())
    if len(digits) != 9:
        raise ValueError("SSN must be 9 digits.")
    return f"{digits[:3]}-{digits[3:5]}-{digits[5:]}"


def safe_log(level: int, message: str, *args: Any) -> None:
    logger.log(level, mask_pii(message), *args)


def log_audit(
    db: Session,
    *,
    action: str,
    entity_type: str,
    entity_id: int | None = None,
    actor: str = "system",
    details: str | None = None,
    ip_address: str | None = None,
) -> None:
    entry = AuditLog(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        actor=actor,
        details=mask_pii(details) if details else None,
        ip_address=ip_address,
        created_at=datetime.now(timezone.utc),
    )
    db.add(entry)
    db.commit()


def anonymize_lead_record(lead_data: dict[str, Any]) -> dict[str, Any]:
    """Return a privacy-safe export row with masked contact fields."""
    return {
        **lead_data,
        "full_name": "REDACTED",
        "email": "REDACTED",
        "phone": "REDACTED",
        "notes": "REDACTED" if lead_data.get("notes") else None,
    }