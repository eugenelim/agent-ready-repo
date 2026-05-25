"""Nit-7: marker-schema-version parity between the writer template and the CLI.

Both ``packages/agentbundle/templates/install-marker.py`` and
``packages/agentbundle/agentbundle/commands/install.py`` embed a literal
``marker-schema-version = "<X>"`` string. This test greps both files for the
literal, extracts ``<X>``, and asserts they are equal — so a bump in one file
that is not mirrored in the other fails CI immediately.
"""

from __future__ import annotations

import re
from pathlib import Path

# Repo-relative anchor: this test file lives at
# packages/agentbundle/tests/unit/test_marker_schema_version_parity.py
_REPO_ROOT = Path(__file__).resolve().parents[4]
_WRITER = _REPO_ROOT / "packages" / "agentbundle" / "templates" / "install-marker.py"
_CLI = _REPO_ROOT / "packages" / "agentbundle" / "agentbundle" / "commands" / "install.py"

# Both writers emit the version via _emit_basic_string('<version>') in an
# f-string: `f"marker-schema-version = {_emit_basic_string('0.1')}"`.
# Match both the f-string form and any plain quoted form so future edits
# (e.g. changing to a literal "0.2") are still caught.
_VERSION_RE = re.compile(
    r"""marker-schema-version.*?_emit_basic_string\(['"]([^'"]+)['"]\)"""
    r"""|marker-schema-version\s*=\s*['"]([^'"]+)['"]"""
)


def _extract_version(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    m = _VERSION_RE.search(text)
    assert m is not None, (
        f"Could not find marker-schema-version literal in {path}"
    )
    # group(1) matches the _emit_basic_string form; group(2) matches a plain
    # quoted literal. Exactly one group will be non-None.
    return m.group(1) or m.group(2)


def test_marker_schema_version_parity() -> None:
    """Writer template and CLI writer emit the same marker-schema-version."""
    writer_version = _extract_version(_WRITER)
    cli_version = _extract_version(_CLI)
    assert writer_version == cli_version, (
        f"marker-schema-version mismatch: "
        f"install-marker.py has {writer_version!r}, "
        f"install.py has {cli_version!r}. "
        f"Bump both files together when the schema version changes."
    )
