"""AC2 — the vendored shared modules are byte-identical to the file-to-markdown
originals. This detects drift (a tripwire); it does not structurally prevent it
(no cross-skill shared-lib mechanism exists). Editing either copy fails this test
until both are re-synced.

Run with `python -m pytest` from this directory.
"""
from __future__ import annotations

from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ORIGIN = HERE.parent.parent / "file-to-markdown" / "scripts"


@pytest.mark.parametrize("name", ["contract.py", "safe_io.py"])
def test_vendored_copy_is_byte_identical(name):
    vendored = (HERE / name).read_bytes()
    original = (ORIGIN / name).read_bytes()
    assert vendored == original, (
        f"{name} has drifted from file-to-markdown/scripts/{name}; re-sync the "
        f"vendored copy (AC2)."
    )
