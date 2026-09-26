# Plan: delivery state observation

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/atlassian/.apm/skills/jira/SKILL.md` (JQL
  search, issue and changelog reads); `packs/atlassian/.apm/skills/flow-metrics/SKILL.md`
  (the incumbent metric vocabulary any cross-system meaning reconciles with,
  and Jira-only by pack); `packs/github/.apm/skills/github-brief-intake/SKILL.md`
  (the `gh api` and `gh issue list` read path);
  `tests/roster/test_intent_template_shape_conformance.py` (the repository's
  pattern for an assertion that must read two packs at once). Named deviation:
  the cross-system agreement assertion has no home inside either pack.


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

The vocabulary comes first and is written without a provider in view, because
a vocabulary drafted against Jira's fields and then fitted to GitHub is Jira's
vocabulary with a translation layer — which is exactly what the outcome
forbids. Then each provider's reading is built against it independently, in its
own pack, sharing no code.

The agreement assertion is the point of the slice and it cannot live in either
pack, because a pack test may not read above its own pack. It goes at
repository level, following the pattern
`tests/roster/test_intent_template_shape_conformance.py` already sets for a
cross-pack assertion.

The riskiest part is that two independent readings agree only for the fixture
someone wrote. The mitigation is that the fixture pair represents the *same
work* in both systems rather than two convenient shapes, so the assertion fails
when a definition is provider-flavoured rather than when the fixture is
awkward.

## Constraints

- **ADR-0077 D6-D12** and **ADR-0019 D5**, for repo-origin work, set the
  authority boundary: an observation stays an observation.
- **ADR-0127 D4** bounds what may be read: nothing below the floor is counted,
  though a trace may be readable.
- **CAP-0004's guardrail** forbids a daemon, control plane, database or
  scheduler, so a reading is computed when asked and states its moment.
- **No shared implementation across delivery systems.** Each provider pack
  installs at user scope and stays independently installable, so identical
  arithmetic is duplicated rather than factored out.
- `flow-metrics` is the incumbent vocabulary to reconcile with. It is not
  moved, generalised or depended on.

## Construction tests

- A definition check over the vocabulary document: no term names a provider
  field.
- Per-provider reading fixtures, recorded from each provider's real response
  shape.
- One canonical work record, its expected vocabulary values declared beside
  it, and two provider representations derived from it. Each reading is
  compared against the declared values, never against the other reading.
- A zero-completion fixture asserting all four observations still return.
- A freshness assertion over rendered output.

## Durable-output map

| Output | Task | Evidence |
| --- | --- | --- |
| Vocabulary document | T1 | definition check clean |
| Jira Software reading | T2 | provider fixtures green |
| GitHub reading | T3 | provider fixtures green |
| Cross-system agreement assertion | T4 | both readings match independently declared expected values |
| Changelog entries for `atlassian` and `github` | T4 | one entry per pack |

## Design (LLD)

### Design decisions

- **The vocabulary is written before either reading.** Writing it after the
  first provider would encode that provider's semantics as the neutral one,
  which is the failure the outcome names.
- **The agreement assertion lives at repository level.** A pack test cannot
  read above its own pack, and this assertion needs both.
- **The expected values are owned outside both provider fixtures.** Comparing
  one reading against the other passes whenever both fixtures were authored to
  agree, which is the failure a cross-provider test is supposed to catch. A
  third, independently declared expectation is what makes the comparison
  evidence.
- **Duplication is accepted deliberately.** Two implementations of the same
  four reads is the cost of packs an adopter installs one at a time, and the
  agreement assertion is what buys it back.

### Data & schema

Four observations: state, assignment, blocking, elapsed time. Each has a
provider-neutral definition and a per-provider resolution recorded in that
provider's pack. Elapsed time is measured from a moment the vocabulary defines,
not from a provider's created timestamp.

### Interfaces & contracts

No new interface. Each provider reads through the client its pack already
ships.

### Component / module decomposition

Vocabulary in `docs/architecture/`; Jira reading in `packs/atlassian/`; GitHub
reading in `packs/github/`; the agreement assertion in `tests/roster/`.

### State & control flow

A reading is computed on invocation from the provider's current response. There
is no cache and no resident state, so freshness is a property of the moment the
call was made and is stated with the result.

### Behavior & rules

An observation a provider cannot supply is reported as absent for that
provider, never substituted from another. An artifact below ADR-0127's floor
yields no value.

### Failure, edge cases & resilience

A provider error is surfaced rather than rendered as an empty reading, because
an empty reading is indistinguishable from work that has not started. A
zero-item scope returns all four observations with zero counts, which is a
valid answer and not an error.

### Quality attributes (NFRs)

The agreement criterion is the one with a pass/fail bar: identical vocabulary
values from the same work in both systems.

### Dependencies & integration

Jira credentials through the broker and an authenticated `gh`, both already
stated requirements of their packs. No new dependency.

## Tasks

### T1: every vocabulary term is defined without naming a provider field

**Depends on:** none

**Tests:**
- The definition check passes over the vocabulary document. Verifies *defined
  without naming a provider's field*.
- No term's truth depends on a provider-specific semantic or capability, tested
  by evaluating each against a third delivery system neither pack supports.
  Verifies *no term's truth depends on a provider-specific semantic*.
- Each term carries a worked positive and negative example. Verifies *each term
  carries at least one worked positive and one worked negative example*.

**Approach:**
- Written before either reading exists, so no provider's semantics can become
  the default by being first.

**Done when:** the check is clean and each of the four terms has a definition
a reader could implement against a system neither pack supports.

**Touches:** docs/architecture/**

### T2: Jira Software reports all four observations against the vocabulary

**Depends on:** T1

**Tests:**
- Provider fixtures for state, assignment, blocking and elapsed time.
- A zero-completion scope returns all four.
- No value is returned below ADR-0127's floor.
- Every rendered reading states its moment.

**Done when:** the Jira fixtures are green and each read names the vocabulary
term it satisfies.

**Touches:** packs/atlassian/.apm/skills/**

### T3: GitHub Issues + Projects reports the same four, independently

**Depends on:** T1

**Tests:**
- Provider fixtures for the same four observations.
- Neither pack imports from the other.

**Approach:**
- Built from the vocabulary document rather than from T2's implementation, so
  agreement in T4 is evidence rather than a consequence of copying.

**Done when:** the GitHub fixtures are green with no reference to
`packs/atlassian`.

**Touches:** packs/github/.apm/skills/**

### T4: the same work read on both systems yields identical vocabulary values

**Depends on:** T2, T3

**Tests:**
- Both representations derive from one canonical work record and carry its
  identity. Verifies *derive from one canonical work record*.
- The expected values are declared outside both provider fixtures, and each
  reading matches them. Verifies *declared outside both provider fixtures* and
  *each reading matches those values*.
- A representation that cannot prove it is that record fails rather than being
  compared. Verifies *fails rather than being compared*.
- Nothing read updates a canonical artifact, and a reading leaves no resident
  process.

**Done when:** the repository-level assertion is green and `atlassian` and
`github` each lead a changelog entry.

**Touches:** tests/roster/**, packs/atlassian/CHANGELOG.md, packs/github/CHANGELOG.md

## Rollout

T2 and T3 are independent and can land in either order. T4 is the gate: until
it is green the vocabulary is a claim.

## Risks

- **The two readings agree only because both fixtures were written to agree.**
  Mitigated by declaring the expected values outside both fixtures and
  comparing each reading against them, and by building T3 from the document
  rather than from T2.
- **A provider-flavoured definition passes the definition check.** The check
  catches a named field, not a borrowed concept; T4 is the real detector, which
  is why it gates.
- **`blocked` may not generalise to a third provider.** Recorded as an open
  assumption; the Linear slice's author finds out first.

## Changelog

- 2026-09-24 — plan drafted.
