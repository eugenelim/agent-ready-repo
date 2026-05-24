# Events

> Derived from the [Zalando RESTful API Guidelines](https://opensource.zalando.com/restful-api-guidelines/) (CC-BY-4.0, Zalando SE).

Events are first-class API contracts. These rules cover event type definition,
categorization, schema design, ordering, metadata, and consumer resilience.
Chapters 19-21 of the Zalando guidelines define ~24 rules for event-driven APIs.

---

## Event Fundamentals (Chapter 19)

### [#194] MUST treat events as part of the service interface

Events are not internal implementation details — they are **public API contracts**.
They MUST be:

- Designed with the same rigor as REST endpoints
- Documented in the API specification
- Subject to the same review and governance processes
- Versioned and maintained with backward compatibility guarantees

---

### [#195] MUST make event schema available for review

Event schemas MUST be published and peer-reviewed before deployment, following
the same API-first principles that apply to REST specifications. Schema review
ensures consistency, prevents data leaks, and catches compatibility issues early.

---

### [#196] MUST ensure event schema conforms to OpenAPI schema object

Event payload schemas MUST be valid **OpenAPI Schema Objects**. This enables:

- Reuse of existing OpenAPI tooling for validation and code generation
- Consistent schema language across synchronous (REST) and asynchronous (event) APIs
- Automated compatibility checking

---

### [#197] MUST specify and register events as event types

Every event MUST be formally registered as a named **event type** in the
organization's event registry. Registration enables:

- Discovery — consumers can find available event streams
- Governance — ownership, compatibility mode, and lifecycle are tracked
- Schema evolution — versioned schemas are stored centrally

---

### [#207] MUST indicate ownership of event types

Every event type MUST have a clearly designated **owning team or service**.
Ownership implies responsibility for:

- Schema design and evolution
- Backward compatibility guarantees
- Consumer support and incident response

---

### [#208] MUST define events compliant with overall API guidelines

All naming conventions, data formats, and design principles from the REST API
guidelines apply equally to events:

- Property names in `snake_case`
- Date/time in ISO 8601 / RFC 3339
- Standard problem/error formats where applicable
- Currency as ISO 4217, country as ISO 3166, language as BCP 47

---

### [#213] MUST follow naming convention for event type names

Event type names MUST use a hierarchical, domain-driven naming pattern:

```
{organization}.{domain}.{resource}.{event-verb}
```

Examples:
```
zalando.order.order.placed
zalando.order.shipment.dispatched
zalando.fulfillment.parcel.delivered
zalando.customer.address.updated
```

- Use lowercase, dot-separated segments
- The resource segment SHOULD match the corresponding REST resource name
- The event verb describes what happened (past tense)

---

## Event Categories (Chapter 20)

### [#198] MUST ensure that events conform to an event category

Every event type MUST belong to one of the defined categories:

| Category | Purpose | Use when... |
|---|---|---|
| **General event** | Signal business process steps or milestones | Communicating workflow progression |
| **Data change event** | Signal resource state mutations (create/update/delete) | Synchronizing state across services |
| **Business event** | Signal significant business occurrences | Representing domain-level facts |

The category determines the event's semantics, ordering guarantees, and expected
payload structure.

---

### [#201] MUST use general events to signal steps in business processes

General events represent **milestones or transitions** in a business workflow:

```yaml
# Example: order dispatched event
event_type: 'acme.order.shipment.dispatched'
category: general
payload:
  order_id: '12345'
  shipment_id: 'ship-789'
  carrier: 'DHL'
  dispatched_at: '2025-06-15T14:30:00Z'
```

General events:
- Describe what happened in business terms
- Do not necessarily carry the full resource state
- Ordering is SHOULD-level ([#203])

---

### [#202] MUST use data change events to signal mutations

Data change events are emitted when a resource's state changes (created, updated,
deleted):

```yaml
# Example: order updated data change event
event_type: 'acme.order.order.updated'
category: data-change
payload:
  operation: 'update'
  resource:
    id: '12345'
    status: 'shipped'
    updated_at: '2025-06-15T14:30:00Z'
  previous:
    status: 'processing'
```

Data change events:
- Carry enough state for consumers to synchronize
- SHOULD include the operation type (`create`, `update`, `delete`)
- MUST provide explicit ordering ([#242])
- SHOULD match the corresponding REST resource structure ([#205])

---

### [#199] MUST ensure that events define useful business resources

Event payloads MUST represent **meaningful domain concepts**, not low-level
technical artifacts:

- Good: `order.placed`, `payment.captured`, `shipment.delivered`
- Bad: `database.row.inserted`, `cache.invalidated`, `queue.message.processed`

Events should be understandable by domain experts, not just developers.

---

### [#200] SHOULD avoid writing sensitive data to events

Event payloads SHOULD NOT contain personally identifiable information (PII),
secrets, or other sensitive data:

- Use **reference identifiers** instead of inline sensitive values
  - Good: `customer_id: "cust-123"` (consumer fetches details via API if needed)
  - Bad: `email: "user@example.com"`, `credit_card: "4111..."`
- If sensitive data is unavoidable, document the classification and ensure
  appropriate access controls on the event stream

---

### [#205] SHOULD ensure that data change events match the API's resources

Data change event payloads SHOULD mirror the structure of the corresponding REST
resource. This reduces cognitive load — consumers who know the REST API already
understand the event schema.

```
REST:   GET /orders/123  -->  { "id": "123", "status": "shipped", ... }
Event:  order.updated    -->  { "resource": { "id": "123", "status": "shipped", ... } }
```

---

## Event Ordering and Partitioning

### [#203] SHOULD provide explicit event ordering for general events

General events SHOULD include a mechanism for consumers to reconstruct order:

- Timestamps (`occurred_at`) for approximate ordering
- Sequence numbers for strict ordering within a partition
- Causal identifiers (e.g., `parent_event_id`) for workflow correlation

---

### [#242] MUST provide explicit event ordering for data change events

Data change events have **stricter ordering requirements** than general events.
They MUST include:

- A monotonically increasing **sequence number** or comparable ordering field
- Ordering is guaranteed **per partition** (typically per resource instance)
- Consumers MUST be able to detect gaps and request replays if needed

---

### [#204] SHOULD use the hash partition strategy for data change events

Data change events SHOULD be partitioned by a **hash of the resource identifier**:

```
partition_key = hash(resource_id)
```

This guarantees that:
- All events for the same resource land in the same partition
- Events for a single resource are strictly ordered
- Load is distributed evenly across partitions

---

## Event Schema and Compatibility

### [#209] MUST maintain backward compatibility for events

Event schemas follow the same compatibility rules as REST APIs ([#106]):

**Breaking changes (forbidden):**
- Removing or renaming a required field
- Changing a field's type or format
- Tightening validation constraints

**Compatible changes (allowed):**
- Adding new optional fields
- Relaxing validation constraints
- Adding new event types

---

### [#210] SHOULD avoid additionalProperties in event type schemas

Unlike REST APIs ([#111]), event schemas SHOULD be **more restrictive** about
additional properties:

- Prefer explicit property definitions over open schemas
- This improves schema validation and consumer code generation
- Event schemas are harder to evolve than REST responses because events are
  persisted and replayed

---

### [#245] MUST carefully define the compatibility mode

Every event type MUST declare its **compatibility mode** — the rules governing
how the schema can evolve:

| Mode | Allowed changes |
|---|---|
| **Forward** | New fields can be added; consumers must tolerate unknown fields |
| **Backward** | Old consumers can read new events; no required field removal |
| **Full** | Both forward and backward compatible |
| **None** | No compatibility guarantee (use sparingly) |

Document the compatibility mode in the event type registration.

---

### [#246] MUST use semantic versioning of event type schemas

Event schemas MUST be versioned following **semantic versioning** (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking schema changes (should be avoided — [#209])
- **MINOR**: New optional fields or compatible extensions
- **PATCH**: Documentation or description corrections

The schema version is tracked in the event registry and included in event metadata.

---

## Event Identifiers and Consumer Resilience

### [#211] MUST provide unique event identifiers

Every event instance MUST carry a globally unique identifier:

- Use UUID v4 or an equivalent globally unique ID scheme
- The identifier enables deduplication, tracing, and audit logging
- It MUST be assigned by the producer at creation time

---

### [#212] SHOULD design for idempotent out-of-order processing

Event consumers SHOULD be designed to handle:

- **Out-of-order delivery** — events may arrive in a different order than produced
- **Idempotent processing** — applying the same event twice produces the same result
- Include sufficient context in the event (e.g., full resource state, version number)
  so consumers can reconcile state regardless of arrival order

---

### [#214] MUST be robust against duplicates when consuming events

Event consumers MUST implement deduplication or idempotent processing:

- Assume **at-least-once delivery** semantics — duplicates will occur
- Use `event_id` ([#211]) as a deduplication key
- Track processed event IDs in a persistent store
- Alternatively, design processing logic to be naturally idempotent

---

## Event Metadata

### [#247] MUST provide mandatory event metadata

Every event MUST include a standard metadata envelope with these required fields:

| Field | Type | Description |
|---|---|---|
| `eid` | `string` (UUID) | Unique event identifier ([#211]) |
| `event_type` | `string` | Fully qualified event type name ([#213]) |
| `occurred_at` | `string` (date-time) | When the event actually happened (ISO 8601) |
| `received_at` | `string` (date-time) | When the event was received by the broker (ISO 8601) |
| `version` | `string` | Event schema version, semver ([#246]) |
| `partition_key` | `string` | Key used for partitioning ([#204]) |

---

## Event Schema Template

Use this template as the starting point for any event type definition:

```yaml
components:
  schemas:

    # Reusable event metadata envelope
    EventMetadata:
      type: object
      description: |
        Mandatory event metadata fields per [#247].
        All events MUST include this metadata.
      required:
        - eid
        - event_type
        - occurred_at
        - version
      properties:
        eid:
          type: string
          format: uuid
          description: Unique event identifier [#211]
          example: 'a2c8f3d1-7b4e-4f5a-9c6d-8e2f1a3b5c7d'
        event_type:
          type: string
          description: Fully qualified event type name [#213]
          example: 'acme.order.order.placed'
        occurred_at:
          type: string
          format: date-time
          description: Timestamp when the event occurred [#247]
          example: '2025-06-15T14:30:00.000Z'
        received_at:
          type: string
          format: date-time
          description: Timestamp when the event was received by the broker [#247]
          example: '2025-06-15T14:30:01.123Z'
        version:
          type: string
          description: Event schema version (semver) [#246]
          example: '1.2.0'
        partition_key:
          type: string
          description: Hash partition key, typically the resource ID [#204]
          example: 'order-12345'

    # Example: General event
    OrderPlacedEvent:
      type: object
      description: |
        General event [#201] signaling that an order has been placed.
        Category: general [#198].
        Event type: acme.order.order.placed [#213].
      allOf:
        - $ref: '#/components/schemas/EventMetadata'
        - type: object
          required:
            - payload
          properties:
            payload:
              type: object
              required:
                - order_id
                - placed_at
              properties:
                order_id:
                  type: string
                  description: Unique order identifier
                  example: 'order-12345'
                customer_id:
                  type: string
                  description: Reference to the customer [#200] — no PII
                  example: 'cust-67890'
                placed_at:
                  type: string
                  format: date-time
                  example: '2025-06-15T14:30:00.000Z'
                total_amount:
                  type: number
                  format: decimal
                  example: 99.95
                currency:
                  type: string
                  description: ISO 4217 currency code [#208]
                  example: 'EUR'

    # Example: Data change event
    OrderUpdatedDataChangeEvent:
      type: object
      description: |
        Data change event [#202] for order resource mutations.
        Category: data-change [#198].
        MUST provide explicit ordering [#242].
      allOf:
        - $ref: '#/components/schemas/EventMetadata'
        - type: object
          required:
            - payload
          properties:
            sequence_number:
              type: integer
              format: int64
              description: |
                Monotonically increasing sequence for ordering [#242].
                Unique per partition (per resource instance).
              example: 42
            payload:
              type: object
              required:
                - operation
                - resource
              properties:
                operation:
                  type: string
                  enum:
                    - create
                    - update
                    - delete
                  description: Type of mutation
                resource:
                  $ref: '#/components/schemas/Order'
                  description: |
                    Current resource state [#205].
                    Structure SHOULD match the REST API resource.
```

---

## Rules checklist

Use this checklist when defining or reviewing event schemas:

```
Event type definition:
  [ ] Treated as a first-class API contract [#194]
  [ ] Schema reviewed and approved [#195]
  [ ] Schema conforms to OpenAPI Schema Object [#196]
  [ ] Registered in event registry [#197]
  [ ] Ownership clearly assigned [#207]
  [ ] Naming follows convention: org.domain.resource.verb [#213]
  [ ] Category assigned: general, data-change, or business [#198]

Schema design:
  [ ] Compliant with API guidelines (naming, formats) [#208]
  [ ] Defines useful business resources [#199]
  [ ] No sensitive data in payload [#200]
  [ ] Data change events match REST resource structure [#205]
  [ ] additionalProperties avoided [#210]
  [ ] Compatibility mode declared [#245]
  [ ] Semantic version assigned [#246]

Metadata and ordering:
  [ ] Mandatory metadata present (eid, event_type, occurred_at, version) [#247]
  [ ] Unique event identifier (UUID) [#211]
  [ ] General events: ordering mechanism provided [#203]
  [ ] Data change events: explicit ordering (sequence number) [#242]
  [ ] Data change events: hash partition strategy [#204]

Consumer resilience:
  [ ] Backward compatibility maintained [#209]
  [ ] Consumers handle duplicates [#214]
  [ ] Consumers support idempotent, out-of-order processing [#212]
```
