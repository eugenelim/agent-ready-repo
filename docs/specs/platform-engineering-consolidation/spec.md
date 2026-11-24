# Spec: Platform engineering pack consolidation and migration

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0118, ADR-0071, ADR-0101
- **Brief:** none
- **Discovery:** none
- **Depends on:** spec:platform-engineering-interchange-contracts, spec:platform-engineering-terraform-independence, spec:platform-engineering-release-admission-review, spec:platform-engineering-github-actions-execution
- **Contract:** none
- **Shape:** mixed
- **Risk triggers:** structural-interface, persistent-representation

> **Spec contract:** this document defines what done means. Agent Rules, Testing
> Strategy and Acceptance Criteria are the completion contract. Outcome, What
> Changes, Durable Outputs, Follow-ons and Assumptions are working material.
> § Closeout is controller work after the run and is not part of the criteria.

## Outcome

One `platform-engineering` pack, version 1.0.0, replaces `iac-terraform` and `release-engineering` and installs with no required dependency. Terraform authoring and drift review, release collection, admission, focused review and protected GitHub Actions execution keep their names and behaviour. Existing installs migrate in two phases (uninstall every old-pack row, then install the new pack), keep adopter-edited files as `.upstream` companions, and roll back from a pinned catalogue ref. RFC-0118 holds the decisions; this spec holds the proof.

## What Changes

- New `packs/platform-engineering/` holding every skill, agent, reference, asset, eval and test of both old packs, under the same skill and agent names.
- `packs/iac-terraform/` and `packs/release-engineering/` are deleted; `contracts/renames/pack-renames.toml` maps both names to `platform-engineering`.
- The new `pack.toml` and `.claude-plugin/plugin.json` say 1.0.0 and declare no required dependency.
- Every catalogue, CI, roster, census, site, docs-site and guide surface that names either old pack names the new one instead; frozen records (accepted RFCs and ADRs, shipped specs and their ledgers, changelog history) are not rewritten.
- `platform-engineering` ships agents, so the skills-only agent-plugin route does not offer it; the Terraform skills lose that route, which `iac-terraform` alone was eligible for.
- Core's source (`.apm/`, `seeds/` and its manifests) and every `repo-governance` file are unchanged, which keeps both packs out of a release; core's `README.md` and `JOURNEY.md`, which are documentation outside core's release scope, name the new pack. Remaining mentions in core and `repo-governance` source are left for follow-on releases of those packs.
- `guides/platform-engineering/` replaces both old guide trees, with a migration how-to.
- A changelog fragment records the release and the migration.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Pack | One pack replaces two | `packs/platform-engineering/` | platform-engineering maintainers | Pack suites, catalogue lint and verify | Old directories absent; every primitive present |
| Migration contract | Old names resolve to the new pack | `contracts/renames/pack-renames.toml` | catalogue maintainers | Rename lint and hint tests | Both entries present |
| User instructions | Adopters install, migrate and roll back | `guides/platform-engineering/` including `how-to/migrate-from-iac-terraform-and-release-engineering.md`; pack README | platform-engineering maintainers | Guide validation and link checks | Migration and rollback steps have a reader-facing home |
| Release history | Breaking rename | Changelog fragment from `tools/changelog.py new` | platform-engineering maintainers | Fragment validation | 1.0.0 recorded with migration |
| Execution evidence | Five fixtures and live runs | `docs/specs/platform-engineering-consolidation/notes/verification-ledger.md` | Delivery controller | Commands, run ids, outcomes; cloud identifiers as placeholders | Stable evidence handed to close-work |

## Migration and rollback

The documented migration, for every adapter `<a>` and scope `<s>` an old pack is installed at:

1. **Phase 1.** `agentbundle uninstall --pack iac-terraform --adapter <a> --scope <s>` and `agentbundle uninstall --pack release-engineering --adapter <a> --scope <s>`, for every installed row, before any install.
2. **Phase 2.** `agentbundle install <catalogue> --pack platform-engineering --adapter <a> --scope <s>` for each of those adapters and scopes, from a catalogue that contains the new pack.

