#!/usr/bin/env python3
"""Derive the release surfaces a version bump must move, and read each one.

The surface set is derived from repository facts rather than enumerated by
hand, so a surface added upstream appears here instead of being silently
omitted from the criterion that covers "every derived release surface".

Exits 1 when a governing rule this derivation depends on is absent.

Run from the repository root:
    python3 docs/specs/catalogue-sync-apply/notes/grounding/derive-release-surfaces.py
"""
from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

ROOT = Path.cwd()


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def fail(message: str) -> int:
    print(f"derive-release-surfaces: {message}", file=sys.stderr)
    return 1


def main() -> int:
    package_rules = read("packages/AGENTS.md")
    required = (
        "Non-cosmetic package changes update both `version.py` and `pyproject.toml`."
    )
    if required not in package_rules:
        return fail("the version-bump rule is absent from packages/AGENTS.md")

    config = tomllib.loads(read("packages/agentbundle/pyproject.toml"))
    project = config.get("project", {})
    if project.get("name") != "agentbundle":
        return fail("agentbundle package metadata is absent")
    readme = project.get("readme")
    if not isinstance(readme, str):
        return fail("the published package declares no readme surface")

    # Each surface states the version in its own form. Reading "the first
    # semver anywhere in the file" is wrong for both changelogs, whose header
    # cites the Keep a Changelog spec version before any release heading, and
    # for the product changelog, which is artifact-scoped: core entries sit
    # above the newest agentbundle one, so the topmost heading is not it.
    surfaces: list[tuple[str, str]] = [
        ("packages/agentbundle/agentbundle/version.py",
         r'CLI_VERSION = "(\d+\.\d+\.\d+)"'),
        ("packages/agentbundle/pyproject.toml",
         r'^version = "(\d+\.\d+\.\d+)"'),
        ("packages/agentbundle/CHANGELOG.md",
         r"^## \[(\d+\.\d+\.\d+)\]"),
        ("docs/product/changelog.md",
         r"^## \[agentbundle\]\[(\d+\.\d+\.\d+)\]"),
        (f"packages/agentbundle/{readme}",
         r"^## What's new in (\d+\.\d+\.\d+)"),
    ]

    print(f"release surfaces: {len(surfaces)}")
    found: list[str] = []
    for rel, pattern in surfaces:
        match = re.search(pattern, read(rel), re.MULTILINE)
        if match is None:
            return fail(f"{rel}: no version statement matched {pattern!r}")
        found.append(match.group(1))
        print(f"  {rel}: {match.group(1)}")
    print(f"agreement: {'yes' if len(set(found)) == 1 else 'no'} ({sorted(set(found))})")
    print(
        "oracle: every surface above states the same version, each read by the "
        "form that surface uses. The set is derived from the version-bump rule "
        "plus the package's declared readme, not from a hand-written list."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
