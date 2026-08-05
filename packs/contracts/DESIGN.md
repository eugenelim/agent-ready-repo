# Contracts Pack — Design Document

Living design reference for the contracts pack. Records the philosophy, architecture, invariants, and key decisions so the reasoning survives beyond individual PRs and applies when extending or replacing either skill.

---

## TL;DR

`contracts` is the API-first design seat. Both skills — `api-contract` (OpenAPI 3.1) and `event-contract` (AsyncAPI 2.x) — run a multi-phase method against a pluggable house standard: Zalando by default, replaceable with any base + delta bundle without forking the skill. The contract drives implementation; the pack produces a versioned, validated YAML file the consumer can build against without talking to the author. Consumer-perspective check is built into every session. Human review happens at one gate: G-contract, before the contract feeds any build loop.

---

## Non-Goals

Things a reasonable reader might expect this pack to solve. It doesn't, by design:

- **Code generation from contracts.** The pack produces a contract that developers and downstream tooling (code generators, test generators, mock servers, SDK builders) consume. Generating stubs from the contract is a downstream tool concern, not a contract-authoring concern.
- **Runtime contract validation.** The pack validates the contract structure at authoring time. Whether a running service honors its contract is a separate concern — contract-testing and consumer-driven test suites.
- **Live API testing.** No HTTP calls, no mock server activation, no test-run integration. The output is a static YAML document, not a running mock.
- **Protocol-specific implementation stubs.** The pack does not emit framework-specific handler scaffolding, route registration, or serialization code. Those are build-loop outputs.

---

## 1. The contract-first principle

### Why the contract comes first

The API contract is the implementation brief for every consumer of the service. When code is written before the contract, the contract retroactively describes what the producer found convenient to implement — not what consumers need. Consumers who integrate against a convenience API discover missing cases (error shapes, pagination semantics, edge-case behavior) through production failures instead of through the spec.

Writing the contract first inverts the dependency: the contract describes the agreed consumer surface, and the implementation is constrained to fulfill it. This makes the spec a testable commitment rather than an after-the-fact description.

### The consumer-perspective check

Both skills apply a consumer-perspective check built into the method:

- **`api-contract`:** Phase 4 (Error Handling & Status Codes) requires specifying error responses for every operation. A contract that covers only 200 responses is a best-case spec, not a contract. Phase 2 (Design URLs & Methods) requires path and method semantics consistent with the active standard's rules — which are grounded in what the consumer expects from a REST interface.
- **`event-contract`:** Phase 1 (Model the event domain) requires deciding whether the feature *produces* the event type or merely *consumes* it — a feature that only consumes someone else's event is not a contract authoring event. Phase 3 (Choose categories) assigns category semantics that set ordering and delivery expectations for consumers.

---

## 2. The pluggable house standard

### What "pluggable" means

Both skills carry the *method* — phases, decision rules, design discipline — and apply *data* from the active standard: the specific rules, naming conventions, error format, versioning strategy, and message envelope. The bundled default is the Zalando RESTful API Guidelines for `api-contract`, and the Zalando Events Guidelines for `event-contract`.

An organization can replace the bundled standard by delivering a `base + delta` bundle via `adapt-to-project`'s companion-merge. The delta can disable rules (set to `false`), add house rules (under `adds`), and swap the message envelope (Axis B for event contracts). The skill doesn't need to be forked; the standard is data, not logic.

### Why Zalando guidelines as default

Zalando's guidelines are widely adopted, machine-readable, designed for extension, and explicitly cover the consumer perspective. A team can define a "base + delta" bundle that overrides specific rules without discarding the full standard. This makes them an appropriate default for a pack designed to be adopted across organizations with diverse API conventions.

### How base + delta resolves

If the active standard extends a base, the skill resolves by reading:
1. Apply the base rules first.
2. Apply the delta: rules set to `false` are disabled; rules under `adds` are additional constraints.
3. For event contracts, an envelope override under `components.envelope` swaps Axis B.

Nothing parses the manifest automatically — the skill resolves it by reading.

---

## 3. OpenAPI 3.1 and AsyncAPI 2.x in one pack

### Why one pack covers both

REST and event-driven contracts are designed by the same team at the same moment — when the service's boundaries are being defined, before implementation starts. Separating them into two packs would create unnecessary friction: teams building event-driven services alongside REST endpoints would need to install two packs to cover one design session.

Both skills share the same house standard (Zalando by default), the same gate (G-contract), and the same output model (a versioned YAML file committed alongside the service). Their methods are distinct; their contract-first principle is identical.

### Why OpenAPI 3.1, not 3.0

OpenAPI 3.1 aligns with JSON Schema 2020-12, enabling better schema reuse and unambiguous nullable field semantics. The `nullable: true` workaround in 3.0 is a known source of tooling inconsistency; 3.1's `type: ["string", "null"]` is explicit and standards-conformant.

