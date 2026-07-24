"""Catalogue sync-defaults stub.

Wave 2 (catalogue-tooling-sync-defaults spec) fills this module.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agentbundle.catalogue_tooling.results import SyncDefaultsResult


def check_defaults(root: Path) -> "SyncDefaultsResult":
    """Check whether install-defaults.toml is in sync with catalogue.toml.

    Wave 2 implementation: reads both files and reports drift.
    """
    raise NotImplementedError(
        "check_defaults is not yet implemented — see catalogue-tooling-sync-defaults spec"
    )


def write_defaults(root: Path) -> "SyncDefaultsResult":
    """Regenerate install-defaults.toml from catalogue.toml.

    Wave 2 implementation: writes the [defaults] and [organization] blocks.
    """
    raise NotImplementedError(
        "write_defaults is not yet implemented — see catalogue-tooling-sync-defaults spec"
    )
