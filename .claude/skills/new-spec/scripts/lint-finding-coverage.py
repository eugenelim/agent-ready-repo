#!/usr/bin/env python3
"""Check that every finding a checker can emit is exercised by some test.

The defect this detects. A rule-based checker emits one distinct message per
rule. A rule whose message no test ever observes has no red case: its suite is
green for a reason unrelated to whether the rule works. That is a control that
cannot fail, one level up -- in the tests rather than in the guard.

How a script opts in. Declare a module-level `FINDING_KINDS` mapping of rule
name to the message fragment that rule emits, and format the messages from it so
the two cannot drift. Scripts declaring none are skipped and counted, so adding
this check to a repository fails nothing that has not opted in.

Nothing about any repository's layout is assumed. Subjects and test
directories are given as arguments. When `--tests` is omitted the script looks
for a `tests/` directory beside the subject's skill and at the invocation root,
and the report names what it considered -- silence about the candidate set is
what turns a heuristic into a false clean.

What this is not. It is a floor. A test source containing a fragment is not
proof that an assertion fires, and only executing the case proves the branch is
reachable. It catches the absent red case, which is cheap; branch coverage
catches the unreachable one, which is not.

Usage:
    python lint-finding-coverage.py <subject.py> [<subject.py> ...] [--tests DIR]
    python lint-finding-coverage.py --discover <root>

Exit codes: '0' no findings, including when every subject declared no
catalogue and was skipped as not opted in; '1' at least one finding, which
includes a discovery scan where no subject declared one at all; '2' the check
could not run -- a subject path outside the invocation root.
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

FINDING_KINDS = {
    "uncovered": "can emit findings no test observes",
    "no-suite": "declares findings but no test source was found",
    "nobody-opted-in": "no subject declares FINDING_KINDS",
    "unconfined": "refusing path outside root",
    "unreadable": "could not be parsed",
    # Distinctive enough that a test's own function name cannot supply it: a bare
    # common word was matched by `def test_..._searched...` and reported covered
    # with both assertions deleted.
    "searched": "directories searched",
    "missing": "path does not resolve",
}


def confined(path: Path, root: Path) -> Path | None:
    """The canonical path if it is a regular file inside ``root``, else None.

    Canonicalise first and re-check containment on the *resolved* path: `~`
    expansion and `..` rejection do not stop an in-boundary symlink pointing
    out, which is the escape this repository's security rule names. A link, a
    reparse point, or anything that is not a regular file is refused rather than
    followed, because every path here arrives from a caller or is derived from
    one.
    """
    try:
        real = path.resolve(strict=True)
    except (OSError, RuntimeError):
        return None
    base = root.resolve()
    if real != base and base not in real.parents:
        return None
    if path.is_symlink() or not real.is_file():
        return None
    return real


def confined_dir(path: Path, root: Path) -> Path | None:
    """The same contract for a directory a caller supplied or the walk derived."""
    try:
        real = path.resolve(strict=True)
    except (OSError, RuntimeError):
        return None
    base = root.resolve()
    if real != base and base not in real.parents:
        return None
    if path.is_symlink() or not real.is_dir():
        return None
    return real


def _rel(path: Path, root: Path) -> str:
    """A path as the caller's repository sees it.

    Every emitted path goes through here. An absolute host path is wrong in a
    review, a commit message and an issue alike -- and it carries the operator's
    home directory into text an agent pastes elsewhere.
    """
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _is_test_file(path: Path) -> bool:
    """Whether this is a test module rather than a subject.

    Matched on the test-file shapes a runner collects -- a ``test_``/``test-``
    prefix or a ``_test`` suffix -- not on the substring, which excluded any
    checker whose name happens to contain the word.
    """
    stem = path.stem
    return stem.startswith(("test_", "test-")) or stem.endswith(("_test", "-test"))


def catalogue(subject: Path, root: Path | None = None) -> dict[str, str] | None:
    """Read `FINDING_KINDS` from a subject without importing it.

    Parsed rather than imported: a subject with side effects at import must never
    run merely because something checked its coverage.
    """
    real = confined(subject, root) if root is not None else subject
    if real is None:
        return None
    try:
        tree = ast.parse(real.read_text(encoding="utf-8", errors="replace"))
    except (OSError, SyntaxError):
        # None, not {}. A subject that cannot be read is not a subject that
        # declares nothing, and counting the two together reports an unreadable
        # file as a deliberate non-participant.
        return None
    for node in tree.body:
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Dict):
            continue
        if "FINDING_KINDS" not in [t.id for t in node.targets if isinstance(t, ast.Name)]:
            continue
        return {
            str(k.value): str(v.value)
            for k, v in zip(node.value.keys, node.value.values)
            if isinstance(k, ast.Constant) and isinstance(v, ast.Constant)
        }
    return {}


def test_dirs(subject: Path, given: list[Path], root: Path) -> list[Path]:
    """Where a subject's tests might live, without assuming a repository shape."""
    if given:
        # A caller-supplied directory is confined like everything else: an
        # out-of-root tests tree could otherwise satisfy the coverage predicate
        # with a file the repository does not contain.
        return [d for d in (confined_dir(g, root) for g in given) if d is not None]
    skill = subject.parent.parent                      # <skill>/scripts/x.py
    # Walk upward looking for a tests tree that names this skill, rather than
    # assuming a fixed depth. An installed skill, a pack in a catalogue and a
    # loose script all sit at different depths from their suite, and guessing one
    # of them finds nothing in the other two -- silently, which is the failure
    # this whole check exists to detect.
    candidates = [skill / "tests"]
    here = skill.parent
    base = root.resolve()
    while True:
        candidates += [here / "tests" / "skills" / skill.name, here / "tests" / skill.name]
        # Terminate at the boundary at any depth. Stopping only on `here == root`
        # let a subject at the root make `skill.parent` the root's parent, so the
        # walk climbed past the boundary and offered ancestors above it.
        try:
            at_or_above = here.resolve() == base or base not in here.resolve().parents
        except (OSError, RuntimeError):
            break
        if at_or_above or here.parent == here:
            break
        here = here.parent
    seen, out = set(), []
    for candidate in candidates:
        directory = confined_dir(candidate, root)
        if directory is None:
            continue
        if directory.is_dir() and directory not in seen:
            seen.add(directory)
            out.append(directory)
    # The repository-wide tests tree is a *fallback*, taken only when nothing
    # names this skill. Including it alongside a specific match means a fragment
    # observed by an unrelated suite reads as covered — a false clean, and the
    # one this check exists to prevent.
    if not out and (root / "tests").is_dir():
        out.append(root / "tests")
    return out


