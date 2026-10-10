# Verification ledger — code-intelligence-estate-0-26

Observations from execution. The binary under test is `wicked-estate 0.26.0`,
built on 2026-10-10 with `cargo install --root /tmp/we-026-bin wicked-estate --version 0.26.0 --locked`.
The maintainer's `PATH` carried `wicked-estate 0.21.0` during T1–T3; each suite run put the 0.26.0 build first.

## Base

- The branch was fast-forwarded onto current `main` before PLAN. The pack was at 0.1.7, so this change releases 0.1.8.
- Baseline before any edit: with 0.26.0 first on `PATH`, the live suite had 7 failed, 62 passed; with 0.21.0, 69 passed.

## T1 — suites on the 0.26.0 surface

- An implementer wrote T1 (commit `6d8ec4394`). The controller then found `test_retired_claim_planted_samples` red: the per-dependent-depth-is-MCP-only pattern had no stale sample, and the `gaps.md` "carries `ts`, not `last_verified`" pattern had been dropped. The controller restored that pattern and planted both real sentences.
- `_ESTATE_CLI_VERBS` in `test_composition_example.py` now loads the allowlist's `CLI_VERBS` instead of copying it.
- With the 0.26.0 binary first on `PATH`: 15 failed, 215 passed. The 15 are exactly the T1 Done-when list; every live test and both planted-sample tests pass.

## T2 — prose teaches 0.26.0

- An implementer wrote T2 (commit `5551473eb`, 19 files). With the 0.26.0 binary first on `PATH`: 1 failed, 229 passed; the one failure is the T3-owned version test. Guide `pin` and `retired` commands exit 0; `tools/test_check_output_readability.py` 36 passed; `make lint-ruff lint-mypy` pass.
- The implementer read each file whole before editing and the diffs after; the post-edit whole-file read is completed by the REVIEW pass.

## T3 — release and projection

- `pack.toml` and `plugin.json` carry 0.1.8; `FORCE=1 make build-self` set the marketplace entry to 0.1.8; the changelog carries `## [code-intelligence][0.1.8] — 2026-10-10` with Highlights, because the change alters what a pack consumer can do.
