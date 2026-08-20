# Plan: Build-check single verification

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done

## Approach

Make the cross-platform gate-chain script the single owner of the complete
Windows-clean build-check sequence. It runs portable verification once, keeps
the persistent catalogue build, and invokes the pre-PR aggregator in an
explicit repository-checks-only mode. Standalone pre-PR calls retain their
current verification-first behavior.

## Constraints

- ADR-0056 keeps portable catalogue verification in the published engine and repository policy wiring in `tools/`.
- ADR-0017 keeps conditional SAST/SCA after the Windows-clean gate chain in `make build-check`; the make-free Windows command does not acquire that leg.
- The persistent catalogue build remains observable behavior even though portable verification performs its own temporary build.

## Construction tests

**Integration tests:** exercise `SKIP_SAST=1 make build-check`, `python tools/repo/build_gate_chain.py build-check`, and `make pre-pr`; record exit codes and verification-count evidence from complete, unfiltered command output.

**Manual verification:** inspect the three command transcripts for one `catalogue verify: ok` on each build-check path and one on standalone pre-PR, plus every expected terminal success line.

## Design (LLD)

### Dependencies & integration

`tools/repo/build_gate_chain.py` owns the Windows-clean sequence. It invokes the portable verifier, materializes `dist/`, and then calls the repository pre-PR aggregator in an explicit mode that omits only the already-completed portable verification. The Make target delegates to that chain before appending SAST/SCA. This realizes AC1-AC5 without changing the published catalogue CLI.

### Interfaces & contracts

The contributor-facing interfaces remain `make build-check`, `python tools/repo/build_gate_chain.py build-check`, `make pre-pr`, and `python tools/catalogue/pre_pr_catalogue.py`. The new pre-PR option is repo-internal and accepted only to prevent nested verification; default invocation remains verification-first. This realizes AC1-AC4.

### Failure, edge cases & resilience

The chain still stops at the first non-zero step. The nested pre-PR mode cannot suppress portable verification for standalone callers by default, and focused argv tests distinguish the parent-owned skip from accidental verifier removal. This realizes AC1-AC5.

## Tasks

### T1: Build-check performs one portable verification without dropping gates

**Depends on:** none

**Tests:**
stub: true

- TDD stub in `tools/test_build_gate_chain.py` asserts the chain invokes `catalogue verify` once, then `catalogue build`, then every existing repository-specific script in order.
- TDD stub in `tools/test_build_gate_chain.py` asserts the nested pre-PR invocation receives its explicit skip-verification argument while standalone pre-PR retains verification.
- TDD stub in `tools/test_build_gate_chain.py` captures the ordered repository-specific `_run(...)` labels inside `pre_pr_catalogue.py` plus final `tools/hooks/pre-pr.py` delegation, so removal or reordering fails.
- TDD construction tests pin the complete build-check spawned-step roster and both pre-PR ownership boundaries.

**Approach:**
- Use TDD for the argv, ownership, ordering, and default-behavior invariants; verify the stubs fail before changing production orchestration.
- Move the portable verification step from the Make recipe into `tools/repo/build_gate_chain.py` so direct Windows invocation has the same coverage.
- Add an explicit internal pre-PR mode that skips only its portable verification when the parent chain has already completed it.
- Update focused orchestration tests and comments to encode the single-verification contract.

**Done when:** focused tests pass and the real `SKIP_SAST=1 make build-check` run reports one successful portable verification without losing any later gate.

### T2: Living architecture and real command evidence match the optimized chain

**Depends on:** T1

**Tests:**
- No stub (goal-based): `docs/architecture/agentbundle.md` names the current `agentbundle catalogue` surfaces and the actual portable/repo/SAST sequence.
- No stub (goal-based/manual CLI): run the Make build-check, make-free build-check, and standalone pre-PR commands unfiltered; retain exit codes and verification-count observations in the work-loop handoff.

**Approach:**
- Update the living architecture's stale `agentbundle.build` handler description and command paths.
- Run each contributor-facing command and compare its output against AC1-AC6.

**Done when:** architecture prose matches the implementation and all three real command paths exit zero with the expected verification ownership.

## Rollout

The change lands atomically and is reversible by restoring the previous Make and Python orchestration. It adds no deployment, infrastructure, external integration, or irreversible state.

## Risks

- A skip option applied to a standalone pre-PR call could silently remove portable verification; default behavior and focused parser/argv tests prevent that.
- Moving verifier ownership into the Python chain could drop Make-only coverage; exact sequence tests and both real CLI paths prevent drift.
- The optimization intentionally retains two catalogue builds because one validates temporary output and one materializes `dist/`; removing the persistent build is outside this spec.

## Resolve-vs-surface disposition

- Resolve locally: implementation details, focused test shape, architecture wording, and all review findings within the accepted command boundaries.
- Surface: any need to remove or alter a gate, change `dist/` materialization, modify SAST policy, add a dependency, or cross the managed workspace's Git mutation boundary.

## Changelog

- 2026-08-16: initial plan; escalated to full mode after spec review identified the contributor-facing command contract.
