# Mermaid sequenceDiagram — request flows and handshakes

The right notation for *what happens when X arrives* — request paths,
integration handshakes, async event flows.

## Skeleton

````
```mermaid
sequenceDiagram
    actor User
    participant Web as Web app
    participant API as API service
    participant DB as Postgres

    User->>Web: submit order
    Web->>API: POST /orders
    API->>DB: INSERT
    DB-->>API: row id
    API-->>Web: 201 Created
    Web-->>User: redirect to /orders/123
```
````

Declare every participant at the top. `actor` for humans, `participant`
for systems. Use `as` to give a short alias and a readable label.

## Arrow shapes

| Mermaid | Meaning |
| --- | --- |
| `A->>B: msg` | Synchronous call — A blocks until B returns |
| `A-->>B: msg` | Return / reply (dashed) |
| `A-)B: msg` | Asynchronous send — A does not wait |
| `A--)B: msg` | Asynchronous reply |
| `A-xB: msg` | Sync that fails / does not return |
| `A--xB: msg` | Async that fails |

Be consistent. Don't mix `->>` (sync) and `-)` (async) for the same
kind of edge across the diagram.

## Activation bars

Show *who is doing work* during a span:

````
sequenceDiagram
    A->>+B: request
    B->>+C: subrequest
    C-->>-B: response
    B-->>-A: response
````

`+` activates the receiver; `-` on the reply deactivates. Use it when
the diagram needs to show concurrency or hold-open semantics; skip it
when the flow is purely linear.

## Alternative and parallel paths

```
alt happy path
    A->>B: success request
    B-->>A: 200 OK
else error
    A->>B: failing request
    B-->>A: 500
end

par fan-out
    A->>B: branch 1
and
    A->>C: branch 2
end

opt only sometimes
    A->>B: optional call
end
```

Use `alt` for mutually exclusive paths, `par` for concurrent paths,
`opt` for "happens sometimes".

## Notes and separators

```
Note over A,B: assumption: token already validated
Note right of A: TODO: clarify retry policy
```

Notes are the right way to surface *assumptions the picture can't
show* — auth state, prior context, time skips.

## Loops

```
loop every 30s
    Worker->>Queue: poll
    Queue-->>Worker: batch
end
```

## Sequence numbers

Add `autonumber` as the first statement to label every message with an
incrementing number — useful in dense or nested flows where prose references
"step 4":

```
sequenceDiagram
    autonumber
    User->>API: POST /login
    API->>DB: query user
    DB-->>API: user record
    API-->>User: 200 OK + token
```

## Early exit — `break`

`break` short-circuits the flow for a guard clause or validation failure.
Different from `alt`: `break` is "stop here on this condition" (early
return); `alt` is "take one of these paths" (branching).

```
sequenceDiagram
    User->>API: POST /order
    API->>Validator: check payload

    break Payload invalid
        API-->>User: 400 Bad Request
    end

    API->>DB: save order
    DB-->>API: ok
    API-->>User: 201 Created
```

## Participant links

Attach a clickable link to a participant lane with `link`:

```
sequenceDiagram
    participant API as Order API
    link API: Docs @ https://docs.example.com/orders
    link API: Runbook @ https://wiki.example.com/runbooks/orders

    participant DB as Postgres
    API->>DB: INSERT
```

Links render as clickable icons in renderers that support them. In
unsupporting renderers the participant draws normally — links degrade
gracefully.

## Common architecture pitfalls

- **Happy path only.** Add at least one `alt` for the failure case
  that matters. A flow without error handling is fiction.
- **Unnamed participants.** Every box has an alias and a label;
  `participant A as User-service [Go, gRPC]` is fine and answers
  "what tech" at a glance.
- **Time skips with no note.** If the flow waits 24 hours for a
  human, `Note over B: waits for human approval (≤24h)` makes it
  honest.
- **Diagram drives the design.** Sequence diagrams describe flows
  that already exist or are being committed to; if you find
  yourself inventing the flow *as you draw*, switch back to a
  design doc first.
