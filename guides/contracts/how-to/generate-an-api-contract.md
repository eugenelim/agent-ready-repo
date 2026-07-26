# Generate an API contract

**Use this when:** You own an API's resources and need a complete OpenAPI 3.1 contract from requirements, a domain model, or plain-English prose.
**Prerequisites:** `contracts` pack installed, active standard known (Zalando by default), and you are the API producer.
**Result:** A validated OpenAPI 3.1 YAML document ready to feed into code generators, mock servers, or SDK builders.

You have requirements — user stories, a domain model, plain-English prose, or a half-finished spec — and you need a complete OpenAPI 3.1 contract downstream tooling can consume without edits. This is the `api-contract` skill's job.

## Before you start

- The `contracts` pack is installed (the skill lives at [`packs/contracts/.apm/skills/api-contract/`](../../../../packs/contracts/.apm/skills/api-contract/SKILL.md)).
- You know your **active standard**. The bundled default is Zalando; if your org plugged in its own base + delta bundle, the skill reads that instead. See [contract-first design](../explanation/contract-first-design.md) for what the standard is and how to swap it.
- You're the *producer* of this API — you own the resources it exposes.

## Invoke it

Hand the skill your requirements in plain language:

```text
Use api-contract to generate an OpenAPI contract for an order-management
service: create an order, fetch it, list a customer's orders, cancel one.
```

The skill activates on API-design work — REST contract authoring, OpenAPI spec creation — so a clear description of the resources and operations is enough. The richer your input (domain model, lifecycle, invariants), the less the skill has to assume.

## What it does

The skill resolves the active standard, then walks seven phases in order — it does not skip ahead:

1. **Understand & model** — extracts resources, relationships, operations, and business invariants; picks the API's audience; populates `info`.
2. **Design URLs & methods** — builds resource paths and maps operations to HTTP methods, following the standard's naming and method-semantics rules.
3. **Design representations** — payloads, property naming, data formats, null handling, reusable objects (Money, Problem), enums.
4. **Error handling & status codes** — a success and error response for every operation, in the standard's error format, using only official status codes.
5. **Security & headers** — a `security` scheme on every endpoint, with auth flows and scope naming per the standard.
6. **Compatibility & extensibility** — designs for compatible extension and tolerant readers; applies the standard's versioning strategy.
7. **Hypermedia & events** — REST maturity per the standard; if the domain has async events, treats those schemas as contracts too.

Every MUST and MUST-NOT in the standard is a hard rail. A SHOULD the skill deviates from gets an inline rationale comment.

## What you get back

A single OpenAPI 3.1 YAML document with `info`, `servers`, `security`, `paths` (every operation carries responses and security), and `components` (domain schemas plus the standard's reusable components and reusable error responses). It's validated against the standard's quality-gate checklist before you see it — a single failure means it isn't ready.

Feed it straight into a code generator, a test generator, a mock server, or an SDK builder. No hand-editing required.

## Variations and pitfalls

- **Async events in the domain.** The `api-contract` skill covers events *surfaced inside* a REST contract (phase 7). For a standalone event stream you produce, reach for [`event-contract`](author-an-event-contract.md) instead — it emits AsyncAPI, not OpenAPI.
- **Partial spec as input.** Hand the skill an existing partial OpenAPI document and it fills the gaps against the standard rather than starting from scratch.
- **Your house style isn't Zalando.** Don't fork the skill. Plug in a base + delta standard bundle; the method is unchanged, only the rules differ. See [contract-first design](../explanation/contract-first-design.md#the-pluggable-house-standard).
- **You only consume this API.** Don't author a contract for an API you don't own — reference the producer's. Authoring one falsely claims ownership and drifts from the real thing.

## Related

- [The contract skills](../reference/contract-skills.md) — the full input/output and standard reference for `api-contract`.
- [Author an event contract](author-an-event-contract.md) — the AsyncAPI counterpart.
