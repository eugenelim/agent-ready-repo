#!/usr/bin/env python3
"""Measure how many changelog collector windows are trustworthy.

A "collector" selects the commits belonging to one release so an entry can be
drafted from them. This measures the selection, not the drafting.

Boundary rule R3: the mainline commit that added `## [artifact][version]` to
`docs/product/changelog.md`. Merge diffs must be searched, because a heading can
enter through a merge resolution and plain `git log -S` never shows one --
`--diff-merges=first-parent` does that, and `-s` is required with it or the patch
itself is printed and parsed as commit ids.

Window: previous heading commit to this one, path-filtered to the artifact's
subtree, squash messages split on their `* ` subject lines, with an exclusion
list on commit type rather than a `feat`/`fix` include list.

Three detectors condemn a window. A fourth was implemented and withdrawn: "another
release's heading falls inside the window" cannot fire, because every window runs
between two consecutive entries of the same artifact, so its zero was a property
of the construction rather than a result.

  foreign         an admitted commit's message names another version of the
                  same artifact
  shared squash   a squashed pull request touching several artifacts; its split
                  units cannot be attributed to files, so every unit reaches
                  every artifact the squash touched
  cross artifact  an admitted commit touches several artifact subtrees at all --
                  touching a subtree is not the same as belonging to its release

Usage:
    python3 tools/measure-changelog-collector.py [--tip REV]
"""

from __future__ import annotations

import argparse
import collections
import importlib.util
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
CHANGELOG = "docs/product/changelog.md"
EXCLUDED_TYPES = frozenset({
    "docs",
    "chore",
    "test",
    "ci",
    "style",
    "build",
    "release",
    "refactor",
})
SQUASH_SUBJECT = re.compile(r"^\* (.+)$", re.MULTILINE)
# Loose enough for this repository's compound `chore(core)+feat(core): ...`.
COMMIT_TYPE = re.compile(r"^(\w+)(\([^)]*\))?(\+\w+(\([^)]*\))?)*!?:")
SEMVER = re.compile(r"\b(\d+\.\d+\.\d+)\b")


def git(*args: str) -> str:
    """Run git in the repository and return stdout.

    Raises on a non-zero exit. This script is an evidence of record, so an
    environment or revision error must not read as "no results found".
    """
    done = subprocess.run(["git", "-C", str(REPO_ROOT), *args], capture_output=True, text=True)
    if done.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {done.stderr.strip()}")
    return done.stdout


