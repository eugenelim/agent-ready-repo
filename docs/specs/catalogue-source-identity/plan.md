# Plan: Catalogue source identity

- **Spec:** [`spec.md`](spec.md)
- **Status:** Executing

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as implementation evidence develops.

## Approach

First pin the adapter-neutral marker contract in source-resolution tests and
replace only the local marker predicate. Then pin lint/verify behavior with an
adapter matrix, expose the existing self-host Claude-artifact decision as a
shared predicate, and make lint/verify consume it. Finally update the package
version, changelog, frozen-decision errata, and current documentation. The
implementation preserves source precedence, explicit-source handling, archive
layout, and internal fallback callers outside lint/verify.

## Constraints

- RFC-0085 defines the breaking source identity and release increment.
- RFC-0046 and ADR-0036 continue to govern source precedence and the
  repository-bounded editable walk; only their marker text changes by erratum.
- Package changes require synchronized `version.py` and `pyproject.toml` values
  plus an `Engine-Change-RFC:` commit footer.
- Production code remains standard-library-only and Windows-clean.
- The workspace shell cannot create temporary files; tests requiring
  `tmp_path` need the user's writable runner for final confirmation.

## Construction tests

**Integration tests:** Existing editable-source detection tests continue to
exercise the real PEP 610 metadata path; focused source-default and CLI suites
cover the cross-module contract.

**Manual verification:** Invoke the real `agentbundle catalogue lint` command
against the repository source root and record exit/output. Negative Kiro-only
and missing-marker cases run through pytest on a writable runner.

## Design (LLD)

### Design decisions

- Keep the literal identity predicate in `source_defaults.py`; change its file
  marker from the Claude marketplace to `catalogue.toml` without touching the
  enclosing walk or precedence composer. Traces to AC1–AC3.
- Add a public, pure `projects_claude_artifacts(preferred_adapter)` predicate
  beside the existing effective-adapter calculation in `build/self_host.py`.
  It has two callers—self-host and lint—and creates no new module. Traces to
  AC6–AC9.
- Enforce missing configuration at the `lint_catalogue` boundary rather than
  globally changing `load_catalogue_config`; verify delegates to lint even when
  config is absent. Traces to AC4 and AC10.

### Component / module decomposition

- `source_defaults.py`: local catalogue identity only.
- `build/self_host.py`: authoritative effective-adapter and Claude-artifact
  predicate.
- `catalogue_tooling/lint.py`: source marker and conditional marketplace
  diagnostics.
- `catalogue_tooling/verify.py`: unconditional lint step at the source-checkout
  boundary.
- `catalogue_tooling/archive.py`: archive-native validation only; installable
  archives remain distinct from source checkouts and may omit `catalogue.toml`.
- Existing unit/integration test modules own regression coverage; no new test
  root or fixture tree is introduced.

### State & control flow

1. Source discovery checks root `catalogue.toml` plus root `packs/`.
2. Lint loads and validates `catalogue.toml`; absence returns one `CAT-L002`.
3. Lint requires root `packs/`, then separately uses configured pack paths for
   pack content rules.
4. Lint asks the shared predicate whether a missing marketplace is an error.
5. Verify always invokes lint before later config-dependent steps.

### Behavior & rules

- Invalid present config remains `CAT-L001`; absent config becomes `CAT-L002`.
- Missing literal root `packs/` is `CAT-L002` regardless of custom configured
  packs.
- Marketplace presence is required if and only if Claude belongs to the
  effective self-host adapter set.
- A present marketplace continues through existing verify validation.
- Installable archives continue through their manifest, digest, path-safety,
  marker, and compatibility checks without being reclassified as source
  catalogues after extraction.
- Tar-member confinement uses POSIX archive semantics on every host, rejects
  Windows separators, and verifies the resolved extraction destination stays
  inside its root before any write.

### Failure, edge cases & resilience

- Missing config returns early from lint to avoid duplicate marker errors.
- A custom configured packs directory cannot satisfy the literal root marker;
  once identity passes, missing configured content remains visible.
- Recipe read/parse failure retains the existing default self-host allow-list,
  so lint and projection fail closed together on the Claude requirement.

### Quality attributes (NFRs)

- One predicate prevents drift between generation and validation.
- No network, filesystem writes, or dependency changes are added to runtime
  validation.
- Diagnostics remain deterministic and machine-readable.

## Tasks

### T1: Adapter-neutral source roots resolve and legacy marker-only roots do not

**Depends on:** none

**Touches:** packages/agentbundle/agentbundle/source_defaults.py, packages/agentbundle/tests/unit/test_source_defaults.py, packages/agentbundle/tests/integration/test_editable_source_detection.py

**Mode:** TDD

