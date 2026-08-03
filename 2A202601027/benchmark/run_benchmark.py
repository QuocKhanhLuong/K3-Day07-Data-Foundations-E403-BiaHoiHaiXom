"""Legacy compatibility entry point for the root common benchmark runner.

The canonical MSSV for this member is ``2A20261027``.  Use ``python bench.py``
from the repository root for the official run.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from bench import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
