from __future__ import annotations

import streamlit as st

from collection_playlists.services.catalog_loader import count_jsonl_lines


def render_overview() -> None:
    desc_path = st.session_state.cfg_descriptors_path
    line_estimate = count_jsonl_lines(desc_path)

    st.markdown(
        """
<div class="cp-hero">
  <h1>Playlist Studio</h1>
  <p class="lead">
    One JSONL catalog: filter by musical attributes, find similar tracks, or search by description.
    Data paths come from the environment before startup.
  </p>
</div>
        """,
        unsafe_allow_html=True,
    )

    if line_estimate:
        st.markdown(
            f'<div class="cp-muted">{line_estimate:,} lines in descriptors file (quick count).</div>',
            unsafe_allow_html=True,
        )
    else:
        st.warning(
            "Descriptors file missing or empty. Set **COLLECTION_PLAYLISTS_DESCRIPTORS_JSONL** "
            "or keep the default `analysis/descriptors.jsonl` layout."
        )

    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        with st.container(border=True):
            st.markdown("**Descriptors**")
            st.caption("Tempo, voice, dance, key, Discogs400 styles; M3U8 export.")
            if st.button("Open", key="home_open_desc", use_container_width=True):
                st.session_state.active_view = "descriptors"
                st.rerun()

    with c2:
        with st.container(border=True):
            st.markdown("**Similarity**")
            st.caption("Effnet vs CLAP neighbours for one track ID.")
            if st.button("Open", key="home_open_sim", use_container_width=True):
                st.session_state.active_view = "similarity"
                st.rerun()

    with c3:
        with st.container(border=True):
            st.markdown("**Text**")
            st.caption("CLAP text vs stored `clap_mean` vectors.")
            if st.button("Open", key="home_open_txt", use_container_width=True):
                st.session_state.active_view = "text"
                st.rerun()
