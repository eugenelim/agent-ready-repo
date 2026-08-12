# Plan: self-host cross-owner write

- **Spec:** [`spec.md`](spec.md)
- **Status:** Executing <!-- Drafting | Approved | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as evidence sharpens the approach.

## Approach

Add one internal projection-copy operation that separates in-place content
replacement from metadata replacement. Its default path preserves current
behavior; a `preserve_existing_metadata` option switches existing regular
destinations to confined no-follow writes through a held descriptor. It records
the original bytes for best-effort restoration, preserves inode/ownership/mode,
and permits the OS to advance mtime. The rollback snapshot is capped at 64 MiB,
while write-only files retain the old content-copy permission floor without
rollback because their original bytes cannot be read. Thread that option through self-host's
adapter dispatcher and direct-file adapters, enabling it only for real-write.
Apply the equivalent policy to seed projection. Dry-run and ordinary adapter
callers keep their current source-metadata behavior, so mode drift remains
observable.

## Constraints

- RFC-0002 and the shipped self-hosting spec require low-nine-bit mode drift to
  remain detectable.
- Existing adapter `project` and `project_packs` callers remain source-compatible;
  any new parameter is keyword-only with a backward-compatible default.
- The package stays stdlib-only and Windows-clean.
- Package tests carry no `STUB: AC…` comments because
  `packages/AGENTS.local.md` forbids internal AC markers under `packages/`;
  the `stub: true` mapping remains in this plan as the scoped source of truth.
- The current shell cannot write temporary files, so pytest and tools that use
  `tempfile` are operator-run rather than silently treated as passing.
- Base freshness is an explicitly approved skip for this execution.

## Construction tests

**Integration tests:** A self-host dispatcher test derives every shipped adapter
from the bundled contract and asserts real-write enables metadata preservation
while dry-run leaves it disabled. A POSIX drift test proves a
source/destination mode difference remains reported by dry-run.

**Manual verification:** Run the published CLI against a prepared cross-owner
fixture and record exit status, content, mode, and modification time.

## Design (LLD)

### Design decisions

- Existing-file metadata preservation is an explicit real-write policy, not an
  exception handler. Content failures continue to raise. Traces to AC1 and AC5.
- Dry-run renders the ideal projection rather than mirroring the write process's
  ownership limitations. This preserves RFC-0002 mode-drift detection. Traces
  to AC4.
- Adapter entry points accept a keyword-only boolean with a false default; no
  global monkeypatch or process-wide context changes `shutil` behavior. Traces
  to AC2 and AC4.
- Existing targets reuse and extend `projection_io`'s root-relative,
  held-directory no-follow primitives. The opened file is identity-checked and
  must be regular before any write. Traces to AC6.

### Interfaces & contracts

No public CLI or library contract changes. The internal adapter projection
entry points gain only a backward-compatible keyword used by self-host.

### Data & schema

No persistent schema changes. The relevant state is whether the destination
existed before copying and whether the caller selected metadata preservation.

### Failure, edge cases & resilience

- Existing destinations: read original bytes, open and verify the single-link
  regular file without following links, write bytes in place, and leave
  inode/ownership/mode untouched. Mtime advances naturally. This works when the
  file is writable but its parent directory is not.
- New destinations: seed files inherit source mode; adapter direct files
  inherit source mode and, on POSIX, timestamps. Platform-specific flags and
  extended attributes are outside the self-host drift contract.
- Files larger than 64 MiB refuse before truncation. Write-only destinations
  update content but cannot restore it if that write fails after truncation.
- Mode mismatch: `--write` cannot repair it under cross-owner restrictions;
  `--check` reports it for an owner or checkout manager to resolve.
- A failed write/truncate attempts to restore original bytes through the same
  descriptor and exits nonzero; failed restoration is attached to the original
  exception. Symlink, hard-link, directory, confinement, and identity races
  refuse before the first byte is written.
- Direct-directory rails retain delete-and-recreate semantics. They do not
  overwrite an existing file and cannot reproduce the reported post-content
  metadata failure.

### Quality attributes (NFRs)

The fix is deterministic across POSIX and Windows, adds no dependency, and does
not hide content or drift failures.

## Tasks

### T1: Cross-owner overwrite regressions are red against current self-host

**Depends on:** none

**Touches:** `packages/agentbundle/tests/build_pipeline/test_projection_io.py`, `packages/agentbundle/tests/build_pipeline/test_self_host_check.py`, `packages/agentbundle/tests/build_pipeline/test_self_host_metadata_policy.py`, `packages/agentbundle/tests/unit/test_catalogue_tooling_self_host.py`

**Tests:**
- `CopyProjectedFileTests.test_existing_target_preserves_inode_owner_and_mode`
  asserts updated bytes in the same inode, unchanged POSIX owner/mode, and no
  explicit metadata mutator (AC1). `stub: true`.
- `CopyProjectedFileTests.test_existing_target_refuses_symlink` asserts the
  outside referent remains unchanged (AC6). `stub: true`.
- `CopyProjectedFileTests.test_partial_write_restores_original_bytes` asserts a
  forced mid-write failure exits by exception with original bytes restored
  (AC7). `stub: true`.
- `SelfHostAdapterRoutingTests.test_metadata_policy_reaches_every_shipped_adapter`
  derives adapters from the bundled contract and asserts real-write policy
  propagation (AC2). `stub: true`.
- `test_run_self_host_selects_metadata_policy_by_mode` drives both orchestration
  branches and asserts only real-write enables preservation;
  `DryRunCleanTreeTests.test_dry_run_reports_mode_drift_after_write` proves the
  read-only check still reports a real POSIX mode mismatch (AC4). `stub: true`.
