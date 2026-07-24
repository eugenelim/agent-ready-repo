"""Catalogue verification engine stub.

Wave 2 (catalogue-tooling-verify spec) fills this module.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agentbundle.catalogue_tooling.results import VerifyResult


def verify_catalogue(root: Path, pack: str | None = None) -> "VerifyResult":
    """Verify a catalogue at *root* against its contracts.

    Wave 3 implementation: checks adapter contract conformance, schema
    compliance, and install-marker integrity.
    """
    raise NotImplementedError(
        "verify_catalogue is not yet implemented — see catalogue-tooling-verify spec"
    )
