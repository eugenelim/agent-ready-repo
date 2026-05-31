# Event categories

> Derived from the [Zalando RESTful API and Event Guidelines](https://opensource.zalando.com/restful-api-guidelines/) (CC-BY-4.0, Zalando SE), chapter 20. Restated for **AsyncAPI 3.1.0** output. Each rule keeps its shared `[#NNN]` token.

The category an event type belongs to determines its semantics, ordering
guarantees ([#203], [#242]), and expected payload structure.

---

### [#198] MUST ensure that events conform to an event category

Every event type MUST belong to one of the defined categories:

| Category | Purpose | Use when… |
|---|---|---|
| **General event** | Signal business process steps or milestones | Communicating workflow progression |
| **Data change event** | Signal resource state mutations (create/update/delete) | Synchronizing state across services |
| **Business event** | Signal significant business occurrences | Representing domain-level facts |

Declare the category on the AsyncAPI message — in its `description`, via a
`tags` entry, or an `x-event-category` extension — so consumers and reviewers can
see it without inferring from the payload shape.

---

### [#201] MUST use general events to signal steps in business processes

General events represent **milestones or transitions** in a business workflow.
They describe what happened in business terms, do not necessarily carry full
resource state, and have SHOULD-level ordering ([#203]).

```yaml
# AsyncAPI message — general event (CloudEvents structured mode)
components:
  messages:
    ShipmentDispatched:
      name: ShipmentDispatched
      contentType: application/cloudevents+json
      payload:
        allOf:
          - $ref: '#/components/schemas/CloudEventEnvelope'   # [#247] envelope
          - type: object
            properties:
              data:                                           # business payload
                $ref: '#/components/schemas/ShipmentDispatchedData'
```

---

### [#202] MUST use data change events to signal mutations

Data change events are emitted when a resource's state changes (created,
updated, deleted). They:

- Carry enough state for consumers to synchronize.
- SHOULD include the operation type (`create`, `update`, `delete`).
- MUST provide explicit ordering ([#242]).
- SHOULD match the corresponding REST resource structure ([#205]).

```yaml
# Business payload schema for a data change event
OrderChangedData:
  type: object
  required: [operation, resource]
  additionalProperties: false                                # [#210]
  properties:
    operation:
      type: string
      enum: [create, update, delete]
    resource:
      $ref: '#/components/schemas/Order'                     # [#205] mirrors REST
```

---

### [#199] MUST ensure that events define useful business resources

Event payloads MUST represent **meaningful domain concepts**, not low-level
technical artifacts:

- Good: `order.placed`, `payment.captured`, `shipment.delivered`.
- Bad: `database.row.inserted`, `cache.invalidated`, `queue.message.processed`.

An event a domain expert can name is a useful event; one only a developer
recognises usually leaks an implementation detail.
