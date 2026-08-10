# Plan: catalogue verify classification

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done

## Approach

Keep RFC-0002's two-part implementation model: dynamically enumerate every
Projected target and use `EXCLUDED_PATTERNS` for repository-owned Source,
Manual, and Excluded paths. Extend the dynamic set with the two special
projection rails that run outside the adapter shadow, run their existing drift
checks during every self-host dry-run, and broaden exclusions only at stable
ownership boundaries. Pin the behavior with focused tests and the repository's
real verifier command.

## Constraints

- RFC-0002 owns self-host path categories and keeps unclassified output
  informational.
- RFC-0013 and the shipped credbroker-user-scope spec define the
  `.agentbundle/{bin,lib}` projections and their drift gates.
- The existing `catalogue-verifier-correctness` spec remains queued; this plan
  does not implement or close its unrelated acceptance criteria.
- Base freshness is an explicitly approved skip for this execution.

## Construction tests

**Integration tests:** Run self-host against a real Git worktree fixture, assert
special targets produce no unclassified notices, then mutate a special target
and assert non-zero drift.

**Manual verification:** None; the CLI goal check captures both stderr and exit
status.

## Design (LLD)

### Design decisions

- A private `_self_host_projection_paths` helper composes existing projection
  enumerators; it does not duplicate target filenames. Traces to AC3.
- A private `_self_host_projection_drifts` helper composes existing drift
  checkers so dry-run and build-check share the same truth. Traces to AC4.
- Stable repository-owned directories use subtree exclusions; isolated root
  files use exact anchored entries. Traces to AC1 and AC2.

### Dependencies & integration

The implementation reuses `adapter_root_bins.compute_projections`,
`user_libs.compute_projections`, and their existing `check_drift` functions.
No external dependency or interface contract is introduced.

### Failure, edge cases & resilience

Projection targets outside the requested working tree are ignored for that
tree's classification. Projection enumeration errors keep the existing
fail-closed self-host behavior. Git enumeration failure remains a warning, not
a false claim of complete classification.

## Tasks

### T1: Classification policy accounts for repository-owned paths

**Depends on:** none

**Touches:** `packages/agentbundle/agentbundle/build/self_host.py`, `packages/agentbundle/tests/build_pipeline/test_self_host_check.py`

**Tests:**
- TDD stub `ExcludedGlobTests.test_repository_owned_boundaries_are_excluded`:
  each new subtree/root ownership entry is excluded (AC1).
- Existing TDD `InfoLineUnclassifiedTests.test_unclassified_path_surfaces_as_info_without_failing`:
  `stray-note.md` remains unclassified and informational (AC2).
- TDD stub `InfoLineUnclassifiedTests.test_git_filenames_are_nul_delimited_and_lossless`:
  whitespace/newline filenames retain their exact identity (AC6).
- TDD stub `InfoLineUnclassifiedTests.test_git_enumeration_failure_warns_without_failing`:
  a non-zero Git result warns rather than implying completeness (AC7).

**Approach:**
- Add the stable docs-site, web, packages, profiles, documentation, and root
  configuration ownership boundaries to `EXCLUDED_PATTERNS`.
- Update the on-disk exclusion control path so it remains genuinely unknown.

**Done when:** focused exclusion and unclassified tests pass.

### T2: Special self-host projections participate in classification and dry-run drift

**Depends on:** T1

**Touches:** `packages/agentbundle/agentbundle/build/self_host.py`, `packages/agentbundle/agentbundle/build/adapter_root_bins.py`, `packages/agentbundle/agentbundle/build/user_libs.py`, `packages/agentbundle/agentbundle/build/projection_io.py`, `packages/agentbundle/tests/build_pipeline/test_self_host_check.py`, `packages/agentbundle/tests/build_pipeline/test_adapter_root_bins_projection.py`, `packages/agentbundle/tests/build_pipeline/test_user_libs_projection.py`, `packages/agentbundle/tests/integration/test_build_check_drift_gates.py`, `packages/agentbundle/tests/unit/test_catalogue_tooling_verify.py`

**Tests:**
- TDD stub `SpecialProjectionClassificationTests.test_special_targets_come_from_projection_enumerators`:
  special targets are present in the dynamically derived Projected set (AC3).
- TDD stub `SpecialProjectionClassificationTests.test_special_target_drift_fails_self_host_dry_run`:
  special-target drift fails `run_self_host(dry_run=True)` and names the target
  (AC4).
- TDD stubs `AdapterRootBinsTests.test_check_drift_rejects_symlink_target` and
  `test_check_drift_rejects_posix_mode_drift`: executable projections are
  lstat/type/mode checked without following outside-root symlinks (AC5).