**Tests:**

- `stub: true` —
  `packages/agentbundle/tests/unit/test_source_defaults.py::test_scheme_gate_accepts_catalogue_toml_and_packs_without_marketplace`
  (AC1).
- `stub: true` —
  `packages/agentbundle/tests/unit/test_source_defaults.py::test_scheme_gate_rejects_legacy_packs_and_marketplace_without_catalogue_toml`
  (AC2).
- `stub: true` —
  `packages/agentbundle/tests/unit/test_source_defaults.py::test_editable_symlink_loop_defers_without_exception`
  (AC15).
- Update marker helpers to create `catalogue.toml + packs/`; confirm configured
  local paths and editable discovery succeed (AC1, AC3).
- Add a marketplace-only legacy-root regression that fails source validation
  and editable discovery (AC2).
- Retain repository-boundary and five-layer precedence tests unchanged (AC3).
- Retain canonicalized-symlink and above-Git-root regressions, and make a
  circular editable path defer diagnostically rather than escape or raise
  (AC15).

**Approach:**

- Replace `_MARKER_FILE` and its documentation with root `catalogue.toml`.
- Leave canonicalization, walk bounds, precedence, and explicit-source branches
  untouched.

**Done when:** Focused source-default and editable-detection tests pass.

### T2: Lint and verify share self-host's adapter-aware marketplace contract

**Depends on:** T1

**Touches:** packages/agentbundle/agentbundle/build/self_host.py, packages/agentbundle/agentbundle/catalogue_tooling/lint.py, packages/agentbundle/agentbundle/catalogue_tooling/verify.py, packages/agentbundle/agentbundle/catalogue_tooling/archive.py, packages/agentbundle/agentbundle/https_catalogue.py, packages/agentbundle/tests/unit/test_catalogue_tooling_lint.py, packages/agentbundle/tests/unit/test_catalogue_tooling_verify.py, packages/agentbundle/tests/unit/test_catalogue_tooling_self_host.py, packages/agentbundle/tests/unit/test_catalogue_tooling_archive.py, packages/agentbundle/tests/unit/test_catalogue_tooling_package.py, packages/agentbundle/tests/unit/test_https_catalogue.py, packages/agentbundle/tests/unit/test_package_catalogue.py, packages/agentbundle/tests/unit/test_catalogue_wave2_validation.py, packages/agentbundle/tests/build_pipeline/test_self_host_check.py, packages/agentbundle/tests/integration/test_install_default_source.py, packages/agentbundle/tests/integration/test_show_cmd.py, packages/agentbundle/tests/fixtures/blank_catalogue/catalogue.toml

**Mode:** TDD

**Tests:**

- `stub: true` —
  `packages/agentbundle/tests/unit/test_catalogue_tooling_lint.py::test_no_catalogue_toml`
  (AC4).
- `stub: true` —
  `packages/agentbundle/tests/unit/test_catalogue_tooling_lint.py::test_kiro_only_catalogue_does_not_require_claude_marketplace`
  (AC7).
- `stub: true` —
  `packages/agentbundle/tests/unit/test_catalogue_tooling_lint.py::test_literal_root_packs_and_configured_packs_are_checked_separately`
  (AC5).
- `stub: true` —
  `packages/agentbundle/tests/unit/test_catalogue_tooling_lint.py::test_claude_marketplace_requirement_uses_shared_projection_predicate`
  (AC6, AC9).
- `stub: true` —
  `packages/agentbundle/tests/unit/test_catalogue_tooling_self_host.py::test_projects_claude_artifacts_for_default_and_allowed_adapters`
  (AC8, AC9).
- `stub: true` —
  `packages/agentbundle/tests/unit/test_catalogue_tooling_lint.py::test_allowed_adapter_requires_claude_marketplace`
  (AC8; real-config lint boundary for already-allowed `codex`; default `None`
  remains covered at the shared self-host predicate boundary because the
  published config schema requires `preferred-adapter`).
- `stub: true` —
  `packages/agentbundle/tests/unit/test_catalogue_tooling_self_host.py::test_run_self_host_claude_artifacts_follow_shared_predicate`
  (AC9; patched false/true predicate controls both Claude generation calls).
- `stub: true` —
  `packages/agentbundle/tests/unit/test_catalogue_tooling_verify.py::test_verify_empty_dir_reports_missing_catalogue`
  (AC10).
- `stub: true` —
  `packages/agentbundle/tests/unit/test_catalogue_tooling_verify.py::test_verify_non_catalogue_with_agents_file_reports_missing_catalogue`
  and
  `packages/agentbundle/tests/unit/test_catalogue_tooling_verify.py::test_cli_verify_format_json`
  (AC10; remove the remaining config-less-success expectations from the unit
  and CLI surfaces).
