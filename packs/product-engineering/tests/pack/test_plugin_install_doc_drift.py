"""Product-engineering README plugin-install form check."""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
BARE_INSTALL_RE = re.compile(r"claude\s+plugin\s+install\s+(?P<id>[^\s`\n]+)")


def test_readme_uses_marketplace_qualifier() -> None:
    path = REPO_ROOT / "packs" / "product-engineering" / "README.md"
    stale = [
        identifier
        for match in BARE_INSTALL_RE.finditer(path.read_text(encoding="utf-8"))
        if "@" not in (identifier := match.group("id").strip("`"))
    ]
    assert not stale, f"{path}: stale plugin install forms: {stale!r}"
