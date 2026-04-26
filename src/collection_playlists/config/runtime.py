"""
Paths are resolved **before** the app runs: environment variables override repository defaults.

Relative paths in env vars are resolved against the repository root (same as ``paths.project_root()``).
"""

from __future__ import annotations

import os
from pathlib import Path

from collection_playlists.config.paths import (
    default_clap_checkpoint,
    default_descriptor_and_label_paths,
    project_root,
)


def _resolve_path(raw: str) -> str:
    p = Path(raw.strip()).expanduser()
    if not raw.strip():
        raise ValueError("Path is empty.")
    if p.is_absolute():
        return str(p.resolve())
    return str((project_root() / p).resolve())


def runtime_descriptors_path() -> str:
    v = os.environ.get("COLLECTION_PLAYLISTS_DESCRIPTORS_JSONL", "").strip()
    if v:
        return _resolve_path(v)
    d, _ = default_descriptor_and_label_paths()
    return d


def runtime_labels_path() -> str:
    v = os.environ.get("COLLECTION_PLAYLISTS_LABELS_JSON", "").strip()
    if v:
        return _resolve_path(v)
    _, lab = default_descriptor_and_label_paths()
    return lab


def runtime_clap_checkpoint() -> str:
    v = os.environ.get("COLLECTION_PLAYLISTS_CLAP_CKPT", "").strip()
    if v:
        return _resolve_path(v)
    return str(default_clap_checkpoint())
