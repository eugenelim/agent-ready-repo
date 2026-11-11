# Unattended and in-session mechanized delivery

- **Slug:** `mechanized-delivery`
- **Level:** capability
- **Owner:** eugenelim
- **Status:** Accepted
- **Accepted:** 2026-11-10 by eugenelim, lifecycle owner, after the shaping review of 2026-11-07 and with RFC-0115, RFC-0116 and RFC-0117 Accepted that day.
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** opportunity:autonomous-product-team-operating-model
- **Decomposed:** 2026-11-10 brief
- **Shaping-reviewed:** 2026-11-07
- **Related intents:** capability:external-tracker-projection, capability:work-loop-delivery-efficiency, capability:workspace-mcp-production-readiness, intent:tracker-refresh-trusted-authority-inputs, intent:loop-state-lock-cross-spec-serialization, outcome:supervisor-launch-routing-for-plan-authored-commands, intent:agent-loop-escalation-recovery, intent:role-journey-agent-swarm-section

## Outcome

Work moves from an accepted intent to a merged change with the people responsible present only at decisions, and nothing recorded is lost when a session, a process or a machine stops. Whoever starts the work can leave it running or pick it up again later, and the repository remains the only authority on what was approved.

- **Input (steerable):** The count of spec and discovery steps that resume from committed records after a forced context loss, with no manual re-derivation. A resume test or a live run shows it.
- **Outcome (lagging):** In live sessions, a real spec reaches `plan-approved` and a real discovery reaches G3. Each survives a forced context loss and stops at its human gates.
- **Guardrail:** No approval counts without a human answer record, and no tracker, worker or controller becomes a source of authority. The pinned `work-supervisor.py` is not edited (ADR-0144).

A numeric target waits for a baseline. Once the first brief has run, measure how often spec and discovery work loses context or needs hand recovery, then set one.

## Opportunity

The work-loop already mechanizes implementation through a supervisor. Shaping and spec authoring still run on prose procedure, so a lost context, a stalled review or a missing approval is recovered by hand, and nothing can carry the work forward while nobody is watching.

- **Functional job:** Take an accepted intent through spec and discovery work to a merged change without babysitting each step.
- **Emotional job:** Trust that work left running cannot approve itself or lose a step.
- **Social job:** Be seen as shipping reviewed work whose approvals are demonstrably human.
- **Struggling moment:** A review loop with no stop rule, a session that loses context mid-spec, or an unattended run that cannot be trusted to stop at a human decision.

## Assumptions

- A session agent can drive a sibling supervisor through `start`, `next` and `report`, and a fresh session resumes from `status`. Tested on a stub supervisor and on the real `work-supervisor` as a proxy across three CLIs (4 of 4 resume-capable tries), and untested on `spec-supervisor`, which does not exist yet.
- Spec and discovery procedure can be a deterministic script that routes by file state, with the judgment left to a worker session.
- A controller can classify a worker's stop reliably enough to park for a human. Spikes show stops differ across CLIs.
- An optional controller adds value on top of supervisors that already work without it.
- A restored checkpoint passes the supervisor's own integrity checks only when the restore reproduces its attempt fingerprint. Tested locally, untested against a real remote.
- **Riskiest assumption:** the first one, that a session agent drives a real sibling supervisor and resumes from `status`. Tested on a stub and on the real `work-supervisor` as a proxy across three CLIs, where the kill condition was not met. Kill condition: a fresh session fails to resume a real `spec-supervisor` run from `status` alone, reaching the same request id with no lost record, in at least two of three tries across different CLIs. If it dies, the supervisors need a controller and the first brief's premise changes. The same test on the real `spec-supervisor` remains the first slice of `everyday-supervisors-delivery`, because it needs that supervisor. No de-risk date is stamped until it runs.
- **Knowledge surface:** none detected.

## Delivery

Three delivery briefs carry the work, grouped by outcome, owner and readiness. They ship in this order: an ordinary session first, then an optional controller on one machine, then tracker approval, parallel worktrees and a remote pool.

- Everyday supervisors (`everyday-supervisors-delivery`): `spec-supervisor`, `discovery-supervisor`, their contracts, and the everyday-user path, with no controller.
- `ferryman` local (`ferryman-local-delivery`): the optional foreground controller, a light-session route, the frontier and a read-only tracker shim.
- Authority and scale (`authority-and-scale-delivery`): tracker-approved write-back, parallel worktrees and a remote pool.

The design lives in the architecture set at [`docs/architecture/unattended-delivery-runner/`](../../architecture/unattended-delivery-runner/README.md).

## Boundary

In scope: the supervisors, the optional controller, the contracts between them and the way they are installed and adopted.

Two entry doors to shaping: `intent frame` stays standalone and writes a plain intent, and `discovery-loop` is the door for raw ideas and tickets that need shaping. The discovery supervisor covers only initiatives that have a sidecar. The short route (`intent frame`, `intent de-risk`, `intent decompose`) stays in the intent skill, with progress recorded in the intent's own headers and no supervisor. A ticket becomes an intent through manual `work-intake` until `discovery-supervisor` ships. Tracker flows are two independent one-way flows, an import into the repository and a display-only mirror out, and there is no continuous two-way sync.

Out of scope:

- Changes in the Studio repository, and a generic command center.
- The brief-level runner (ADR-0159) and the run grant (RFC-0113), which other work owns. This capability consumes them.
- Direct-light work started in a live session, which stays as it is.

## Appetite

Appetite is a stopping rule per brief, not one time box for the capability. Brief 1 ships `spec-supervisor` first. Discovery is optional: people with an intent already in hand go straight to the spec step, so `discovery-supervisor` is not a dependency of `spec-supervisor`. Briefs 2 and 3 set their own appetite at their Ready review.

## Gaps

- A numeric target is not set, by choice: it waits for a baseline after the first brief runs. Appetite is set per brief, and Briefs 2 and 3 have none yet.
- Overlap with the related intents is named, and none of them has been edited. Their changes follow the architecture's acceptance.

## Decomposition

- Brief `everyday-supervisors-delivery`.
- Brief `ferryman-local-delivery`.
- Brief `authority-and-scale-delivery`.
