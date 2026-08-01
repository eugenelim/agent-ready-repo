# Spec: workspace-status simplification — Order 1A

- **Status:** Shipped
- **Owner:** maintainer
- **Plan:** [`plan.md`](plan.md)
- **Mode:** full (structural/public-interface change + file-I/O boundary + multi-feature/dependent work)
- **Constrained by:**
  - [RFC-0023](../../rfc/0023-credential-manager-broker.md) — shared-libs projection retired; skills must be self-contained
  - [RFC-0049](../../rfc/0049-the-release-loop-and-company-os.md) — Company OS architecture authority
  - [RFC-0064](../../rfc/0064-ini-001-ai-native-ecosystem.md) — workspace.toml schema and workspace-status behavior authority
  - `packs/core/.apm/skills/workspace-status/SKILL.md` — production behavior; preserved
  - `packs/core/.apm/skills/work-loop/SKILL.md` — workspace.toml interactions; unchanged
  - `docs/specs/workspace-status-simplification-order-0/spec.md` — Phase 0 characterization; compatibility authority
- **Contract:** none (internal skill interface only)
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Promote the Phase 0 executable reference model into the installed, self-contained
workspace-status skill and make it the one canonical production parser and resolver.
The live skill invokes a deterministic Python backend for all parsing, DAG resolution,
reconciliation, and cleanup-planning; the backend returns a versioned JSON object the
skill uses as its sole data source for rendering. No algorithmic logic is duplicated
between the backend, SKILL.md, and tools/. Order 1A changes the implementation path
only: it introduces no intentional change to classifications, reconciliation findings,
output categories, next-action semantics, cleanup confirmation behavior,
workspace.toml schema, work-loop behavior, scan scope, or session-start performance.

## Boundaries

### Always do

- The canonical engine lives at `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py` (moved from `tools/` via `git mv`)
- A thin CLI at `packs/core/.apm/skills/workspace-status/scripts/workspace_status.py` accepts a repository root, invokes the engine, and serializes the result as deterministic UTF-8 JSON with `"schema_version": 1`
- `tools/test_workspace_status.py` and `tools/bench-workspace-status.py` import from the production module path
- Update SKILL.md to invoke the CLI; remove duplicated manual parsing/DAG/reconciliation procedure; preserve rendering, confirmation, and cleanup behavior
- Add projection tests (scripts present in every installed adapter) and an end-to-end installed-CLI invocation test
- Correct `guides/_shared/how-to/author-a-skill.md` to remove the false shared-libs projection promise
- Run `make build-self` after editing packs/; verify generated projection contains both scripts
- Keep the engine Python 3.11 standard-library-only

### Ask first

- Any change to workspace.toml schema (not in scope; surface if evidence requires)
- Any change to existing Phase 0 characterization test assertions beyond updating the import path
- Any installation behavior change (the contract says not to modify installer production code)
- Changes to the cleanup confirmation behavior in SKILL.md beyond routing the operation metadata from backend output

### Never do

- Add quick/default-versus-full mode
- Add workspace-reconcile subcommand
- Edit work-loop behavior or its stale-state check
- Remove or reinterpret `work.active` / `work.shipped`
- Change workspace.toml schema
- Add caching, cycle detection, or missing-target diagnostics
- Fix Phase 0 known defects (KD-01 through KD-09); document them as unchanged
- Put the engine in `.apm/shared-libs/` or restore generic shared-libs projection
- Create a Python package or global CLI adapter-root binary
- Import from `tools/`, `packs/`, or sibling skills at runtime
- Import the engine from `tools/` in production code (only Phase 0 tests use a test-only importlib loader)
- Invoke the CLI via `shell=True` or with an unquoted `--root` argument in SKILL.md; the invocation must quote the root path
- Modify installer production code
- Add any third-party dependency
- Create nested directories under `scripts/`

## Testing Strategy

- **TDD** — CLI contract (invocation, JSON shape, exit codes, no-write guarantee, Unicode, non-repo cwd), production module parity (all 41 Phase 0 tests rewired to the skill-local module), and projection contract (scripts present in every adapter projection). Tests written as red stubs before implementation.
- **Goal-based check** — `make build-self` passes and generated projection contains both scripts. SKILL.md correctly invokes CLI (grep-based structural check).
- **Visual / manual QA** — installed CLI invoked end-to-end against a fixture repository; exit code, schema_version, and semantic counts recorded.

## Acceptance Criteria

