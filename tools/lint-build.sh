#!/usr/bin/env bash
# Two-part build-pipeline lint:
#
#   1. Stdlib-import audit — walks every .py under
#      packages/agentbundle/agentbundle/build/ (excluding the
#      tests/fixtures/ subtree, which may carry realistic hook payloads
#      that import third-party packages), parses import statements via
#      ast, and asserts every top-level package name is either in
#      sys.stdlib_module_names (Python 3.10+) or begins with "agentbundle."
#      (intra-package imports). Any non-stdlib non-agentbundle import is
#      reported to stderr as:
#        <relative-path>:<lineno>: non-stdlib import '<name>'
#      and the script exits non-zero.
#
#   2. No-new-top-level-directory audit — compares the root-level
#      directories in HEAD against the merge-base of HEAD and main using
#      `git ls-tree -d --name-only`.  The -d flag scopes the check to
#      directories only so new root-level files (Makefile, .gitignore,
#      etc.) don't trip it.  The merge-base comparison stays correct even
#      after a merge from main into the feature branch.  `comm -23`
#      between the two sorted lists is empty iff no new top-level
#      directory has been introduced.
#
# Exit codes: 0 = clean, 1 = violation(s) found.

set -uo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

# ── 1. Stdlib-import audit ─────────────────────────────────────────────────

# LINT_BUILD_DIR can be overridden in tests to point at a scratch directory.
BUILD_DIR="${LINT_BUILD_DIR:-packages/agentbundle/agentbundle/build}"
FIXTURES_SUBDIR="${LINT_BUILD_DIR:-packages/agentbundle/agentbundle/build}/tests/fixtures"

# Collect .py files under BUILD_DIR, excluding FIXTURES_SUBDIR.
py_files=()
while IFS= read -r f; do
  py_files+=("$f")
done < <(find "$BUILD_DIR" -name "*.py" ! -path "$FIXTURES_SUBDIR/*" | sort)

import_violations=0

if (( ${#py_files[@]} > 0 )); then
  # Run a single Python process over all files to amortise startup cost.
  python3 - "${py_files[@]}" <<'PY'
import ast, sys

# sys.stdlib_module_names is available in Python 3.10+.
stdlib = sys.stdlib_module_names

violations = 0
for path in sys.argv[1:]:
    try:
        source = open(path).read()
        tree = ast.parse(source, filename=path)
    except SyntaxError as exc:
        print(f"{path}:{exc.lineno}: syntax error: {exc.msg}", file=sys.stderr)
        violations += 1
        continue

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                if top not in stdlib and not alias.name.startswith("agentbundle.") and top != "agentbundle":
                    print(f"{path}:{node.lineno}: non-stdlib import '{alias.name}'", file=sys.stderr)
                    violations += 1
        elif isinstance(node, ast.ImportFrom):
            if node.module is None:
                continue  # relative import with no module name
            top = node.module.split(".")[0]
            if node.level == 0 and top not in stdlib and not node.module.startswith("agentbundle.") and top != "agentbundle":
                print(f"{path}:{node.lineno}: non-stdlib import '{node.module}'", file=sys.stderr)
                violations += 1

sys.exit(1 if violations else 0)
PY
  import_violations=$?
fi

if (( import_violations == 0 )); then
  echo "lint-build: stdlib-import audit passed"
fi

# ── 2. No-new-top-level-directory audit ───────────────────────────────────

merge_base="$(git merge-base HEAD main 2>/dev/null)" || {
  echo "lint-build: warning: could not compute merge-base HEAD main; skipping top-level audit" >&2
  exit "$import_violations"
}

new_dirs="$(comm -23 \
  <(git ls-tree -d --name-only HEAD | sort) \
  <(git ls-tree -d --name-only "$merge_base" | sort))"

if [[ -n "$new_dirs" ]]; then
  echo "lint-build: new top-level directories introduced (RFC required):" >&2
  while IFS= read -r dir; do
    echo "  $dir" >&2
  done <<< "$new_dirs"
  exit 1
fi

echo "lint-build: no-new-top-level-directory audit passed"

exit "$import_violations"
