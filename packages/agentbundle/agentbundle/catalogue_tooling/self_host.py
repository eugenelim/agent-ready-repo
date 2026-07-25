"""Catalogue self-host tooling stub.

Wave 2 (catalogue-tooling-build-self spec) fills this module.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agentbundle.catalogue_tooling.results import SelfHostResult


def check_self_host(root: Path) -> "SelfHostResult":
    """Check self-host configuration at *root*.

    Wave 2 implementation: validates install-defaults.toml shape and
    preferred-adapter setting.
    """
    raise NotImplementedError(
        "check_self_host is not yet implemented — see catalogue-tooling-build-self spec"
    )


def write_self_host(root: Path) -> "SelfHostResult":
    """Write self-host configuration at *root*.

    Wave 2 implementation: generates install-defaults.toml from catalogue.toml.
    """
    raise NotImplementedError(
        "write_self_host is not yet implemented — see catalogue-tooling-build-self spec"
    )
