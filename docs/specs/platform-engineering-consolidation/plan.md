# Plan: Platform engineering pack consolidation and migration

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done
- **Repository anchors:** RFC-0118 (the decisions); `docs/specs/repo-governance-rename/` and `contracts/renames/pack-renames.toml` (the one rename precedent, map entry plus migration text); `packs/iac-terraform/` and `packs/release-engineering/` (the sources); `tools/lint-pack-renames.py`, `tools/lint-plugin-roster.py`, `tools/lint-plugin-route-docs.py`, `tools/lint-ci-parity.py`, `packs/agent-skill-engineering/tests/fixtures/skill-census.json` (registration gates). Uncertainty: whether any moved test hard-codes its pack directory name is implementation-discovered.

> **Plan contract:** Tests, Touches and Done when are completion fields.
> Design, Approach, Grounding and Risks are working material. Execution evidence
> belongs in `notes/verification-ledger.md`, not in this plan.

## Approach

Move first, register second, prove third. T1 moves both packs into `packs/platform-engineering/` with `git mv`, merges the manifests and adds the rename entries, so every later task works against the final layout. T2 and T3 update the surfaces that name the old packs, split by kind: CI, roster and route gates with their coupled guide, then guides, site and prose. T4 adds the core-absent, end-to-end and recovery journeys, and only then T5 removes the dependencies. T6 records packaging. T7 and T8 are controller-run proofs against the real CLI, a real Terraform provider and the live GitHub fixture, because a sandboxed worker has no network and CI cannot reach the old commit.

## Constraints

- RFC-0118 settles the decisions; this plan changes none of them.
- [ADR-0071](../../adr/0071-pack-runtime-export-boundary-and-test-placement.md) governs runtime exports and test placement; [ADR-0101](../../adr/0101-pack-test-isolation-by-default-with-declared-compatibility-classes.md) governs isolated pytest processes.
- No installer change, no dependency, no change to core or its hooks. Frozen records stay as written.
- The pinned old ref is `42849d1e7`, the merge of the last change to both old packs.

## Construction tests

**Integration tests:** the moved pack suites; a new end-to-end journey in `packs/platform-engineering/tests/` that builds a plan bundle and a release candidate in one isolated root.

**Manual verification:** T7 (migration against the real CLI) and T8 (live Terraform provider and the GitHub fixture), recorded in the ledger.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Pack and rename map | T1, T5 | Catalogue lint, verify, rename lint, moved suites | Old directories absent |
| Registrations | T2, T3 | Roster, parity, census, guide and site checks | Search finds no live old name |
| Journeys | T4 | Isolated-root runs | Ledger transcript |
| Release history | T6 | Fragment validation, version parity | 1.0.0 recorded |
| Migration and live proof | T7, T8 | Commands, state rows, run ids | Ledger entries |

## Design (LLD)

### Pack layout

Owned by: T1

`packs/platform-engineering/` keeps the union of both `.apm/` trees: `skills/{generate-iac,reconcile-iac,define-slo,prepare-release-handoff,release-loop}`, `agents/{release-lead,release-reliability-reviewer,release-security-reviewer}.md`, and `tests/skills/{generate-iac,prepare-release-handoff,release-loop}`. `pack.toml` merges both packs' metadata into one, version 1.0.0, repo scope, no required dependency. README and JOURNEY are rewritten as one pack's text with a migration section that links the how-to.

### Surface update rule

Owned by: T2, T3

A live surface names the new pack: navigation, rosters, CI lists, prose that tells an adopter what to install, and other packs' shipped content. A frozen record keeps the old name: accepted RFCs and ADRs, shipped specs and their notes, released changelog entries, and the rename fixtures under `packages/agentbundle/tests/`.

## Tasks

Pack suites always run one skill directory per pytest process (ADR-0101): `python3 -m pytest packs/platform-engineering/tests/skills/generate-iac -q`, `python3 -m pytest packs/platform-engineering/tests/skills/prepare-release-handoff -q` and `python3 -m pytest packs/platform-engineering/tests/skills/release-loop -q`.

### T1: Create the platform-engineering pack from both packs

**Depends on:** none

**Verification mode:** goal-based check.

**Touches:** `packs/platform-engineering/**`, `packs/iac-terraform/**` (removed), `packs/release-engineering/**` (removed), `contracts/renames/pack-renames.toml`, `packs/core/JOURNEY.md` and `packs/core/README.md` (documentation only), `web/src/content/journeys/` (regenerated from the pack journeys by `tools/build-site.py`), generated self-host projections

**Tests:**
- Every moved file is byte-identical to its source at `42849d1e7` except the manifest, README, JOURNEY and path fixes this task names (AC-0001); old directories gone and rename lint passes (AC-0002); catalogue lint and verify (AC-0004); each moved suite passes from the new path (AC-0005 suite half); eval harnesses pass (AC-0026); the generated journey pages match their pack sources, and core's journey and README name the new pack (AC-0010 journey half, AC-0011 core half). The merged `pack.toml` keeps both old packs' required dependencies for now; T5 removes them.

