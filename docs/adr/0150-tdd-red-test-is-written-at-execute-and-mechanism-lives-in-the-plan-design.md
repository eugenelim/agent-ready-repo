# ADR-0150: The TDD red test is written at EXECUTE, and mechanism lives in the plan's design, not the contract

- **Status:** Proposed
- **Date:** 2026-10-27
- **Areas:** work-loop, shaping
- **Reversibility:** high
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** RFC-0028 (decision 3 and erratum E1 — the PLAN-time stub timing this record replaces; the vehicle, `work-loop/references/tdd-stubs.md`, stays); RFC-0019 (the plan's `## Design (LLD)` this record makes the home of mechanism)

## Decision summary

- **Decision:** We will have `work-loop` write and prove the TDD red test at EXECUTE, not store exact stub code in `plan.md` at PLAN, and we will route a mechanism claim to the plan's `## Design (LLD)` when its falsehood could move only the mechanism and no protected class depends on it.
- **Because:** reviewing a test or a mechanism before the code exists turns review into argument about guesses: rounds lengthen, each repair adds mechanism that draws the next finding, and the code still diverges and reopens spec review through amendments.
- **Applies to:** `work-loop` PLAN and EXECUTE in full mode, and `new-spec` claim routing, spec template, and plan template.
- **Tradeoff accepted:** a vague acceptance criterion is caught when EXECUTE tries to write its red test, not at PLAN; the `Tests:` bullet must still name the behavior, boundary, and verification mode, so a criterion nobody can test is still visible before approval.
- **Revisit if:** a run shows a TDD task reaching EXECUTE whose criterion cannot be turned into a red test, or a protected-class defect ships because its means was left to the design.

## Context

RFC-0028 decision 3 has PLAN generate a compilable red stub into `plan.md` and
EXECUTE consume it unchanged. Erratum E1 sharpened that into PLAN-contained code
validated from scratch and copied byte-identical after `CODE-IMPLEMENTATION`.
That puts exact test code under plan approval and pre-EXECUTE review.

Saved review reports from long full-mode runs show the cost. One spec took 7
shaping, 6 adversarial, and 5 security rounds. Rounds 4 and 5 argued about
crash windows in mechanism the plan had specified at code level, such as a
temp-file publish through `os.link` and `O_CREAT|O_EXCL|O_NOFOLLOW` flags. Each
repair added mechanism, which drew the next finding, and the shipped code still
had durability bugs that code-stage review found by running probes. In the
largest run, 9 of 11 pre-EXECUTE rounds reviewed amendment diffs made after
building started, because code kept diverging from mechanism-level spec and
plan text.

`new-spec` routes any unsettled load-bearing claim that could change "the
chosen mechanism" to `reaches-the-contract`, which settles it before approval.
That is what pulls mechanism into the reviewed contract. Plan approval hashes
the whole plan, so `## Design (LLD)` is not correctable after approval except
through the verification ledger route for a declared implementation-discovered
seam.

ADR-0117 D3 admits an RFC erratum only to clarify a decision, not change it.
Moving the red test's timing changes what decision 3 decided, so this is a new
record. RFC-0028's vehicle decisions (1, 2, 4, 5, 6) stay in force.

## Decision

We will write the TDD red test at EXECUTE and keep mechanism in the plan's design.

- **D1:** At PLAN, a TDD task's `Tests:` bullet names the behavior, the boundary it is checked at, and the verification mode. `plan.md` carries no required stub code.
- **D2:** At EXECUTE, the implementer writes the red test at the real test location and runs it, and it must fail for the intended reason before production code changes. An import failure of the not-yet-written target counts as that reason; any other collection, import, or setup error, or a timeout, is not red. Where a spec exists, the command and its failing output go to the verification ledger.
- **D3:** A `stub` fence in `plan.md` stays an optional form for a task that a supervisor run executes and that needs machine red proof. When present, EXECUTE materializes it unchanged, as before.
- **D4:** The protected classes are a security boundary, data loss or durability, a migration or persisted state, a public interface, and an irreversible operation. A mechanism claim reaches the contract when a protected class depends on it or when its falsehood could also move a criterion, boundary, task graph, verification strategy, or failure direction. For a protected class the property settles before approval; its means still lives in the design.
- **D5:** A mechanism claim whose falsehood could move only the chosen mechanism, and on which no protected class depends, is a task's local method. One a test can decide, and whose undoing needs no migration, external side effect, or user-visible contract change, is settled in code. One no test can decide lives in the plan's `## Design (LLD)`: the design states the required property and marks the means `implementation-discovered`, and the chosen means and any later correction go to the verification ledger, not an amendment.
- **D6:** Agent Rules and acceptance criteria name what the agent may do and what is observable. A syscall, flag, helper name, or exact write order is mechanism.
- **D7:** `implementation-discovered` is the one marker for a seam or a means the plan cannot ground before code exists. It replaces the `no stub (implementation-discovered)` and `no stub (mode)` records, which existed only because plan stubs were required.

## Consequences

**Positive:**
- Pre-EXECUTE review reads behavior, boundaries, and protected-class properties, which it can decide before code exists.
- Code that chooses a different means for an unprotected mechanism records it in the ledger and does not reopen spec review.

**Negative:**
- An untestable criterion surfaces at EXECUTE rather than at PLAN when its `Tests:` bullet looked plausible.
- A supervisor task without a `stub` fence gets no machine red proof from the engine; the plan author adds the fence when that proof is needed.

**Revisit if:** a run shows a TDD task reaching EXECUTE whose criterion cannot be turned into a red test, or a protected-class defect ships because its means was left to the design.

## Confirmation

- **Mode:** lint/CI
- **Signal:** `tests/roster/test_tdd_stub_lifecycle_contract.py` requires the EXECUTE-time red test, the optional supervisor fence, the protected-class routing in `new-spec`, and the `implementation-discovered` ledger route in the plan template, and refuses PLAN-time stub-code wording in every live source it reads.
- **Owner:** eugenelim
