"""Catalogue build engine stub.

Wave 2 (catalogue-tooling-build-self spec) fills this module.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agentbundle.catalogue_tooling.results import BuildResult


def build_catalogue(root: Path, output: Path, pack: str | None = None) -> "BuildResult":
    """Build a catalogue at *root* to *output*.

    Wave 2 implementation: renders all packs through the F-build pipeline,
    writes the dist/ tree and marketplace.json.
    """
    raise NotImplementedError(
        "build_catalogue is not yet implemented — see catalogue-tooling-build-self spec"
    )
