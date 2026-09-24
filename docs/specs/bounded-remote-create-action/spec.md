# Spec: bounded remote create action

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0077; ADR-0019
- **Brief:** brief:intent-backed-working-view
- **Discovery:** none
- **Contract:** none
- **Shape:** integration


> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites. Marking the tiers is the spec's job; honouring them
> when a finding is adjudicated is the reviewing surface's.

<!-- **Durable-spec fill.** This template governs work that needs a durable
behavior contract for one delivery slice. Fill Outcome, What Changes, Agent
Rules, Testing Strategy, and Acceptance Criteria to the depth the durable work
requires, and Assumptions only where something is unresolved. The sibling plan carries the implementation and verification strategy.
Eligible direct-light work does not create this artifact. -->

<!-- **Present tense, as-built.** Write every body section below as if the
feature already exists and always worked this way — no "will be", no
"previously X, now Y", no deprecation timelines, no version-stamped history.
The body describes the current contract; decision history lives in ADRs and the
release changelog. `plan.md` holds to the same rule: its `## Changelog` records
approvals, not how the approach evolved. -->


## Outcome

A delivery-system pack can dispatch a create under the same human-confirmation
boundary that already governs every other remote write, and a pack that has
not asked for that authority does not get it.
Success is that widening the shared action set widens nothing for a provider
until that provider declares the capability.

## What Changes

- The bounded remote-action set gains a create action —
  `packs/core/.apm/skills/work-intake/scripts/refresh.py`
- The capability a remote action requires is derived from the action, so a
  resolve call cannot reach a provider without one — same file
- The create action's confirmation displays the exact payload it will send —
  same file
- Provider handlers, remote items and anything a tracker actually holds stay
  with the provider slices; this spec ships the dispatch contract only

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility | Applicable — this changes a contract four provider packs route writes through, in a repo-scope pack that ships to every adopter | `packs/core/.apm/skills/work-intake/scripts/refresh.py` and its tests | this spec | the action enumerated, validated, capability-gated and confirmation-bound at all three enforcement sites | no provider accepts the action without a declared capability and a session-fresh single-use confirmation |
| Operations | Applicable — a new trust boundary in a shared write contract | `docs/architecture/security.md` | this spec | the create action's boundary recorded: what authorizes it, what it may write, what an unknown outcome means | the record names the capability derivation and the reconciliation obligation |
| Release history | Applicable — `core` changes | `packs/core/CHANGELOG.md` | this spec | one entry | the pack leads its own entry |
| Decision rationale | Not applicable — the decision to widen the set is the lifecycle owner's, recorded in the parent brief | — | — | — | — |

## Agent Rules

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Derive the capability an action requires from the action itself.
- Keep the create action's confirmation single-use, session-fresh, bound to an
  exact mutation tuple, and gated on the existing approver roles.
- Display the exact payload in the confirmation before transport.
- Move all three enforcement sites in one change.

### Ask first

- Adding a seventh action, or any approver role.
- Any change to an existing action's behaviour.

### Never do

- Treat membership of the action set as authority for a provider to run it.
- Implement a provider's handler, or assert anything about a remote item. Each
  provider slice owns its own projection, handler and end-to-end result.
- Leave the capability requirement as an optional caller argument.
  `ProcessorRegistry.resolve` takes `required_capability: str | None = None`
  today, so a call site that omits it gets no gate at all.
- Violate ADR-0019 D5 as ADR-0077 D6-D12 refine it, by letting the create path
  carry anything read off a tracker into canonical authority.
- Let a credential, token or cookie reach a confirmation, a receipt, a log, a
  serialized error or a repository artifact.

## Testing Strategy

- **Three-site enforcement: TDD, integration surface.** The action is
  exercised against payload validation, item validation and the confirmation
  binding together, because an action accepted at one site and dropped at
  another passes two separate unit tests and still ships broken.
- **Capability derivation: TDD.** A dispatch that supplies no required
  capability is asserted to refuse. The shipped gate is opt-in, so this is the
  assertion that turns it into a gate.
- **Non-declaring providers: TDD.** With the action in the set and no profile
  declaring it, each of the four providers is asserted to refuse.
- **Positive path: TDD, against a handler double.** One fresh confirmation
  invokes the declared handler exactly once with the confirmed payload;
  re-presenting it invokes nothing. A refusal-only suite is satisfied by an
  action that never dispatches anything. No test reaches a live tracker:
  whether an item appears belongs to the provider slice.

## Acceptance Criteria

- [ ] One fresh confirmation carrying approver evidence invokes the
      capability-declared handler exactly once, with the confirmed payload.
- [ ] Re-presenting that same confirmation invokes no handler and fails.
- [ ] Whether a remote item actually appears is the provider slice's
      criterion, not this one. This spec is satisfied by the dispatch, and is
      verified against a handler double rather than a live tracker.
- [ ] The confirmation displays the exact payload the create will send.
- [ ] The refresh processor refuses the action without a single-use,
      session-fresh confirmation carrying approver evidence.
- [ ] The refresh processor refuses the action at every one of its three
      enforcement sites, not only at payload validation.
- [ ] The capability an action requires is derived from the action, so a
      resolve call cannot reach a provider without one.
- [ ] A dispatch of the action that supplies no required capability is refused
      rather than resolved.
- [ ] With the action present in the set and no provider profile declaring it,
      Jira Software, Jira Align, GitHub and Linear each refuse it before
      confirmation and before transport.
- [ ] A provider gains the action only by its own profile declaring the
      capability and supplying a handler.
- [ ] No existing action's behaviour changes.
- [ ] No credential, token or cookie appears in a confirmation, a receipt, a
      log line or a serialized error.

## Follow-ons

none

## Assumptions

none
