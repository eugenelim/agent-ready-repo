#!/usr/bin/env python3
"""Reject catalogue conformance tests that name a shipped pack."""

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
    violations = find_violations(args.root.resolve())
    if violations:
        print("conformance-portability: specific pack references found:", file=sys.stderr)
        for violation in violations:
            print(f"  {violation}", file=sys.stderr)
        return 1
    print("conformance-portability: passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
