# Schema design

> Derived from the [Zalando RESTful API and Event Guidelines](https://opensource.zalando.com/restful-api-guidelines/) (CC-BY-4.0, Zalando SE), chapters 19-20. Restated for **AsyncAPI 3.1.0** output. Each rule keeps its shared `[#NNN]` token.

These rules govern the **payload schema** — the business data carried under the
envelope's `data` member (structured mode) or as the message payload (binary
mode).

---

### [#195] MUST make event schema available for review

The payload schema MUST be expressed inline in the AsyncAPI document
(`components.schemas`) or referenced from a registry the document points at, so
it is reviewable before deployment. (Governance framing for this rule is in
`naming.md`; here it is the concrete obligation to put the schema where a
reviewer can read it.)

---

### [#196] MUST ensure event schema conforms to the AsyncAPI schema object

Event payload schemas MUST be valid **AsyncAPI Schema Objects**. AsyncAPI 3.1.0
uses JSON Schema (draft 2020-12 superset) as its default schema language; declare
any alternative with `schemaFormat` on the message. Conforming enables:

- Reuse of AsyncAPI/JSON-Schema tooling for validation and code generation.
- One consistent schema language across the synchronous (OpenAPI) and
  asynchronous (AsyncAPI) surfaces.
- Automated compatibility checking ([#209]).

Place reusable payload schemas under `components.schemas` and `$ref` them from
`components.messages`.

---

### [#200] SHOULD avoid writing sensitive data to events

Event payloads SHOULD NOT contain PII, secrets, or other sensitive data:

- Use **reference identifiers** instead of inline sensitive values.
  - Good: `customer_id: "cust-123"` (consumer fetches details via API if needed).
  - Bad: `email: "user@example.com"`, `credit_card: "4111…"`.
- Events are persisted and replayed, so a leak is durable and wide. If sensitive
  data is unavoidable, document the classification and ensure access controls on
  the stream.

---

### [#205] SHOULD ensure that data change events match the API's resources

Data change event payloads SHOULD mirror the structure of the corresponding REST
resource. A consumer who knows the REST API then already understands the event:

```
REST:   GET /orders/123  -->  { "id": "123", "status": "SHIPPED", … }
Event:  order.updated    -->  { "data": { "resource": { "id": "123", "status": "SHIPPED", … } } }
```

Where the OpenAPI contract already defines the resource schema, reuse it (copy or
shared schema registry) rather than re-deriving a divergent shape.

---

### [#210] SHOULD avoid additionalProperties in event type schemas

Unlike REST APIs, event schemas SHOULD be **more restrictive** about additional
properties:

- Prefer explicit property definitions; set `additionalProperties: false` on
  payload objects.
- This improves validation and consumer code generation.
- Event schemas are harder to evolve than REST responses because events are
  persisted and replayed, so an open schema commits you to fields you never
  declared.

(An org whose consumers tolerate unknown fields may relax this via a delta that
disables `#210` — see `standards-authoring.md`.)
