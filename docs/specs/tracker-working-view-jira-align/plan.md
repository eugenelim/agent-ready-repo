# Plan: tracker working view jira align

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/atlassian/.apm/skills/jira-align/SKILL.md`
  (REST 2.0 record read and creation across epics, features, stories,
  capabilities, themes, portfolios);
  `packs/atlassian/.apm/skills/jira-align-refresh/SKILL.md` (the fail-closed
  processor this slice leaves alone);
  `docs/specs/tracker-working-view-jira-software/` (the pattern). Named
  deviation: this is the only slice with no return leg, so the pattern's
  projection half is exercised alone.


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

Jira Align is the deep target: it expands where Linear collapses, and the two
product rungs land above the portfolio Epic rather than being folded into it.
That makes this slice the one that proves ADR-0125's range in the expanding
direction, which no other slice does.

It is also the only slice with no return leg. The Jira Align refresh processor
refuses write-back by design, because the client exposes generic record updates
rather than a bounded action set. This slice does not change that. The refusal
is instead pinned by a test, so a later change that quietly makes the processor
writable fails here rather than shipping.

The riskiest part is vocabulary. A Jira Align Feature and a Jira Software Epic
may be the same object across a sync, and the shipped profile table asserts
they are while the survey records the claim as unverified. The projection
therefore names the tier a rung landed on rather than relying on the word, so
the ambiguity cannot silently merge two rungs.

## Constraints

- **ADR-0125** D1 through D4a fix what projects and how far; D3 and D5 are
  non-waivable. This slice exercises D3's expanding direction.
- **ADR-0019 D5**, as **ADR-0077 D6-D12** refine it, keeps this one-way for
  repo-origin work.
- **ADR-0033 D2** makes `Level` an open set, so an unmapped rung is named
  rather than derived.
- **CAP-0004's guardrail** forbids a daemon, control plane, database or
  scheduler.
- The Jira Align refresh processor stays fail-closed. Giving it a bounded
  action set is separate work with no spec.
- The pattern the Jira Software slice sets is an input, not a subject.

## Construction tests

- An expansion fixture with a tree shallower than Jira Align's depth,
  asserting the unused tiers stay empty rather than gaining an invented rung.
- A product-rung assertion: both land above the portfolio Epic.
- An idempotency fixture: same tree twice, then one rung renamed.
- A refusal assertion: a return-leg action against Jira Align refuses and the
  refusal names the fail-closed processor. This pins behaviour the slice
  depends on but does not build.

## Durable-output map

| Output | Task | Evidence |
| --- | --- | --- |
| Jira Align projection across the tier set | T1 | reference-tree and product-rung assertions green |
| Bounded record creation | T1a | refusal plus one positive case |
| Derived repository scope | T1b | both sides of the brief rule exercised |
| Fail-closed refusal pinned | T2 | refusal test green |
| `atlassian` changelog entry | T2 | the pack leads its own entry |

## Design (LLD)

### Design decisions

- **The tier is named, the word is not trusted.** Because the same word names
  different tiers in adjacent Atlassian products, a projected record records
  which Jira Align tier it occupies. That makes the unverified Feature-to-Epic
  equivalence unable to merge two rungs by accident.
- **Empty tiers stay empty.** A tree shallower than the provider is not padded.
  Inventing a rung to fill a tier would put an object on the board that no
  canonical artifact backs, which is the board-doubling failure in a different
  costume.
- **The fail-closed refusal is tested, not changed.** A slice that depends on a
  refusal and does not assert it inherits a silent regression.

### Data & schema

The profile table's Jira Align column is the schema. The projection payload
carries the canonical identity, the rung's `Level`, and the resolved tier name.

### Interfaces & contracts

No new interface. Record creation uses the shipped Jira Align client through
the pattern slice's bounded create action and its confirmation binding.

### Component / module decomposition

Everything lands in `packs/atlassian/`. The action set is the pattern slice's,
and `jira-align-refresh` is untouched.

### State & control flow

Invocation reads the tree, resolves each rung against the profile row, and
emits a confirmation request per record. No resident state: the back-reference
on the remote record is the only durable link.

### Behavior & rules

A rung whose `Level` has no row is named as unmapped rather than guessed. A
rung below the floor produces a trace link on the floor record or nothing. A
same-repository delivery brief produces nothing. The Capability and Solution
tiers apply to multi-ART programmes and are used only when asked for.

### Failure, edge cases & resilience

A refused confirmation aborts that record and leaves the rest untouched. A
back-reference pointing at a deleted record is reported rather than
re-created. A return-leg action refuses before any payload is constructed,
which is the processor's existing behaviour and is asserted rather than
assumed.

### Quality attributes (NFRs)

The board-doubling guardrail carries the pass/fail bar, measured as a record
count against the programme's existing portfolio at the first projection.

### Dependencies & integration

A Jira Align credential through the broker, already this pack's stated
requirement. No new dependency.

## Tasks

### T1: the reference tree expands across Jira Align's tiers with a resolvable rollup

**Depends on:** spec:tracker-projection-profile-table/T2, spec:bounded-remote-create-action/T2

**Tests:**
- The reference tree yields one record per in-range rung down to the floor;
  zero records fails. Verifies *one record for every rung in the range*.
- The rollup resolves from floor to top across the tiers. Verifies *the rollup
  resolves across the Jira Align tiers*.
- Expansion mapping across Theme, Epic, Feature and Story, with each record
  recording its tier name. Verifies *records the Jira Align tier it occupies*.
- Both product rungs land above the portfolio Epic. Verifies *project above the
  portfolio Epic*.
- A shallower tree leaves unused tiers empty. Verifies *leaves the unused tiers
  empty*.
- Back-references resolve from both ends, and the same tree twice changes no
  record count.
- An agent-internal unit produces no managed object.

**Approach:**
- One reference tree carries every rung, so an exclusion cannot be satisfied by
  a projector that emits nothing.

**Done when:** every fixture is green and no projected record occupies a tier
no canonical rung resolved to.

**Touches:** packs/atlassian/.apm/skills/**

### T1a: record creation refuses without an exact, single-use confirmation

**Depends on:** spec:bounded-remote-create-action/T2

**Tests:**
- Creation without a session-fresh confirmation showing the exact payload
  refuses. Verifies *record creation refuses without a confirmation*.
- One fresh confirmation creates exactly one intended record. Verifies *one
  fresh confirmation creates exactly one record*.

**Approach:**
- Asserted per provider rather than inherited from the pattern slice, because
  Jira Align's client exposes generic record updates and a provider-level
  refusal is what keeps the create bounded here.

**Done when:** both the refusal and the single positive case hold.

**Touches:** packs/atlassian/.apm/skills/**

### T1b: repository scope is derived, and both sides of the brief rule are exercised

**Depends on:** T1

**Tests:**
- Scope derives from the canonical artifact's repository and the target's, with
  no static list. Verifies *repository scope is derived*.
- A same-repository brief produces no object; a cross-repository brief produces
  exactly one managed record. Verifies both brief criteria.

**Approach:**
- Both sides together. The exclusion alone is satisfied by dropping every
  brief.

**Done when:** the paired fixture passes on both sides.

**Touches:** packs/atlassian/.apm/skills/**

### T2: the fail-closed return-leg refusal is pinned

**Depends on:** none

**Tests:**
- A return-leg action against Jira Align refuses, and the refusal names the
  processor as fail-closed. Verifies *a return-leg action refuses*.

**Approach:**
- The assertion lives with this slice rather than with the processor, because
  this is the slice whose scope depends on the refusal holding.

**Done when:** the refusal test is green and `packs/atlassian/CHANGELOG.md`
leads an entry.

**Touches:** packs/atlassian/tests/**, packs/atlassian/CHANGELOG.md

## Rollout

T2 is independent of T1 and can land first, since it only pins existing
behaviour. Each task is independently revertible.

## Risks

- **The unverified Feature-to-Epic equivalence.** Mitigated by recording the
  tier rather than trusting the word; the claim stays open in the spec's
  assumptions and only an adopter with a live sync can settle it.
- **A later change makes the refresh processor writable.** T2's assertion is
  the detector.
- **Padding an empty tier looks like completeness.** The empty-tier fixture
  asserts the absence, because a reviewer reading a full-looking portfolio
  cannot tell an invented rung from a real one.

## Changelog

- 2026-09-24 — plan drafted.
