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
from collections.abc import Sequence
from pathlib import Path

import lint_harness


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
_REPO_ONLY_SEGMENTS = ("packages", "tools", "docs", "contracts")
# `contracts` is here even though a shipped pack shares the name. The
# pack-name check below deliberately exempts `CATALOGUE_ROOT / "contracts"`
# as a path rather than a pack reference; for portability that expression is
# exactly the defect, because a catalogue from `catalogue init` has only
# tests/, packs/, guides/ and profiles/ at its root. The two checks read the
# same expression for opposite reasons, which is why neither can cover both.

# `CATALOGUE_ROOT / "packages"` and a bare `"packages/agentbundle"` literal are
# the two ways the reach is written; neither is visible to a pack-name search.
_ROOT_JOIN = re.compile(
    r"/\s*[\"'](" + "|".join(_REPO_ONLY_SEGMENTS) + r")[\"']"
)
_PATH_LITERAL = re.compile(
    r"[\"'](?:" + "|".join(_REPO_ONLY_SEGMENTS) + r")/"
)
# The predicate is handed one path at a time, so the scan root and the compiled
# pack-name patterns — both derived once from the root — are parked here by
# `_files`. The two are read-only for the rest of the run.
_STATE: dict[str, object] = {}

# The two violation classes are reported under different headers and the
# pack-name class suppresses the other entirely, so each message carries its
# class through the driver's single violation list. A NUL cannot occur in a
# path or a pack name, so the tag cannot collide with message text.
_PACK_TAG = "\x00pack\x00"
_REPO_ONLY_TAG = "\x00repo-only\x00"


def _name_patterns(catalogue_root: Path) -> dict[str, re.Pattern[str]]:
    return {
        name: re.compile(
            rf"(?<![A-Za-z0-9_-]){re.escape(name)}(?![A-Za-z0-9_-])"
        )
        for name in _pack_names(catalogue_root)
    }


def _repo_only_in_file(path: Path, catalogue_root: Path) -> list[str]:
    """Return this file's repository-only path reaches, in line order."""
    violations: list[str] = []
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


def find_repo_only_references(catalogue_root: Path) -> list[str]:
    """Return line-addressed repository-only path reaches in conformance tests.

    Bound worth stating: this reads text, so it catches the two spellings that
    appear in practice -- a literal join and a bare path literal -- and cannot
    see a segment assembled from a variable or split across lines. It is a
    barrier against the accident, not a proof of portability.
    """
    violations: list[str] = []
    for path in sorted((catalogue_root / "tests" / "conformance").rglob("*.py")):
        violations.extend(_repo_only_in_file(path, catalogue_root))
    return violations


def _pack_names_in_file(
    path: Path, catalogue_root: Path, patterns: dict[str, re.Pattern[str]]
) -> list[str]:
    """Return this file's specific-pack references, in line order."""
    violations: list[str] = []
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


def find_violations(catalogue_root: Path) -> list[str]:
    """Return line-addressed specific-pack references in conformance tests."""
    patterns = _name_patterns(catalogue_root)
    violations: list[str] = []
    for path in sorted((catalogue_root / "tests" / "conformance").rglob("*.py")):
        violations.extend(_pack_names_in_file(path, catalogue_root, patterns))
    return violations


def _parse(argv: list[str] | None) -> Path:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    return parser.parse_args(argv).root.resolve()


def _conformance_tests(root: Path) -> list[Path] | None:
    """Return the conformance tests, or ``None`` when the directory is absent.

    The pack names are read first and unconditionally, as they were when this
    ran as one function: an unparseable `pack.toml` raises here whether or not
    there is anything to scan, and moving that behind the directory check would
    quietly change it.
    """
    _STATE["root"] = root
    _STATE["patterns"] = _name_patterns(root)
    conformance = root / "tests" / "conformance"
    if not conformance.is_dir():
        return None
    return sorted(conformance.rglob("*.py"))


def _references(path: Path) -> list[str]:
    """Return both violation classes for one conformance test, each tagged."""
    root = _STATE["root"]
    patterns = _STATE["patterns"]
    assert isinstance(root, Path) and isinstance(patterns, dict)
    return [
        _PACK_TAG + message
        for message in _pack_names_in_file(path, root, patterns)
    ] + [
        _REPO_ONLY_TAG + message
        for message in _repo_only_in_file(path, root)
    ]


def _report(violations: Sequence[str]) -> None:
    """Print one class under its own header.

    A specific-pack reference suppresses the repository-only report entirely,
    as it did when the two were sequential scans with an early return between
    them, so the second header is only reached when the first class is empty.
    """
    named = [v[len(_PACK_TAG):] for v in violations if v.startswith(_PACK_TAG)]
    if named:
        print("conformance-portability: specific pack references found:", file=sys.stderr)
        for violation in named:
            print(f"  {violation}", file=sys.stderr)
        return
    print(
        "conformance-portability: repository-only references found "
        "(move the test to its owner, e.g. tests/roster/):",
        file=sys.stderr,
    )
    for violation in violations:
        print(f"  {violation[len(_REPO_ONLY_TAG):]}", file=sys.stderr)


# A catalogue with no `tests/conformance` and one with an empty `tests/conformance`
# both scanned nothing and both passed before the move onto the driver. Kept
# that way deliberately: giving this rule a fail-closed guard it never had is a
# behaviour change, not a migration.
_PASSED = lint_harness.Outcome("conformance-portability: passed", 0, "stdout")

RULE = lint_harness.Rule(
    parse=_parse,
    files=_conformance_tests,
    predicate=_references,
    pass_line=lambda root, n: "conformance-portability: passed",
    empty_scan=lambda root: _PASSED,
    absent_root=lambda root: _PASSED,
    report=_report,
)


def main(argv: list[str] | None = None) -> int:
    """Run the portability lint and return its process exit status."""
    return lint_harness.run(RULE, argv)


if __name__ == "__main__":
    raise SystemExit(main())
