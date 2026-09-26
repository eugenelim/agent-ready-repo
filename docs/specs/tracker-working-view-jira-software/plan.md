# Plan: tracker working view jira software

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/core/.apm/skills/work-intake/scripts/refresh.py`
  (the bounded remote-action contract and its confirmation machinery);
  `packs/atlassian/.apm/skills/jira-story-triage/` and
  `packs/atlassian/.apm/skills/jira-refresh/` (the two shipped confirmed-write
  precedents);
  `packs/product-engineering/.apm/skills/decompose-intent/references/tracker-projection.md`
  (the profile table this reconciles); `docs/adr/0127-managed-unit-floor-and-projected-range.md`.
  Named deviation: the sixth remote action has no precedent — every existing
  action annotates an item that already exists.

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

This slice makes the outcome real on Jira Software, end to end: the reference
tree projects onto a board, the projection stays idempotent against a board
the team already uses, and the return leg writes shaped intent onto items they
already hold. It also documents the pattern the other three delivery systems
conform to.

Two inputs arrive from their own slices. The classified profile table comes
from `tracker-projection-profile-table`, and the bounded create action and its
derived capability gate come from `bounded-remote-create-action`. This slice
declares the Jira Software capability and supplies its handler.

The riskiest part is the first projection against a populated board. The
projection key is derived from the canonical artifact before anything is sent,
and the repository-owned mapping — not text found on a Jira item — decides
whether a rung is already projected, because a back-reference is something
anyone with Jira write access can write.

No test writes to Jira. The projection is exercised against fixtures; the live
write path is evidenced by a recorded confirmation transcript.

## Constraints

- **ADR-0127** D1 through D4a fix what projects and how far, and D3 and D5 are
  non-waivable on every delivery system. The plan implements the range and does
  not reopen the floor.
- **ADR-0019 D5**, as **ADR-0077 D6-D12** refine it, keeps this one-way for
  repo-origin work: nothing read off Jira acquires authority.
- **ADR-0033 D2** makes `Level` an open set, so an unmapped rung is named
  rather than derived.
- **CAP-0004's guardrail** forbids a daemon, control plane, database or
  scheduler. Projection runs when invoked.
- The refresh processor's confirmation is single-use, session-fresh and
  approver-role-gated. The sixth action inherits it unchanged rather than
  defining its own.
- Delivery-system packs install at user scope and stay independently
  installable. Nothing here makes one provider pack depend on another.

## Construction tests

- The profile-table runner resolves every row against ADR-0127 and fails on a
  below-floor managed object. It runs over the table file, so it keeps working
  when a later slice adds a column.
- A projection fixture pair — a tree and its expected Jira rendering — drives
  the mapping functions, including the collapse case where the tree is deeper
  than Jira's three levels.
- An idempotency fixture projects the same tree twice and asserts the item
  count is unchanged, then renames one rung and asserts the count is still
  unchanged.
- A refresh-processor test exercises the sixth action against all three
  enforcement sites in one assertion, because a set entry accepted at
  validation and dropped at the confirmation binding passes two separate unit
  tests and still ships broken.

## Durable-output map

| Output | Task | Evidence |
| --- | --- | --- |
| Classified, reconciled profile table with the Jira Software column | T1 | the goal-based runner exits clean |
| Sixth bounded remote action | T2 | three-site enforcement test green |
| Jira projection | T3 | mapping and idempotency fixtures green |
| Jira return leg | T4 | recorded confirmation transcript |
| Pattern architecture document | T5 | every variation point named |
| Changelog entries for `core`, `atlassian`, `product-engineering` | T5 | one entry per changed pack |

## Design (LLD)

### Design decisions

- **The projection key is repository-derived; the remote back-reference is a
  claim.** Deriving the key from the canonical artifact before any request is
  what stops the board doubling. Using the text found on a Jira item as the
  key would let anyone with Jira write access mint a matching item and
  redirect or suppress a projection, so the repository-owned mapping is the
  authority and the remote value is verified against it.
- **The sixth action goes in the shared set rather than in each provider
  pack.** Linear's own rule sends confirmed write-back through the configured
  refresh processor, so four ad-hoc create paths would mean deleting that rule
  in one pack rather than extending the mechanism it names. One action in the
  shared set gives four providers one reviewed boundary.
- **Below the floor renders as a trace or not at all.** ADR-0127 D4 permits a
  readable trace object provided it is neither managed nor counted, so the
  rendering is a link on the floor item rather than a child object.

### Data & schema

The profile table is the schema. A row maps a canonical rung to a per-provider
object, and the two new columns extend it rather than replacing its shape. The
projection payload carries the canonical identity, the rung's `Level`, and the
target object type resolved from that row.

### Interfaces & contracts

The sixth remote action is the only interface this slice adds. It takes the
same confirmation binding as the five that exist — an exact mutation tuple,
single-use, session-fresh, approver evidence — and adds no new approver role.

### Component / module decomposition

Profile table in `product-engineering`; action set in `core`; projection and
return leg in `atlassian`. Nothing crosses from one provider pack to another.

### State & control flow

Invocation reads the tree, resolves each rung against the profile, and emits a
confirmation request per item. There is no resident state: the back-reference
carried on the remote item is the only durable link, which is what lets a later
run be idempotent without a local database.

### Behavior & rules

A rung whose `Level` has no row is named as unmapped rather than guessed. A
rung below the floor produces a trace or nothing. A same-repository delivery
brief produces nothing at all.

### Failure, edge cases & resilience

A refused confirmation aborts that item and leaves the rest of the projection
untouched, because a partial projection is recoverable and a half-confirmed
mutation is not. A back-reference pointing at an item that no longer exists is
reported rather than re-created, since silently re-creating it is how a
deleted-on-purpose item comes back.

### Quality attributes (NFRs)

The board-doubling guardrail is the one with a pass/fail bar, and it is
measured as an item count against the team's existing board at the first
projection.

### Dependencies & integration

No new dependency. The Jira transport, the confirmation machinery and the
profile table all ship today.

## Tasks

### T3: the reference tree projects onto an empty board with a resolvable rollup

**Depends on:** spec:tracker-projection-profile-table/T2, spec:bounded-remote-create-action/T2

**Tests:**
- Projecting the reference tree onto an empty Jira project yields one object
  per in-range rung and none for an out-of-range rung; zero objects fails.
  Verifies *one Jira object for every rung in the range*.
- The rollup resolves from floor to top through each carrier. Verifies *the
  rollup resolves through each carrier*.
- Back-references resolve from both ends. Verifies *names the canonical
  artifact* and *a repository reader can determine which item*.
- A spec, plan, wave, task, subagent job or retry produces no managed object.
  Verifies *no Jira object that is scheduled, assigned or counted*.

**Approach:**
- The reference tree is the one fixture the positive criteria rest on, and it
  carries every rung in the range plus one below the floor, so an exclusion
  cannot be satisfied by emitting nothing.

**Done when:** the reference projection produces the expected object per rung
and the rollup walk reaches the top.

**Touches:** packs/atlassian/.apm/skills/**

### T4: projecting onto a populated board creates no duplicate and refuses an unkeyed collision

**Depends on:** T3

**Tests:**
- Projecting onto a board already holding the team's items yields no second
  managed object where the repository mapping already records one. Verifies
  *no second managed object*.
- The projection searches the target for its own key and adopts a match rather
  than creating. Verifies *adopts an existing match instead of creating*.
- A rung whose counterpart exists without a back-reference refuses, named,
  before any mutation. Verifies *refuses that rung and names it*.
- Same tree twice changes no item count; a renamed rung updates in place.
  Verifies the two idempotency criteria.

**Approach:**
- The populated-board case is separate from idempotency because idempotency
  only covers rungs this projector already created. The first run against a
  team's existing board is where the guardrail actually fails.

**Done when:** the populated-board fixture creates nothing, and the unkeyed
collision refuses before any write.

**Touches:** packs/atlassian/.apm/skills/**

### T4a: repository scope is derived, and both sides of the brief rule are exercised

**Depends on:** T3

**Tests:**
- Scope is derived from the canonical artifact's owning repository and the
  target's, with no hand-maintained list. Verifies *repository scope is
  derived*.
- A same-repository delivery brief produces no object. Verifies *produces no
  Jira object of any kind*.
- A cross-repository delivery brief produces exactly one managed object.
  Verifies *produces exactly one managed Jira object*.

**Approach:**
- Both sides are asserted together. The exclusion alone is satisfied by
  dropping every brief.

**Done when:** the paired fixture passes on both sides and the derivation reads
no static list.

**Touches:** packs/atlassian/.apm/skills/**

### T4b: the create path is credential-confined, field-closed and capability-gated

**Depends on:** spec:bounded-remote-create-action/T1

**Tests:**
- Credentials resolve only through `credbroker` into the existing `jira`
  client; a direct environment read, dotfile read or raw HTTP call fails.
  Verifies *resolve only through `credbroker`*.
- A dispatch supplying no required capability is refused rather than resolved.
  Verifies *a dispatch that supplies no required capability is refused*.
- A create payload with a field outside the closed schema is rejected before
  transport. Verifies *a field not in that schema is rejected*.
- A create carrying a protected field the confirmation did not display is
  refused. Verifies *refused unless that exact field is explicitly mapped*.
- The Jira Software profile declares the create capability and supplies a
  handler, and refuses before it does. Verifies *the Jira Software profile
  declares the create capability*.
- No token or cookie appears in a confirmation, receipt, log or serialized
  error. Verifies *no credential, token or cookie appears*.

**Approach:**
- The capability gate reuses the processor's existing machinery, but not as
  shipped. `ProcessorRegistry.resolve` takes `required_capability: str | None
  = None` and only raises `unsupported_capability` when a caller passes one, so
  the gate is opt-in and a call site that omits it fails open. The required
  capability is therefore derived from the action rather than supplied by the
  caller, which makes omitting it impossible instead of merely wrong.
- Adding a name to `_REMOTE_ACTIONS` makes it syntactically valid for all four
  providers at once — membership is checked at lines 716 and 1133, neither of
  which consults a provider capability — so three providers must stay refusing
  until their own slice declares it.

**Done when:** the three non-declaring providers refuse, the closed schema
rejects an unmapped field, and a credential scan over rendered output is
clean.

**Touches:** packs/atlassian/.apm/skills/**

### T4c: hostile tracker text takes no direction and an interrupted create never duplicates

**Depends on:** T4

**Tests:**
- A Jira item whose title and description carry instruction-shaped text is
  read through the return leg and directs nothing. Verifies *cannot select the
  action, the target item, the destination project, the profile, a field, the
  credential, the approval policy, or the content of a confirmation*.
- Jira text travels the `invoke_refresh` path with `normalized-intake.v1`
  validation and `intake_guard` redaction, delimited as untrusted. Verifies
  *carried as data through the canonical `invoke_refresh` path*.
- Faulting before send, after send, and before the response is recorded: each
  records an unknown outcome, exits non-zero, and a re-run adopts rather than
  duplicates. Verifies the three unknown-outcome criteria.
- An item carrying a back-reference the repository mapping does not record is
  refused and named; two items claiming one artifact are both refused.
  Verifies the two spoofing criteria.

**Approach:**
- Fault injection is the only way to reach the lost-response case. A
  single-use confirmation stops a replayed token and does nothing about a
  create Jira completed and we never recorded.
- Reconciliation searches the target for the repository-derived key rather
  than keeping local durable state, which would need storage CAP-0004's
  guardrail forbids.

**Done when:** all three fault points leave no duplicate on re-run, and the
hostile-text fixture changes no decision.

**Touches:** packs/atlassian/.apm/skills/**

### T5: the return leg writes shaped intent without touching a protected field

**Depends on:** spec:bounded-remote-create-action/T1

**Tests:**
- A return-leg write leaves the `jira-story-triage` protected set unchanged.
  Verifies *leaves the protected set unchanged*.

**Approach:**
- Extends the shipped `jira-story-triage` confirmation surface rather than
  adding a second one, because it already shows exact fields, prior values and
  the protected set.

**Done when:** a recorded confirmation transcript shows the protected set
untouched.

**Touches:** packs/atlassian/.apm/skills/**

### T6: the pattern is documented and every changed pack leads a changelog entry

**Depends on:** T3, T4, T4a, T4b, T4c, T5

**Tests:**
- The architecture document names each variation point and the branch each of
  the four delivery systems takes. Verifies *the architecture document names
  every variation point*.

**Done when:** the document exists at its resolved destination and `core`,
`atlassian` and `product-engineering` each lead their own changelog entry.

**Touches:** docs/architecture/**, packs/*/CHANGELOG.md

## Rollout

Each task is independently revertible. The sixth action is inert until a
provider processor accepts it, so T2 can land ahead of T3 without changing any
existing behaviour.

## Risks

- **The create action doubles a board.** Mitigated by the back-reference as
  projection key and the idempotency criteria, and measurable at the first
  real projection.
- **Widening the shared action set widens it for every provider at once.**
  Mitigated by a capability gate derived from the action. The shipped gate is
  opt-in — `required_capability` defaults to `None` — so leaving it as a caller
  obligation would fail open at the first call site that forgot it.
- **A create Jira completed but we never recorded.** Mitigated by pre-send key
  derivation, a pre-create search, and an unknown outcome that exits non-zero
  rather than retrying. The residual risk is Jira's indexing delay, recorded as
  an open assumption.
- **The profile table is edited by four slices in sequence.** The runner reads
  the file rather than a fixed column list, so a later column cannot silently
  escape the check — provided each new cell carries its classification, which
  the one-spelling-one-classification assertion enforces.

## Changelog

- 2026-09-24 — plan drafted.
