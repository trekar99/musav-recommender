from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import streamlit as st


def render_track_player(track: Dict[str, Any], caption: str | None = None) -> None:
    ap = track.get("absolute_path")
    if not ap:
        st.warning("Missing absolute_path for this track.")
        return
    path = Path(str(ap))
    if not path.is_file():
        st.error(f"Audio file not found:\n`{path}`")
        return
    try:
        data = path.read_bytes()
    except OSError as exc:
        st.error(f"Could not read audio file: {exc}")
        return

    ext = path.suffix.lower().lstrip(".") or "mpeg"
    fmt = f"audio/{ext}" if ext in {"wav", "flac", "ogg", "opus"} else "audio/mpeg"
    st.audio(data, format=fmt)
    if caption:
        st.caption(caption)
