#!/usr/bin/env python3
"""Presence, version, and index preflight for the Wicked Estate CLI.

The catalogue's three-tier dependency policy requires a `--check` verb that
detects a non-stdlib dependency before any real work and fails clean when it is
absent. This is that verb. It is a preflight, not a query wrapper: every actual
code-intelligence question goes to `wicked-estate` directly, because wrapping a
CLI that already emits JSON would add a layer with nothing to do.

Exit codes are the contract the skill branches on:

    0  ready            binary present at or above the floor, and an index exists
    2  binary-absent    `wicked-estate` not on PATH
    3  index-absent     binary present, but no graph database was found
    4  version-below    binary present but older than the required floor
    5  install-failed   `--install` ran and the binary is still unresolvable
    6  override-refused `WICKED_ESTATE_DB` resolves outside the repository

`--install` implements the Tier-2 ladder: detect, gate on explicit consent,
install a pinned version with no sudo, then re-verify rather than trusting that
a just-installed binary is resolvable in this session.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

#: Minimum Wicked Estate release this skill's documented surface was verified
#: against. Every CLI verb the skill names exists in this release.
MINIMUM_VERSION = (0, 16)

#: Exact pinned version. A caret range would resolve to whatever 0.16.x is
#: newest at install time, which is not a pin.
PINNED_VERSION = "0.16.7"

#: Pinned install, matching `[[pack.runtime-dependencies]]` in pack.toml.
#: `--locked` makes the build reproducible from the crate's shipped lockfile.
INSTALL_COMMAND = [
    "cargo",
    "install",
    "wicked-estate",
    "--version",
    PINNED_VERSION,
    "--locked",
]

#: Default graph location, and the environment variable that overrides it.
#: This mirrors the CLI's own resolution order: an explicit `--db` beats
#: `WICKED_ESTATE_DB`, which beats `.wicked-estate/graph.db`.
DEFAULT_DB_RELPATH = Path(".wicked-estate") / "graph.db"
DB_ENV_VAR = "WICKED_ESTATE_DB"

EXIT_READY = 0
EXIT_BINARY_ABSENT = 2
EXIT_INDEX_ABSENT = 3
EXIT_VERSION_BELOW = 4
EXIT_INSTALL_FAILED = 5
EXIT_OVERRIDE_REFUSED = 6

_VERSION_RE = re.compile(r"(\d+)\.(\d+)(?:\.(\d+))?")


def find_binary() -> str | None:
    """Return the resolved path to `wicked-estate`, or None when absent."""
    return shutil.which("wicked-estate")


def read_version(binary: str) -> tuple[int, ...] | None:
    """Return the CLI's version as a tuple, or None when it cannot be parsed.

    Wicked Estate has no `--version` flag. The argument falls through to the
    dispatcher's default arm, which prints a 65-line usage banner whose first
    line reads ``wicked-estate 0.16.7 — usage:``. That banner is what this
    parses, which is why the regex scans rather than anchoring, and why an
    unparseable result is deliberately not fatal: the pack is reading an
    unspecified fallback, so a future change to the banner must degrade to a
    warning rather than block a working binary.
    """
    try:
        completed = subprocess.run(
            [binary, "--version"],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    match = _VERSION_RE.search(f"{completed.stdout}\n{completed.stderr}")
    if match is None:
        return None
    return tuple(int(part) for part in match.groups(default="0"))


class OverrideRefused(Exception):
    """`WICKED_ESTATE_DB` resolved outside the repository root."""

    def __init__(self, raw: str) -> None:
        super().__init__(raw)
        self.raw = raw


def _safe_override_path(raw: str, base: Path) -> Path | None:
    """Resolve an operator-supplied path override and confine it to ``base``.

    Returns the resolved path when it stays inside ``base``, and ``None``
    otherwise so the caller falls back to its trusted default.

    ``WICKED_ESTATE_DB`` is operator config, but this script runs
    automatically at the start of a workflow, so a stray or hostile value must
    not steer it at an arbitrary file — not only traversal (``../../etc/passwd``,
    CWE-22) but any absolute path to a secret, or a symlink that escapes after
    resolution (CWE-73). Containment is checked *after* ``resolve()``, so a
    symlink is validated at its real target rather than its lexical form.
    """
    raw = raw.strip()
    if not raw:
        return None
    try:
        resolved = Path(raw).expanduser().resolve()
        base_resolved = base.resolve()
    except (OSError, RuntimeError, ValueError):
        return None
    if not resolved.is_relative_to(base_resolved):
        print(
            f"ignoring out-of-bounds {DB_ENV_VAR} override {raw!r} "
            f"(must resolve within {base_resolved})",
            file=sys.stderr,
        )
        return None
    return resolved


def resolve_db(explicit: str | None, root: Path) -> Path:
    """Resolve the graph path using the CLI's own precedence order.

    Explicit ``--db`` beats ``WICKED_ESTATE_DB``, which beats the default. The
    explicit argument is a direct instruction from the caller and is taken as
    given; the environment variable is ambient and is confined to *root*.
    """
    if explicit:
        return Path(explicit).expanduser()
    raw = os.environ.get(DB_ENV_VAR, "").strip()
    if raw:
        confined = _safe_override_path(raw, root)
        if confined is None:
            # Refused, not absent. Falling through to the default here would
            # report `index-absent` for a graph that exists and that the CLI
            # itself would happily read, and would tell the caller to rebuild
            # it at a path they did not choose.
            raise OverrideRefused(raw)
        return confined
    return root / DEFAULT_DB_RELPATH


def install_with_consent(*, assume_yes: bool) -> bool:
    """Run the pinned Tier-2 install, gated on cargo presence and consent.

    Returns True only when the binary resolves afterwards. Cargo must already be
    on PATH: the policy permits installing through a package manager the user
    demonstrably has, never bootstrapping one.
    """
    if shutil.which("cargo") is None:
        print(
            "cargo is not on PATH, so this skill will not install anything.\n"
            "Install Rust from https://rustup.rs, then run:\n"
            f"  {' '.join(INSTALL_COMMAND)}",
            file=sys.stderr,
        )
        return False

    if not assume_yes:
        print(
            "wicked-estate is not installed. Proposed command (no sudo, pinned):\n"
            f"  {' '.join(INSTALL_COMMAND)}\n"
            "This compiles from source and can take several minutes.",
            file=sys.stderr,
        )
        print(
            "Re-run with --install --yes to proceed, or run the command yourself.",
            file=sys.stderr,
        )
        return False

    completed = subprocess.run(INSTALL_COMMAND, check=False)
    if completed.returncode != 0:
        print(f"install failed with exit code {completed.returncode}", file=sys.stderr)
        return False
    # Re-verify rather than trusting PATH within this session.
    return find_binary() is not None


def build_report(*, root: Path, explicit_db: str | None) -> tuple[int, dict[str, object]]:
    """Return the exit code and a JSON-serializable status report."""
    binary = find_binary()
    if binary is None:
        return EXIT_BINARY_ABSENT, {
            "status": "binary-absent",
            "remediation": " ".join(INSTALL_COMMAND),
        }

    version = read_version(binary)
    try:
        db = resolve_db(explicit_db, root)
    except OverrideRefused as refused:
        return EXIT_OVERRIDE_REFUSED, {
            "status": "override-refused",
            "binary": binary,
            "version": ".".join(str(p) for p in version) if version else None,
            "override": refused.raw,
            "remediation": (
                f"{DB_ENV_VAR} resolves outside {root}. Pass --db "
                f"{refused.raw} explicitly, or move the graph inside the "
                "repository."
            ),
        }
    report: dict[str, object] = {
        "binary": binary,
        "version": ".".join(str(p) for p in version) if version else None,
        "database": str(db),
    }

    if version is not None and version[: len(MINIMUM_VERSION)] < MINIMUM_VERSION:
        floor = ".".join(str(p) for p in MINIMUM_VERSION)
        report["status"] = "version-below"
        report["remediation"] = " ".join(INSTALL_COMMAND)
        report["required"] = floor
        return EXIT_VERSION_BELOW, report

    if not db.exists():
        report["status"] = "index-absent"
        report["remediation"] = f"wicked-estate index {root}"
        return EXIT_INDEX_ABSENT, report

    report["status"] = "ready"
    return EXIT_READY, report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Preflight the Wicked Estate CLI and its index.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report readiness and exit with the status code (default action).",
    )
    parser.add_argument(
        "--install",
        action="store_true",
        help="Offer the pinned Tier-2 install when the binary is absent.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Record explicit consent for --install. Without it, --install only proposes.",
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Repository root used to resolve the default index path.",
    )
    parser.add_argument("--db", default=None, help="Explicit graph database path.")
    parser.add_argument("--json", action="store_true", help="Emit the report as JSON.")
    args = parser.parse_args(argv)

    root = Path(args.root).expanduser().resolve()

    wants_install = args.install and find_binary() is None
    if wants_install and not install_with_consent(assume_yes=args.yes):
        return EXIT_INSTALL_FAILED

    code, report = build_report(root=root, explicit_db=args.db)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for key in ("status", "binary", "version", "database", "required", "remediation"):
            if key in report and report[key] is not None:
                print(f"{key}: {report[key]}")
    return code


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
