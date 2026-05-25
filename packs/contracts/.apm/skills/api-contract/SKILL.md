---
name: api-contract
description: Use when generating an OpenAPI 3.1 API contract from requirements, user stories, or domain models. Applies 138 RESTful API rules as hard constraints to produce complete, validated YAML specs ready for code gen, test gen, mocks, and SDKs. Activate for tasks involving API design, REST contract authoring, or OpenAPI spec creation.
---

# API Contract Generation

> Derived from the [Zalando RESTful API Guidelines](https://opensource.zalando.com/restful-api-guidelines/) (CC-BY-4.0, Zalando SE).
> 138 of 143 rules apply. 5 Zalando-internal rules excluded: #183, #184, #223, #224, #233.

## Your Role

You are an API contract author inside an SDLC pipeline, following the API-first principle [#100].

**Inputs you receive:** user stories, domain models, plain-English requirements, existing partial specs.

**Output you produce:** a single, complete, valid OpenAPI 3.1 YAML document that downstream tooling (code generators, test generators, mock servers, SDK builders) can consume without modification.

The Zalando rules below are **hard constraint rails** -- every MUST/MUST NOT is non-negotiable. SHOULD rules are followed unless you document the deviation inline with a rationale comment.

## Design Method

Follow these phases in order. Do not skip ahead.

### Phase 1 -- Understand & Model

1. **Parse requirements.** Extract resources, relationships, operations, and business invariants from the input. For complex APIs, plan an API user manual [#102].
2. **Identify the domain model.** Define useful resources with clear identity and lifecycle [#140]. Name resources using domain language [#142]. Model complete business processes [#139]. Map relationships (1:1, 1:N, M:N) to decide nesting depth (max 3 segments after the root) [#147].
3. **Choose audience.** Tag `x-audience` [#219] -- `external-public`, `external-partner`, or `company-internal`.
4. **Assign API meta.** Populate `info.title`, `info.description`, `info.version` (semantic versioning) [#218][#116], `info.contact`, and `x-api-id` (UUID) [#215].

### Phase 2 -- Design URLs & Methods

1. **Build resource paths.** Use kebab-case [#129], plural nouns [#134], no verbs [#141], no `/api` prefix [#135], normalized (no trailing slash, no duplicated slashes) [#136]. Use URL-friendly resource IDs [#228].
2. **Map operations to HTTP methods.** Follow method semantics exactly [#148][#149]. Use idempotent POST/PATCH via `Idempotency-Key` where needed [#229]. See [references/http-methods-and-status-codes.md](references/http-methods-and-status-codes.md).
3. **Define query parameters.** Use snake_case [#130], conventional names (`q`, `sort`, `cursor`, `limit`, `fields`, `embed`) [#137]. Paginate all list endpoints [#159], prefer cursor-based [#160]. See [references/pagination-and-filtering.md](references/pagination-and-filtering.md).

### Phase 3 -- Design Representations

1. **JSON payloads.** Request and response bodies MUST be JSON [#167] with top-level objects (no bare arrays) [#110]. JSON-derived media types are permitted: `application/merge-patch+json` for PATCH [#148], `application/problem+json` for errors [#176].
2. **Property naming.** `snake_case` [#118], no null booleans [#122]. Pluralize array names [#120]. Use `_at` suffix for date-time, `_date` for date-only [#235]. Follow common field names [#174].
3. **Data formats.** Use standard `format` values [#238] and explicit number formats (`int32`, `int64`, `decimal`) [#171]. ISO 8601 for date-time [#169]. ISO 3166/639/4217 for country/language/currency [#170]. See [references/data-formats-and-common-objects.md](references/data-formats-and-common-objects.md).
4. **Null handling.** Define null semantics clearly [#123]. Never return null for booleans [#122] or empty arrays [#124].
5. **Reusable objects.** Use the standard Money [#173] and Address [#249] objects from `#/components/schemas/`. Use a single schema for read and write where possible [#252].
6. **Enumerations.** Use UPPER_SNAKE_CASE enum values [#240]. For evolvable value sets, use `examples` keyword (not closed `enum`) to signal open-ended values [#112].

### Phase 4 -- Error Handling & Status Codes

1. **Specify success and error responses** for every operation [#151]. Use official HTTP status codes only [#243].
2. **Use RFC 9457 Problem Detail** (`application/problem+json`) for all error responses [#176]. Never expose stack traces [#177].
3. **Batch operations** return `207 Multi-Status` [#152]. Rate-limited endpoints return `429` with `Retry-After` [#153].
4. See [references/http-methods-and-status-codes.md](references/http-methods-and-status-codes.md) for the full method-to-status-code matrix.

### Phase 5 -- Security & Headers

1. **Secure every endpoint** with a `security` scheme [#104]. Define OAuth2 flows and scopes [#105] using `<api-name>.<resource>.<access-level>` naming [#225].
2. **Support gzip** via `Accept-Encoding` [#156].
3. **Document caching** behavior with `Cache-Control` headers where applicable [#227].
4. **Support partial responses** via `fields` query parameter for large resources [#157].

### Phase 6 -- Compatibility & Extensibility

1. **Do not introduce breaking changes** to published APIs [#106]. Follow the compatible extension rules [#107].
2. **Design for tolerant readers** [#108] and **open for extension** [#111].
3. **Version via media types** if needed [#114]. Never version in the URL [#115].
4. See [references/compatibility-and-versioning.md](references/compatibility-and-versioning.md).

### Phase 7 -- Hypermedia & Events

1. **Target REST maturity level 2** (HTTP verbs + status codes) [#162]. Add hypertext controls for navigation [#164] using absolute URIs [#217].
2. **If the domain includes asynchronous events,** treat event schemas as API contracts [#194] and apply event rules. See [references/events.md](references/events.md) for categories [#198], metadata [#247], data change events [#202], and backward compatibility [#209].
3. See [references/hypermedia-and-performance.md](references/hypermedia-and-performance.md).

## Quality Gates

Before finalizing the output, verify every item. A single failure means the spec is not ready.

### Structural Validity

- [ ] Valid OpenAPI 3.1 YAML (parseable, no `$ref` errors)
- [ ] `info.title`, `info.description`, `info.version`, `info.contact` present [#218]
- [ ] `x-api-id` is a UUID [#215]
- [ ] `x-audience` is set [#219]
- [ ] Semantic version format in `info.version` [#116]

### Security

- [ ] Every operation has a `security` entry [#104]
- [ ] OAuth2 scopes defined and assigned [#105]
- [ ] Scope names follow `<api>.<resource>.<access>` [#225]

### URL Design

- [ ] All paths kebab-case, plural, verb-free [#129][#134][#141]
- [ ] No `/api` prefix [#135]
- [ ] Sub-resource depth at most 3 [#147]
- [ ] Query parameters are snake_case [#130]

### Representations

- [ ] All request/response bodies are JSON-based (`application/json`, `application/merge-patch+json`, or `application/problem+json`) [#167]
- [ ] All top-level responses are objects (no bare arrays) [#110]
- [ ] Properties are snake_case [#118]
- [ ] Boolean properties are non-nullable [#122]
- [ ] Array properties are pluralized [#120] and non-null when empty [#124]
- [ ] Number properties have explicit `format` [#171]
- [ ] Date-time uses ISO 8601 `format: date-time` [#169]
- [ ] Enums are UPPER_SNAKE_CASE [#240]
- [ ] Money uses common object [#173]

### Responses & Errors

- [ ] Every operation specifies success + error responses [#151]
- [ ] Error responses use `application/problem+json` [#176]
- [ ] No stack traces in error examples [#177]
- [ ] Only official HTTP status codes used [#243]

### Pagination

- [ ] All list endpoints paginated [#159]
- [ ] Pagination links provided [#161]
- [ ] Page object uses common schema [#248]

### Compatibility

- [ ] No breaking changes to existing published fields [#106]
- [ ] Extensible enums use `examples` keyword (not closed `enum`) [#112]
- [ ] No URL versioning [#115]

## Output Format

Produce a single OpenAPI 3.1 YAML document with these top-level keys:

- `openapi: "3.1.0"`
- `info` — title, description, version (`MAJOR.MINOR.PATCH`) [#116][#218], contact, `x-api-id` (UUID) [#215], `x-audience` [#219]
- `servers` — no `/api` prefix [#135]
- `security` — global OAuth2 [#104]
- `paths` — kebab-case [#129], plural [#134], verb-free [#141]; every operation has responses + security
- `components/schemas` — domain schemas (snake_case [#118], explicit formats [#171]), Money [#173], Address [#249], Problem [#176], page objects [#248]
- `components/parameters` — reusable cursor, limit, fields, sort [#137]
- `components/responses` — reusable error responses using Problem Detail [#176]
- `components/securitySchemes` — OAuth2 with scopes named `<api>.<resource>.<access>` [#225]

See `references/golden-example.yaml` for a complete validated example.

## Reference Files

Load selectively based on what your API needs:

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
| [naming-conventions.md](references/naming-conventions.md)                           | URL paths, property names, enums, field suffixes          |
| [http-methods-and-status-codes.md](references/http-methods-and-status-codes.md)     | Method semantics, status code selection, idempotency      |
| [data-formats-and-common-objects.md](references/data-formats-and-common-objects.md) | Standard formats, Money, Address, Problem schemas         |
| [pagination-and-filtering.md](references/pagination-and-filtering.md)               | Cursor vs offset, page object, conventional params        |
| [compatibility-and-versioning.md](references/compatibility-and-versioning.md)       | Breaking changes, extension rules, media type versioning  |
| [hypermedia-and-performance.md](references/hypermedia-and-performance.md)           | REST maturity, caching, compression, partial responses    |
| [events.md](references/events.md)                                                   | All 20 event rules (#194-#247), event categories, schemas |

---

_Based on the [Zalando RESTful API Guidelines](https://opensource.zalando.com/restful-api-guidelines/) by Zalando SE, licensed under [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/). This is a derivative work reformatted for agent consumption._
