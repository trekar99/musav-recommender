"""
Launch the Phase 3 Streamlit dashboard.

Usage::

    python main.py

Extra arguments are forwarded to Streamlit, for example::

    python main.py --server.port 8502

The entry script is ``src/catalog_lab/app.py``.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parent
    app = root / "src" / "catalog_lab" / "app.py"
    if not app.is_file():
        print(f"Missing entry script: {app}", file=sys.stderr)
        raise SystemExit(1)
    cmd = [sys.executable, "-m", "streamlit", "run", str(app)]
    cmd.extend(sys.argv[1:])
    raise SystemExit(subprocess.call(cmd))


if __name__ == "__main__":
    main()
