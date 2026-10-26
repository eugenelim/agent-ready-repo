# ADR-0148: The completion receipt rides on the waiting item's `Dependency receipts:` header line

- **Status:** Accepted
- **Date:** 2026-10-26
- **Areas:** workspace, contracts
- **Reversibility:** low
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** ADR-0103 D6
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** RFC-0106 D3 (the dependency edge moves to the waiting item's `Depends on:` header); ADR-0103 (the receipt's fields and outcome vocabulary, which this record keeps)

## Decision summary

- **Decision:** We will keep a completion receipt on the citing item's `Dependency receipts:` preamble line, as `<reference> completion <delivery_id> <outcome> <completion_event> <evidence_ref>`, in place of an optional object on a `workspace.toml` dependency edge.
- **Because:** RFC-0106 D3 moves the dependency edge off the registry and onto the waiting item's `Depends on:` header, so the edge ADR-0103 D6 named as the receipt's carrier no longer exists.
- **Applies to:** every completion receipt written by `close-work` and read by `workspace-status`.
- **Tradeoff accepted:** the receipt is still a self-assertion, and its trust now rests on a reviewed, committed item file instead of a reviewed, committed registry file.
- **Revisit if:** a receipt must outlive the item that cited it; or the registry's removal changes where reviewed coordination state lives.

## Context

ADR-0103 D6 places the receipt "as an optional object on the citing local
dependency edge in `workspace.toml`". RFC-0106 D3 (accepted 2026-10-15) moves the
dependency edge to a `Depends on:` header on the waiting item, and the
`depends-on-headers` spec delivers it. The workspace entry's `needs` stays `[]`,
so there is no edge left in the registry to carry an object.

ADR-0117 D3 admits an Errata entry only to clarify what a decision means, not to
change where it puts something. Moving the carrier changes what D6 decided, so
the move is a new record that supersedes D6 in part, and D1 to D5, D7, and D8
stay in force.

## Decision

We will keep a completion receipt on the waiting item, on the `Dependency receipts:` line of its preamble, beside its `Depends on:` line.

- **D1:** A completion receipt is one entry of the citing item's `Dependency receipts:` preamble line, written `<reference> completion <delivery_id> <outcome> <completion_event> <evidence_ref>`. The `<reference>` is a typed reference that the same file's `Depends on:` line names.
- **D2:** The carrier is a header line and nothing else. The registry gains no field for a receipt, and no permanent initiative shell, shipped-spec list, third room, receipt store, or lifecycle schema is created.
- **D3:** The receipt's four fields, the outcome vocabulary, the grammars pinned to `delivery-lifecycle-record.schema.json`, and the finding code `invalid_completion_receipt` stay as ADR-0103 D1 to D5 and D8 decided them. A receipt line that does not parse, or names a reference the same file's `Depends on:` line does not, reports `invalid_dependency`.
- **D4:** The receipt's lifetime is the citing item's: removing the citing `Depends on:` item removes its receipt.
- **D5:** A captured-item reference may not carry a completion receipt.

## Consequences

**Positive:**
- The receipt sits in the one file that holds the edge it settles, so a reader of the waiting item sees both.
- The registry carries no dependency fact, which RFC-0106 needs before it can retire.

**Negative:**
- A receipt is now spread across item files instead of one registry, so finding every live receipt means reading item headers.
- A receipt for a captured item is refused, because a captured item has no delivery record to settle it.

**Revisit if:** a receipt must outlive the item that cited it; or the registry's removal changes where reviewed coordination state lives.

## Confirmation

- **Mode:** lint/CI
- **Signal:** `tests/roster/test_depends_on_headers_instructions.py` requires `close-work` to name `Dependency receipts:` as the receipt's home, and the `depends-on-headers` repair and engine suites cover the receipt grammar.
- **Owner:** Platform Core maintainer

## Alternatives considered

- **Keep the receipt on a registry `needs` edge:** rejected, because the edge moves to the header and a registry-only receipt would keep the registry a dependency fact store.
- **Record the move as an ADR-0103 Errata entry:** rejected, because ADR-0117 D3 admits an Errata entry only for a clarification, and moving the carrier changes D6.
- **A separate receipt file per delivery:** rejected, because ADR-0103 already refused a receipt store and the header line gives the receipt the citing item's lifetime for free.

## References

- [RFC-0106](../rfc/0106-stop-registering-derivable-work.md) D3.
- [ADR-0103](0103-the-completion-receipt-carries-a-delivery-outcome-not-a-disposition.md) D1 to D8.
- [`docs/specs/depends-on-headers/spec.md`](../specs/depends-on-headers/spec.md) AC-0004.
