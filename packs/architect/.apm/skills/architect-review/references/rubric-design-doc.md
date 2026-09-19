# Design-doc rubric — for `architect-review`

The quality bar for critiquing a design doc. Walk every applicable check; do not
start writing findings until the walk is complete so findings can be
ordered by severity.

> Note: this rubric is intentionally duplicated from
> `architect-design`'s `design-doc-rubric.md`. Skill autonomy beats
> DRY at this scale — each skill stands alone. See the pack README.

**How to walk this rubric.** Three scopes author from three templates, and
they do not carry the same sections or the same table columns. **A check
applies when the document's scope has the section the check sits under.** A
check naming a field that scope does not carry is not applicable, and its
absence is not a finding — marking one would fail a correctly authored
document, which is the fastest way to teach an author to ignore the reviewer.

Where a check is narrower than all three scopes it says so in the item, as
*(subsystem)*, *(application/system)* or *(architecture change)*.

An architecture-change document carries eight delta sections under different
names. A `*(architecture change)*` check applies to the delta section its
parent heading maps to:

| Spine section | Its delta section |
| --- | --- |
| Scope and Context | Scope and Baseline |
| Structural Model | Structural Change |
| Runtime Model | Runtime Change |
| Contracts and Invariants | Contract and Invariant Change |
| Data and State | Data/State Migration |
| Deployment and Operations | Deployment/Operational Change |
| Quality Scenarios and Verification | Quality Regression and Verification |
| Implementation Mapping | Build Mapping |

A change document has no Decisions, Rollout, or Open Questions section, so no
check under those headings reaches it, and their absence is never a finding.

## Scope and Context

- [ ] The header names a **Decision sought** and a **Title** a
      non-author can recall — the structured fields a reader checks
      instead of scanning for a summary paragraph.
- [ ] States the user-visible problem (not the technical symptom).
- [ ] Names the relevant constraints (deadline, regulatory, team
      shape, existing system shape). At least one is non-obvious.
- [ ] References the system being changed by name — module, service,
      surface — not by gesture.
- [ ] Goals are testable. Each is something an outsider could verify.
- [ ] Non-goals are *substantive*. At least one non-goal is something
      a reasonable reader might assume is in scope.

## Structural Model

- [ ] Names the trust boundaries the design crosses.
- [ ] Every diagram states the one named question it answers and its
      zoom level — a reader landing on the diagram alone knows what
      it is for without reading the surrounding prose first.

## Runtime Model

- [ ] Carries at least one normal-path scenario and one
      failure-or-recovery-path scenario, each sequenced rather than
      only described. A design that sequences only the happy path has
      not shown how it degrades, and that is a finding.
- [ ] *(architecture change)* The runtime delta names which existing
      scenarios change and which are untouched, rather than
      re-sequencing the whole system.

## Contracts and Invariants

- [ ] *(subsystem, application/system)* Each contract names its
      identity, its compatibility rule and its failure semantics, not
      only its request/response shape.
- [ ] *(architecture change)* Each contract change names its change
      type, the baseline it is measured against, compatibility during
      the transition, and how the change is enforced and verified.
- [ ] Each stated invariant names what enforces it. An invariant with
      no enforcement is an aspiration, and saying so is the finding.

## Data and State

- [ ] *(subsystem)* Every element's state is declared explicitly,
      including an element that is `stateless`. An absent row is a
      finding, because a reader cannot tell it from an oversight.
- [ ] *(application/system)* Every data domain names its authority —
      the one place allowed to decide the value. Two authorities for
      one domain is a finding.
- [ ] *(architecture change → Data/State Migration)* Every migrated data
      element names its old shape, its new shape, the migration mechanism
      and its trigger, and what a partial migration leaves behind and how
      that is undone. A migration with no stated rollback is a finding.

## Quality Scenarios and Verification

- [ ] Each quality attribute carries a measurable target — the number
      that decides pass or fail. A scenario with no number cannot be
      failed, so it is not yet a scenario.
- [ ] Each scenario names the mechanism that achieves the response.
      Naming a target with no mechanism is a wish, not a design.
- [ ] Each scenario names how it is verified.

## Decisions, Alternatives, and Risks

- [ ] At least two alternatives, each a real option a reasonable
      engineer might have chosen.
- [ ] Each alternative has a *rejection reason*, not a dismissal.
- [ ] No strawmen.
- [ ] At least three risks (two if the design is genuinely small).
- [ ] Each risk is paired with a mitigation, or explicitly marked as
      *accepted unmitigated* with the reason.
- [ ] At least one risk is operational (what breaks at 3am).

## Rollout, Migration, and Reversal

- [ ] Names the migration / launch shape.
- [ ] Has a rollback story. "We won't need to roll back" fails.
- [ ] Names who is on the hook for the rollout window.

