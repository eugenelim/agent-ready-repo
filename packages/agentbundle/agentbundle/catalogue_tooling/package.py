"""Catalogue packaging stub.

Wave 4 (catalogue-tooling-package-enhanced spec) fills this module.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agentbundle.catalogue_tooling.results import PackageResult


def package_catalogue(
    root: Path,
    bundle: str | None = None,
    release: str | None = None,
    channel: str | None = None,
    output: Path | None = None,
) -> "PackageResult":
    """Package a catalogue at *root* into an Artifactory artifact layout.

    Wave 4 implementation: wraps the existing package-catalogue command
    logic behind the portable engine interface.
    """
    raise NotImplementedError(
        "package_catalogue is not yet implemented — see catalogue-tooling-package-enhanced spec"
    )
