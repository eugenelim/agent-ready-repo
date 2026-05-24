# Pagination and Filtering Reference

> Derived from the [Zalando RESTful API Guidelines](https://opensource.zalando.com/restful-api-guidelines/).
> License: CC-BY-4.0 — Copyright Zalando SE. This is a derivative work.

This reference covers pagination patterns, filtering approaches, and partial
response mechanisms for OpenAPI 3.1 contract generation.

---

## Must Support Pagination [#159]

**MUST** support pagination on all collection endpoints. Unbounded result sets
cause performance degradation, timeouts, and excessive memory usage.

```yaml
paths:
  /orders:
    get:
      summary: List orders
      parameters:
        - $ref: "#/components/parameters/Cursor"
        - $ref: "#/components/parameters/Limit"
      responses:
        "200":
          description: Paginated list of orders
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/OrderList"
```

---

## Cursor-Based Pagination Preferred [#160]

**SHOULD** prefer cursor-based pagination over offset-based pagination.

### Cursor-Based (Preferred)

The cursor is an opaque token (typically a base64-encoded value) that points to
a position in the result set. The server returns items after that position.

**Advantages:**
- Consistent results even when data changes between pages
- Performs well on large datasets (no OFFSET scan)
- Stable under concurrent inserts/deletes

**Disadvantages:**
- Cannot jump to an arbitrary page
- Cannot easily compute total page count

```yaml
# Request
GET /orders?cursor=eyJpZCI6MTIzfQ==&limit=20

# Response
{
  "items": [...],
  "cursor": {
    "self": "eyJpZCI6MTIzfQ==",
    "next": "eyJpZCI6MTQzfQ=="
  },
  "has_more": true
}
```

### Offset-Based (Use Only When Necessary)

Offset-based pagination uses `offset` (number of items to skip) and `limit`.

**Advantages:**
- Clients can jump to any page
- Simpler mental model for UI pagination

**Disadvantages:**
- Moving window problem: inserts/deletes shift items between pages
- Performance degrades with large offsets (database must scan and discard rows)
- Inconsistent results under concurrent modification

```yaml
# Request
GET /orders?offset=40&limit=20

# Response
{
  "items": [...],
  "offset": 40,
  "limit": 20
}
```

**When to use offset-based:** Only for small, slowly-changing datasets where
jump-to-page navigation is a hard requirement.

---

## Pagination Response Page Object [#248]

**SHOULD** include a page object with pagination metadata in the response:

```yaml
# Full paginated response structure
OrderList:
  type: object
  required:
    - items
  properties:
    items:
      type: array
      items:
        $ref: "#/components/schemas/Order"
      description: List of orders for the current page
    cursor:
      type: object
      description: Cursor-based pagination metadata
      properties:
        self:
          type: string
          description: Cursor pointing to the start of this page
          example: "eyJpZCI6MTIzfQ=="
        next:
          type: string
          description: Cursor for the next page (absent if no more pages)
          example: "eyJpZCI6MTQzfQ=="
        prev:
          type: string
          description: Cursor for the previous page (absent if first page)
    has_more:
      type: boolean
      description: Whether more results exist beyond this page
      example: true
```

For offset-based pagination (when necessary):

```yaml
OrderListOffset:
  type: object
  required:
    - items
  properties:
    items:
      type: array
      items:
        $ref: "#/components/schemas/Order"
    offset:
      type: integer
      format: int32
      description: Current offset in the result set
    limit:
      type: integer
      format: int32
      description: Maximum number of items per page
    has_more:
      type: boolean
      description: Whether more results exist beyond this page
```

---

## Pagination Links [#161]

**SHOULD** include navigation links in paginated responses for discoverability:

```yaml
OrderList:
  type: object
  properties:
    items:
      type: array
      items:
        $ref: "#/components/schemas/Order"
    _links:
      type: object
      description: Pagination navigation links
      properties:
        self:
          type: string
          format: uri
          description: Link to the current page
          example: "https://api.example.com/orders?cursor=eyJpZCI6MTIzfQ==&limit=20"
        next:
          type: string
          format: uri
          description: Link to the next page (absent if last page)
          example: "https://api.example.com/orders?cursor=eyJpZCI6MTQzfQ==&limit=20"
        prev:
          type: string
          format: uri
          description: Link to the previous page (absent if first page)
          example: "https://api.example.com/orders?cursor=eyJpZCI6MTAzfQ==&limit=20"
        first:
          type: string
          format: uri
          description: Link to the first page
          example: "https://api.example.com/orders?limit=20"
        last:
          type: string
          format: uri
          description: Link to the last page (if computable)
```

Links should be fully qualified absolute URIs [#217].

---

## Avoid Total Result Count [#254]

**SHOULD** avoid returning a `total_count` in paginated responses. Total counts
require expensive `COUNT(*)` queries that don't scale.

```yaml
# Preferred — use has_more boolean
{
  "items": [...],
  "has_more": true
}

# Avoid — expensive total count
{
  "items": [...],
  "total_count": 15847    # requires COUNT(*) query
}
```

If a total count is absolutely required (e.g., for UI showing "Page 3 of 47"),
consider:
- Caching the count with a TTL (approximate is acceptable)
- Providing it as an optional, separately-requested field
- Using an estimate rather than an exact count

---

## Conventional Query Parameters [#137]

**MUST** use these established query parameter names:

| Parameter | Type      | Description                                      |
|-----------|-----------|--------------------------------------------------|
| `q`       | `string`  | Full-text search query                           |
| `sort`    | `string`  | Sort order (e.g., `created_at` or `-created_at`) |
| `cursor`  | `string`  | Opaque pagination cursor                         |
| `limit`   | `integer` | Maximum items per page (default: 20, max: 100)   |
| `offset`  | `integer` | Number of items to skip (offset-based only)      |
| `fields`  | `string`  | Comma-separated list of fields to return [#157]  |
| `embed`   | `string`  | Comma-separated sub-resources to embed [#158]    |
| `expand`  | `string`  | Alias for embed — sub-resources to inline        |

```yaml
components:
  parameters:
    Cursor:
      name: cursor
      in: query
      required: false
      schema:
        type: string
      description: Opaque cursor for pagination. Omit for the first page.

    Limit:
      name: limit
      in: query
      required: false
      schema:
        type: integer
        format: int32
        minimum: 1
        maximum: 100
        default: 20
      description: Maximum number of items to return per page.

    Sort:
      name: sort
      in: query
      required: false
      schema:
        type: string
      description: |
        Sort field with optional direction prefix. Use `-` for descending.
        Example: `created_at` (ascending) or `-created_at` (descending).

    Query:
      name: q
      in: query
      required: false
      schema:
        type: string
      description: Full-text search query across searchable fields.

    Fields:
      name: fields
      in: query
      required: false
      schema:
        type: string
      description: |
        Comma-separated list of fields to include in the response.
        Example: `id,status,created_at`

    Embed:
      name: embed
      in: query
      required: false
      schema:
        type: string
      description: |
        Comma-separated list of sub-resources to embed in the response.
        Example: `items,customer`
```

---

## Simple Query Languages [#236]

**SHOULD** design simple filtering using dedicated query parameters for each
filterable property:

```yaml
# Example: filtering orders
GET /orders?status=OPEN&customer_id=cust-42&created_after=2024-01-01&sort=-created_at&limit=20

parameters:
  - name: status
    in: query
    required: false
    schema:
      type: string
      examples:
        - OPEN
        - CLOSED
        - PENDING
        - CANCELLED
    description: Filter by order status

  - name: customer_id
    in: query
    required: false
    schema:
      type: string
    description: Filter by customer identifier

  - name: created_after
    in: query
    required: false
    schema:
      type: string
      format: date-time
    description: Filter orders created after this timestamp

  - name: created_before
    in: query
    required: false
    schema:
      type: string
      format: date-time
    description: Filter orders created before this timestamp

  - name: min_total
    in: query
    required: false
    schema:
      type: number
      format: decimal
    description: Filter orders with total amount >= this value
```

**Conventions for range filters:**
- Use `_after` / `_before` suffixes for date ranges
- Use `min_` / `max_` prefixes for numeric ranges
- Multi-value filters use comma-separated values or repeated parameters [#154]

---

## Complex Queries via JSON [#237]

**SHOULD** use a POST request to a search sub-resource for complex query
requirements that exceed what simple query parameters can express:

```yaml
paths:
  /orders/search:
    post:
      operationId: searchOrders
      summary: Search orders with complex filters
      description: |
        Use this endpoint for complex queries with nested logic,
        range filters, and multi-field sorting. Results are paginated.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/OrderSearchQuery"
      responses:
        "200":
          description: Search results
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/OrderList"

components:
  schemas:
    OrderSearchQuery:
      type: object
      properties:
        filter:
          type: object
          description: Filter criteria
          properties:
            status:
              type: array
              items:
                type: string
              description: Match any of these statuses
            total_amount:
              type: object
              properties:
                gte:
                  type: number
                  format: decimal
                lte:
                  type: number
                  format: decimal
            created_at:
              type: object
              properties:
                after:
                  type: string
                  format: date-time
                before:
                  type: string
                  format: date-time
        sort:
          type: array
          items:
            type: object
            required:
              - field
            properties:
              field:
                type: string
              order:
                type: string
                enum: [asc, desc]
                default: asc
          description: Sort criteria applied in order
        cursor:
          type: string
          description: Pagination cursor
        limit:
          type: integer
          format: int32
          minimum: 1
          maximum: 100
          default: 20
```

**When to use search sub-resource vs. query parameters:**
- Simple filters on 1-3 properties: query parameters [#236]
- Nested boolean logic (AND/OR): search sub-resource
- Range queries on multiple fields: search sub-resource
- Full-text search with facets: search sub-resource
- Complex sort with multiple fields: search sub-resource

---

## Partial Responses — Fields Parameter [#157]

**SHOULD** support a `fields` query parameter to let clients request only the
properties they need, reducing payload size and bandwidth:

```yaml
# Request only specific fields
GET /orders/ord-123?fields=id,status,total_price,created_at

# Response — only requested fields
{
  "id": "ord-123",
  "status": "OPEN",
  "total_price": {
    "amount": 99.99,
    "currency": "EUR"
  },
  "created_at": "2024-06-15T14:30:00Z"
}
```

```yaml
parameters:
  - name: fields
    in: query
    required: false
    schema:
      type: string
    description: |
      Comma-separated list of top-level fields to include.
      Omit to return all fields.
    example: "id,status,total_price,created_at"
```

**Notes:**
- Fields filtering applies to top-level properties
- Nested field selection (e.g., `total_price.amount`) is optional
- Always return `id` even if not explicitly requested

---

## Embedding Sub-Resources [#158]

**SHOULD** support `embed` or `expand` query parameters to inline related
resources, reducing the number of round-trip requests:

```yaml
# Without embedding — client must make separate requests
GET /orders/ord-123
{
  "id": "ord-123",
  "customer_id": "cust-42",
  "items": [...]
}
# Then: GET /customers/cust-42

# With embedding — sub-resource inlined
GET /orders/ord-123?embed=customer
{
  "id": "ord-123",
  "customer_id": "cust-42",
  "customer": {
    "id": "cust-42",
    "name": "Jane Doe",
    "email": "jane@example.com"
  },
  "items": [...]
}
```

```yaml
parameters:
  - name: embed
    in: query
    required: false
    schema:
      type: string
    description: |
      Comma-separated list of related resources to embed.
      Example: `customer,payment` embeds customer and payment
      details inline.

paths:
  /orders/{order_id}:
    get:
      parameters:
        - $ref: "#/components/parameters/Embed"
      responses:
        "200":
          description: Order with optionally embedded sub-resources
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Order"
```

**Guidelines:**
- Document which sub-resources are embeddable per endpoint
- Embedded resources use the same schema as their standalone representation
- Use embedding to solve N+1 query problems on the client side
- Do not embed deeply nested resources (1 level is typical)

---

## Complete Paginated Collection Example

Combining pagination, filtering, sorting, and partial responses:

```yaml
paths:
  /orders:
    get:
      operationId: listOrders
      summary: List orders with filtering and pagination
      parameters:
        # Pagination
        - $ref: "#/components/parameters/Cursor"
        - $ref: "#/components/parameters/Limit"
        # Sorting
        - $ref: "#/components/parameters/Sort"
        # Filtering
        - name: status
          in: query
          schema:
            type: string
        - name: customer_id
          in: query
          schema:
            type: string
        - name: created_after
          in: query
          schema:
            type: string
            format: date-time
        # Partial response
        - $ref: "#/components/parameters/Fields"
        # Embedding
        - $ref: "#/components/parameters/Embed"
      responses:
        "200":
          description: Paginated list of orders
          content:
            application/json:
              schema:
                type: object
                required:
                  - items
                properties:
                  items:
                    type: array
                    items:
                      $ref: "#/components/schemas/Order"
                  cursor:
                    type: object
                    properties:
                      self:
                        type: string
                      next:
                        type: string
                  has_more:
                    type: boolean
                  _links:
                    type: object
                    properties:
                      self:
                        type: string
                        format: uri
                      next:
                        type: string
                        format: uri
                      prev:
                        type: string
                        format: uri
        "400":
          description: Invalid filter or pagination parameters
          content:
            application/problem+json:
              schema:
                $ref: "#/components/schemas/Problem"
```
