from __future__ import annotations

import numpy as np
import streamlit as st

from collection_playlists.domain.similarity import top_k_indices
from collection_playlists.services.catalog_loader import load_catalog_bundle
from collection_playlists.ui.playlist_row import format_track_subtitle, render_playlist_track_row
from collection_playlists.ui.audio_player import render_track_player


def render_similarity_screen() -> None:
    st.markdown("### Similarity")
    st.caption("Pick a query track (`relative_path`), then choose which embedding defines “nearby”.")

    descriptors_path = st.session_state.cfg_descriptors_path
    labels_path = st.session_state.cfg_labels_path

    try:
        tracks, _eff, _clap, eff_unit, clap_unit = load_catalog_bundle(descriptors_path, labels_path)
    except Exception as exc:
        st.error(f"Could not load catalog: {exc}")
        return

    ids = [str(t.get("relative_path", "")) for t in tracks]
    id_to_idx = {rid: i for i, rid in enumerate(ids)}

    with st.container(border=True):
        filter_q = st.text_input("Filter IDs", placeholder="substring of relative_path…")
        opts = [rid for rid in ids if filter_q.strip().lower() in rid.lower()]
        if not opts:
            st.warning("No track IDs match the filter.")
            return
        query_id = st.selectbox("Query track", options=opts, index=0)

    qidx = id_to_idx[query_id]
    q_eff = eff_unit[qidx]
    q_clap = clap_unit[qidx]

    eff_scores = (eff_unit @ q_eff).astype(np.float64)
    clap_scores = (clap_unit @ q_clap).astype(np.float64)

    eff_hits = top_k_indices(eff_scores, k=11, exclude=[qidx])[:10]
    clap_hits = top_k_indices(clap_scores, k=11, exclude=[qidx])[:10]

    st.caption("Now playing")
    st.code(query_id, language=None)
    render_track_player(tracks[qidx], caption="Query")

    st.divider()
    mode = st.radio(
        "Neighbour list",
        options=["effnet", "clap"],
        format_func=lambda x: "Effnet" if x == "effnet" else "CLAP",
        horizontal=True,
        key="similarity_backend",
    )

    hits = eff_hits if mode == "effnet" else clap_hits

    for rank, (j, score) in enumerate(hits, start=1):
        tr = tracks[j]
        render_playlist_track_row(
            rank=rank,
            track=tr,
            subtitle=format_track_subtitle(tr),
            match_label=f"similarity {score:.3f}",
        )