**Done when:** `agentbundle catalogue lint --root . --deep`, `agentbundle catalogue verify --root .`, `tools/lint-pack-renames.py` and the three per-suite commands pass.

### T2: CI, roster, census and route registrations

**Depends on:** T1

**Verification mode:** goal-based check.

**Touches:** `Makefile`, `.github/workflows/build-check.yml`, `.github/workflows/iac-release-loop-canary.yml`, `.github/workflows/iac-staleness.yml`, `tools/lint-ci-parity.py`, `tools/test_local_ci_shared_test_deduplication.py`, `tools/fixtures/build-check-good.yml`, `tools/test-build-check-workflow.py`, `tools/lint-plugin-roster.py`, `tools/lint-plugin-route-docs.py`, `guides/_shared/how-to/install-packs.md`, `packs/agent-skill-engineering/tests/fixtures/skill-census.json`, `packages/agentbundle/tests/build_pipeline/test_agent_plugin_projection.py`, `tests/roster/test_registry_upgrade_notes.py`, `tests/roster/test_repo_governance_rename_completeness.py` (pointed at `platform-engineering`, which still requires `repo-governance` until T5), `tests/roster/test_architecture_decision_surface_portability.py`, other `tools/` tests that pin the old names

**Tests:**
- CI lists and parity (AC-0005); plugin rosters, route docs and the agent-plugin outcome (AC-0006); census and roster pins (AC-0007); the two pack workflows point at moved paths (AC-0011 workflow half).

**Done when:** the named lints and tests pass, plus `pytest tests/roster -q` apart from recorded pre-existing failures.

### T3: Guides, site, docs-site and prose

**Depends on:** T2

**Verification mode:** goal-based check.

**Touches:** `guides/platform-engineering/**` (from both old guide trees), `guides/iac-terraform/**` and `guides/release-engineering/**` (removed), `guides/README.md`, every other live guide (outside frozen records) that names the packs or links into the old guide trees, found by searching for both names and both guide paths, `guide-nav-baseline.toml`, `site.toml`, `web/src/content/packs/`, `web/src/lib/catalogue-navigation.ts`, `web/src/pages/catalogue/index.astro`, `web/src/pages/journeys/index.astro`, `web/src/test/**` pins, `docs-site/astro.config.ts`, `docs-site/src/**` pins, `README.md`, `governance/manifest.example.yaml`, `docs/architecture/lifecycle-flow.md`, `docs/architecture/loop-infrastructure.md`, `docs/product/journeys/engineer-provisions-infrastructure.md`, `docs/product/journeys/README.md`, and every other live document under `docs/architecture/` or `docs/product/journeys/` that the AC-0012 search finds, `tools/render-lifecycle-graphics.py` and the shared guide graphics it generates, `tools/test_build_site_*.py` and other tools tests that pin guide paths

**Tests:**
- Guide tree, titles and navigation baseline (AC-0008); migration how-to and README link (AC-0009); site and docs-site names and builds (AC-0010); live docs and examples, no change to core's `.apm/`, `seeds/` or manifests and none under `packs/repo-governance/`, and regenerated lifecycle graphics naming the new pack (AC-0011); the AC-0012 search.

**Done when:** `tools/validate_guides.py`, `tools/check-guide-index.py`, `tools/lint-guide-titles.py`, `tools/build-site.py`, the site's test suite, a re-run of `tools/render-lifecycle-graphics.py` with no diff, and the AC-0012 search pass.

### T4: Core-absent, end-to-end and recovery journeys

**Depends on:** T1

**Verification mode:** integration.

**Touches:** `packs/platform-engineering/tests/**`

**Tests:**
- Terraform-only suites from the new path (AC-0013 suite half); release-only journeys with no Terraform tooling (AC-0014); a new end-to-end journey from a `generate-iac` plan bundle to final stage, plus a failed post-deploy check's repair handoff and an interrupted run's `pause` (AC-0015); core-installed results unchanged and the optional-core tests pass (AC-0016).

**Done when:** the three per-suite commands pass in isolated roots.

### T5: Remove the required dependencies

**Depends on:** T4

**Verification mode:** goal-based check.

**Touches:** `packs/platform-engineering/pack.toml`, `packs/platform-engineering/.claude-plugin/plugin.json`, `tests/roster/test_repo_governance_rename_completeness.py` (its Terraform pin now asserts no required dependency and no retired name)

**Tests:**
- No `[[pack.dependencies.required]]`, version 1.0.0 in both manifests, repo scope (AC-0003); the rename-completeness roster test updated for the removed dependency (AC-0007); `agentbundle install --pack platform-engineering` into an isolated Git repository with no other pack succeeds (AC-0013 install half).

