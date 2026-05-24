"""Contract loader.

Reads `docs/contracts/adapter.toml` via `tomllib` and
returns a dict. No validation logic — `validate.py` does that, and
the CLI's `validate` subcommand wires the two together.

The loader exposes a single function `load(path)` so adapters and
the build pipeline share the same input shape.
"""

from __future__ import annotations

import tomllib
from pathlib import Path


def load(path: str | Path) -> dict:
    """Load a TOML file from disk and return its parsed contents."""
    contents = Path(path).read_bytes()
    return tomllib.loads(contents.decode("utf-8"))