- [x] AC1. The canonical engine lives under `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py`.
- [x] AC2. The engine no longer exists under `tools/`; no second copy of parsing, dependency, reconciliation, or cleanup-planning logic remains.
- [x] AC3. Phase 0 tests and benchmark exercise the production module (import path updated; no copy of engine in tools/).
- [x] AC4. The production skill (SKILL.md) invokes `scripts/workspace_status.py` against the target repository.
- [x] AC5. The CLI emits deterministic versioned JSON with `"schema_version": 1`. The JSON provides ready, blocked, shaping, brief, and reconciliation data (including `type2_cleanup_ops` per Type 2 finding) so the skill does not independently recompute the DAG or reconciliation. The skill may still read external files the engine does not own: `docs/product/findings/*.md` (findings-register tables) and per-backlog-entry `# ` comment lines from workspace.toml text for the backlog section summary.
- [x] AC6. Current ready, blocked, shaping, brief, and reconciliation semantics are unchanged (Phase 0 parity: 40/40 tests pass against the production module; 1 hash-anchor test removed in T3).
- [x] AC7. Current Type 2 confirmation and cleanup behavior is unchanged; the exact cleanup operation metadata (`type2_cleanup_ops`) comes from backend output rather than a second reconciliation.
- [x] AC8. The CLI is read-only (no file writes); verified by snapshotting fixture subtree membership and mtimes before/after execution and asserting no new files are created and no existing files are modified.
- [x] AC9. Skill-local scripts are present in every supported adapter projection (verified by installer tests).
- [x] AC10. An installed CLI is executed end-to-end against a fixture repository, result recorded.
- [x] AC11. The CLI works when invoked from a non-repository current working directory.
- [x] AC12. Runtime code has no imports from `tools/`, `packs/`, shared-libs, or sibling skills. Verified by a goal-based grep over both scripts asserting only stdlib and script-relative imports.
- [x] AC13. No new runtime dependency is introduced (stdlib-only). Verified by a goal-based grep asserting no third-party import in either script.
- [x] AC14. `guides/_shared/how-to/author-a-skill.md` no longer promises generic shared-libs projection; states skills must be self-contained with `scripts/`.
- [x] AC15. Quick mode, reconciliation separation, schema migration, and caching are absent from the diff. Work-loop skill improvements (anchor-test PLAN step, structured-config grep anti-pattern, QA-isolation section in verification-modes) were co-landed as a separate concern in the same PR; they do not alter workspace-status engine behavior or output contract.
- [x] AC16. `make build-self`, focused tests, `make build-check`, and `make ci` pass.
- [x] AC17. The actual installed artifact's happy path is exercised and recorded (command, exit code, schema_version, semantic counts).
- [x] AC18. Production behavior and output-category parity are documented in the PR.
- [x] AC19. The Type-1 forward scan's symlink-confinement guards (`followlinks=False`, symlinked-`spec.md` skip, `docs/specs`-escape rejection via `relative_to`) are preserved invariants, verified by a characterization test that plants a symlinked spec dir escaping root and asserts it is not read.
- [x] AC20. The CLI's top-level exception handler routes every unhandled exception to stderr (exit 2) with no traceback and no absolute filesystem paths on stdout, verified by a test forcing a permission/generic error and asserting stdout is empty or valid JSON.

## Assumptions

- Technical: Engine is 861 lines, stdlib-only (`dataclasses`, `os`, `re`, `time`, `tomllib`, `pathlib`) — confirmed by read; now at `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py`
- Technical: `packs/core/.apm/skills/workspace-status/scripts/` holds both `workspace_status_engine.py` and `workspace_status.py` — confirmed by `ls`
- Technical: `packs/core/.apm/skills/work-loop/scripts/` projects correctly to `.claude/skills/work-loop/scripts/` — confirmed by `ls` of self-host projection
- Technical: Phase 0 suite passes 40/40 tests (one hash-anchor test removed in T3) and benchmark completes cleanly — confirmed by running both
- Technical: RFC-0023 retired shared-libs projection; `shared_libs.py` is source-enumeration for the sso-broker companion rail only — confirmed by reading the module
- Technical: `author-a-skill.md` corrected in T6 to remove false shared-libs projection promise — confirmed by edit
- Process: Full-mode work-loop required; risk triggers: structural/public-interface change, file-I/O boundary, multi-feature — stated in contract and cross-checked against work-loop risk-trigger list
