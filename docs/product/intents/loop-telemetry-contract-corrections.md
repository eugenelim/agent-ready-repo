# Two contract corrections that a frozen task section could not accept

- **Slug:** `loop-telemetry-contract-corrections`
- **Level:** feature
- **Status:** Draft
- **Owner:** eugenelim


## Outcome

`loop-telemetry-export`'s contract carries two corrections that were found by doing the work and could not be made to it, and each is either landed or deliberately closed.

## Boundary

- Admits: correcting AC-0031's enumeration, giving the undeliverable-setting refusal a criterion, and deciding whether either is worth a new contract at all.
- Excludes: reopening anything that shipped. Both behaviours are implemented, gated and mutation-proved; what is missing is contract text, not code.
- Excludes: resetting `loop-telemetry-export`'s cohort. That is what made these unfixable in place, and the owner chose the audit trail over the amendment.

## Owner

- Repository maintainers. They decide whether either correction is worth a contract change now that the work it would describe has already shipped.

## Unresolved questions

- AC-0031 names four gate enumerations; six are required, and two of the six are not surfaces it names — so the criterion can be satisfied literally while the gate checks nothing. Reword it, or accept that its purpose clause carries the obligation and the ledger carries the correction?
- ~~`telemetry_layout.resolve()` refuses a `[telemetry]` setting the sender cannot receive. `CONVENTIONS.md` requires an observable refusal added during implementation to become a criterion. AC-0055 was written and withdrawn because its only honest task entry, T2, was already complete and frozen. Give it a criterion in a future contract, or accept three controls and no criterion?~~ **Answered 2026-09-16 by relocation, not by amendment.** `telemetry-sender-owns-its-configuration` retires `telemetry_layout` and moves the refusal into the sender, where it becomes AC-0075 in `docs/specs/jsonl-otlp-exporter/spec.md` — a criterion in a live contract rather than a withdrawn one in a frozen task. The question closed because the behaviour changed owner: nothing had to be written into `loop-telemetry-export`, so the frozen-task obstacle that sank AC-0055 never applied.
- More generally: when a contract error is found by implementing the task it describes, the task is complete by the time it is visible and the section is frozen. Is that acceptable, or does the amendment path need a way to correct a completed task's contract without discarding the cohort's audit trail?

## Projection

- One question remains: AC-0031's four-of-six gate enumeration. A small spec amendment against a future `loop-telemetry-export` revision, or a decision to close it as accepted. No queue entry is implied and no work is blocked on this. The undeliverable-setting question above is closed and needs no amendment.

## Opportunity

Both corrections are recorded with evidence in the spec's verification ledger, which is tracked. Neither blocks anything: the behaviour ships and is tested. What is absent is the contract text that would make a completion gate read them.

## Assumptions

- `loop-cohort` refuses a plan that rewrites a completed task's section by design — `validate_completed_task_sections` exists to 'return a stable refusal when an amended plan rewrites completed work'. This intent assumes that guard is correct and that the ordering constraint, not the guard, is what needs a decision.


## Source

- Mode: repo-origin
- Locator: docs/specs/loop-telemetry-export/notes/verification-ledger.md
- Revision: sha256-bytes-v1:bdd4d6cd3cfab9155919b5ac4fd5cfd167e529a2cc748e992d81c0153e61ef5d
- Authority: repo-origin
