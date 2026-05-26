#!/usr/bin/env python3
"""Two-part build-pipeline lint.

  1. Stdlib-import audit — walks every .py under
     packages/agentbundle/agentbundle/build/ (excluding the
     tests/fixtures/ subtree, which may carry realistic hook payloads
     that import third-party packages), parses import statements via
     ast, and asserts every top-level package name is either in
     sys.stdlib_module_names (Python 3.10+) or begins with "agentbundle."
     (intra-package imports). Any non-stdlib non-agentbundle import is
     reported to stderr as:
       <relative-path>:<lineno>: non-stdlib import '<name>'

  2. No-new-top-level-directory audit — compares the root-level
     directories in HEAD against the merge-base of HEAD and main using
     `git ls-tree -d --name-only`. `comm -23` between the two sorted
     lists is empty iff no new top-level directory has been introduced.

Exit codes: 0 = clean, 1 = violation(s) found.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path


# Top-level directories explicitly authorised by an Accepted RFC. Add
# entries only when an Accepted RFC authorises the new directory.
RFC_AUTHORISED_DIRS = (
    "packs",  # RFC-0002 — self-hosting source-of-truth split
    ".agentbundle",  # RFC-0013 — adapter-root-bins/ self-hosted projection (sso-broker.py + helpers)
)


def _repo_root() -> Path:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return Path(result.stdout.strip())
    except FileNotFoundError:
        pass
    return Path.cwd()


def _audit_imports(py_files: list[Path]) -> int:
    """Return violation count. Empty py_files → 0 (matches bash short-circuit
    at line 45 where the heredoc is skipped entirely)."""
    if not py_files:
        return 0
    stdlib = sys.stdlib_module_names  # Python 3.10+
    violations = 0
    for path in py_files:
        try:
            source = path.read_text()
            tree = ast.parse(source, filename=str(path))
        except SyntaxError as exc:
            print(f"{path}:{exc.lineno}: syntax error: {exc.msg}", file=sys.stderr)
            violations += 1
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    if (
                        top not in stdlib
                        and not alias.name.startswith("agentbundle.")
                        and top != "agentbundle"
                    ):
                        print(
                            f"{path}:{node.lineno}: non-stdlib import '{alias.name}'",
                            file=sys.stderr,
                        )
                        violations += 1
            elif isinstance(node, ast.ImportFrom):
                if node.module is None:
                    continue  # relative import with no module name
                top = node.module.split(".")[0]
                if (
                    node.level == 0
                    and top not in stdlib
                    and not node.module.startswith("agentbundle.")
                    and top != "agentbundle"
                ):
                    print(
                        f"{path}:{node.lineno}: non-stdlib import '{node.module}'",
                        file=sys.stderr,
                    )
                    violations += 1
    return violations


def _top_level_dirs(ref: str) -> list[str]:
    """Return sorted list of top-level directory names at *ref*."""
    result = subprocess.run(
        ["git", "ls-tree", "-d", "--name-only", ref],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        return []
    return sorted(line for line in result.stdout.splitlines() if line)


def main() -> int:
    os.chdir(_repo_root())

    # ── Part 1: Stdlib-import audit ──────────────────────────────────────
    build_dir = os.environ.get(
        "LINT_BUILD_DIR", "packages/agentbundle/agentbundle/build"
    )
    build_path = Path(build_dir)
    fixtures_path = Path(build_dir) / "tests" / "fixtures"

    py_files: list[Path] = []
    if build_path.is_dir():
        for f in sorted(build_path.rglob("*.py")):
            # Match bash `! -path "$FIXTURES_SUBDIR/*"` exclusion.
            try:
                f.relative_to(fixtures_path)
                continue  # under fixtures — skip
            except ValueError:
                pass
            py_files.append(f)

    import_violations = _audit_imports(py_files)

    if import_violations == 0:
        print("lint-build: stdlib-import audit passed")

    # ── Part 2: No-new-top-level-directory audit ─────────────────────────
    merge_base_result = subprocess.run(
        ["git", "merge-base", "HEAD", "main"],
        capture_output=True, text=True, check=False,
    )
    if merge_base_result.returncode != 0 or not merge_base_result.stdout.strip():
        print(
            "lint-build: warning: could not compute merge-base HEAD main; "
            "skipping top-level audit",
            file=sys.stderr,
        )
        # Normalise to 0/1 — bash heredoc's sys.exit(1 if violations else 0)
        # always emitted 0 or 1; raw count would change the rc shape for
        # callers that pattern-match on rc==1.
        return 1 if import_violations else 0

    merge_base = merge_base_result.stdout.strip()
    head_dirs = _top_level_dirs("HEAD")
    base_dirs = _top_level_dirs(merge_base)

    # `comm -23 <(head) <(base)` = entries in head not in base.
    new_dirs = [d for d in head_dirs if d not in base_dirs]

    if new_dirs:
        unauthorised = [d for d in new_dirs if d not in RFC_AUTHORISED_DIRS]
        if unauthorised:
            print(
                "lint-build: new top-level directories introduced (RFC required):",
                file=sys.stderr,
            )
            for d in unauthorised:
                print(f"  {d}", file=sys.stderr)
            return 1

    print("lint-build: no-new-top-level-directory audit passed")

    # Normalise to 0/1 — see comment at the merge-base early-return.
    return 1 if import_violations else 0


if __name__ == "__main__":
    sys.exit(main())
