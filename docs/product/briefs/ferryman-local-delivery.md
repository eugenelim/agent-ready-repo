# Brief: an optional controller that runs delivery work unattended on one machine

- **Slug:** `ferryman-local-delivery`
- **Received:** 2026-11-07
- **Owner:** eugenelim
- **Status:** Draft
- **Source / provenance:** [`docs/architecture/unattended-delivery-runner/`](../../architecture/unattended-delivery-runner/README.md), pages 03 (runtime), 03b (headless worker launch), 03c (run chain and locks), 04 (frontier), 05 (light session route) and 13 (phases P0, PL, P1 and P4). RFC-0115 (mechanized delivery) and RFC-0117 (approval and the trust model, which owns the scribe, guard and trusted configuration) are Accepted as of 2026-11-10, and the architecture set carries their design.
- **Parent intent:** capability:mechanized-delivery

## Outcome

A person can start `ferryman`, an optional foreground command, on one machine and leave it driving a spec, a light session or a tracker ticket through the existing supervisors. It starts one worker session per request, stops at every human gate, and resumes after a kill from committed records. The repository stays the only authority. `ferryman` pushes no branch (on one machine it writes only checkpoint refs under `refs/ferryman/`) and approves nothing.

## Success metrics

The brief is measured by tests, and adopter numbers wait for the baseline the capability intent names: kill-boundary and guard corpora that pass, a real spec run end to end on a scratch repository, `--demo` reaching a parked gate at no model cost, and a light request that leaves no `docs/specs/` or work-registry change. These tests are also the done condition.

## Scope / Non-goals

In scope:

- P0: the `ferryman` loop, workers and profiles, `doctor`, the `work-supervisor` descriptor, the gate scribe, the guard, the trusted configuration pin, locks, `init`, `clean`, `--demo` and `setup-ferryman`.
- PL: the supervisor-less light session route, `ferryman session`, delivered together with a named slice that changes `light-mode.md` to record a local, human-launched `ferryman session` as an explicit trusted invocation. The work-loop owners own the slice, and it needs a core version bump and an eval-harness update.
- P1: the frontier and waves, with brief-scoped order delegated to the brief-level runner when one exists.
- P4: a read-only GitHub shim for candidates, events and revisions, including the read-only candidate listing for bring-over. The bring-over itself is the discovery supervisor's `intake-ticket` request from `everyday-supervisors-delivery`, or manual `work-intake` until that ships.

Non-goals:

- The supervisors themselves (Brief `everyday-supervisors-delivery`).
- Tracker write-back, approval from a tracker, parallel worktrees and the remote pool (a later brief).
- Continuous two-way sync, ticket creation, and importing a ticket that no human selected.
- A scheduler of many runs, a model router, a generic command center, and any edit to the pinned `work-supervisor.py` (ADR-0144).

## Constraints / Appetite

Appetite is a stopping rule. Stop and replan if a headless worker cannot authenticate to its model with credentials stripped on any one of the CLIs whose profiles P0 ships (the P0 spec names them, and the spikes covered Claude Code, Codex, Copilot and Pi), or if the guard corpus cannot be made to pass. Otherwise the brief is done when its success tests pass. Constraints from the architecture: `ferryman` is an optional, stdlib-only package under `packages/ferryman`, separate from the installer. It calls supervisors only through their JSON commands and consumes the `supervisor-manifest.v1` contract that `everyday-supervisors-delivery` publishes. In v1 it accepts only the terminal-prompt approval, runs one run per process in one checkout, and runs no pool.

## Assumptions / Risks

- **Riskiest assumption:** a headless worker stays inside its limits across CLIs. A spike found the limits enforced unevenly across Claude Code, Copilot and Pi, and a Pi run wrote a stray file.
- **Risk:** the credential stripping in the worker launch contract may stop a CLI authenticating to its model. It is untested on any CLI.
- **Risk:** a headless light worker implements a change without independent review unless the reviewer runs inside the session.
- **Risk:** the light session route assumes a local human launch counts as an explicit trusted invocation under `light-mode.md`. The repository owner decided it does. The work-loop owners own that file and have not confirmed it, so PL ships only when the work-loop-owned slice that changes it lands.
- **Open before P0:** four ADRs are written and Accepted first: record 11a (what an approval is), record 11b (the gate scribe), record 12 (the trusted configuration pin) and record 19 (distribution and the version rule). The `ferryman` name is checked, with trademark, before the first publish.
- **Open before PL:** the work-loop owners confirm light-session eligibility, and the `light-mode.md` slice gets a spec, with its core version bump and eval-harness update.
- **Spikes:** the restore spike (S1) and the light-session spike (S2) were partial and need a re-run against real supervisors.
- **Unset:** the per-team bring-over label and the ordering default for several candidates.

## Rabbit holes

- Do not build a container floor. The architecture records a container executor as a later alternative.
- Do not widen the controller into a scheduler. Scheduling belongs to a pool's control plane.

## Spec map

| Spec | Status |
| --- | --- |
