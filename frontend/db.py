"""Database bootstrap for Streamlit deployment."""

from __future__ import annotations

from app.database import SessionLocal, init_db

_db_ready = False


def ensure_db() -> None:
    global _db_ready
    if not _db_ready:
        init_db()
        _db_ready = True


def get_session():
    ensure_db()
    return SessionLocal()