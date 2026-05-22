"""Cross-command helpers re-used by more than one subcommand.

This module is imported lazily (alongside its sibling command modules) so it
does not add startup cost to `--version` / `--help`. Only pure stdlib is
allowed here — see spec § Never do.
"""

from __future__ import annotations

import sys
from pathlib import Path
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
    at import time from the bundled `adapter.toml`). AC #14 in the spec
    requires every subcommand that consumes a pack manifest to invoke
    this gate before any I/O the pack would drive — uniform refusal, no
    partial behaviour.
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


def load_pack_and_gate(pack_path: Path) -> tuple[dict[str, Any], int] | tuple[dict[str, Any], None]:
    """Load a pack's `pack.toml` and apply the spec-version gate.

    Returns `(pack_toml, None)` on accept and `(pack_toml, 1)` on refusal.
    The pack_toml is returned in both cases so the caller can introspect
    even on refusal — useful for `validate` which reports schema errors
    and version errors together.
    """
    from agentbundle.config import load_pack_toml

    pack_toml = load_pack_toml(pack_path / "pack.toml")
    return pack_toml, check_spec_version_gate(pack_toml)


def _major(version: str) -> str:
    """Return the major component of a version string like '0.1' or 'v2.0'."""
    v = version.lstrip("v")
    return v.split(".")[0]
