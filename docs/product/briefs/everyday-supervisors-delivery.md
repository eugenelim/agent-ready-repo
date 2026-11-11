# Brief: everyday supervisors for spec and discovery work

- **Slug:** `everyday-supervisors-delivery`
- **Received:** 2026-11-07
- **Owner:** eugenelim
- **Status:** Draft
- **Source / provenance:** [`docs/architecture/unattended-delivery-runner/`](../../architecture/unattended-delivery-runner/README.md), pages 05 (supervisors and gates) and 13 (phases E0 to E3 and spike S3). RFC-0115 (mechanized delivery) and RFC-0116 (the discovery supervisor) are Accepted as of 2026-11-10, and the architecture set carries their design.
- **Parent intent:** capability:mechanized-delivery

## Outcome

A user in an ordinary interactive session, with no `ferryman` installed, drives intent-to-spec work through a new sibling supervisor, `spec-supervisor` (inside `new-spec`, repo scope, driven by `work-loop`, which stays the one front door, per ADR-0163), and, when E2 is taken, a second one, `discovery-supervisor` (shipped with `discovery-loop`). Each resumes from committed records after a context loss, caps review rounds at the policy limit (page 05 of the architecture) with a consent gate at the cap, keeps reviewers distinct from authors, and parks human gates through the existing `park` command.

## Success metrics

The brief is measured by tests, and adopter numbers wait for the baseline the capability intent names: review independence and round-cap tests, a refusal test per verb, one real spec taken from `Draft` to `plan-approved` in a live session, the kill-condition trial of the capability intent `mechanized-delivery`, run on the real `spec-supervisor` in three tries across different CLIs (it passes when the trial does not meet that kill condition, and a single failed try is recorded and its cause found before the brief closes), and, if E2 is taken, one discovery run from G0 to G3 that resumes after a context loss.

## Scope / Non-goals

In scope:

- E0: `supervisor-manifest.v1` and the shared request envelope. The core pack owns the schema and envelope (ADR-0162 D7), and each supervisor ships a manifest that conforms to it.
- E1: `spec-supervisor`.
- E2: `discovery-supervisor`, for initiatives that have a sidecar. It is optional and not a dependency of E1.
- E3: the everyday-user path: one how-to per supervisor, routing, install prerequisites, and a plain statement that `ferryman` is later and optional.

Governance references (they constrain delivery and enter no rollup): RFC-0115 and RFC-0116 (Accepted), ADR-0162 (the sibling command contract, Accepted), ADR-0163 (the spec supervisor inside `new-spec`, Accepted), and RFC-0116 D2 (two doors into shaping, with the supervisor covering only initiatives that have a sidecar) and D5 (the supervisor is optional).

Delivery slices proposed for specs, to be confirmed at the slice cut: E0 (manifest and envelope), E1 (`spec-supervisor`), E2 (`discovery-supervisor`, optional). E3 ships inside the E1 and E2 specs and is not a spec of its own: each spec carries its own supervisor's how-to, and E1 carries the shared items (routing, install prerequisites, and the statement that `ferryman` is later and optional). E2 adds only its how-to and the `discovery-supervisor` install combinations.

Non-goals:

- `ferryman`, the light session route, the frontier and the tracker shim (a later brief).
- Tracker write-back, parallel worktrees and the remote pool (a later brief).
- Any edit to the pinned `work-supervisor.py` (ADR-0144).

## Constraints / Appetite

Appetite is a stopping rule. Stop and replan when the kill condition in the capability intent `mechanized-delivery` is met. Otherwise the brief is done when its own success metrics pass (the E2 items only if E2 is taken) and each supervisor has its how-to. Constraints from the architecture: `discovery-supervisor` ships at user or repo scope and in v1 needs the core pack at repo scope, so the supported combinations are a user-scope supervisor with a repo-scope core pack, and both at repo scope. Approval follows ADR-0157 with no scribe or guard until `ferryman` runs the supervisors.

## Assumptions / Risks

- **Riskiest assumption:** a session agent can drive a real sibling supervisor and resume from `status` alone. Spike S3 passed on a stub supervisor with Claude Code, and the real `work-supervisor` served as a proxy across three CLIs. It is untested on `spec-supervisor`, which does not exist yet.
- **Risk:** without the guard, a session agent could write an approval itself. The exposure matches `work-loop` today, and the mitigation is the instruction text.
- **Owner waiver:** the repository owner, eugenelim, waives a checked identity for the session-only period. The capability guardrail says "no approval counts without a human answer record", and this brief reads "human" as implying a checked identity. In a plain session `answer` needs a controlling terminal and records an unverified `--by` name, so the record exists and the identity is not checked. The capability intent does not record this waiver, and this brief is its record. The waiver ends when `ferryman`'s guard and scribe run the supervisors, in brief `ferryman-local-delivery`.
- **Risk:** a session agent does not dispatch a distinct reviewer unprompted, so review independence rests on instruction text and the supervisor's `weak` flag.
- **Open for the E2 slice:** the E2 spec decides how session `answer`, the tier ledger and `intake-confirm` behave in a plain session, and starts from page 05 of the architecture. Until `discovery-supervisor` ships, a ticket becomes an intent through manual `work-intake`.
- **Open for the E1 slice:** a stronger human-attribution check than the `answer --by` flag is not designed, and the `answer` record states the identity is unverified. Page 05 reads review independence in a session as distinct agent definitions, and the spec confirms it.

## Rabbit holes

- Do not design the unattended controller here. These supervisors must work without it and run unchanged under it later.
- Do not widen the work into tracker intake or approval from a tracker. Those need record 18 (the ADR that lets a verified human's recorded approve count) and belong to a later brief.

## Spec map

| Spec | Status |
| --- | --- |
