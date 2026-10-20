# Verification ledger: graph well-formed authoring

Evidence for each task, bound to the commit that carries it.

## T1: Changed-artifact pointer fixtures pass

- **Suite:** `packs/core/tests/skills/work-loop/test_lint_graph_pointers.py` — 49 passed in 110 s (Python 3.13, macOS, 2026-10-20). Covers VI-1001, VI-1002, and VI-1003.
- **Local gate:** `make lint-ruff lint-mypy` passed.
- **Real repository:** `lint-graph-pointers.py --root . --base-ref origin/main` printed `0 violation(s) in 1 selected artifact(s)` and exited 0.
- **Design notes found while building:**
  - `git diff` rewrote `.git/index` on Git 2.50.1 even with optional locks off. The check therefore diffs against a temporary copy of the index, which keeps repository bytes unchanged. A split-index repository refuses with exit 2.
  - Any failed Git command reports `base-unavailable`. `git-unavailable` is kept for a missing Git binary or a timeout.

## T2: Authoring sources and guidance agree on typed emission

- **Writer inventory:** 25 candidates re-derived from the bounded universe and pinned with roles: 4 templates, 2 examples, 12 instructions, 7 excluded with reasons, and no generated copies in these roots. The derived set equals the manifest.
- **Gaps fixed:** 6 sources offered the repository path as a `Brief:` value to write. They are the new-spec template, its skill, its contract reference, the author-delivery-brief skill, the field guide, and the brief template's `Slug:` comment. Two `Parent intent:` comments no longer say "never interpreted".
- **Suite:** `packs/core/tests/skills/work-loop/test_graph_pointer_authoring.py` — 23 passed in 2.3 s. Reverting each fixed file to its pre-T2 version turned the suite red.
- **Suites pinning edited files:** 646 passed and 79 subtests passed, in 258 s.
- **Guide checks:** `validate_guides.py` 0 errors, `lint-guide-titles.py` OK, `lint-guides-no-repo-only-refs.py` OK.
- **Local gate:** `make lint-ruff lint-mypy` passed.
- **Product-engineering:** no source changed, so that pack needs no version bump.
