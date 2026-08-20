# Spec: Build-check single verification

- **Status:** Shipped
- **Owner:** maintainers
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0056; ADR-0017
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** integration

Mode: full (public-interface change: contributor-facing build-check and pre-PR command orchestration)

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

The repository's `make build-check` and make-free Windows equivalent run the
portable catalogue verification exactly once while preserving the materialized
catalogue build, every repository-specific policy gate, their fail-fast order,
and standalone `make pre-pr` verification.

## Boundaries

### Always do

- Keep portable catalogue checks inside the `agentbundle catalogue verify` boundary defined by ADR-0056.
- Keep repository-specific policy gates in `tools/` and preserve their existing fail-fast ordering.
- Keep ADR-0017's SAST/SCA leg appended to `make build-check` and outside the make-free Windows chain.

### Ask first

- Changing any individual portable or repository-specific gate's behavior or membership.
- Changing whether `build-check` materializes `dist/`.
- Changing the SAST relevance or skip policy.

### Never do

- Add a dependency, cache, new module boundary, or top-level directory for this optimization.
- Move repository-only policy logic into the published `agentbundle` package.
- Treat reduced logging as proof that duplicate verification work was removed.

## Testing Strategy

- **TDD at the orchestration boundary:** focused unit tests record spawned argv and prove one portable verification, one persistent build, explicit nested pre-PR skip mode, exact repository-specific step order, and fail-fast behavior.
- **Goal-based integration checks:** the real Make target, make-free build-check command, and standalone pre-PR command each run successfully; captured output proves the build-check paths report one verification while standalone pre-PR still reports its own verification.
- **Goal-based repository gates:** Ruff, mypy where applicable, focused tests, and `SKIP_SAST=1 make build-check` prove the changed gate remains self-hosting without requiring the separately governed scanner leg during the inner loop.

## Acceptance Criteria

- [x] `make build-check` and `python tools/repo/build_gate_chain.py build-check` each reach exactly one `agentbundle catalogue verify` invocation before any persistent build or repository-specific policy gate.
- [x] The build-check gate chain still materializes the configured `dist/` output once before repository-specific policy gates run.
- [x] Standalone `make pre-pr` still performs portable catalogue verification before repository-specific policy gates.
- [x] The repository-specific build-check roster remains the ordered `steps` list in `tools/repo/build_gate_chain.py`; the pre-PR roster remains the ordered calls in `tools/catalogue/pre_pr_catalogue.py`, including delegation to `tools/hooks/pre-pr.py`; focused tests fail if the orchestrated commands, arguments, ordering, or delegation change.
- [x] The Make target still appends ADR-0017's conditional SAST/SCA leg after the complete Windows-clean chain, while the make-free command continues to exclude it.
- [x] `docs/architecture/agentbundle.md` describes the as-built portable-verification, persistent-build, repo-policy, and SAST boundaries without naming retired command surfaces.

## Assumptions

- Technical: `catalogue verify` performs a temporary catalogue build as step 10 (source: `packages/agentbundle/agentbundle/catalogue_tooling/verify.py`).
- Technical: the persistent catalogue build remains part of the build-check contract (source: `tools/repo/build_gate_chain.py`).
- Product: repeated portable verification is the optimization target; catalogue scope filtering remains unchanged (source: user confirmation 2026-08-16).
- Process: the change runs through the full work-loop because contributor-facing command orchestration is a public interface, and stops before Git mutations prohibited by the managed workspace (source: adversarial review 2026-08-16; user confirmation 2026-08-16).
