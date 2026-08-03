"""Compatibility entry point for the common Lab 07 benchmark.

The official benchmark is root ``bench.py``.  Keeping this wrapper prevents a
personal runner from silently using a different model, prompt, score rule, or
chunk size.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bench import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
