#!/usr/bin/env python3
"""Gate G — release impact check.

Exits 1 when changed files include a release-impacting path AND the diff
contains no changelog fragment or version bump.  Exits 0 otherwise.

Usage (in CI — pass the merge-base SHA):
    python tools/repo/check_release_impact.py --base <sha>
    python tools/repo/check_release_impact.py --base origin/main
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

# Windows cp1252 guard — reconfigure stdout/stderr to UTF-8 before any print.
sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Paths whose changes imply a public interface change → a release is required.
RELEASE_IMPACTING_PREFIXES = (
    "packages/agentbundle/agentbundle/catalogue_tooling/",
    "packages/agentbundle/agentbundle/cli.py",
    "packages/agentbundle/agentbundle/_data/catalogue.schema.json",
    "packages/agentbundle/agentbundle/_data/pack.schema.json",
    "packages/agentbundle/agentbundle/_data/adapter.toml",
    "docs/contracts/",
)

# Paths that are explicitly repo governance — never release-impacting regardless
# of what RELEASE_IMPACTING_PREFIXES would say.
NON_IMPACTING_PREFIXES = (
    "catalogue.toml",
    "packs/",
    "profiles/",
    "tools/catalogue/",
    "tools/repo/",
    "web/",
    "site/",
    "docs/guides/",
    "docs/specs/",
    "docs/adr/",
    "docs/rfc/",
)

# A changed file matching one of these patterns indicates a planned release.
RELEASE_INDICATOR_PATTERNS = (
    r"packages/agentbundle/pyproject\.toml",
    r"packages/agentbundle/agentbundle/version\.py",
    r"docs/product/changelog\.md",
)


def _changed_files(base: str) -> list[str]:
    # Try three-dot diff (PR merge-base form) first; fall back to two-dot.
    for args in (
        ["git", "diff", "--name-only", f"{base}...HEAD"],
        ["git", "diff", "--name-only", base, "HEAD"],
    ):
        r = subprocess.run(args, capture_output=True, text=True, cwd=REPO_ROOT, check=False)
        if r.returncode == 0:
            return [f for f in r.stdout.splitlines() if f.strip()]
    return []


def is_release_impacting(path: str) -> bool:
    for prefix in NON_IMPACTING_PREFIXES:
        if path.startswith(prefix):
            return False
    return any(path.startswith(prefix) for prefix in RELEASE_IMPACTING_PREFIXES)


def has_release_indicator(changed: list[str]) -> bool:
    for f in changed:
        for pattern in RELEASE_INDICATOR_PATTERNS:
            if re.search(pattern, f):
                return True
    return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip())
    parser.add_argument("--base", required=True, help="Merge-base SHA or branch name")
    args = parser.parse_args(argv)

    changed = _changed_files(args.base)
    if not changed:
        print("check-release-impact: no changed files detected — pass")
        return 0

    impacting = [f for f in changed if is_release_impacting(f)]

    if not impacting:
        print(
            f"check-release-impact: {len(changed)} changed file(s), none release-impacting — pass"
        )
        return 0

    if has_release_indicator(changed):
        print(
            f"check-release-impact: {len(impacting)} release-impacting file(s) changed, "
            "release indicator present — pass"
        )
        for f in impacting:
            print(f"  ✓ {f}")
        return 0

    print(
        f"check-release-impact: {len(impacting)} release-impacting file(s) changed "
        "WITHOUT a release indicator — FAIL",
        file=sys.stderr,
    )
    print("Release-impacting files:", file=sys.stderr)
    for f in impacting:
        print(f"  {f}", file=sys.stderr)
    print(
        "\nAdd a changelog entry, version bump, or no-release declaration before merging.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
