from __future__ import annotations

import queue
import threading
from typing import Any

import numpy as np
import streamlit as st

from collection_playlists.domain.similarity import top_k_indices
from collection_playlists.services.catalog_loader import load_catalog_bundle
from collection_playlists.services.clap_text import embed_text_query, load_clap_module_from_disk
from collection_playlists.ui.playlist_row import format_track_subtitle, render_playlist_track_row

# CLAP weights load in a daemon thread so the Streamlit script thread stays responsive.
# Do not call ``st.rerun()`` from ``st.fragment`` (or similar); it can trigger ForwardMsg cache errors.
_text_clap_queue: queue.Queue | None = None
_text_clap_worker_ckpt: str | None = None


def _reset_clap_background_load() -> None:
    global _text_clap_queue, _text_clap_worker_ckpt
    _text_clap_queue = None
    _text_clap_worker_ckpt = None


def _start_clap_background_load(ckpt: str) -> None:
    global _text_clap_queue, _text_clap_worker_ckpt
    if _text_clap_worker_ckpt == ckpt and _text_clap_queue is not None:
        return
    _text_clap_worker_ckpt = ckpt
    _text_clap_queue = queue.Queue(maxsize=1)

    def worker() -> None:
        try:
            m = load_clap_module_from_disk(ckpt)
            _text_clap_queue.put(("ok", m))
        except Exception as exc:
            _text_clap_queue.put(("err", str(exc)))

    threading.Thread(target=worker, daemon=True).start()


def _drain_clap_result_queue() -> bool:
    """Apply a finished worker message to session state. Returns whether state changed."""
    global _text_clap_queue
    if _text_clap_queue is None:
        return False
    try:
        kind, payload = _text_clap_queue.get_nowait()
    except queue.Empty:
        return False
    if kind == "err":
        st.session_state["text_clap_model"] = None
        st.session_state["text_clap_error"] = str(payload)
        st.session_state["text_clap_failed"] = True
    else:
        st.session_state["text_clap_model"] = payload
        st.session_state["text_clap_error"] = None
        st.session_state["text_clap_failed"] = False
    return True


def render_text_search_screen() -> None:
    st.markdown("### Text search")
    st.caption(
        "Type a short description; results rank your catalog by cosine match between CLAP text embeddings "
        "and each row's stored `clap_mean` (same model family as your offline export)."
    )

    descriptors_path = st.session_state.cfg_descriptors_path
    labels_path = st.session_state.cfg_labels_path
    clap_ckpt = st.session_state.cfg_clap_ckpt

    try:
        tracks, _eff, _clap, _eu, clap_unit = load_catalog_bundle(descriptors_path, labels_path)
    except Exception as exc:
        st.error(f"Could not load catalog: {exc}")
        return

    _drain_clap_result_queue()

    if st.session_state.get("text_clap_failed"):
        st.error(st.session_state.get("text_clap_error") or "CLAP failed to load.")
        if st.button("Retry load", type="primary", key="text_clap_retry"):
            _reset_clap_background_load()
            for k in ("text_clap_model", "text_clap_error", "text_clap_failed"):
                st.session_state.pop(k, None)
            st.rerun()
        return

    model = st.session_state.get("text_clap_model")
    if model is None:
        _start_clap_background_load(clap_ckpt)
        _drain_clap_result_queue()
        model = st.session_state.get("text_clap_model")

    if model is not None:
        _render_text_search_body(model, tracks, clap_unit)
        return

    st.info(
        "**CLAP weights are loading** (reading the local `.pt`; first load can take a minute). "
        "You can switch to **Overview**, **Descriptors**, or **Similarity**—this page will stay safe to leave. "
        "When the file has finished loading, press **Check load status** or revisit **Text** from the nav."
    )
    st.caption(
        "This app does not download checkpoints. Place the file on disk (for example `models/…pt`) "
        "or point `COLLECTION_PLAYLISTS_CLAP_CKPT` at it before starting Streamlit."
    )
    if st.button("Check load status", type="primary", key="text_clap_check"):
        _drain_clap_result_queue()
        st.rerun()


def _render_text_search_body(model: Any, tracks: list, clap_unit: np.ndarray) -> None:
    with st.container(border=True):
        query = st.text_area(
            "Query",
            height=100,
            placeholder="Describe the sound you want…",
        )
        run = st.button("Search", type="primary", key="text_search_run")

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
            match_label=f"score {score:.3f}",
        )
