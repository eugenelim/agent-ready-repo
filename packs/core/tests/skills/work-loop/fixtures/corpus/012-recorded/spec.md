# Spec: core pack path confinement

- **Status:** Shipped
- **Owner:** maintainer
- **Plan:** [`plan.md`](plan.md)
- **Mode:** full (security boundary and shipped public-interface behavior)
- **Constrained by:**
  - [ADR-0017](../../adr/0017-adopt-bandit-pip-audit-semgrep-sast-gate.md) — fix source before suppressing a finding
  - [`pack-script-root-boundary-validation`](../pack-script-root-boundary-validation/spec.md) — prior argv-path hardening and its now-disproved scanner assumption
  - [`loop-cohort-state-lock`](../loop-cohort-state-lock/spec.md) — fail-closed lock ownership and no-follow semantics
- **Contract:** none; existing CLI arguments, valid-input output, and state schemas stay compatible
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it.

## Objective

Close the genuine CWE-23 class behind downstream Snyk Code reports against
the shipped core pack: repository-derived reads and probes must remain inside
their declared root, and work-loop managed state and lock files must not follow
attacker-controlled symlinks. Preserve intentional operator-selected scan
roots and valid CLI behavior. Where a reported flow is already safe, keep the
control readable and record an evidence-backed false-positive disposition
instead of weakening the interface or adding scanner-specific code.

## Evidence and scope

The report names seven paths in core 2.5.6. Direct call-path tracing produced
the following disposition:

| Reported file | Reported sink | Disposition |
| --- | --- | --- |
| `append-knowledge.py` | `os.link(stale, lock)` | Reported argv flow is confined to `docs/knowledge`; adjacent custom lock reads can follow a symlink and will be replaced by the hardened shipped lock helper. |
| `lint-spec-status.py` | root-relative path operations | Valid class: `workspace.toml`, `contracts/REGISTRY.md`, and Markdown/code reference probes are not uniformly resolve-then-confine. |
| `lint-traceability.py` | `os.walk` / path probes | Highlighted configured-layout path is checked; adjacent default and component-marker probes check existence before confinement. |
| `loop-engine.py` | `.loop-run` path construction | Environment-to-directory flow is false positive; adjacent state and pending-event reads can follow symlinks and expose target JSON through status output. |
| `workspace_status.py` | temporary-file `Path` | False positive: the workspace path is confined and the temporary name is created by `mkstemp` in its parent. |
| `check-spec-status.py` | `spec_dir / args.file` | False positive: the resolved target is immediately required to be below the resolved spec directory. |
| `lint-knowledge.py` | `os.chdir(repo_root)` | False positive: Git location variables are stripped before discovering the repository; its optional file argument intentionally selects an operator-owned input. |

The same-class sweep also found `loop-cohort.py` reading managed `state.json`
through a symlink and `loop-engine.py` following a dangling `events.jsonl`
symlink while creating the event log. They are in scope because they share the
work-loop state trust boundary and can expose or mutate external files.
Unrelated argv-to-path sites remain in the existing
`pack-argv-path-boundary-sweep` backlog item.

## Boundaries

### Always

- Resolve repository-derived candidate paths, verify containment, and only
  then probe or read the canonical path.
- Treat work-loop state, pending-event, and lock paths as managed files:
  reject symlinks and non-regular files, detect identity changes around a
  read, and cap each managed JSON input at 8 MiB (the existing shipped
  file-reader cap).
- Use pure-stdlib, cross-platform behavior and preserve current valid CLI
  arguments, output, exit codes, and state schemas.
- Change canonical `packs/core/.apm/` sources, synchronize every generated
  projection, and bump the core pack patch version.

### Ask first

- Narrow any intentional operator-selected root or file argument beyond
  rejecting traversal or symlink escapes from a declared root.
- Change a state schema, introduce a new shared runtime primitive, or add a
  scanner-org suppression.

### Never

- Read an external target merely to decide whether it is safe.
- Add a dependency, hard-code an allowed parent for a general-purpose scan
  root, or exclude an entire shipped file from Snyk Code.
- Put real secrets or user-specific paths in fixtures or diagnostics.

## Acceptance Criteria

- [x] **AC1 — Spec-status confinement.** `lint-spec-status.py` resolves and
  confines `workspace.toml`, the contract registry, contract files, and every
  Markdown/code reference candidate before any existence probe or read.
  Outside-root traversal and symlink targets do not affect diagnostics;
  valid in-root behavior is unchanged.
- [x] **AC2 — Traceability confinement.** `lint-traceability.py` performs
  containment before default-layout and component-marker probes and operates
  on the resulting canonical path. Its recursive directory iterator prunes a
  child before descent when that child resolves outside the root, handles a
  circular-resolution failure without escaping or crashing, and derives
  reported IDs only from canonical confined paths. An outside-root symlink or
  junction cannot affect the graph or diagnostics; configured valid layouts
  still work.
- [x] **AC3 — Managed-state files.** `loop-engine.py` and `loop-cohort.py`
  reject symlinked, non-regular, over-8-MiB, or identity-changing state and
  pending-event files without printing or acting on the external target's
  content; recovery also rejects a linked or non-directory `.loop-run` parent
  before accessing any child. Event-log initialization and append reject
  symlinked, non-regular, or identity-changing paths without creating or
  mutating the external target, and newly created event logs are owner-only.
  Normal state/status/recovery behavior remains compatible.
