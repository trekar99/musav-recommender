"""
Collection-agnostic Streamlit UI for browsing analyzed audio catalogs.

Run from the repository root:

    streamlit run src/catalog_lab/app.py

Or:

    python main.py
"""

from __future__ import annotations

import streamlit as st

from services.catalog_loader import init_session_defaults
from screens.descriptors import render_descriptor_screen
from screens.overview import render_overview
from screens.similarity import render_similarity_screen
from screens.text_search import render_text_search_screen
from ui.shell import render_settings_expander, render_top_nav
from ui.theme import inject_theme

st.set_page_config(
    page_title="Catalog lab",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_theme()
init_session_defaults()
render_top_nav()
render_settings_expander()

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
