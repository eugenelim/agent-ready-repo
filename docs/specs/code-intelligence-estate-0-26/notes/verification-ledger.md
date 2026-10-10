# Verification ledger — code-intelligence-estate-0-26

Observations from execution. The binary under test is `wicked-estate 0.26.0`,
built on 2026-10-10 with `cargo install --root /tmp/we-026-bin wicked-estate --version 0.26.0 --locked`.
The maintainer's `PATH` carried `wicked-estate 0.21.0` during T1–T3; each suite run put the 0.26.0 build first.

## Base

- The branch was fast-forwarded onto current `main` before PLAN. The pack was at 0.1.7, so this change releases 0.1.8.
- Baseline before any edit: with 0.26.0 first on `PATH`, the live suite had 7 failed, 62 passed; with 0.21.0, 69 passed.
