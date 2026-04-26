"""
Standalone: Effnet vs CLAP embedding neighbours (no hub navigation).

    PYTHONPATH=src streamlit run src/collection_playlists/apps/track_similarity/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[3]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import streamlit as st

from collection_playlists.services.catalog_loader import init_session_defaults
from collection_playlists.screens.similarity import render_similarity_screen
from collection_playlists.ui.theme import inject_theme

st.set_page_config(
    page_title="Playlist Studio · Similarity",
    page_icon="♪",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_theme()
init_session_defaults()
st.caption("Standalone · run `python main.py` for the full hub.")
render_similarity_screen()
