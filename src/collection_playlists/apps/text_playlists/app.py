"""
Standalone: CLAP text-to-audio embedding search (no hub navigation).

    PYTHONPATH=src streamlit run src/collection_playlists/apps/text_playlists/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[3]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import streamlit as st

from collection_playlists.services.catalog_loader import init_session_defaults
from collection_playlists.screens.text_search import render_text_search_screen
from collection_playlists.ui.theme import inject_theme

st.set_page_config(
    page_title="Playlist Studio · Text",
    page_icon="♪",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_theme()
init_session_defaults()
st.caption("Text search loads its encoder once; progress appears only in this view.")
render_text_search_screen()
