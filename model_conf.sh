mkdir -p models
cd models

# 1. Discogs-Effnet (Embeddings Extractor)
wget https://essentia.upf.edu/models/feature-extractors/discogs-effnet/discogs-effnet-bs64-1.pb

# 2. Genre Discogs400 (400 Style Classifier based on Effnet)
wget https://essentia.upf.edu/models/classification-heads/genre_discogs400/genre_discogs400-discogs-effnet-1.pb

# 3. Voice/Instrumental (Classifier based on Effnet)
wget https://essentia.upf.edu/models/classification-heads/voice_instrumental/voice_instrumental-discogs-effnet-1.pb

# 4. Danceability (Classifier based on Effnet)
wget https://essentia.upf.edu/models/classification-heads/danceability/danceability-discogs-effnet-1.pb

# 5. LAION-CLAP
wget https://huggingface.co/lukewys/laion_clap/resolve/main/music_speech_epoch_15_esc_89.25.pt

cd ..