- TDD stubs `UserLibsProjectionTests.test_check_drift_rejects_symlink_target`
  and `test_check_drift_rejects_mode_drift`: user-lib projections are also
  lstat/type/mode checked against their package sources (AC5).
- Remediation regressions replace leaf/root symlinks without modifying their
  referents, a nested projected parent is checked and repaired no-follow, and a
  dangling symlink orphan remains visible. A concurrent leaf-link swap is
  defeated by held-directory atomic replacement (AC4, AC5).
- TDD stub `InfoLineUnclassifiedTests.test_unclassified_symlink_surfaces_as_info`:
  symlink type does not hide an otherwise unknown path (AC2).
- TDD stub `test_step_selfhost_drift_maps_special_projection_failure_to_cat_v_015`:
  verifier step 15 maps a failed self-host check to `CAT-V-015` (AC4).
- Regression: direct build-check drift-gate callers retain existing behavior.

**Approach:**
- Compose projection paths and drift results from the existing special-rail
  enumerators/checkers.
- Include paths during info classification and drift results during dry-run.
- Parse `git ls-files -z` without stripping filenames and preserve the existing
  non-failing warning on enumeration failure.
- Tighten adapter-root-bin drift to use `lstat`, refuse target symlinks, and
  compare POSIX executable mode.
- Avoid duplicate special-gate diagnostics in the combined build-check path.

**Done when:** focused self-host and drift-gate tests pass.

### T3: Ownership documentation, release metadata, and repository ratchet are complete

**Depends on:** T2

**Touches:** `docs/rfc/0002-self-hosting.md`, `docs/specs/self-hosting/spec.md`, `packs/core/seeds/docs/CONVENTIONS.md`, `docs/CONVENTIONS.md`, `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `packages/agentbundle/pyproject.toml`, `packages/agentbundle/agentbundle/version.py`, `packages/agentbundle/CHANGELOG.md`, `packages/agentbundle/README-pypi.md`, `docs/product/changelog.md`, `docs/specs/README.md`, `workspace.toml`

**Tests:**
- Goal-based: `agentbundle catalogue verify --root .` exits zero and emits no
  unclassified line (AC1, AC8).
- Goal-based: version pins agree and changelogs name the fix (AC9).
- Goal-based: the PyPI long-description source documents the verifier's
  classification, failure, and repair boundaries and its links resolve (AC9).
- Goal-based: `make build-self` keeps the conventions seed/projection pair in
  sync and regenerates marketplace metadata (AC8, AC9).

**Approach:**
- Append an RFC-0002 amendment and reconcile the living ownership docs with the
  two later special projection rails; do not rewrite frozen RFC history.
- Bump AgentBundle by one patch release and record the correction.
- Update the AgentBundle PyPI landing page from the canonical CLI and self-host
  behavior; leave Credbroker's page unchanged because its library contract and
  version do not change.
- Bump core `2.5.1` to `2.5.2` in both manifests and regenerate the marketplace.
- Add this focused spec to the active spec index without moving the broader
  verifier-correctness queue item; track it as the current ini-007 active work.

**Done when:** the repository verifier has zero unclassified output and release
metadata is internally consistent.

### T4: Full gates and specialist reviews are clean

**Depends on:** T3

**Tests:**
- `python3 -m pytest packages/agentbundle/tests/ -q` (AC10).
- `SKIP_SAST=1 make build-check` (AC10).
- Adversarial, security, and quality review report no unresolved blocker or
  major finding.

**Approach:**
- Run targeted tests first, then package and repository gates.
- Resolve review findings within this spec's boundaries and rerun affected
  gates.

**Done when:** all available gates and required reviews are clean; any
environmental limitation is recorded with the exact user-runnable command.

## Rollout

Ship as AgentBundle 0.30.1 and core 2.5.2. No migration or infrastructure change is required;
rollback is the code/doc revert. The classifier remains informational for
unknown paths.

## Risks

- An exclusion boundary that is too broad can hide a future projected path;
  mitigated by keeping `.agentbundle/**` dynamic and preserving the unknown-path
  regression.
- Running special checks from both self-host and build-check can duplicate
  diagnostics; the combined command must select one owner for those messages.
- The real-repository ratchet depends on Git enumeration; the existing warning
  remains the observable failure mode when Git is unavailable.

## Changelog

- 2026-08-09: initial focused plan; split from the queued multi-defect verifier
  correctness release after confirming its atomic version/closeout dependency.
- 2026-08-10: implementation, package tests, catalogue verification, build gate,
  and specialist reviews completed; plan closed.
- 2026-08-10: added the missing AgentBundle PyPI release-page update and pinned
  the required commit trailer to RFC-0002.
