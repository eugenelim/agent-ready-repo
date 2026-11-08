# Brief: an optional controller that runs delivery work unattended on one machine

- **Slug:** `ferryman-local-delivery`
- **Received:** 2026-11-07
- **Owner:** eugenelim
- **Status:** Draft
- **Source / provenance:** [`docs/architecture/unattended-delivery-runner/`](../../architecture/unattended-delivery-runner/README.md), pages 03 (runtime), 03b (headless worker launch), 03c (run chain and locks), 04 (frontier), 05 (light session route) and 13 (phases P0, PL, P1 and P4). The set is a Draft architecture, uncommitted at the time of writing.
- **Parent intent:** capability:mechanized-delivery

## Outcome

A person can start `ferryman`, an optional foreground command, on one machine and leave it driving a spec, a light session or a tracker ticket through the existing supervisors. It starts one worker session per request, stops at every human gate, and resumes after a kill from committed records. The repository stays the only authority, and `ferryman` never pushes a real branch or approves anything.

## Success metrics

Not yet set. The architecture names tests rather than adopter metrics: kill-boundary and guard corpora that pass, a real spec run end to end on a scratch repository, `--demo` reaching a parked gate at no model cost, and a light request that leaves no `docs/specs/` or `workspace.toml` change. These are candidates for the Ready review, not agreed metrics.

## Scope / Non-goals

In scope:

- P0: the `ferryman` loop, workers and profiles, `doctor`, the `work-supervisor` descriptor, the gate scribe, the guard, the trusted configuration pin, locks, `init`, `clean`, `--demo` and `setup-ferryman`.
- PL: the supervisor-less light session route, `ferryman session`.
- P1: the frontier and waves, with brief-scoped order delegated to the brief-level runner when one exists.
- P4: a read-only GitHub shim for candidates, events and revisions, including the read-only candidate listing for bring-over. The bring-over itself is `work-intake` or `intake-ticket`.

Non-goals:

- The supervisors themselves (Brief `everyday-supervisors-delivery`).
- Tracker write-back, approval from a tracker, parallel worktrees and the remote pool (a later brief).
- Continuous two-way sync, ticket creation, and importing by itself.
- A scheduler of many runs, a model router, a generic command center, and any edit to the pinned `work-supervisor.py` (ADR-0144).

## Constraints / Appetite

Appetite is not set. Constraints from the architecture: `ferryman` is an optional, stdlib-only package under `packages/ferryman`, separate from the installer. It calls supervisors only through their JSON commands and consumes the manifest contract the first brief publishes. In v1 it accepts only the terminal-prompt approval, runs one run per process in one checkout, and a pool refuses a session run.

## Assumptions / Risks

- **Riskiest assumption:** a headless worker stays inside its limits across CLIs. A spike found the limits enforced unevenly across Claude Code, Copilot and Pi, and a Pi run wrote a stray file.
- **Risk:** the credential stripping in the worker launch contract may stop a CLI authenticating to its model. It is untested on any CLI.
- **Risk:** a headless light worker implements a change without independent review unless the reviewer runs inside the session.
- **Risk:** the light session route assumes a local human launch counts as an explicit trusted invocation under `light-mode.md`. The work-loop owners have not been asked.

## Ready gaps (Draft only)

- Records 11 and 12 are not Accepted.
- The light-session spike (S2) is partial and the restore spike (S1) is partial. Both need a re-run.
- The work-loop owners have not confirmed light-session eligibility.
- The distribution channel and compatibility rule for the release need a record, and the `ferryman` name needs a check before first publish.
- This brief depends on the manifest contract from `everyday-supervisors-delivery`, whose schema home is unconfirmed.
- The per-team bring-over label and the ordering default for several candidates are not set.
- Success metrics and appetite are not set.

## Rabbit holes

- Do not build a container floor. The architecture records a container executor as a later alternative.
- Do not widen the controller into a scheduler. Scheduling belongs to a pool's control plane.

## Spec map

| Spec | Status |
| --- | --- |
