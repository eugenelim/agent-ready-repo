# contracts

API-first design — OpenAPI 3.1 and AsyncAPI contracts before implementation.

---

## Start here

Type `api-contract` and describe the API surface — resources, actions, and the consumers who will call it.

```text
api-contract [orders service: create, get, cancel]

  Endpoint              Method   Schema
  /orders               POST     OrderCreate → OrderResponse
  /orders/{order_id}    GET      → OrderResponse
  /orders/{order_id}    DELETE   → (204 No Content)

  Error responses: 400, 404, 409, 500 (Problem schema)
```

No orient command in this pack. On any session return, open the contract file directly and continue: `api-contract [path to existing spec]` to review or extend.

---

## Entry points

| Say this | What happens |
|----------|-------------|
| `api-contract` | Author or review an OpenAPI 3.1 contract — endpoints, schemas, error codes, consumer-perspective check |
| `event-contract` | Author or review an AsyncAPI 2.x event contract — channels, message shapes, producer/consumer boundary |

---

## How a session runs

```text
api-contract [orders service: create, get, cancel]

  Endpoint              Method   Schema
  /orders               POST     OrderCreate → OrderResponse
  /orders/{order_id}    GET      → OrderResponse
  /orders/{order_id}    DELETE   → (204 No Content)

  Error responses: 400, 404, 409, 500 (Problem schema)
  House standard: Zalando (default)
```

```text
  Consumer-perspective check

  ● All endpoints secured (Bearer token)
  ● Error shapes consistent (Problem schema)
  ⚠ POST /orders: missing 409 Conflict for duplicate order_id

  G-contract ›
```

```text
event-contract [order.placed event]

  Channel                     Message           Category
  orders/order.placed.v1      OrderPlacedV1     business-event

  Envelope: CloudEvents (structured mode)
  Payload:  order_id · customer_id · items[] · total_amount
```

---

## Cross-pack

**Upstream — `architect`:** Contracts inform architecture. When an OpenAPI or AsyncAPI contract exists, `architect-design` reads it as a boundary specification before proposing a backend shape.

**Downstream — `core`:** Contracts feed the build loop via `contract-acquisition`. When `work-loop` hits an unfamiliar API surface, `contract-acquisition` grounds the implementation against the contract before code is written.

---

→ **How it works:** [DESIGN.md](DESIGN.md) — philosophy, architecture, and decision log.  
→ **Go deeper:** the [`contracts` guides](https://github.com/eugenelim/agent-ready-repo/tree/main/guides/contracts/).
