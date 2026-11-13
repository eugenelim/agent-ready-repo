# Self-test untracked plant window

- **Slug:** `selftest-untracked-plant-window`
- **Status:** Fulfilled
- **Fulfilled:** 2026-11-12 eugenelim: both negative CLI plants run only in disposable catalogues while one full live-tree proof remains, verified by 162 self-test cases with unchanged live status and a 158-case simulated no-symlink run.
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **Level:** feature
- **Owner:** eugenelim

## Outcome

Catalogue boundary self-tests retain end-to-end confidence without briefly
placing an untracked violation in a maintainer's live worktree.

## Opportunity

The former production-wiring proof planted two untracked files in separate lint
launches (four live-tree launches with symlinks, three without). A concurrent `git add -A` can stage a synthetic violation even though
the self-test later cleans it up.

The affected mechanism was layer 3 of `tools/test-lint-pack-test-boundary.py`, which
planted `packs/figma/.apm/skills/figma/scripts/test_planted_boundary_violation.py`
and the symlinked `packs/figma/tests/test_planted_link.py` into the real
worktree. The window was bounded three ways — a refusal to plant over an
existing path, a `finally` cleanup scoped to the planting branch, and direct
absence assertions rather than `git status` reads, because porcelain with `--untracked-files=no` cannot see
an untracked leftover. Those bounds narrowed the window; they did not remove it.

## Assumptions

- The tracked-file mutation hazard is already closed — `lint-performance-p0`
  moved the tracked-`Makefile` mutation of `selftest-mutates-tracked-makefile`
  to fixtures. Only the untracked plant window remains.
- The existing production `--root` option and disposable catalogue builders
  support isolated negative controls without a new root mechanism.
- Any replacement must preserve a real end-to-end assertion that the production
  CLI is wired to the live catalogue.

## Source

- Mode: repo-origin
- Locator: docs/specs/lint-performance-p0/spec.md
- Revision: sha256-bytes-v1:9bf95e7308260b96ba5456eb61aab8d5ab45b9fe32091c3092571ef02c724a0e

## Non-goals

- The tracked-file mutation hazard is already closed and stays out of scope.
- The clean real-tree run that proves production wiring is not weakened.

**Riskiest assumption:** disposable catalogue plants preserve end-to-end failure detection while the one clean live-tree launch proves production wiring. The clean run must retain all eight ordered success lines and the exact terminal verdict. Each isolated plant must fail with exit 1 and name its own violation; the link case must also name the symlink.

## Readiness

Route: direct-light.

The production CLI now runs both negative controls through its existing `--root` option against a disposable minimal catalogue. The real-tree launch budget is one on every host. The post-cleanup live launch is replaced with fixture cleanup and isolation checks; the measured case floor is 162 with symlinks and 158 without. Symlink-unavailable hosts retain an explicit skip.

Live-tree status must equal its initial state, including tracked and untracked files, during each active isolated plant and after cleanup. An initially dirty worktree is valid. These snapshots complement the construction rule that all plant paths stay outside the live repository; before/after snapshots alone cannot prove the absence of a transient plant.
