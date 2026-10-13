#!/usr/bin/env python3
"""Measure historical anchor drift in the monolith changelog counterfactual.

The fragment source model leaves the frozen historical changelog bytes in place,
so historical anchors cannot move. The counterfactual arm takes the same
synthetic updates and prepends them as release sections in
``docs/product/changelog.md``. Re-slugging that combined file shows whether the
shared-file shape would move an existing historical anchor through duplicate
suffix renumbering.

All objects are built as detached commits over a named base with a scratch Git
object store and index. The shared working tree and index are not modified.

Usage:
    python3 tools/measure-changelog-anchor-drift.py
"""

from __future__ import annotations

import contextlib
import importlib.util
import os
import subprocess
import sys
import tempfile
import uuid
from collections.abc import Generator
from pathlib import Path
from types import ModuleType

REPO_ROOT = Path(__file__).resolve().parent.parent
CHANGELOG = "docs/product/changelog.md"
FRAGMENT_DIR = "docs/product/changelog.d"
CHANGELOG_TOOL = REPO_ROOT / "tools" / "changelog.py"
UPDATE_COUNT = 20
UUID_NAMESPACE = uuid.UUID("8a1f796d-e32d-45cb-9e3a-cc1b24051e0a")

_GIT_REDIRECTS = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_COMMON_DIR",
    "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_NAMESPACE",
    "GIT_CEILING_DIRECTORIES",
)
_SYNTHETIC_ENV = {
    "GIT_AUTHOR_NAME": "changelog-anchor-measurement",
    "GIT_AUTHOR_EMAIL": "measurement@invalid",
    "GIT_COMMITTER_NAME": "changelog-anchor-measurement",
    "GIT_COMMITTER_EMAIL": "measurement@invalid",
    "GIT_AUTHOR_DATE": "2026-01-01T00:00:00+00:00",
    "GIT_COMMITTER_DATE": "2026-01-01T00:00:00+00:00",
}


def load_changelog() -> ModuleType:
    """Import the shared changelog model by path."""
    spec = importlib.util.spec_from_file_location("product_changelog", CHANGELOG_TOOL)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {CHANGELOG_TOOL}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@contextlib.contextmanager
def git_session() -> Generator[dict[str, str], None, None]:
    """Yield a Git environment whose object writes are temporary."""
    env = {key: value for key, value in os.environ.items() if key not in _GIT_REDIRECTS}
    env.update(_SYNTHETIC_ENV)
    real_objects = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "--git-path", "objects"],
        capture_output=True,
        text=True,
        env=env,
        check=True,
    ).stdout.strip()
    with tempfile.TemporaryDirectory(
        prefix="changelog-anchor-drift-", ignore_cleanup_errors=True
    ) as scratch:
        objects = Path(scratch) / "objects"
        objects.mkdir()
        env["GIT_OBJECT_DIRECTORY"] = str(objects)
        env["GIT_ALTERNATE_OBJECT_DIRECTORIES"] = str(Path(real_objects).resolve())
        yield env


def git(*args: str, env: dict[str, str], index: Path | None = None) -> str:
    """Run Git in the repository and return stdout."""
    run_env = dict(env)
    if index is not None:
        run_env["GIT_INDEX_FILE"] = str(index)
    done = subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args],
        capture_output=True,
        text=True,
        env=run_env,
    )
    if done.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {done.stderr.strip()}")
    return done.stdout


def write_blob(content: str, env: dict[str, str]) -> str:
    """Write one blob into the scratch object store."""
    done = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "hash-object", "-w", "--stdin"],
        input=content,
        capture_output=True,
        text=True,
        env=env,
    )
    if done.returncode != 0:
        raise RuntimeError(f"git hash-object failed: {done.stderr.strip()}")
    return done.stdout.strip()


