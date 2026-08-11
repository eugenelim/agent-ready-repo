# Spec: Catalogue source identity

- **Status:** Implementing
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0085; RFC-0046; ADR-0036
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Catalogue maintainers and `agentbundle` users have one adapter-neutral
definition of a local catalogue source: a valid root `catalogue.toml` and a
literal root `packs/` directory. Local default-source discovery, `catalogue
lint`, and `catalogue verify` enforce that identity. Claude's plugin marketplace
is required only when self-host projection effectively targets Claude Code, so
a Kiro-only catalogue can omit Claude artifacts without failing lint while a
Claude-capable catalogue cannot silently ship an incomplete projection.

## Boundaries

### Always do

- Preserve the five-layer source-precedence chain and repository-bounded
  editable-install walk.
- Treat `catalogue.toml` and literal root `packs/` as source-identity markers;
  validate configured operational paths separately.
- Derive Claude marketplace requirements from the same effective-adapter
  predicate used by self-host projection.

### Ask first

- Expanding the mandate to every internal caller that currently accepts a
  missing `catalogue.toml`.
- Changing explicit catalogue-argument validation, remote source resolution,
  or installable archive content.
- Adding any compatibility alias, deprecation window, or migration automation.

### Never do

- Accept `.claude-plugin/marketplace.json` as a substitute for
  `catalogue.toml`.
- Remove or reorder the organization Artifactory bootstrap or any other source
  precedence layer.
- Add a new dependency, top-level directory, or new module boundary for this
  change.

## Testing Strategy

- **Source identity and editable discovery: TDD at unit and integration
  boundaries.** Marker fixtures prove `catalogue.toml + packs/` succeeds,
  marketplace-only legacy roots fail, and the repository-bounded walk remains
  unchanged.
- **Adapter-aware lint and verify: TDD at unit level.** Matrix tests cover
  Kiro-only, Claude, default effective adapters, missing config, missing root
  packs, custom configured pack paths, and present-marketplace validation.
- **Release and documentation coupling: goal-based checks.** Version equality,
  reference searches, doc links, and repository lint gates prove all published
  surfaces carry the same contract.
- **CLI behavior: manual QA through the real package entry point.** A valid
  source checkout is linted through `python -m agentbundle catalogue lint`;
  targeted pytest exercises the negative filesystem cases that require a
  writable temporary directory.

## Acceptance Criteria

- [x] AC1: Local configured-source validation and editable-install discovery
  recognize a root only when both `catalogue.toml` and literal root `packs/`
  exist.
- [x] AC2: A legacy root containing `packs/` and
  `.claude-plugin/marketplace.json` but no `catalogue.toml` is not a valid
  default local source.
- [x] AC3: The five-layer order remains explicit argument, user configuration,
  organization Artifactory bootstrap, editable discovery, packaged default;
  explicit catalogue arguments retain their existing pass-through behavior.
- [x] AC4: `catalogue lint` emits one catalogue-level `CAT-L002` diagnostic and
  returns non-zero when `catalogue.toml` is absent.
- [x] AC5: `catalogue lint` requires the literal root `packs/` marker even when
  `catalogue.paths.packs` names another directory; the configured directory is
  checked separately for catalogue content.
- [x] AC6: A missing configured Claude marketplace emits `CAT-L002` when the
  effective adapters include `claude-code`.
- [x] AC7: Marketplace absence emits no diagnostic when a preferred adapter
  outside the self-host allow-list makes the effective set Kiro-only.
- [x] AC8: Default or already-allowed preferred adapters retain the full
  self-host allow-list and therefore retain the Claude marketplace requirement.
- [x] AC9: Self-host generation and lint consume one shared predicate for
  whether Claude project artifacts are required.
- [x] AC10: `catalogue verify` runs lint for a root without `catalogue.toml` and
  reports the lint failure instead of treating config-dependent steps as a
  successful skip.
- [x] AC11: Existing marketplace files continue through the established verify
  parsing and manifest-validation steps; installable archive verification is
  unchanged.
- [x] AC12: `agentbundle` reports version 0.33.0 from both version sources, and
  the changelog includes the breaking source-marker migration.
- [x] AC13: RFC-0046 and ADR-0036 carry approver-signed errata for the marker
  replacement, and current architecture, reference, and PyPI package
  documentation no longer calls the Claude marketplace catalogue identity.
- [x] AC14: Focused source-default, lint, verify, self-host, and CLI tests pass;
  Ruff, type checking, spec-status lint, and diff hygiene pass.
- [x] AC15: Editable discovery continues to canonicalize before its
  enclosing-Git-root walk and never accepts a marker outside that root.
  Traversal, symlink escape, and circular-resolution failures in editable or
  configured catalogue paths fail closed with existing diagnostic families;
  lint does not inspect pack content through a configured path that resolves
  outside the catalogue root.

## Assumptions

- Technical: self-host intentionally omits Claude artifacts when the effective
  adapters exclude `claude-code` (source: `packages/agentbundle/agentbundle/build/self_host.py`).
- Technical: the current local marker pair is an accident guard rather than a
  trust control (source: RFC-0046 and ADR-0036).
- Technical: modern catalogue initialization creates `catalogue.toml` and
  `packs/`, and source-flavour packaging includes `catalogue.toml` (source:
  initializer/package implementation and tests).
- Product: legacy marker-only catalogues may break now because the project is
  early enough to mandate one identity (source: user confirmation 2026-08-11).
- Process: the change ships as `agentbundle` 0.33.0 with no compatibility
  window (source: user confirmation 2026-08-11 and `packages/AGENTS.md`).
- Process: the implementation belongs to initiative `ini-007` (source: user
  confirmation 2026-08-11).
