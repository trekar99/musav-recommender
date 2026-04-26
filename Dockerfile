# Playlist Studio — Hugging Face Spaces (Docker + Streamlit)
#
#   docker build -t playlist-studio .
#   docker run -p 7860:7860 playlist-studio
#
# HF Spaces expect the app on port 7860.

FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-spaces.txt .
RUN pip install --no-cache-dir -r requirements-spaces.txt

COPY main.py .
COPY src/ src/
COPY .streamlit/ .streamlit/
COPY analysis/ analysis/

# Label list + CLAP weights are gitignored locally; bake them into the image for Spaces.
RUN mkdir -p models \
    && curl -fsSL -o models/genre_discogs400-discogs-effnet-1.json \
        "https://essentia.upf.edu/models/classification-heads/genre_discogs400/genre_discogs400-discogs-effnet-1.json" \
    && curl -fsSL -o models/music_speech_epoch_15_esc_89.25.pt \
        "https://huggingface.co/lukewys/laion_clap/resolve/main/music_speech_epoch_15_esc_89.25.pt"

RUN useradd -m -u 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 7860

CMD ["python", "main.py", \
     "--server.port=7860", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
