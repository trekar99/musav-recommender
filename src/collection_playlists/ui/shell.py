from __future__ import annotations

import streamlit as st

BRAND_TITLE = "Playlist Studio"
BRAND_SUB = "Descriptors · similarity · text search"


def render_top_nav() -> None:
    pages = [
        ("overview", "Overview"),
        ("descriptors", "Descriptors"),
        ("similarity", "Similarity"),
        ("text", "Text"),
    ]
    top = st.columns([1.55, 1, 1, 1, 1], gap="small")
    with top[0]:
        st.markdown(
            f'<div class="cp-brand">{BRAND_TITLE}</div>'
            f'<div class="cp-tagline">{BRAND_SUB}</div>',
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
