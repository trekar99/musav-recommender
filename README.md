# musav-recommender

Standalone analyzer script:

- `analyze_collection.py` recursively scans a collection for `.mp3` files.
- Extracts tempo, key/scale (temperley/krumhansl/edma), LUFS, Discogs-Effnet embeddings, Discogs400 style activations, voice/instrumental, danceability, and CLAP embeddings.
- Writes resumable incremental output to JSONL (`analysis/descriptors.jsonl`) and errors to `analysis/errors.jsonl`.

## Usage

```bash
python analyze_collection.py \
  --audio-root MusAV/audio_chunks \
  --discogs-effnet-model /path/to/discogs-effnet.pb \
  --discogs400-model /path/to/genre_discogs400.pb \
  --voice-model /path/to/voice_instrumental.pb \
  --danceability-model /path/to/danceability.pb \
  --clap-ckpt /path/to/music_speech_epoch_15_esc_89.25.pt
```