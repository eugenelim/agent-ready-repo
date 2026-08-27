# Self-test untracked plant window

- **Status:** Draft
- **Level:** feature

## Outcome

Catalogue boundary self-tests retain end-to-end confidence without briefly
placing an untracked violation in a maintainer's live worktree.

## Opportunity

The current production-wiring proof plants two untracked files for one lint
launch. A concurrent `git add -A` can stage a synthetic violation even though
the self-test later cleans it up.

The mechanism is layer 3 of `tools/test-lint-pack-test-boundary.py`, which
plants `packs/figma/.apm/skills/figma/scripts/test_planted_boundary_violation.py`
and the symlinked `packs/figma/tests/test_planted_link.py` into the real
worktree. The window is already bounded three ways — a refusal to plant over an
existing path, a `finally` cleanup scoped to the planting branch, and direct
absence assertions rather than `git status` reads, because porcelain cannot see
an untracked leftover. Those bounds narrow the window; they do not remove it.

## Assumptions

- The tracked-file mutation hazard is already closed — `lint-performance-p0`
  moved the tracked-`Makefile` mutation of `selftest-mutates-tracked-makefile`
  to fixtures. Only the untracked plant window remains.
- Closing the window requires a design choice between a copied worktree and a
  weaker production-wiring proof, not a local cleanup patch.
- Any replacement must preserve a real end-to-end assertion that the production
  CLI is wired to the live catalogue.

## Source

- Mode: repo-origin
- Locator: docs/specs/lint-performance-p0/spec.md
- Revision: sha256-bytes-v1:9bf95e7308260b96ba5456eb61aab8d5ab45b9fe32091c3092571ef02c724a0e
