# ADR-0105: Retained lifecycle records may terminate as Reclassified

- **Status:** Accepted
- **Date:** 2026-09-04
- **Areas:** workspace, state
- **Reversibility:** low
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** [RFC-0096](../rfc/0096-portable-delivery-artifact-lifecycle.md) §2 (reclassification ends delivery authority without deletion); [`delivery-lifecycle-record.schema.json`](../../contracts/jsonschema/delivery-lifecycle-record.schema.json) (the lifecycle record contract)

## Decision summary

- **Decision:** the lifecycle transition table admits exactly one new edge: `(retain-exception, Retained) → (retain-exception, Reclassified)`. `Reclassified` is a `post_closeout_result`, not a seventh disposition; the record continues to admit exactly the dispositions `cool-30-days` and `retain-exception`.
- **Because:** a durable owner can accept a retained multi-role artifact after delivery authority ends, and the lifecycle record must preserve that routing result without deleting the artifact.
- **Applies to:** lifecycle records already in `(retain-exception, Retained)` when a supplied, validated durable-owner acceptance block is recorded. The transition is not date-gated.
- **Tradeoff accepted:** the record states rather than proves acceptance. The supplied block is validated for shape and vocabulary only, which is the same bar every `Retained` record already meets. Reclassification is irreversible; a mistake is corrected by an ordinary reviewed change to the record file, not by another transition or a deletion workflow.
- **Revisit if:** durable-owner acceptance gains an authority-verifiable proof contract, or the lifecycle needs a governed route out of a terminal result.

## Context

RFC-0096 §2 classifies `Reclassified` as the routing result for a multi-role
artifact accepted by a durable owner: delivery authority ends without deletion.
The result belongs in `post_closeout_result`, alongside the other outcomes of
closeout, while `disposition` remains the two-value choice between cooling and
exceptional retention.

The frozen `thirty-day-cooling-and-retirement` record has a ticked AC22 whose
oracle is the six-row transition table in its `plan.md:117-124`. Adding
reclassification makes that exact-six-row assertion false without making its
hardcoded refusal sweep fail. This ADR supersedes only AC22's transition-table
oracle: the corrected table has the following seven rows. Everything else in
that frozen record stands.

## Decision

The lifecycle transition table admits one new terminal edge for a retained record.

- **D1:** The transition table admits exactly one new edge, `(retain-exception, Retained) → (retain-exception, Reclassified)`.
- **D2:** `Reclassified` is a `post_closeout_result`, not a seventh disposition.
- **D3:** The record continues to admit exactly the dispositions `cool-30-days` and `retain-exception`.
- **D4:** The new edge is reachable only from a record already in `(retain-exception, Retained)`.
- **D5:** The edge fires only when the caller supplies a durable-owner acceptance block that passes the record contract's shape and vocabulary validation.
- **D6:** The transition consults no date.
- **D7:** `Reclassified` is terminal; no edge leaves it, matching `Retired` and `ExternalAdvisory`.
- **D8:** A mistaken reclassification is corrected by an ordinary reviewed change to the record file, not by another transition or a deletion workflow.
- **D9:** This record supersedes only AC22's transition-table oracle in the frozen `thirty-day-cooling-and-retirement` record; everything else in that record stands.

## Corrected transition table

| From `(disposition, post_closeout_result)` | To |
| --- | --- |
| `(cool-30-days, Cooling)` | `(cool-30-days, Retired)` |
| `(cool-30-days, Cooling)` | `(retain-exception, Retained)` |
| `(retain-exception, Retained)` | `(retain-exception, Retained)` |
| `(retain-exception, Retained)` | `(cool-30-days, Cooling)` |
| `(retain-exception, Retained)` | `(retain-exception, Retired)` |
| `(retain-exception, Retained)` | `(retain-exception, ExternalAdvisory)` |
| `(retain-exception, Retained)` | `(retain-exception, Reclassified)` |

The new edge is reachable only from a retained record and only when the caller
supplies a durable-owner acceptance block that passes the record contract's
shape and vocabulary validation. It consults no date. `Reclassified` is
terminal: no edge leaves it, matching the existing `Retired` and
`ExternalAdvisory` results.

## Consequences

**Revisit if:** durable-owner acceptance gains an authority-verifiable proof
contract, so the record can prove rather than state acceptance (D5); or the
lifecycle needs a governed route out of a terminal result (D7, D8).
