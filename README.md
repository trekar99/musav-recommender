# Audio descriptor recommender

Tools for **any** analyzed music collection: run the offline analyzer on your audio root, then browse the resulting **JSONL catalog** in a small Streamlit UI.

## Components

1. **Analyzer** (`src/analyze_collection.py`) — walks a folder of `.mp3` files, runs Essentia + CLAP, and appends one JSON object per track to `analysis/descriptors.jsonl` (resumable). Paths and errors are configurable.
2. **Catalog lab** (`src/catalog_lab/`) — Streamlit app: descriptor filters, embedding similarity, CLAP text search, M3U8 export. **Collection-agnostic**: defaults point at this repo’s `analysis/` and `models/` folders; you can aim it at another machine’s paths via the in-app **Data sources & models** panel.

Example: you might analyze a public dataset such as MusAV under one `--audio-root`, or your own library under another. The UI only cares about the **schema** of each JSON line (see app docstrings and course spec), not the dataset name.

## Analyzer usage

```bash
python src/analyze_collection.py \
  --audio-root /path/to/your/mp3/collection \
  --discogs-effnet-model /path/to/discogs-effnet.pb \
  --discogs400-model /path/to/genre_discogs400.pb \
  --voice-model /path/to/voice_instrumental.pb \
  --danceability-model /path/to/danceability.pb \
  --clap-ckpt /path/to/music_speech_epoch_15_esc_89.25.pt
```

Model download hints live in `model_conf.sh`.

## Catalog lab (Streamlit)

```bash
pip install -r requirements.txt
python main.py
# or: streamlit run src/catalog_lab/app.py
```

Optional theme defaults live in `.streamlit/config.toml`.

## Package layout (`src/catalog_lab`)

| Area | Role |
|------|------|
| `config/` | Default filesystem paths (repo-relative). |
| `domain/` | Pure Python: filters, cosine top-k, M3U builder. |
| `services/` | Cached JSONL load + CLAP text model. |
| `ui/` | Theme, shell (nav + settings strip), audio widget. |
| `screens/` | The three tools + overview. |
| `app.py` | Single Streamlit entry and router. |

## Future: FastAPI + SPA

A separate **FastAPI** (or similar) API plus **React/Vue/Svelte** is feasible: the same `domain/` logic can sit behind HTTP endpoints while a front-end handles layout and audio URLs. That is a larger migration than renaming folders; this README documents the current baseline first.