### Why AsyncAPI 2.x, not 3.0

AsyncAPI 3.0 is still maturing; 2.x has broader tooling support and is the current stable version for event contract authoring. The version is governed by the manifest's `output target` field — when the ecosystem matures, adopters can update their standard manifest without forking the skill.

---

## 4. Human gate design

### G-contract — the one gate

| Gate | When | Duration | What to check |
|------|------|----------|---------------|
| **G-contract** | After `api-contract` or `event-contract` produces the first complete draft | 10–20 min | Are all error codes specified? Does the contract read from the consumer's perspective? Are schema field names consistent with team conventions? For event contracts: is the producer/consumer boundary explicit? |

### Why one gate, not zero

A contract without a human review creates a commitment consumers build against before the producer has verified it covers the agreed surface. The cost of a missing error code discovered in production is substantially higher than 10–20 minutes of review at contract time.

Zero gates is the wrong default because the contract is the implementation brief for every consumer — it is not an intermediate artifact but a public commitment.

### Why one gate, not two

Unlike `work-loop`, which gates at plan time and again at PR merge, `contracts` needs only one gate. The contract is the plan; the implementation is separately gated by the build loop (`work-loop`'s G-pr). Duplicating the contract review gate would pay the cost of G-pr twice for the same artifact.

---

## 5. Safety invariants

These constraints must never be violated by any skill in the contracts pack or any skill that extends it.

1. **Consumer-perspective check is non-negotiable.** No skill may produce a contract that specifies only success responses. Every operation requires at minimum the standard error codes the active standard mandates.

2. **The active standard is data, not a hardcoded rule set.** No rule number, naming convention, or error format may be hardcoded into the skill logic. All such rules come from the active standard's manifest and rule files.

3. **The event authoring boundary is produce-only.** `event-contract` must not author a contract for a stream the feature only consumes. A fabricated contract for a stream the feature doesn't own will drift from the producer's real contract, creating a false commitment.

4. **Versioned output files.** Both skills emit versioned YAML files. A contract without a version is not ready to commit — consumers cannot detect incompatible changes without a semantic version they can check.

5. **No stack-specific stubs.** Neither skill emits framework-specific code. The output is a YAML document; code generation belongs downstream.

---

## 6. Design decisions and rationale log

### Why Zalando guidelines as the bundled default (from v0.1)

Zalando's guidelines are: (a) widely adopted — many API platforms have trained their teams on them; (b) consumer-perspective explicit — they treat the consumer as the primary stakeholder, not the implementor; (c) designed for extension — the base + delta model is a design goal, not a retrofit. An organization that uses a different standard can deliver it as a delta bundle without forking the skill. A bundled default that assumes no standard is less useful than one that assumes a well-known standard the adopter can override.

**Alternative considered:** ship no bundled standard, require the adopter to supply one. Rejected because it creates an installation friction point that discourages the pack's primary use case (quick first-value: run `api-contract` on a service description and get a validated spec). The bundled default is a useful starting point, not a prescription.

### Why OpenAPI 3.1 instead of 3.0 (from v0.1)

OpenAPI 3.0's `nullable: true` extension is not part of the JSON Schema standard; it creates tooling inconsistency where code generators and validators interpret it differently. OpenAPI 3.1's `type: ["string", "null"]` follows JSON Schema 2020-12 exactly and resolves the inconsistency. Improved schema reuse (via `$defs` and relative `$ref`) was an additional benefit.

**Alternative considered:** support both 3.0 and 3.1 with a version flag. Rejected because maintaining two code paths in the skill and the active standard's rule files creates ongoing complexity without meaningful benefit — 3.0-era tools now have mature 3.1 support.

### Why AsyncAPI 2.x instead of 3.0 (from v0.1)

AsyncAPI 3.0 introduced breaking changes to the channel/operation model and had immature tooling support at the time of authoring. The version is governed by the manifest's output target field — adopters who need 3.0 can update their standard manifest's output target. The skill method does not hardcode the version; the manifest does.

**Alternative considered:** target AsyncAPI 3.0 only. Rejected because the tooling ecosystem (validators, code generators, documentation renderers) was not stable at 3.0 at the time of authoring. Choosing a version with immature tooling would break the pack's core value: a validated contract that downstream tooling can consume without modification.

### Why one pack for OpenAPI and AsyncAPI, not two (from v0.1)

Service boundary design is a single design session. When a team defines a service, they decide its REST interface and its event interface simultaneously. Requiring two pack installations for one design session creates unnecessary friction and a gap where teams design the REST contract but skip the event contract because of the additional step.

**Alternative considered:** separate `api-contracts` and `event-contracts` packs. Rejected because the install and invoke surface would double for teams that need both, and the shared concepts — active standard, G-contract gate, versioned YAML output — are not costly to maintain in one pack.
