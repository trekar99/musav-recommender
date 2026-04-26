from __future__ import annotations

import numpy as np
import streamlit as st

from domain.similarity import top_k_indices
from services.catalog_loader import load_catalog_bundle
from ui.audio_player import render_track_player


def render_similarity_screen() -> None:
    st.header("Track similarity")
    st.caption("Query by track ID (`relative_path`). Compare Effnet vs CLAP cosine neighbours.")

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
        filter_q = st.text_input("Filter track IDs", placeholder="Substring of relative_path…")
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

    st.subheader("Query")
    st.code(query_id, language=None)
    render_track_player(tracks[qidx], caption="Query track")

    st.divider()
    left, right = st.columns(2, gap="large")

    with left:
        st.markdown("#### Effnet–Discogs (1280-d)")
        for rank, (j, score) in enumerate(eff_hits, start=1):
            tr = tracks[j]
            with st.container(border=True):
                st.markdown(f"**{rank}.** `{tr.get('relative_path','')}` · cos **{score:.4f}**")
                render_track_player(tr)

    with right:
        st.markdown("#### CLAP audio (512-d)")
        for rank, (j, score) in enumerate(clap_hits, start=1):
            tr = tracks[j]
            with st.container(border=True):
                st.markdown(f"**{rank}.** `{tr.get('relative_path','')}` · cos **{score:.4f}**")
                render_track_player(tr)
