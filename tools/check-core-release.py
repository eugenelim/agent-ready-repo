#!/usr/bin/env python3
"""Delivery-time check that a core pack release is internally consistent.

Four facts, checked together because a release that gets any one of them wrong
ships a version string naming a code state nobody can reconstruct:

  1. `pack.toml` and `.claude-plugin/plugin.json` declare the same version.
  2. That version is the patch successor of the version at a named base commit
     — same major, same minor, patch exactly one greater.
  3. The topmost core entry in the changelog names that version.
  4. That entry carries a `### Highlights` subsection with at least one bullet.

The base commit is an explicit argument, never inferred. An unresolvable base
exits non-zero rather than defaulting to a guess: a check that silently picks
its own expectation is not a check.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path

PACK_TOML = "packs/core/pack.toml"
PLUGIN_JSON = "packs/core/.claude-plugin/plugin.json"
CHANGELOG = "docs/product/changelog.md"
# A free-standing release heading: `## [<pack>][<version>] — <date>`.
RELEASE_HEADING = re.compile(r"^## \[([a-z0-9-]+)\]\[([0-9]+\.[0-9]+\.[0-9]+)\]", re.M)


class Refusal(Exception):
    """A stated reason the release is not consistent."""


def _version_at(root: Path, ref: str | None) -> str:
    """The core version in `pack.toml`, at `ref` when given, else on disk."""
    if ref is None:
        data = tomllib.loads((root / PACK_TOML).read_text(encoding="utf-8"))
        return str(data["pack"]["version"])
    proc = subprocess.run(
        ["git", "show", f"{ref}:{PACK_TOML}"],
        cwd=root, capture_output=True, text=True, check=False,
    )
    if proc.returncode != 0:
        raise Refusal(f"base commit {ref!r} does not resolve")
    return str(tomllib.loads(proc.stdout)["pack"]["version"])


def _plugin_version(root: Path) -> str:
    return str(json.loads((root / PLUGIN_JSON).read_text(encoding="utf-8"))["version"])


def _patch_successor(base: str) -> str:
    major, minor, patch = (int(p) for p in base.split("."))
    return f"{major}.{minor}.{patch + 1}"


def _topmost_core_entry(text: str) -> tuple[str, str]:
    """The first core release heading's version, and the body beneath it.

    Topmost, not 'anywhere in the file': a check that searches the whole
    changelog passes on a release whose own entry is missing but whose version
    appears in an older one.
    """
    for match in RELEASE_HEADING.finditer(text):
        if match.group(1) != "core":
            continue
        body = text[match.end():]
        # Equal-or-shallower, not "the next release heading": a sibling `##`
        # section carrying its own `### Highlights` would otherwise be read as
        # belonging to this entry.
        nxt = re.search(r"^#{1,2} ", body, re.M)
        return match.group(2), body[: nxt.start()] if nxt else body
    raise Refusal("no core release entry found in the changelog")


def _has_highlight_bullet(entry_body: str) -> bool:
    if "### Highlights" not in entry_body:
        return False
    section = entry_body.split("### Highlights", 1)[1].split("\n### ", 1)[0]
    return bool(re.search(r"^\s*[-*] \S", section, re.M))


def check(root: Path, base: str) -> list[str]:
    """Return the refusal reasons; empty means the release is consistent."""
    reasons: list[str] = []
    try:
        declared = _version_at(root, None)
        expected = _patch_successor(_version_at(root, base))
    except Refusal as exc:
        return [str(exc)]

    plugin = _plugin_version(root)
    if declared != plugin:
        reasons.append(f"{PACK_TOML} says {declared}, {PLUGIN_JSON} says {plugin}")
    if declared != expected:
        reasons.append(f"version is {declared}, expected the patch successor {expected}")

    try:
        named, body = _topmost_core_entry((root / CHANGELOG).read_text(encoding="utf-8"))
    except Refusal as exc:
        reasons.append(str(exc))
        return reasons
    if named != declared:
        reasons.append(f"topmost core changelog entry names {named}, not {declared}")
    elif not _has_highlight_bullet(body):
        reasons.append(f"core {named} entry carries no Highlights bullet")
    return reasons


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, help="base commit to compare against")
    parser.add_argument("--root", default=".", help="repository root")
    args = parser.parse_args(argv)

    reasons = check(Path(args.root).resolve(), args.base)
    for reason in reasons:
        print(f"check-core-release: {reason}", file=sys.stderr)
    if not reasons:
        print("check-core-release: release is consistent")
    return 1 if reasons else 0


if __name__ == "__main__":
    raise SystemExit(main())
