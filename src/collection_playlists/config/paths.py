from pathlib import Path


def project_root() -> Path:
    """Repository root (``collection_playlists/config`` → … → repo)."""
    return Path(__file__).resolve().parent.parent.parent.parent


def default_descriptors_jsonl() -> Path:
    """Default per-track descriptors file produced by the analyzer (any audio root)."""
    return project_root() / "analysis" / "descriptors.jsonl"


def default_discogs400_labels_json() -> Path:
    """Label list for the 400 style dimensions (Essentia Discogs400 head)."""
    return project_root() / "models" / "genre_discogs400-discogs-effnet-1.json"


def default_clap_checkpoint() -> Path:
    """LAION-CLAP weights for text queries (must match how descriptors were computed)."""
    return project_root() / "models" / "music_speech_epoch_15_esc_89.25.pt"


def default_descriptor_and_label_paths() -> tuple[str, str]:
    return str(default_descriptors_jsonl()), str(default_discogs400_labels_json())
