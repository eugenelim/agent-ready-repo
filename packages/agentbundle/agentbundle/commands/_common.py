"""Cross-command helpers re-used by more than one subcommand.

This module is imported lazily (alongside its sibling command modules) so it
does not add startup cost to `--version` / `--help`. Only pure stdlib is
allowed here — see spec § Never do.
"""

from __future__ import annotations

import sys


def check_spec_version(pack_toml: dict, cli_spec_version: str) -> bool:
    """Refuse if the pack's declared adapter-contract major version differs from
    the CLI's own major version.

    Logic:
      - If the pack does not declare ``[pack.adapter-contract] version``,
        silently accept (version gate is opt-in for packs that predate the
        contract field).
      - If the major components differ, print a one-line refusal to stderr
        and return ``False``.
      - Otherwise return ``True``.

    The ``cli_spec_version`` string is passed in (not imported here directly)
    so this helper is trivially testable without mutating module-level state.

    Returns:
        True  — caller may proceed.
        False — caller must exit non-zero; message already printed.
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
    """Return the major component of a semver-ish version string.

    '0.1'    → '0'
    '1.2.3'  → '1'
    '99.0'   → '99'
    'abc'    → 'abc'  (non-numeric; returned as-is for comparison)
    """
    return version.split(".")[0]
