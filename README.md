# Audio descriptor recommender

Offline **analysis** for any folder of MP3s, plus a **collection-agnostic** Streamlit suite for turning the resulting **JSONL catalog** into playlists. Dataset names do not matter: only file paths and the per-track JSON schema.

## Components

| Path | Role |
|------|------|
| `src/analyze_collection.py` | Walks `--audio-root`, runs Essentia + CLAP, appends one JSON object per track to `analysis/descriptors.jsonl` (resumable). |
| `src/collection_playlists/` | **Playlist Studio**: Streamlit **domain** + **services** + **screens**, and **four** runnable apps under `apps/` (see below). |
| `notebooks/music_collection_overview.ipynb` | Exploratory stats + plots; writes figures under `analysis/report/`. |
| `generate_music_overview_figures.py` | Regenerates the same report PNGs + TSV from `analysis/descriptors.jsonl` without Jupyter (`python generate_music_overview_figures.py`). |

## Configuration (before `streamlit run`)

Paths are **not** edited in the UI. Set optional environment variables (absolute paths or paths relative to the **repository root**):

| Variable | Purpose |
|----------|---------|
| `COLLECTION_PLAYLISTS_DESCRIPTORS_JSONL` | Per-track descriptors JSONL |
| `COLLECTION_PLAYLISTS_LABELS_JSON` | Discogs400 labels JSON (400 classes) |
| `COLLECTION_PLAYLISTS_CLAP_CKPT` | LAION-CLAP `.pt` for text search |

If unset, defaults match this repo’s usual layout: `analysis/descriptors.jsonl`, `models/genre_discogs400-discogs-effnet-1.json`, `models/music_speech_epoch_15_esc_89.25.pt`.

**Playlist Studio** (the Streamlit hub) does **not** load CLAP until you open **Text**; that tab shows a slim progress strip while weights load from your local `.pt`. Descriptor and Similarity never load the text encoder.

The CLAP weights are **always local files** (e.g. from `model_conf.sh` or Hugging Face); the app does not download them for you.

## Quick start

```bash
pip install -r requirements.txt
python main.py
```

Optional Streamlit chrome: `.streamlit/config.toml`.

### Integrated hub (recommended)

```bash
python main.py
# equivalent:
PYTHONPATH=src streamlit run src/collection_playlists/apps/integrated/app.py
```

### Standalone mini-apps

From the repository root. Each `app.py` prepends `src/` to `sys.path`.

```bash
streamlit run src/collection_playlists/apps/descriptor_playlists/app.py --server.port 8501
streamlit run src/collection_playlists/apps/track_similarity/app.py   --server.port 8502
streamlit run src/collection_playlists/apps/text_playlists/app.py     --server.port 8503
```

For notebooks or scripts, use `PYTHONPATH=src` when importing `collection_playlists`.

## Package layout (`src/collection_playlists`)

```
collection_playlists/
  config/paths.py           # Repo root, default analysis/models paths
  config/runtime.py         # Env overrides for paths
  domain/                   # Pure Python: filters, cosine top-k, M3U builder
  services/                 # Cached JSONL load + CLAP text module
  ui/                       # Theme, shell (nav), audio widget
  screens/                  # Shared page bodies (hub + standalone reuse)
  apps/
    integrated/app.py       # Hub: overview + nav
    descriptor_playlists/app.py
    track_similarity/app.py
    text_playlists/app.py   # Text-only; CLAP loads on first paint with in-view progress
```

## Analyzer (reminder)

```bash
python src/analyze_collection.py \
  --audio-root /path/to/mp3s \
  --discogs-effnet-model /path/to/discogs-effnet.pb \
  --discogs400-model /path/to/genre_discogs400.pb \
  --voice-model /path/to/voice_instrumental.pb \
  --danceability-model /path/to/danceability.pb \
  --clap-ckpt /path/to/music_speech_epoch_15_esc_89.25.pt
```

Suggested weight locations: `model_conf.sh`.

## Notes

- **Playback** uses `absolute_path` from each JSON line; the M3U8 export writes resolved absolute paths.
- **Caching:** Catalog and CLAP are memoized by path string. Change env vars and **restart** the app to pick up new locations.
- **Naming:** The package is `collection_playlists` to stress that any analyzed library works—the same code paths apply whether your audio root was a course dataset or a personal drive.
