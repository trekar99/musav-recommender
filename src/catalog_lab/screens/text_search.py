from __future__ import annotations

import numpy as np
import streamlit as st

from domain.similarity import top_k_indices
from services.catalog_loader import load_catalog_bundle
from services.clap_text import embed_text_query, get_clap_module
from ui.audio_player import render_track_player


def render_text_search_screen() -> None:
    st.header("Text search (CLAP)")
    st.caption("Describe the music; CLAP text embeddings rank against stored `clap_mean` vectors.")

    descriptors_path = st.session_state.cfg_descriptors_path
    labels_path = st.session_state.cfg_labels_path
    clap_ckpt = st.session_state.cfg_clap_ckpt

    try:
        tracks, _eff, _clap, _eu, clap_unit = load_catalog_bundle(descriptors_path, labels_path)
    except Exception as exc:
        st.error(f"Could not load catalog: {exc}")
        return

    with st.container(border=True):
        query = st.text_area(
            "Describe the music you want",
            height=110,
            placeholder="e.g. warm analog techno with dub chords and tape saturation…",
        )
        run = st.button("Search", type="primary")

    if not run:
        st.info("Enter a query and press **Search**.")
        return

    if not query.strip():
        st.warning("Please enter a non-empty text query.")
        return

    try:
        model = get_clap_module(clap_ckpt)
    except Exception as exc:
        st.error(str(exc))
        return

    with st.spinner("Embedding text and scoring the catalog…"):
        text_unit = embed_text_query(model, query)
        text_unit64 = np.asarray(text_unit, dtype=np.float64).reshape(-1)
        scores = (clap_unit.astype(np.float64) @ text_unit64).astype(np.float64)
        hits = top_k_indices(scores, k=10)

    st.subheader("Top matches")
    for rank, (j, score) in enumerate(hits, start=1):
        tr = tracks[j]
        with st.container(border=True):
            st.markdown(f"**{rank}.** `{tr.get('relative_path','')}` · cos **{score:.4f}**")
            render_track_player(tr)
