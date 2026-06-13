# Contract-first design

A contract is the agreement between an API and everyone who calls it. Contract-first means you write that agreement *before* the code, not after. The OpenAPI or AsyncAPI document is the source of truth; the implementation is one consumer of it, alongside the test suite, the mock server, the SDK, and the docs.

The `contracts` pack ships two skills for this — `api-contract` for synchronous REST (OpenAPI 3.1) and `event-contract` for asynchronous streams (AsyncAPI). Both run the same discipline: design the contract, validate it, then build against it.

## Why the contract comes first

The contract is the documentation. Author it after the code and it describes whatever the code happened to do — accidents and all. Author it first and it describes what you *meant*, which is the thing consumers actually integrate against.

A few rationalizations the skills are built to reject:

- **"We'll document the API later."** Later never has the design context that now has. The contract written first is the design.
- **"Internal APIs don't need a contract."** Internal consumers are still consumers. A contract prevents coupling and lets producer and consumer teams build in parallel.
- **"Nobody depends on that undocumented behavior."** Hyrum's Law: every observable behavior becomes a de-facto contract whether you wrote it down or not. Treat it as a commitment from the start.

Design a contract first and the downstream tooling falls out of it for free. The same document feeds code generators, test generators, mock servers, and SDK builders — without modification.

## The pluggable house standard

A contract isn't just "valid OpenAPI." It's valid OpenAPI that follows *your* conventions: how you name paths, how you shape errors, how you paginate, how you version. Two teams writing valid specs can still write two incompatible APIs.

So the skills separate the *method* from the *rules*. The method — model the domain, design the URLs, design the representations, handle errors, secure the endpoints, plan for compatibility — is what the skill carries. The rules are *data*, supplied by an **active standard** the skill reads.

The bundled default is the [Zalando RESTful API Guidelines](https://opensource.zalando.com/restful-api-guidelines/) (CC-BY-4.0) — a mature, public, battle-tested ruleset. Every MUST and MUST-NOT becomes a non-negotiable rail; SHOULD rules are followed unless the author documents the deviation inline.

When Zalando isn't your house style, you plug in your own. You write a small **base + delta** bundle that `extends` the default: disable an inherited rule by setting it to `false`, add your own house rules under `adds`. No forking the skill. It's the same model Spectral popularised (`extends: spectral:oas` plus a `rules` override). The whole standard is *agent-read* — no program parses it; the skill resolves base and delta by reading them, the way it reads any reference file.

The `event-contract` skill takes this one axis further. Its standard has **two** swappable parts: the event-design ruleset (Axis A, Zalando-events by default) and the message envelope (Axis B, CloudEvents 1.0.2 by default). Swap the envelope for EventBridge-native, Avro, or bare JSON Schema by overriding a single `components.envelope` key — the method that composes it into each message stays identical.

## Where to read next

- [Generate an API contract](../how-to/generate-an-api-contract.md) — run `api-contract` against requirements or user stories.
- [Author an event contract](../how-to/author-an-event-contract.md) — run `event-contract` for a stream you produce.
- [The contract skills](../reference/contract-skills.md) — the exact inputs, outputs, and standard mechanism for both.
