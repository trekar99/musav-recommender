from __future__ import annotations

import streamlit as st

from services.catalog_loader import count_jsonl_lines


def render_overview() -> None:
    desc_path = st.session_state.cfg_descriptors_path
    line_estimate = count_jsonl_lines(desc_path)

    st.markdown(
        """
<div class="lab-hero">
  <h1>Explore any analyzed audio catalog</h1>
  <p class="lead">
    Point the app at a <strong>descriptors.jsonl</strong> file: each line is one track with tempo,
    loudness, key (Krumhansl), Discogs400 style activations, voice/dance estimates, Discogs-Effnet
    and CLAP embeddings, plus <code>relative_path</code> (track ID) and <code>absolute_path</code> for
    playback. Filter by musical attributes, find nearest neighbours in embedding space, or describe
    what you want in text and rank the whole library with CLAP.
  </p>
  <div class="lab-pill-row">
    <span class="lab-pill">Streamlit UI</span>
    <span class="lab-pill">Cached loads</span>
    <span class="lab-pill">Local preview</span>
    <span class="lab-pill">M3U8 export</span>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )

    if line_estimate:
        st.caption(
            f"Quick scan: **{line_estimate:,}** non-empty lines in the current descriptors file "
            "(full validation runs when a tool loads the catalog)."
        )
    else:
        st.warning("Descriptors file missing or empty — set paths under **Data sources & models**.")

    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        with st.container(border=True):
            st.markdown("**Descriptor search**")
            st.caption(
                "Tempo band, vocal vs instrumental, danceability, key/scale, Discogs400 styles. "
                "Preview matches and download an M3U8 playlist (absolute file paths)."
            )
            if st.button("Open descriptor search", key="home_open_desc", use_container_width=True):
                st.session_state.active_view = "descriptors"
                st.rerun()

    with c2:
        with st.container(border=True):
            st.markdown("**Similarity**")
            st.caption(
                "Pick a query track by ID. Compare top-10 neighbours with cosine similarity for "
                "Effnet (1280-d) vs CLAP audio (512-d)."
            )
            if st.button("Open similarity", key="home_open_sim", use_container_width=True):
                st.session_state.active_view = "similarity"
                st.rerun()

    with c3:
        with st.container(border=True):
            st.markdown("**Text search**")
            st.caption(
                "Natural-language query. CLAP text vectors are matched to stored "
                "`clap_mean` audio embeddings (same checkpoint family as offline analysis)."
            )
            if st.button("Open text search", key="home_open_txt", use_container_width=True):
                st.session_state.active_view = "text"
                st.rerun()

    st.divider()
    st.markdown(
        """
**Why Streamlit (for now).** It keeps the whole UI in Python and pairs well with course timelines.
For a **production-grade** product UI, **FastAPI (or similar) + React/Vue/Svelte** is usually a
better long-term fit: you own routing, layout, and component polish. That migration is **feasible**
here because the heavy work is already “JSONL + numpy + optional CLAP”; a REST or JSON API would
expose the same operations to a separate front-end. This shell deliberately stays **one entry file**
with **top navigation buttons** (no Streamlit multipage filenames in a sidebar).

**Heavier front-end later:** ship endpoints such as `POST /catalog/reload`, `POST /query/descriptors`,
`GET /similar`, `POST /query/text`, return JSON + paths; the SPA plays audio via URLs you control
(static file server or signed URLs).
        """
    )
