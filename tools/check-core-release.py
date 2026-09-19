#!/usr/bin/env python3
"""Delivery-time check that a core pack release is internally consistent.

Five facts, checked together because a release that gets any one of them wrong
ships a version string naming a code state nobody can reconstruct:

  1. `pack.toml` and `.claude-plugin/plugin.json` declare the same version.
  2. That version is the patch successor of the version at a named base commit
     — same major, same minor, patch exactly one greater.
  3. The topmost core entry in the changelog names that version.
  4. That entry carries a `### Highlights` subsection with at least one bullet.
  5. The `/now/` payload carries that entry's bullets, read independently of
     the projection's own parser.

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
        try:
            data = tomllib.loads((root / PACK_TOML).read_text(encoding="utf-8"))
        except OSError as exc:
            raise Refusal(f"cannot read {PACK_TOML}: {exc.strerror}") from exc
        except UnicodeDecodeError as exc:
            raise Refusal(f"{PACK_TOML} is not valid UTF-8: {exc}") from exc
        except tomllib.TOMLDecodeError as exc:
            raise Refusal(f"{PACK_TOML} is not valid TOML: {exc}") from exc
        try:
            return str(data["pack"]["version"])
        except (KeyError, TypeError) as exc:
            raise Refusal(f"{PACK_TOML} has no [pack].version") from exc
    proc = subprocess.run(
        ["git", "show", f"{ref}:{PACK_TOML}"],
        cwd=root, capture_output=True, text=True, check=False,
    )
    if proc.returncode != 0:
        raise Refusal(f"base commit {ref!r} does not resolve")
    try:
        return str(tomllib.loads(proc.stdout)["pack"]["version"])
    except (tomllib.TOMLDecodeError, KeyError, TypeError) as exc:
        raise Refusal(f"{PACK_TOML} at {ref} has no readable [pack].version") from exc


def _plugin_version(root: Path) -> str:
    try:
        data = json.loads((root / PLUGIN_JSON).read_text(encoding="utf-8"))
    except OSError as exc:
        raise Refusal(f"cannot read {PLUGIN_JSON}: {exc.strerror}") from exc
    except UnicodeDecodeError as exc:
        raise Refusal(f"{PLUGIN_JSON} is not valid UTF-8: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise Refusal(f"{PLUGIN_JSON} is not valid JSON: {exc}") from exc
    try:
        return str(data["version"])
    except (KeyError, TypeError) as exc:
        raise Refusal(f"{PLUGIN_JSON} has no version field") from exc


def _patch_successor(base: str) -> str:
    try:
        major, minor, patch = (int(p) for p in base.split("."))
    except ValueError as exc:
        raise Refusal(f"base version {base!r} is not major.minor.patch") from exc
    return f"{major}.{minor}.{patch + 1}"


def _live(text: str) -> str:
    """Markdown that renders: fenced blocks and HTML comments removed.

    A changelog heading shown as an example inside a fence is not a release.
    """
    # Both CommonMark fence characters, any info string: a tilde-fenced example
    # changelog entry would otherwise be read as a real release.
    without_fences, marker, skipping = [], None, False
    for line in text.splitlines():
        opener = re.match(r"^\s{0,3}(`{3,}|~{3,})(.*)$", line)
        if not skipping and opener:
            marker, skipping = opener.group(1), True
            continue
        if skipping:
            if opener and opener.group(1)[0] == marker[0] \
                    and len(opener.group(1)) >= len(marker) and not opener.group(2).strip():
                skipping, marker = False, None
            continue
        without_fences.append(line)
    return re.sub(r"<!--.*?-->", "", "\n".join(without_fences), flags=re.S)


def _topmost_core_entry(text: str) -> tuple[str, str]:
    """The first core release heading's version, and the body beneath it.

    Topmost, not 'anywhere in the file': a check that searches the whole
    changelog passes on a release whose own entry is missing but whose version
    appears in an older one.
    """
    text = _live(text)
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
    # Anchored: a substring match lets ordinary prose mentioning the words
    # stand in for the heading the projection actually reads.
    head = re.search(r"^### Highlights\s*$", entry_body, re.M)
    if head is None:
        return False
    section = entry_body[head.end():].split("\n### ", 1)[0]
    return bool(re.search(r"^\s*[-*] \S", section, re.M))


def check(root: Path, base: str) -> list[str]:
    """Return the refusal reasons; empty means the release is consistent."""
    reasons: list[str] = []
    try:
        declared = _version_at(root, None)
        expected = _patch_successor(_version_at(root, base))
    except Refusal as exc:
        return [str(exc)]

    try:
        plugin = _plugin_version(root)
    except Refusal as exc:
        return [str(exc)]
    if declared != plugin:
        reasons.append(f"{PACK_TOML} says {declared}, {PLUGIN_JSON} says {plugin}")
    if declared != expected:
        reasons.append(f"version is {declared}, expected the patch successor {expected}")

    try:
        changelog = (root / CHANGELOG).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        reasons.append(f"cannot read {CHANGELOG}: {exc}")
        return reasons
    try:
        named, body = _topmost_core_entry(changelog)
    except Refusal as exc:
        reasons.append(str(exc))
        return reasons
    if named != declared:
        reasons.append(f"topmost core changelog entry names {named}, not {declared}")
        return reasons
    if not _has_highlight_bullet(body):
        reasons.append(f"core {named} entry carries no Highlights bullet")
        return reasons
    reasons.extend(_projection_reasons(root, declared, body))
    return reasons


def _entry_bullets(entry_body: str) -> list[str]:
    """The entry's Highlights bullets, read without the projection's parser."""
    head = re.search(r"^### Highlights\s*$", entry_body, re.M)
    section = entry_body[head.end():].split("\n### ", 1)[0]
    bullets: list[str] = []
    current: str | None = None
    for line in section.splitlines():
        if re.match(r"^- \S", line):
            if current is not None:
                bullets.append(" ".join(current.split()))
            current = line[2:]
        elif current is not None and line.startswith("  "):
            current += " " + line.strip()
        elif current is not None and not line.strip():
            bullets.append(" ".join(current.split()))
            current = None
    if current is not None:
        bullets.append(" ".join(current.split()))
    return bullets


def _projection_reasons(root: Path, version: str, entry_body: str) -> list[str]:
    """Does this release's entry reach the `/now/` payload, bullet for bullet?

    Read independently of `build_site.parse_changelog_releases`: the existing
    real-changelog tests build both their expected and their actual values from
    that parser, so an entry it cannot see is absent from both sides and they
    stay green while the entry never reaches the page.
    """
    import importlib.util

    site = root / "tools" / "build-site.py"
    if not site.is_file():
        return [f"cannot read {site.name}: the projection cannot be checked"]
    try:
        spec = importlib.util.spec_from_file_location("build_site", site)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        payload = module.project_now_highlights(
            (root / CHANGELOG).read_text(encoding="utf-8"))
    except Exception as exc:  # the projection is third-party to this check
        return [f"the /now/ projection could not be built: {exc}"]
    try:
        groups = [
            g for g in payload["groups"]
            if any(p["name"] == "core" and p["version"] == version
                   for p in g["packages"])
        ]
        if len(groups) != 1:
            return [
                f"/now/ payload carries {len(groups)} core {version} groups, expected 1"
            ]
        projected = [" ".join(h["source"].split()) for h in groups[0]["highlights"]]
    except (KeyError, TypeError, AttributeError) as exc:
        return [f"the /now/ payload has an unexpected shape: {exc}"]
    expected = _entry_bullets(entry_body)
    if projected != expected:
        return [f"/now/ payload bullets differ from the core {version} changelog entry"]
    return []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, help="base commit to compare against")
    parser.add_argument("--root", default=".", help="repository root")
    args = parser.parse_args(argv)

    try:
        reasons = check(Path(args.root).resolve(), args.base)
    except Exception as exc:  # fail closed: a delivery check must never pass on an error
        reasons = [f"unexpected failure ({type(exc).__name__}): {exc}"]
    for reason in reasons:
        print(f"check-core-release: {reason}", file=sys.stderr)
    if not reasons:
        print("check-core-release: release is consistent")
    return 1 if reasons else 0


if __name__ == "__main__":
    raise SystemExit(main())
