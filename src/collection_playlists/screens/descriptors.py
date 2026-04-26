from __future__ import annotations

from typing import Any, Dict, List

import streamlit as st

from collection_playlists.domain.descriptor_filters import DescriptorFilterConfig, filter_and_rank_tracks
from collection_playlists.domain.playlist_export import build_m3u8_playlist
from collection_playlists.services.catalog_loader import load_catalog_bundle, load_discogs400_labels
from collection_playlists.ui.playlist_row import format_track_subtitle, render_playlist_track_row


def _default_filter_state() -> Dict[str, Any]:
    return {
        "tempo_min": 80.0,
        "tempo_max": 180.0,
        "voice_mode": "any",
        "dance_min": 0.0,
        "dance_max": 1.0,
        "key_choice": "Any",
        "scale_choice": "Any",
        "style_query": "",
        "selected_labels": [],
        "style_floor": 0.08,
        "top_n": 25,
    }


def render_descriptor_screen() -> None:
    st.markdown("### Descriptors")
    st.caption("Edit the form, then **Run query** to refresh the results column.")

    descriptors_path = st.session_state.cfg_descriptors_path
    labels_path = st.session_state.cfg_labels_path

    try:
        tracks, _eff, _clap, _eu, _cu = load_catalog_bundle(descriptors_path, labels_path)
        labels = load_discogs400_labels(labels_path)
    except Exception as exc:
        st.error(f"Could not load catalog: {exc}")
        return

    if "desc_filter_cfg" not in st.session_state:
        st.session_state.desc_filter_cfg = _default_filter_state()

    cfg = st.session_state.desc_filter_cfg

    left, right = st.columns([1, 1.22], gap="large")

    with left:
        with st.form("descriptor_query_form"):
            tempo_min, tempo_max = st.slider(
                "Tempo (BPM)",
                min_value=40.0,
                max_value=240.0,
                value=(float(cfg["tempo_min"]), float(cfg["tempo_max"])),
                step=1.0,
            )

            st.caption("Groove & key")
            r2a, r2b = st.columns(2)
            with r2a:
                voice_mode = st.selectbox(
                    "Voice",
                    options=["any", "vocal", "instrumental"],
                    index=["any", "vocal", "instrumental"].index(cfg["voice_mode"])
                    if cfg["voice_mode"] in ("any", "vocal", "instrumental")
                    else 0,
                    format_func=lambda x: {
                        "any": "Any",
                        "vocal": "Mostly vocal",
                        "instrumental": "Mostly instrumental",
                    }[x],
                )
            with r2b:
                dance_min, dance_max = st.slider(
                    "Danceability",
                    min_value=0.0,
                    max_value=1.0,
                    value=(float(cfg["dance_min"]), float(cfg["dance_max"])),
                    step=0.01,
                )

            catalog_keys = sorted(
                {str(((t.get("key") or {}).get("krumhansl") or {}).get("key") or "") for t in tracks}
                - {""}
            )
            r3a, r3b = st.columns(2)
            with r3a:
                key_opts = ["Any"] + catalog_keys
                kdef = cfg["key_choice"] if cfg["key_choice"] in key_opts else "Any"
                key_choice = st.selectbox("Key", key_opts, index=key_opts.index(kdef))
            with r3b:
                scale_opts = ["Any", "major", "minor"]
                sdef = cfg["scale_choice"] if cfg["scale_choice"] in scale_opts else "Any"
                scale_choice = st.selectbox("Scale", scale_opts, index=scale_opts.index(sdef))

            st.caption("Styles (Discogs400)")
            style_query = st.text_input(
                "Filter label list",
                value=cfg["style_query"],
                placeholder="substring…",
            )
            q = style_query.strip().lower()
            filtered_labels = [lab for lab in labels if not q or q in lab.lower()]
            st.markdown(
                f'<div class="cp-muted">{len(filtered_labels)} labels match · {len(labels)} total</div>',
                unsafe_allow_html=True,
            )

            valid_selected = [x for x in cfg["selected_labels"] if x in filtered_labels]
            selected_labels = st.multiselect(
                "Styles to require",
                options=filtered_labels,
                default=valid_selected,
            )

            r4a, r4b = st.columns(2)
            with r4a:
                style_floor = st.slider(
                    "Min activation / style",
                    min_value=0.0,
                    max_value=1.0,
                    value=float(cfg["style_floor"]),
                    step=0.01,
                )
            with r4b:
                top_n = st.slider("List up to", min_value=5, max_value=100, value=int(cfg["top_n"]), step=1)

            submitted = st.form_submit_button("Run query", type="primary")

        if submitted:
            tmin, tmax = float(tempo_min), float(tempo_max)
            if tmin > tmax:
                tmin, tmax = tmax, tmin
            st.session_state.desc_filter_cfg = {
                "tempo_min": tmin,
                "tempo_max": tmax,
                "voice_mode": voice_mode,
                "dance_min": float(dance_min),
                "dance_max": float(dance_max),
                "key_choice": key_choice,
                "scale_choice": scale_choice,
                "style_query": style_query,
                "selected_labels": list(selected_labels),
                "style_floor": float(style_floor),
                "top_n": int(top_n),
            }
            st.rerun()

    cfg = st.session_state.desc_filter_cfg
    style_indices: List[int] = []
    for lab in cfg["selected_labels"]:
        if lab in labels:
            style_indices.append(labels.index(lab))

    dcfg = DescriptorFilterConfig(
        tempo_min=float(cfg["tempo_min"]),
        tempo_max=float(cfg["tempo_max"]),
        voice_mode=str(cfg["voice_mode"]),
        dance_min=float(cfg["dance_min"]),
        dance_max=float(cfg["dance_max"]),
        key=None if cfg["key_choice"] == "Any" else cfg["key_choice"],
        scale=None if cfg["scale_choice"] == "Any" else cfg["scale_choice"],
        style_indices=style_indices,
        style_activation_min=float(cfg["style_floor"]),
    )

    ranked = filter_and_rank_tracks(tracks, dcfg)
    top_n = max(5, min(100, int(cfg["top_n"])))
    subset = [t for t, _ in ranked[:top_n]]

    with right:
        st.markdown("### Results")
        m1, m2 = st.columns(2)
        with m1:
            st.metric("Matches", len(ranked))
        with m2:
            if subset:
                m3u_body = build_m3u8_playlist(
                    (t.get("absolute_path") or "" for t in subset),
                    extinf_titles=[str(t.get("relative_path", "")) for t in subset],
                )
                st.download_button(
                    label="Download .m3u8",
                    data=m3u_body.encode("utf-8"),
                    file_name="descriptor_playlist.m3u8",
                    mime="audio/x-mpegurl",
                    type="primary",
                    use_container_width=True,
                )

        if not subset:
            st.info("No rows in the current window. Widen filters and press **Run query**.")
            return

        for rank, tr in enumerate(subset, start=1):
            sub = format_track_subtitle(tr)
            render_playlist_track_row(rank=rank, track=tr, subtitle=sub)