- `stub: true` —
  `packages/agentbundle/tests/unit/test_catalogue_tooling_verify.py::test_step_plugin_manifests_marketplace_with_hooks`
  (AC11; preservation test for the established manifest-validation step).
- `stub: true` —
  `packages/agentbundle/tests/unit/test_catalogue_tooling_archive.py::test_archive_valid_passes_all`
  and
  `packages/agentbundle/tests/unit/test_catalogue_tooling_archive.py::test_archive_malformed_marketplace_fails_archive_semantics`
  and
  `packages/agentbundle/tests/unit/test_catalogue_tooling_archive.py::test_archive_invalid_marketplace_entry_fails_schema`
  and
  `packages/agentbundle/tests/unit/test_catalogue_tooling_package.py::test_packaged_archive_passes_archive_verification_without_source_config`
  (AC11; installable archives remain valid without the source-only marker and
  retain marketplace semantic validation).
- `stub: true` —
  `packages/agentbundle/tests/unit/test_catalogue_tooling_lint.py::test_configured_packs_symlink_escape_is_not_inspected`
  and
  `packages/agentbundle/tests/unit/test_catalogue_tooling_lint.py::test_configured_packs_symlink_loop_is_diagnostic`
  (AC15).
- `stub: true` —
  `packages/agentbundle/tests/unit/test_catalogue_tooling_verify.py::test_verify_invalid_config_path_reports_diagnostic`
  (AC15; invalid config remains inside verify's structured result contract).
- Convert shared lint fixtures to valid modern catalogues and invert the
  missing-config regression to one `CAT-L002` (AC4).
- Add literal-root-packs versus configured-packs coverage (AC5).
- Add Claude, Kiro-only, default, and already-allowed preferred-adapter cases
  for missing marketplace behavior (AC6–AC9).
- Add verify coverage proving missing config reports `CAT-V-002` and present
  marketplace validation remains active (AC10–AC11).
- Keep self-host effective-adapter projection tests green against the shared
  predicate (AC9).
- Modernize valid local-source fixtures to carry both identity markers, while
  retaining config-less roots only in explicit negative tests (AC1, AC4).

**Approach:**

- Add `projects_claude_artifacts()` beside `_effective_adapters()` and replace
  self-host's local boolean expression.
- Make lint return one missing-config diagnostic before catalogue rules.
- Make marker rules check literal root `packs/`, separately diagnose a missing
  custom configured packs directory, and gate marketplace absence on the shared
  predicate.
- Resolve configured operational paths once before catalogue content rules;
  preserve the configuration loader's `CAT-L001` as the earliest failure for
  symlink escape or circular resolution, retain `CAT-L021` as defense in depth
  if a loaded path becomes unsafe, and never inspect content through either.
- Remove verify's config-absence lint skip.
- Remove the source-verifier round-trip from `verify_archive`; archive-native
  checks own installable artifacts, which intentionally omit `catalogue.toml`,
  while a shared entry validator preserves marketplace semantics.
- Share tar-member destination confinement between archive verification and
  HTTPS extraction; reject backslash traversal and resolved-prefix escape on
  every platform.

**Done when:** Focused lint, verify, and self-host tests pass with the full
adapter matrix.

### T3: Published governance, documentation, and release surfaces agree

**Depends on:** T2

**Touches:** packages/agentbundle/agentbundle/version.py, packages/agentbundle/pyproject.toml, packages/agentbundle/CHANGELOG.md, packages/agentbundle/README-pypi.md, docs/rfc/0046-convenient-install-defaults.md, docs/adr/0036-install-source-resolves-through-trusted-precedence-chain-no-repo-source-no-cwd.md, docs/guides/**, docs/architecture/**, guides/**

**Mode:** Goal-based check

**Tests:**

- No stub (goal-based):
  `.venv/bin/python -c 'import tomllib; from pathlib import Path; from agentbundle import __version__; data = tomllib.loads(Path("packages/agentbundle/pyproject.toml").read_text(encoding="utf-8")); assert __version__ == data["project"]["version"] == "0.33.0"'`
  exits 0, proving the exact version fields agree (AC12).
- No stub (goal-based):
  `rg -n 'marketplace\.json' docs/architecture docs/guides guides` emits the
  complete reviewed allow-list of maintained documentation references. Every
  match must describe one of: a conditional Claude projection, marketplace
  format/aggregation, an archive that deliberately contains the artifact, or
  an operational flow that consumes an existing artifact. No match may call
  marketplace catalogue identity or an unconditional lint prerequisite.
  Frozen RFC/ADR bodies are checked separately through their appended errata
  (AC13).
- No stub (goal-based): `pyproject.toml` names `README-pypi.md` as the package
  readme, and that long description states the two source-root markers plus
  the adapter-conditional Claude marketplace rule (AC13).
- No stub (goal-based):
  `python3 .agents/skills/work-loop/scripts/lint-spec-status.py` exits 0 and
  `git diff --check` exits 0 (AC13–AC14).
- No stub (goal-based): `make lint-ruff` and `make lint-mypy` each exit 0
  (AC14).
- Manual CLI QA:
  `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m agentbundle catalogue lint --root . --format json`
  exits 0 and emits no `CAT-L001` or `CAT-L002` diagnostic (AC4–AC9).

**Approach:**

- Bump both version sources and add the breaking migration changelog entry.
- Append approver-signed errata to RFC-0046 and ADR-0036.
- Update current reference and architecture text only where it defines source
  identity or claims marketplace is unconditionally required by lint; do not
  rewrite frozen historical bodies.
- Update the PyPI long description at its `pyproject.toml`-selected source so
  custom-catalogue maintainers see the same source identity and conditional
  marketplace contract before installing 0.33.0.

**Done when:** Version, documentation, diff-hygiene, and repository policy
checks pass.

### T4: Close the initiative only after 0.33.0 is public

**Depends on:** T3 and confirmed publication of `agentbundle` 0.33.0 to PyPI

**Touches:** docs/specs/catalogue-source-identity/spec.md, docs/specs/catalogue-source-identity/plan.md, docs/specs/README.md, workspace.toml

**Mode:** Goal-based check; post-publication follow-on, excluded from the
implementation/version-bump PR

**Tests:**

- No stub (goal-based): `python3 -m pip index versions agentbundle` exits 0 and
  lists 0.33.0; then
  `python3 .agents/skills/work-loop/scripts/lint-spec-status.py` exits 0 after
  the lifecycle edits.

**Approach:**

- After publication, mark the spec `Shipped` and plan `Done`, update the specs
  index, and remove `spec/catalogue-source-identity` from the workspace queue.
- Do not perform these lifecycle edits in the version-bump PR; the package
  closeout rule requires a separate post-PyPI step.

**Done when:** PyPI confirms 0.33.0 and the lifecycle/queue closeout is merged.

## Rollout

The implementation ships in one `agentbundle` 0.33.0 release. Its PR leaves
the spec `Implementing`, plan `Executing`, and queue entry active until the
post-PyPI T4 follow-on. Rollback is a package revert to 0.32.x; no data
migration or irreversible state change occurs. Catalogue maintainers migrate
before upgrading by adding a valid root `catalogue.toml` and literal root
`packs/` directory.

## Risks

- The version bump may conflict with another queued `agentbundle` release;
  serialize before merge and renumber if main advances first.
- Converting the lint fixture helper could hide a dedicated missing-config
  case; retain one explicit negative test outside the helper.
- Importing the shared self-host predicate into lint could expose a cycle;
  verify imports before implementation and keep the helper in the existing
  acyclic build module.
- Full pytest and CLI negative-path QA require a writable temporary directory
  unavailable to this agent session.

## Changelog

- 2026-08-11: Initial plan derived from accepted RFC-0085.
- 2026-08-11: Added executable red stubs, exact goal checks, and the required
  post-PyPI closeout task after pre-execution review.
- 2026-08-11: Expanded T2 construction coverage to every adapter/lint/verify
  criterion, included shipped `guides/`, and made version, CLI, and publication
  checks exact after the second pre-execution review.
- 2026-08-11: Pinned both shared-predicate consumers with false/true overrides
  and added exact Ruff/mypy gates after the third pre-execution review.
- 2026-08-11: Added the known stale architecture/how-to claims to T3 and
  removed remaining config-less verify success expectations after the fourth
  pre-execution review.
- 2026-08-11: Replaced the phrase-sensitive doc search with a complete reviewed
  marketplace-reference allow-list and added default/allowed lint-boundary
  coverage after the fifth pre-execution review.
- 2026-08-11: Added AC15 and construction tests for canonicalized confinement,
  symlink escape, and circular-path failure after secure-design review.
- 2026-08-11: Preserved config-less installable archives through archive-native
  verification, modernized legacy valid-source fixtures, and documented the
  source/archive boundary after implementation review.
- 2026-08-11: Added cross-platform tar destination confinement and structured
  verify config-error handling after implementation security review.
- 2026-08-11: Recorded green writable-runner evidence: the final 327-test
  focused suite passed after an earlier whole-unit run reached 1,974 passes;
  adversarial, quality, and security implementation reviews were clean.
- 2026-08-11: Added the `pyproject.toml`-selected PyPI long description to T3
  so the 0.33.0 package page carries the source-identity migration contract.
