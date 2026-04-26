"""
Launch **Playlist Studio** (integrated Streamlit hub: descriptors, similarity, text search, overview).

Usage::

    python main.py

Arguments are forwarded to Streamlit, for example::

    python main.py --server.port 8502

Entry script: ``src/collection_playlists/apps/integrated/app.py``.

``PYTHONPATH`` is set to ``src/`` so the ``collection_playlists`` package resolves the same way
when you invoke Streamlit manually (see README).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parent
    src = root / "src"
    app = src / "collection_playlists" / "apps" / "integrated" / "app.py"
    if not app.is_file():
        print(f"Missing entry script: {app}", file=sys.stderr)
        raise SystemExit(1)
    env = os.environ.copy()
    prev = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(src) + (os.pathsep + prev if prev else "")
    cmd = [sys.executable, "-m", "streamlit", "run", str(app)]
    cmd.extend(sys.argv[1:])
    raise SystemExit(subprocess.call(cmd, env=env, cwd=str(root)))


if __name__ == "__main__":
    main()
