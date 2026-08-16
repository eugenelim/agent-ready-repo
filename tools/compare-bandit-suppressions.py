#!/usr/bin/env python3
"""Prove a `# nosec` edit changed no suppression, by scanning two clean worktrees.

Run this whenever a suppression comment is touched. Rewriting one is supposed to
be behaviour-preserving, and the only way to know is to compare what bandit
reports before and after — but the comparison has four traps that each produced
a *wrong answer* the first time the procedure was run by hand
(`docs/specs/bandit-nosec-comment-hygiene` § Testing Strategy). This script
exists so they are encoded once instead of re-derived:

  1. **Rows are not keys.** A scan of this repo yields ~362 raw result rows that
     collapse to ~239 distinct `(filename, test_id, issue_text)` keys. Comparing
     row counts answers a different question than comparing key sets. This
     reports both and diffs the keys.
  2. **Both sides must be clean worktrees** — never a worktree against the
     development tree. A dev tree carries gitignored build output
     (`packages/agentbundle/build/lib/…`) a worktree does not; scanning one of
     each inflated both totals and produced a 27-key phantom delta.
  3. **Relative scan roots**, resolved from each worktree's own root. Absolute
     paths stop `bandit.yaml`'s `exclude_dirs: '*/tests/*'` glob from matching,
     so the two scans silently cover different file sets.
  4. **Both scans exit 1** at the low/low floor, because findings are expected
     there. A non-zero exit is not an error and must not abort the run.

Two complementary checks, because neither is sufficient alone:

  * **Reported findings.** Catches a suppression that weakened, or that widened
    onto a test which fires somewhere in the repo.
  * **Resolved-id inventory.** Runs every suppression comment at both revisions
    through bandit's own `_parse_nosec_comment`. Catches the case the scan
    cannot see — a suppression widened onto a test that fires nowhere today, and
    any directive that resolves to no id at all (a blanket suppression).

Line numbers are deliberately excluded from the finding key: a comment edit
shifts them without changing what is suppressed.

Usage:
    python3 tools/compare-bandit-suppressions.py <base-ref> [<head-ref>]

`head-ref` defaults to HEAD. Pin `base-ref` to a SHA rather than a branch name
so the check stays reproducible after the branch moves.

Exit 0 = the two revisions suppress the same things, 1 = they differ,
2 = the comparison could not be performed.

Requires `bandit` on PATH and importable — this is a bandit driver, so the
repo's pure-stdlib rule for `tools/` scripts cannot apply to it; that is stated
rather than worked around.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess  # nosec B404  # list argv, no shell; argv[0] is "git" or "bandit"
import sys
import tempfile
import tokenize
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

REPO_ROOT = Path(__file__).resolve().parent.parent

# Trap 4: findings ARE expected at this floor, so a non-zero exit is normal.
# The floor is deliberately lower than `make sast`'s medium/medium — a
# suppression that moved a low-severity finding is still a moved suppression.
FLOOR = ["--severity-level", "low", "--confidence-level", "low"]


class CompareError(RuntimeError):
    """The comparison could not be performed."""


def _run(argv: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(  # nosec B603  # list argv, no shell; argv[0] is "git" or "bandit"
        argv, cwd=cwd, capture_output=True, encoding="utf-8",
        errors="surrogateescape", check=False,
    )


def sast_dirs(root: Path) -> list[str]:
    """Return the Makefile's SAST_DIRS. Trap 3 — these stay RELATIVE."""
    import re  # noqa: PLC0415

    text = (root / "Makefile").read_text(encoding="utf-8")
    matches = re.findall(r"^SAST_DIRS\s*[:+?]*=\s*(.+)$", text, re.MULTILINE)
    if len(matches) != 1:
        raise CompareError(f"expected exactly one SAST_DIRS assignment, found {len(matches)}")
    return matches[0].split("#", 1)[0].split()


