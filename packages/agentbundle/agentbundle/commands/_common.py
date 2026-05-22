"""Cross-command helpers re-used by more than one subcommand.

This module is imported lazily (alongside its sibling command modules) so it
does not add startup cost to `--version` / `--help`. Only pure stdlib is
allowed here — see spec § Never do.
"""

from __future__ import annotations

import sys
from typing import Any

from agentbundle.version import SPEC_VERSION


def check_spec_version_gate(pack_toml: dict[str, Any]) -> int | None:
    """Refuse if the pack's declared spec major version differs from ours.

    Returns:
        None — caller may proceed (pack does not gate, or majors agree).
        1    — caller should `return` this immediately; refusal already
               printed to stderr with both versions named.

    The pack declares its version under `[pack.adapter-contract] version`;
    the CLI's version comes from `agentbundle.version.SPEC_VERSION` (read
    at import time from the bundled `adapter.toml`).
    """
    from agentbundle.config import pack_spec_version  # local import avoids circular

    declared = pack_spec_version(pack_toml)
    if declared is None:
        return None

    cli_major = _major(SPEC_VERSION)
    pack_major = _major(declared)
    if cli_major != pack_major:
        print(
            f"error: pack declares adapter-contract version {declared!r} "
            f"(major {pack_major}), but this CLI ships spec version {SPEC_VERSION!r} "
            f"(major {cli_major}); refusing to operate on incompatible pack.",
            file=sys.stderr,
        )
        return 1
    return None


def check_spec_version(pack_toml: dict[str, Any], cli_spec_version: str) -> bool:
    """Legacy bool-shaped helper kept for one caller (validate.py).

    New callers should prefer `check_spec_version_gate` which returns the
    exit-code shape uniformly.
    """
    pack_table = pack_toml.get("pack", {})
    contract_table = pack_table.get("adapter-contract", {})
    if not isinstance(contract_table, dict):
        return True
    pack_version = contract_table.get("version")
    if pack_version is None:
        return True

    pack_major = _major(str(pack_version))
    cli_major = _major(cli_spec_version)

    if pack_major != cli_major:
        print(
            f"validate: pack adapter-contract version {pack_version!r} is "
            f"incompatible with CLI spec version {cli_spec_version!r} "
            f"(major: {pack_major} vs {cli_major})",
            file=sys.stderr,
        )
        return False
    return True


def _major(version: str) -> str:
    """Return the major component of a version string like '0.1' or 'v2.0'."""
    v = version.lstrip("v")
    return v.split(".")[0]