**Done when:** that install exits 0 and catalogue lint and verify still pass.

### T6: Changelog, version and gates

**Depends on:** T3, T5

**Verification mode:** goal-based check.

**Touches:** `docs/product/changelog.d/`, generated projections and journey pages the self-host writes

**Tests:**
- A fragment for `platform-engineering` 1.0.0 (removals and migration), validated (AC-0025); `make build-self` zero diff, lint pair, precheck, roster and boundary lint (AC-0027).

**Done when:** every command in AC-0027 exits 0.

### T7: Migration proof against the real CLI

**Depends on:** T6

**Verification mode:** visual / manual QA. Controller-executed: the old commit is outside CI's shallow clone.

**Touches:** `docs/specs/platform-engineering-consolidation/notes/verification-ledger.md` (a controller commit between attempts)

**Tests:**
- Happy path, edits, duplicate activation, mixed scope and retry, rollback and hint (AC-0017, AC-0018, AC-0019, AC-0020, AC-0021), each in a fresh isolated Git repository with the old catalogue at `42849d1e7` and the current catalogue.

**Done when:** the ledger records each case's commands, state rows and file listings.

### T8: Live Terraform and GitHub fixture runs

**Depends on:** T7

**Verification mode:** visual / manual QA against a real provider, the GitHub.com fixture and the AWS sandbox. Controller-executed.

**Touches:** `docs/specs/platform-engineering-consolidation/notes/verification-ledger.md` (a controller commit between attempts); outside this repository, the scratch fixture repository's workflows and vendored skill

**Tests:**
- Live provider schema and saved plan (AC-0022); release-only approved deploy from the new pack (AC-0023); end-to-end approved deploy with the plan bundle admitted, after the fixture's prepare and archive-allowlist adaptations (AC-0024).

**Done when:** the ledger records run ids and outcomes with cloud identifiers as placeholders.

### T9: Review and acceptance repairs

**Depends on:** T8

**Verification mode:** goal-based check.

**Touches:** `packs/platform-engineering/pack.toml`, `packs/platform-engineering/README.md`, `packs/platform-engineering/tests/skills/release-loop/`, `docs/knowledge/topics/a-pack-version-bump-is-three-files-build-self-syncs-none-of-them.json`, generated projections the self-host writes

**Tests:**
- `kiro-cli` is an allowed adapter again, as it was for `iac-terraform`, and `agentbundle install --pack platform-engineering --adapter kiro-cli --scope repo` into an isolated Git repository succeeds (adv-1; AC-0013, AC-0017).
- The pack README describes core and repo-governance as optional integrations, never as retained dependencies (adv-2; AC-0003).
- The README's rollback tells the adopter to merge and delete each `.upstream` companion before reinstalling the old packs, matching the migration how-to (qe-1; AC-0021).
- The knowledge topic's synthesis counts and names the current packs, with `platform-engineering` in place of both retired names, and `tools/lint-knowledge-freshness.py` passes (AC-0012).
- A release-only journey variant runs with core's projected files installed beside the platform skills and gives the same stage results as the core-absent journey (AC-0016).

**Done when:** catalogue lint and verify, the three pack suites, the knowledge-freshness lint and the lint pair pass.

### T10: Published migration link

**Depends on:** T9

**Verification mode:** goal-based check.

**Touches:** `packs/platform-engineering/JOURNEY.md`, `web/src/content/journeys/platform-engineering.md` (regenerated by `tools/build-site.py --journeys-only`)

**Tests:**
- The journey's migration link uses the published guide path, as core's journey does, and resolves in the site build (adv-3; AC-0010).

**Done when:** the journey lints, the journey editorial test and the site build pass, and the built journey page's migration link names an existing page.

## Risks

- A moved test may resolve paths through its pack directory name; T1's suite run finds it.
- The live end-to-end run needs the plan bundle inside the fixture candidate; the fixture's prepare workflow gains a fixture-only step for it.

## Changelog

- 2026-11-22: drafted.
- 2026-11-22: spec approved by eugenelim (scope)
- 2026-11-22: plan approved by eugenelim (build strategy)
- 2026-11-22: amendment drafted: the spec's Agent Rules carry the gate declaration the supervisor runs.
- 2026-11-22: amendment approved by eugenelim (scope)
- 2026-11-22: amendment approved by eugenelim (build strategy)
- 2026-11-22: amendment drafted: `governance/manifest.example.yaml` is a self-hosted copy of the unchanged repo-governance seed, so AC-0011 no longer lists it and AC-0012 classifies it with that source.
- 2026-11-22: amendment approved by eugenelim (scope)
- 2026-11-22: amendment approved by eugenelim (build strategy)
