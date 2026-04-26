from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import streamlit as st

from collection_playlists.config.runtime import (
    runtime_clap_checkpoint,
    runtime_descriptors_path,
    runtime_labels_path,
)


@st.cache_data(show_spinner=False)
def count_jsonl_lines(path_str: str) -> int:
    path = Path(path_str)
    if not path.is_file():
        return 0
    n = 0
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                n += 1
    return n


@st.cache_data(show_spinner=False)
def load_discogs400_labels(labels_json_path: str) -> List[str]:
    path = Path(labels_json_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    classes = data.get("classes")
    if not isinstance(classes, list) or len(classes) != 400:
        raise ValueError("Expected `classes` array of length 400 in labels JSON.")
    return [str(x) for x in classes]


@st.cache_data(show_spinner=False)
def load_catalog_bundle(
    descriptors_path: str,
    labels_json_path: str,
) -> Tuple[List[Dict[str, Any]], np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    dpath = Path(descriptors_path)
    if not dpath.is_file():
        raise FileNotFoundError(f"Descriptors file not found: {dpath}")

    tracks: List[Dict[str, Any]] = []
    eff_rows: List[np.ndarray] = []
    clap_rows: List[np.ndarray] = []

    with dpath.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            emb = row.get("embeddings") or {}
            e = emb.get("discogs_effnet_mean")
            c = emb.get("clap_mean")
            if not e or not c or len(e) != 1280 or len(c) != 512:
                continue
            tracks.append(row)
            eff_rows.append(np.asarray(e, dtype=np.float32))
            clap_rows.append(np.asarray(c, dtype=np.float32))

    if not tracks:
        raise ValueError("No valid tracks with Effnet + CLAP embeddings were found.")

    effnet = np.stack(eff_rows, axis=0)
    clap = np.stack(clap_rows, axis=0)

    eff_norm = np.linalg.norm(effnet, axis=1, keepdims=True)
    eff_norm = np.maximum(eff_norm, 1e-12)
    clap_norm = np.linalg.norm(clap, axis=1, keepdims=True)
    clap_norm = np.maximum(clap_norm, 1e-12)
    effnet_unit = effnet / eff_norm
    clap_unit = clap / clap_norm

    labels = load_discogs400_labels(labels_json_path)
    cls0 = tracks[0].get("classifiers") or {}
    v0 = cls0.get("discogs400_style_activations_mean") or []
    if len(v0) != len(labels):
        raise ValueError(
            f"Style activation length {len(v0)} does not match labels ({len(labels)})."
        )

    return tracks, effnet, clap, effnet_unit, clap_unit


def init_session_defaults() -> None:
    """Sync catalog paths from the environment each run (no in-app path editor)."""
    st.session_state.cfg_descriptors_path = runtime_descriptors_path()
    st.session_state.cfg_labels_path = runtime_labels_path()
    st.session_state.cfg_clap_ckpt = runtime_clap_checkpoint()
    if "active_view" not in st.session_state:
        st.session_state.active_view = "overview"
