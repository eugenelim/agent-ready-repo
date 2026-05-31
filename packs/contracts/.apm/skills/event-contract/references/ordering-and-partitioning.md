# Ordering & partitioning

> Derived from the [Zalando RESTful API and Event Guidelines](https://opensource.zalando.com/restful-api-guidelines/) (CC-BY-4.0, Zalando SE), chapters 20-21. Restated for **AsyncAPI 3.1.0** output. Each rule keeps its shared `[#NNN]` token.

These rules govern how consumers reconstruct order and how producers distribute
events across partitions.

---

### [#203] SHOULD provide explicit event ordering for general events

General events SHOULD carry a mechanism for consumers to reconstruct order:

- A timestamp (`occurred_at`, or the CloudEvents `time` attribute) for
  approximate ordering.
- A sequence number for strict ordering within a partition.
- Causal identifiers (e.g. `parent_event_id`) for workflow correlation.

For general events this is SHOULD-level; for data change events it is MUST-level
([#242]).

---

### [#242] MUST provide explicit event ordering for data change events

Data change events have **stricter ordering requirements** than general events.
They MUST include:

- A monotonically increasing **sequence number** (or comparable ordering field)
  in the payload.
- Ordering guaranteed **per partition** (typically per resource instance —
  [#204]).
- Enough information for consumers to detect gaps and request replays.

```yaml
OrderChangedData:
  type: object
  required: [sequence_number, operation, resource]
  properties:
    sequence_number:
      type: integer
      format: int64
      description: Monotonically increasing per partition (per resource) [#242]
```

---

### [#204] SHOULD use the hash partition strategy for data change events

Data change events SHOULD be partitioned by a **hash of the resource
identifier**:

```
partition_key = hash(resource_id)
```

This guarantees that all events for one resource land in the same partition and
are strictly ordered, while load spreads evenly. The partition key travels in the
event metadata ([#247]) and, where the broker binding supports it, in the
message's protocol binding (e.g. a Kafka key). Protocol-binding catalogues are
out of scope here; the method notes where they plug in.

---

### [#212] SHOULD design for idempotent out-of-order processing

Even with explicit ordering, consumers SHOULD be designed to handle:

- **Out-of-order delivery** — events may arrive in a different order than
  produced.
- **Idempotent processing** — applying the same event twice produces the same
  result (keyed on the unique event id, [#211]).
- Sufficient context in the event (full resource state or a version number) so a
  consumer can reconcile regardless of arrival order.

This is the producer-side design obligation; the consumer-side duplicate
robustness rule is [#214] (see `metadata.md`).
