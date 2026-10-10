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
