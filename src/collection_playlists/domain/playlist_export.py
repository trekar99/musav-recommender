from __future__ import annotations

from pathlib import Path
from typing import Iterable, List


def build_m3u8_playlist(absolute_paths: Iterable[str], extinf_titles: List[str] | None = None) -> str:
    lines: List[str] = ["#EXTM3U"]
    paths = list(absolute_paths)
    for i, p in enumerate(paths):
        title = None
        if extinf_titles and i < len(extinf_titles):
            title = extinf_titles[i]
        if title:
            lines.append(f"#EXTINF:-1,{title}")
        lines.append(str(Path(p).resolve()))
    return "\n".join(lines) + "\n"
