# Brief: everyday supervisors for spec and discovery work

- **Slug:** `everyday-supervisors-delivery`
- **Received:** 2026-11-07
- **Owner:** eugenelim
- **Status:** Draft
- **Source / provenance:** [`docs/architecture/unattended-delivery-runner/`](../../architecture/unattended-delivery-runner/README.md), pages 05 (supervisors and gates) and 13 (phases E0 to E3 and spike S3). The set is a Draft architecture, uncommitted at the time of writing.
- **Parent intent:** capability:mechanized-delivery

## Outcome

A user in an ordinary interactive session, with no `ferryman` installed, drives intent-to-spec work through two new sibling supervisors: `spec-supervisor` (inside `new-spec`, repo scope, driven by `work-loop`, which stays the one front door) and `discovery-supervisor` (shipped with `discovery-loop`, user or repo scope). Each resumes from committed records after a context loss, caps review rounds at 3 with a consent gate at the cap, keeps reviewers distinct from authors, and parks human gates through the existing `park` command with approval following ADR-0157.

## Success metrics

Not yet set. The architecture names tests rather than adopter metrics: review independence and round-cap tests, a refusal test per verb, one real spec taken from `Draft` to `plan-approved` in a live session, and one discovery run from G0 to G3 that resumes after a context loss. These are candidates for the Ready review, not agreed metrics.

## Scope / Non-goals

In scope:

- E0: records for the command contract and the spec supervisor, the discovery-supervisor RFC, `supervisor-manifest.v1` and the shared request envelope, and the architecture record of the discovery front-door decision (D3).
- E1: `spec-supervisor`.
- E2: `discovery-supervisor`, for initiatives that have a sidecar. It is optional and not a dependency of E1. It writes the ledger of its tier in a plain session as under `ferryman`. In a session `answer` needs a controlling terminal and records an unverified identity, `intake-confirm` is refused, and a ticket becomes an intent through manual `work-intake`.
- E3: the everyday-user path: one how-to per supervisor, routing, install prerequisites, and a plain statement that `ferryman` is later and optional.

Non-goals:

- `ferryman`, the light session route, the frontier and the tracker shim (a later brief).
- Tracker write-back, parallel worktrees and the remote pool (a later brief).
- Any edit to the pinned `work-supervisor.py` (ADR-0144).

## Constraints / Appetite

Appetite is not set. Constraints from the architecture: the core pack owns `supervisor-manifest.v1` (the page 05 default, unconfirmed), `discovery-supervisor` requires the core pack at repo scope in v1, and approval follows ADR-0157 with no scribe or guard until `ferryman` runs the supervisors. Spike S3 passed on a stub supervisor with Claude Code (a session agent drove it, parked a gate, and a fresh session resumed from `status`). It did not run against the real supervisors or other CLIs.

## Assumptions / Risks

- **Riskiest assumption:** a session agent can drive a real sibling supervisor and resume from `status` alone. Tested on a stub and on the real `work-supervisor` as a proxy across three CLIs. Untested on `spec-supervisor`, which does not exist yet.
- **Risk:** without the guard, a session agent could write an approval itself. The exposure matches `work-loop` today, and the mitigation is ADR-0157 plus the instruction text.
- **Risk:** a session agent does not dispatch a distinct reviewer unprompted, so review independence rests on instruction text and the supervisor's `weak` flag.

## Ready gaps (Draft only)

- Records 3 and 4 and the discovery RFC are not written or Accepted.
- The home of `supervisor-manifest.v1` is unconfirmed.
- What review independence means in a session is undecided.
- A stronger human-attribution check than the `answer --by` flag is not designed. The `answer` record states that the identity is unverified.
- Whether the supervisor refuses a gate answer that has no human record is an open item for E1.
- Success metrics and appetite are not set.

## Rabbit holes

- Do not design the unattended controller here. These supervisors must work without it and run unchanged under it later.
- Do not widen the work into tracker intake or approval from a tracker. Those need record 18 and belong to a later brief.

## Spec map

| Spec | Status |
| --- | --- |
