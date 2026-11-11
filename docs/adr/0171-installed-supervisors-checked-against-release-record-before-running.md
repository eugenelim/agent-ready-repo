# ADR-0171: `ferryman` checks installed supervisors against a release-time record before running them, and confines its own files

- **Status:** Proposed
- **Date:** 2026-11-10
- **Areas:** install, security
- **Reversibility:** high
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** RFC-0115 (the proposal this records; its D3 requires the release-time comparison); ADR-0144 (the self-verifying supervisor); ADR-0164 (the program); ADR-0182 (the version and compatibility rule); ADR-0162 (the supervisor contract)

## Context

`ferryman` must run where `agentbundle` is absent, so it cannot import the installer or its blessed `file_safety` helpers. Two copies of a supervisor exist: the installed one and one packaged inside `agentbundle`. A check against digests taken at `ferryman`'s own first start would trust whatever was on disk then. Reversal needs no migration, because the design adds no installed state.

## Decision

We will have `ferryman` refuse any supervisor or manifest file that does not match a release-time record, and carry its own detection and file helpers.

- **D1:** Before running a repository-resident supervisor or manifest, `ferryman` compares each file's SHA-256 with a release-time record and refuses on a mismatch. The candidate record is the per-file digest in the install state (`PackState.file_sha`). `ferryman` never checks a copy only against digests taken at its own first start.
- **D2:** The pin taken at the first admitted `start` stays as a second, inner check, which the supervisor runs on its own installed files.
- **D3:** The install state is writable by the same user. The check catches an edited supervisor, not a worker that also rewrites the record. A digest published with the catalogue release is a stronger root and is an open design item.
- **D4:** `ferryman` runs the installed copy, with repository scope preferred and user scope allowed for `discovery-supervisor`. It never runs the copy packaged inside `agentbundle`.
- **D5:** `ferryman` builds supervisor argv only from its built-in per-version descriptors, never from manifest text. A skill version with no descriptor parks `unknown-descriptor`.
- **D6:** `ferryman` detects packs by reading install state with `tomllib`. The reader is read-only, accepts schema version 0.4 or 0.5, and refuses any other as `unsupported-state-schema`. It maps an adapter to its skill home with its own table.
- **D7:** `ferryman` never imports `agentbundle` and installs nothing. A missing pack ends in a refusal that names the command the user runs.
- **D8:** `ferryman` carries its own confined-file helpers. They refuse links, reparse points, hard-linked or non-regular files, oversize files, out-of-root paths, and files whose identity changed between open and read.
- **D9:** The peer worktree root has mode 0700, `ferryman` refuses a symlinked or foreign-owned component, and every path under it derives from the owner id alone.
- **D10:** Core at repo scope is the supported v1 install. The version and compatibility rule is decided in ADR-0182.

## Consequences

**Positive:**
- An edited supervisor or manifest is refused before it runs.
- Installer and runtime stay separate.

**Negative:**
- The helpers are copies and can drift until the equal-behaviour test exists.
- A newer install-state version makes `ferryman` refuse until its allowlist updates. Whether `agentbundle` writes versions beyond 0.5 is unverified.

**Revisit if:** a release-published digest becomes available, or a non-core supervisor must be supported.

## Confirmation

- **Mode:** lint/CI
- **Signal:** a test edits one installed supervisor or manifest file and expects a refusal, an import-graph test finds no `import agentbundle`, and a fixture refuses state version 0.6. An equal-behaviour test in the repository's tests, comparing `_file_safety` with `file_safety` on hostile fixtures, is required and not yet written.
- **Owner:** eugenelim

## Alternatives considered

- **Run the packaged copy:** it bypasses the installed pin check and splits `ferryman` from the copy the run was admitted under.
- **Import `agentbundle`:** it ties the runtime to the installer.
- **A first-start pin only:** it trusts the copy on disk at that moment, which RFC-0115 D3 forbids.
- **Trust the checkout without confinement:** a link or swapped file could steer a read or write.

## References

- `docs/rfc/0115-mechanized-delivery.md`
- `docs/architecture/unattended-delivery-runner/02-install-trust-and-detection.md`
- `docs/architecture/unattended-delivery-runner/08-worktree-and-concurrency.md`
