# Decide the remaining loop telemetry contract correction

- **Slug:** `loop-telemetry-contract-corrections`
- **Level:** feature
- **Status:** Draft
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** capability:loop-telemetry-governance


## Outcome

The owner decides whether to amend AC-0031's four-of-six gate enumeration or
accept the verification-ledger correction as the durable account, with no
production work implied by either choice.

## Boundary

- Admits: correcting AC-0031's enumeration or recording an owner decision that the ledger correction is sufficient.
- Excludes: production code, a new telemetry event, or reopening shipped behavior. The six gate outcomes already emit and are tested.
- Excludes: the undeliverable-setting refusal. It moved to the sender and is covered by AC-0075 in `docs/specs/jsonl-otlp-exporter/spec.md`.
- Excludes: a general completed-task amendment mechanism. That is a wider work-loop lifecycle question and is not needed to dispose this one correction.

## Owner

- Repository maintainers. They decide whether the remaining wording mismatch warrants an amendment to a frozen integration contract.

## Unresolved questions

- AC-0031 names four gate enumerations while the gate requires six. Should the frozen contract enumerate all six, or should the owner accept the purpose clause plus verification ledger as the durable correction?

## Projection

- A small amendment to a future `loop-telemetry-export` revision, or an owner decision to close the mismatch as accepted. No implementation queue entry is implied.

## Opportunity

The six gate outcomes ship and are tested, but the frozen criterion enumerates
only four. The remaining job is to decide what the durable contract should say,
not to build another telemetry mechanism.

## Assumptions

- **Riskiest assumption:** the verification ledger is durable enough to support an explicit close decision if the owner judges a frozen-contract amendment disproportionate.
- **Knowledge surface:** In-repository loop telemetry specs, verification ledgers, contract-amendment rules, and delivery history.


## Source

- Mode: repo-origin
- Locator: docs/specs/loop-telemetry-export/notes/verification-ledger.md
- Revision: sha256-bytes-v1:bdd4d6cd3cfab9155919b5ac4fd5cfd167e529a2cc748e992d81c0153e61ef5d
- Authority: repo-origin
