#!/usr/bin/env python3
"""Bootstrap only the requested frontend dependency profile."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PROFILES = ("web", "docs-site", "sites")


class BootstrapError(RuntimeError):
    """An actionable bootstrap configuration or execution error."""


def profile_commands(profile: str) -> tuple[tuple[str, ...], ...]:
    """Return the exact npm commands belonging to one bootstrap profile."""
    if profile == "web":
        return (("npm", "ci", "--prefix", "web"),)
    if profile == "docs-site":
        return (("npm", "ci", "--prefix", "docs-site"),)
    if profile == "sites":
        return (
            ("npm", "ci", "--prefix", "web"),
            ("npm", "ci", "--prefix", "docs-site"),
        )
    choices = ", ".join(PROFILES)
    raise BootstrapError(f"unknown profile {profile!r}; choose one of: {choices}")


def bootstrap(
    profile: str,
    *,
    repo_root: Path = REPO_ROOT,
    install_gate_browser: bool = False,
    browsers_path: str | None = None,
) -> int:
    """Install only the npm dependency trees selected by ``profile``."""
    if install_gate_browser and profile == "docs-site":
        raise BootstrapError("--install-gate-browser requires the web or sites profile")
    commands = profile_commands(profile)
    if shutil.which("npm") is None:
        raise BootstrapError("npm was not found; install Node.js/npm before bootstrapping")
    for profile_command in commands:
        try:
            result = subprocess.run(profile_command, cwd=repo_root, check=False)
        except FileNotFoundError as error:
            raise BootstrapError(
                "npm could not be started; install Node.js/npm before bootstrapping"
            ) from error
        if result.returncode != 0:
            return result.returncode
    if install_gate_browser:
        command: list[str] = [
            sys.executable,
            str(repo_root / "tools" / "repo" / "frontend_runtime.py"),
            "install-browsers",
        ]
        if browsers_path is not None:
            command.extend(("--browsers-path", browsers_path))
        result = subprocess.run(command, cwd=repo_root, check=False)
        return result.returncode
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", nargs="?", choices=PROFILES)
    parser.add_argument(
        "--install-gate-browser",
        action="store_true",
        help="also install the Chromium browser used by the web gate",
    )
    parser.add_argument("--browsers-path", help="shared Playwright browser cache")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the selective-bootstrap command-line interface."""
    args = _parser().parse_args(argv)
    if args.profile is None:
        profiles = ", ".join(PROFILES)
        print(f"error: select a bootstrap profile: {profiles}", file=sys.stderr)
        return 2
    try:
        return bootstrap(
            args.profile,
            install_gate_browser=args.install_gate_browser,
            browsers_path=args.browsers_path,
        )
    except BootstrapError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
