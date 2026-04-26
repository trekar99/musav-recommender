#!/usr/bin/env python3
"""
Build overview figures from ``analysis/descriptors.jsonl`` into ``analysis/report/``.

Uses the same logic as ``notebooks/music_collection_overview.ipynb`` (no Jupyter required).

    python generate_music_overview_figures.py
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


def _find_root() -> Path:
    here = Path(__file__).resolve().parent
    if (here / "analysis" / "descriptors.jsonl").exists():
        return here
    raise FileNotFoundError(f"Expected {here / 'analysis' / 'descriptors.jsonl'}")


def main() -> int:
    root = _find_root()
    analysis_path = root / "analysis" / "descriptors.jsonl"
    report_dir = root / "analysis" / "report"
    report_dir.mkdir(parents=True, exist_ok=True)
    figure_paths: list[Path] = []

    def savefig(name: str) -> None:
        p = report_dir / name
        plt.savefig(p, dpi=160, bbox_inches="tight", facecolor="white", edgecolor="none")
        figure_paths.append(p)
        plt.close()

    plt.rcParams.update(
        {
            "figure.figsize": (10, 5),
            "figure.facecolor": "white",
            "axes.facecolor": "#f6f7f9",
            "axes.edgecolor": "#d8dde6",
            "axes.labelcolor": "#1a1d24",
            "axes.titleweight": "600",
            "axes.titlesize": 12,
            "text.color": "#1a1d24",
            "xtick.color": "#3a3f4a",
            "ytick.color": "#3a3f4a",
            "font.size": 10,
            "grid.color": "#e2e5ec",
            "grid.linestyle": "-",
            "grid.alpha": 0.85,
        }
    )
    sns.set_theme(style="whitegrid", palette="deep")

    rows = [json.loads(line) for line in analysis_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    df = pd.DataFrame(
        {
            "relative_path": [r["relative_path"] for r in rows],
            "tempo_bpm": [r.get("tempo_bpm") for r in rows],
            "loudness_lufs": [r.get("loudness_lufs") for r in rows],
            "danceability": [
                (r.get("classifiers", {}).get("danceability_mean", [np.nan, np.nan]) or [np.nan, np.nan])[0]
                for r in rows
            ],
            "instrumental_prob": [
                (r.get("classifiers", {}).get("voice_instrumental_mean", [np.nan, np.nan]) or [np.nan, np.nan])[0]
                for r in rows
            ],
            "vocal_prob": [
                (r.get("classifiers", {}).get("voice_instrumental_mean", [np.nan, np.nan]) or [np.nan, np.nan])[1]
                for r in rows
            ],
            "style_activations": [
                r.get("classifiers", {}).get("discogs400_style_activations_mean", []) for r in rows
            ],
            "key_temperley": [r.get("key", {}).get("temperley", {}).get("key") for r in rows],
            "scale_temperley": [r.get("key", {}).get("temperley", {}).get("scale") for r in rows],
            "key_krumhansl": [r.get("key", {}).get("krumhansl", {}).get("key") for r in rows],
            "scale_krumhansl": [r.get("key", {}).get("krumhansl", {}).get("scale") for r in rows],
            "key_edma": [r.get("key", {}).get("edma", {}).get("key") for r in rows],
            "scale_edma": [r.get("key", {}).get("edma", {}).get("scale") for r in rows],
        }
    )

    def load_style_labels(expected_len: int) -> list[str]:
        meta_path = root / "models" / "genre_discogs400-discogs-effnet-1.json"
        if not meta_path.exists():
            return [f"style_{i:03d}" for i in range(expected_len)]
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        classes = meta.get("classes")
        if not isinstance(classes, list) or len(classes) != expected_len:
            raise ValueError("Unexpected classes in genre_discogs400 JSON")
        return [str(x) for x in classes]

    def parent_genre(label: str) -> str:
        for sep in ("---", "--", "—"):
            if sep in label:
                return label.split(sep, 1)[0].strip()
        if "-" in label and not label.startswith("style_"):
            return label.split("-", 1)[0].strip()
        return "unknown"

    style_dim = len(df["style_activations"].iloc[0])
    style_labels = load_style_labels(style_dim)
    style_matrix = np.vstack(df["style_activations"].to_numpy())
    style_top1_idx = style_matrix.argmax(axis=1)
    style_top1_label = [style_labels[i] for i in style_top1_idx]
    df["style_top1"] = style_top1_label
    df["broad_genre_top1"] = [parent_genre(s) for s in style_top1_label]

    style_threshold = 0.10
    style_binary = (style_matrix >= style_threshold).astype(int)
    style_stats = pd.DataFrame(
        {
            "style_id": np.arange(style_dim),
            "style_label": style_labels,
            "broad_genre": [parent_genre(s) for s in style_labels],
            "mean_activation": style_matrix.mean(axis=0),
            "top1_count": np.bincount(style_top1_idx, minlength=style_dim),
            "tracks_above_threshold": style_binary.sum(axis=0),
        }
    ).sort_values("tracks_above_threshold", ascending=False)
    style_stats.to_csv(report_dir / "styles_distribution.tsv", sep="\t", index=False)

    broad_counts = (
        df["broad_genre_top1"].value_counts().rename_axis("broad_genre").reset_index(name="tracks")
    )
    fig, ax = plt.subplots(figsize=(11, 5))
    sns.barplot(data=broad_counts, x="broad_genre", y="tracks", color="#3b6ea5", ax=ax)
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    ax.set_title("Broad genre (parent of top-1 Discogs400 style)")
    ax.set_xlabel("")
    fig.tight_layout()
    savefig("01_broad_genre.png")

    style_top20 = style_stats.head(20)
    fig, ax = plt.subplots(figsize=(11, 5.5))
    sns.barplot(data=style_top20, x="style_label", y="tracks_above_threshold", color="#d9822b", ax=ax)
    plt.setp(ax.get_xticklabels(), rotation=55, ha="right")
    ax.set_title(f"Top 20 styles by tracks ≥ activation {style_threshold}")
    ax.set_xlabel("")
    fig.tight_layout()
    savefig("02_styles_top20.png")

    fig, ax = plt.subplots(figsize=(9, 4.2))
    sns.histplot(
        df["tempo_bpm"].dropna(),
        bins=42,
        kde=True,
        ax=ax,
        color="#2d8a6e",
        stat="density",
        edgecolor="white",
        linewidth=0.35,
    )
    ax.set_title("Tempo (BPM)")
    ax.set_xlabel("BPM")
    med_t = df["tempo_bpm"].median()
    ax.axvline(med_t, color="#1a1d24", ls="--", lw=1, label=f"median {med_t:.0f}")
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    savefig("03_tempo_bpm.png")

    fig, ax = plt.subplots(figsize=(9, 4.2))
    sns.histplot(
        df["danceability"].dropna(),
        bins=36,
        kde=True,
        ax=ax,
        color="#c44e52",
        stat="density",
        edgecolor="white",
        linewidth=0.35,
    )
    ax.set_title("Danceability (softmax dim 0)")
    ax.set_xlabel("probability")
    ax.set_xlim(0, 1)
    med_d = df["danceability"].median()
    ax.axvline(med_d, color="#1a1d24", ls="--", lw=1, label=f"median {med_d:.2f}")
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    savefig("04_danceability_dim0.png")

    fig, ax = plt.subplots(figsize=(9, 4.2))
    sns.histplot(
        df["loudness_lufs"].dropna(),
        bins=42,
        kde=True,
        ax=ax,
        color="#8172b2",
        stat="density",
        edgecolor="white",
        linewidth=0.35,
    )
    ax.set_title("Integrated loudness (LUFS)")
    ax.set_xlabel("LUFS")
    med_l = df["loudness_lufs"].median()
    ax.axvline(med_l, color="#1a1d24", ls="--", lw=1, label=f"median {med_l:.1f}")
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    savefig("05_loudness_lufs.png")

    profiles = ["temperley", "krumhansl", "edma"]
    profile_labels = ["Temperley", "Krumhansl", "Edma"]

    def pair_agreement(a: str, b: str) -> float:
        return 100 * (
            (df[f"key_{a}"] == df[f"key_{b}"]) & (df[f"scale_{a}"] == df[f"scale_{b}"])
        ).mean()

    def key_scale_series(profile: str) -> pd.Series:
        return (
            df[f"key_{profile}"].astype(str).str.strip()
            + " "
            + df[f"scale_{profile}"].astype(str).str.strip()
        )

    counts = {p: key_scale_series(p).value_counts() for p in profiles}
    pool: set[str] = set()
    for p in profiles:
        pool.update(counts[p].head(14).index)

    def _label_weight(lab: str) -> int:
        return sum(int(counts[p].get(lab, 0)) for p in profiles)

    top_labels = sorted(pool, key=_label_weight, reverse=True)[:12]
    long_rows: list[dict[str, str | int]] = []
    nice = dict(zip(profiles, profile_labels))
    for lab in top_labels:
        for p in profiles:
            long_rows.append({"key_scale": lab, "profile": nice[p], "tracks": int(counts[p].get(lab, 0))})
    top_long = pd.DataFrame(long_rows)

    fig, ax = plt.subplots(figsize=(11, 5.2))
    sns.barplot(
        data=top_long,
        x="key_scale",
        y="tracks",
        hue="profile",
        hue_order=profile_labels,
        order=top_labels,
        ax=ax,
    )
    ax.set_title("Top key+scale labels by Essentia profile (track counts)")
    ax.set_xlabel("")
    ax.set_ylabel("tracks")
    ax.legend(title="Profile", frameon=False, loc="upper right")
    plt.setp(ax.get_xticklabels(), rotation=42, ha="right")
    fig.tight_layout()
    savefig("06_key_scale_top_by_profile.png")

    profile_scores = pd.DataFrame(
        {
            "profile": profile_labels,
            "mean_pairwise_agreement_pct": [
                (pair_agreement("temperley", "krumhansl") + pair_agreement("temperley", "edma")) / 2,
                (pair_agreement("temperley", "krumhansl") + pair_agreement("krumhansl", "edma")) / 2,
                (pair_agreement("temperley", "edma") + pair_agreement("krumhansl", "edma")) / 2,
            ],
        }
    )

    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    sns.barplot(data=profile_scores, x="profile", y="mean_pairwise_agreement_pct", color="#6a8caf", ax=ax)
    ax.set_title("Key profiles: mean agreement with the other two (%)")
    ax.set_ylabel("% of tracks matching on key + scale")
    ax.set_xlabel("")
    ax.set_ylim(0, 100)
    fig.tight_layout()
    savefig("07_key_profiles_mean_pairwise_agreement.png")

    voice_summary = pd.DataFrame(
        {
            "class": ["instrumental", "vocal"],
            "mean_probability": [df["instrumental_prob"].mean(), df["vocal_prob"].mean()],
        }
    )
    fig, ax = plt.subplots(figsize=(5.5, 4))
    sns.barplot(data=voice_summary, x="class", y="mean_probability", color="#e892a4", ax=ax)
    ax.set_title("Voice vs instrumental (mean softmax)")
    ax.set_ylim(0, 1)
    ax.set_xlabel("")
    fig.tight_layout()
    savefig("08_voice_instrumental.png")

    paths = [
        p
        for p in figure_paths
        if p.exists() and p.name != "00_figure_overview_mosaic.png"
    ]
    if len(paths) >= 2:
        n = len(paths)
        ncols = 3
        nrows = int(np.ceil(n / ncols))
        fig, axes = plt.subplots(nrows, ncols, figsize=(5.2 * ncols, 3.45 * nrows))
        axes = np.atleast_1d(axes).ravel()
        for ax_i, p in zip(axes, paths):
            ax_i.imshow(mpimg.imread(p))
            ax_i.set_title(p.name, fontsize=9, color="#444")
            ax_i.axis("off")
        for ax_i in axes[len(paths) :]:
            ax_i.axis("off")
        fig.suptitle("Report figures overview", fontsize=13, fontweight="600", y=1.02)
        fig.tight_layout()
        mosaic = report_dir / "00_figure_overview_mosaic.png"
        plt.savefig(mosaic, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close()
        print("Wrote", mosaic)

    print(f"Wrote {len(figure_paths)} figures + TSV under {report_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
