# `contracts` — guides

`contracts` is the pack for contract-first design: write the agreement before the code. It ships two skills — `api-contract` for synchronous REST (OpenAPI 3.1) and `event-contract` for asynchronous streams (AsyncAPI) — each applying a design *method* over a pluggable house standard. The bundled default is the Zalando guidelines; swap in your own as a base + delta bundle without forking the skill.

New here? Read [contract-first design](explanation/contract-first-design.md) first — it's the *why*. Then author your first contract with [generate an API contract](how-to/generate-an-api-contract.md).

## How-to

Task-oriented recipes for a problem you already have.

- [Generate an API contract](how-to/generate-an-api-contract.md) — run `api-contract` over requirements, user stories, or a domain model to get a validated OpenAPI 3.1 spec.
- [Author an event contract](how-to/author-an-event-contract.md) — run `event-contract` for a stream you produce, with the produce-vs-consume check up front.

## Reference

Information-oriented, dry and complete.

- [The contract skills](reference/contract-skills.md) — both skills' inputs, outputs, phases, and the pluggable standard mechanism.

## Explanation

Understanding-oriented — the *why* behind the design.

- [Contract-first design](explanation/contract-first-design.md) — designing the contract before the code, and the pluggable house standard.

---

Cross-cutting guides — installing the catalogue, upgrading packs, the adapter support matrix — live in [`../_shared/`](../_shared/).
