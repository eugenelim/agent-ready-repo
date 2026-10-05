# Verification ledger: optional intelligence in repository grounding

Execution observations for the approved spec and plan. Each entry records what
was observed, not what the contract requires.

## T1 — one public grounding owner (2026-10-05)

- **Stub red, then green.** `test_explorer_has_one_home_under_repository_grounding`
  was materialized byte-identical from the plan block. Before the move it
  failed on `assert owner.is_file()` (1 failed in 0.16s); after the move it
  passed.
- **Relocated suite.** `packs/core/tests/skills/repository-grounding/`: 36
  passed. `packs/core/tests/skills/new-spec/`: 259 passed, 79 subtests.
- **Suite registration.** One Makefile line added after `receive-brief`
  (alphabetical position). `tools/lint-ci-parity.py`: ok, 73 recipe lines, 132
  roster keys dispositioned.
- **Plan-digest re-pin.** Sole cause: one added Makefile line at plan index 29;
  standalone 74 -> 75 and composed 73 -> 74 lines. Prior pins were current
  against `origin/main:Makefile`. `tools/test_local_ci_shared_test_deduplication.py`:
  51 passed.
- **Projections.** `make build-self` (no `FORCE`) refused on a dirty tree and
  wrote after the source commit. `repository-grounding` projects under
  `.claude/skills/` and `.agents/skills/`; no `new-spec` projection contains
  `scripts/explore-grounding.py`.
- **Version.** `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json`
  carry 2.28.0 (from 2.27.14; minor, new primitive).
- **Deviation — marketplace.** `.claude-plugin/marketplace.json` lists no `core`
  entry, before or after this change, because Core is repository-scope only
  (`allowed-scopes = ["repo"]`). AC-0013's marketplace-agreement clause has no
  core entry to compare. Raised for the owner at closeout.
- **Gates.** `make lint-ruff lint-mypy` passed. `agentbundle catalogue lint
  --deep`: zero errors. Governance-citation grep over shipped content: 0 hits.
