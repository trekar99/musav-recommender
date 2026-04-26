from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple


@dataclass
class DescriptorFilterConfig:
    tempo_min: float
    tempo_max: float
    voice_mode: str
    dance_min: float
    dance_max: float
    key: Optional[str]
    scale: Optional[str]
    style_indices: Sequence[int]
    style_activation_min: float


def _krumhansl(track: Dict[str, Any]) -> Dict[str, Any]:
    return (track.get("key") or {}).get("krumhansl") or {}


def _voice_vocal_prob(track: Dict[str, Any]) -> float:
    cls = track.get("classifiers") or {}
    vi = cls.get("voice_instrumental_mean") or [0.0, 0.0]
    if len(vi) < 2:
        return 0.0
    return float(vi[1])


def _danceability(track: Dict[str, Any]) -> float:
    cls = track.get("classifiers") or {}
    d = cls.get("danceability_mean") or [0.0]
    return float(d[0]) if d else 0.0


def _style_vec(track: Dict[str, Any]) -> List[float]:
    cls = track.get("classifiers") or {}
    v = cls.get("discogs400_style_activations_mean")
    if not v:
        return []
    return [float(x) for x in v]


def passes_descriptor_filters(track: Dict[str, Any], cfg: DescriptorFilterConfig) -> bool:
    tempo = float(track.get("tempo_bpm") or 0.0)
    if tempo < cfg.tempo_min or tempo > cfg.tempo_max:
        return False

    vocal_p = _voice_vocal_prob(track)
    if cfg.voice_mode == "vocal" and vocal_p < 0.5:
        return False
    if cfg.voice_mode == "instrumental" and vocal_p >= 0.5:
        return False

    d = _danceability(track)
    if d < cfg.dance_min or d > cfg.dance_max:
        return False

    kh = _krumhansl(track)
    if cfg.key is not None and str(kh.get("key", "")) != cfg.key:
        return False
    if cfg.scale is not None and str(kh.get("scale", "")).lower() != cfg.scale.lower():
        return False

    if cfg.style_indices:
        vec = _style_vec(track)
        if len(vec) < max(cfg.style_indices) + 1:
            return False
        for i in cfg.style_indices:
            if vec[int(i)] < cfg.style_activation_min:
                return False

    return True


def style_rank_score(track: Dict[str, Any], style_indices: Sequence[int]) -> float:
    if not style_indices:
        return 0.0
    vec = _style_vec(track)
    if not vec:
        return 0.0
    s = 0.0
    for i in style_indices:
        s += vec[int(i)]
    return s / len(style_indices)


def filter_and_rank_tracks(
    tracks: Sequence[Dict[str, Any]], cfg: DescriptorFilterConfig
) -> List[Tuple[Dict[str, Any], float]]:
    rows: List[Tuple[Dict[str, Any], float]] = []
    for t in tracks:
        if not passes_descriptor_filters(t, cfg):
            continue
        score = style_rank_score(t, cfg.style_indices)
        rows.append((t, score))

    if cfg.style_indices:
        rows.sort(key=lambda x: x[1], reverse=True)
    else:
        rows.sort(key=lambda x: str(x[0].get("relative_path", "")))
    return rows
