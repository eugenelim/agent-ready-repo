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

## REVIEW — implementation rounds

- Round 1's adversarial findings were all refuted: the strings it cited do not exist in the pack. Rounds 2–8 each sustained findings, and each was repaired in its own commit. The main ones: `stats --json` returns the indexed commit and freshness; there are several `STALENESS:` line forms, and silence from text `stats` proves nothing; a graph is current only when `commits_behind` is 0 and `staleness.unknown` is empty; `--repo` graphs report provenance under `repos[]`; `query`, `clusters` and `context` print stale lines before their JSON; seven commands turn a missing database path into an empty graph; `rules-recall --steering-type` exists; the `drift` output is not meaningful before `tfstate`. An adopter-copy review sustained five wording fixes.
- Owner decisions: the zero-byte `graph.db` case is handled in SKILL.md text, and `estate_preflight.py` is unchanged. The review retry cap was overridden twice, first for the round-7 repair and then for the one-sentence `drift` correction. The final scoped review of that correction was clean.
- The 0.26.0 binary was observed on a scratch git repository. `stats --json` returned a commit and `commits_behind` 0. After one more commit, `lineage` printed `STALENESS: 1 commit(s) since last index` and `path` printed the same line in text mode. On the non-git fixture, `stats --json` returned `commits_behind: null` with the root in `unknown`, and `lineage` printed `STALENESS: unknown for <root>`. `rank --limit 999` printed `CLAMPED: limit=999 … used limit=200`. Shipped prose labels these behaviours source-read, because no criterion pins them.

## End-to-end QA

On a scratch git repository with two Python functions:
- With `wicked-estate 0.21.0` first on `PATH`, `estate_preflight.py --check` exits 4 with `required: 0.26` and the pinned install command.
- With 0.26.0 first, it exits 3 before indexing and 0 after `wicked-estate index .`.
- `wicked-estate lineage entry --json` returns `helper` (`total` 1, `relation` `dependency`).
- `wicked-estate blast-radius helper --json` returns `entry` and `m.py`, each with per-row `depth` 1.
- `stats --json` reports `commits_behind` 0 and an empty `unknown`.

## Projection

- On the PR head, `agentbundle catalogue self-host --root . --write` exits 0 and leaves `git status --porcelain` empty (AC-0048). `agentbundle catalogue verify --root .` exits 0 (AC-0049).

## Local rollout

- On 2026-10-11, `cargo install wicked-estate --version 0.26.0 --locked` replaced the maintainer's `~/.cargo/bin/wicked-estate` 0.21.0 with 0.26.0.
- `wicked-estate index .` on the main checkout exited 0. `stats --json` reports 76,023 nodes, 119,696 edges, `indexed_version` 0.26.0 and `commits_behind` 0.