def sources(dirs: list[Path], root: Path) -> str:
    """Every test module under these directories, by one shared shape.

    `_is_test_file` decides what a test module is here too. Globbing
    'test_*.py' while the subject exclusion also accepted a '_test' suffix meant
    a repository using 'foo_test.py' had its suites excluded from being subjects
    and never read as sources either, which turns every declared finding kind
    into a false 'no test observes'.
    """
    chunks = []
    for directory in dirs:
        for path in sorted(p for p in directory.rglob("*.py") if _is_test_file(p)):
            real = confined(path, root)
            if real is None:
                continue
            chunks.append(real.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(chunks)


def check(subjects: list[Path], given: list[Path],
          root: Path) -> tuple[list[str], int, int, int, list[str]]:
    findings: list[str] = []
    participating = skipped = unreadable = 0
    searched: list[str] = []
    for subject in subjects:
        kinds = catalogue(subject, root)
        if kinds is None:
            unreadable += 1
            findings.append(f"{_rel(subject, root)}: {FINDING_KINDS['unreadable']}")
            continue
        if not kinds:
            skipped += 1
            continue
        participating += 1
        dirs = test_dirs(subject, given, root)
        searched += [_rel(d, root) for d in dirs]
        body = sources(dirs, root)
        if not body:
            findings.append(
                f"{_rel(subject, root)}: {FINDING_KINDS['no-suite']} "
                f"(looked in {', '.join(_rel(d, root) for d in dirs) or 'no candidate directory'})"
            )
            continue
        missing = sorted(name for name, fragment in kinds.items() if fragment not in body)
        if missing:
            findings.append(
                f"{_rel(subject, root)}: {FINDING_KINDS['uncovered']}: {', '.join(missing)}"
            )
    return findings, participating, skipped, unreadable, searched


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("subject", nargs="*", type=Path)
    parser.add_argument("--tests", action="append", type=Path, default=[])
    parser.add_argument("--discover", type=Path, default=None,
                        help="find subjects under a root, any layout")
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args(argv)

    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

    root = args.root.resolve()
    subjects = [s.resolve() for s in args.subject]
    refused: list[Path] = []
    if args.discover:
        # Confined before the walk, not after it. Resolving and then reading
        # every `*.py` underneath before the containment loop meant an
        # out-of-root tree was fully read and parsed, and only then refused.
        base = confined_dir(args.discover, root)
        if base is None:
            print(f"lint-finding-coverage: {FINDING_KINDS['unconfined']}: "
                  f"{_rel(args.discover.resolve(), root)}")
            return 2
        # `catalogue(p) is not None` admits a subject that declares a catalogue;
        # `catalogue(p) is None` admits one that could not be read. Filtering on
        # truthiness dropped the second silently, so the unreadable finding was
        # unreachable in exactly the mode that scans a tree the caller has not
        # inspected.
        # A subject is excluded only if it looks like a test *file*, not if the
        # word appears anywhere in its name: `lint-pack-test-boundary.py` is a
        # checker, and dropping it left it unchecked, uncounted and unnamed --
        # the silent omission this check exists to report in other suites.
        # A refused candidate is named, never dropped. `confined` returns None
        # for a link, an unresolvable path and a containment failure alike, and
        # `continue` left all three in no list at all -- reported as neither
        # checked, skipped nor unreadable, which is the same silent omission as
        # the test-file filter above.
        for candidate in sorted(base.rglob("*.py")):
            if _is_test_file(candidate):
                continue
            if confined(candidate, root) is None:
                refused.append(candidate)
                continue
            kinds = catalogue(candidate, root)
            if kinds is None or kinds:
                subjects.append(candidate)
    # Confinement first, on every supplied path, before anything reads or
    # classifies it: a path outside the root is refused whether or not it
    # exists, and deciding existence first would let an out-of-root path be
    # reported as a typo instead of refused.
    for subject in subjects:
        if root != subject and root not in subject.parents:
            print(f"lint-finding-coverage: {FINDING_KINDS['unconfined']}: {_rel(subject, root)}")
            return 2
    # Only then: a caller's path typo is not a malformed subject. Collapsing the
    # two reported an adopter's mistyped argument as "could not be parsed",
    # which sends them to debug a checker instead of their command line.
    missing = [s for s in subjects if not s.exists()]
    subjects = [s for s in subjects if s.exists()]

    findings, participating, skipped, unreadable, searched = check(subjects, args.tests, root)
    findings = ([f"{_rel(s, root)}: {FINDING_KINDS['unconfined']}" for s in refused]
                + [f"{_rel(s, root)}: {FINDING_KINDS['missing']}" for s in missing]
                + findings)
    for finding in findings:
        print(f"lint-finding-coverage: {finding}")
    if args.discover is not None and not participating:
        # A *discovery* scan that finds no participant is the vacuous pass this
        # check exists to detect: it would report success over a tree it never
        # examined. An explicitly named subject that has not opted in is a
        # different thing -- the caller chose the file, and a skip is the honest
        # answer -- so the guard is scoped to discovery rather than to both.
        print(f"lint-finding-coverage: {FINDING_KINDS['nobody-opted-in']} "
              f"({len(subjects)} subject(s) scanned under {args.discover})")
        return 1
    # The searched set is named on every path, not only when nothing was found:
    # a fragment observed by an unrelated suite reads as covered, and only the
    # directory list makes that visible.
    if searched:
        # The directory list is unbounded across many subjects, so it is capped
        # with an exact remainder. The set still has to be named -- silence about
        # it is what turns a heuristic into a false clean -- but naming it must
        # not itself flood.
        uniq = sorted(set(searched))
        head = ", ".join(uniq[:6])
        tail = f" and {len(uniq) - 6} more" if len(uniq) > 6 else ""
        print(f"lint-finding-coverage: {FINDING_KINDS['searched']} {head}{tail}")
    print(f"lint-finding-coverage: {len(findings)} finding(s); "
          f"{participating} subject(s) checked, {skipped} skipped as not opted in, "
          f"{unreadable} unreadable.")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
