#!/usr/bin/env python3
"""Derive the release surfaces a version bump must move, and read each one.

Two of the three things this reports are derived and one is maintained, and
the difference matters to the criteria that cite it.

Derived: the readme surface, read from the package metadata, and each
surface's prose/literal kind, computed from that surface's own version
pattern. Maintained: the surface *list* itself. `packages/AGENTS.md` names
only `version.py` and `pyproject.toml`, so the three changelog-shaped surfaces
have no repository rule to derive them from and are listed below by hand. A
sixth surface added upstream is NOT picked up automatically - add it here.

So this file is where the release-surface set is *maintained*, not a place it
is inferred. AC-0097 and AC-0098 cite it so the set has one home rather than
being re-enumerated in prose; they do not claim it is self-discovering.

Exits 1 when a governing rule this derivation depends on is absent.

Run from the repository root:
    python3 docs/specs/catalogue-package-sync/notes/grounding/derive-release-surfaces.py
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
        # A sixth surface, added 2026-09-25 after CI caught it and this
        # derivation did not. `tests/roster/test_okf_catalogue_discovery.py`
        # pins the release version and asserts POSITION -- that the topmost
        # changelog and readme headings name it -- so a bump that leaves it
        # behind fails the roster suite while every surface above passes.
        # It is executable, unlike the five above, which is why the unit
        # suite could not see it: the roster suite is outside
        # `packages/agentbundle/tests/`.
        ("tests/roster/test_okf_catalogue_discovery.py",
         r'^    expected = "(\d+\.\d+\.\d+)"'),
    ]

    # A surface is `prose` when it carries adopter-facing narrative a criterion
    # can require a sentence of, and `literal` when the version is the whole of
    # what it states. Phase 4's AC-0098 quantifies over the prose surfaces
    # only: a criterion asking version.py to describe a flag is unsatisfiable,
    # and an unsatisfiable criterion is worse than an absent one.
    #
    # Decided from the surface's own pattern above rather than from a second
    # hand-written list: a Markdown heading is how a narrative surface states
    # its version, an assignment is how a literal one does. Keeping this a
    # function of the table means adding a surface cannot leave its kind
    # unset, which a parallel set would.
    def surface_kind(pattern: str) -> str:
        # Fail loudly on a pattern that is neither shape. A silent "literal"
        # default would quietly shrink AC-0098's quantifier: a prose surface
        # that stated its version as `Version: 0.51.0` would be marked literal
        # and drop out of the criterion with no error anywhere.
        body = pattern.lstrip("^")
        if body.startswith("## "):
            return "prose"
        if " = " in body or body.startswith("version = "):
            return "literal"
        raise ValueError(
            f"unclassifiable release-surface pattern {pattern!r}: it is "
            "neither a Markdown heading nor an assignment, so its prose/"
            "literal kind cannot be derived. Classify it explicitly."
        )

    print(f"release surfaces: {len(surfaces)}")
    found: list[str] = []
    prose_count = 0
    for rel, pattern in surfaces:
        match = re.search(pattern, read(rel), re.MULTILINE)
        if match is None:
            return fail(f"{rel}: no version statement matched {pattern!r}")
        found.append(match.group(1))
        kind = surface_kind(pattern)
        prose_count += kind == "prose"
        print(f"  {rel}: {match.group(1)} [{kind}]")
    print(f"agreement: {'yes' if len(set(found)) == 1 else 'no'} ({sorted(set(found))})")
    print(f"prose surfaces: {prose_count} of {len(surfaces)}")
    print(
        "oracle: every surface above states the same version, each read by the "
        "form that surface uses. The readme surface and every prose/literal "
        "mark are derived; the surface list is maintained in this file, which "
        "is the one home AC-0097 and AC-0098 quantify over."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
