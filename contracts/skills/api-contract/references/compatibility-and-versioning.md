# Compatibility and Versioning

> Derived from the [Zalando RESTful API Guidelines](https://opensource.zalando.com/restful-api-guidelines/) (CC-BY-4.0, Zalando SE).

These rules govern how APIs evolve without breaking existing consumers. Compatibility
is the single most important long-term quality of a public API.

---

## [#106] MUST not break backward compatibility

Every change to a published API MUST be backward compatible. The following changes
are **breaking** and therefore forbidden without a new major version:

| Category | Breaking change examples |
|---|---|
| **Endpoints** | Removing or renaming a path; changing the HTTP method |
| **Request parameters** | Removing a parameter; making an optional parameter required; renaming a parameter; changing a parameter's type or format |
| **Request body** | Adding a new required property; removing or renaming an existing property; changing a property's type, format, or constraints (e.g., tightening `maxLength`) |
| **Response body** | Removing or renaming a property; changing a property's type or format; changing the structure of a response object |
| **Status codes** | Removing a documented success or error status code; changing the semantics of an existing code |
| **Headers** | Removing a required response header; changing header semantics |
| **Authentication** | Removing or restricting OAuth scopes; changing auth schemes |
| **Enumerations** | Removing an enum value from a closed enum (see [#112] for open enums) |

**Safe (non-breaking) changes:** adding optional request parameters, adding response
properties, adding new endpoints, adding new HTTP methods to existing endpoints,
adding new enum values to open enums.

---

## [#107] SHOULD prefer compatible extensions

When evolving an API, SHOULD prefer additive, compatible changes over breaking ones:

- **Add** new optional request/query parameters with sensible defaults
- **Add** new properties to response objects
- **Add** new endpoints or resources
- **Add** new enum values to open-ended enumerations ([#112])
- **Support** new media types alongside existing ones

Design every change so that existing clients continue to work without modification.
When a breaking change is truly unavoidable, follow a deprecation-then-removal
lifecycle and coordinate with known consumers.

---

## [#108] MUST prepare clients to accept compatible API extensions

Clients (consumers) MUST implement the **tolerant reader** pattern:

- **Ignore** unknown properties in JSON response bodies — never fail on unexpected fields
- **Ignore** unknown enum values (treat as an unrecognized but valid state)
- **Ignore** new optional response headers
- **Do not** depend on the ordering of JSON properties
- **Do not** depend on the exact set of HTTP status codes beyond what is documented

This rule is the consumer-side counterpart to [#107]. Without tolerant readers,
even compatible extensions become de-facto breaking changes.

---

## [#109] SHOULD design APIs conservatively

Apply **Postel's Law** (the robustness principle):

> *Be conservative in what you send, be liberal in what you accept.*

- Send only well-defined, documented fields in responses — no leaking of internal state
- Accept unknown fields in request bodies gracefully (see [#111])
- Validate inputs, but do not reject requests solely because they contain extra properties

---

## [#110] MUST always return JSON objects as top-level data structures

Every JSON response body MUST have an **object** (`{}`) as the root — never a bare
array, string, number, or `null`.

```yaml
# Correct — array wrapped in an object
responses:
  '200':
    content:
      application/json:
        schema:
          type: object
          properties:
            items:
              type: array
              items:
                $ref: '#/components/schemas/Order'

# Wrong — bare array at root
responses:
  '200':
    content:
      application/json:
        schema:
          type: array
          items:
            $ref: '#/components/schemas/Order'
```

**Rationale:** Top-level objects allow adding new properties (e.g., `_links`,
`cursor`, `total_count`) without breaking the response shape, and they prevent
certain classes of JSON-based security vulnerabilities.

---

## [#111] MUST treat OpenAPI specification as open for extension by default

API schemas MUST allow additional, undocumented properties unless there is a
compelling reason to forbid them. In OpenAPI 3.x terms:

- Do **not** set `additionalProperties: false` on object schemas by default
- Consumers MUST tolerate unexpected properties ([#108])
- Providers MAY add new properties to response objects at any time ([#107])

Explicitly restricting `additionalProperties` is only appropriate for closed
domain objects where the property set is genuinely fixed (rare).

---

## [#112] SHOULD use open-ended list of values (via `examples`) for enumerations

For enumerations that may grow over time, SHOULD use the `examples` keyword
instead of a closed `enum`:

> **Historic note:** Prior to October 2025, the Zalando guidelines recommended
> `x-extensible-enum`. The current guideline uses the standard `examples` keyword.

```yaml
# Open enum — new values can be added without breaking clients
order_status:
  type: string
  examples:
    - placed
    - shipped
    - delivered
    - returned
  description: |
    Current status of the order.
    Clients MUST accept unknown values gracefully.

# Closed enum — only for truly fixed value sets (e.g., ISO country codes)
currency:
  type: string
  enum:
    - EUR
    - USD
    - GBP
```

**Key contract:** When an enum is open (uses `examples` instead of `enum`),
consumers MUST handle unknown values without failing ([#108]). Providers MAY add
new values at any time without a version bump.

---

## [#113] SHOULD avoid versioning

Versioning is a **last resort**. APIs SHOULD evolve through compatible extensions
([#107]) and tolerant readers ([#108]) instead of introducing new versions:

- Versioning multiplies maintenance burden — every version needs support, docs, tests
- Consumers must migrate, which creates coordination overhead
- Most "breaking" changes can be redesigned as compatible extensions

Only version when a fundamental, irreconcilable incompatibility is unavoidable.

---

## [#114] MUST use media type versioning

When versioning is unavoidable, MUST use **media type versioning** via the
`Content-Type` / `Accept` headers:

```
Content-Type: application/vnd.zalando.order+json;v=2
Accept: application/vnd.zalando.order+json;v=2
```

This keeps the URL space clean and makes version negotiation explicit in the HTTP
content negotiation layer.

---

## [#115] MUST not use URL versioning

MUST NOT include version numbers in URL paths:

```
# Wrong
GET /v1/orders/123
GET /v2/orders/123

# Correct — version in media type, not URL
GET /orders/123
Accept: application/vnd.zalando.order+json;v=2
```

URL versioning pollutes the resource namespace, breaks bookmarks, and conflates
resource identity with representation format.

---

## [#116] MUST use semantic versioning

The `info.version` field in the OpenAPI specification MUST follow **semantic
versioning** (MAJOR.MINOR.PATCH):

| Component | Increment when... |
|---|---|
| **MAJOR** | Incompatible / breaking changes (ideally never — see [#113]) |
| **MINOR** | Backward-compatible new functionality (new endpoints, optional fields) |
| **PATCH** | Backward-compatible bug fixes (documentation, typo corrections) |

```yaml
openapi: '3.1.0'
info:
  title: Order Service API
  version: '1.3.2'   # MAJOR.MINOR.PATCH
```

Start at `1.0.0` for the initial release. Pre-release APIs MAY use `0.x.y` to
signal instability.

---

## Quick-reference decision tree

```
Need to change the API?
  |
  +-- Can it be done as a compatible extension? [#107]
  |     YES --> Add it. Bump MINOR version. [#116]
  |
  +-- NO, it is a breaking change [#106]
        |
        +-- Can the design be reworked to avoid the break?
        |     YES --> Rework. [#113]
        |
        +-- NO, a version bump is truly required
              |
              Use media type versioning [#114]
              Never URL versioning [#115]
              Bump MAJOR version [#116]
```
