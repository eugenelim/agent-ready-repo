#!/usr/bin/env python3
"""Reject catalogue conformance tests that cannot run in another catalogue.

Two classes are rejected: a test that names a shipped pack, and a test that
reaches a repository-only directory. A shipped conformance test must be
rule-shaped -- it asserts that *any* catalogue is well-formed -- so a path only
this repository has makes it fail on an adopter's first run.
"""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from pathlib import Path


def _pack_names(catalogue_root: Path) -> list[str]:
    names: list[str] = []
    for manifest in sorted((catalogue_root / "packs").glob("*/pack.toml")):
        data = tomllib.loads(manifest.read_text(encoding="utf-8"))
        name = data.get("pack", {}).get("name")
        if isinstance(name, str) and name:
            names.append(name)
    return names


# Top-level directories this repository has and a catalogue built from
# `catalogue init` does not. A conformance test that reaches one of them is
# repository-only by construction, whatever its filename suggests, and belongs
# with its real owner rather than in the shipped set.
_REPO_ONLY_SEGMENTS = ("packages", "tools", "docs")

# `CATALOGUE_ROOT / "packages"` and a bare `"packages/agentbundle"` literal are
# the two ways the reach is written; neither is visible to a pack-name search.
_ROOT_JOIN = re.compile(
    r"/\s*[\"'](" + "|".join(_REPO_ONLY_SEGMENTS) + r")[\"']"
)
_PATH_LITERAL = re.compile(
    r"[\"'](?:" + "|".join(_REPO_ONLY_SEGMENTS) + r")/"
)


def find_repo_only_references(catalogue_root: Path) -> list[str]:
    """Return line-addressed repository-only path reaches in conformance tests."""
    violations: list[str] = []
    for path in sorted((catalogue_root / "tests" / "conformance").rglob("*.py")):
        for line_number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            match = _ROOT_JOIN.search(line) or _PATH_LITERAL.search(line)
            if not match:
                continue
            segment = match.group(0).strip("/\"' ")
            relative = path.relative_to(catalogue_root)
            violations.append(
                f"{relative}:{line_number}: reaches repository-only "
                f"{segment.split('/')[0]!r}"
            )
    return violations


def find_violations(catalogue_root: Path) -> list[str]:
    """Return line-addressed specific-pack references in conformance tests."""
    names = _pack_names(catalogue_root)
    patterns = {
        name: re.compile(
            rf"(?<![A-Za-z0-9_-]){re.escape(name)}(?![A-Za-z0-9_-])"
        )
        for name in names
    }
    violations: list[str] = []
    for path in sorted((catalogue_root / "tests" / "conformance").rglob("*.py")):
        for line_number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            for name, pattern in patterns.items():
                if not pattern.search(line):
                    continue
                if name == "contracts" and re.search(
                    r"CATALOGUE_ROOT\s*/\s*['\"]contracts['\"]", line
                ):
                    continue
                # Text-lint, not URL sanitisation: skip a line that names the
                # `github` pack only because it mentions the github.com domain.
                # Uses a regex search rather than a `"github.com" in line`
                # substring test so it is not misread as host-allowlisting.
                if name == "github" and re.search(r"github\.com", line):
                    continue
                relative = path.relative_to(catalogue_root)
                violations.append(f"{relative}:{line_number}: names pack {name!r}")
    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    root = args.root.resolve()
    violations = find_violations(root)
    if violations:
        print("conformance-portability: specific pack references found:", file=sys.stderr)
        for violation in violations:
            print(f"  {violation}", file=sys.stderr)
        return 1
    repo_only = find_repo_only_references(root)
    if repo_only:
        print(
            "conformance-portability: repository-only references found "
            "(move the test to its owner, e.g. tests/roster/):",
            file=sys.stderr,
        )
        for violation in repo_only:
            print(f"  {violation}", file=sys.stderr)
        return 1
    print("conformance-portability: passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
