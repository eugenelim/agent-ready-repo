# The contract skills

The `contracts` pack ships two skills. Both apply a contract-design *method* over a pluggable *standard* supplied as data. This page describes their inputs, outputs, and the standard mechanism.

## `api-contract`

Generates an OpenAPI 3.1 API contract.

- **Source:** [`packs/contracts/.apm/skills/api-contract/SKILL.md`](../../../../packs/contracts/.apm/skills/api-contract/SKILL.md)
- **Activates on:** API design, REST contract authoring, OpenAPI spec creation.
- **Inputs:** user stories, domain models, plain-English requirements, existing partial specs.
- **Output:** a single, complete, valid OpenAPI 3.1 YAML document that downstream tooling (code generators, test generators, mock servers, SDK builders) consumes without modification.

### Phases

Applied in order; the skill does not skip ahead.

| Phase | Produces |
| --- | --- |
| 1. Understand & model | resources, relationships, operations, invariants; audience; `info` |
| 2. Design URLs & methods | resource paths; operation→HTTP-method mapping; query params |
| 3. Design representations | payloads, property naming, data formats, null handling, reusable objects, enums |
| 4. Error handling & status codes | success + error responses per operation, in the standard's error format |
| 5. Security & headers | `security` scheme per endpoint; auth flows; scope naming |
| 6. Compatibility & extensibility | compatible-extension and tolerant-reader design; versioning |
| 7. Hypermedia & events | REST maturity; event schemas surfaced inside the REST contract |

### Output keys

Top-level keys of the emitted document: `openapi: "3.1.0"`, `info`, `servers`, `security`, `paths`, and `components` (`schemas`, `parameters`, `responses`, `securitySchemes`). The active standard governs the specifics.

## `event-contract`

Authors an AsyncAPI event contract for a stream you produce.

- **Source:** [`packs/contracts/.apm/skills/event-contract/SKILL.md`](../../../../packs/contracts/.apm/skills/event-contract/SKILL.md)
- **Activates on:** event-driven API design, event/message contract authoring, AsyncAPI spec creation.
- **Inputs:** user stories, domain models, plain-English requirements, an existing partial contract, the producing service's emitted events.
- **Output:** a single, complete, valid AsyncAPI YAML document — `channels`, `operations`, `components.messages`, `components.schemas` — with the active envelope composed into the messages.

### Produce vs. consume

The skill authors **only when the feature produces or owns the event type.**

| The feature… | Action |
| --- | --- |
| Produces / owns the event type | Author or modify the contract in `contracts/asyncapi/`. |
| Consumes an event with an in-repo contract | No authoring; reference the producer contract; no back-pointer. |
| Consumes an event with no in-repo contract | No authoring; no fabricated contract. |

### Phases

| Phase | Produces |
| --- | --- |
| 1. Model the event domain | event types around business resources; ownership confirmed |
| 2. Name event types | names → `channel` + `components.messages` member |
| 3. Choose categories | general / data-change / business classification |
| 4. Design the message envelope | active envelope composed in, structured or binary mode |
| 5. Design payload schemas | snake_case payloads, ISO formats, reference ids, closed schemas |
| 6. Ordering & partitioning | ordering field, partition key, idempotent/out-of-order tolerance |
| 7. Compatibility & versioning | compatibility mode; new-major-on-parallel-type for breaks |
| 8. Quality gates | standard checklist verified |
| 9. Emit the document | AsyncAPI document at the manifest's output-target version |

### Output keys

Top-level keys: `asyncapi` (version from the manifest's output target), `info`, `channels`, `operations`, `components.messages`, `components.schemas`, and `x-spec` (present only when authored against a real spec).

## The pluggable standard

Both skills carry the *method*; the *rules* are data supplied by an **active standard** the skill reads. No program parses the standard — the skill resolves it by reading, the way it reads any reference file.

### `api-contract` standard (one axis)

- **Default:** Zalando RESTful API Guidelines, bundle version `1.0.0` (CC-BY-4.0, Zalando SE). 138 of Zalando's 143 rules apply; 5 Zalando-internal rules (#183, #184, #223, #224, #233) are excluded.
- **Manifest:** `references/standards-manifest-zalando.yaml` — names the per-phase rule files, the quality-gate checklist, the golden example, and reusable components (`money`, `problem`).
- **Custom standard:** write a base + delta bundle that `extends` the default. Disable an inherited rule with `"#<id>": false`; add house rules under `adds`. No skill fork. See `references/standards-authoring.md`.

### `event-contract` standard (two axes)

- **Axis A — event-design ruleset.** Default: Zalando-events, bundle version `1.0.0` (CC-BY-4.0, Zalando SE; chapters 19-21, ~24 numbered rules restated for AsyncAPI 3.1.0). Manifest: `references/standards-manifest-zalando-events.yaml`.
- **Axis B — message envelope.** Default: CloudEvents 1.0.2, named by the manifest's reserved `components.envelope` key. Swap it for EventBridge-native, Avro, or bare JSON Schema by overriding that one key — the method is unchanged.
- **Output target:** AsyncAPI `3.1.0`, named in the manifest's `output` block (a spec bump is a one-line manifest edit, never a skill change).
- **Custom standard:** a base + delta bundle that `extends` the default, on either axis. See `references/standards-authoring.md`.

In every active standard, MUST / MUST-NOT rules are non-negotiable rails; a SHOULD is followed unless the author documents the deviation inline.

## Related

- [Contract-first design](../explanation/contract-first-design.md) — why the contract precedes the code, and the standard plug explained.
- [Generate an API contract](../how-to/generate-an-api-contract.md).
- [Author an event contract](../how-to/author-an-event-contract.md).
