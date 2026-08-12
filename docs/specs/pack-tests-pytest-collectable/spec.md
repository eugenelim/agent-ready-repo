# Spec: Pack test collection and isolation

- **Status:** Shipped
- **Owner:** maintainers
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** `packs/AGENTS.md`, `packages/AGENTS.md`
- **Contract:** none
- **Shape:** data

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

Mode: full. Relocating repository-level tests out of published pack trees is a
structural test-ownership correction.

## Objective

Python tests shipped under `packs/*/tests/` are ordinary pytest tests and are
self-contained within their owning pack. Pytest reports every legacy case
independently; pack tests do not inspect repository contracts, tools, packages,
projections, guides, or sibling packs; and repository-level coverage lives in
the existing root conformance or roster test layer.

## Boundaries

### Always do

- Convert every Python pack skill test module with a standalone `main()` or
  `unittest.main()` entry point into directly collectable pytest cases.
- Preserve behavioral assertions, skip conditions, and hermetic temporary
  repository setup while giving pytest ownership of fixtures and failures.
- Update every live direct caller of a converted module to invoke pytest.
- Anchor pack-local source paths at `packs/<pack>` without first resolving the
  repository root.
- Move tests that inspect source outside their owning pack to the existing
  repository `tests/conformance/` or `tests/roster/` layer, preserving coverage.
- Extend `tools/lint-pack-test-boundary.py` and its self-test so future pack
  tests cannot climb above their owning pack or resolve the Git root.
- Compare repository-relative fixture paths in their portable POSIX form.

### Ask first

- Change an assertion's intended behavior or weaken an existing failure.
- Remove unique test coverage that cannot be represented at the correct layer.
- Change a pack runtime payload, published metadata, or dependency.

### Never do

- Retain `main()` compatibility wrappers, `test_main` adapters, aggregate
  failure registries, or other paths that let pytest report a false pass.
- Treat temporary fixture repositories or declared runtime dependencies as
  source-tree boundary violations.
- Add a top-level directory, dependency, or parallel test-runner abstraction.
- Convert JavaScript or shell-native tests to pytest.

## Requirements

### Pytest collection

Every Python module under `packs/*/tests/skills/` that previously owned a
standalone entry point exposes its cases through pytest naming, fixtures,
assertions, and skips. A missing optional runtime dependency is an explicit
pytest skip, not a silent branch in an aggregate runner.

### Pack source confinement

A test below `packs/<pack>/tests/` may inspect files below `packs/<pack>/` and
may create or inspect temporary fixture trees. It may not derive or discover the
repository root to read another pack or a repository-owned top-level tree.
Repository conformance and catalogue roster assertions are stored outside the
pack tree.

### Portable contract paths

When a contract fixture contains a repository-relative POSIX path, its expected
value is produced with `PurePosixPath` or `Path.as_posix()` rather than
platform-native `str(Path(...))`.

## Testing Strategy

- A checked-in AST/source contract rejects standalone harnesses, aggregate
  result state, undiscoverable legacy cases, repository-root discovery, and
  path climbs above an owning pack.
- Focused pytest collection and execution runs once per affected skill
  directory, preserving the repository's basename-isolation rule.
- Existing build-chain tests verify that all migrated call sites use pytest and
  retain their ordering.
- Root conformance/roster tests execute relocated cross-boundary assertions.
- The boundary lint self-test falsifies both accepted pack-local anchors and
  rejected repository-root/path-climb shapes.
- The two work-intake fixture comparisons execute with portable POSIX expected
  paths; a source assertion prevents regression to `str(Path(...))`.
- A final diff audit rejects changes to `.apm/` runtime sources, pack metadata,
  dependency declarations, and non-Python test bodies except the approved shell
  runner invocation edits.

## Acceptance Criteria

- [x] Every audited Python pack skill test is pytest-collectable without
  missing-fixture setup errors, and every legacy case is independently named.
- [x] Python pack skill tests contain no standalone entry point, aggregate
  result registry, or wrapper around a legacy harness.
- [x] All repository callers of converted modules invoke `python -m pytest`.
- [x] No Python test below `packs/<pack>/tests/` resolves or reads source above
  `packs/<pack>`; the existing pack-boundary lint enforces and self-tests this.
- [x] Cross-pack and repository-level assertions remain covered from
  `tests/conformance/` or `tests/roster/`.
- [x] Repository-relative contract fixture paths compare as POSIX paths on
  Windows and POSIX hosts.
- [x] Pack runtime sources, pack metadata and versions, dependencies, and
  non-Python test bodies are unchanged; shell runners change only their Python
  test invocation where required.

## Assumptions

- Technical: pytest is the Python pack-test runner, and each skill directory
  runs in its own process to avoid same-basename imports (`packs/AGENTS.md`).
- Technical: temporary fixture paths and imports of installed dependencies are
  not source-tree escapes; only reads of checkout content outside the owning
  pack violate confinement (user clarification interpreted 2026-08-12).
- Product: legacy harnesses are removed and rewritten as pytest tests, without
  compatibility wrappers (user direction 2026-08-12).
- Product: repository-level contracts belong in the existing root conformance
  or roster layers rather than a published pack test tree
  (`packages/AGENTS.md`).
- Process: the change is test-only and does not require pack version bumps
  (`packs/AGENTS.md`).
