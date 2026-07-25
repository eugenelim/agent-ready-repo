"""Catalogue lint engine stub.

Wave 2 (catalogue-tooling-lint spec) fills this module.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agentbundle.catalogue_tooling.results import LintResult


def lint_catalogue(root: Path, pack: str | None = None) -> "LintResult":
    """Lint a catalogue at *root*, optionally scoped to *pack*.

    Wave 2 implementation: validates pack.toml structure, skill/agent
    frontmatter, hook wiring, and cross-references.
    """
    raise NotImplementedError(
        "lint_catalogue is not yet implemented — see catalogue-tooling-lint spec"
    )
