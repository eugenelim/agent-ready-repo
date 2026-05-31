# Event metadata & consumer resilience

> Derived from the [Zalando RESTful API and Event Guidelines](https://opensource.zalando.com/restful-api-guidelines/) (CC-BY-4.0, Zalando SE), chapters 19-21. Restated for **AsyncAPI 3.1.0** output. Each rule keeps its shared `[#NNN]` token.

These rules govern the metadata envelope and consumer-side robustness. The
**envelope itself is Axis B** of the standard (CloudEvents 1.0.2 by default), so
the mandatory metadata fields below map onto the active envelope's attributes
rather than being re-invented per event.

---

### [#211] MUST provide unique event identifiers

Every event instance MUST carry a globally unique identifier:

- Use UUID v4 or an equivalent globally unique scheme.
- Assigned by the producer at creation time.
- Enables deduplication ([#214]), tracing, and audit logging.

With the bundled CloudEvents envelope this is the required `id` attribute
(unique per `source`).

---

### [#247] MUST provide mandatory event metadata

Every event MUST carry a standard metadata envelope. With the bundled CloudEvents
1.0.2 envelope, the Zalando-mandated fields map onto CloudEvents context
attributes — the envelope is the metadata, so do not duplicate these into the
business payload:

| Zalando metadata | CloudEvents attribute | Notes |
|---|---|---|
| `eid` (unique id) | `id` | Required; unique per `source` [#211] |
| `event_type` | `type` | Fully qualified name [#213] |
| `occurred_at` | `time` | RFC 3339 timestamp [#203] |
| `version` (schema semver) | `dataschema` / `x-schema-version` | Schema version [#246] |
| `partition_key` | `partitionkey` (Partitioning extension) | Hash key [#204] |
| (received_at) | broker-assigned | Set by the broker, not the producer |

If the active envelope is **not** CloudEvents (an org swapped Axis B), the same
mandatory fields apply to that envelope's equivalent attributes; the obligation
is the field set, not the CloudEvents spelling.

---

### [#214] MUST be robust against duplicates when consuming events

Event consumers MUST implement deduplication or idempotent processing:

- Assume **at-least-once delivery** — duplicates will occur.
- Use the unique event id ([#211] / CloudEvents `id`) as the dedup key.
- Track processed event ids in a persistent store, or design processing to be
  naturally idempotent ([#212]).

This is a consumer-design rule. It still shapes the contract: the event id MUST
be present and stable so consumers *can* dedup on it.
