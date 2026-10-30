# Spec: Windows confined write

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0152, ADR-0144
- **Brief:** none
- **Discovery:** none
- **Depends on:** none
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy`,
> `Acceptance Criteria`, and `Accepted Risk` are what a completion gate reads,
> and an amendment changes them. `Outcome`, `What Changes`, `Durable Outputs`,
> `Follow-ons`, and `Assumptions` are working material that an author corrects
> in place.

## Outcome

Maintainers and adopters running full-mode `work-loop` on Windows get a
supervisor whose durable writes succeed through the same three confined-write
operations POSIX uses, refusing every link, reparse point, alias, and escape they
can observe, and reporting "state unknown" when they observe one too late.
Success is that suite passing unpatched on a real Windows host, with the one race
a path check cannot close declared by the module, refused for untrusted code, and
accepted by its owner for trusted runs.

## What Changes

- A path-checked mode for create, append, and atomic replace —
  `packs/core/.apm/skills/work-loop/scripts/_confined_mutation.py`.
- A race-free-mutation query in the same module, read by the supervisor's
  untrusted-code admission — `_supervisor_admission.py`.
- Path-checked tests on a simulated host and on the Windows CI job —
  `packs/core/tests/skills/work-loop/` and `.github/workflows/build-check-windows.yml`.
- The decision, the platform capability line, and a pointer on the narrowed
  Slice 1 spec — ADR-0152, `docs/architecture/runtime-security-primitives.md`,
  and `docs/specs/acceptance-authority-and-evidence/spec.md`'s `Status`.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Decision rationale | A shipped security guarantee narrows on one platform. | `docs/adr/0152-path-checked-confined-writes-on-hosts-without-descriptor-walking.md`, `docs/adr/README.md`, and the `Status` of `docs/specs/acceptance-authority-and-evidence/spec.md` | eugenelim | ADR shape lint and spec-status lint | ADR-0152 is `Accepted` and the Slice 1 `Status` names it. |
| Current architecture | The platform capability set gains one declared gap. | `docs/architecture/runtime-security-primitives.md` | Platform Core | Architecture review | The page names the path-checked mode, its residual race, and the untrusted-code refusal. |
| Release history | Pack content changes. | Core manifests and `docs/product/changelog.d/` | Core pack maintainers | Version parity | A patch entry names the Windows write support. |

## Agent Rules

### Always do

- Refuse on any check the host cannot perform, rather than write.
- Keep shipped text under `packs/` free of internal record citations.
- Get a security-reviewer pass before merge.

### Ask first

- Any change to the descriptor-walk path that POSIX hosts take.

### Never do

- Add a dependency or a `ctypes` binding; the module stays standard-library only.
- Change a caller of the three operations other than the untrusted-code
  check in `work-supervisor.py` and `_supervisor_admission.py`, or change the
  read helpers.

## Testing Strategy

- **Path-checked behaviour (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005,
  AC-0006, AC-0007, AC-0008):** TDD on a simulated host, because every refusal
  and every late detection is a deterministic function of the path string and
  the identities the host reports, so a POSIX run that selects the path-checked
  mode at its one host-capability point proves each branch.
- **Real host (AC-0009):** goal-based, by the Windows CI job running the
  Windows module unpatched on NTFS with real junctions, because only Windows
  reports reparse attributes, folds letter case, generates short names, and has
  its `os.replace` and `os.link` semantics.
- **Capability query and admission (AC-0010, AC-0011):** TDD, because both are
  pure functions of the host's support.
- **POSIX parity (AC-0012):** goal-based regression, because the existing
  descriptor-walk suite already pins POSIX behaviour.

## Acceptance Criteria

### Definitions

- **Path-checked host.** A host where descriptor-relative walking is
  unavailable and `os.lstat` reports the file-attribute field that identifies
  reparse points.
- **The three operations.** `confined_create`, `confined_append`, and
  `confined_atomic_replace`.
- **Late detection.** A check that runs after the bytes are committed finds the
  target or an ancestor different from what was recorded before the write.

### Criteria

- [x] **AC-0001.** On a path-checked host, each of the three operations returns
  without raising, and the target holds exactly the supplied bytes, or for
  append the prior bytes followed by the supplied bytes.
- [x] **AC-0002.** On a path-checked host, each of the three operations refuses
  with `denied-path-violation`, leaves any prior target byte-identical, and
  writes nothing, when the target or any component below the root is a link or
  a reparse point.
- [x] **AC-0003.** On a path-checked host, each of the three operations refuses
  with `denied-path-violation`, leaving any prior target byte-identical, when the
  target is not a regular file or has more than one link.
- [x] **AC-0004.** On a path-checked host, each of the three operations refuses
  with `denied-path-violation` before any filesystem call when the target's path
  relative to its root has a component that is an alternate data stream
  (contains `:`), a reserved device name with or without an extension (`CON`,
  `PRN`, `AUX`, `NUL`, `COM1` to `COM9`, `LPT1` to `LPT9`, `CONIN$`, `CONOUT$`),
  or ends in a dot or a space, or when that relative path is itself absolute,
  drive-relative, or starts with `\\?\`, `\\.\`, or `\\`.
- [x] **AC-0005.** On a path-checked host, containment compares the
  case-normalised, fully resolved long-name paths of the target and the root,
  so a short name or a different letter case cannot place a target outside the
  root.
- [x] **AC-0006.** On a path-checked host, when a newly created staging file
  fails its identity, link-count, reparse, or containment check, the operation
  refuses with `denied-path-violation` before writing any byte, and removes only
  the file it created.
- [x] **AC-0007.** On a path-checked host, a late detection raises
  `denied-rollback-failed` and never returns success, for each of the three
  operations. For create and replace that means the committed target is not a
  regular file with exactly one link that is the file the operation wrote, or
  an ancestor's identity differs from its recorded identity. For append it
  means the open file's identity differs from the in-root path's identity, or
  an ancestor's identity differs.
- [x] **AC-0008.** A host with neither descriptor-relative walking nor reparse
  attributes refuses each of the three operations with `denied-unsafe-host`.
- [x] **AC-0009.** The Windows CI job runs
  `packs/core/tests/skills/work-loop/test_confined_mutation_windows.py` on a
  real Windows host with the host-capability mode not patched, with no case skipped, and it passes. The
  module covers AC-0001, AC-0002 with a real junction ancestor, AC-0003 with a
  hard-linked target, AC-0004, AC-0005 with a root and a target named in a
  different letter case, and with the root given as its short-name alias and
  the target in long form,
  and AC-0007 with an ancestor swapped for a real junction between the last
  pre-write check and the commit call.
- [x] **AC-0010.** `race_free_mutation()` in `_confined_mutation.py` returns
  `True` on a descriptor-walk host and `False` on every other host.
- [x] **AC-0011.** When `race_free_mutation()` returns `False`, every
  `work-supervisor.py` verb refuses with refusal code `untrusted-unsafe-host`
  and writes nothing (no file in the working tree, `<spec>/.supervisor/`, or the
  Git directory changes) when the run's code trust is untrusted or cannot be
  determined. For `start` the code trust is its `--code-trust` argument, the
  trust the call would record. For every other verb it is the `code_trust` of
  the latest pair in `delivery/approvals.jsonl` as committed at `HEAD`; a file
  absent at `HEAD`, or present but unreadable, malformed, or without a parseable
  latest pair, leaves it undetermined.
- [x] **AC-0012.** The confined-mutation tests in
  `packs/core/tests/skills/work-loop/test_security_primitives.py` pass
  unchanged.

## Accepted Risk

On a path-checked host, a same-user process can swap an ancestor for a
junction in the instant between the last pre-write check and the open,
replace, or link call, and redirect that one write outside the root. When the
swap is still in place at the post-write check, the operation raises
`denied-rollback-failed`, and the caller treats the state as unknown; the bytes
may already have landed, in the root or outside it, and are not undone. A swap
undone before the post-write check goes undetected. Supervisor directory
creation, the store directory's rename, and the recovery discard's unlink run
by path on such hosts and carry the same race.

eugenelim accepted this risk on 2026-10-29, in ADR-0152, for trusted runs only:
such a process already holds the same-user authority that
`execution-supervisor-attempt-security`'s Accepted Risk grants. Untrusted runs
refuse on such hosts (AC-0011).

## Follow-ons

none

## Assumptions

none
