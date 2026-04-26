#!/usr/bin/env python3
"""Analyze a music collection with Essentia + CLAP.

This script recursively scans an input directory for .mp3 files and computes:
- tempo (BPM)
- key + scale with 3 key profiles (temperley, krumhansl, edma)
- integrated loudness (LUFS, EBU R128)
- Discogs-Effnet embeddings (mean pooled)
- Discogs400 style activations (mean pooled)
- voice/instrumental prediction (mean pooled)
- danceability prediction (mean pooled)
- LAION-CLAP audio embeddings (mean pooled)

Results are written incrementally to JSONL so interrupted runs can resume.
Per-track failures are logged and do not stop the run.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

import numpy as np
from tqdm import tqdm


def _lazy_import_essentia():
    try:
        import essentia  # type: ignore
        import essentia.standard as es  # type: ignore
    except Exception as exc:  # pragma: no cover - runtime environment dependent
        raise RuntimeError(
            "Could not import `essentia.standard`. Install Essentia first."
        ) from exc
    # Silence noisy C++ warning logs from Essentia internals.
    try:
        essentia.log.warningActive = False
    except Exception:
        pass
    return es


def _lazy_import_clap():
    try:
        import laion_clap  # type: ignore
    except Exception as exc:  # pragma: no cover - runtime environment dependent
        raise RuntimeError(
            "Could not import `laion_clap`. Install with `pip install laion-clap`."
        ) from exc
    return laion_clap


def iter_mp3_files(root: Path) -> Iterable[Path]:
    for current_root, _, files in os.walk(root):
        for name in files:
            if name.lower().endswith(".mp3"):
                yield Path(current_root) / name


def load_processed_set(jsonl_path: Path) -> Set[str]:
    processed: Set[str] = set()
    if not jsonl_path.exists():
        return processed
    with jsonl_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
                rel = row.get("relative_path")
                if isinstance(rel, str):
                    processed.add(rel)
            except json.JSONDecodeError:
                continue
    return processed


def append_jsonl(path: Path, row: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=True) + "\n")


def as_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except Exception:
        return None


def _resolve_essentia_alg(es: Any, candidates: Sequence[str], purpose: str) -> Any:
    """Return the first available Essentia algorithm constructor."""
    for name in candidates:
        if hasattr(es, name):
            return getattr(es, name)
    tf_like = sorted([n for n in dir(es) if "Tensorflow" in n or "ONNX" in n])
    preview = ", ".join(tf_like[:25])
    if len(tf_like) > 25:
        preview += ", ..."
    raise RuntimeError(
        f"Missing Essentia algorithm for {purpose}. Tried: {list(candidates)}. "
        f"Available TF/ONNX algorithms in this build: [{preview}]. "
        "This usually means Essentia was installed without TensorFlow inference support. "
        "Install an Essentia build that includes TensorflowPredict* algorithms."
    )


def _validate_required_paths(args: argparse.Namespace) -> None:
    required = {
        "discogs-effnet-model": args.discogs_effnet_model,
        "discogs400-model": args.discogs400_model,
        "voice-model": args.voice_model,
        "danceability-model": args.danceability_model,
        "clap-ckpt": args.clap_ckpt,
    }
    missing: List[str] = []
    for name, path in required.items():
        if not Path(path).exists():
            missing.append(f"--{name} -> {path}")
    if missing:
        joined = "\n  ".join(missing)
        raise RuntimeError(
            "Missing required model files. Provide real existing paths (not placeholders).\n"
            f"  {joined}"
        )


def _preflight_essentia_tf_support(es: Any) -> None:
    required_groups = [
        ("Discogs-Effnet embedder", ("TensorflowPredictEffnetDiscogs", "TensorflowPredictEffnet")),
        ("Generic TF predictor", ("TensorflowPredict", "TensorflowPredict2D")),
    ]
    missing_groups: List[str] = []
    for label, candidates in required_groups:
        if not any(hasattr(es, c) for c in candidates):
            missing_groups.append(f"{label}: expected one of {list(candidates)}")

    if not missing_groups:
        return

    tf_like = sorted([n for n in dir(es) if "Tensorflow" in n or "ONNX" in n])
    preview = ", ".join(tf_like[:40]) + (", ..." if len(tf_like) > 40 else "")
    raise RuntimeError(
        "Your Essentia build does not include required TensorFlow inference algorithms.\n"
        f"Missing components:\n  - " + "\n  - ".join(missing_groups) + "\n"
        f"Available TF/ONNX algorithms:\n  - {preview}\n"
        "Install an Essentia build with TensorFlow support and retry."
    )


def _build_effnet_embedder_with_dim_check(
    ctor: Any,
    graph_filename: Path,
    expected_dim: int = 1280,
    probe_audio_16k: Optional[np.ndarray] = None,
) -> Any:
    """Instantiate Effnet predictor and validate output embedding dimensionality."""
    # Candidate node configs seen across TF1/TF2 exports.
    # None means "use algorithm defaults".
    candidate_configs: Sequence[Tuple[Optional[str], Optional[str]]] = (
        (None, None),
        ("serving_default_melspectrogram", "PartitionedCall"),
        ("serving_default_melspectrogram", "PartitionedCall:0"),
        ("serving_default_melspectrogram", "PartitionedCall:1"),
        ("serving_default_melspectrogram", "PartitionedCall:2"),
        ("serving_default_melspectrogram", "StatefulPartitionedCall"),
        ("serving_default_melspectrogram", "StatefulPartitionedCall:0"),
        ("serving_default_melspectrogram", "StatefulPartitionedCall:1"),
        ("serving_default_melspectrogram", "StatefulPartitionedCall:2"),
        ("serving_default_melspectrogram", "StatefulPartitionedCall_1"),
        ("serving_default_melspectrogram", "StatefulPartitionedCall_1:0"),
        ("serving_default_melspectrogram", "StatefulPartitionedCall_1:1"),
        ("serving_default_melspectrogram", "StatefulPartitionedCall_1:2"),
        ("serving_default_model_Placeholder", "PartitionedCall"),
        ("serving_default_model_Placeholder", "StatefulPartitionedCall"),
        ("serving_default_model_Placeholder", "StatefulPartitionedCall_1"),
        ("model/Placeholder", "model/Identity"),
        ("model/Placeholder", "Identity"),
        ("model/Placeholder", "model/global_average_pooling2d/Mean"),
        ("model/Placeholder", "global_average_pooling2d/Mean"),
    )

    if probe_audio_16k is None:
        # Random probe avoids degenerate empty outputs some models can return on zeros.
        test_audio = np.random.randn(16000 * 10).astype(np.float32) * 0.01
    else:
        test_audio = np.asarray(probe_audio_16k, dtype=np.float32)
        if test_audio.size < 16000 * 3:
            pad = np.zeros((16000 * 3 - test_audio.size,), dtype=np.float32)
            test_audio = np.concatenate([test_audio, pad])
    errors: List[str] = []

    for in_node, out_node in candidate_configs:
        try:
            if in_node is None or out_node is None:
                predictor = ctor(graphFilename=str(graph_filename))
                label = "default"
            else:
                predictor = ctor(
                    graphFilename=str(graph_filename),
                    input=in_node,
                    output=out_node,
                )
                label = f"{in_node} -> {out_node}"

            out = np.asarray(predictor(test_audio))
            dim = int(out.shape[-1]) if out.ndim > 0 else -1
            if dim == expected_dim and out.size > 0:
                return predictor

            errors.append(f"{label} produced shape {tuple(out.shape)}")
        except Exception as exc:
            if in_node is None or out_node is None:
                label = "default"
            else:
                label = f"{in_node} -> {out_node}"
            errors.append(f"{label} failed: {exc}")

    tail = "\n  - ".join(errors[-10:])
    raise RuntimeError(
        "Could not configure Discogs-Effnet predictor that outputs 1280-d embeddings.\n"
        f"Graph: {graph_filename}\n"
        f"Recent attempts:\n  - {tail}"
    )


@dataclass
class EssentiaModels:
    # Signal processing algorithms
    rhythm_extractor: Any
    key_extractors: Dict[str, Any]
    mono_mixer: Any
    loudness_ebur128: Any
    # ML models using Effnet embeddings
    effnet_embedder: Any
    genre_classifier: Any
    voice_classifier: Any
    dance_classifier: Any


class Analyzer:
    def __init__(
        self,
        models: EssentiaModels,
        clap_model: Any,
        clap_sample_rate: int = 48000,
    ) -> None:
        self.models = models
        self.clap_model = clap_model
        self.clap_sample_rate = clap_sample_rate
        self.es = _lazy_import_essentia()
        self._resamplers: Dict[Tuple[int, int], Any] = {}

    def _to_mono(self, stereo: np.ndarray) -> np.ndarray:
        """Convert stereo/multi-channel audio to mono with robust fallbacks."""
        if stereo.ndim == 1:
            return stereo.astype(np.float32)

        # Prefer Essentia MonoMixer when possible.
        # Some builds expect a single matrix, others expect (left, right).
        try:
            return np.asarray(self.models.mono_mixer(stereo.astype(np.float32)), dtype=np.float32)
        except Exception:
            pass

        try:
            if stereo.shape[1] >= 2:
                return np.asarray(
                    self.models.mono_mixer(
                        stereo[:, 0].astype(np.float32),
                        stereo[:, 1].astype(np.float32),
                    ),
                    dtype=np.float32,
                )
        except Exception:
            pass

        # Build-agnostic fallback.
        if stereo.shape[1] >= 2:
            return (0.5 * (stereo[:, 0] + stereo[:, 1])).astype(np.float32)
        if stereo.shape[0] >= 2:
            return (0.5 * (stereo[0, :] + stereo[1, :])).astype(np.float32)
        raise RuntimeError(f"Could not convert to mono from shape: {stereo.shape}")

    @staticmethod
    def _mean_pool(x: np.ndarray) -> np.ndarray:
        if x.ndim == 1:
            return x
        if x.shape[0] == 0:
            return np.zeros((x.shape[1],), dtype=np.float32)
        return x.mean(axis=0)

    def _resample(self, audio: np.ndarray, sr_in: int, sr_out: int) -> np.ndarray:
        if sr_in == sr_out:
            return np.asarray(audio, dtype=np.float32)
        key = (int(sr_in), int(sr_out))
        if key not in self._resamplers:
            self._resamplers[key] = self.es.Resample(
                inputSampleRate=sr_in, outputSampleRate=sr_out
            )
        return np.asarray(self._resamplers[key](np.asarray(audio, dtype=np.float32)))

    def _audio_from_loader(self, path: Path) -> Tuple[np.ndarray, np.ndarray, int]:
        """Load once, then derive mono and stereo."""
        # AudioLoader keeps this script format-agnostic.
        audio_loader = self.es.AudioLoader(filename=str(path))
        data = audio_loader()

        # Essentia versions differ slightly in AudioLoader outputs.
        # Common case: audio, sampleRate, numChannels, md5, bitrate, codec
        if len(data) < 3:
            raise RuntimeError("Unexpected AudioLoader output shape.")
        stereo = np.asarray(data[0], dtype=np.float32)
        sample_rate = int(data[1])
        num_channels = int(data[2])

        if stereo.ndim == 1 or num_channels == 1:
            mono = stereo if stereo.ndim == 1 else stereo[:, 0]
            stereo2 = np.column_stack([mono, mono]).astype(np.float32)
            return mono.astype(np.float32), stereo2, sample_rate

        # Robust stereo handling across Essentia builds:
        # most outputs are (n_samples, n_channels), but some can differ.
        if stereo.ndim != 2:
            raise RuntimeError(f"Unexpected multi-channel audio shape: {stereo.shape}")

        if stereo.shape[1] >= 2:
            # Shape: (n_samples, n_channels)
            left = stereo[:, 0]
            right = stereo[:, 1]
        elif stereo.shape[0] >= 2:
            # Shape: (n_channels, n_samples)
            left = stereo[0, :]
            right = stereo[1, :]
            stereo = np.column_stack([left, right]).astype(np.float32)
        else:
            raise RuntimeError(f"Could not interpret stereo shape: {stereo.shape}")

        mono = self._to_mono(np.column_stack([left, right]).astype(np.float32))
        stereo2 = np.column_stack([left, right]).astype(np.float32)
        return mono.astype(np.float32), stereo2, sample_rate

    def _compute_tempo(self, mono: np.ndarray) -> Optional[float]:
        bpm, _, _, _, _ = self.models.rhythm_extractor(mono)
        return as_float(bpm)

    def _compute_key(self, mono: np.ndarray) -> Dict[str, Dict[str, Any]]:
        out: Dict[str, Dict[str, Any]] = {}
        for profile, extractor in self.models.key_extractors.items():
            key, scale, strength = extractor(mono)
            out[profile] = {
                "key": str(key),
                "scale": str(scale),
                "strength": as_float(strength),
            }
        return out

    def _compute_loudness(self, stereo: np.ndarray, sr: int) -> Optional[float]:
        if sr != 48000:
            # Resample both channels for LoudnessEBUR128 reference workflow.
            left = self._resample(stereo[:, 0], sr_in=sr, sr_out=48000)
            right = self._resample(stereo[:, 1], sr_in=sr, sr_out=48000)
            stereo_48k = np.column_stack([left, right]).astype(np.float32)
        else:
            stereo_48k = stereo

        # LoudnessEBUR128 returns (momentary, short-term, integrated, loudness_range, ...).
        # Integrated loudness (LUFS) is index 2; index -1 is loudness range, not integrated.
        result = self.models.loudness_ebur128(stereo_48k)
        if isinstance(result, (list, tuple)) and len(result) >= 3:
            return as_float(result[2])
        return as_float(result)

    def _compute_effnet_features(
        self, mono: np.ndarray, sr: int
    ) -> Dict[str, np.ndarray]:
        audio_16k = mono if sr == 16000 else self._resample(mono, sr_in=sr, sr_out=16000)
        embedding_frames = np.asarray(
            self.models.effnet_embedder(np.asarray(audio_16k, dtype=np.float32))
        )

        style_frames = np.asarray(self.models.genre_classifier(embedding_frames))
        voice_frames = np.asarray(self.models.voice_classifier(embedding_frames))
        dance_frames = np.asarray(self.models.dance_classifier(embedding_frames))

        return {
            "effnet_mean": self._mean_pool(embedding_frames).astype(np.float32),
            "style_mean": self._mean_pool(style_frames).astype(np.float32),
            "voice_mean": self._mean_pool(voice_frames).astype(np.float32),
            "dance_mean": self._mean_pool(dance_frames).astype(np.float32),
        }

    def _compute_clap_embedding(self, mono: np.ndarray, sr: int) -> np.ndarray:
        audio_48k = (
            mono
            if sr == self.clap_sample_rate
            else self._resample(mono, sr_in=sr, sr_out=self.clap_sample_rate)
        )
        # laion-clap expects list of float32 arrays for batch processing.
        emb = self.clap_model.get_audio_embedding_from_data(
            x=[np.asarray(audio_48k, dtype=np.float32)],
            use_tensor=False,
        )
        emb = np.asarray(emb)
        if emb.ndim == 2:
            return emb[0].astype(np.float32)
        return emb.astype(np.float32)

    def analyze_track(self, path: Path) -> Dict[str, Any]:
        mono, stereo, sr = self._audio_from_loader(path)

        tempo_bpm = self._compute_tempo(mono)
        key_info = self._compute_key(mono)
        loudness_lufs = self._compute_loudness(stereo, sr)

        effnet = self._compute_effnet_features(mono, sr)
        clap_mean = self._compute_clap_embedding(mono, sr)

        voice_pred = effnet["voice_mean"].tolist()
        dance_pred = effnet["dance_mean"].tolist()

        return {
            "tempo_bpm": tempo_bpm,
            "key": key_info,
            "loudness_lufs": loudness_lufs,
            "embeddings": {
                "discogs_effnet_mean": effnet["effnet_mean"].tolist(),
                "clap_mean": clap_mean.tolist(),
            },
            "classifiers": {
                "discogs400_style_activations_mean": effnet["style_mean"].tolist(),
                "voice_instrumental_mean": voice_pred,
                "danceability_mean": dance_pred,
            },
        }


def build_essentia_models(args: argparse.Namespace) -> EssentiaModels:
    es = _lazy_import_essentia()
    _preflight_essentia_tf_support(es)

    # Signal processing
    rhythm_extractor = es.RhythmExtractor2013(method="multifeature")
    key_extractors = {
        profile: es.KeyExtractor(profileType=profile)
        for profile in ("temperley", "krumhansl", "edma")
    }
    mono_mixer = es.MonoMixer()
    loudness_ebur128 = es.LoudnessEBUR128(sampleRate=48000)

    # ML models
    effnet_ctor = _resolve_essentia_alg(
        es,
        candidates=(
            "TensorflowPredictEffnetDiscogs",
            "TensorflowPredictEffnet",
            "TensorflowPredict",
        ),
        purpose="Discogs-Effnet embeddings",
    )
    predict2d_ctor = _resolve_essentia_alg(
        es,
        candidates=("TensorflowPredict2D", "TensorflowPredict"),
        purpose="2D classifier inference",
    )

    probe_audio_16k: Optional[np.ndarray] = None
    try:
        probe_loader = es.MonoLoader(filename=str(args.probe_audio_file), sampleRate=16000)
        probe_audio_16k = np.asarray(probe_loader(), dtype=np.float32)
    except Exception:
        probe_audio_16k = None

    effnet_embedder = _build_effnet_embedder_with_dim_check(
        ctor=effnet_ctor,
        graph_filename=args.discogs_effnet_model,
        expected_dim=1280,
        probe_audio_16k=probe_audio_16k,
    )
    genre_classifier = predict2d_ctor(
        graphFilename=str(args.discogs400_model),
        input="serving_default_model_Placeholder",
        output="PartitionedCall:0",
    )
    voice_classifier = predict2d_ctor(
        graphFilename=str(args.voice_model),
        output="model/Softmax",
    )
    dance_classifier = predict2d_ctor(
        graphFilename=str(args.danceability_model),
        output="model/Softmax",
    )

    return EssentiaModels(
        rhythm_extractor=rhythm_extractor,
        key_extractors=key_extractors,
        mono_mixer=mono_mixer,
        loudness_ebur128=loudness_ebur128,
        effnet_embedder=effnet_embedder,
        genre_classifier=genre_classifier,
        voice_classifier=voice_classifier,
        dance_classifier=dance_classifier,
    )


def build_clap_model(ckpt_path: Path):
    laion_clap = _lazy_import_clap()
    clap_model = laion_clap.CLAP_Module(enable_fusion=False, amodel="HTSAT-base")
    clap_model.load_ckpt(ckpt=str(ckpt_path))
    return clap_model


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Analyze music collection descriptors.")
    p.add_argument("--audio-root", type=Path, required=True, help="Root folder to scan.")
    p.add_argument(
        "--output-jsonl",
        type=Path,
        default=Path("analysis/descriptors.jsonl"),
        help="Incremental JSONL output path.",
    )
    p.add_argument(
        "--errors-jsonl",
        type=Path,
        default=Path("analysis/errors.jsonl"),
        help="Per-track error log JSONL path.",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional max number of tracks to process (for smoke tests).",
    )
    p.add_argument(
        "--overwrite",
        action="store_true",
        help="Ignore existing JSONL and recompute everything.",
    )
    p.add_argument(
        "--discogs-effnet-model",
        type=Path,
        default=Path("models/discogs-effnet-bs64-1.pb"),
        help="Path to Discogs-Effnet embedding model (.pb).",
    )
    p.add_argument(
        "--discogs400-model",
        type=Path,
        default=Path("models/genre_discogs400-discogs-effnet-1.pb"),
        help="Path to Discogs400 style classifier model (.pb).",
    )
    p.add_argument(
        "--voice-model",
        type=Path,
        default=Path("models/voice_instrumental-discogs-effnet-1.pb"),
        help="Path to voice/instrumental classifier model (.pb).",
    )
    p.add_argument(
        "--danceability-model",
        type=Path,
        default=Path("models/danceability-discogs-effnet-1.pb"),
        help="Path to danceability classifier model (.pb).",
    )
    p.add_argument(
        "--clap-ckpt",
        type=Path,
        default=Path("models/music_speech_epoch_15_esc_89.25.pt"),
        help="Path to LAION-CLAP checkpoint music_speech_epoch_15_esc_89.25.pt",
    )
    p.add_argument(
        "--probe-audio-file",
        type=Path,
        default=None,
        help="Optional audio file for probing model output shapes at startup.",
    )
    return p.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    _validate_required_paths(args)
    audio_root = args.audio_root.resolve()
    if not audio_root.exists():
        print(f"[ERROR] audio root does not exist: {audio_root}", file=sys.stderr)
        return 2

    mp3_files = sorted(iter_mp3_files(audio_root))
    if args.limit is not None:
        mp3_files = mp3_files[: args.limit]
    if not mp3_files:
        print(f"[ERROR] no .mp3 files found under: {audio_root}", file=sys.stderr)
        return 3
    if args.probe_audio_file is None:
        args.probe_audio_file = mp3_files[0]

    if args.overwrite:
        if args.output_jsonl.exists():
            args.output_jsonl.unlink()
        if args.errors_jsonl.exists():
            args.errors_jsonl.unlink()
        processed: Set[str] = set()
    else:
        processed = load_processed_set(args.output_jsonl)

    models = build_essentia_models(args)
    clap_model = build_clap_model(args.clap_ckpt)
    analyzer = Analyzer(models=models, clap_model=clap_model)

    to_process: List[Path] = []
    for p in mp3_files:
        rel = str(p.relative_to(audio_root))
        if rel not in processed:
            to_process.append(p)

    print(f"Found {len(mp3_files)} .mp3 files")
    print(f"Already analyzed: {len(processed)}")
    print(f"Remaining: {len(to_process)}")

    for path in tqdm(to_process, desc="Analyzing tracks", unit="track"):
        rel = str(path.relative_to(audio_root))
        try:
            analysis = analyzer.analyze_track(path)
            row = {
                "relative_path": rel,
                "absolute_path": str(path),
                **analysis,
            }
            append_jsonl(args.output_jsonl, row)
        except Exception as exc:  # pragma: no cover - runtime dependent failures
            append_jsonl(
                args.errors_jsonl,
                {
                    "relative_path": rel,
                    "absolute_path": str(path),
                    "error": str(exc),
                    "traceback": traceback.format_exc(limit=20),
                },
            )

    print(f"Done. Results: {args.output_jsonl}")
    if args.errors_jsonl.exists():
        print(f"Errors (if any): {args.errors_jsonl}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
