#!/usr/bin/env python3
"""Measure whether per-update changelog fragments merge where a monolith does not.

Answers the mergeability claim in
`docs/architecture/changelog-fragment-source.md` § 7 for the spike recorded in
`docs/product/research/changelog-fragment-assembly-spike.md`: when two queued
changes each add a changelog update, does the shared file force a conflict that
one-file-per-update would avoid?

Two arms, replayed identically. The **fragment arm** builds 20 synthetic commits
off one base, each adding a single `docs/product/changelog.d/<uuid>.md` and
nothing else. The **control arm** rebuilds the same 20 changes as prepended
release sections in `docs/product/changelog.md`, all at the same insertion
anchor -- the position a new release actually takes. Every unordered pair of the
20 (190 pairs) is replayed with `git merge-tree --write-tree --merge-base=<base>`.

The control arm is what makes the fragment arm readable. A zero conflict count
measures nothing on its own: it is equally consistent with fragments being
independent and with the harness never invoking git correctly. The control arm
has to come back non-zero for the fragment arm's zero to be a result.

Pairs bucket on `git merge-tree`'s **exit status**, not on its output text:
0 is clean, 1 is a conflict, and anything else is a harness error reported per
arm rather than silently counted as clean. A clean merge writes only a tree oid
to stdout, so a text scan cannot separate a clean pair from a failed invocation
-- which is exactly the survive threshold, and so exactly the confusion that
would invalidate the run. Two hand-built pairs, one known to conflict and one
known to be clean, exercise that classifier before either arm's figure is taken.

Every commit is built as a detached object through a scratch index
(`GIT_INDEX_FILE`), never as a branch and never through the working tree, so the
measurement cannot disturb a worktree a coordination lease may be sharing. The
script leaves `git status --porcelain` empty.

Fragment identifiers come from a seeded generator so that two runs at the same
base produce byte-identical output. They are UUIDv4-shaped because the anchor
under test is `change-` plus a UUID's 32 hexadecimal digits.

Usage:
    python3 tools/measure-changelog-fragment-merges.py
"""

from __future__ import annotations

import contextlib
import importlib.util
import itertools
import os
import random
import subprocess
import sys
import tempfile
import uuid
from collections.abc import Iterator
from pathlib import Path
from typing import Any, NamedTuple

REPO_ROOT = Path(__file__).resolve().parent.parent
CHANGELOG = "docs/product/changelog.md"
FRAGMENT_DIR = "docs/product/changelog.d"
BRANCH_COUNT = 20
BUILD_SITE = REPO_ROOT / "tools" / "build-site.py"
# Seeded so the run reproduces; the value itself carries no meaning.
UUID_SEED = 0x5C_11_A9_00


class ArmResult(NamedTuple):
    """One arm's 190-pair replay, bucketed by `git merge-tree` exit status."""

    name: str
    pairs: int
    clean: int
    conflicted: int
    errored: int


# Redirect variables that would silently point git at another repository or
# index. An inherited GIT_DIR makes `-C` cosmetic, so the run could measure a
# tree the reader never named.
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
# Process-local identity and timestamps. `commit-tree` refuses without an
# identity, so inheriting one makes the procedure fail on a machine that has
# none configured -- and an ambient clock makes two runs differ. Neither value
# is written to the reader's configuration, and these commits reach no branch.
_SYNTHETIC_ENV = {
    "GIT_AUTHOR_NAME": "changelog-fragment-measurement",
    "GIT_AUTHOR_EMAIL": "measurement@invalid",
    "GIT_COMMITTER_NAME": "changelog-fragment-measurement",
    "GIT_COMMITTER_EMAIL": "measurement@invalid",
    "GIT_AUTHOR_DATE": "2026-01-01T00:00:00+00:00",
    "GIT_COMMITTER_DATE": "2026-01-01T00:00:00+00:00",
}


@contextlib.contextmanager
def git_session() -> Iterator[dict[str, str]]:
    """Yield a git environment whose writes land in a throwaway object store.

    `hash-object -w`, `commit-tree` and `merge-tree --write-tree` all write
    objects. Left to the default store those objects are unreachable but
    permanent, and in a worktree the store belongs to the PARENT repository, so
    a measurement would deposit them in a tree it never touched and
    `git status --porcelain` could not reveal it. Writing to a temporary
    directory with the real store as a read-only alternate keeps every read
    working and leaves nothing behind when the directory goes.
    """
    env = {k: v for k, v in os.environ.items() if k not in _GIT_REDIRECTS}
    env.update(_SYNTHETIC_ENV)
    real_objects = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "--git-path", "objects"],
        capture_output=True, text=True, env=env, check=True,
    ).stdout.strip()
    with tempfile.TemporaryDirectory(prefix="changelog-merge-measure-") as scratch:
        objects = Path(scratch) / "objects"
        objects.mkdir()
        env["GIT_OBJECT_DIRECTORY"] = str(objects)
        env["GIT_ALTERNATE_OBJECT_DIRECTORIES"] = str(Path(real_objects).resolve())
        yield env


