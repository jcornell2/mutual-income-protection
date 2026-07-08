"""Bidirectional Streamlit component for the HTML intake form."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import streamlit.components.v1 as components

_BRIDGE_DIR = Path(__file__).resolve().parent / "intake_bridge"
_intake_component = components.declare_component(
    "mip_intake_bridge",
    path=str(_BRIDGE_DIR),
)


def render_intake_form(html: str, *, height: int = 2400) -> dict[str, Any] | None:
    """Render intake HTML and return submitted payload dict, if any."""
    result = _intake_component(
        html=html,
        height=height,
        key="mip_intake_form",
        default=None,
    )
    if result is None:
        return None
    if isinstance(result, dict):
        return result
    if isinstance(result, str):
        try:
            parsed = json.loads(result)
        except json.JSONDecodeError:
            return None
        return parsed if isinstance(parsed, dict) else None
    return None