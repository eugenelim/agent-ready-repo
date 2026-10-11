# Verification ledger — code-intelligence-estate-0-29

Observations from execution. The binary under test is `wicked-estate 0.29.2`,
built on 2026-10-11 with `cargo install --root /tmp/we-0292-bin wicked-estate --version 0.29.2 --locked`.
The maintainer's `PATH` carries `wicked-estate 0.26.0`; each suite run puts the 0.29.2 build first.

## Base

- The branch was fast-forwarded onto current `main` before PLAN. The pack was at 0.1.8, so this change releases 0.1.9.
- Baseline before any edit: with 0.29.2 first on `PATH`, the pack suite had 4 failed, 226 passed. The four are the blast-radius and lineage key sets, the version string, and the lineage default depth.
- Paging was observed on a scratch repository whose `helper` had 1,500 callers: `blast-radius helper` paged 1,503 rows over 12 pages, `lineage fan_out` 1,501 over 12, all distinct; a cursor with another `--depth`, a malformed cursor, and a cursor from before a re-index that changed the answer each exited 1 with nothing on stdout.
