# Data Formats and Common Objects Reference

> Derived from the [Zalando RESTful API Guidelines](https://opensource.zalando.com/restful-api-guidelines/).
> License: CC-BY-4.0 — Copyright Zalando SE. This is a derivative work.

This reference covers data format rules, JSON conventions, and common reusable
objects for OpenAPI 3.1 contract generation.

---

## JSON as Interchange Format [#167]

**MUST** use JSON (`application/json`) as the default data interchange format
for request and response payloads. All APIs must support JSON; other formats
are supplementary.

```yaml
paths:
  /orders:
    post:
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/OrderCreate"
      responses:
        "201":
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Order"
```

---

## Standard Data Formats [#238]

**MUST** use OpenAPI-defined format values for standard data types:

| Type      | Format      | Description                    | Example                        |
|-----------|-------------|--------------------------------|--------------------------------|
| `string`  | `date`      | ISO 8601 date                  | `2024-06-15`                   |
| `string`  | `date-time` | ISO 8601 date-time             | `2024-06-15T14:30:00Z`         |
| `string`  | `time`      | ISO 8601 time                  | `14:30:00`                     |
| `string`  | `duration`  | ISO 8601 duration              | `P1DT12H`                      |
| `string`  | `period`    | ISO 8601 interval              | `2024-01-01/2024-12-31`        |
| `string`  | `uri`       | RFC 3986 URI                   | `https://example.com/orders/1` |
| `string`  | `uri-reference` | Relative or absolute URI   | `/orders/1`                    |
| `string`  | `url`       | RFC 3986 URL                   | `https://example.com`          |
| `string`  | `email`     | RFC 5322 email address         | `user@example.com`             |
| `string`  | `hostname`  | RFC 1123 hostname              | `api.example.com`              |
| `string`  | `ipv4`      | RFC 2673 IPv4                  | `192.168.1.1`                  |
| `string`  | `ipv6`      | RFC 4291 IPv6                  | `::1`                          |
| `string`  | `uuid`      | RFC 4122 UUID                  | `550e8400-e29b-41d4-a716-...`  |
| `string`  | `password`  | Sensitive value (hint to UIs)  | `••••••••`                     |
| `string`  | `byte`      | Base64-encoded binary          | `dGVzdA==`                     |
| `string`  | `binary`    | Raw binary (for file uploads)  | —                              |
| `integer` | `int32`     | 32-bit signed integer          | `2147483647`                   |
| `integer` | `int64`     | 64-bit signed integer          | `9223372036854775807`          |
| `number`  | `float`     | 32-bit IEEE 754 float          | `3.14`                         |
| `number`  | `double`    | 64-bit IEEE 754 double         | `3.141592653589793`            |
| `number`  | `decimal`   | Arbitrary-precision decimal    | `29.99`                        |

---

## Number and Integer Formats [#171]

**MUST** define format for all number and integer types to ensure
interoperability across languages and platforms:

```yaml
# Correct — explicit format
quantity:
  type: integer
  format: int32
  minimum: 0
total_amount:
  type: number
  format: decimal
  description: Monetary amount — use decimal to avoid floating-point errors
weight_kg:
  type: number
  format: double

# Wrong — missing format
quantity:
  type: integer     # What size? int32? int64?
price:
  type: number      # float? double? decimal?
```

**Guideline for choosing format:**
- `int32` — Counts, quantities, small identifiers
- `int64` — Large identifiers, timestamps in millis
- `float` — Low-precision measurements (rarely used in APIs)
- `double` — Scientific/engineering values
- `decimal` — Monetary amounts, financial calculations (MUST for money)

---

## Date and Time — ISO 8601 [#169]

**MUST** use ISO 8601 / RFC 3339 formats for all date and time properties:

```yaml
created_at:
  type: string
  format: date-time
  description: Timestamp in UTC with timezone offset
  example: "2024-06-15T14:30:00Z"

due_date:
  type: string
  format: date
  description: Calendar date without time component
  example: "2024-07-01"
```

### Date vs. Date-Time [#255]

**SHOULD** choose the right format based on precision needs:

- Use `date` for calendar dates where time is irrelevant (birth dates,
  due dates, billing periods)
- Use `date-time` for timestamps where time precision matters (creation time,
  event times, deadlines)

```yaml
# Date — no time component needed
birth_date:
  type: string
  format: date
  example: "1990-05-20"

# Date-time — time precision needed
order_placed_at:
  type: string
  format: date-time
  example: "2024-06-15T14:30:00Z"
```

---

## Duration and Interval — ISO 8601 [#127]

**SHOULD** use ISO 8601 formats for duration and interval properties:

```yaml
# Duration
processing_time:
  type: string
  format: duration
  description: Expected processing time in ISO 8601 duration
  example: "P1DT12H"    # 1 day, 12 hours

# Interval (period)
billing_period:
  type: string
  format: period
  description: Billing period as ISO 8601 interval
  example: "2024-01-01/2024-03-31"
```

**Common duration patterns:**
- `PT30M` — 30 minutes
- `PT1H` — 1 hour
- `P1D` — 1 day
- `P7D` — 7 days
- `P1M` — 1 month
- `P1Y` — 1 year

---

## Country, Language, and Currency Standards [#170]

**MUST** use international standards for locale-related properties:

```yaml
# Country — ISO 3166-1 alpha-2
country_code:
  type: string
  format: iso-3166-1-alpha-2
  description: Two-letter country code
  example: "DE"
  pattern: "^[A-Z]{2}$"

# Language — BCP 47 / ISO 639-1
language:
  type: string
  format: bcp47
  description: Language tag
  example: "en-US"

# Currency — ISO 4217
currency:
  type: string
  format: iso-4217
  description: Three-letter currency code
  example: "EUR"
  pattern: "^[A-Z]{3}$"
```

---

## Content Negotiation [#244]

**SHOULD** use content negotiation via `Accept` and `Content-Type` headers when
clients may choose different representations:

```yaml
# Multiple representations
paths:
  /reports/{report_id}:
    get:
      parameters:
        - name: Accept
          in: header
          schema:
            type: string
            enum:
              - application/json
              - application/pdf
              - text/csv
      responses:
        "200":
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Report"
            application/pdf:
              schema:
                type: string
                format: binary
            text/csv:
              schema:
                type: string
```

---

## UUIDs — Only If Necessary [#144]

**SHOULD** prefer shorter, URL-friendly identifiers over UUIDs. Use UUIDs only
when global uniqueness without coordination is required.

```yaml
# Preferred — short, readable identifiers
id:
  type: string
  description: URL-friendly order identifier
  example: "ord-7kBx3"

# UUID — only when globally unique, uncoordinated IDs are required
correlation_id:
  type: string
  format: uuid
  description: Globally unique correlation identifier
  example: "550e8400-e29b-41d4-a716-446655440000"
```

---

## Non-JSON Media Types [#168]

**MAY** use non-JSON media types for binary or specialized content, with proper
Content-Type headers:

```yaml
# File upload
requestBody:
  content:
    multipart/form-data:
      schema:
        type: object
        properties:
          file:
            type: string
            format: binary
          description:
            type: string

# PDF download
responses:
  "200":
    content:
      application/pdf:
        schema:
          type: string
          format: binary
```

---

## Standard Media Types [#172]

**SHOULD** use IANA-registered media types. Avoid inventing custom media types
unless content negotiation specifically requires versioned types [#114].

Common types:
- `application/json` — Default API payloads
- `application/problem+json` — Error responses [#176]
- `application/merge-patch+json` — PATCH requests
- `application/pdf`, `image/png`, `text/csv` — Binary/text content

---

## Null and Absent Semantics [#123]

**MUST** treat null values and absent (missing) properties identically. An API
must not assign different meaning to a property being `null` versus being
omitted from the payload.

```yaml
# These two payloads MUST be treated the same way:
# { "nickname": null }
# { }   (nickname absent)

# In the schema, nullable properties should be marked:
nickname:
  type: string
  nullable: true   # OpenAPI 3.0
  description: Optional display name (null and absent are equivalent)

# In OpenAPI 3.1 (JSON Schema), use oneOf or type array:
nickname:
  oneOf:
    - type: string
    - type: "null"
```

---

## No Null Booleans [#122]

**MUST NOT** use null for boolean properties. If a third state is needed, use
a tri-state enum instead:

```yaml
# Wrong — nullable boolean
is_verified:
  type: boolean
  nullable: true    # What does null mean? Unknown? Not applicable?

# Correct — tri-state enum
verification_status:
  type: string
  enum:
    - VERIFIED
    - NOT_VERIFIED
    - UNKNOWN
  description: |
    VERIFIED — identity has been confirmed
    NOT_VERIFIED — verification attempted but failed
    UNKNOWN — verification has not been attempted
```

---

## No Null Empty Arrays [#124]

**SHOULD NOT** use null for empty arrays. Represent empty collections as `[]`
to simplify client-side handling:

```yaml
# Correct
items:
  type: array
  items:
    $ref: "#/components/schemas/OrderItem"
  default: []
  description: Order line items. Empty array if no items.

# Wrong — clients must handle both null and []
# { "items": null }   ← avoid this
# { "items": [] }     ← use this instead
```

---

## Maps via additionalProperties [#216]

**SHOULD** define dictionary/map types using `additionalProperties`:

```yaml
# Map of locale to translated text
translations:
  type: object
  description: Translations keyed by BCP 47 language tag
  additionalProperties:
    type: string
  example:
    en: "Shopping Cart"
    de: "Warenkorb"
    fr: "Panier"

# Map with structured values
inventory_by_warehouse:
  type: object
  additionalProperties:
    type: object
    properties:
      quantity:
        type: integer
        format: int32
      last_updated_at:
        type: string
        format: date-time
```

---

## Open-Ended Enums via `examples` [#112]

**SHOULD** use the `examples` keyword instead of closed `enum` for values that
may grow over time. This signals to clients that they must handle unknown values
gracefully (tolerant reader pattern [#108]).

> **Historic note:** Prior to October 2025, the Zalando guidelines recommended
> `x-extensible-enum`. The current guideline uses the standard `examples` keyword.

```yaml
# Open-ended — new values can be added without breaking clients
OrderStatus:
  type: string
  examples:
    - ORDER_PLACED
    - PAYMENT_PENDING
    - PAYMENT_CONFIRMED
    - SHIPPED
    - DELIVERED
    - CANCELLED
  description: |
    Order lifecycle status. Clients MUST handle unknown values
    gracefully as new statuses may be added.

# Fixed — only use enum when the set is truly closed
DayOfWeek:
  type: string
  enum:
    - MONDAY
    - TUESDAY
    - WEDNESDAY
    - THURSDAY
    - FRIDAY
    - SATURDAY
    - SUNDAY
```

---

## Single Resource Schema [#252]

**SHOULD** design a single schema per resource for both read and write
operations. Use `readOnly` and `writeOnly` markers for asymmetry:

```yaml
Order:
  type: object
  required:
    - customer_id
    - items
  properties:
    id:
      type: string
      readOnly: true          # only in responses
      description: Server-assigned order identifier
    customer_id:
      type: string
      description: Customer placing the order
    items:
      type: array
      items:
        $ref: "#/components/schemas/OrderItem"
    created_at:
      type: string
      format: date-time
      readOnly: true          # only in responses
    password:
      type: string
      writeOnly: true         # only in requests (if applicable)
```

---

## Unicode Awareness [#250]

**SHOULD** be aware of services that may not fully support JSON/Unicode. When
relevant, document encoding requirements and constraints for string properties.

---

## Top-Level JSON Objects [#110]

**MUST** always return JSON objects as the top-level data structure. Never return
a bare array or primitive as the top-level response:

```yaml
# Correct — object wrapper enables future extension
OrderList:
  type: object
  properties:
    items:
      type: array
      items:
        $ref: "#/components/schemas/Order"
    cursor:
      type: string

# Wrong — bare array prevents adding metadata later
# Response: [{"id": "1"}, {"id": "2"}]
```

This enables backward-compatible extension by adding new top-level fields
without breaking existing clients.

---

## Common Money Object [#173]

**MUST** use the standard Money object for all monetary values:

```yaml
Money:
  type: object
  description: |
    Standard money representation following ISO 4217.
    Amount uses decimal format to avoid floating-point errors.
  required:
    - amount
    - currency
  properties:
    amount:
      type: number
      format: decimal
      description: >
        Monetary amount as decimal. The number of decimal places
        must match the currency's minor unit (e.g., 2 for EUR/USD,
        0 for JPY).
      example: 29.99
    currency:
      type: string
      format: iso-4217
      description: ISO 4217 three-letter currency code
      pattern: "^[A-Z]{3}$"
      example: "EUR"
```

**Usage in schemas:**

```yaml
Order:
  type: object
  properties:
    total_price:
      $ref: "#/components/schemas/Money"
    shipping_cost:
      $ref: "#/components/schemas/Money"
    discount_amount:
      $ref: "#/components/schemas/Money"
```

**Important:** Always use `decimal` format for monetary amounts, never `float`
or `double`, to prevent rounding errors [#171].

---

## Common Address Fields [#249]

**MUST** use the standardized address schema fields:

```yaml
Address:
  type: object
  description: Standard postal address representation
  properties:
    street_address:
      type: string
      description: Street name and house number
      example: "Mollstr. 1"
    additional_address_info:
      type: string
      description: Additional address line (apartment, suite, etc.)
      example: "Apt 4B"
    city:
      type: string
      description: City or locality name
      example: "Berlin"
    state:
      type: string
      description: State, province, or region
      example: "Berlin"
    zip_code:
      type: string
      description: Postal or ZIP code
      example: "10178"
    country_code:
      type: string
      format: iso-3166-1-alpha-2
      description: ISO 3166-1 alpha-2 country code
      example: "DE"
      pattern: "^[A-Z]{2}$"
  required:
    - street_address
    - city
    - zip_code
    - country_code
```

---

## Format Selection Quick Reference

| Data Type          | `type`    | `format`    | Rule  |
|--------------------|-----------|-------------|-------|
| Timestamp          | `string`  | `date-time` | [#169]|
| Calendar date      | `string`  | `date`      | [#255]|
| Duration           | `string`  | `duration`  | [#127]|
| Email              | `string`  | `email`     | [#238]|
| URI                | `string`  | `uri`       | [#238]|
| UUID               | `string`  | `uuid`      | [#144]|
| Country            | `string`  | `iso-3166`  | [#170]|
| Currency code      | `string`  | `iso-4217`  | [#170]|
| Language           | `string`  | `bcp47`     | [#170]|
| Monetary amount    | `number`  | `decimal`   | [#171]|
| Count / quantity   | `integer` | `int32`     | [#171]|
| Large identifier   | `integer` | `int64`     | [#171]|
| Measurement        | `number`  | `double`    | [#171]|