def git(*args: str, env: dict[str, str], index: Path | None = None) -> str:
    """Run git in the repository and return stdout.

    Raises on a non-zero exit. This script is an evidence of record, so an
    environment error must not read as "no conflicts found".
    """
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


def merge_tree(base: str, ours: str, theirs: str, env: dict[str, str]) -> int:
    """Replay one pair; return `git merge-tree`'s exit status.

    0 clean, 1 conflicted, anything else a harness error. The status is returned
    rather than interpreted here so the caller can report the error bucket: a
    run that errors on all 190 pairs would otherwise be indistinguishable from
    the clean result that is the survive threshold.
    """
    done = subprocess.run(
        [
            "git",
            "-C",
            str(REPO_ROOT),
            "merge-tree",
            "--write-tree",
            "--name-only",
            f"--merge-base={base}",
            ours,
            theirs,
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    return done.returncode


def write_blob(content: str, env: dict[str, str]) -> str:
    """Write `content` as a loose blob and return its oid."""
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
    """Build a detached commit over `base` that sets each path to its blob.

    Uses a scratch `GIT_INDEX_FILE`, so neither the repository index nor the
    working tree is read or written.
    """
    with tempfile.TemporaryDirectory() as scratch:
        index = Path(scratch) / "index"
        git("read-tree", base, env=env, index=index)
        for path, blob in path_blobs.items():
            git(
                "update-index", "--add", "--cacheinfo",
                f"100644,{blob},{path}", env=env, index=index,
            )
        tree = git("write-tree", env=env, index=index).strip()
    return git("commit-tree", tree, "-p", base, "-m", message, env=env).strip()


def fragment_body(identifier: str, ordinal: int) -> str:
    """One per-update fragment: TOML envelope, then a Highlights section."""
    return (
        "+++\n"
        'schema = "changelog-fragment/v1"\n'
        f'id = "{identifier}"\n'
        'date = "2026-09-23"\n'
        'packages = [{ name = "core", version = "2.26.36" }]\n'
        "+++\n"
        "\n"
        "### Highlights\n"
        "\n"
        f"- Synthetic fragment {ordinal:02d} for the merge-independence measurement.\n"
    )


def release_section(identifier: str, ordinal: int) -> str:
    """The same change authored as a prepended release section."""
    return (
        f"## [core][2.27.{ordinal}] — 2026-09-23\n"
        "\n"
        "### Highlights\n"
        "\n"
        f"- Synthetic fragment {ordinal:02d} for the merge-independence measurement.\n"
        f"<!-- {identifier} -->\n"
        "\n"
    )


def load_build_site() -> object:
    """Import `tools/build-site.py` by path; the module name has a hyphen."""
    spec = importlib.util.spec_from_file_location("build_site", BUILD_SITE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {BUILD_SITE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def first_release_line(build_site: Any, changelog: str) -> int:
    """Zero-based line index of the first free-standing release heading.

    Delegates to `parse_changelog_releases` on three counts, because each one
    is a rule this script would otherwise re-derive and drift from.

    *Which `##` lines are real* is decided by the parser's fence and comment
    state machine; `ParsedChangelog.headings` is exported precisely so a caller
    needing heading POSITION does not rewrite it.

    *Which occurrence* is decided by source position, never by heading text.
    `changelog.md` repeats release headings -- the parser ships a slugger whose
    only job is disambiguating them -- so matching the first heading whose
    title equals a chosen release can land on an earlier duplicate.

    *Which releases are free-standing* is decided by the parser's `unreleased`
    flag, which it derives from the whole stack of enclosing headings and not
    from depth. Testing for level 2 instead would be wrong in general: a
    level-1 `Unreleased` region can enclose a level-2 release, and that release
    is not free-standing however shallow its heading. It holds on today's file
    only by accident of layout.

    Release-bearing headings and release records are the same sequence in
    source order, so they zip. That is asserted rather than assumed: a
    divergence means one of the two rules above has moved, and this fails
    closed rather than inserting at a guessed position.
    """
    identity = getattr(build_site, "_parse_release_identity", None)
    if identity is None:
        raise RuntimeError(
            f"{BUILD_SITE} exposes no release-identity predicate; refusing to "
            "guess which heading a release occupies"
        )
    parsed = build_site.parse_changelog_releases(changelog)
    bearing = [h for h in parsed.headings if identity(h.title) is not None]
    if len(bearing) != len(parsed.releases):
        raise RuntimeError(
            f"{CHANGELOG}: {len(bearing)} release-bearing headings against "
            f"{len(parsed.releases)} release records; the parser and this "
            "script disagree about what a release heading is"
        )
    for heading, record in zip(bearing, parsed.releases, strict=True):
        if heading.title != record["heading"]:
            raise RuntimeError(
                f"{CHANGELOG}: heading {heading.title!r} at line "
                f"{heading.lineno} does not pair with release record "
                f"{record['heading']!r}; source order diverged"
            )
        if not record["unreleased"]:
            return heading.lineno - 1
    raise RuntimeError(f"{CHANGELOG} has no free-standing released entry")


def prepend_release(changelog: str, section: str, position: int) -> str:
    """Insert `section` immediately above the first real release heading.

    Every control-arm commit inserts at this one anchor because that is where a
    new release actually goes; spreading them over the file would measure a
    shape no release takes.
    """
    lines = changelog.splitlines(keepends=True)
    return "".join(lines[:position]) + section + "".join(lines[position:])


def identifiers(count: int) -> list[str]:
    """`count` deterministic UUIDv4-shaped identifiers."""
    rng = random.Random(UUID_SEED)
    return [str(uuid.UUID(bytes=rng.randbytes(16), version=4)) for _ in range(count)]


def build_arm(
    base: str, name: str, changelog_at_base: str, ids: list[str], anchor: int,
    env: dict[str, str],
) -> list[str]:
    """Build one arm's synthetic commits and return their oids."""
    commits = []
    for ordinal, identifier in enumerate(ids, start=1):
        if name == "fragment":
            blob = write_blob(fragment_body(identifier, ordinal), env)
            paths = {f"{FRAGMENT_DIR}/{identifier}.md": blob}
        else:
            updated = prepend_release(
                changelog_at_base, release_section(identifier, ordinal), anchor
            )
            paths = {CHANGELOG: write_blob(updated, env)}
        commits.append(
            commit_with(base, paths, f"{name} arm branch {ordinal:02d}", env)
        )
    return commits


def replay(base: str, name: str, commits: list[str], env: dict[str, str]) -> ArmResult:
    """Replay every unordered pair of `commits` and bucket by exit status."""
    clean = conflicted = errored = 0
    pairs = 0
    for ours, theirs in itertools.combinations(commits, 2):
        pairs += 1
        status = merge_tree(base, ours, theirs, env)
        if status == 0:
            clean += 1
        elif status == 1:
            conflicted += 1
        else:
            errored += 1
    return ArmResult(name, pairs, clean, conflicted, errored)


def classifier_self_check(
    base: str, changelog_at_base: str, env: dict[str, str]
) -> list[tuple[str, str, bool]]:
    """Bucket one pair known to conflict and one known to be clean.

    Without this, an invocation that errors on every pair looks exactly like the
    clean fragment arm, which is the survive threshold.
    """
    left_blob = write_blob("left\n" + changelog_at_base, env)
    right_blob = write_blob("right\n" + changelog_at_base, env)
    left = commit_with(base, {CHANGELOG: left_blob}, "sc left", env)
    right = commit_with(base, {CHANGELOG: right_blob}, "sc right", env)
    conflict_status = merge_tree(base, left, right, env)

    a = commit_with(base, {f"{FRAGMENT_DIR}/self-check-a.md": write_blob("a\n", env)}, "sc a", env)
    b = commit_with(base, {f"{FRAGMENT_DIR}/self-check-b.md": write_blob("b\n", env)}, "sc b", env)
    clean_status = merge_tree(base, a, b, env)

    return [
        ("known-conflicting pair", f"exit {conflict_status} (want 1)", conflict_status == 1),
        ("known-clean pair", f"exit {clean_status} (want 0)", clean_status == 0),
    ]


def report(base: str, checks: list[tuple[str, str, bool]], arms: list[ArmResult]) -> None:
    """Print every figure the spike report cites."""
    expected_pairs = BRANCH_COUNT * (BRANCH_COUNT - 1) // 2
    print(f"base commit: {base}")
    print(f"branches per arm: {BRANCH_COUNT}   unordered pairs per arm: {expected_pairs}")
    print()
    print("classifier self-check (runs before either arm's figure is taken):")
    for label, detail, passed in checks:
        print(f"  {'PASS' if passed else 'FAIL'}  {label}: {detail}")
    print()
    for arm in arms:
        print(f"{arm.name} arm")
        print(f"  pairs replayed          : {arm.pairs}")
        print(f"  clean (exit 0)          : {arm.clean}")
        print(f"  conflicting (exit 1)    : {arm.conflicted}")
        print(f"  errored (any other exit): {arm.errored}")


def main() -> int:
    with git_session() as env:
        base = git("rev-parse", "HEAD", env=env).strip()
        changelog_at_base = git("show", f"{base}:{CHANGELOG}", env=env)
        anchor = first_release_line(load_build_site(), changelog_at_base)
        ids = identifiers(BRANCH_COUNT)

        checks = classifier_self_check(base, changelog_at_base, env)
        if not all(passed for _, _, passed in checks):
            report(base, checks, [])
            print(
                "\nclassifier self-check failed; no arm figure is reportable",
                file=sys.stderr,
            )
            return 1

        arms = [
            replay(base, name, build_arm(base, name, changelog_at_base, ids, anchor, env), env)
            for name in ("fragment", "control")
        ]
    report(base, checks, arms)
    return 0


if __name__ == "__main__":
    sys.exit(main())
