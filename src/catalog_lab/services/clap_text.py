from __future__ import annotations

from pathlib import Path

import numpy as np
import streamlit as st

from config.paths import default_clap_checkpoint


@st.cache_resource(show_spinner="Loading CLAP (text encoder)…")
def get_clap_module(clap_ckpt_path: str):
    import laion_clap  # type: ignore

    ckpt = Path(clap_ckpt_path)
    if not ckpt.is_file():
        raise FileNotFoundError(
            f"CLAP checkpoint not found: {ckpt}\n"
            "Point to a valid .pt file under **Data sources** in the app, or download weights separately."
        )

    model = laion_clap.CLAP_Module(enable_fusion=False, amodel="HTSAT-base")
    model.load_ckpt(ckpt=str(ckpt))
    return model


def embed_text_query(model, text: str) -> np.ndarray:
    text = (text or "").strip()
    if not text:
        raise ValueError("Empty text query.")
    try:
        emb = model.get_text_embedding([text], use_tensor=False)
    except TypeError:
        emb = model.get_text_embedding([text])
    emb = np.asarray(emb, dtype=np.float64)
    if emb.ndim == 2:
        emb = emb[0]
    emb = emb.reshape(-1)
    n = np.linalg.norm(emb)
    if n > 0:
        emb = emb / n
    return emb.astype(np.float32)


def default_ckpt_str() -> str:
    return str(default_clap_checkpoint())