An adopter whose old packs sit at repo and `local` scope for one adapter chooses one scope for the new pack before phase 1. Rollback reverses the phases: uninstall every `platform-engineering` row, then install the old packs from `git+https://github.com/eugenelim/agent-ready-repo@<ref>`, where `<ref>` is the last commit that still holds them. The README and the migration how-to name that ref. There is no automatic install backup; a file the adopter deletes during migration is not recovered.

## Agent Rules

### Always do

- Move files with their history (`git mv`) and keep every skill, agent, reference, script and contract name unchanged.
- Treat frozen records as history: leave accepted RFCs and ADRs, shipped specs, ledgers and released changelog entries naming the old packs as they are.
- Keep cloud account numbers, role identifiers and bucket names out of every committed file.

### Gates

The supervisor runs these commands for every task and gate run; each skill suite is its own process.

```gate-declaration
[{"argv": ["uv", "run", "--no-project", "--with", "pytest", "--with", "pyyaml", "python", "-m", "pytest", "packs/platform-engineering/tests/skills/generate-iac", "-q", "-p", "no:cacheprovider"], "cwd": ".", "expected_exit": 0},
 {"argv": ["uv", "run", "--no-project", "--with", "pytest", "--with", "pyyaml", "python", "-m", "pytest", "packs/platform-engineering/tests/skills/prepare-release-handoff", "-q", "-p", "no:cacheprovider"], "cwd": ".", "expected_exit": 0},
 {"argv": ["uv", "run", "--no-project", "--with", "pytest", "--with", "pyyaml", "python", "-m", "pytest", "packs/platform-engineering/tests/skills/release-loop", "-q", "-p", "no:cacheprovider"], "cwd": ".", "expected_exit": 0},
 {"argv": ["uv", "run", "--no-project", "--with", "ruff==0.16.10", "python", "tools/lint-ruff.py"], "cwd": ".", "expected_exit": 0}]
```

### Ask first

- Ask the owner before renaming any skill, agent or contract, changing behaviour of a moved script, or removing a dependency while a core-absent fixture fails.

### Never do

- Add an installer feature (alias, merge, prune or backup), a dependency, or a cross-pack import.
- Leave an old pack directory, or a live surface that still names an old pack as installable.
- Cite internal catalogue records, ADR numbers or spec paths in shipped `.apm/` content.

## Testing Strategy

- **Structure, goal-based (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007).** Catalogue lint and verify, the rename lint, roster and census tests, and the moved pack suites prove the pack and its registrations.
- **Surfaces, goal-based (AC-0008, AC-0009, AC-0010, AC-0011, AC-0012).** A repository search, guide validation, the site and docs-site builds and their tests prove no live surface names an old pack as installable.
- **Core-absent fixtures, integration (AC-0013, AC-0014, AC-0015, AC-0016).** Isolated roots with only the new pack and the real CLI.
- **Migration, manual QA with the real CLI (AC-0017, AC-0018, AC-0019, AC-0020, AC-0021).** Isolated Git repositories, the old catalogue checked out at the pinned commit and the current catalogue; CI's shallow clone cannot reach that commit, so the controller runs these and records commands, state rows and file listings in the ledger.
- **Live, manual QA (AC-0022, AC-0023, AC-0024).** A real Terraform provider and the GitHub.com fixture and AWS sandbox already used by the GitHub Actions spec.
- **Packaging, goal-based (AC-0025, AC-0026, AC-0027).**

## Acceptance Criteria

