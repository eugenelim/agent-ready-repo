# architect

Concept to reviewed design doc — workspace-agnostic.

---

## Start here

Type `architect-design` and describe the problem — what you're building, for whom, and the key constraint.

```text
architect-design

  Knowledge surface: docs/architecture/reference.md

  Problem      Billing engine for a multi-tenant SaaS.
  Constraint   No shared state between tenants.
  Candidates   Event-sourced ledger; relational schema + row-level security

Approve this shape? ›
```

On any session return, type `architect-design [path]` to continue.

```text
architect-design docs/design/multi-tenant-billing/design.md

  Stage 1  in progress — §3 Proposal (last saved)
```

---

## Entry points

| Say this | What happens |
|----------|-------------|
| `architect-design` | Frame a concept, write a Google-style design doc, and converge it against review |
| `architect-diagram` | Draw a Mermaid diagram — C4, sequence, state, ER, or flowchart |
| `architect-review` | Critique a design doc or diagram with severity-tagged findings |

---

## How a session runs

```text
architect-design [event notification service — at-least-once delivery]

  Knowledge surface: docs/architecture/reference.md

  Problem      Events from checkout must reach three downstream services.
  Constraint   At-least-once delivery; no shared database between subscribers.
  Candidates   Outbox pattern; Kafka topic per subscriber; webhook relay

Approve this shape? ›
```

```text
architect-design docs/design/event-notification/design.md

  ## TL;DR

  Use the transactional outbox pattern. The service writes event records
  in the same transaction as the originating write; a poller fans out to
  each subscriber, and each subscriber tracks its own cursor. Kafka
  per-subscriber is rejected — it couples all subscribers to broker
  availability for a sync path that can tolerate async retry.
```

```text
architect-review docs/design/event-notification/design.md

  Verdict: SHIP WITH CHANGES

  🟥  Proposal §3 — subscriber cursor schema is unspecified; needed
      before the contracts pack can draft the delivery API.
  🟧  Alternatives §1 — webhook relay rejection rationale is thin.
  ⚪  TL;DR last sentence is passive voice; tighten.
```

The reviewer runs in a forked context — no authoring memory. You act on its findings, then proceed.

---

## Diagram session

````text
architect-diagram [C4 component view — billing service]

  Routed: C4 Component
  Reference: docs/architecture/reference.md

  ```mermaid
  C4Component
    Container_Ext(api, "API Gateway", "HTTPS")
    Container(billing, "Billing Service", "Go · event-sourced")
    Container(events, "Event Store", "Kafka")
    Container_Ext(pay, "Payment Processor", "Stripe")
    Rel(api, billing, "POST /invoice")
    Rel(billing, events, "append event")
    Rel(billing, pay, "POST /charge")
  ```
````

`architect-diagram` routes by intent — C4 (container, component, context), sequence, state, ER, or flowchart — from a plain description. No notation flag needed.

---

→ **How it works:** [DESIGN.md](DESIGN.md) — philosophy, architecture invariants, and decision log.  
→ **Go deeper:** the [`architect` guides](https://github.com/eugenelim/agent-ready-repo/tree/main/guides/architect/).
