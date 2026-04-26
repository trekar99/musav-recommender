from __future__ import annotations

import numpy as np
import streamlit as st

from collection_playlists.domain.similarity import top_k_indices
from collection_playlists.services.catalog_loader import load_catalog_bundle
from collection_playlists.services.clap_text import embed_text_query, get_clap_module
from collection_playlists.ui.playlist_row import format_track_subtitle, render_playlist_track_row


def _ensure_text_encoder(clap_ckpt: str):
    """
    Load CLAP only inside the Text view, with a small progress strip (not a blocking app-wide wait).

    The checkpoint is always a local path (download once via README / model_conf.sh, then point
    COLLECTION_PLAYLISTS_CLAP_CKPT at the .pt file).
    """
    if st.session_state.get("text_encoder_ready"):
        return get_clap_module(clap_ckpt)

    st.markdown(
        """
<div class="cp-load-panel">
  <p><strong>Preparing text search</strong> — loading the CLAP weights from disk (one time per session).</p>
  <div class="cp-indeterminate"><div></div></div>
</div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(
        "The model is not streamed from the app; keep the `.pt` on your machine and set "
        "`COLLECTION_PLAYLISTS_CLAP_CKPT` if it is not in `models/`."
    )
    try:
        get_clap_module(clap_ckpt)
    except Exception as exc:
        st.error(str(exc))
        return None
    st.session_state.text_encoder_ready = True
    st.rerun()
    return None


def render_text_search_screen() -> None:
    st.markdown("### Text search")
    st.caption("Describe what you want; rankings use the same CLAP family as your offline analysis.")

    descriptors_path = st.session_state.cfg_descriptors_path
    labels_path = st.session_state.cfg_labels_path
    clap_ckpt = st.session_state.cfg_clap_ckpt

    try:
        tracks, _eff, _clap, _eu, clap_unit = load_catalog_bundle(descriptors_path, labels_path)
    except Exception as exc:
        st.error(f"Could not load catalog: {exc}")
        return

    model = _ensure_text_encoder(clap_ckpt)
    if model is None:
        return

    with st.container(border=True):
        query = st.text_area(
            "Query",
            height=100,
            placeholder="Describe the sound…",
        )
        run = st.button("Search", type="primary")

    if not run:
        return

    if not query.strip():
        st.warning("Enter a non-empty query.")
        return

    text_unit = embed_text_query(model, query)
    text_unit64 = np.asarray(text_unit, dtype=np.float64).reshape(-1)
    scores = (clap_unit.astype(np.float64) @ text_unit64).astype(np.float64)
    hits = top_k_indices(scores, k=10)

    st.divider()
    st.markdown("##### Matches")
    for rank, (j, score) in enumerate(hits, start=1):
        tr = tracks[j]
        sub = format_track_subtitle(tr)
        render_playlist_track_row(
            rank=rank,
            track=tr,
            subtitle=sub,
            match_label=f"rank score {score:.3f}",
        )
