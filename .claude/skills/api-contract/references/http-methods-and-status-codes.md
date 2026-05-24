# HTTP Methods and Status Codes Reference

> Derived from the [Zalando RESTful API Guidelines](https://opensource.zalando.com/restful-api-guidelines/).
> License: CC-BY-4.0 — Copyright Zalando SE. This is a derivative work.

This reference covers HTTP method semantics, status code usage, error handling,
headers, and security rules for OpenAPI 3.1 contract generation.

---

## HTTP Method Semantics [#148]

**MUST** use HTTP methods according to their defined semantics:

| Method  | Semantics                          | Request Body | Response Body  |
|---------|------------------------------------|-------------|----------------|
| GET     | Read resource(s)                   | No          | Yes            |
| POST    | Create resource or trigger action  | Yes         | Yes            |
| PUT     | Full replacement of resource       | Yes         | Yes (optional) |
| PATCH   | Partial update of resource         | Yes         | Yes            |
| DELETE  | Remove resource                    | No (usually)| No (usually)   |
| HEAD    | Same as GET without response body  | No          | No             |
| OPTIONS | Get communication options          | No          | Yes            |

### GET
- Retrieves a resource or collection without side effects
- Must be safe and idempotent
- Collection GET returns list with pagination [#159]

### POST
- Creates a new resource (returns 201 + Location header)
- Triggers a processing action (returns 200 or 202)
- Not idempotent by default (but see [#229])

### PUT
- Full replacement of the entire resource
- Client sends the complete resource representation
- Idempotent: repeated calls produce the same result
- Returns 200 (with body) or 204 (without body)

### PATCH
- Partial update using merge-patch (application/merge-patch+json) or
  JSON Patch (application/json-patch+json)
- Only changed fields are sent
- Returns 200 with updated resource

### DELETE
- Removes the resource
- Idempotent: deleting an already-deleted resource returns 204 (not 404)
- Returns 204 (no content) or 200 (with confirmation body)

---

## Method Properties [#149]

**MUST** honor the standard method properties:

| Method  | Safe | Idempotent | Cacheable |
|---------|------|------------|-----------|
| GET     | Yes  | Yes        | Yes       |
| HEAD    | Yes  | Yes        | Yes       |
| OPTIONS | Yes  | Yes        | No        |
| POST    | No   | No*        | No        |
| PUT     | No   | Yes        | No        |
| PATCH   | No   | No*        | No        |
| DELETE  | No   | Yes        | No        |

*POST and PATCH can be designed to be idempotent [#229].

- **Safe:** The method does not alter server state
- **Idempotent:** Multiple identical requests have the same effect as one
- **Cacheable:** Response may be stored for reuse

---

## Idempotent POST and PATCH [#229]

**SHOULD** design POST and PATCH to be idempotent where possible.

### Using Secondary Keys [#231]

**SHOULD** use a client-provided secondary key (business key) to achieve
POST idempotency. The server detects duplicate creation via the key and returns
the existing resource.

```yaml
# Client sends a creation request with a business key
POST /orders
{
  "client_reference": "PO-2024-001",  # secondary/business key
  "customer_id": "cust-42",
  "items": [...]
}

# Duplicate request with same client_reference returns existing order
# Response: 200 OK (or 201 Created on first call)
```

### Using Idempotency-Key Header [#230]

**MAY** support the `Idempotency-Key` header for non-idempotent operations:

```yaml
# OpenAPI definition for idempotency key
parameters:
  - name: Idempotency-Key
    in: header
    required: false
    schema:
      type: string
      format: uuid
    description: |
      Unique key for idempotent retry. The server stores the
      response and returns it for duplicate requests with the
      same key.
```

```http
POST /payments HTTP/1.1
Idempotency-Key: 7c4b8e2f-1a3d-4e5f-8b2c-9d0e1f2a3b4c
Content-Type: application/json

{"amount": "29.99", "currency": "EUR"}
```

---

## Asynchronous Processing [#253]

**MAY** use 202 Accepted for long-running operations:

```yaml
# Endpoint that triggers async processing
post:
  operationId: initiateExport
  summary: Initiate data export
  responses:
    "202":
      description: Export request accepted for processing
      headers:
        Location:
          schema:
            type: string
            format: uri
          description: URL to poll for export status
      content:
        application/json:
          schema:
            $ref: "#/components/schemas/ExportStatus"
```

**Pattern:**
1. Client sends POST request
2. Server returns 202 with Location header pointing to status resource
3. Client polls GET on the status resource
4. Status resource reports progress; final state includes result link

---

## Collection Format for Parameters [#154]

**MUST** define the collection format for multi-value header and query parameters.

```yaml
# Explicit collection format using style/explode
parameters:
  - name: status
    in: query
    required: false
    schema:
      type: array
      items:
        type: string
        enum: [OPEN, CLOSED, PENDING]
    style: form       # csv format: ?status=OPEN,CLOSED
    explode: false

  - name: tag
    in: query
    schema:
      type: array
      items:
        type: string
    style: form       # multi format: ?tag=a&tag=b
    explode: true
```

---

## Simple Query Languages [#236]

**SHOULD** design simple filtering using dedicated query parameters per
filterable property:

```yaml
# Per-property filter parameters
GET /orders?status=OPEN&customer_id=cust-42&created_after=2024-01-01

parameters:
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
```

---

## Complex Queries via JSON [#237]

**SHOULD** use a POST to a search sub-resource for complex query needs:

```yaml
# Search sub-resource
POST /orders/search
Content-Type: application/json

{
  "filter": {
    "status": ["OPEN", "PENDING"],
    "total_amount": { "gte": 100.00, "lte": 500.00 },
    "created_at": { "after": "2024-01-01T00:00:00Z" }
  },
  "sort": [{ "field": "created_at", "order": "desc" }],
  "cursor": "eyJpZCI6MTIzfQ==",
  "limit": 20
}
```

---

## Document Implicit Filtering [#226]

**MUST** document any implicit response filtering. If results are automatically
filtered (e.g., by tenant, by user permissions, by region), this must be stated
in the API specification description.

```yaml
get:
  summary: List orders
  description: |
    Returns orders visible to the authenticated user. Results are
    implicitly filtered by the user's tenant and permission scope.
```

---

## Official HTTP Status Codes [#243]

**MUST** only use status codes from the IANA HTTP Status Code Registry.

---

## Most Common Status Codes [#150]

**SHOULD** limit usage to these well-known status codes:

### Success (2xx)

| Code | Meaning              | Typical Use                              |
|------|----------------------|------------------------------------------|
| 200  | OK                   | GET, PUT, PATCH, DELETE with body         |
| 201  | Created              | POST that created a resource              |
| 202  | Accepted             | Async processing initiated [#253]        |
| 204  | No Content           | DELETE, PUT/PATCH without response body   |

### Redirection (3xx) — Avoid [#251]

| Code | Meaning              | Note                                     |
|------|----------------------|------------------------------------------|
| 301  | Moved Permanently    | Avoid in APIs                            |
| 303  | See Other            | Redirect after POST (rare in APIs)       |
| 304  | Not Modified         | Conditional GET with ETag/If-None-Match  |

**SHOULD NOT** use redirection codes [#251]. Return data directly or use
explicit resource links.

### Client Error (4xx)

| Code | Meaning              | Typical Use                              |
|------|----------------------|------------------------------------------|
| 400  | Bad Request          | Malformed request syntax or invalid data |
| 401  | Unauthorized         | Missing or invalid authentication        |
| 403  | Forbidden            | Authenticated but insufficient permissions|
| 404  | Not Found            | Resource does not exist                  |
| 405  | Method Not Allowed   | HTTP method not supported on resource    |
| 406  | Not Acceptable       | Content negotiation failed               |
| 408  | Request Timeout      | Client took too long                     |
| 409  | Conflict             | State conflict (e.g., concurrent update) |
| 410  | Gone                 | Resource permanently removed             |
| 412  | Precondition Failed  | ETag/If-Match condition not met          |
| 415  | Unsupported Media    | Wrong Content-Type                       |
| 422  | Unprocessable Entity | Syntactically valid but semantically wrong|
| 429  | Too Many Requests    | Rate limit exceeded [#153]               |

### Server Error (5xx)

| Code | Meaning              | Typical Use                              |
|------|----------------------|------------------------------------------|
| 500  | Internal Server Error| Unexpected server failure                |
| 501  | Not Implemented      | Feature not yet available                |
| 503  | Service Unavailable  | Temporary overload or maintenance        |

---

## Most Specific Status Code [#220]

**MUST** return the most specific applicable status code. Do not use a generic
400 when 422 (validation error) or 409 (conflict) is more precise.

---

## Specify Success and Error Responses [#151]

**MUST** specify all relevant success and error response codes in the OpenAPI
specification:

```yaml
responses:
  "200":
    description: Order retrieved successfully
    content:
      application/json:
        schema:
          $ref: "#/components/schemas/Order"
  "400":
    description: Bad request — invalid parameters
    content:
      application/problem+json:
        schema:
          $ref: "#/components/schemas/Problem"
  "404":
    description: Order not found
    content:
      application/problem+json:
        schema:
          $ref: "#/components/schemas/Problem"
```

---

## 207 for Batch Operations [#152]

**MUST** use 207 Multi-Status for batch or bulk requests where individual items
can succeed or fail independently:

```yaml
responses:
  "207":
    description: Multi-status response for batch operation
    content:
      application/json:
        schema:
          type: object
          properties:
            items:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: string
                  status:
                    type: integer
                    description: HTTP status code for this item
                  detail:
                    type: string
```

---

## 429 for Rate Limits [#153]

**MUST** use 429 Too Many Requests with appropriate headers:

```yaml
responses:
  "429":
    description: Rate limit exceeded
    headers:
      Retry-After:
        schema:
          type: integer
        description: Seconds to wait before retrying
      X-Rate-Limit-Limit:
        schema:
          type: integer
        description: Maximum requests per time window
      X-Rate-Limit-Remaining:
        schema:
          type: integer
        description: Remaining requests in current window
      X-Rate-Limit-Reset:
        schema:
          type: integer
        description: Unix timestamp when the window resets
    content:
      application/problem+json:
        schema:
          $ref: "#/components/schemas/Problem"
```

---

## Problem JSON — RFC 9457 [#176]

**MUST** use RFC 9457 Problem Details for all error responses:

```yaml
Problem:
  type: object
  properties:
    type:
      type: string
      format: uri
      description: |
        URI reference identifying the problem type. Use
        "about:blank" if no specific type is defined.
      default: "about:blank"
      example: "https://api.example.com/problems/order-not-found"
    title:
      type: string
      description: Short human-readable summary of the problem type
      example: "Order Not Found"
    status:
      type: integer
      format: int32
      description: HTTP status code (redundant but convenient)
      example: 404
    detail:
      type: string
      description: Human-readable explanation specific to this occurrence
      example: "Order with id 'ord-123' does not exist"
    instance:
      type: string
      format: uri
      description: URI reference identifying the specific occurrence
      example: "/orders/ord-123"
  required:
    - type
    - title
    - status
```

Error responses use `application/problem+json` content type.

---

## No Stack Traces [#177]

**MUST NOT** expose stack traces or internal implementation details in error
responses. The Problem `detail` field should contain a user-friendly description,
never a Java/Python/Node stack trace.

---

## No Redirection Codes [#251]

**SHOULD NOT** use HTTP redirection (3xx) status codes. Return the data directly
or provide explicit resource links in the response body.

---

## Content-* Headers [#178]

**MUST** use Content-* headers correctly:

- `Content-Type` — Media type of the request/response body
- `Content-Encoding` — Compression encoding (gzip, deflate)
- `Content-Language` — Language of the response content
- `Content-Length` — Size of the response body in bytes

---

## Location Header [#180]

**SHOULD** use the `Location` header (not `Content-Location`) for:
- 201 Created responses — points to the newly created resource
- 202 Accepted responses — points to the async status resource

```yaml
post:
  responses:
    "201":
      description: Order created
      headers:
        Location:
          schema:
            type: string
            format: uri
          description: URI of the newly created order
          example: /orders/ord-456
```

---

## Content-Location Header [#179]

**MAY** use `Content-Location` to indicate the direct URL of the returned
representation when it differs from the request URL.

---

## Prefer Header [#181]

**MAY** support RFC 7240 `Prefer` header for client processing preferences:

```
Prefer: respond-async          # request async processing
Prefer: return=minimal         # return minimal response
Prefer: return=representation  # return full resource after mutation
```

---

## ETag and Conditional Requests [#182]

**MAY** support ETags for optimistic concurrency control:

```yaml
# Response includes ETag
GET /orders/ord-123
ETag: "33a64df551425fcc55e4d42a148795d9f25f89d4"

# Client sends If-Match for safe update
PUT /orders/ord-123
If-Match: "33a64df551425fcc55e4d42a148795d9f25f89d4"

# Server returns 412 if ETag doesn't match (concurrent modification)
```

In OpenAPI:
```yaml
parameters:
  - name: If-Match
    in: header
    required: true
    schema:
      type: string
    description: ETag value from previous GET for optimistic locking
```

---

## Standard Headers [#133]

**MAY** use IANA-registered standard HTTP headers. Prefer standard headers over
custom ones for common functionality. Common standard headers in API contracts:

- `Authorization` — Bearer token or API key
- `Accept` / `Content-Type` — Content negotiation
- `Cache-Control` — Caching directives
- `Retry-After` — Rate limit recovery
- `ETag` / `If-Match` / `If-None-Match` — Conditional requests

---

## Secure Endpoints [#104]

**MUST** secure every API endpoint using appropriate authentication and
authorization mechanisms:

```yaml
components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
    OAuth2:
      type: oauth2
      flows:
        clientCredentials:
          tokenUrl: https://auth.example.com/oauth/token
          scopes:
            orders.read: Read access to orders
            orders.write: Write access to orders

security:
  - BearerAuth: []
  - OAuth2: [orders.read]
```

---

## OAuth Scopes [#105]

**MUST** define and assign fine-grained permissions (OAuth 2.0 scopes) that
map to business capabilities:

```yaml
paths:
  /orders:
    get:
      security:
        - OAuth2: [orders.read]
    post:
      security:
        - OAuth2: [orders.write]
  /orders/{order_id}:
    delete:
      security:
        - OAuth2: [orders.admin]
```

---

## Scope Naming Convention [#225]

**MUST** follow a hierarchical naming pattern for OAuth scopes:

```
<api-id>.<resource>.<access-mode>
```

```yaml
# Examples
orders.read              # read access to orders
orders.write             # write access to orders
orders.admin             # administrative access to orders
payments.read            # read access to payments
payments.refund          # permission to issue refunds
```

---

## Method-to-Status-Code Quick Reference

| Method | Success         | Common Errors                        |
|--------|-----------------|--------------------------------------|
| GET    | 200             | 400, 401, 403, 404                   |
| POST   | 201, 200, 202   | 400, 401, 403, 409, 422             |
| PUT    | 200, 204        | 400, 401, 403, 404, 409, 412, 422   |
| PATCH  | 200             | 400, 401, 403, 404, 409, 412, 422   |
| DELETE | 204, 200        | 401, 403, 404, 409                   |
