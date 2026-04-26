from __future__ import annotations

import html
from pathlib import Path
from typing import Any, Dict, Optional

import streamlit as st

from collection_playlists.ui.audio_player import render_track_player


def _track_title(track: Dict[str, Any]) -> str:
    ap = track.get("absolute_path")
    if ap:
        return Path(str(ap)).stem
    return str(track.get("relative_path") or "Track")


def format_track_subtitle(track: Dict[str, Any]) -> str:
    kh = (track.get("key") or {}).get("krumhansl") or {}
    cls = track.get("classifiers") or {}
    dance = (cls.get("danceability_mean") or [0.0])[0]
    vocal = (cls.get("voice_instrumental_mean") or [0.0, 0.0])[1]
    parts = [
        f"{float(track.get('tempo_bpm') or 0):.0f} BPM",
        f"{kh.get('key', '?')} {kh.get('scale', '?')}",
        f"dance {dance:.2f}",
        f"vocal {vocal:.2f}",
    ]
    return " · ".join(parts)


def render_playlist_track_row(
    *,
    rank: int,
    track: Dict[str, Any],
    subtitle: str,
    match_label: Optional[str] = None,
) -> None:
    """Spotify-inspired row: index, title, meta, then inline audio."""
    title = _track_title(track)
    sub_esc = html.escape(subtitle) if subtitle else ""
    if match_label and sub_esc:
        meta = f"{html.escape(match_label)} · {sub_esc}"
    elif match_label:
        meta = html.escape(match_label)
    else:
        meta = sub_esc
    t_esc = html.escape(title)
    meta_row = f'<div class="cp-track-meta">{meta}</div>' if meta else ""
    st.markdown(
        f"""
<div class="cp-track-shell">
  <div class="cp-track-row">
    <span class="cp-track-idx">{rank}</span>
    <span class="cp-track-play" aria-hidden="true">▶</span>
    <div class="cp-track-text">
      <div class="cp-track-title">{t_esc}</div>
      {meta_row}
    </div>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )
    render_track_player(track, caption=None)
