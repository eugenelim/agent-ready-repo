# Verification ledger — code-intelligence-estate-0-29

Observations from execution. The binary under test is `wicked-estate 0.29.2`,
built on 2026-10-11 with `cargo install --root /tmp/we-0292-bin wicked-estate --version 0.29.2 --locked`.
The maintainer's `PATH` carries `wicked-estate 0.26.0`; each suite run puts the 0.29.2 build first.

## Base

- The branch was fast-forwarded onto current `main` before PLAN. The pack was at 0.1.8, so this change releases 0.1.9.
- Baseline before any edit: with 0.29.2 first on `PATH`, the pack suite had 4 failed, 226 passed. The four are the blast-radius and lineage key sets, the version string, and the lineage default depth.
- Paging was observed on a scratch repository whose `helper` had 1,500 callers: `blast-radius helper` paged 1,503 rows over 12 pages, `lineage fan_out` 1,501 over 12, all distinct; a cursor with another `--depth`, a malformed cursor, and a cursor from before a re-index that changed the answer each exited 1 with nothing on stdout.

## T1 — suites on the 0.29.2 surface

- An implementer wrote T1 (commit `a60cbce6e`), adding a session-scoped wide fixture (`helper` with 300 callers, `fan_out` calling all 300) and eight paging tests. With 0.29.2 first on `PATH`: 16 failed, 231 passed; the 16 are prose, eval and manifest tests T2 and T3 own. Both planted-sample tests pass.

## T2 — prose teaches 0.29.2

- An implementer wrote T2 (commit `2640fa14b`). With 0.29.2 first on `PATH`: 1 failed (the T3 version test), 246 passed. Guide `pin` and `retired` commands exit 0; the guide paging greps exit 0; readability 36 passed; `make lint-ruff lint-mypy` pass.
- Eval prompts 1–9 are hash-pinned, so the paging and refused-cursor cases are new evals 10 and 11; eval 8's expected output now reports a lineage horizon cut at 24 as a cut.

## T3 — release and projection

- The controller implemented T3 directly rather than dispatching an implementer; the cohort receipt records it as a decline, the closest reason the receipt catalogue offers.
- `pack.toml` and `plugin.json` carry 0.1.9; `FORCE=1 make build-self` set the marketplace entry to 0.1.9; the changelog carries `## [code-intelligence][0.1.9] — 2026-10-11` with Highlights, because paging changes what a pack consumer can retrieve.
- Pack suite plus readability with 0.29.2 first on `PATH`: 283 passed. `agentbundle catalogue self-host --root . --write` leaves `git status --porcelain` empty; `agentbundle catalogue verify --root .` exits 0.

## End-to-end QA

On `/tmp/we-page` (indexed by 0.29.2):
- With `wicked-estate 0.26.0` first on `PATH`, `estate_preflight.py --check` exits 4 with `required: 0.29` and `cargo install wicked-estate --version 0.29.2 --locked`.
- With 0.29.2 first, it exits 0 (`status: ready`).
- `blast-radius helper --json` and `lineage fan_out --json` paged to a `null` cursor return 1,503 and 1,501 distinct rows over 12 pages each.
