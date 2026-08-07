# Hypermedia and Performance

> Derived from the [Zalando RESTful API Guidelines](https://opensource.zalando.com/restful-api-guidelines/) (CC-BY-4.0, Zalando SE).

These rules cover REST maturity, hypertext controls, and performance optimizations
for bandwidth, caching, and responsiveness.

---

## Hypermedia

### [#162] MUST use REST maturity level 2

All APIs MUST implement at least **Richardson Maturity Model level 2**:

| Level | Requirement | Status |
|---|---|---|
| 0 | Single URI, single verb | Not acceptable |
| 1 | Multiple URIs (resources) | Not sufficient |
| **2** | **Proper HTTP verbs + status codes** | **Required** |
| 3 | HATEOAS (hypermedia controls) | Optional ([#163]) |

Level 2 means:
- Resources are identified by distinct URIs
- HTTP methods (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`) carry correct semantics
- HTTP status codes (2xx, 4xx, 5xx) convey outcome accurately
- Standard headers (`Content-Type`, `Location`, `ETag`, etc.) are used correctly

---

### [#163] MAY use REST maturity level 3 — HATEOAS

Hypermedia as the Engine of Application State is **optional**. APIs MAY provide
navigational links in responses to improve discoverability, but consumers MUST NOT
be forced to rely on them for basic operation.

When HATEOAS is used, follow [#164] and [#165] for link format.

---

### [#164] MUST use common hypertext controls

When providing hypermedia links, MUST use a consistent link object format:

```yaml
# Link object schema
components:
  schemas:
    Link:
      type: object
      properties:
        href:
          type: string
          format: uri
          description: Target URI of the linked resource
          example: 'https://api.example.com/orders/123'
        rel:
          type: string
          description: Link relation type (IANA or custom)
          example: 'self'
        type:
          type: string
          description: Expected media type of the target resource
          example: 'application/json'
        title:
          type: string
          description: Human-readable link label
      required:
        - href
```

Standard link relations (`self`, `next`, `prev`, `first`, `last`) SHOULD follow
[IANA link relation types](https://www.iana.org/assignments/link-relations/).

---

### [#165] SHOULD use simple hypertext controls for pagination and self-references

For the most common hypermedia use cases — pagination and self-links — SHOULD use a
simple, flat link structure:

```yaml
# Paginated collection response
OrderList:
  type: object
  properties:
    self:
      type: string
      format: uri
      example: 'https://api.example.com/orders?cursor=abc&limit=10'
    next:
      type: string
      format: uri
      example: 'https://api.example.com/orders?cursor=def&limit=10'
    prev:
      type: string
      format: uri
      example: 'https://api.example.com/orders?cursor=xyz&limit=10'
    items:
      type: array
      items:
        $ref: '#/components/schemas/Order'
```

This pattern avoids the complexity of full HAL or JSON:API link structures while
still enabling client navigation.

---

### [#217] MUST use full, absolute URI for resource identification

All resource URIs in responses MUST be **absolute** (fully qualified):

```
# Correct
"href": "https://api.example.com/orders/123"

# Wrong — relative URI
"href": "/orders/123"
```

Absolute URIs prevent clients from having to construct URLs and reduce coupling to
specific deployment configurations.

---

### [#166] MUST NOT use link headers with JSON entities

When the response body is JSON, hyperlinks MUST be embedded **inside the JSON
payload**, not in HTTP `Link` headers:

```
# Wrong — link in header with JSON body
Link: <https://api.example.com/orders?page=2>; rel="next"
Content-Type: application/json
{"items": [...]}

# Correct — link in JSON body
Content-Type: application/json
{
  "items": [...],
  "next": "https://api.example.com/orders?cursor=abc"
}
```

HTTP `Link` headers are appropriate for non-JSON media types (e.g., HTML, binary)
but MUST NOT be mixed with JSON response bodies.

---

## Performance

### [#155] SHOULD reduce bandwidth needs and improve responsiveness

APIs SHOULD employ strategies to minimize data transfer and improve response times:

- Support field filtering / partial responses ([#157])
- Enable compression ([#156])
- Allow sub-resource embedding ([#158])
- Use pagination for collections
- Support conditional requests (`If-None-Match`, `If-Modified-Since`)

---

### [#156] SHOULD use gzip compression

APIs SHOULD support **gzip** content encoding for response bodies:

```
# Client request
Accept-Encoding: gzip

# Server response
Content-Encoding: gzip
```

Gzip typically reduces JSON payload size by 60-80%. Servers SHOULD respect the
`Accept-Encoding` header and compress responses when the client supports it.

---

### [#157] SHOULD support partial responses via filtering

APIs SHOULD allow clients to request only the fields they need using a `fields`
query parameter:

```
GET /orders/123?fields=id,status,total_amount
```

This reduces payload size and can improve backend performance when expensive
computed fields can be skipped.

OpenAPI definition pattern:

```yaml
parameters:
  - name: fields
    in: query
    required: false
    description: Comma-separated list of fields to include in the response
    schema:
      type: string
    example: 'id,status,total_amount'
```

---

### [#158] SHOULD allow optional embedding of sub-resources

APIs SHOULD support an `embed` (or `expand`) query parameter that lets clients
request related resources inline, avoiding additional round-trips:

```
# Without embedding — requires two requests
GET /orders/123
GET /orders/123/items

# With embedding — single request
GET /orders/123?embed=items
```

OpenAPI definition pattern:

```yaml
parameters:
  - name: embed
    in: query
    required: false
    description: Comma-separated list of sub-resources to embed
    schema:
      type: string
    example: 'items,customer'
```

Embedded sub-resources SHOULD appear as nested objects within the parent response.
The un-embedded response SHOULD include a link ([#164]) to the sub-resource instead.

---

### [#227] MUST document cacheable GET, HEAD, and POST endpoints

For every `GET`, `HEAD`, or cacheable `POST` endpoint, the API specification MUST
document caching behavior:

| Aspect | What to document |
|---|---|
| **Cache-Control** | Directives (`max-age`, `no-cache`, `no-store`, `private`, `public`) |
| **TTL** | Expected freshness duration |
| **Vary** | Which request headers affect the cached response (`Vary: Accept, Accept-Encoding`) |
| **ETags** | Whether the endpoint supports `ETag` / `If-None-Match` conditional requests |
| **Last-Modified** | Whether the endpoint supports `Last-Modified` / `If-Modified-Since` |

OpenAPI example:

```yaml
paths:
  /products/{product_id}:
    get:
      summary: Get product details
      description: |
        Cacheable. Responses include `ETag` and `Cache-Control: max-age=300`.
        Use `If-None-Match` for conditional requests.
      responses:
        '200':
          headers:
            Cache-Control:
              schema:
                type: string
              example: 'max-age=300, public'
            ETag:
              schema:
                type: string
              example: '"33a64df5"'
        '304':
          description: Not Modified — use cached version
```

**Key rule:** If an endpoint is cacheable, say so explicitly. If it is not cacheable
(e.g., returns user-specific data), document `Cache-Control: no-store` or
`Cache-Control: private`.

---

## Quick-reference checklist

```
For every endpoint:
  [ ] Correct HTTP method and status codes [#162]
  [ ] All URIs in responses are absolute [#217]
  [ ] Links embedded in JSON body, not Link headers [#166]
  [ ] Cacheable endpoints document Cache-Control / ETag [#227]

For collections:
  [ ] Pagination with self/next/prev links [#165]
  [ ] Consider field filtering support [#157]
  [ ] Consider sub-resource embedding [#158]
  [ ] Support gzip compression [#156]
```