- `test_existing_direct_file_preserves_metadata_for_every_shipped_adapter`
  runs the actual direct-file projection through every contract adapter, and
  `test_existing_seed_file_preserves_metadata` exercises the seed caller
  (AC1-AC4). `stub: true`.
- POSIX mode-drift regression proves dry-run still reports the mismatch (AC4).
  `stub: true`.

**Approach:**
- Add observable outcome assertions around real self-host entry points; use
  metadata-call fault injection only to reproduce the OS denial.
- Keep assertions on bytes, mode, modification time, exit/result, and drift
  output rather than mock call shape.

**Done when:** the checked-in stubs parse successfully and each fails for the
expected missing symbol or policy before production changes; execution is
operator-run because this shell cannot create their temporary fixtures.

### T2: Self-host overwrites preserve existing destination metadata

**Depends on:** T1

**Touches:** `packages/agentbundle/agentbundle/build/projection_io.py`, `packages/agentbundle/agentbundle/build/self_host.py`, `packages/agentbundle/agentbundle/build/adapters/*.py`, `packages/agentbundle/agentbundle/build/projections/kiro_ide_hook.py`, `packages/agentbundle/tests/build_pipeline/test_self_host_check.py`

**Tests:**
- Complete T1's regression stubs with new-file metadata cases for seed and
  adapter rails (AC1-AC4).
- Add no-follow identity-race and rollback-failure diagnostics coverage (AC6,
  AC7).
- Existing content/path/type failure tests remain green (AC5).

**Approach:**
- Implement the confined conditional copy primitive in `projection_io.py`,
  reusing held parent descriptors and keeping a rollback copy in memory.
- Thread a keyword-only preservation policy through all self-host-capable
  adapter projectors, defaulting false for existing callers.
- Enable preservation only in `run_self_host`'s real-write branch and seed
  projection; leave dry-run false.

**Done when:** focused self-host regressions pass and targeted code contains no
  real-write `copy`/`copy2` call that can mutate existing-file metadata.

### T3: Version-bump metadata identifies the correction

**Depends on:** T2

**Touches:** `packages/agentbundle/pyproject.toml`, `packages/agentbundle/agentbundle/version.py`, `packages/agentbundle/CHANGELOG.md`, `docs/specs/self-host-cross-owner-write/{spec.md,plan.md}`, `docs/specs/README.md`

**Tests:**
- Goal-based: version pins both read the AC8 release version and the changelog names the
  cross-owner write behavior (AC8); `no stub (goal-based)`.
- Goal-based: spec-status lint and the active-spec index agree (AC8, AC9);
  `no stub (goal-based)`.

**Approach:**
- Bump the two AgentBundle version pins to the AC8 release version and add its
  changelog entry.
- Keep the spec Implementing and the active index synchronized with
  implementation evidence; do not claim publication or Shipped closeout.

**Done when:** version and governance checks report no mismatch.

### T4: Available gates and required reviews are clean

**Depends on:** T3

**Tests:**
- `make lint-ruff`, `make lint-mypy`, and
  `python3 -m pytest packages/agentbundle/tests/ -q` (AC9).
- `python3 -m pytest tools/test_check_artifact_contents.py -q` builds the real
  sdist and replays its complete packaged engine suite (AC9).
- `python3 tools/test-build-check-windows-workflow.py` pins the parallel Windows
  jobs, bounded timeouts, relocated CredBroker suite, and blocking aggregate;
  `test_self_host_windows.py` pins the public command's narrower suite (AC9).
- `SKIP_SAST=1 make build-check` (AC9).
- Adversarial, security, and quality reviewers report no unresolved findings.

**Approach:**
- Run read-only checks available in this environment.
- Move CredBroker's package suite from the sequential AgentBundle Windows
  compatibility command into a parallel Windows job. Preserve the existing
  AgentBundle check identity, every test stage, and bounded timeouts for both
  jobs.
- Give the operator one minimal multiline command block for tempfile-dependent
  gates and the cross-owner CLI verification.

**Done when:** all available gates and reviewers are clean and operator-run
commands are recorded without being represented as locally passing.

### T5: Published release closes the spec in a follow-on change

**Depends on:** T4

**Tests:**
- Goal-based: the published package reports the AC8 release version, spec status is Shipped,
  plan status is Done, and the spec index/initiative queue reflect closeout;
  `no stub (goal-based)`.

**Approach:**
- After the version-bump implementation PR merges and the AC8 release is published,
  perform the repository-required two-step closeout in a separate change.

**Done when:** release publication is externally confirmed and closeout gates
pass. This task is not part of the implementation PR.

## Rollout

Merge the version-bump implementation change, publish the AC8 release version, then
land T5's separate closeout change. No migration, flag, dependency,
infrastructure, or other deployment sequencing is required. Rollback is the
code and version revert. Existing wrong modes remain visible to `--check` and
require the file owner or checkout manager to reconcile them.

## Risks

- Accidentally enabling preservation in dry-run would hide mode drift; a
  dedicated mismatch regression guards the branch distinction.
- Updating only the default adapters would leave preferred-adapter downstream
  repos broken; every registry adapter with a direct-file rail participates.
- Catching `PermissionError` after a metadata call could also hide content or
  path failures; the design avoids the metadata call entirely for existing
  real-write destinations.
- A parent-directory-only writer cannot use atomic replacement; in-place byte
  replacement intentionally preserves the existing operational model.

## Changelog

- 2026-08-12: initial plan after tracing `copy`/`copy2` through their metadata
  operations and confirming the preserve-existing-metadata contract.
- 2026-08-12: after rebase and CI, moved the release target to 0.33.3, restored
  two projection call contracts, refreshed the zipapp bloat tripwire, and split
  the Windows CredBroker package suite behind the existing aggregate check.