## Deployment and Operations

- [ ] Every deployment unit names how it scales and the signal an
      operator watches. A unit with no observable signal is a finding.
- [ ] A topology diagram appears only where physical placement differs
      from the structural model. A second diagram that repeats the
      structure is a finding, not thoroughness.

## Implementation Mapping

- [ ] The complete model set plus Implementation Mapping is
      sufficient to implement from — a reader should not need to ask
      the author what is missing.
- [ ] *(subsystem)* Each element in the model reaches a verification
      that proves the mapping holds.
- [ ] *(application/system)* The mapping reaches product, repository,
      deployable, platform and team. It carries no per-file or
      per-module detail; that detail here is a finding, not a bonus.

## Open Questions

- [ ] Omit this section entirely when no honest open questions
      remain. An empty section left in place is not evidence that
      none exist.
- [ ] Each question names who could answer it.
- [ ] No question is a disguised TODO.

## Cross-cutting

- [ ] If the design introduces an extension contract (a hook, plugin,
      or convention for third-party customisation), it names the
      contract explicitly, describes the extension point's shape, and
      states what is stable vs what the adopter must not depend on.
- [ ] Performance / scale assumptions named. For a **synchronous** request path,
      the worst-case latency is summed across every hop and compared to the
      binding front-door timeout; an unbudgeted long-operation path that can
      exceed it is a finding (see the serverless lens's sync-vs-async gate).
- [ ] Data-handling and privacy obligations named.
- [ ] Failure modes and observability hooks named.
- [ ] Cost shape named (when material).

### Document-architecture gates

The same ten gates `architect-design`'s authoring rubric walks at the
self-check, walked again here at review. A severity orders which fix an
author makes first, in the same vocabulary the author already used — 🟥
blocker, 🟧 major, 🟨 minor. 🔧 marks a gate `architect-design`'s
`check_document_architecture.py` script decides directly; 🧭 marks a gate
the reviewer decides.

| ID | Tag | Severity | Asks |
| --- | --- | --- | --- |
| `DA1` | 🧭 | 🟨 | Is the body written in the present tense? |
| `DA2` | 🧭 | 🟧 | Does every cross-reference name its target? |
| `DA3` | 🔧 | 🟨 | Does any prose paragraph run past three sentences? |
| `DA4` | 🧭 | 🟧 | Does each model come before the prose explaining it? |
| `DA5` | 🧭 | 🟥 | Does each concern live in exactly one place? |
| `DA6` | 🧭 | 🟨 | Have settled decisions been removed from the body? |
| `DA7` | 🧭 | 🟧 | Does each diagram state one question at one zoom? |
| `DA8` | 🧭 | 🟥 | Can the reader build from the models plus the mapping? |
| `DA9` | 🧭 | 🟨 | Is evidence linked rather than piled into the document? |
| `DA10` | 🔧 | 🟧 | Is the document over the size bound? |

`DA5`'s verdict is the reviewer's judgement alone; no automated measure
decides it.

## Decomposition

A document covering several subsystems is judged against six criteria for
whether a part earns a document of its own:

| ID | Criterion |
| --- | --- |
| `D1` | A live architectural decision of its own. Mandatory, and also the recursion's stopping rule. |
| `D2` | Crosses a trust, identity, data-ownership, or deployment boundary that differs from the parent's. |
| `D3` | An independent release or failure unit. |
| `D4` | A different system shape or workload class, so a different overlay applies. |
| `D5` | Different owners or reviewers. |
| `D6` | Its own quality scenarios, rather than inherited ones. |

- [ ] A child described in this document meets `D1` plus at least one other
      criterion and has no document of its own. This is a finding: the
      document should have been several.
- [ ] A child was split out that does not meet `D1`, or a split gives one
      contract two homes, or a split was made because a child was merely
      large. Each is a finding on its own. **Size alone never justifies a
      split.**
- [ ] Where children have split out, the parent is judged as the set's
      index: it retains the scope table, the structural model with the
      children as named elements, the contracts between children, the
      cross-child invariants, and the links to each child document.
- [ ] The parent does not restate child internals. Restatement is the main
      fuel of the oversized single document, so a parent repeating a
      child's internal model is a finding.

## Severity mapping (typical)

- 🟥 **Blocker** — the header's Decision sought misleads; Structural
  Model or the decisions section contradicts the header or is
  incomplete; a trust boundary is unlabeled; Decisions, Alternatives,
  and Risks names one option dressed as two.
- 🟧 **Major** — Goals not testable; Non-goals empty; one alternative
  is a strawman; no rollback story; cross-cutting concerns ignored.
- 🟨 **Minor** — Section ordering awkward; one risk has no
  mitigation; cross-cutting partial.
- ⚪ **Nit** — Phrasing, typos, capitalization.
