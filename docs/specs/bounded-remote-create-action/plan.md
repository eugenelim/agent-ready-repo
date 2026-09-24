# Plan: bounded remote create action

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/core/.apm/skills/work-intake/scripts/refresh.py`
  — `_REMOTE_ACTIONS` at line 482, the membership checks at 716 and 1133,
  `ProcessorRegistry.resolve` and its `required_capability` parameter at 343,
  the `ConfirmationBinding` tuple at 359, and the inline capability check for
  `acquire` at 331, which is the precedent for deriving a requirement rather
  than passing one. Named deviation: every existing action annotates an item
  that already exists; none creates one.


> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/<feature>/notes/verification-ledger.md` (or the adopter's
> equivalent). A genuine artifact error follows the controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material that an implementer corrects in place only
> before approval: approval hashes the whole plan. After approval, grounding for
> a seam recorded as `no stub (implementation-discovered)` goes to the
> verification ledger; a settled design decision that execution falsified is a
> plan error that follows the controlled-amendment procedure. Treating them as
> contract is how a review spends a round on prose no gate consumes — the
> measured share is over half the plan's lines. `Grounding` stays *recorded*,
> because a per-task resolution that nobody wrote is not grounding; what it stops
> being is a claim a reviewer holds the plan to.

<!-- Existing plans without this field remain valid. Treat its absence as a
named assurance gap during structural review, not a universal lint failure. -->

<!-- **Durable-plan fill.** This template is the implementation and verification
strategy for a durable delivery slice. Fill Approach, Constraints, Risks,
Design, Tasks, and Changelog to the depth the durable work requires. Its sibling

## Approach

Two changes land together. The action joins the set, and the capability
requirement stops being a caller's option.

The second is the load-bearing one. `ProcessorRegistry.resolve` takes
`required_capability: str | None = None` and raises `unsupported_capability`
only when a caller passes one, so as shipped the gate is opt-in: any call site
that forgets the argument resolves a provider with no capability check at all.
Adding the create action to `_REMOTE_ACTIONS` makes it syntactically valid for
all four provider packs at once — membership is checked at lines 716 and 1133,
neither of which consults a capability — so an opt-in gate would mean three
packs that currently refuse all writes become reachable the moment this lands.
Deriving the requirement from the action makes omitting it impossible rather
than merely wrong, and `acquire`'s inline check at line 331 is the precedent.

All three enforcement sites move in one change. An action accepted at
validation and dropped at the confirmation binding passes two separate unit
tests and ships broken.

## Constraints

- **ADR-0077 D6-D12** and **ADR-0019 D5** set the authority boundary for
  repo-origin work; the create path carries nothing from a tracker into
  canonical authority.
- The confirmation contract is the shipped one — single-use, session-fresh,
  bound to an exact mutation tuple, gated on `remote_mutation_approver_roles`.
  This slice inherits it and adds no approver role.
- `packs/core` is repo-scope and ships to every adopter, so a widening here is
  a widening everywhere.
- No existing action's behaviour changes.

## Construction tests

- A three-site fixture exercising the action against payload validation, item
  validation and the confirmation binding in one assertion.
- A dispatch with no required capability, asserted to refuse.
- Four provider fixtures with no declared capability, each asserted to refuse
  before confirmation and before transport.
- A positive fixture against a handler double: one fresh confirmation, exactly
  one handler invocation; the same confirmation again, none.
- A regression fixture over the five existing actions.

## Durable-output map

| Output | Task | Evidence |
| --- | --- | --- |
| Create dispatch at all three enforcement sites | T1 | three-site fixture green against a handler double |
| Derived capability requirement | T2 | a dispatch with no capability refuses |
| Recorded trust boundary | T3 | `docs/architecture/security.md` names the gate and the reconciliation obligation |
| `core` changelog entry | T3 | the pack leads its own entry |

## Design (LLD)

### Design decisions

- **The capability is derived, not passed.** An opt-in gate on a shared write
  contract fails open at the first call site that forgets it, and the failure
  is silent because a resolved provider looks identical either way.
- **The confirmation displays the payload.** A digest proves the payload did
  not change between confirmation and transport; it does not tell the approver
  what they are approving.
- **The positive path is specified alongside the refusals.** A set of refusal
  criteria alone is satisfied by an action that never dispatches anything.
