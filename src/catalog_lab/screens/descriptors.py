from __future__ import annotations

from pathlib import Path

import streamlit as st

from domain.descriptor_filters import DescriptorFilterConfig, filter_and_rank_tracks
from domain.playlist_export import build_m3u8_playlist
from services.catalog_loader import load_catalog_bundle, load_discogs400_labels
from ui.audio_player import render_track_player


def render_descriptor_screen() -> None:
    st.header("Descriptor search")
    st.caption("Filter your catalog, rank by selected Discogs400 styles, preview audio, export M3U8.")

    descriptors_path = st.session_state.cfg_descriptors_path
    labels_path = st.session_state.cfg_labels_path

    try:
        tracks, _eff, _clap, _eu, _cu = load_catalog_bundle(descriptors_path, labels_path)
        labels = load_discogs400_labels(labels_path)
    except Exception as exc:
        st.error(f"Could not load catalog: {exc}")
        return

    with st.container(border=True):
        st.subheader("Filters")
        col_a, col_b = st.columns(2)
        with col_a:
            tempo_min, tempo_max = st.slider(
                "Tempo (BPM) range",
                min_value=40.0,
                max_value=240.0,
                value=(80.0, 180.0),
                step=1.0,
            )
        with col_b:
            voice_mode = st.radio(
                "Voice",
                options=["any", "vocal", "instrumental"],
                format_func=lambda x: {
                    "any": "Any",
                    "vocal": "Mostly vocal (≥ 0.5)",
                    "instrumental": "Mostly instrumental (< 0.5)",
                }[x],
                horizontal=True,
            )

        d1, d2 = st.columns(2)
        catalog_keys = sorted(
            {str(((t.get("key") or {}).get("krumhansl") or {}).get("key") or "") for t in tracks}
            - {""}
        )
        with d1:
            dance_min, dance_max = st.slider(
                "Danceability probability",
                min_value=0.0,
                max_value=1.0,
                value=(0.0, 1.0),
                step=0.01,
            )
        with d2:
            key_opts = ["Any"] + catalog_keys
            key_choice = st.selectbox("Key (Krumhansl)", key_opts)
            scale_choice = st.selectbox("Scale", ["Any", "major", "minor"])

        st.markdown(
            "**Discogs400 styles** — pick one or more; each selected style must meet the activation floor."
        )
        style_query = st.text_input("Search style names", placeholder="e.g. Deep House, Jazz")
        filtered_labels = labels
        if style_query.strip():
            q = style_query.strip().lower()
            filtered_labels = [lab for lab in labels if q in lab.lower()]
            st.caption(f"{len(filtered_labels)} styles match.")

        selected_labels = st.multiselect(
            "Styles",
            options=filtered_labels,
            default=[],
            help="Indices align with activations in your descriptors (alphabetical label list).",
        )
        style_indices = [labels.index(lab) for lab in selected_labels]
        style_floor = st.slider(
            "Minimum activation on each selected style",
            min_value=0.0,
            max_value=1.0,
            value=0.08,
            step=0.01,
        )

        top_n = st.slider("How many tracks to list", 5, 100, 25)

    cfg = DescriptorFilterConfig(
        tempo_min=float(tempo_min),
        tempo_max=float(tempo_max),
        voice_mode=voice_mode,
        dance_min=float(dance_min),
        dance_max=float(dance_max),
        key=None if key_choice == "Any" else key_choice,
        scale=None if scale_choice == "Any" else scale_choice,
        style_indices=style_indices,
        style_activation_min=float(style_floor),
    )

    ranked = filter_and_rank_tracks(tracks, cfg)
    subset = [t for t, _ in ranked[:top_n]]

    mcol1, mcol2 = st.columns([1, 2])
    with mcol1:
        st.metric("Matching tracks", len(ranked))
    with mcol2:
        if subset:
            m3u_body = build_m3u8_playlist(
                (t.get("absolute_path") or "" for t in subset),
                extinf_titles=[str(t.get("relative_path", "")) for t in subset],
            )
            st.download_button(
                label="Download playlist (.m3u8)",
                data=m3u_body.encode("utf-8"),
                file_name="descriptor_playlist.m3u8",
                mime="audio/x-mpegurl",
                type="primary",
                use_container_width=True,
            )

    if not subset:
        st.warning("No tracks match. Widen tempo, danceability, or style thresholds.")
        return

    st.divider()
    st.subheader("Results")

    for rank, tr in enumerate(subset, start=1):
        rid = tr.get("relative_path", "")
        kh = (tr.get("key") or {}).get("krumhansl") or {}
        cls = tr.get("classifiers") or {}
        dance = (cls.get("danceability_mean") or [0.0])[0]
        vocal = (cls.get("voice_instrumental_mean") or [0.0, 0.0])[1]
        with st.container(border=True):
            st.markdown(f"**{rank}.** `{rid}`")
            st.write(
                f"Tempo **{float(tr.get('tempo_bpm') or 0):.1f}** BPM · "
                f"LUFS **{float(tr.get('loudness_lufs') or 0):.1f}** · "
                f"Key **{kh.get('key', '?')} {kh.get('scale', '?')}** · "
                f"Dance **{dance:.2f}** · Vocal prob. **{vocal:.2f}**"
            )
            render_track_player(tr, caption=Path(str(tr.get("absolute_path", ""))).name)
