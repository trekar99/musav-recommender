"""
Integrated hub: overview plus top navigation between descriptor, similarity, and text tools.

Run (from repository root)::

    python main.py
    # or:
    PYTHONPATH=src streamlit run src/collection_playlists/apps/integrated/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[3]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import streamlit as st

from collection_playlists.services.catalog_loader import init_session_defaults
from collection_playlists.screens.descriptors import render_descriptor_screen
from collection_playlists.screens.overview import render_overview
from collection_playlists.screens.similarity import render_similarity_screen
from collection_playlists.screens.text_search import render_text_search_screen
from collection_playlists.ui.shell import render_top_nav
from collection_playlists.ui.theme import inject_theme

st.set_page_config(
    page_title="Playlist Studio",
    page_icon="♪",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_theme()
init_session_defaults()
render_top_nav()

st.divider()

view = st.session_state.active_view
if view == "overview":
    render_overview()
elif view == "descriptors":
    render_descriptor_screen()
elif view == "similarity":
    render_similarity_screen()
elif view == "text":
    render_text_search_screen()
else:
    st.session_state.active_view = "overview"
    render_overview()
