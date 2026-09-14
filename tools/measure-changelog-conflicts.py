#!/usr/bin/env python3
"""Count the textual conflicts the pre-merge rebases had to resolve.

Answers the first known unknown in
`docs/product/research/changelog-fragmentation-spike.md`: how many of the
commits touching `docs/product/changelog.md` produced a real conflict, rather
than how often the file was touched.

Counting merges is useless here. Every merge into `main` is linear -- the branch
is rebased or updated onto main before it merges -- so `git merge-tree P1 P2`
conflicts on nothing and the answer comes back zero. The cost is paid during the
rebase, which leaves no commit of its own.

So the replay reconstructs the rebase. For merge `M = (P1 mainline, P2 branch)`
the fork point `A` is the newest mainline commit whose *committer* date is
strictly before the branch's earliest *author* date. The branch side uses author dates
because they survive a rebase; the mainline side uses committer dates because
they are that commit's position in the mainline. Then

    git merge-tree --merge-base=P1 A P2

takes base `P1`, ours `A` (main's work reverted) and theirs `P2` (main plus the
branch's work), so it conflicts on exactly the regions where main's `A..P1` work
and the branch's work touch the same lines. That is the condition the rebase
faced.

Three self-checks run alongside, because a high rate needs them: a linearity
check proving the naive merge replay is uninformative, a negative control over
merges where the two sides did not both touch the file, and the
shared-insertion-anchor mechanism reported for conflicting and non-conflicting
rebases alike, so the reader can see it does not discriminate between them.

The window is a commit range, not a date, so the same invocation returns the same
figures on every run and every machine. Successive runs of an earlier date-windowed
version of this script disagreed on the commit counts; the cause was never
established, and a commit range removes the question rather than answering it.

Usage:
    python3 tools/measure-changelog-conflicts.py --from REV [--tip REV]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

REPO_ROOT = Path(__file__).resolve().parent.parent
WATCHED_PATHS = ("docs/product/changelog.md", "workspace.toml")
# A release heading added by both sides is the same-anchor insertion collision.
HEADING_PREFIX = "+## ["


class Replay(NamedTuple):
    """One merge replayed as the rebase that preceded it."""

    merge: str
    subject: str
    fork_point: str
    mainline_parent: str
    branch_tip: str
    mainline_commits_skipped: int
    branch_touched: dict[str, bool]
    main_moved: dict[str, bool]
    conflicted_paths: list[str]
    both_added_heading: dict[str, bool]


def git(*args: str) -> str:
    """Run git in the repository and return stdout.

    Raises on a non-zero exit. This script is an evidence of record, so an
    environment or revision error must not read as "no results found".
    """
    done = subprocess.run(["git", "-C", str(REPO_ROOT), *args], capture_output=True, text=True)
    if done.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {done.stderr.strip()}")
    return done.stdout


def merge_tree(*args: str) -> tuple[int, str]:
    """Run `git merge-tree` and return its exit code with stdout.

    0 is a clean merge and 1 is conflicts; anything else is a real failure and
    must not be silently recorded as "no conflict".
    """
    done = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "merge-tree", *args], capture_output=True, text=True
    )
    if done.returncode not in (0, 1):
        raise RuntimeError(f"git merge-tree failed: {done.stderr.strip()}")
    return done.returncode, done.stdout


def added_release_heading(start: str, end: str, path: str) -> bool:
    """True when `start..end` adds a top-level release heading to `path`."""
    diff = git("diff", "--unified=0", start, end, "--", path)
    return any(line.startswith(HEADING_PREFIX) for line in diff.splitlines())


def replay(tip: str, start: str) -> list[Replay]:
    """Replay every first-parent merge in the window as its preceding rebase."""
    mainline = [
        line.split()
        for line in git(
            "rev-list", "--first-parent", "--format=%H %ct", "--no-commit-header", tip
        ).splitlines()
    ]
    times = {sha: int(stamp) for sha, stamp in mainline}
    order = [sha for sha, _ in mainline]
    index_of = {sha: position for position, sha in enumerate(order)}

    rows: list[Replay] = []
    for line in git(
        "log", f"{start}..{tip}", "--first-parent", "--merges", "--format=%H|%P|%s"
    ).splitlines():
        sha, parents, subject = line.split("|", 2)
        pair = parents.split()
        if len(pair) != 2:
            continue
        mainline_parent, branch_tip = pair
        authored = [
            int(stamp)
            for stamp in git(
                "log", "--format=%at", f"{mainline_parent}..{branch_tip}"
            ).splitlines()
        ]
        if not authored:
            continue
        cutoff = min(authored) - 1
        fork_point = next(
            (
                candidate
                for candidate in order[index_of[mainline_parent] :]
                if times[candidate] <= cutoff
            ),
            None,
        )
        # No fork point behind the mainline parent means the branch started from
        # main's tip and never fell behind: no rebase, so nothing to replay.
        if fork_point is None or fork_point == mainline_parent:
            continue

        code, out = merge_tree(
            "--write-tree",
            "--name-only",
            f"--merge-base={mainline_parent}",
            fork_point,
            branch_tip,
        )
        conflicted: list[str] = []
        if code == 1:
            # First line is the tree oid; the conflicted paths follow, then a
            # blank line and git's informational messages.
            for entry in out.splitlines()[1:]:
                if not entry:
                    break
                conflicted.append(entry)

        rows.append(
            Replay(
                merge=sha,
                subject=subject,
                fork_point=fork_point,
                mainline_parent=mainline_parent,
                branch_tip=branch_tip,
                mainline_commits_skipped=index_of[fork_point] - index_of[mainline_parent],
                branch_touched={
                    path: bool(git("diff", "--name-only", mainline_parent, branch_tip, "--", path))
                    for path in WATCHED_PATHS
                },
                main_moved={
                    path: bool(git("diff", "--name-only", fork_point, mainline_parent, "--", path))
                    for path in WATCHED_PATHS
                },
                conflicted_paths=conflicted,
                both_added_heading={
                    path: (
                        added_release_heading(fork_point, mainline_parent, path)
                        and added_release_heading(mainline_parent, branch_tip, path)
                    )
                    for path in WATCHED_PATHS
                },
            )
        )
    return rows


def linearity(tip: str, start: str) -> tuple[int, int, int]:
    """(merges, linear merges, merges conflicting under the naive replay).

    A linear merge is one whose merge base IS its mainline parent -- the branch
    was already up to date, so `git merge-tree P1 P2` cannot conflict. Printing
    this is what makes "the naive replay returns zero" a measurement rather than
    an assertion.
    """
    merges = linear = conflicting = 0
    for line in git(
        "log", f"{start}..{tip}", "--first-parent", "--merges", "--format=%P"
    ).splitlines():
        pair = line.split()
        if len(pair) != 2:
            continue
        merges += 1
        if git("merge-base", *pair).strip() == pair[0]:
            linear += 1
        if merge_tree("--write-tree", "--name-only", *pair)[0] == 1:
            conflicting += 1
    return merges, linear, conflicting


def report(tip: str, start: str, rows: list[Replay]) -> None:
    """Print every figure the fragmentation spike cites."""
    merges, linear, naive_conflicts = linearity(tip, start)
    print(f"window: {start[:9]}..{tip}")
    print(f"merges into main in the window: {merges}")
    print(f"  linear (merge base IS the mainline parent): {linear}")
    print(f"  conflicting under the naive replay `merge-tree P1 P2`: {naive_conflicts}")
    print(f"  replayed (fork point behind the mainline parent): {len(rows)}")
    print(f"  not replayed (branch started from main's tip): {merges - len(rows)}")

    for path in WATCHED_PATHS:
        commits = len(git("rev-list", f"{start}..{tip}", "--", path).splitlines())
        exposed = [r for r in rows if r.branch_touched[path] and r.main_moved[path]]
        conflicting = [r for r in exposed if path in r.conflicted_paths]
        unexposed = [r for r in rows if not (r.branch_touched[path] and r.main_moved[path])]
        false_positives = [r for r in unexposed if path in r.conflicted_paths]
        print(f"\n{path}")
        print(f"  commits touching it in the window: {commits}")
        print(f"  branch edited it AND main moved it meanwhile: {len(exposed)}")
        print(f"  of those, the replay conflicts textually: {len(conflicting)}")
        if exposed:
            print(f"    = {100 * len(conflicting) / len(exposed):.0f}% of exposed")
        if rows:
            print(f"    = {100 * len(conflicting) / len(rows):.0f}% of all replayed merges")
        print(
            f"  negative control: {len(unexposed)} unexposed merges, "
            f"{len(false_positives)} conflicting on this path"
        )
        # The shared insertion anchor is a changelog shape. `workspace.toml` has
        # no release heading, so reporting 0/0 there would read as a measured
        # result rather than an undefined one.
        if path == "docs/product/changelog.md":
            anchor_in_conflicting = sum(1 for r in conflicting if r.both_added_heading[path])
            anchor_in_clean = sum(
                1 for r in exposed if r not in conflicting and r.both_added_heading[path]
            )
            print(
                f"  shared insertion anchor (both sides added a release heading): "
                f"{anchor_in_conflicting}/{len(conflicting)} conflicting, "
                f"{anchor_in_clean}/{len(exposed) - len(conflicting)} non-conflicting"
            )
        if conflicting:
            skipped = sorted(r.mainline_commits_skipped for r in conflicting)
            print(
                f"  mainline commits behind, among conflicting: "
                f"min {skipped[0]}, max {skipped[-1]}, "
                f"{skipped.count(skipped[0])} at the minimum"
            )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tip", default="HEAD", help="mainline revision to measure")
    parser.add_argument(
        "--from",
        dest="start",
        required=True,
        help="commit just before the window; a range, not a date, so it reproduces",
    )
    args = parser.parse_args(argv)
    report(args.tip, args.start, replay(args.tip, args.start))
    return 0


if __name__ == "__main__":
    sys.exit(main())
