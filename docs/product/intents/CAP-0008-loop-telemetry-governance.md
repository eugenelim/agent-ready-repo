# Loop telemetry governance

- **Slug:** `loop-telemetry-governance`
- **Status:** Withdrawn
- **Level:** capability
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** none
- **Decomposed:** 2026-10-02 children

## Disposition — withdrawn 2026-11-05, decided: both children are terminal and no repository work remains

**Do not shape this capability.** [FEAT-0016](FEAT-0016-loop-telemetry-contract-corrections.md) was withdrawn on 2026-11-04 with the verification ledger as the durable account. [FEAT-0015](FEAT-0015-loop-telemetry-event-vocabulary.md) is withdrawn with its answers recorded and waits for the ecosystem's INI-005. The shipped sender, its configuration, and the enterprise endpoint default are owned by other records ([FEAT-0017](FEAT-0017-catalogue-level-telemetry-endpoint-default.md) for the endpoint), so this capability has nothing left to hold.

## Outcome

- **Steerable input:** The share of unresolved loop telemetry claims that name their emitting source, governing contract, and required disposition.
- **Lagging outcome:** Maintainers can keep the shipped loop telemetry contract and the future observability vocabulary truthful without adding events or implementation work merely to reconcile prose.
- **Guardrail:** Governance decisions do not reopen the shipped sender, add fields without a measured need, or absorb configuration work owned by another programme.

## Opportunity

- **Functional job:** Reconcile what the loop emits with what its contracts and future observability programme claim.
- **Emotional job:** Trust that a named telemetry event or criterion is backed by a real emitting source.
- **Social job:** Explain a telemetry claim from one reviewable chain of evidence rather than from delivery-session memory.
- **Struggling moment:** The shipped loop integration left a bounded contract correction and a separate future-vocabulary decision as top-level backlog items with no shared governance owner.

## Boundary

This capability owns the reconciliation of the future INI-005 event vocabulary
with the envelope the loop can actually emit. The second decision it was framed
around, the AC-0031 contract correction, is closed: FEAT-0016 is withdrawn with
the verification ledger as the durable account.

It does not own the separately installed sender, sender resume or bounds,
effective-configuration diagnostics, a durable base-freshness-waiver marker,
or the enterprise endpoint. The endpoint follows RFC-0101 and
`credential-pack-defaults-projection`; no sender change is currently needed.
The two unshaped ideas remain outside this tree until each earns an intent.

## Assumptions

- **Riskiest assumption:** the delivered loop envelope is stable enough for contract and vocabulary decisions to proceed without implementation changes.
- The remaining AC-0031 mismatch and the INI-005 vocabulary are independently decidable and neither needs a speculative sender feature.
- **Knowledge surface:** In-repository loop telemetry specs and ledgers, telemetry architecture, derivability research, ecosystem shaping, workspace records, and Git history.

## Decomposition

The bounded repository contract question is closed. The ecosystem vocabulary is
the one live child.

1. **Contract accuracy** — [FEAT-0016: Loop telemetry contract correction](FEAT-0016-loop-telemetry-contract-corrections.md) (withdrawn; decision recorded there)
2. **Vocabulary** — [FEAT-0015: Loop telemetry event vocabulary](FEAT-0015-loop-telemetry-event-vocabulary.md)