def load_build_site() -> Any:
    """Import `tools/build-site.py`, whose hyphen blocks a plain import."""
    spec = importlib.util.spec_from_file_location(
        "build_site", REPO_ROOT / "tools" / "build-site.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def artifact_subtree(name: str, tip: str) -> str | None:
    """The subtree a released artifact's work lives in at `tip`, if one exists.

    Resolved from the revision rather than the working tree, so the figures do
    not shift with whatever the checkout happens to contain.
    """
    for candidate in (f"packs/{name}", f"packages/{name}"):
        if git("ls-tree", "-d", "--name-only", tip, candidate).strip():
            return candidate
    return None


def split_units(message: str) -> list[str]:
    """Split a squashed pull request's message into its constituent commits."""
    starts = [match.start() for match in SQUASH_SUBJECT.finditer(message)]
    if len(starts) < 2:
        return [message]
    units = [message[: starts[0]]] if message[: starts[0]].strip() else []
    for position, start in enumerate(starts):
        end = starts[position + 1] if position + 1 < len(starts) else len(message)
        units.append(message[start:end])
    return units


def touched_artifacts(sha: str) -> set[str]:
    """Artifact subtrees this commit touches.

    `git show --name-only` prints nothing at all for a merge commit, which would
    make every admitted merge structurally invisible to the cross-artifact
    detector. `diff-tree --first-parent` reports a merge's net effect and behaves
    identically on an ordinary commit.
    """
    return {
        entry.split("/")[1]
        for entry in git(
            "diff-tree", "--no-commit-id", "--name-only", "-r", "--first-parent", sha
        ).split()
        if entry.startswith(("packs/", "packages/")) and len(entry.split("/")) > 2
    }


def measure(tip: str) -> list[dict]:
    """Build and score every released artifact/version window."""
    build_site = load_build_site()
    text = git("show", f"{tip}:{CHANGELOG}")
    entries = [
        r for r in build_site.parse_changelog_releases(text).releases if not r["unreleased"]
    ]

    by_artifact: dict[str, list[tuple[str, dict]]] = {}
    for record in entries:
        for package in record["packages"]:
            by_artifact.setdefault(package["name"], []).append((package["version"], record))

    mainline = git("rev-list", "--first-parent", tip).split()
    position = {sha: index for index, sha in enumerate(mainline)}

    def heading_commit(artifact: str, version: str) -> str | None:
        found = git(
            "log",
            tip,
            "--first-parent",
            "--diff-merges=first-parent",
            "-s",
            f"-S## [{artifact}][{version}]",
            "--format=%H",
            "--",
            CHANGELOG,
        ).split()
        return found[-1] if found else None

    rows: list[dict] = []
    for artifact, items in by_artifact.items():
        subtree = artifact_subtree(artifact, tip)
        resolved = []
        for version, record in items:
            commit = heading_commit(artifact, version)
            if commit is None:
                # Reported, never dropped: an unresolvable boundary is an
                # outcome of the rule, and swallowing it shrinks the denominator
                # every other figure is taken over.
                rows.append({
                    "artifact": artifact,
                    "version": version,
                    "date": record["date"],
                    "multi_artifact": len(record["packages"]) > 1,
                    "status": "no heading",
                    "foreign": [],
                    "shared_squash": [],
                    "cross_artifact": [],
                })
                continue
            resolved.append((version, commit, record))
        resolved.sort(key=lambda item: position.get(item[1], len(mainline)))

        for index, (version, commit, record) in enumerate(resolved):
            previous = resolved[index + 1][1] if index + 1 < len(resolved) else None
            row: dict = {
                "artifact": artifact,
                "version": version,
                "date": record["date"],
                "multi_artifact": len(record["packages"]) > 1,
                "foreign": [],
                "shared_squash": [],
                "cross_artifact": [],
            }
            if previous is None or subtree is None:
                row["status"] = "no boundary"
                rows.append(row)
                continue

            span = f"{previous}..{commit}"
            units: list[dict] = []
            for sha in git("log", "--format=%H", span, "--", subtree).split():
                message = git("log", "-1", "--format=%B", sha)
                for unit in split_units(message):
                    subject = unit.strip().splitlines()[0] if unit.strip() else ""
                    match = COMMIT_TYPE.match(subject.lstrip("* ").strip())
                    units.append({
                        "commit": sha,
                        "message": unit.strip(),
                        "type": match.group(1) if match else None,
                    })
            admitted = [unit for unit in units if unit["type"] not in EXCLUDED_TYPES]

            others = {v for v, _ in items} - {version}
            for unit in admitted:
                if (
                    any(found in others for found in SEMVER.findall(unit["message"]))
                    and artifact in unit["message"]
                ):
                    row["foreign"].append(unit["commit"][:9])
            for sha in {unit["commit"] for unit in admitted}:
                spread = touched_artifacts(sha)
                if len(spread) > 1:
                    row["cross_artifact"].append(sha[:9])
                    if sum(1 for u in units if u["commit"] == sha) >= 2:
                        row["shared_squash"].append(sha[:9])

            if not admitted:
                row["status"] = "empty"
            elif row["foreign"] or row["cross_artifact"]:
                row["status"] = "polluted"
            else:
                row["status"] = "clean"
            rows.append(row)
    return rows


def report(tip: str, rows: list[dict]) -> None:
    """Print every figure the generator-inputs spike cites."""
    status = collections.Counter(row["status"] for row in rows)
    clean = [row for row in rows if row["status"] == "clean"]
    polluted = [row for row in rows if row["status"] == "polluted"]
    artifacts = {row["artifact"] for row in rows}

    print(f"tip: {tip}")
    print(f"released (artifact, version) pairs in the changelog: {len(rows)}")
    for name in ("clean", "polluted", "empty", "no boundary", "no heading"):
        print(f"  {name:<12} {status[name]}")
    # Only these three statuses represent a window that was actually
    # constructed: `no heading` and `no boundary` both return before one exists.
    built = status["clean"] + status["polluted"] + status["empty"]
    print(f"  windows actually built: {built}")
    if rows:
        print(f"  clean as a share of all pairs:      {100 * len(clean) / len(rows):.0f}%")
    if built:
        print(f"  clean as a share of built windows:  {100 * len(clean) / built:.0f}%")
    print("\ndetectors, over the polluted windows:")
    for name in ("foreign", "shared_squash", "cross_artifact"):
        print(f"  {name:<15} {sum(1 for row in polluted if row[name])}")
    only_cross = sum(1 for row in polluted if row["cross_artifact"] and not row["foreign"])
    union = sum(1 for row in polluted if row["shared_squash"] or row["cross_artifact"])
    print(f"  cross_artifact caught by nothing else: {only_cross}")
    print(f"  shared_squash OR cross_artifact (union): {union}")

    per_artifact = collections.Counter(row["artifact"] for row in clean)
    print(f"\nclean windows by artifact ({len(per_artifact)} of {len(artifacts)} artifacts):")
    for name, count in per_artifact.most_common():
        print(f"  {name:<26} {count}")

    # Per-window rows, so which windows are clean is auditable rather than
    # implied by a total.
    print("\nevery window (artifact, version, date, status, detector hits):")
    for row in sorted(rows, key=lambda r: (r["artifact"], r["date"], r["version"])):
        hits = ",".join(
            name for name in ("foreign", "shared_squash", "cross_artifact") if row[name]
        )
        print(
            f"  {row['artifact']:<26} {row['version']:<10} {row['date']} "
            f"{row['status']:<12} {hits}"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tip", default="HEAD", help="mainline revision to measure")
    args = parser.parse_args(argv)
    report(args.tip, measure(args.tip))
    return 0


if __name__ == "__main__":
    sys.exit(main())
