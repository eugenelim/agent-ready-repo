#!/usr/bin/env python3
"""Check canonical pack npm parity, lock provenance, and npm configuration."""

from __future__ import annotations

import argparse
import json
import os
import stat
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

from lint_harness import Outcome, Rule, RuleAbort, run
from npm_project_discovery import DiscoveryError, canonical_projects

_REPO_ROOT = Path(__file__).resolve().parents[1]


def _parse(argv: list[str] | None) -> Path:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=_REPO_ROOT)
    args = parser.parse_args(argv)
    try:
        root = args.root.resolve(strict=True)
    except OSError as exc:
        raise RuleAbort(
            Outcome(f"lint-pack-npm-projects: unusable root {args.root}: {exc}", 2)
        ) from exc
    if not root.is_dir():
        raise RuleAbort(Outcome(f"lint-pack-npm-projects: root is not a directory: {root}", 2))
    return root


def _projects(root: Path) -> list[Path] | None:
    try:
        projects = [project.directory for project in canonical_projects(root)]
        _reject_npmrc(root)
        return projects
    except DiscoveryError as exc:
        raise RuleAbort(Outcome(f"lint-pack-npm-projects: {exc}", 2)) from exc


def _reject_npmrc(root: Path) -> None:
    """Refuse repository npm configuration without opening configuration files."""
    stack = [root]
    while stack:
        directory = stack.pop()
        try:
            entries = list(directory.iterdir())
        except OSError as exc:
            message = (
                "lint-pack-npm-projects: cannot read npm configuration directory "
                f"{directory}: {exc}"
            )
            raise RuleAbort(Outcome(message, 2)) from exc
        for entry in entries:
            if entry.name == ".npmrc":
                message = f"lint-pack-npm-projects: repository npm configuration refused: {entry}"
                raise RuleAbort(Outcome(message, 1))
            try:
                mode = os.lstat(entry).st_mode
            except OSError as exc:
                message = (
                    "lint-pack-npm-projects: cannot inspect npm configuration path "
                    f"{entry}: {exc}"
                )
                raise RuleAbort(Outcome(message, 2)) from exc
            if stat.S_ISLNK(mode):
                try:
                    resolved = entry.resolve(strict=True)
                    resolved.relative_to(root)
                except (OSError, RuntimeError, ValueError) as exc:
                    message = (
                        "lint-pack-npm-projects: npm configuration scan refused path "
                        f"outside repository root: {entry}"
                    )
                    raise RuleAbort(Outcome(message, 2)) from exc
                # Only a linked DIRECTORY is refused. A linked regular file hides
                # nothing from this scan: it has no children, and a symlink named
                # `.npmrc` was already refused by the name check above. Refusing
                # every symlink reds the gate on the repository's own tracked
                # `CLAUDE.md -> AGENTS.md` links.
                if resolved.is_dir():
                    message = (
                        "lint-pack-npm-projects: npm configuration scan refused linked "
                        f"directory {entry}"
                    )
                    raise RuleAbort(Outcome(message, 2))
                continue
            if not stat.S_ISDIR(mode):
                continue
            try:
                resolved = entry.resolve(strict=True)
                resolved.relative_to(root)
            except (OSError, RuntimeError, ValueError) as exc:
                message = (
                    "lint-pack-npm-projects: npm configuration scan refused path "
                    f"outside repository root: {entry}"
                )
                raise RuleAbort(Outcome(message, 2)) from exc
            stack.append(entry)


def _entry_identity(key: str, record: dict[str, object]) -> tuple[str, str] | None:
    """Return the package identity encoded by a non-root lockfile record."""
    version = record.get("version")
    parts = key.split("node_modules/")
    if not isinstance(version, str) or not version or len(parts) < 2 or not parts[-1]:
        return None
    return parts[-1], version


def _resolved_matches(identity: tuple[str, str], resolved: str) -> bool:
    """Require the registry tarball path to name the package and exact version."""
    name, version = identity
    parsed = urlparse(resolved)
    if parsed.scheme != "https" or parsed.netloc != "registry.npmjs.org":
        return False
    pathname = unquote(parsed.path)
    tarball = f"{name.rsplit('/', 1)[-1]}-{version}.tgz"
    return pathname.endswith(f"/-/{tarball}") and f"/{name}/-/" in pathname


def _provenance_violations(lockfile: Path) -> list[str]:
    """Return fail-closed provenance findings for a canonical lockfile."""
    try:
        data = json.loads(lockfile.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        message = f"lint-pack-npm-projects: cannot read lockfile {lockfile}: {exc}"
        raise RuleAbort(Outcome(message, 2)) from exc
    if not isinstance(data, dict):
        return [f"lint-pack-npm-projects: {lockfile}: lockfile root must be an object"]
    if data.get("lockfileVersion") not in (2, 3):
        return [f"lint-pack-npm-projects: {lockfile}: unsupported lockfileVersion"]
    packages = data.get("packages")
    if not isinstance(packages, dict):
        return [f"lint-pack-npm-projects: {lockfile}: packages must be an object"]

    examined = 0
    findings: list[str] = []
    for key, value in sorted(packages.items()):
        if key == "":
            continue
        examined += 1
        if not isinstance(key, str) or not isinstance(value, dict):
            findings.append(f"lint-pack-npm-projects: {lockfile}: invalid package record {key!r}")
            continue
        if "link" in value:
            findings.append(f"lint-pack-npm-projects: {lockfile}: linked package record {key}")
            continue
        identity = _entry_identity(key, value)
        if identity is None:
            findings.append(f"lint-pack-npm-projects: {lockfile}: invalid package identity {key}")
            continue
        resolved = value.get("resolved")
        if not isinstance(resolved, str) or not resolved:
            findings.append(f"lint-pack-npm-projects: {lockfile}: missing resolved URL for {key}")
            continue
        integrity = value.get("integrity")
        if (
            not isinstance(integrity, str)
            or not integrity.startswith("sha512-")
            or len(integrity) == len("sha512-")
        ):
            findings.append(
                f"lint-pack-npm-projects: {lockfile}: missing sha512 integrity for {key}"
            )
        if not _resolved_matches(identity, resolved):
            findings.append(
                f"lint-pack-npm-projects: {lockfile}: resolved URL does not name "
                f"{identity[0]}@{identity[1]}"
            )
    if not examined:
        findings.append(
            f"lint-pack-npm-projects: {lockfile}: no non-root package records examined"
        )
    return findings


def _violations(directory: Path) -> list[str]:
    manifest = directory / "package.json"
    lockfile = directory / "package-lock.json"
    if manifest.exists() and not lockfile.exists():
        return [f"lint-pack-npm-projects: {manifest}: missing sibling package-lock.json"]
    if lockfile.exists() and not manifest.exists():
        return [f"lint-pack-npm-projects: {lockfile}: missing sibling package.json"]
    if lockfile.exists():
        return _provenance_violations(lockfile)
    return []


def _pass(root: Path, count: int) -> str:
    return f"lint-pack-npm-projects: checked {count} canonical pack npm project(s) under {root}"


def _empty(root: Path) -> Outcome:
    return Outcome(f"lint-pack-npm-projects: no canonical pack npm project under {root}", 2)


RULE = Rule(
    parse=_parse,
    files=_projects,
    predicate=_violations,
    pass_line=_pass,
    empty_scan=_empty,
    absent_root=_empty,
    summary=lambda count: f"lint-pack-npm-projects: {count} project mismatch(es)",
)


def main(argv: list[str] | None = None) -> int:
    """Run the canonical manifest/lockfile parity rule."""
    return run(RULE, argv)


if __name__ == "__main__":
    sys.exit(main())
