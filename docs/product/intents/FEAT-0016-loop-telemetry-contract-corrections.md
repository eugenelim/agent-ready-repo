# Decide the remaining loop telemetry contract correction

- **Slug:** `loop-telemetry-contract-corrections`
- **Level:** feature
- **Status:** Withdrawn
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** capability:loop-telemetry-governance



## Disposition — withdrawn 2026-11-04, decided: the verification ledger is the durable account

**Do not shape this intent.** The question it asked is answered by the owner as
lifecycle owner: AC-0031 is not amended, and
[the verification ledger](../../specs/loop-telemetry-export/notes/verification-ledger.md)
stays the durable account of which enumeration sites the criterion's purpose
requires. `loop-telemetry-export` is Shipped. `tools/test_gate_enumeration.py`
reads each enumeration site and asserts it names the package, so a missing site
fails a test rather than waiting on prose. The refusal this intent excluded moved
to the sender and is AC-0075 in
[`jsonl-otlp-exporter`](../../specs/jsonl-otlp-exporter/spec.md). Reopen only if
a gate enumeration site stops naming the package and that test cannot catch it.

## Outcome

The owner decides whether to amend AC-0031's four-of-six gate enumeration sites or
accept the verification-ledger correction as the durable account, with no
production work implied by either choice.

## Boundary

- Admits: correcting AC-0031's enumeration or recording an owner decision that the ledger correction is sufficient.
- Excludes: production code, a new telemetry event, or reopening shipped behavior. The six literal gate enumeration sites (`pyproject.toml` `pythonpath` and mypy `files`, the `Makefile` `PYTHONPATH`, its test-suite invocations and its pip-audit leg, and `tools/lint-mypy.py` `TYPED_PACKAGES`) already name the package and are tested by `tools/test_gate_enumeration.py`.
- Excludes: the undeliverable-setting refusal. It moved to the sender and is covered by AC-0075 in `docs/specs/jsonl-otlp-exporter/spec.md`.
- Excludes: a general completed-task amendment mechanism. That is a wider work-loop lifecycle question and is not needed to dispose this one correction.

## Owner

- Repository maintainers. They decide whether the remaining wording mismatch warrants an amendment to a frozen integration contract.

## Unresolved questions

- AC-0031 names four gate enumerations while the gate requires six. Should the frozen contract enumerate all six, or should the owner accept the purpose clause plus verification ledger as the durable correction?

## Projection

- A small amendment to a future `loop-telemetry-export` revision, or an owner decision to close the mismatch as accepted. No implementation queue entry is implied.

## Opportunity

The six gate enumeration sites name the package and are tested, but the frozen
criterion enumerates only four. The remaining job is to decide what the durable contract should say,
not to build another telemetry mechanism.

## Assumptions

- **Riskiest assumption:** the verification ledger is durable enough to support an explicit close decision if the owner judges a frozen-contract amendment disproportionate.
- **Knowledge surface:** In-repository loop telemetry specs, verification ledgers, contract-amendment rules, and delivery history.


## Source

- Mode: repo-origin
- Locator: docs/specs/loop-telemetry-export/notes/verification-ledger.md
- Revision: sha256-bytes-v1:bdd4d6cd3cfab9155919b5ac4fd5cfd167e529a2cc748e992d81c0153e61ef5d
- Authority: repo-origin
