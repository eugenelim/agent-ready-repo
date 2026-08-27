#!/usr/bin/env python3
"""Check npm install-script entries against each project's ``allowScripts``.

An install script is arbitrary code executed during dependency installation.
Every ``packages`` entry in a committed ``package-lock.json`` whose
``hasInstallScript`` flag is true must therefore have an exact ``name@version``
key in the sibling ``package.json`` ``allowScripts`` map. The reverse direction
is also enforced: a stale allowlist key is a standing permission for a package
that is not present, so its later return at another version could escape fresh
review.

Lockfiles are discovered rather than hardcoded, so a third npm project cannot
appear without this gate noticing. Discovery mirrors ``tools/audit-npm.py``:
walk from the repository root, prune ``node_modules`` and dot-directories, skip
symlinked directories for loop safety, and sort the result for stable output.
That script exposes the discovery function from a hyphenated executable rather
than an importable helper module; mirroring the small walk keeps both standalone
tools conventional and avoids dynamic execution of one gate from another.

Usage:
    lint-npm-allow-scripts.py [--root DIR]

Exit codes deliberately preserve three outcomes, as ``tools/audit-npm.py`` and
``tools/test-all.py`` do. A policy violation and a check that never actually ran
are different facts; conflating them lets an unavailable or malformed input look
like an ordinary finding and obscures that the repository was never checked.

  0  every discovered project's install-script set exactly matches allowScripts.
  1  at least one install-script entry is unallowlisted, or an allowScripts key
     is stale.
  2  the checker could not run: no lockfile was discovered; required JSON was
     unreadable or unparseable; a lockfile had no usable ``packages`` map; or a
     sibling package.json had no usable ``allowScripts`` map.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

_REPO_ROOT = Path(__file__).resolve().parents[1]
_LOCKFILE_NAME = "package-lock.json"
_PRUNED_DIR_NAMES = frozenset({"node_modules"})


class CheckError(Exception):
    """The checker could not establish a verdict and must exit 2."""


@dataclass(frozen=True)
class ProjectVerdict:
    """One npm project's exact set comparison."""

    lockfile: Path
    install_scripts: set[str]
    allow_scripts: set[str]

    @property
    def unallowlisted(self) -> set[str]:
        """Install-script packages that have not been reviewed and permitted."""
        return self.install_scripts - self.allow_scripts

    @property
    def stale(self) -> set[str]:
        """Standing permissions with no matching install-script package."""
        return self.allow_scripts - self.install_scripts


def discover_lockfiles(root: Path) -> list[Path]:
    """Return every project package-lock under *root*, sorted for stable output."""
    found: list[Path] = []
    stack = [root]
    while stack:
        current = stack.pop()
        try:
            entries = list(current.iterdir())
        except OSError as exc:
            # Match audit-npm's fail-visible discovery idiom: partial walk
            # failures are never silent, while the total-empty guard below
            # still refuses a vacuous green result.
            print(
                f"lint-npm-allow-scripts: warning: cannot read {current}: {exc}",
                file=sys.stderr,
            )
            continue
        for entry in entries:
            if entry.is_dir():
                if (
                    entry.is_symlink()
                    or entry.name in _PRUNED_DIR_NAMES
                    or entry.name.startswith(".")
                ):
                    continue
                stack.append(entry)
            elif entry.name == _LOCKFILE_NAME:
                found.append(entry)
    return sorted(found)


def _load_json(path: Path) -> object:
    """Read one UTF-8 JSON file, converting all input failures to exit-2 errors."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CheckError(f"cannot read valid JSON from {path}: {exc}") from exc


def _install_script_key(lockfile: Path, package_path: str, entry: object) -> str | None:
    """Return ``name@version`` for one install-script package, else ``None``."""
    if not isinstance(entry, dict):
        raise CheckError(
            f"{lockfile}: packages entry {package_path!r} is not a JSON object"
        )
    if entry.get("hasInstallScript") is not True:
        return None

    marker = "node_modules/"
    if marker not in package_path:
        raise CheckError(
            f"{lockfile}: install-script entry {package_path!r} has no "
            f"{marker!r} segment from which to derive its package name"
        )
    name = package_path.rsplit(marker, 1)[1]
    version = entry.get("version")
    if not name or not isinstance(version, str) or not version:
        raise CheckError(
            f"{lockfile}: install-script entry {package_path!r} has no usable version"
        )
    return f"{name}@{version}"


def check_project(lockfile: Path) -> ProjectVerdict:
    """Load and compare one lockfile and its sibling package manifest."""
    lock_data = _load_json(lockfile)
    if not isinstance(lock_data, dict) or "packages" not in lock_data:
        raise CheckError(f"{lockfile}: lockfile has no `packages` key")
    packages = lock_data["packages"]
    if not isinstance(packages, dict):
        raise CheckError(f"{lockfile}: `packages` must be a JSON object")

    install_scripts: set[str] = set()
    for package_path, entry in packages.items():
        key = _install_script_key(lockfile, package_path, entry)
        if key is not None:
            install_scripts.add(key)

    package_json = lockfile.with_name("package.json")
    package_data = _load_json(package_json)
    if not isinstance(package_data, dict) or "allowScripts" not in package_data:
        raise CheckError(f"{package_json}: package.json has no `allowScripts` key")
    allow_scripts = package_data["allowScripts"]
    if not isinstance(allow_scripts, dict):
        raise CheckError(f"{package_json}: `allowScripts` must be a JSON object")

    return ProjectVerdict(
        lockfile=lockfile,
        install_scripts=install_scripts,
        allow_scripts=set(allow_scripts),
    )


def _relative(path: Path, root: Path) -> str:
    """Render a stable POSIX-style path for diagnostics on every platform."""
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _validated_root(candidate: Path | None) -> Path:
    """Resolve ``--root`` and reject unusable values without a traceback."""
    raw = candidate if candidate is not None else _REPO_ROOT
    try:
        root = raw.resolve()
    except (OSError, ValueError, RuntimeError) as exc:
        raise SystemExit(
            f"lint-npm-allow-scripts: --root is not a usable path: {raw!r} ({exc})"
        ) from exc
    if not root.exists():
        raise SystemExit(f"lint-npm-allow-scripts: --root does not exist: {root}")
    if not root.is_dir():
        raise SystemExit(f"lint-npm-allow-scripts: --root is not a directory: {root}")
    return root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=None)
    args = parser.parse_args(argv)
    root = _validated_root(args.root)

    lockfiles = discover_lockfiles(root)
    if not lockfiles:
        print(
            f"lint-npm-allow-scripts: no {_LOCKFILE_NAME} discovered under {root}",
            file=sys.stderr,
        )
        return 2

    try:
        verdicts = [check_project(lockfile) for lockfile in lockfiles]
    except CheckError as exc:
        print(f"lint-npm-allow-scripts: could not run: {exc}", file=sys.stderr)
        return 2

    failed = False
    for verdict in verdicts:
        display = _relative(verdict.lockfile, root)
        for key in sorted(verdict.unallowlisted):
            failed = True
            print(
                f"lint-npm-allow-scripts: {display}: unallowlisted install-script "
                f"entry {key}",
                file=sys.stderr,
            )
        for key in sorted(verdict.stale):
            failed = True
            print(
                f"lint-npm-allow-scripts: {display}: stale allowScripts entry {key}",
                file=sys.stderr,
            )
        if not verdict.unallowlisted and not verdict.stale:
            checked = ", ".join(sorted(verdict.install_scripts)) or "none"
            print(
                f"lint-npm-allow-scripts: {display}: ok — install-script entries "
                f"match allowScripts ({checked})"
            )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
