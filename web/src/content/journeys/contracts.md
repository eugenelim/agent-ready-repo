---
pack: contracts
scope: user
tagline: "OpenAPI 3.1 and AsyncAPI — API-first design."
prerequisitePacks: []
contract:
  useItWhen: "You are designing an API or event-driven interface and need a machine-readable contract before implementation starts."
  youProvide: "The API surface — resources, actions, consumers, and any house standard to apply."
  youReceive: "A validated OpenAPI 3.1 or AsyncAPI 2.x contract file, versioned and ready to commit."
  yourDecisions:
    - "Review the contract before it drives implementation"
whatChanges: "After installing contracts, API design starts from the contract, not the code. `api-contract` produces a validated OpenAPI 3.1 spec from requirements, user stories, or a domain model. `event-contract` produces an AsyncAPI 2.x spec for event-driven interfaces. Both skills apply a pluggable house standard — the Zalando guidelines by default, your own base + delta bundle without forking the skill."
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

### 1. Author the contract

- **You provide:** a description of the API surface — resources, actions, consumers, and any house naming conventions.
- **Agent does:** runs `api-contract` or `event-contract` with the pluggable house standard configured (Zalando guidelines by default), producing a first-draft contract: endpoints, request/response schemas, error codes, and a consumer-perspective check.
- **You do:** watch the draft take shape and note corrections as they arise — don't wait for the full draft to redirect on a naming convention or a missing error case; if you know the consumer will call this API in a specific way, say so before the agent finalizes the response schemas.
- **Output:** a first-draft contract ready for consumer-perspective review.

---

### 2. Review from the consumer's perspective

- **Agent does:** runs a self-review against the house standard and surfaces the contract for your review at the G-contract gate.
- **You decide:** read through the error responses first — the most common failure mode is a contract that specifies the happy path thoroughly but skips 400, 404, or 500 cases; name any missing error cases explicitly, and correct naming inconsistencies before implementation begins.
- **Output:** a ratified contract that covers the consumer's full perspective, including all error codes.

---

### 3. Commit the versioned contract

- **Agent does:** emits the ratified contract as a versioned OpenAPI 3.1 or AsyncAPI 2.x file, ready to commit alongside the implementation it governs.
- **You do:** confirm the contract file is placed alongside the service it governs — not in a separate repository or a documentation folder that would diverge from the service over time.
- **Output:** a versioned contract file committed alongside its implementation.
