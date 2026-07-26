# Author an event contract

**Use this when:** You own an event type and need a complete, validated AsyncAPI contract for consumers to integrate against.
**Prerequisites:** `contracts` pack installed; know your active event-design standard (Axis A) and message envelope (Axis B).
**Result:** A single AsyncAPI YAML document with channels, operations, messages, and schemas ready for downstream consumers.

You're publishing an event stream — an order placed, a shipment dispatched, a price changed — and consumers need a contract to integrate against. The `event-contract` skill turns your requirements into a complete, validated AsyncAPI document.

## Before you start

- The `contracts` pack is installed (the skill lives at [`packs/contracts/.apm/skills/event-contract/`](../../../../packs/contracts/.apm/skills/event-contract/SKILL.md)).
- You know your **active standard** — the event-design ruleset (Axis A, Zalando-events by default) and the message envelope (Axis B, CloudEvents 1.0.2 by default). See [contract-first design](../explanation/contract-first-design.md) for what the two axes are and how to swap either.

## Check first: do you produce or consume?

Author a contract **only when your feature produces or owns the event type.** Consuming a stream is not owning it. The skill resolves to one of three outcomes before it writes anything:

| Your feature… | What happens |
| --- | --- |
| **Produces / owns** the event type | Author or modify the AsyncAPI contract — the full method below. |
| **Consumes** an event whose contract already lives in `contracts/asyncapi/` | No authoring. Reference the existing producer contract; add no back-pointer. |
| **Consumes** an event with no in-repo contract (external producer) | No authoring, no fabricated contract. Optionally note the upstream type you depend on. |

Fabricating a contract for a stream you only consume falsely claims ownership and drifts from the producer's real one. If in doubt, you're a consumer — ask who publishes the event.

## Invoke it

```text
Use event-contract to author the AsyncAPI contract for the order events we
publish: order.placed, order.cancelled. Order is the resource we own.
```

The skill activates on event-driven API design and AsyncAPI authoring. Give it the event types, the owning resource, and what state changes the events announce.

## What it does

Resolves the active standard, then walks nine phases in order:

1. **Model the event domain** — which state changes other services react to; defines types around meaningful business resources, not technical artifacts; confirms you produce each one.
2. **Name event types** — per the standard's naming rule; each name maps to an AsyncAPI `channel` and a `components.messages` member.
3. **Choose categories** — classifies each type (general / data-change / business), fixing its semantics, ordering, and payload shape.
4. **Design the message envelope** — composes the envelope the manifest names (CloudEvents by default) into each message, in structured or binary content mode per your broker.
5. **Design payload schemas** — snake_case properties, ISO formats, reference identifiers instead of sensitive data, closed schemas where the standard requires; reuses a REST resource's schema where a data-change event mirrors it.
6. **Ordering & partitioning** — ordering field per category, the partition key, and a design that tolerates out-of-order, at-least-once delivery.
7. **Compatibility & versioning** — declares each type's compatibility mode; a breaking change becomes a new major on a parallel type, never an in-place mutation.
8. **Quality gates** — verifies the standard's checklist; one failure means it isn't ready.
9. **Emit the document** — a single AsyncAPI document at the version the manifest's output target names.

## What you get back

One AsyncAPI YAML document with `channels`, `operations`, `components.messages` (each with the active envelope composed in), and `components.schemas` (business payloads plus the envelope schema). When you author against a real spec, it carries a top-level `x-spec` extension naming that spec; a standalone teaching example carries none.

## Variations and pitfalls

- **Structured vs. binary mode.** Structured mode nests the business payload under the envelope's `data` member; binary mode rides the envelope's context attributes as message headers. Pick per your broker.
- **Swapping the envelope.** Override the manifest's `components.envelope` key for EventBridge-native, Avro, or bare JSON Schema. The composition method is identical; only the composed component changes.
- **Sensitive data.** Never inline PII in a payload — events are persisted and replayed. Reference identifiers instead.
- **A REST contract instead.** For synchronous request/response, use [`api-contract`](generate-an-api-contract.md), which emits OpenAPI.

## Related

- [The contract skills](../reference/contract-skills.md) — the full input/output and standard reference for `event-contract`.
- [Generate an API contract](generate-an-api-contract.md) — the OpenAPI counterpart.
