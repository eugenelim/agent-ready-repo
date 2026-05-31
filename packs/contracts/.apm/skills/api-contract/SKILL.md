---
name: api-contract
description: Use when generating an OpenAPI 3.1 API contract from requirements, user stories, or domain models. Applies a pluggable API standard (Zalando by default) as hard constraints to produce complete, validated YAML specs ready for code gen, test gen, mocks, and SDKs. Activate for tasks involving API design, REST contract authoring, or OpenAPI spec creation.
---

# API Contract Generation

> **Standard-driven.** This skill carries the API-design *method*; the rules it
> enforces are *data* supplied by the **active standard**. The bundled default
> is Zalando (`references/standards-manifest-zalando.yaml`). An organisation can
> plug in its own standard as a base+delta bundle without forking this skill —
> see [references/standards-authoring.md](references/standards-authoring.md).

## Your Role

You are an API contract author inside an SDLC pipeline, following the active standard's API-first principle.

**Inputs you receive:** user stories, domain models, plain-English requirements, existing partial specs.

**Output you produce:** a single, complete, valid OpenAPI 3.1 YAML document that downstream tooling (code generators, test generators, mock servers, SDK builders) can consume without modification.

## The active standard

Before authoring, resolve the **active standard** — the data this method applies:

1. **Read the standard manifest.** The default is `references/standards-manifest-zalando.yaml`. If your organisation installed a custom standard (a bundle that `extends` the base, delivered via `adapt-to-project`'s `.upstream` companion-merge), read that instead.
2. **Load rule files per phase.** The manifest names the standard's rule files (grouped by the phases below), its quality-gate checklist, and any reusable schema components. Load the rule file for each phase as you reach it.
3. **Resolve base + delta by reading.** If the manifest `extends` a base, apply the base's rules first, then the delta: a rule the delta sets to `false` is disabled; rules under `adds` are additional house rules. Nothing parses the manifest for you — you resolve it by reading.

Every MUST / MUST-NOT in the active standard is a non-negotiable rail. SHOULD rules are followed unless you document the deviation inline with a rationale comment. The rule numbers and the specific conventions — casing, path grammar, pagination policy, error format, versioning strategy — all come from the active standard; this method does not hardcode them.

## Design Method

Follow these phases in order. Do not skip ahead. For each phase, load the active standard's rule file for that category (named in the manifest) and apply its rules.

### Phase 1 — Understand & Model

1. **Parse requirements.** Extract resources, relationships, operations, and business invariants from the input.
2. **Identify the domain model.** Define useful resources with clear identity and lifecycle, name them in domain language, model complete business processes, and map relationships (1:1, 1:N, M:N) to decide nesting depth — within the active standard's limits.
3. **Choose audience.** Tag the API's audience as the active standard requires (e.g. external-public / external-partner / company-internal).
4. **Assign API meta.** Populate `info` (title, description, version), contact, and any standard-required identifiers (e.g. an API id / audience extension).

### Phase 2 — Design URLs & Methods

1. **Build resource paths** following the active standard's naming and structure rules (casing, pluralisation, verb policy, prefix policy, normalisation, depth limits).
2. **Map operations to HTTP methods** following the standard's method-semantics and idempotency rules. Load the methods/status rule file.
3. **Define query parameters** using the standard's naming and conventional-parameter rules; paginate list endpoints as the standard requires. Load the pagination/filtering rule file.

### Phase 3 — Design Representations

1. **Payloads & media types** per the standard's representation rules (body format, top-level shape, permitted JSON-derived media types).
2. **Property naming** per the standard (casing, array pluralisation, date/time suffixes, common field names).
3. **Data formats** per the standard (standard `format` values, number formats, date/time and country/language/currency encodings). Load the data-formats rule file.
4. **Null handling** per the standard.
5. **Reusable objects.** Use the standard's reusable schema components (named in the manifest — e.g. Money, Problem) where applicable.
6. **Enumerations** per the standard (value casing; open vs. closed enums for evolvable value sets).

### Phase 4 — Error Handling & Status Codes

1. **Specify success and error responses** for every operation, using only official HTTP status codes as the standard requires.
2. **Use the standard's error format** for all error responses; never expose stack traces.
3. **Batch / rate-limit** semantics per the standard. Load the methods/status rule file for the full matrix.

### Phase 5 — Security & Headers

1. **Secure every endpoint** with a `security` scheme; define auth flows and scope naming per the standard.
2. **Encoding, caching, partial responses** per the standard where applicable.

### Phase 6 — Compatibility & Extensibility

1. **Avoid breaking changes** to published APIs; follow the standard's compatible-extension and tolerant-reader rules.
2. **Versioning** per the standard's strategy. Load the compatibility/versioning rule file.

### Phase 7 — Hypermedia & Events

1. **REST maturity / hypermedia** per the standard. Load the hypermedia/performance rule file.
2. **If the domain includes asynchronous events,** treat event schemas as API contracts and apply the standard's event rules. Load the events rule file.

## Design discipline

Standard-independent practice — true whatever the active standard says. The *specific* rules (pagination, error format, URL grammar, versioning) belong to the active standard; these are about the craft of contract-first design.

**Rationalizations to reject:**

| Rationalization | Reality |
| --- | --- |
| "We'll document the API later." | The contract *is* the documentation. Author it first (API-first). |
| "Internal APIs don't need a contract." | Internal consumers are still consumers; a contract prevents coupling and enables parallel work. |
| "Nobody depends on that undocumented behavior." | Hyrum's Law: every observable behavior becomes a de-facto contract. Treat it as a commitment. |
| "We'll handle compatibility when we need to." | Compatibility is a day-one design concern; design for extension up front (specifics per the active standard). |

**Red flags** (consistency properties — the active standard decides the specific rule):

- A representation's shape varies across endpoints without the active standard sanctioning it.
- Error shape varies across endpoints without the active standard sanctioning it.
- Unplanned breaking changes to existing fields (type changes, removals).
- Authoring before reading the active standard's rules.

## Quality Gates

Before finalizing the output, verify every item in the active standard's quality-gate checklist (named in the manifest — for Zalando, [references/standards-quality-gates-zalando.md](references/standards-quality-gates-zalando.md)). A single failure means the spec is not ready.

## Output Format

Produce a single OpenAPI 3.1 YAML document. The active standard governs the specifics; in general it has these top-level keys:

- `openapi: "3.1.0"`
- `info` — title, description, version, contact, and any standard-required identifiers
- `servers`
- `security` — global auth as the standard requires
- `paths` — every operation has responses + security, named per the standard
- `components/schemas` — domain schemas plus the standard's reusable components (e.g. Money, Problem, page objects)
- `components/parameters` — reusable query parameters
- `components/responses` — reusable error responses in the standard's error format
- `components/securitySchemes` — auth schemes with scope naming per the standard

For the bundled Zalando standard, see `references/golden-example.yaml` for a complete validated example.

## Reference Files

The active standard's manifest names its rule files; load the one for the phase you're in. For the bundled Zalando standard:

| Your API has...              | Load this reference                          |
| ---------------------------- | -------------------------------------------- |
| Multiple endpoints           | naming-conventions.md                        |
| Non-trivial CRUD             | http-methods-and-status-codes.md             |
| Money, dates, or enums       | data-formats-and-common-objects.md           |
| List endpoints               | pagination-and-filtering.md                  |
| Published consumers          | compatibility-and-versioning.md              |
| Caching or embedding needs   | hypermedia-and-performance.md                |
| Async events or webhooks     | events.md                                    |

Full reference index:

| Reference                                                                            | Covers                                                    |
| ------------------------------------------------------------------------------------ | --------------------------------------------------------- |
| [standards-manifest-zalando.yaml](references/standards-manifest-zalando.yaml)       | The active standard (default): attribution, rule-file map, quality gates, components |
| [standards-authoring.md](references/standards-authoring.md)                         | How to plug in your organisation's own standard (base + delta) |
| [standards-quality-gates-zalando.md](references/standards-quality-gates-zalando.md) | The Zalando quality-gate checklist                        |
| [naming-conventions.md](references/naming-conventions.md)                           | URL paths, property names, enums, field suffixes          |
| [http-methods-and-status-codes.md](references/http-methods-and-status-codes.md)     | Method semantics, status code selection, idempotency      |
| [data-formats-and-common-objects.md](references/data-formats-and-common-objects.md) | Standard formats, Money, Address, Problem schemas         |
| [pagination-and-filtering.md](references/pagination-and-filtering.md)               | Cursor vs offset, page object, conventional params        |
| [compatibility-and-versioning.md](references/compatibility-and-versioning.md)       | Breaking changes, extension rules, media type versioning  |
| [hypermedia-and-performance.md](references/hypermedia-and-performance.md)           | REST maturity, caching, compression, partial responses    |
| [events.md](references/events.md)                                                   | Event rules, event categories, schemas                    |

---

_The bundled Zalando standard is a derivative work; its attribution and licence (CC-BY-4.0) live in `references/standards-manifest-zalando.yaml`._
