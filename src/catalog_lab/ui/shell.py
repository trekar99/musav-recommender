from __future__ import annotations

import streamlit as st

BRAND_TITLE = "Catalog lab"
BRAND_SUB = "Descriptor playlists · embedding similarity · CLAP text search"


def render_top_nav() -> None:
    pages = [
        ("overview", "Overview"),
        ("descriptors", "Descriptor search"),
        ("similarity", "Similarity"),
        ("text", "Text search"),
    ]
    top = st.columns([1.35, 1, 1, 1, 1], gap="small")
    with top[0]:
        st.markdown(
            f'<span class="lab-brand">{BRAND_TITLE}</span>'
            f'<p class="lab-tagline">{BRAND_SUB}</p>',
            unsafe_allow_html=True,
        )
    for col, (key, label) in zip(top[1:], pages):
        with col:
            active = st.session_state.active_view == key
            if st.button(
                label,
                key=f"nav_{key}",
                type="primary" if active else "secondary",
                use_container_width=True,
            ):
                st.session_state.active_view = key
                st.rerun()


def render_settings_expander() -> None:
    with st.expander("Data sources & models", expanded=False):
        st.text_input("Descriptors JSONL (one JSON object per track)", key="cfg_descriptors_path")
        st.text_input("Discogs400 labels JSON (400 class names)", key="cfg_labels_path")
        st.text_input("CLAP checkpoint (.pt) for text search", key="cfg_clap_ckpt")
        st.caption(
            "Defaults assume this repository’s `analysis/` and `models/` folders. "
            "Use absolute paths when your catalog or weights live elsewhere. "
            "The Streamlit header (top right) can reopen the app sidebar for built-in settings."
        )
