"""Publish the intake HTML as a static file (avoids oversized component args)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = ROOT / "static"
STATIC_FORM = STATIC_DIR / "apply_form.html"
SOURCE_FORM = ROOT / "app" / "static" / "capture_form.html"


def ensure_apply_form_static() -> str:
    """Write patched intake HTML to /static for iframe loading."""
    from frontend.html_pages import load_intake_html

    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    source_mtime = SOURCE_FORM.stat().st_mtime if SOURCE_FORM.exists() else 0
    if not STATIC_FORM.exists() or STATIC_FORM.stat().st_mtime < source_mtime:
        STATIC_FORM.write_text(load_intake_html(), encoding="utf-8")
    return "/static/apply_form.html"