- **The positive path stops at the handler boundary.** Asserting that an item
  appears would pull a provider's projection and handler into a `core` slice
  that claims to ship before any provider exists, so the spec would contradict
  its own rollout.

### Data & schema

The action joins `_REMOTE_ACTIONS`. The confirmation binding gains no field;
the create's payload digest uses the existing slot.

### Interfaces & contracts

`ProcessorRegistry.resolve` stops accepting a caller-supplied capability for
this action and derives it. That is the only signature-visible change.

### Component / module decomposition

One file, `packs/core/.apm/skills/work-intake/scripts/refresh.py`, plus its
tests.

### State & control flow

Unchanged. The action is inert until a provider profile declares the
capability and supplies a handler, so this slice ships without altering any
observable behaviour.

### Behavior & rules

An action with no derivable capability is refused. A provider whose profile
does not declare the capability is refused before confirmation and before
transport.

### Failure, edge cases & resilience

A provider registration that declares the capability but supplies no handler
is refused at resolve rather than at transport, so the failure surfaces before
a confirmation is requested from a human.

### Quality attributes (NFRs)

The three-site enforcement and the four non-declaring-provider refusals are
the pass/fail bar.

### Dependencies & integration

No new dependency.

## Tasks

### T1: the create dispatch is enforced at all three sites and invokes its handler exactly once

**Depends on:** none

**Tests:**
- One fresh confirmation invokes the declared handler exactly once with the
  confirmed payload. Verifies *invokes the capability-declared handler exactly
  once*.
- Re-presenting it invokes no handler and fails. Verifies *invokes no handler
  and fails*.
- The confirmation displays the exact payload. Verifies *displays the exact
  payload*.
- The action is refused at payload validation, item validation and the
  confirmation binding, asserted together. Verifies *refuses the action at
  every one of its three enforcement sites*.
- The five existing actions are unchanged. Verifies *no existing action's
  behaviour changes*.

**Approach:**
- All three sites move in one change; splitting them is how the set accepts an
  action one site later drops.

**Done when:** the three-site fixture is green, the positive case invokes the
handler double exactly once, and the regression fixture over the existing five
is unchanged.

**Touches:** packs/core/.apm/skills/work-intake/scripts/refresh.py, packs/core/tests/skills/work-intake/*

### T2: the capability requirement is derived, and no undeclared provider is reachable

**Depends on:** T1

**Tests:**
- A dispatch supplying no required capability refuses. Verifies *a dispatch
  that supplies no required capability is refused*.
- The requirement is derived from the action, not from a caller argument.
  Verifies *derived from the action, so a resolve call cannot reach a provider
  without one*.
- With the action in the set and no profile declaring it, all four providers
  refuse before confirmation and before transport. Verifies *each refuse it
  before confirmation and before transport*.
- A provider declaring the capability with no handler refuses at resolve.
  Verifies *a provider gains the action only by declaring the capability and
  supplying a handler*.

**Approach:**
- Follows `acquire`'s inline check at line 331 rather than the optional
  parameter at 343, because the optional form is the fail-open this task
  exists to close.

**Done when:** no call path reaches a provider for this action without a
capability check, and all four providers refuse.

**Touches:** packs/core/.apm/skills/work-intake/scripts/refresh.py, packs/core/tests/skills/work-intake/*

### T3: the trust boundary is recorded and `core` leads a changelog entry

**Depends on:** T1, T2

**Tests:**
- `docs/architecture/security.md` names what authorizes the create, what it
  may write, and what an unknown outcome obliges a caller to do.
- No credential, token or cookie appears in a confirmation, receipt, log or
  serialized error. Verifies *no credential, token or cookie appears*.

**Done when:** the boundary is recorded and `packs/core/CHANGELOG.md` leads an
entry.

**Touches:** docs/architecture/security.md, packs/core/CHANGELOG.md

## Rollout

The action is inert until a provider declares the capability, so this slice
lands ahead of every provider slice without changing observable behaviour.
That is also what makes it independently shippable.

## Risks

- **The gate is left opt-in.** This is the shipped default and the reason T2
  exists; its assertion is that a dispatch with no capability refuses.
- **Widening the set widens four packs at once.** Mitigated by the derived
  capability and the four non-declaring-provider refusals.
- **A refusal-only suite hides an action that never creates.** Mitigated by
  the positive criterion in T1.

## Changelog

- 2026-09-24 — plan drafted.
