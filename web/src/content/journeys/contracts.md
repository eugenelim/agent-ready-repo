---
pack: contracts
scope: user
tagline: "OpenAPI 3.1 and AsyncAPI — API-first design."
prerequisitePacks: []
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

## Stage 1 — Author the contract

You described the API surface — the resources, actions, and consumers. The agent ran `api-contract` or `event-contract` with the pluggable house standard configured (Zalando guidelines by default). It produced a first-draft contract: endpoints, request/response schemas, error codes, and the consumer-perspective check.

**You did:** Watched the draft take shape and noted corrections as they arose — don't wait for the full draft to redirect on a naming convention or a missing error case. Small corrections mid-draft are faster than a full re-generate. If you knew the consumer would call this API in a specific way, say so before the agent finalizes the response schemas.

---

## Stage 2 — Review from the consumer's perspective

After the first complete draft, the agent ran a self-review against the house standard. You reviewed the contract at the G-contract gate — reading from the consumer's perspective, not the producer's.

**You did:** Read through the error responses first. The most common failure mode is a contract that specifies the happy path thoroughly but skips error cases — a 200 response with no corresponding 400, 404, or 500. If an error case was missing, name it explicitly: the agent can't infer which errors are real without domain knowledge. If the schema field names used inconsistent conventions (camelCase in some places, snake_case in others), correct them here before implementation begins.

---

## Stage 3 — Versioned output

The ratified contract was emitted as a versioned OpenAPI 3.1 or AsyncAPI 2.x file, ready to commit alongside the implementation it governs.

**You did:** Confirmed the contract file was placed alongside the service it governs — not in a separate repository or a documentation folder that would diverge from the service over time. A contract that lives apart from its implementation will drift silently until a consumer discovers the mismatch.
