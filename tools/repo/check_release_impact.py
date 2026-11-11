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
    # The authored contract tree. This used to read "docs/contracts/", a
    # directory ADR-0055 deleted, so the entry gated nothing. It was not a live
    # hole while every contract had a packaged twin — contracts/adapter.toml is
    # byte-identical to the _data/ copy listed above (test_contract_files_
    # byte_identical pins that), so a real change tripped the gate through the
    # twin. It becomes a hole the moment a contracts/ file has no twin, which
    # catalogue.schema.json and guide.schema.json already do not.
    "contracts/",
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
    "docs-site/",
    "docs/guides/",
    "docs/specs/",
    "docs/adr/",
    "docs/rfc/",
)

# Documentation *about* a contract is not itself contract surface. The
# "contracts/" prefix above is a whole-directory match, so without this a README
# edit demanded an agentbundle release — observed on the first docs-only PR after
# that prefix landed. What the CLI bundles byte-identically into `_data/` is the
# contract files; no Markdown in this tree has a packaged twin.
NON_IMPACTING_SUFFIXES_UNDER = (
    ("contracts/", ".md"),
)

# A changed file matching one of these patterns indicates a planned release.
# These match by presence alone (add/modify/delete all count).
RELEASE_INDICATOR_PATTERNS = (
    r"packages/agentbundle/pyproject\.toml",
    r"packages/agentbundle/agentbundle/version\.py",
    r"docs/product/changelog\.md",
)
# Fragment patterns require a file to be ADDED or MODIFIED (not deleted).
# Bundle-part additions and retraction-list changes are explicitly excluded (AC-B8a).
RELEASE_INDICATOR_ADDED_PATTERNS = (
    r"docs/product/changelog\.d/[^/]+\.md",
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


def _added_modified_files(base: str) -> list[str]:
    """Files added or modified (not deleted) relative to base (AC-B8a)."""
    for spec in (f"{base}...HEAD", f"{base} HEAD"):
        args = ["git", "diff", "--name-only", "--diff-filter=AM"] + spec.split()
        r = subprocess.run(args, capture_output=True, text=True, cwd=REPO_ROOT, check=False)
        if r.returncode == 0:
            return [f for f in r.stdout.splitlines() if f.strip()]
    return []


def is_release_impacting(path: str) -> bool:
    for prefix in NON_IMPACTING_PREFIXES:
        if path.startswith(prefix):
            return False
    for prefix, suffix in NON_IMPACTING_SUFFIXES_UNDER:
        if path.startswith(prefix) and path.endswith(suffix):
            return False
    return any(path.startswith(prefix) for prefix in RELEASE_IMPACTING_PREFIXES)


def has_release_indicator(
    changed: list[str], added: list[str] | None = None
) -> bool:
    """Return True when any changed file signals a planned release.

    AC-B8a: fragment additions count; fragment deletions, bundle-part additions,
    and retraction-list changes do not. When ``added`` is provided, fragment
    patterns are checked against it; when absent every file in ``changed`` is
    treated as added (backwards-compatible, used from tests that cannot supply
    the diff-filter output).
    """
    for f in changed:
        for pattern in RELEASE_INDICATOR_PATTERNS:
            if re.search(pattern, f):
                return True
    # Fragment patterns: only added/modified files count.
    added_set = set(changed if added is None else added)
    for f in added_set:
        for pattern in RELEASE_INDICATOR_ADDED_PATTERNS:
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

    added = _added_modified_files(args.base)
    if has_release_indicator(changed, added=added):
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
