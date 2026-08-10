"""Pack README plugin-install form checks pending relocation."""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]  # pack tests -> repository root
_BARE_INSTALL_RE = re.compile(r"claude\s+plugin\s+install\s+(?P<id>[^\s`\n]+)")


def _find_stale_installs(text: str) -> list[str]:
    return [
        identifier
        for match in _BARE_INSTALL_RE.finditer(text)
        if "@" not in (identifier := match.group("id").strip("`"))
    ]


def _assert_pack_readme_uses_marketplace_qualifier(pack_name: str) -> None:
    path = REPO_ROOT / "packs" / pack_name / "README.md"
    stale = _find_stale_installs(path.read_text(encoding="utf-8"))
    assert not stale, f"{path}: stale plugin install forms: {stale!r}"


def test_architect_readme_uses_marketplace_qualifier():
    _assert_pack_readme_uses_marketplace_qualifier("architect")
