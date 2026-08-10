"""Portable rules for retired credential-shim copies in pack scripts."""

from __future__ import annotations

import re
from pathlib import Path

CATALOGUE_ROOT = Path(__file__).resolve().parents[2]
PACKS_DIR = CATALOGUE_ROOT / "packs"
SHIM_BASENAMES = (
    "credentials_shim.py",
    "_keychain_macos.py",
    "_credman_windows.py",
)
SHIM_IMPORT_RE = re.compile(
    r"(?:from\s+\.{0,2}(?:[\w.]+\.)?credentials_shim\s+import"
    r"|import\s+(?:[\w.]+\.)?credentials_shim\b)"
)


def test_no_pack_skill_carries_a_retired_shim_copy() -> None:
    offenders = [
        str(path.relative_to(CATALOGUE_ROOT))
        for scripts_dir in PACKS_DIR.glob("*/.apm/skills/*/scripts")
        for basename in SHIM_BASENAMES
        if (path := scripts_dir / basename).exists()
    ]
    assert not offenders, offenders


def test_no_pack_skill_imports_the_retired_shim() -> None:
    offenders: list[str] = []
    for path in PACKS_DIR.glob("*/.apm/skills/*/scripts/*.py"):
        try:
            source = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if SHIM_IMPORT_RE.search(source):
            offenders.append(str(path.relative_to(CATALOGUE_ROOT)))
    assert not offenders, offenders
