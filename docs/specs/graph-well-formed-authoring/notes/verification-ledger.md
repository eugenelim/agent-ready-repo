# Verification ledger: graph well-formed authoring

Evidence for each task, bound to the commit that carries it.

## T1: Changed-artifact pointer fixtures pass

- **Suite:** `packs/core/tests/skills/work-loop/test_lint_graph_pointers.py` — 49 passed in 110 s (Python 3.13, macOS, 2026-10-20). Covers VI-1001, VI-1002, and VI-1003.
- **Local gate:** `make lint-ruff lint-mypy` passed.
- **Real repository:** `lint-graph-pointers.py --root . --base-ref origin/main` printed `0 violation(s) in 1 selected artifact(s)` and exited 0.
- **Design notes found while building:**
  - `git diff` rewrote `.git/index` on Git 2.50.1 even with optional locks off. The check therefore diffs against a temporary copy of the index, which keeps repository bytes unchanged. A split-index repository refuses with exit 2.
  - Any failed Git command reports `base-unavailable`. `git-unavailable` is kept for a missing Git binary or a timeout.
