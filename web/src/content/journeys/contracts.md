---
pack: contracts
scope: user
tagline: "API-first design — OpenAPI 3.1 and AsyncAPI contracts before implementation."
prerequisitePacks: []
contract:
  useItWhen: "You are designing an API or event-driven interface and need a machine-readable contract before implementation starts."
  youProvide: "The API surface — resources, actions, consumers, and any house standard to apply."
  youReceive: "A validated OpenAPI 3.1 or AsyncAPI 2.x contract file, versioned and ready to commit."
  yourDecisions:
    - "Review the contract before it drives implementation"
whatChanges: "After installing contracts, every API or event-driven interface starts from the contract, not the code. `api-contract` produces a validated OpenAPI 3.1 spec from requirements or a domain model; `event-contract` produces an AsyncAPI 2.x spec for event-driven interfaces. Both skills apply a pluggable house standard — Zalando by default, replaceable with your own base + delta bundle. A consumer-perspective check is built in; the contract drives implementation, not the other way."
skills:
  - name: api-contract
    description: "Authors an OpenAPI 3.1 contract from requirements or user stories — endpoints, request/response schemas, error codes, and the consumer-perspective check built in."
    humanTouches: 1
  - name: event-contract
    description: "Authors an AsyncAPI 2.x event contract for a stream interface — message shape, channel bindings, and the producer/consumer boundary made explicit."
    humanTouches: 1
humanGates:
  - id: G-contract
    globalGate: null
    label: "Review the contract before it drives implementation"
    trigger: "After api-contract or event-contract produces the first complete draft"
    duration: "10–20 minutes"
    whatToCheck:
      - "Does the contract reflect the agreed API surface — not a superset, not a subset of what was agreed?"
      - "Are the error codes complete? A contract that only specifies 200 responses is a best-case spec, not a contract."
      - "Are schema field names consistent with the team's existing naming conventions?"
      - "Does the contract specify what the consumer needs — or what the producer finds convenient to produce?"
      - "For event contracts: is the producer/consumer boundary explicit — does the contract name who owns the channel?"
    whatGoodLooksLike: "A contract that names all resources, all error codes, and all schemas — and reads from the consumer's perspective, not the implementation's. Every developer who reads it could build a compatible client without asking the author."
    whatBadLooksLike: "A contract that matches an existing implementation exactly — this means the agent described the implementation rather than the agreed surface. Or a contract that omits all 4xx/5xx error cases."
    consequence: "The contract is the implementation brief for every consumer of this API or event stream. A contract approved with missing error codes means every consumer discovers those errors through production failures, not through the spec."
typicalSession:
  agentTurns: "4–8"
  humanTouches: 1
  wallClockMinutes: "15–30"
docsUrl: /docs/guides/contracts/
packUrl: /packs/contracts/
relatedJourneys:
  - architect
  - core
---

| Say this | What happens |
|----------|-------------|
| `api-contract` | Author or review an OpenAPI 3.1 contract — endpoints, schemas, error codes |
| `event-contract` | Author or review an AsyncAPI 2.x event contract — channels and message shapes |

---

### 1. Author the contract

Type `api-contract` and describe the API surface — resources, actions, and the consumers who will call it.

```text
api-contract [orders service: create, get, cancel]

  Endpoint              Method   Schema
  /orders               POST     OrderCreate → OrderResponse
  /orders/{order_id}    GET      → OrderResponse
  /orders/{order_id}    DELETE   → (204 No Content)

  Error responses: 400, 404, 409, 500 (Problem schema)
```

- **Output:** a first-draft OpenAPI 3.1 contract — endpoints, schemas, and error responses taking shape.

---

### 2. Review from the consumer's perspective

The agent runs a consumer-perspective check against the house standard and surfaces the contract at the contract review gate.

```text
  Consumer-perspective check

  ● All endpoints secured (Bearer token)
  ● Error shapes consistent (Problem schema)
  ⚠ POST /orders: missing 409 Conflict for duplicate order_id

  Contract review ›
```

- **You decide:** approve the contract — check error codes first; a contract covering only 200 responses is incomplete.
- **Output:** a ratified contract covering the consumer's full perspective, including all error codes.

---

### 3. Commit the versioned contract

The agent emits the ratified contract as a versioned YAML file. For event-driven interfaces, run `event-contract` through the same review flow before committing.

```text
event-contract [order.placed event]

  Channel                     Message           Category
  orders/order.placed.v1      OrderPlacedV1     business-event

  Envelope: CloudEvents (structured mode)
  Payload:  order_id · customer_id · items[] · total_amount
```

- **Output:** versioned OpenAPI 3.1 or AsyncAPI 2.x contract files committed alongside the services they govern.
