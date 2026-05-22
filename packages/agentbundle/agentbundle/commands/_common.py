"""Shared helpers for subcommand modules.

Extracted here so T5's ``install``, T2's ``validate``, and future
commands can call ``check_spec_version_gate`` without duplication.
"""

from __future__ import annotations

import sys
from typing import Any

from agentbundle.version import SPEC_VERSION


def check_spec_version_gate(pack_toml: dict[str, Any]) -> int | None:
    """Refuse if the pack's declared spec major version differs from ours.

    Returns ``None`` if the version check passes (or the pack does not
    declare a version at all). Returns a non-zero exit code (``1``) if
    the major versions differ — caller should ``return`` the result
    immediately.

    The pack declares its version under ``[pack.adapter-contract]
    version``; the CLI's version comes from ``agentbundle.version.SPEC_VERSION``
    (read at import time from the bundled ``adapter.toml``).
    """
    from agentbundle.config import pack_spec_version  # local import avoids circular

    declared = pack_spec_version(pack_toml)
    if declared is None:
        return None  # Pack does not gate on adapter-contract version.

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


def _major(version: str) -> str:
    """Return the major component of a version string like '0.1' or '2.0'.

    Strips a leading 'v' if present (e.g. 'v0.1' → '0').
    """
    v = version.lstrip("v")
    return v.split(".")[0]
