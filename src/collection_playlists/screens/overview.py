from __future__ import annotations

import streamlit as st

from collection_playlists.services.catalog_loader import count_jsonl_lines


def render_overview() -> None:
    desc_path = st.session_state.cfg_descriptors_path
    line_estimate = count_jsonl_lines(desc_path)

    st.markdown("# Playlist Studio")
    st.markdown(
        "**Build playlists from analysis in seconds.** Filter your catalog, find nearest neighbours, "
        "or search by text—without re-running audio encoding."
    )

    main, side = st.columns((2.35, 1.0), gap="large")

    with main:
        with st.container(border=True):
            st.markdown("##### What this app does")
            st.markdown(
                "- **Descriptors:** Filter by tempo, voice/dance, key, and Discogs400 styles; preview and export **M3U8**.\n"
                "- **Similarity:** Pick one track and find nearest neighbours in **EffNet** or **CLAP** space.\n"
                "- **Text:** Describe a sound in plain English and rank tracks by CLAP match."
            )
            st.caption(
                "Uses one JSONL catalog with precomputed descriptors and vectors. "
                "The Text encoder loads in the background."
            )

    with side:
        with st.container(border=True):
            st.markdown("##### Your catalog")
            if line_estimate:
                st.metric("Tracks in catalog (approx.)", f"{line_estimate:,}")
                st.caption("Line count for your configured descriptors file.")
            else:
                st.warning("Add a descriptors JSONL to get started.")
            st.markdown("##### Configuration")
            st.caption(
                "Point Streamlit at your data with `COLLECTION_PLAYLISTS_*` env vars (or use the repo defaults). "
                "Full setup: **README**."
            )

    st.divider()
    st.markdown("##### Jump in")
    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        with st.container(border=True):
            st.markdown("**Descriptors**")
            st.caption("Shape a playlist with filters, then export.")
            if st.button("Open Descriptors", key="home_open_desc", use_container_width=True):
                st.session_state.active_view = "descriptors"
                st.rerun()

    with c2:
        with st.container(border=True):
            st.markdown("**Similarity**")
            st.caption("Explore “more like this” from any track.")
            if st.button("Open Similarity", key="home_open_sim", use_container_width=True):
                st.session_state.active_view = "similarity"
                st.rerun()

    with c3:
        with st.container(border=True):
            st.markdown("**Text**")
            st.caption("Search by mood or description in plain English.")
            if st.button("Open Text", key="home_open_txt", use_container_width=True):
                st.session_state.active_view = "text"
                st.rerun()