- [x] **AC4 — Knowledge lock.** `append-knowledge.py` uses the existing
  `_statelock` ownership and no-follow semantics rather than its weaker custom
  lock implementation. A symlink or non-regular lock fails closed without
  mutation. Stale recovery applies only to a regular lock carrying a
  recognized `_statelock` record; normal append and recognized stale-lock
  recovery retain their documented behavior. This intentionally replaces the
  old append-only behavior that reclaimed a stale directory.
- [x] **AC5 — Reported false positives.** The evidence table in this spec is
  the source-level disposition for the already-safe boundaries in
  `check-spec-status.py`, `workspace_status.py`, `lint-knowledge.py`, and the
  reported `loop-engine.py` root derivation; those scripts are not changed
  merely to alter scanner dataflow. No valid operator-selected path is
  restricted solely to appease a taint engine.
- [x] **AC6 — Security regressions.** Tests create real traversal and symlink
  cases, assert that external contents never appear, and prove the failure is
  caused by the boundary under test. Symlink-specific cases skip only on
  platforms that cannot create them; they remain required in CI elsewhere.
- [x] **AC7 — Release surfaces.** Core's pack and plugin manifests receive a
  patch bump, projections are synchronized, the marketplace aggregate is
  regenerated (core remains intentionally absent because it is repo-only),
  and `[Unreleased]` records the confinement hardening.
- [x] **AC8 — Documentation accuracy.** The prior blanket "all false
  positives" statement and the prior assumption that Snyk recognizes the
  `_validated_root` shape are corrected with this evidence. Snyk Code findings
  that remain intentional are dispositioned downstream through supported
  issue controls, not a repo-wide file exclusion.
- [x] **AC9 — Verification.** Targeted work-loop and workspace-status tests,
  pack conformance, projection drift, lint, and the repository build/SAST
  gate pass in a writable environment. Any unavailable local gate is reported
  as environment-blocked rather than represented as passing.

## Testing strategy

| AC | Mode | Mechanism |
| --- | --- | --- |
| AC1–AC2 | TDD | Add outside-root traversal, symlink/junction-like, and circular-resolution fixtures to the existing lint suites before changing the readers; assert the iterator prunes before descent and retain valid-layout cases. |
| AC3 | TDD | Add state and pending-event symlink/non-regular/oversize regressions to the engine and cohort suites; assert no target sentinel reaches stdout/stderr. Add dangling event-log symlink regressions for initialization and append; assert no external target is created. |
| AC4 | TDD | Extend append-knowledge tests for hostile lock types and stale recovery, then prove the shared lock helper owns the behavior. |
| AC5 | Goal-based | Maintain the disposition table above as the artifact: each row names the reported sink, its dominating control, and whether adjacent work is in scope. No new source/CLI assertion is implied for intentionally operator-authorized paths. |
| AC6 | Goal-based | Review each security test for a real sink, a sentinel external target, and a fail-closed assertion. |
| AC7–AC8 | Goal-based | Version/projection equality checks, changelog/spec checks, and `workspace.toml` parsing. |
| AC9 | Goal-based | Targeted pytest, `make build-self`, `make build-check`, and lint gates in a writable CI/developer environment. |

The current managed workspace has no writable temporary directory, so it
cannot execute pytest fixtures or generated-output gates. The tests remain
mandatory and will be run as the final external verification set; this is not
a permanent skip.

Initial verification ran in the writable developer environment on 2026-08-11:
`test-append-knowledge.py` passed 30/30 cases,
`test-lint-traceability.py` passed 44/44 cases, and `make ci` completed every
leg including catalogue verification, projection drift, Bandit, dependency
audit, Semgrep plus its construction tests, Ruff, mypy, and the complete test
matrix. A subsequent CodeQL result required an owner-only event-log creation
mask, and Linux CI exposed an obsolete stale-lock test expectation. Those
amendments and their final verification are complete (source: maintainer
confirmation 2026-08-12).

PLAN materializes red stubs for AC1–AC4 in the existing script suites. TDD
coverage: AC1–AC4 covered; AC5–AC9 use goal-based verification and therefore
have no red stub.

## Assumptions

1. An attacker may control repository files and symlinks but not bypass OS
   permissions. Confidence: high; this is the declared untrusted-filesystem
   boundary and the downstream scan context.
2. The same-class sweep should cover managed work-loop state readers, not only
   the exact seven cards. Confidence: high; they expose the same external-file
   read primitive and are within the same shipped boundary.
3. Operator-provided scan roots and standalone file arguments are authority,
   not traversal, unless the command declares a narrower root. Confidence:
   high; restricting them would break the documented CLI contract.

## Declined approaches

- Add a new dependency or a broad path-safety framework: existing stdlib
  primitives and `_statelock` cover the required boundary.
- Force every CLI path below the current repository: several commands are
  intentionally general-purpose scanners or fixture linters.
- Add `.snyk` issue-ignore entries or whole-file exclusions: Snyk Code issue
  handling is downstream-owned and exclusions would also hide future defects.
- Expand this PR into all argv/path call sites: the existing backlog sweep is
  the correct owner for unrelated boundaries.
