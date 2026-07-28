---
title: Remove suppressed ruff preview-mode spacing/blank-line rules
slug: ruff-preview-spacing-fixes
---

Mode: light (no risk trigger fired)

- **Status:** Shipped

## Objective

Apply ruff auto-fixes for 11 preview-mode spacing and blank-line rules that were suppressed rather than fixed, then remove them from `pyproject.toml`'s ignore list so they are enforced going forward.

Rules: E116, E117, E221, E226, E241, E261, E272, E302, E303, E305, E306.

## Boundaries

Never do: change any logic; touch the `UP035` ignore or the `PLW1514` per-file-ignore.

## Testing Strategy

Goal-based check: `python3 -m ruff check .` clean for the 11 rules + `python3 tools/lint-ruff.py` passes.

## Acceptance Criteria

- [x] `python3 -m ruff check --fix .` applied all safe auto-fixes for the 11 rules
- [x] `python3 -m ruff check --unsafe-fixes --fix .` applied any remaining fixes
- [x] The 11 rules are removed from `pyproject.toml` ignore list; UP035 and PLW1514 per-file-ignore remain
- [x] `python3 tools/lint-ruff.py` passes clean with the rules removed

## Tasks

1. Run `ruff check --fix .` (safe fixes)
2. Run `ruff check --unsafe-fixes --fix .` (unsafe fixes for remainder)
3. Verify `python3 tools/lint-ruff.py` passes
4. Remove the 11 rules from `pyproject.toml`
5. Run `python3 tools/lint-ruff.py` again to confirm still clean
6. Commit, rebase, PR, merge
