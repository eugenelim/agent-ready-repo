# Naming Conventions Reference

> Derived from the [Zalando RESTful API Guidelines](https://opensource.zalando.com/restful-api-guidelines/).
> License: CC-BY-4.0 — Copyright Zalando SE. This is a derivative work.

This reference covers all naming rules that apply when generating OpenAPI 3.1
contracts. Every constraint is cited with its rule number.

---

## JSON Property Names — snake_case [#118]

**MUST** use `snake_case` for all JSON property names. Never use `camelCase`,
`PascalCase`, or `kebab-case` in JSON bodies.

```yaml
# Correct
order_status:
  type: string
shipping_address:
  $ref: "#/components/schemas/Address"

# Wrong — camelCase
orderStatus:
  type: string
shippingAddress:
  $ref: "#/components/schemas/Address"
```

**Rationale:** snake_case is the dominant convention in JSON APIs and avoids
ambiguity in case-insensitive contexts.

---

## URL Path Segments — kebab-case [#129]

**MUST** use `kebab-case` for multi-word path segments. Single-word segments
are lowercase.

```yaml
# Correct
/sales-orders
/shipment-tracking
/payment-methods

# Wrong
/salesOrders        # camelCase
/sales_orders       # snake_case
/SalesOrders        # PascalCase
```

---

## Query Parameters — snake_case [#130]

**MUST** use `snake_case` for query parameter names. This aligns with JSON
property naming.

```yaml
# Correct
GET /orders?order_status=open&created_after=2024-01-01

# Wrong
GET /orders?orderStatus=open&createdAfter=2024-01-01
```

---

## Pluralized Resource Names [#134]

**MUST** pluralize collection resource names. Singular names are used only for
singleton resources.

```yaml
# Correct
/orders
/orders/{order_id}
/orders/{order_id}/items

# Wrong
/order
/order/{order_id}
```

---

## Pluralized Array Names [#120]

**SHOULD** pluralize JSON property names that hold arrays to signal cardinality.

```yaml
# Correct
items:
  type: array
  items:
    $ref: "#/components/schemas/OrderItem"
addresses:
  type: array
  items:
    $ref: "#/components/schemas/Address"

# Wrong — singular name for array
item:
  type: array
  items:
    $ref: "#/components/schemas/OrderItem"
```

---

## Verb-Free URLs [#141]

**MUST** keep URLs verb-free. URLs identify resources (nouns); HTTP methods
express the operation.

```yaml
# Correct — use HTTP methods on resource URLs
POST   /orders             # create order
GET    /orders/{order_id}  # read order
PUT    /orders/{order_id}  # replace order
PATCH  /orders/{order_id}  # partial update
DELETE /orders/{order_id}  # delete order

# Wrong — verbs in URL
POST /orders/create
GET  /orders/getOrder/{id}
POST /orders/{id}/cancel    # acceptable ONLY when it models a sub-resource
```

**Exception:** When an action cannot be modeled as a state change on a resource,
a verb-based sub-resource may be acceptable (e.g., `POST /orders/{id}/cancellation`
modeled as creating a cancellation sub-resource) [#138].

---

## Domain-Specific Resource Names [#142]

**MUST** use domain-specific (ubiquitous language) resource names. Names should
come from the business domain, not from implementation details.

```yaml
# Correct — domain language
/sales-orders
/shipments
/payment-transactions

# Wrong — technical/generic names
/entities
/records
/data-objects
```

---

## UPPER_SNAKE_CASE Enums [#240]

**SHOULD** declare enum values using `UPPER_SNAKE_CASE` strings.

```yaml
OrderStatus:
  type: string
  examples:
    - ORDER_PLACED
    - PAYMENT_PENDING
    - PAYMENT_CONFIRMED
    - SHIPPED
    - DELIVERED
    - CANCELLED
```

This convention applies to both closed `enum` and open-ended `examples` [#112] values.

---

## Date/Time Property Suffixes [#235]

**SHOULD** use naming conventions for date and time properties:

| Suffix    | Meaning                     | Format      | Example          |
|-----------|-----------------------------|-------------|------------------|
| `_at`     | Timestamp (date + time)     | `date-time` | `created_at`     |
| `_date`   | Calendar date only          | `date`      | `due_date`       |
| `_time`   | Time of day only            | `time`      | `opening_time`   |

```yaml
created_at:
  type: string
  format: date-time
  readOnly: true
  example: "2024-06-15T14:30:00Z"
due_date:
  type: string
  format: date
  example: "2024-07-01"
```

---

## Common Field Names [#174]

**MUST** use prescribed names and semantics for common fields:

| Field          | Type          | Description                              |
|----------------|---------------|------------------------------------------|
| `id`           | `string`      | Unique resource identifier               |
| `created_at`   | `date-time`   | Timestamp of resource creation (readOnly)|
| `modified_at`  | `date-time`   | Timestamp of last modification (readOnly)|
| `type`         | `string`      | Resource type discriminator              |
| `etag`         | `string`      | Opaque version identifier for concurrency|

```yaml
Order:
  type: object
  properties:
    id:
      type: string
      readOnly: true
      description: Unique order identifier
    created_at:
      type: string
      format: date-time
      readOnly: true
    modified_at:
      type: string
      format: date-time
      readOnly: true
    type:
      type: string
      description: Resource type discriminator
```

---

## URL-Friendly Identifiers [#228]

**MUST** use URL-friendly resource identifiers. IDs appearing in URLs must be
ASCII-safe and not require percent-encoding.

```yaml
# Correct — URL-safe identifiers
/orders/abc-123
/products/sku-7890

# Wrong — requires encoding
/orders/order%20123
/products/SKU/789    # ambiguous path segment
```

---

## Path Hierarchy [#143]

**MUST** use path segments to express resource containment and hierarchy:

```
/{collection}/{id}/{sub-collection}/{sub-id}
```

```yaml
/orders/{order_id}/items/{item_id}
/customers/{customer_id}/addresses/{address_id}
/warehouses/{warehouse_id}/inventory/{product_id}
```

Each path segment alternates between collection name and identifier.

---

## Normalized Paths [#136]

**MUST** use normalized paths without empty segments or trailing slashes.

```yaml
# Correct
/orders/{order_id}/items

# Wrong
/orders/{order_id}/items/   # trailing slash
/orders//{order_id}/items   # empty segment (double slash)
```

The API should have one canonical path per resource.

---

## No /api Base Path [#135]

**SHOULD NOT** use `/api` as a base path prefix. The host or path structure
itself should distinguish API endpoints.

```yaml
# Correct
servers:
  - url: https://orders.example.com

# Avoid
servers:
  - url: https://example.com/api
```

---

## Sub-Resource Level Limits [#147]

**SHOULD** limit URL nesting to a maximum of 3 sub-resource levels.

```yaml
# Acceptable — 3 levels
/orders/{order_id}/items/{item_id}/options/{option_id}

# Too deep — consider flattening
/orders/{order_id}/items/{item_id}/options/{option_id}/variants/{variant_id}
```

When the hierarchy is too deep, consider using flat URLs with query parameter
filters instead [#145].

---

## Nested vs. Flat URLs [#145]

**MAY** choose between nested and flat URL structures based on ownership semantics.

```yaml
# Nested — item belongs to order (strong containment)
GET /orders/{order_id}/items/{item_id}

# Flat — order-item accessible independently (weak association)
GET /order-items/{item_id}
GET /order-items?order_id={order_id}
```

**Guidelines:**
- Use nested URLs when the sub-resource has no meaning outside the parent
- Use flat URLs when the sub-resource has independent identity
- Use flat URLs to avoid deep nesting beyond 3 levels [#147]

---

## Compound Keys [#241]

**MAY** expose compound business keys as resource identifiers using a defined
separator.

```yaml
# Compound key with separator
/products/{country_code}_{product_id}

# Example
GET /products/DE_12345
```

When using compound keys, document the separator convention and the key
components in the API specification.

---

## Resource Type Limits [#146]

**SHOULD** limit the total number of resource types per API to maintain
comprehensibility. Aim for fewer than 8 resource types per API specification.

If an API requires many resource types, consider splitting it into multiple
focused APIs aligned with bounded contexts.

---

## HTTP Header Naming [#132]

**SHOULD** use `Kebab-Upper-Case` (capitalize each word) for custom HTTP headers.

```yaml
# Correct
X-Flow-Id: abc-123
X-Tenant-Id: tenant-42
Accept-Encoding: gzip

# Wrong
x_flow_id: abc-123       # snake_case
x-flow-id: abc-123       # all lowercase
```

Standard headers (Content-Type, Authorization, etc.) already follow this
convention [#133].

---

## Event Type Naming [#213]

**MUST** follow a hierarchical dot-separated naming convention for event types
that reflects the business domain.

```
{organization}.{domain}.{event-name}.{version}
```

```yaml
# Examples
order-service.orders.order-placed.v1
payment-service.payments.payment-completed.v1
inventory-service.stock.stock-updated.v1
```

Event type names use kebab-case for individual segments. The hierarchy enables
consumers to subscribe to specific events or entire domain topics.

---

## Quick Reference Table

| Context             | Convention              | Rule  | Example                    |
|---------------------|------------------------|-------|----------------------------|
| JSON properties     | `snake_case`           | [#118]| `order_status`             |
| URL path segments   | `kebab-case`           | [#129]| `/sales-orders`            |
| Query parameters    | `snake_case`           | [#130]| `?order_status=open`       |
| Collection names    | Plural nouns           | [#134]| `/orders`                  |
| Array properties    | Plural nouns           | [#120]| `"items": [...]`           |
| Enum values         | `UPPER_SNAKE_CASE`     | [#240]| `ORDER_PLACED`             |
| Timestamps          | `_at` suffix           | [#235]| `created_at`               |
| Date properties     | `_date` suffix         | [#235]| `due_date`                 |
| HTTP headers        | `Kebab-Upper-Case`     | [#132]| `X-Flow-Id`                |
| Event types         | Dot-separated hierarchy| [#213]| `orders.order-placed.v1`   |
| Resources in URLs   | Domain language nouns  | [#142]| `/shipments`               |
| Resource identifiers| URL-safe ASCII         | [#228]| `abc-123`                  |
