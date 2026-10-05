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

## T2 — locator reader (2026-10-05)

- **Stub red.** `test_confined_file_uri_is_read_and_outside_root_is_refused` was
  materialized byte-identical from the plan block. Before `read-locator.py`
  existed it failed on `FileNotFoundError` (1 failed); after the script was
  created it passed.
- **Full suite green.** `packs/core/tests/skills/repository-grounding/`: 91
  passed, 2 skipped. Skipped are the two Windows-only tests
  (`test_windows_drive_letter_*`), which require `os.name == "nt"`.
- **lint-pack-test-boundary.** Replaced `SKILL_ROOT / rel` (dynamic loop
  variable, flagged as `_UnresolvedPath`) with an explicit `_EVALS_FILES` tuple
  of literal paths; also added `_EVALS_PY_FILES` and a consistency check. 154
  cases passed after fix.
- **SKILL.md pattern check.** `test_ac0006_skill_md_has_no_probe_instructions`
  failed initially because "Do not probe hidden configuration files" contained
  the pattern `probe hidden`. Rephrased to "Hidden configuration files, arbitrary
  local executables, and inferred endpoints are outside this set and are not
  consulted." Zero AC-0006 and AC-0007 pattern hits after fix.
- **file_safety.py byte pin.** Roster test
  `test_projected_file_safety_matches_the_agentbundle_canonical` passes;
  `repository-grounding` added to the parametrize list.
- **Windows step.** `build-check-windows.yml` carries a new
  `pytest repository-grounding locator reader (Windows placement)` step.
- **Evals.** `evals/evals.json` with 22 cases and 19 fixture files in
  `evals/files/`. `gitleaks dir <evals-dir>`: no leaks found.
- **Governance-citation grep** over shipped `.apm/` content: 0 hits.
- **Projections.** `make build-self` to be run after source commit (same
  two-commit discipline as T1).
- **Gates.** `make lint-ruff lint-mypy`: pass. `agentbundle catalogue lint
  --deep`: ok (73 warnings, all pre-existing in other packs, zero errors).
  `python3 tools/lint-ci-parity.py`: ok. `python3
  tools/test-lint-pack-test-boundary.py`: 154 passed.