- [x] **AC-0001.** `packs/platform-engineering/` holds the skills `generate-iac`, `reconcile-iac`, `define-slo`, `prepare-release-handoff` and `release-loop`, the agents `release-lead`, `release-reliability-reviewer` and `release-security-reviewer`, and every reference, script, asset, eval and test the old packs held, at the same paths relative to the pack root; a byte comparison against the old packs' last commit shows every moved file unchanged except the edits this spec names.
- [x] **AC-0002.** `packs/iac-terraform/` and `packs/release-engineering/` do not exist, and `contracts/renames/pack-renames.toml` maps each old name to `platform-engineering`; `tools/lint-pack-renames.py` passes.
- [x] **AC-0003.** `packs/platform-engineering/pack.toml` and `.claude-plugin/plugin.json` both report version 1.0.0, the pack declares no `[[pack.dependencies.required]]`, it allows repo scope, and its description names Terraform authoring, release preparation and protected GitHub Actions execution.
- [x] **AC-0004.** `agentbundle catalogue lint --root . --deep` and `agentbundle catalogue verify --root .` pass with the new pack and without the old ones.
- [x] **AC-0005.** Every moved pack suite passes from its new path, the Makefile and `build-check.yml` run the new paths, and `tools/lint-ci-parity.py` and `tools/test_local_ci_shared_test_deduplication.py` pass.
- [x] **AC-0006.** The plugin roster and route-docs lints list `platform-engineering` and neither old pack, and pass; the agent-plugin route does not offer `platform-engineering` because it ships agents, and `packages/agentbundle/tests/build_pipeline/test_agent_plugin_projection.py` passes with its real-corpus roster updated to that outcome.
- [x] **AC-0007.** The skill census lists the five skills under `platform-engineering`, keeps its population size, and `tests/roster/test_skill_census.py` passes; `tests/roster/test_registry_upgrade_notes.py`, `tests/roster/test_repo_governance_rename_completeness.py` and `tests/roster/test_architecture_decision_surface_portability.py` pass with their pins and paths updated to the new pack.
- [x] **AC-0008.** `guides/platform-engineering/` holds every page of both old guide trees, with titles, links and the guide navigation baseline updated, and `guides/iac-terraform/` and `guides/release-engineering/` do not exist; `tools/validate_guides.py`, `tools/check-guide-index.py` and `tools/lint-guide-titles.py` pass.
- [x] **AC-0009.** `guides/platform-engineering/how-to/migrate-from-iac-terraform-and-release-engineering.md` gives the two-phase migration, the one-scope-per-adapter choice, the rollback with the named pinned ref, and the no-automatic-backup limit, and the pack README links it.
- [x] **AC-0010.** `site.toml`, the web catalogue and journey pages, `web/src/lib/catalogue-navigation.ts`, the docs-site sidebar and getting-started page, and their tests name `platform-engineering`; the site build and its tests pass.
- [x] **AC-0011.** The root README, `docs/architecture/lifecycle-flow.md`, `docs/product/journeys/engineer-provisions-infrastructure.md` and the pack-specific GitHub workflows name `platform-engineering` and its new paths; `.github/workflows/iac-release-loop-canary.yml` and `iac-staleness.yml` point at the moved files. Core's `README.md` and `JOURNEY.md` name `platform-engineering`, no file under `packs/core/.apm/`, `packs/core/seeds/` or core's manifests changes, and no file under `packs/repo-governance/` changes.
- [x] **AC-0012.** A search of tracked files outside frozen records (accepted RFCs and ADRs, shipped specs and their notes, released changelog entries, rename fixtures, the rename map, the rollback commands of AC-0009 that install the old packs from the pinned ref, and the unchanged source of core and `repo-governance`, including the repository's self-hosted copies of that source such as `governance/manifest.example.yaml`) finds no occurrence of `iac-terraform` or `release-engineering` that names an installable pack, and the ledger records the search and each remaining occurrence's category.
- [x] **AC-0013.** Terraform-only: the moved `generate-iac` suites, including the Terraform-only journey (native ADRs, no core or governance pack, a real `providers schema -json` output, `validate`, saved plan and plan bundle) and the skill-independence pins that keep `reconcile-iac` to managed resources with no apply or destroy, pass from the new path; and `agentbundle install --pack platform-engineering` into an isolated Git repository with no core or repo-governance installed succeeds.
- [x] **AC-0014.** Release-only: in an isolated root with only `platform-engineering` installed and no Terraform tooling on the path, collection, admission, both focused reviews, every stage check and the GitHub Actions offline journeys pass.
- [x] **AC-0015.** End-to-end: in an isolated root with only `platform-engineering`, a plan bundle produced by `generate-iac` becomes a `terraform-plan` component of a release candidate beside an `oci-image` component, and the candidate completes collection, admission, pre-deploy review, `readiness`, `bind`, `budget`, `recheck`, `reconcile`, `summary`, post-deploy review and the final stage with cleanup `torn-down`. In the same root, a failed post-deploy check on that candidate yields a `repair-handoff` naming its repair owner, and an interrupted run (a `mutate-` step started with no terminal ops record) reconciles to `pause` before any retry.
- [x] **AC-0016.** Core installed: with core and `platform-engineering` installed together, the release-only and Terraform-only journeys give the same results, and an optional core reviewer's pass never replaces a local review area (the existing optional-core tests pass from the new path).
- [x] **AC-0017.** Migration happy path: in an isolated Git repository with both old packs installed from the pinned old catalogue for two adapters that share projected skill paths, phase 1 then phase 2 leave every new skill and agent installed once per adapter, no old pack row in state, and no file of the old packs that the new pack does not ship.
- [x] **AC-0018.** Adopter edits: a file edited before phase 1 is kept by uninstall with its edit, and phase 2 writes the new content beside it as a `.upstream` companion without overwriting the edit.
- [x] **AC-0019.** Duplicate activation: for every starting configuration T7 tests (same adapter and scope, another adapter, another scope), the ledger records whether installing `platform-engineering` while an old-pack row remains was refused and that a refusal changed no file or state row; after phase 1, phase 2 succeeds. Each configuration where the new pack installed beside an old row is named as a limit in the migration how-to, and phase 1 still removes every old row at every scope first.
- [x] **AC-0020.** Mixed scope and retry: with one old pack at repo scope and the other at `local` scope for one adapter, the documented one-scope choice migrates both; re-running phase 1 or phase 2 after an interruption reaches the same end state.
- [x] **AC-0021.** Rollback and hint: uninstalling `platform-engineering` and installing both old packs from the pinned ref restores them with the adopter edit kept; requesting `--pack iac-terraform` or `--pack release-engineering` from the current catalogue prints the rename hint naming `platform-engineering`.
- [x] **AC-0022.** Live Terraform: with only `platform-engineering` installed, `generate-iac` produces and reviews a saved plan against a real provider schema fetched by `terraform providers schema -json`, and the plan bundle validates; no apply or destroy runs.
- [x] **AC-0023.** Live release-only: the GitHub Actions fixture, vendoring the release skill from `platform-engineering`, runs prepare, focused review, an approved deploy and teardown with every step successful and the target observed absent afterwards.
- [x] **AC-0024.** Live end-to-end: with fixture-only changes in the scratch repository (prepare adds the AC-0022 plan bundle as a `terraform-plan` component's evidence, and the deploy job's archive allowlist admits those files), a candidate carrying that component completes an approved deploy run whose admission pins the plan bundle digest, and the run's records reconcile and summarise as audited.
- [x] **AC-0025.** A changelog fragment from `tools/changelog.py new` records `platform-engineering` 1.0.0, the removal of both old packs and the migration, and `tools/changelog.py validate` passes.
- [x] **AC-0026.** The pack's eval harnesses cover the moved skills unchanged and pass their checks from the new path.
- [x] **AC-0027.** `make build-self` leaves no diff after rebuilding; `make lint-ruff lint-mypy`, `make precheck`, `pytest tests/roster/` (apart from failures already recorded as pre-existing) and `tools/lint-pack-test-boundary.py` pass.

## Closeout

Controller work after the run, not criteria:

- Mark every `AC-` checkbox, set Status `Shipped` and hand the ledger to `close-work`.
- Update the KB plan's Section 5 completion record and status line.
- Move the GitHub Actions fixture's retirement date if the fixture is still needed.

## Follow-ons

Releases of core and `repo-governance` that update their mentions of the old pack names. Installer aliases, pack merge or prune support, install backups, and new platform-engineering capabilities are outside this contract.

## Assumptions

- Technical: the moved pack suites need only path changes, because each loads its scripts relative to its own file (settled by: T1's suite run).
- Technical: an isolated repository can install the old packs from a local catalogue checked out at the pinned commit as faithfully as from `git+https` (settled by: the migration fixtures; the live check uses the `git+https` form once).

## Terminal Intent

`code`

## Accepted Risk

none
