"""Mutual Income Protection — alternate Streamlit entry (use streamlit_app.py on Cloud)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from frontend.home import render

render()