# Naming & governance

> Derived from the [Zalando RESTful API and Event Guidelines](https://opensource.zalando.com/restful-api-guidelines/) (CC-BY-4.0, Zalando SE), chapter 19. Restated for **AsyncAPI 3.1.0** output. Each rule keeps its shared `[#NNN]` token so it is diffable by number against `api-contract`'s `references/events.md`.

These rules govern how an event type is framed, owned, registered, and named.
In AsyncAPI 3.1.0 an event type is a named entry under `components.messages`,
surfaced on a `channel` and published/subscribed by an `operation`.

---

### [#194] MUST treat events as part of the service interface

Events are **public API contracts**, not internal implementation details. An
AsyncAPI document is the contract surface, exactly as an OpenAPI document is for
REST. Every published event type MUST be:

- Designed with the same rigour as a REST operation (channels/operations/messages
  modelled deliberately, not derived from an internal table schema).
- Documented in the AsyncAPI specification under `components.messages`.
- Subject to the same review and governance as REST contracts ([#195]).
- Versioned with backward-compatibility guarantees ([#209], [#246]).

---

### [#195] MUST make event schema available for review

Event message schemas MUST be published and peer-reviewed before deployment,
following the same API-first principle that applies to REST specs. The AsyncAPI
document is the review artifact: reviewers read `components.messages` and
`components.schemas` to catch consistency, data-leak ([#200]), and compatibility
([#209]) issues before the stream goes live.

---

### [#197] MUST specify and register events as event types

Every event MUST be a formally named **event type**, not an anonymous payload.
In AsyncAPI:

- Each event type is a **named member of `components.messages`** (e.g.
  `OrderPlaced`), referenced by the channel's `messages` map.
- The fully qualified type name ([#213]) is carried in the CloudEvents `type`
  attribute of the envelope.
- A channel's `address` names the stream/topic the type is published to.

Registration enables discovery (consumers find available streams), governance
(ownership and compatibility mode are tracked — [#207], [#245]), and central,
versioned schema storage.

---

### [#207] MUST indicate ownership of event types

Every event type MUST have a clearly designated **owning team or service**.
Record ownership in the AsyncAPI document — typically `info.contact` for the
document's owner, and per-message `tags` or a `x-owner` extension where one
document spans multiple owning teams. Ownership implies responsibility for schema
design, backward-compatibility guarantees ([#209]), and consumer support.

---

### [#213] MUST follow naming convention for event type names

Event type names MUST use a hierarchical, domain-driven pattern:

```
{organization}.{domain}.{resource}.{event-verb}
```

Examples:

```
acme.order.order.placed
acme.order.shipment.dispatched
acme.fulfillment.parcel.delivered
acme.customer.address.updated
```

- Lowercase, dot-separated segments.
- The resource segment SHOULD match the corresponding REST resource name.
- The event verb is **past tense** — it describes what happened.
- This name is the CloudEvents `type` attribute value; the AsyncAPI message
  `name` may use a PascalCase form of the same concept (`OrderPlaced`).

---

### [#208] MUST define events compliant with overall API guidelines

All naming conventions and data formats from the REST API guidelines apply
equally to event payload schemas:

- Property names in `snake_case`.
- Date/time in ISO 8601 / RFC 3339 (`format: date-time`).
- Currency as ISO 4217, country as ISO 3166, language as BCP 47.
- Enums in `UPPER_SNAKE_CASE`; prefer open-ended value sets where the domain may
  grow ([#209]).

These apply to the **business payload** (the data under the envelope's `data`
member in structured mode), not to the CloudEvents context attributes, which
follow the CloudEvents naming spec.