def commit_with(
    base: str, path_blobs: dict[str, str], message: str, env: dict[str, str]
) -> str:
    """Build a detached commit over ``base`` that sets the named paths."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as scratch:
        index = Path(scratch) / "index"
        git("read-tree", base, env=env, index=index)
        for path, blob in path_blobs.items():
            git(
                "update-index",
                "--add",
                "--cacheinfo",
                f"100644,{blob},{path}",
                env=env,
                index=index,
            )
        tree = git("write-tree", env=env, index=index).strip()
    return git("commit-tree", tree, "-p", base, "-m", message, env=env).strip()


def update_id(ordinal: int) -> str:
    """Return a deterministic UUID for a synthetic changelog update."""
    return str(uuid.uuid5(UUID_NAMESPACE, f"anchor-drift-{ordinal:02d}"))


def update_version(ordinal: int) -> str:
    """Return the synthetic package version for one update."""
    return f"9.91.{ordinal}"


def release_heading(ordinal: int) -> str:
    """Return the changelog heading shared by both arms."""
    return f"[core][{update_version(ordinal)}] — 2026-09-23"


def release_section(ordinal: int) -> str:
    """Return one synthetic update as a monolith release section."""
    return (
        f"## {release_heading(ordinal)}\n"
        "\n"
        "### Highlights\n"
        "\n"
        f"- Synthetic update {ordinal:02d} for the anchor-drift measurement.\n"
        "\n"
    )


def fragment_source(changelog: ModuleType, ordinal: int) -> tuple[str, str]:
    """Return ``(relative_path, source)`` for one synthetic fragment."""
    fragment_id = update_id(ordinal)
    packages = [{"name": "core", "version": update_version(ordinal)}]
    fragment_date = "2026-09-23"
    anchor = changelog._compose_fragment_anchor(packages, fragment_date, fragment_id)
    source = (
        "+++\n"
        "schema = 1\n"
        f'id = "{fragment_id}"\n'
        f'anchor = "{anchor}"\n'
        f"date = {fragment_date}\n"
        "[[packages]]\n"
        'name = "core"\n'
        f'version = "{update_version(ordinal)}"\n'
        "+++\n"
        "## Highlights\n"
        f"- Synthetic update {ordinal:02d} for the anchor-drift measurement.\n"
    )
    return f"{FRAGMENT_DIR}/{fragment_id}.md", source


def first_released_heading_line(changelog: ModuleType, text: str) -> int:
    """Return the zero-based insertion line for a new top-level release."""
    parsed = changelog.parse_changelog_releases(text)
    headings = [
        heading
        for heading in parsed.headings
        if changelog._parse_release_identity(heading.title) is not None
    ]
    if len(headings) != len(parsed.releases):
        raise RuntimeError("release headings and parsed release records diverged")
    for heading, release in zip(headings, parsed.releases, strict=True):
        if heading.title != release["heading"]:
            raise RuntimeError("release heading order diverged from parsed releases")
        if not release["unreleased"]:
            return heading.lineno - 1
    raise RuntimeError(f"{CHANGELOG} has no released heading")


def prepend_sections(changelog: ModuleType, text: str, count: int) -> str:
    """Prepend ``count`` synthetic sections at the real release insertion point."""
    position = first_released_heading_line(changelog, text)
    lines = text.splitlines(keepends=True)
    sections = "".join(release_section(ordinal) for ordinal in range(1, count + 1))
    return "".join(lines[:position]) + sections + "".join(lines[position:])


def historical_anchor_sequence(changelog: ModuleType, text: str) -> list[tuple[str, str]]:
    """Return each released heading and rendered anchor in source order."""
    parsed = changelog.parse_changelog_releases(text)
    anchors: list[tuple[str, str]] = []
    for release in parsed.releases:
        if release["unreleased"]:
            continue
        anchors.append((release["heading"], release["anchor"]))
    return anchors


def moved_anchors(
    before: list[tuple[str, str]], after: list[tuple[str, str]], *, skip: int
) -> int:
    """Count historical releases whose post-insertion anchor changed."""
    comparable = after[skip:skip + len(before)]
    if [heading for heading, _anchor in comparable] != [
        heading for heading, _anchor in before
    ]:
        raise RuntimeError("historical release sequence changed unexpectedly")
    return sum(
        1
        for (_heading, before_anchor), (_after_heading, after_anchor)
        in zip(before, comparable, strict=True)
        if before_anchor != after_anchor
    )


def control_moved(changelog: ModuleType) -> int:
    """Run a collision case that must move duplicate-suffixed anchors."""
    before = (
        "# Changelog\n\n"
        "## [core][1.0.0] — 2026-01-01\n\n"
        "First historical body.\n\n"
        "## [core][1.0.0] — 2026-01-01\n\n"
        "Second historical body.\n"
    )
    after = release_section(1).replace(
        "[core][9.91.1] — 2026-09-23", "[core][1.0.0] — 2026-01-01"
    ) + before
    return moved_anchors(
        historical_anchor_sequence(changelog, before),
        historical_anchor_sequence(changelog, after),
        skip=1,
    )


def assert_status_unchanged(before: str, env: dict[str, str]) -> str:
    """Fail if the measurement changed the shared working tree."""
    after = git("status", "--porcelain", env=env)
    if after != before:
        raise RuntimeError(
            "measurement changed git status:\n"
            f"before:\n{before.rstrip()}\n"
            f"after:\n{after.rstrip()}"
        )
    return after


def main() -> int:
    changelog = load_changelog()
    control = control_moved(changelog)
    if control == 0:
        print("control moved historical anchors: 0", file=sys.stderr)
        print("control failed; real figures were not recorded", file=sys.stderr)
        return 1

    with git_session() as env:
        base = git("rev-parse", "HEAD", env=env).strip()
        status_before = git("status", "--porcelain", env=env)
        baseline = git("show", f"{base}:{CHANGELOG}", env=env)
        historical = historical_anchor_sequence(changelog, baseline)

        monolith = prepend_sections(changelog, baseline, UPDATE_COUNT)
        monolith_commit = commit_with(
            base,
            {CHANGELOG: write_blob(monolith, env)},
            "anchor drift monolith counterfactual",
            env,
        )
        monolith_text = git("show", f"{monolith_commit}:{CHANGELOG}", env=env)
        monolith_moved = moved_anchors(
            historical,
            historical_anchor_sequence(changelog, monolith_text),
            skip=UPDATE_COUNT,
        )

        fragment_blobs = {
            path: write_blob(source, env)
            for path, source in (
                fragment_source(changelog, ordinal)
                for ordinal in range(1, UPDATE_COUNT + 1)
            )
        }
        fragment_commit = commit_with(
            base,
            fragment_blobs,
            "anchor drift fragment path",
            env,
        )
        fragment_text = git("show", f"{fragment_commit}:{CHANGELOG}", env=env)
        fragment_moved = moved_anchors(
            historical,
            historical_anchor_sequence(changelog, fragment_text),
            skip=0,
        )
        status_after = assert_status_unchanged(status_before, env)

    print(f"base commit: {base}")
    print(f"synthetic updates: {UPDATE_COUNT}")
    print(f"control moved historical anchors: {control}")
    print(f"monolith moved historical anchors: {monolith_moved}")
    print(f"fragment moved historical anchors: {fragment_moved}")
    if status_after:
        print("git status: unchanged from pre-existing workspace state")
    else:
        print("git status: clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
