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
architect-design [describe the problem]

  Knowledge surface: docs/architecture/reference.md

  Problem      Billing engine for a multi-tenant SaaS.
  Constraint   No shared state between tenants.
  Candidates   Event-sourced ledger; relational schema + row-level security

Approve this shape? ›
```

```text
architect-design [continue to Stage 1]

  ## TL;DR

  Introduce a dedicated billing service backed by an event-sourced ledger.
  Tenant isolation is enforced at ingestion by partition key, not at query
  time by row-level security — a constraint we cannot control in
  third-party integrations. The relational-plus-RLS alternative is rejected
  because it couples isolation to every caller's query discipline.
```

```text
architect-review docs/design/multi-tenant-billing/design.md

  Verdict: SHIP WITH CHANGES

  🟥  Proposal §4 — trust boundary between billing service and payment
      processor is unlabeled; required before the integration contract
      can be implemented.
  🟧  Alternatives §2 — relational-plus-RLS rejection reason is thin.
  ⚪  TL;DR sentence 2 could be tightened.
```

The reviewer runs in a forked context — no authoring memory. You act on its findings, then save.

---

→ **How it works:** [DESIGN.md](DESIGN.md) — philosophy, architecture invariants, and decision log.  
→ **Go deeper:** the [`architect` guides](https://github.com/eugenelim/agent-ready-repo/tree/main/guides/architect/).