def scan(worktree: Path, roots: list[str]) -> tuple[set[tuple[str, str, str]], int, str]:
    """Return `(keys, raw_row_count, stderr)` for a bandit scan of `worktree`.

    Trap 3: `roots` are relative and `cwd` is the worktree, so `exclude_dirs`
    globs match the same way on both sides. Trap 1: the key drops the line
    number, because a comment edit shifts lines without changing coverage.
    """
    out = worktree / ".bandit-compare.json"
    completed = _run(
        ["bandit", "-r", *roots, "-c", "bandit.yaml", *FLOOR, "-f", "json", "-q",
         "-o", str(out)],
        cwd=worktree,
    )
    # Trap 4: exit 1 means "findings", which is the expected state here. Only a
    # missing report is fatal.
    if not out.exists():
        raise CompareError(
            f"bandit produced no report in {worktree} (exit {completed.returncode}): "
            f"{completed.stderr.strip()[:400]}"
        )
    results = json.loads(out.read_text(encoding="utf-8"))["results"]
    keys = {
        (_worktree_relative(r["filename"], worktree), r["test_id"], r["issue_text"])
        for r in results
    }
    return keys, len(results), completed.stderr


def _worktree_relative(filename: str, worktree: Path) -> str:
    """Return `filename` relative to `worktree`, whatever form bandit reported.

    Deliberately string-based. `Path(...).resolve()` would anchor a *relative*
    report to this process's cwd — which is the repo, not the worktree — and
    silently produce paths from the wrong tree. That is trap 2 wearing a
    different hat, and it raised a confusing `relative_to` error the first time.
    """
    text = filename.replace("\\", "/")
    for prefix in (str(worktree.resolve()) + "/", str(worktree) + "/", "./"):
        if text.startswith(prefix.replace("\\", "/")):
            text = text[len(prefix):]
            break
    return text


def inventory(worktree: Path, roots: list[str]) -> dict[str, set[str]]:
    """Return `{"<path>:<line>": {resolved ids}}` for every suppression.

    The half the reported-finding diff cannot see. Uses bandit's own parser, so
    what is recorded is what bandit would actually apply — including an empty
    set, which is a blanket suppression of the whole statement.
    """
    from bandit.core import manager  # noqa: PLC0415

    found: dict[str, set[str]] = {}
    listing = _run(["git", "ls-files", "-z", "--", *roots], cwd=worktree)
    if listing.returncode != 0:
        raise CompareError(f"git ls-files failed in {worktree}: {listing.stderr.strip()}")
    for name in listing.stdout.split("\0"):
        if not name.endswith(".py"):
            continue
        path = worktree / name
        if not path.exists():
            continue
        try:
            with tokenize.open(path) as handle:
                source = handle.read()
            for token in tokenize.generate_tokens(iter(source.splitlines(True)).__next__):
                if token.type != tokenize.COMMENT:
                    continue
                resolved = manager._parse_nosec_comment(token.string)
                if resolved is not None:
                    found[f"{name}:{token.start[0]}"] = set(resolved)
        except (OSError, UnicodeDecodeError, SyntaxError, tokenize.TokenError):
            # A file bandit cannot read is a scan-integrity problem the gate
            # reports; it is not this comparison's business to fail on it.
            continue
    return found


