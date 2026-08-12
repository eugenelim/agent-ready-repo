"""Doc-drift tests for Claude plugin installation command forms.

These tests flag obsolete installation command patterns in active user-facing
documentation. The canonical installation form (since Claude Code 2.1.209) is:

  claude plugin marketplace add eugenelim/agent-ready-repo
  claude plugin install <pack>@agent-ready-repo

Pinned 2026-07-21: the old forms below were rejected by the Claude plugin
validator and caused install failures. Any re-introduction of these forms in
active documentation (not historical RFCs or specs) is a regression.

Obsolete forms that must not appear in active docs:
  - claude plugin install <pack>             (no marketplace qualifier)
  - claude plugin install eugenelim/<pack>   (owner-prefix form, old API)
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

# Active user-facing documentation files to check.
_ACTIVE_DOCS = [
    REPO_ROOT / "packs" / "product-engineering" / "README.md",
    REPO_ROOT / "packs" / "architect" / "README.md",
    REPO_ROOT / "docs-site" / "src" / "content" / "docs" / "getting-started" / "install.md",
    REPO_ROOT / "README.md",
]

# Pattern: `claude plugin install <identifier>` where the identifier does NOT
# contain `@` (the marketplace qualifier). This catches both the bare pack name
# form and the owner/pack form. The negative lookahead (?!.*@) would be fragile
# across newlines; instead match the whole install command and check for @.
_BARE_INSTALL_RE = re.compile(
    r"claude\s+plugin\s+install\s+(?P<id>[^\s`\n]+)"
)


def _read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _find_stale_installs(text: str) -> list[str]:
    """Return install identifiers that lack the @marketplace qualifier."""
    stale = []
    for m in _BARE_INSTALL_RE.finditer(text):
        identifier = m.group("id").strip("`")
        if "@" not in identifier:
            stale.append(identifier)
    return stale


@pytest.mark.parametrize(
    "path",
    _ACTIVE_DOCS,
    ids=lambda path: path.relative_to(REPO_ROOT).as_posix(),
)
def test_active_doc_uses_marketplace_qualifier(path: Path) -> None:
    text = _read(path)
    stale = _find_stale_installs(text)
    assert not stale, (
        f"{path.relative_to(REPO_ROOT).as_posix()} contains stale plugin install forms "
        f"without @marketplace qualifier: {stale!r}. "
        "Use: claude plugin install <pack>@agent-ready-repo"
    )