def compare(base_ref: str, head_ref: str) -> int:
    for tool in ("git", "bandit"):
        if shutil.which(tool) is None:
            raise CompareError(f"`{tool}` is required and not on PATH")

    roots = sast_dirs(REPO_ROOT)
    print(f"comparing {base_ref} -> {head_ref} over: {' '.join(roots)}\n")

    with tempfile.TemporaryDirectory(prefix="bandit-compare-") as raw:
        trees: dict[str, Path] = {}
        try:
            for label, ref in (("base", base_ref), ("head", head_ref)):
                # Trap 2: a clean worktree on BOTH sides. Never compare against
                # the working tree — its gitignored build output is scanned too.
                path = Path(raw) / label
                created = _run(
                    ["git", "worktree", "add", "-q", "--detach", str(path), ref],
                    cwd=REPO_ROOT,
                )
                if created.returncode != 0:
                    raise CompareError(
                        f"could not create a worktree for {ref!r}: {created.stderr.strip()}"
                    )
                trees[label] = path

            scans = {}
            invs = {}
            for label in ("base", "head"):
                keys, rows, stderr = scan(trees[label], roots)
                scans[label] = (keys, rows, stderr)
                invs[label] = inventory(trees[label], roots)
                warn_lines = len([ln for ln in stderr.splitlines() if ln.strip()])
                print(f"  {label:4} ({base_ref if label == 'base' else head_ref}): "
                      f"{rows} rows -> {len(keys)} distinct keys, "
                      f"{len(invs[label])} suppressions, {warn_lines} stderr line(s)")
        finally:
            for path in trees.values():
                _run(["git", "worktree", "remove", "--force", str(path)], cwd=REPO_ROOT)

    print()
    failed = False

    base_keys, _, _ = scans["base"]
    head_keys, _, _ = scans["head"]
    only_base = sorted(base_keys - head_keys)
    only_head = sorted(head_keys - base_keys)
    if only_base or only_head:
        failed = True
        print("REPORTED FINDINGS DIFFER:", file=sys.stderr)
        # Deliberately does not name a cause. A finding present on one side only
        # has two possible explanations — a suppression moved, or the code did
        # (a new file, a deleted one, an edit that introduced or removed the
        # finding). Asserting the first would be wrong every time the second is
        # true, which this tool's own validation run demonstrated: three
        # findings appeared at head purely because an unrelated PR added a file.
        # Read these rows against the resolved-id result below, which is the
        # half that isolates suppression changes from code changes.
        for key in only_base:
            print(f"  - at base only (suppression widened at head, OR the code "
                  f"stopped producing it): {key}", file=sys.stderr)
        for key in only_head:
            print(f"  + at head only (suppression weakened at head, OR the code "
                  f"newly produces it): {key}", file=sys.stderr)
    else:
        print(f"reported findings: identical ({len(base_keys)} distinct keys)")

    # The inventory is keyed by path:line, and a comment edit moves lines — so
    # compare the multiset of resolved id-sets per file, not per line.
    def by_file(inv: dict[str, set[str]]) -> dict[str, list[frozenset]]:
        out: dict[str, list[frozenset]] = {}
        for locator, ids in inv.items():
            out.setdefault(locator.rsplit(":", 1)[0], []).append(frozenset(ids))
        return {k: sorted(v, key=sorted) for k, v in out.items()}

    base_inv, head_inv = by_file(invs["base"]), by_file(invs["head"])

    # Only a file present at BOTH revisions can have had its suppressions
    # changed. A file added at head brings new suppressions by definition, and
    # a deleted file takes its own with it — both are worth printing, neither is
    # an equivalence violation. Conflating them made this script's own first run
    # report a false FAIL, because the change it was checking added two files.
    shared = sorted(set(base_inv) & set(head_inv))
    changed = [name for name in shared if base_inv[name] != head_inv[name]]
    if changed:
        failed = True
        print("\nRESOLVED SUPPRESSION IDS DIFFER:", file=sys.stderr)
        for name in changed:
            print(f"  {name}:\n      base {base_inv[name]}\n      head {head_inv[name]}",
                  file=sys.stderr)
    else:
        total = sum(len(base_inv[name]) for name in shared)
        print(f"resolved suppression ids: identical across {len(shared)} shared "
              f"file(s) ({total} directives)")

    added = sorted(set(head_inv) - set(base_inv))
    removed = sorted(set(base_inv) - set(head_inv))
    for name in added:
        print(f"  note: new file at head carries {len(head_inv[name])} "
              f"suppression(s): {name}")
    for name in removed:
        print(f"  note: file gone at head, took {len(base_inv[name])} "
              f"suppression(s) with it: {name}")

    blanket = {k: v for k, v in invs["head"].items() if not v}
    if blanket:
        failed = True
        print("\nBLANKET SUPPRESSIONS AT HEAD (resolve to no test id):", file=sys.stderr)
        for locator in sorted(blanket):
            print(f"  {locator}", file=sys.stderr)

    print()
    if failed:
        print("compare-bandit-suppressions: FAIL — the two revisions do not "
              "suppress the same things.", file=sys.stderr)
        return 1
    print("compare-bandit-suppressions: OK — identical reported findings and "
          "identical resolved suppression ids.")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Prove a `# nosec` edit changed no suppression.",
    )
    parser.add_argument("base_ref", help="pin to a SHA, not a moving branch name")
    parser.add_argument("head_ref", nargs="?", default="HEAD")
    args = parser.parse_args(argv[1:])
    try:
        return compare(args.base_ref, args.head_ref)
    except CompareError as exc:
        print(f"compare-bandit-suppressions: {exc}", file=sys.stderr)
        return 2
    except ImportError as exc:
        print(f"compare-bandit-suppressions: bandit is not importable ({exc}); "
              "install tools/requirements-sast.txt", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
